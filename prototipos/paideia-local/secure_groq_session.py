"""Explicitly authorized, memory-only, bounded Groq session."""
from datetime import datetime, timedelta, timezone
import threading
import time
import math
import uuid
from contextlib import contextmanager
from pathlib import Path

from providers import API_KEY_ENV, DEFAULT_MODEL, GroqHTTPSJSONTransport, GroqProvider, ProviderError, SendState
from mission_budget import MissionBudget, load_mission

HARD_DEADLINE = datetime(2026, 10, 29, 17, 40, 20, tzinfo=timezone.utc)


def __getattr__(name):
    # Preserve legacy module-level GUI references without loading Tk for HTTP.
    if name == "tk":
        import tkinter
        return tkinter
    if name == "ttk":
        from tkinter import ttk
        return ttk
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Session:
    def __init__(self, key, *, transport=None, clock=None, deadline=HARD_DEADLINE, test_only=False, monotonic=None, mission_budget=None):
        if type(test_only) is not bool or (not test_only and (transport is not None or clock is not None or monotonic is not None)):
            raise ValueError('transport injection requires test_only')
        from structured_session_fixture import StructuredSessionFixture
        if test_only and type(transport) is not StructuredSessionFixture:
            raise ValueError('closed synthetic transport required')
        if (type(key) is not str or not key or not key.isascii() or len(key) > 4096
                or any(ord(c) < 33 or ord(c) > 126 for c in key)):
            raise ValueError('invalid key')
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        now = self._clock()
        if mission_budget is not None:
            if not isinstance(mission_budget, MissionBudget):
                raise ValueError('invalid mission budget')
            verified = load_mission(mission_budget.config.manifest or mission_budget.config.directory / 'mission.json')
            if mission_budget.config != verified or (not test_only and mission_budget.path != verified.directory / 'mission-ledger.json'):
                raise ValueError('invalid mission budget')
            deadline = verified.cutoff
        if (not isinstance(now, datetime) or now.utcoffset() is None
                or not isinstance(deadline, datetime) or deadline.utcoffset() is None
                or (mission_budget is None and deadline > HARD_DEADLINE) or deadline <= now
                or (mission_budget is not None and (now < verified.start or mission_budget.remaining() == 0))):
            raise ValueError('invalid deadline or clock')
        self._mission_budget = mission_budget
        self._run_id = 'run-' + uuid.uuid4().hex if mission_budget and mission_budget.config.digest else None
        self._deadline = min(deadline, now + timedelta(seconds=3600))
        self._monotonic = monotonic or time.monotonic
        self._start_tick = self._monotonic()
        if not isinstance(self._start_tick, (int, float)) or not math.isfinite(self._start_tick):
            raise ValueError('invalid monotonic clock')
        self._last_tick = self._start_tick
        self._last_time = now
        self._environment = {API_KEY_ENV: key}
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._flight = threading.Lock()
        self._benchmark_thread = None
        self._benchmark_started = False
        self._benchmark_state = 'not_started'
        self._calls = 0
        self._state = 'active'
        self._final_pending = False
        self._test_only = test_only
        self._server = None
        self._thread = None
        self._output = None
        self._started = False
        self._upstream = transport if test_only else GroqHTTPSJSONTransport()
        self.transport = _CountedTransport(self, test_only, self._upstream)
        raw_provider = GroqProvider(self.transport, opt_in=True, environment=self._environment, timeout=15)
        self.provider = _SingleFlightProvider(self, raw_provider)

    @property
    def test_only(self):
        return self.transport._binding[0]

    def _check(self, *, allow_quota=False):
        try:
            now = self._clock()
            tick = self._monotonic()
            if (not isinstance(now, datetime) or now.utcoffset() is None or now < self._last_time
                    or now >= self._deadline or not isinstance(tick, (int, float))
                    or not math.isfinite(tick) or tick < self._last_tick or tick - self._start_tick >= 3600):
                self._state = 'expired'
                self._environment.clear()
            else:
                self._last_time = now
                self._last_tick = tick
        except Exception:
            self._state = 'expired'
            self._environment.clear()
        if self._state != 'active':
            self._stop.set()
        return self._state == 'active' or (allow_quota and self._state == 'quota_exhausted')

    def revoke(self):
        with self._lock:
            self._state = 'revoked'
            self._environment.clear()
            self._stop.set()

    def _benchmark_path(self):
        base = (self._mission_budget.config.directory / self._run_id if self._run_id else
                self._mission_budget.config.directory if self._mission_budget else Path(__file__).resolve().parent / 'evidence')
        return base / 'session-benchmark.json'

    def _status_path(self):
        base = (self._mission_budget.config.directory / self._run_id if self._run_id else
                self._mission_budget.config.directory if self._mission_budget else Path(__file__).resolve().parent / 'evidence')
        return base / 'session-status.json'

    def start_benchmark(self, *, confirmed=False, output=None, wait=None):
        if not self.test_only and (output is not None or wait is not None):
            raise ValueError('test injection is disabled')
        if confirmed is not True:
            return False
        with self._lock:
            if self._benchmark_started or not self._check():
                return False
            self._benchmark_started = True
            self._benchmark_state = 'running'
        target = Path(output) if output is not None else self._benchmark_path()
        waiter = wait or self._stop.wait

        def worker():
            import json
            from context_quality_benchmark import run_benchmark
            calls = [0]
            def callback(payload):
                if calls[0] and waiter(21):
                    return {'status': 503, 'text': ''}
                if self.status()['state'] != 'active':
                    return {'status': 503, 'text': ''}
                calls[0] += 1
                try:
                    started_at = time.perf_counter()
                    result = self.provider.chat(payload['messages'])
                    latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
                    if result.refusal or result.finish_reason != 'stop':
                        reason = 'model_refused' if result.refusal else ('response_truncated' if result.finish_reason == 'length' else 'model_unfinished')
                        return {'status': 503, 'text': '', 'error_code': reason,
                                'diagnostic': {'finish_reason': result.finish_reason, 'has_content': bool(result.answer)}}
                    return {'status': 200, 'text': result.answer, 'latency_ms': latency_ms}
                except ProviderError as error:
                    diagnostic = getattr(error, 'diagnostic', None)
                    reason = 'response_truncated' if isinstance(diagnostic, dict) and diagnostic.get('finish_reason') == 'length' else error.code
                    return {'status': 429 if error.code == 'rate_limited' else 503, 'text': '',
                            'error_code': reason, 'diagnostic': diagnostic}
            try:
                report = run_benchmark(callback, DEFAULT_MODEL, max_calls=18, test_only=self.test_only)
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(target.suffix + '.tmp')
                temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                temporary.replace(target)
                with self._lock:
                    self._benchmark_state = 'complete' if report.get('stop_reason') == 'complete' else 'stopped'
            except Exception:
                with self._lock:
                    self._benchmark_state = 'error'  # No exception details or secrets in logs.
        self._benchmark_thread = threading.Thread(target=worker, daemon=True)
        self._benchmark_thread.start()
        return True

    def start_server(self, *, port=8768, output=None, structured_test_only=False):
        from structured_session_fixture import StructuredSessionFixture
        if type(structured_test_only) is not bool or (structured_test_only and (
                not self.test_only or type(self.transport._binding[1]) is not StructuredSessionFixture
                or self._mission_budget is None or not self._mission_budget.config.digest)):
            raise ValueError('synthetic structured mission required')
        import app
        from backend_services import LocalChatService, CatalogueComparisonService
        from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
        from pai_tools import ToolDispatcher
        if not self.test_only and (port != 8768 or output is not None):
            raise ValueError('production port and output are fixed')
        with self._lock:
            if self._started or not self._check():
                raise RuntimeError('session unavailable')
            self._started = True
            try:
                repository = app.SnapshotRepository()
                policy = AdmissionPolicy(max_concurrent=1, max_queue=0, calls_per_minute=24,
                                         calls_per_day=24, ticket_ttl_seconds=120,
                                         claim_ttl_seconds=120, scope='single-session')
                gate = InterfazChatAdmission(policy, self._clock,
                    budget_state=InMemoryBudgetState.new_empty(scope=policy.scope))
                dispatcher = ToolDispatcher(repository, CatalogueComparisonService())
                if structured_test_only:
                    service = LocalChatService(provider=self.provider, enabled=True, test_only=True,
                        admission=gate, structured_session_test_only=True)
                else:
                    service = LocalChatService(provider=self.provider, enabled=True, test_only=self.test_only,
                        dispatcher=dispatcher, tools_enabled=True, tools_scope='calculator_only', admission=gate)
                server = app.create_server(host='127.0.0.1', port=port, repository=repository, chat_service=service)
                self._server = server
                self._output = output if self.test_only and output is not None else self._status_path()
                self._thread = threading.Thread(target=server.serve_forever, daemon=True)
                self._thread.start()
                return server
            except Exception:
                self.revoke()
                raise

    def write_status(self):
        if self._output is None:
            return
        import json
        from pathlib import Path
        path = Path(self._output)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(json.dumps(self.status(), ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)

    def close(self):
        self.revoke()
        with self._lock:
            server, self._server = self._server, None
            thread, self._thread = self._thread, None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=3)
        if self._mission_budget is not None:
            self._mission_budget.close()
        try:
            self.write_status()
        except OSError:
            pass  # Session is revoked even if its status cannot be saved.

    def status(self):
        with self._lock:
            if self._state in ('active', 'quota_exhausted'):
                self._check()
            remaining = None
            try:
                if self._mission_budget is not None and (not self._mission_budget._lock.closed or self._state == 'active'):
                    remaining = self._mission_budget.remaining()
            except Exception:
                self.revoke()
            return {'state': self._state, 'calls': self._calls, 'limit': 24, 'mission_remaining': remaining, 'run_id': self._run_id,
                    'final_pending': self._final_pending,
                    'deadline_utc': self._deadline.astimezone(timezone.utc).isoformat(),
                    'benchmark': self._benchmark_state, 'test_only': self.test_only}


class _SingleFlightProvider:
    def __init__(self, session, provider):
        self._session = session
        self._provider = provider

    def chat(self, messages, *, tools=None):
        try:
            with self._session._flight:
                if self._session.status()['state'] != 'active':
                    raise ProviderError('disabled', send_state=SendState.NOT_STARTED)
                return self._provider.chat(messages, tools=tools)
        finally:
            messages = tools = None


    def structured_chat(self, messages):
        from structured_session_fixture import StructuredSessionFixture
        session = self._session
        if (not session.test_only or type(session.transport._binding[1]) is not StructuredSessionFixture
                or session._mission_budget is None or not session._mission_budget.config.digest):
            raise ProviderError('disabled')
        with session._flight:
            if session.status()['state'] != 'active':
                raise ProviderError('disabled')
            return self._provider._chat(messages, structured=True)


class _CountedTransport:
    __slots__ = ('_session', '_binding')

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError('transport binding is fixed')
        object.__setattr__(self, name, value)

    def __init__(self, session, test_only, upstream):
        self._session = session
        self._binding = (test_only, upstream)

    def post(self, **kwargs):
        failure = None
        try:
            result = _COUNTED_POST_IMPL(self, **kwargs)
        except ProviderError as error:
            failure = ProviderError(error.code, send_state=error.send_state)
        finally:
            kwargs = None
        if failure is not None:
            raise failure
        return result

    def _post(self, **kwargs):
        session = self._session
        test_only, upstream = self._binding
        with session._lock:
            if session._state != 'active' or not session._check() or session._calls >= 24:
                raise ProviderError('disabled', send_state=SendState.NOT_STARTED)
            try:
                remaining = session._mission_budget.reserve(session._clock()) if session._mission_budget else None
            except Exception:
                session.revoke()
                raise ProviderError('disabled', send_state=SendState.NOT_STARTED) from None
            session._calls += 1
            final_slot = session._calls == 24 or remaining == 0
            if final_slot:
                session._final_pending = True
                session._state = 'quota_exhausted'
                session._environment.clear()
                session._stop.set()
        try:
            from structured_session_fixture import StructuredSessionFixture, fixture_post
            if test_only and type(upstream) is not StructuredSessionFixture:
                raise RuntimeError('closed synthetic transport required')
            @contextmanager
            def send_guard():
                with session._lock:
                    try:
                        if session._mission_budget is not None:
                            session._mission_budget.remaining()
                    except Exception:
                        session.revoke()
                        raise RuntimeError('mission unavailable') from None
                    if (session._state not in ('active', 'quota_exhausted')
                            or (session._state == 'quota_exhausted' and not final_slot)
                            or not session._check(allow_quota=final_slot)):
                        raise RuntimeError('session unavailable')
                    yield
            if test_only:
                return fixture_post(upstream, **kwargs, send_guard=send_guard)
            return _AUTHORIZED_GROQ_POST(upstream, **kwargs, send_guard=send_guard)
        finally:
            if final_slot:
                with session._lock:
                    session._final_pending = False


_COUNTED_POST_IMPL = _CountedTransport._post
from providers import _GROQ_POST as _AUTHORIZED_GROQ_POST


def _install_counted_trust():
    # Capture class, methods and slot descriptors once, never dynamically import
    # a class named by an untrusted transport. Arbitrary Python mutation of these
    # module globals or function internals remains outside this integrity check.
    import providers
    cls = _CountedTransport
    post, impl = cls.post, cls._post
    binding_slot = vars(cls)['_binding']
    session_slot = vars(cls)['_session']
    def intact(transport):
        if (type(transport) is not cls or vars(cls).get('post') is not post
                or vars(cls).get('_post') is not impl
                or vars(cls).get('_binding') is not binding_slot
                or vars(cls).get('_session') is not session_slot):
            return False
        binding = binding_slot.__get__(transport, cls)
        return (type(binding) is tuple and len(binding) == 2 and binding[0] is False
                and providers._real_transport_intact(binding[1]))
    providers._counted_trust = intact


_install_counted_trust()


def should_auto_close(state):
    return state['state'] != 'active' and not (
        state['state'] == 'quota_exhausted' and state['final_pending'])


def ready_event(run_id, test_only):
    import json
    return json.dumps({'event': 'READY', 'run_id': run_id, 'test_only': test_only}, separators=(',', ':'))


def create_window(*, deadline=HARD_DEADLINE, test_only=False, transport=None, clock=None, port=8768, output=None, mission_config=None):
    """Construct UI only. Start requires a fresh explicit confirmation."""
    try:
        import sys
        tk = getattr(sys.modules[__name__], "tk")
        ttk = getattr(sys.modules[__name__], "ttk")
    except ImportError as exc:
        raise RuntimeError("The secure GUI requires tkinter.") from exc
    if not test_only and (transport is not None or clock is not None or port != 8768 or output is not None):
        raise ValueError('test injection is disabled')
    budget = MissionBudget(mission_config) if mission_config is not None else None
    root = tk.Tk()
    root.title('Paideia — sesión Groq temporal')
    root.geometry('760x680')
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Sesión limitada de chat', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
    if budget is not None:
        ttk.Label(frame, text=f'Corte local: {mission_config.cutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")}; presupuesto restante: {budget.remaining()}/{mission_config.cap}.').pack(anchor='w')
    ttk.Label(frame, wraplength=700, text=(
        'Comprueba personalmente que tu organización de Groq está en Free, sin facturación. '
        'Pega la clave solo aquí; no la envíes al chat. La clave permanece en memoria.\n\n'
        'El chat puede enviar a Groq el texto que escribas: utiliza únicamente datos ficticios. '
        'Solo se habilita la calculadora, no el catálogo para el modelo. Máximo 24 llamadas '
        'incluidas continuaciones, sin reintentos, durante una hora como máximo y nunca después '
        'del límite UTC indicado. La casilla no verifica tu plan ni garantiza ausencia de costes.'
    )).pack(anchor='w', pady=12)
    ttk.Label(frame, text='Clave API (oculta):').pack(anchor='w')
    entry = ttk.Entry(frame, show='*', width=70)
    entry.pack(fill='x', pady=5)
    confirmed = tk.BooleanVar(root, value=False)
    ttk.Checkbutton(frame, variable=confirmed, text='He comprobado Free sin facturación y autorizo esta sesión limitada.').pack(anchor='w', pady=8)
    benchmark_confirmed = tk.BooleanVar(root, value=False)
    ttk.Checkbutton(frame, variable=benchmark_confirmed, text='Autorizar evaluación A/B/C posterior (hasta 18 peticiones), solo tras comprobar la calidad.').pack(anchor='w', pady=5)
    status = tk.StringVar(root, value='Sin iniciar; no se ha enviado ninguna petición.')
    ttk.Label(frame, textvariable=status, wraplength=700).pack(anchor='w', pady=8)
    current = [None]
    timer = [None]
    started = [False]
    terminal = [False]

    def end_pending(message):
        terminal[0] = True
        entry.configure(state='normal')
        entry.delete(0, tk.END)
        entry.configure(state='disabled')
        start_button.configure(state='disabled')
        status.set(message)

    def pending_expired():
        try:
            now = clock() if clock is not None else datetime.now(timezone.utc)
            cutoff = mission_config.cutoff if mission_config is not None else deadline
            return not isinstance(now, datetime) or now.utcoffset() is None or now >= cutoff
        except Exception:
            return True

    def start():
        if terminal[0]:
            status.set('Inicio no disponible. Cierra esta ventana; no se reactivará la sesión.')
            return
        if started[0]:
            status.set('La sesión ya se ha iniciado; no se iniciará otra.')
            return
        if pending_expired():
            end_pending('Plazo vencido o reloj no válido. Cierra esta ventana; solicita una nueva autorización.')
            return
        if not confirmed.get():
            status.set('Confirma el plan Free y la autorización antes de iniciar.')
            return
        key = entry.get()
        if not key or not key.isascii() or len(key) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in key):
            status.set('Clave vacía o inválida; no se ha enviado nada.')
            return
        started[0] = True
        entry.delete(0, tk.END)
        entry.configure(state='disabled')
        stage = 'session'
        try:
            session = Session(key, transport=transport, clock=clock, deadline=deadline, test_only=test_only, mission_budget=budget)
            key = None
            current[0] = session
            stage = 'server'
            server = session.start_server(port=port, output=output)
            stage = 'status'
            session.write_status()
            if benchmark_confirmed.get() and budget is None:
                session.start_benchmark(confirmed=True)
        except Exception as error:
            key = None
            if current[0] is not None:
                current[0].close()
            if pending_expired():
                message = 'Plazo vencido o reloj no válido. Cierra esta ventana; solicita una nueva autorización.'
            elif stage == 'server' and isinstance(error, OSError):
                message = 'No se pudo abrir el puerto local; puede estar ocupado. Cierra esta ventana y comprueba el puerto antes de reabrir.'
            else:
                message = 'No se pudo iniciar la sesión local. Cierra esta ventana y comprueba la configuración antes de reabrir.'
            end_pending(message)
            return
        label = 'SINTÉTICO — TEST ONLY. ' if test_only else ''
        status.set(label + f'Activo en http://127.0.0.1:{server.server_port}/ — 0/24 llamadas. Límite: {session.status()["deadline_utc"]}.')
        print(ready_event(session.status()['run_id'], test_only) if session._run_id else 'READY test_only=' + str(test_only), flush=True)

    def close():
        if timer[0] is not None:
            root.after_cancel(timer[0])
            timer[0] = None
        if current[0] is not None:
            current[0].close()
        elif budget is not None:
            budget.close()
        entry.delete(0, tk.END) if not started[0] else None
        root.destroy()

    def poll():
        if terminal[0]:
            return
        if not started[0] and pending_expired():
            end_pending('Plazo vencido o reloj no válido. Cierra esta ventana; solicita una nueva autorización.')
            return
        if current[0] is not None:
            session = current[0]
            state = session.status()
            try:
                session.write_status()
            except OSError:
                status.set('No se pudo guardar el estado local; revocando sesión.')
                session.close()
                return
            if should_auto_close(state):
                status.set('Sesión finalizada; no se permiten nuevas llamadas. Una llamada ya enviada puede continuar.')
                session.close()
                return
            status.set(('SINTÉTICO — TEST ONLY. ' if test_only else '') +
                       f'Activo: {state["calls"]}/24 llamadas; restante misión {state["mission_remaining"]}/24; límite {state["deadline_utc"]}.')
        timer[0] = root.after(500, poll)

    start_button = ttk.Button(frame, text='Iniciar sesión limitada', command=start)
    start_button.pack(anchor='w', pady=5)
    def start_evaluation():
        if current[0] is None or not benchmark_confirmed.get():
            status.set('Inicia la sesión, comprueba la calidad y autoriza la evaluación antes de ejecutarla.')
            return False
        return current[0].start_benchmark(confirmed=True)
    ttk.Button(frame, text='Ejecutar evaluación A/B/C ahora', command=start_evaluation).pack(anchor='w', pady=5)
    ttk.Button(frame, text='Revocar y cerrar', command=close).pack(anchor='w', pady=5)
    ttk.Label(frame, wraplength=700, text='Revocar impide nuevas llamadas y elimina la referencia a la clave, pero no cancela una petición ya en curso.').pack(anchor='w', pady=8)
    root.protocol('WM_DELETE_WINDOW', close)
    root.report_callback_exception = lambda *_: status.set('Error local; no se mostrarán datos internos.')
    timer[0] = root.after(500, poll)
    return {'root': root, 'entry': entry, 'confirmed': confirmed, 'benchmark_confirmed': benchmark_confirmed, 'status': status,
            'start': start, 'start_evaluation': start_evaluation, 'close': close, 'session': lambda: current[0]}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sesión local temporal; no introduce ni almacena claves en argumentos.')
    parser.add_argument('--deadline-utc', default=None,
                        help='Fecha ISO 8601 con zona UTC; no posterior al límite autorizado.')
    parser.add_argument('--mission', '--mission-config', dest='mission_config', help='Ruta absoluta al manifiesto autorizado; sin secretos.')
    args = parser.parse_args()
    if args.mission_config:
        if args.deadline_utc is not None:
            parser.error('No combinar plazo legacy y misión.')
        try:
            config = load_mission(args.mission_config)
        except (OSError, ValueError):
            parser.error('Manifiesto de misión inválido.')
        create_window(mission_config=config)['root'].mainloop()
        return
    try:
        deadline = datetime.fromisoformat((args.deadline_utc or HARD_DEADLINE.isoformat()).replace('Z', '+00:00'))
        if deadline.utcoffset() != timedelta(0) or deadline > HARD_DEADLINE or deadline <= datetime.now(timezone.utc):
            raise ValueError
    except ValueError:
        parser.error('Límite UTC inválido o fuera de la ventana autorizada.')
    create_window(deadline=deadline)['root'].mainloop()


if __name__ == '__main__':
    main()

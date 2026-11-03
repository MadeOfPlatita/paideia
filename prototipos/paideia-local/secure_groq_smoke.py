"""One explicitly confirmed synthetic Groq request; key stays in process memory."""
from datetime import datetime, timezone
from providers import GroqProvider, GroqHTTPSJSONTransport, ProviderError, API_KEY_ENV, DEFAULT_MODEL

import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser

SMOKE_MESSAGES = [
    {'role': 'system', 'content': 'Responde en español, brevemente. No recomiendes productos ni solicites datos personales.'},
    {'role': 'user', 'content': 'En una sola frase, explica la diferencia entre ahorrar e invertir. Esta es una prueba con datos ficticios.'},
]


class SmokeSession:
    def __init__(self, transport=None):
        self.transport = transport if transport is not None else GroqHTTPSJSONTransport()
        self.attempted = False

    def run(self, key, *, free_plan_confirmed=False):
        report = {'schema': 'paideia-real-smoke.v1',
                  'checked_at': datetime.now(timezone.utc).isoformat(),
                  'model': DEFAULT_MODEL, 'provider_calls': 0,
                  'test_only': bool(getattr(self.transport, 'test_only', False)),
                  'profile_sent': False, 'key_persisted': False}
        if free_plan_confirmed is not True:
            return dict(report, status='free_plan_confirmation_required')
        if self.attempted:
            return dict(report, status='already_attempted')
        self.attempted = True
        class CountedTransport:
            calls = 0
            http_status = None
            def post(inner, **kwargs):
                inner.calls += 1
                response = self.transport.post(**kwargs)
                if type(response.status) is int:
                    inner.http_status = response.status
                return response
        counted = CountedTransport()
        provider = GroqProvider(counted, opt_in=True, environment={API_KEY_ENV: key}, timeout=15)
        try:
            result = provider.chat(SMOKE_MESSAGES)
        except ProviderError as error:
            return dict(report, status=error.code, provider_calls=counted.calls, http_status=counted.http_status)
        return dict(report, status='success', answer=result.answer, provider_calls=counted.calls,
                    http_status=counted.http_status, truncated=result.finish_reason=='length',
                    refused=result.refusal is not None)


def create_window(result_path, *, transport=None):
    """Build the masked UI; building it neither reads credentials nor sends traffic."""
    result_path = Path(result_path)
    root = tk.Tk()
    root.title('Paideia — prueba real de Groq (clave solo en memoria)')
    root.geometry('740x560')
    root.minsize(650, 500)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Prueba real y acotada de IA', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
    ttk.Label(frame, wraplength=680, text=(
        '1. Inicia sesión en Groq y comprueba que la organización está en Free, sin facturación.\n'
        '2. Copia una clave API de esa organización y pégala únicamente en el campo enmascarado.\n'
        '3. Confirma el plan gratuito y pulsa Probar. Se hará UNA petición, sin reintentos.\n\n'
        'No pegues la clave en Hermes. No se guarda en el proyecto, informes ni logs. '
        'No se enviará el perfil. Esta prueba no activa todavía el chat de la web.'
    )).pack(anchor='w', pady=(10, 10))
    links = ttk.Frame(frame)
    links.pack(anchor='w', pady=5)
    ttk.Button(links, text='Abrir consola / claves de Groq', command=lambda: webbrowser.open('https://console.groq.com/keys')).pack(side='left', padx=(0, 8))
    ttk.Button(links, text='Comprobar plan y facturación', command=lambda: webbrowser.open('https://console.groq.com/settings/billing/plans')).pack(side='left')
    ttk.Label(frame, text='Clave API (oculta):').pack(anchor='w', pady=(12, 4))
    key_entry = ttk.Entry(frame, show='*', width=72)
    key_entry.pack(fill='x')
    confirmed = tk.BooleanVar(root, value=False)
    ttk.Checkbutton(frame, text='He comprobado el plan Free, sin facturación, y autorizo esta petición de prueba.', variable=confirmed).pack(anchor='w', pady=12)
    status = tk.StringVar(root, value='Esperando tu confirmación. No se ha llamado a Groq.')
    ttk.Label(frame, textvariable=status, wraplength=680).pack(anchor='w', pady=8)
    session = SmokeSession(transport=transport)
    results = queue.Queue()
    busy = False
    timer = [None]

    def worker(secret):
        try:
            report = session.run(secret, free_plan_confirmed=True)
        except Exception:
            report = {'status': 'local_error', 'test_only': False, 'profile_sent': False, 'key_persisted': False}
        finally:
            secret = None
        results.put(report)

    def start():
        nonlocal busy
        if busy or session.attempted:
            return
        if not confirmed.get():
            status.set('Primero comprueba el plan Free y marca la confirmación. No se ha enviado nada.')
            return
        secret = key_entry.get()
        if not secret or not secret.isascii() or len(secret) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in secret):
            status.set('La clave está vacía o contiene caracteres no válidos. No se ha enviado nada.')
            return
        busy = True
        key_entry.delete(0, tk.END)
        key_entry.configure(state='disabled')
        start_button.configure(state='disabled')
        status.set('Enviando una pregunta ficticia a Groq. Sin perfil ni reintentos...')
        threading.Thread(target=worker, args=(secret,), daemon=True).start()
        secret = None

    def poll():
        try:
            report = results.get_nowait()
        except queue.Empty:
            timer[0] = root.after(150, poll)
            return
        saved = True
        try:
            result_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = result_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(result_path)
        except OSError:
            saved = False
        if report['status'] == 'success':
            label = 'PRUEBA SINTÉTICA — no es IA real:\n' if report.get('test_only') else 'Respuesta REAL recibida de Groq:\n'
            status.set(label + report.get('answer', '') +
                       ('\nAviso: respuesta truncada.' if report.get('truncated') else '') +
                       ('\nAviso: rechazo del modelo.' if report.get('refused') else ''))
        else:
            status.set('La prueba no se completó: ' + report['status'] + '. No se reintentará automáticamente.')
        if not saved:
            status.set(status.get() + '\nNo se pudo guardar el informe local.')
        print('PAIDEIA_GROQ_SMOKE_FINISHED status=' + report['status'] + ' test_only=' + str(report.get('test_only', False)), flush=True)

    start_button = ttk.Button(frame, text='Probar IA real — una petición', command=start)
    start_button.pack(anchor='w', pady=5)
    ttk.Label(frame, wraplength=680, text=(
        'La confirmación no cambia ni verifica por sí sola tu plan en Groq. No continúes si hay dudas de coste. '
        'Cerrar la ventana no deshace una petición ya enviada. La clave no se conserva para futuras sesiones.'
    )).pack(anchor='w', pady=8)
    ttk.Button(frame, text='Cerrar sin guardar la clave', command=root.destroy).pack(anchor='w')
    root.report_callback_exception = lambda *_: status.set('Error local en la ventana; no se mostrarán datos internos.')
    def cleanup(event):
        if event.widget == root and timer[0] is not None:
            root.after_cancel(timer[0])
            timer[0] = None
    root.bind('<Destroy>', cleanup)
    root.update_idletasks()
    timer[0] = root.after(150, poll)
    return {'root': root, 'key_entry': key_entry, 'confirmed': confirmed, 'session': session, 'start': start_button, 'status': status}


if __name__ == '__main__':
    output = Path(__file__).resolve().parent / 'evidence' / 'REAL-IA-SMOKE.json'
    create_window(output)['root'].mainloop()

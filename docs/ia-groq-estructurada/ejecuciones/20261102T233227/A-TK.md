# Prioridad A — backend sin Tk obligatorio

Misión: inicio 2026-11-02 23:32:27+01; corte inmutable 2026-11-03 00:32:27+01. Evidencia del agente A hasta 2026-11-02 23:37:17+01. Revisión independiente y regresión conjunta pendientes del coordinador.

## Archivos exclusivos

- Modificado: `prototipos/paideia-local/secure_groq_session.py`: Tk/ttk se resuelven perezosamente solo si se accede a esos atributos o se construye GUI; error `RuntimeError` explícito al faltar Tk en `create_window`. Se mantienen los atributos históricos `tk`/`ttk`, incluso los overrides usados por pruebas, y no se modifica la validación de identidad.
- Nuevo: `prototipos/paideia-local/tests/test_backend_without_tk.py`.
- Nuevo: este documento.

## RED → GREEN

En `prototipos/paideia-local`, comando reproducible:

```sh
python -m unittest discover -s tests -p test_backend_without_tk.py -v
```

1. RED inicial: 1 prueba, 1 fallo; `import backend_services` → `secure_groq_session.py:8 import tkinter as tk` → `ModuleNotFoundError: tkinter blocked by test`, con hook en subproceso que bloquea tkinter y submódulos. No fue un error de sintaxis.
2. GREEN tras importar Tk perezosamente: 1 prueba OK.
3. RED de error GUI explícito: 2 pruebas, 1 fallo por `ModuleNotFoundError` al intentar `create_window()` con Tk bloqueado. GREEN: 2 OK tras convertir la falta de importación en `RuntimeError` con nombre tkinter.
4. Se incorporó la comprobación HTTP loopback; la regresión original de importación ya había fallado antes del cambio. Sirve `/api/status`, comprueba HTTP 200 y JSON, bloquea destinos/binds y DNS distintos de 127.0.0.1, cierra conexión, servidor e hilo en `finally`.
5. RED compatibilidad: 4 pruebas, 1 fallo `AttributeError: ... has no attribute 'tk'`; GREEN 4 OK con atributos perezosos.
6. RED override GUI histórico: 5 pruebas, 1 fallo `AssertionError: native Tk forbidden`, porque la importación local ignoraba `patch.object(module, 'tk', ...)`; no se abrió ventana. GREEN final: **5 pruebas OK** tras resolver atributos del módulo al construir GUI. Si Tk no está instalado, las dos comprobaciones de compatibilidad que necesitan el paquete se omiten; importación/HTTP/error GUI siguen siendo obligatorias.

## Regresión dirigida sin GUI nativa

Comando, desde la carpeta de aplicación (se importó `ssl` antes de sustituir sockets para evitar afectar a su inicialización):

```sh
PYTHONPATH=tests python -c "import socket,ssl,tkinter,unittest; from unittest.mock import patch; names=['test_session_guards','test_session_transport_boundary_regression','test_session_send_boundary']; suite=unittest.defaultTestLoader.loadTestsFromNames(names); print('Collected',suite.countTestCases(),'tests'); p1=patch.object(socket,'socket',side_effect=AssertionError('sockets forbidden')); p2=patch.object(tkinter,'Tk',side_effect=AssertionError('native Tk forbidden')); p1.start(); p2.start(); result=unittest.TextTestRunner(verbosity=2).run(suite); p2.stop(); p1.stop(); raise SystemExit(not result.wasSuccessful())"
```

Resultado: **13 pruebas OK**, sockets y constructor Tk bloqueados; transporte externo sustituido por conexión sintética cuando correspondía.

También se ejecutaron seis pruebas históricas de widgets **ficticios**, con constructor Tk nativo bloqueado y sockets limitados a loopback (uno de los casos reemplaza todo socket por prohibición):

```sh
PYTHONPATH=tests python -c "import socket,ssl,tkinter,unittest; from unittest.mock import patch; base=socket.socket; Socket=type('LoopbackSocket',(base,),{'connect':lambda self,a: base.connect(self,a) if isinstance(a,tuple) and a[0]=='127.0.0.1' else (_ for _ in ()).throw(AssertionError('external connect forbidden')),'bind':lambda self,a: base.bind(self,a) if isinstance(a,tuple) and a[0]=='127.0.0.1' else (_ for _ in ()).throw(AssertionError('external bind forbidden'))}); names=['test_secure_groq_session.SessionTests.test_gui_requires_explicit_consent_clears_key_and_single_start','test_session_last_slot_lifecycle']; suite=unittest.defaultTestLoader.loadTestsFromNames(names); print('Collected',suite.countTestCases(),'tests'); p1=patch.object(socket,'socket',Socket); p2=patch.object(tkinter,'Tk',side_effect=AssertionError('native Tk forbidden')); p1.start(); p2.start(); result=unittest.TextTestRunner(verbosity=2).run(suite); p2.stop(); p1.stop(); raise SystemExit(not result.wasSuccessful())"
```

Resultado: **6 pruebas OK**; los `READY` de salida son de sesiones sintéticas con transporte cerrado, salvo la última prueba que indica `test_only=False` pero sustituye HTTPS por conexión ficticia y bloquea sockets. Sin ventanas ni conexión real. No se ejecutó toda la suite ni GUI nativa; no se afirma validación visual. La disponibilidad de `pytest` para el Python invocado era falsa; no se instaló nada. Los resultados no implican revisión independiente, ni cierre de prioridad B, ni conexión real a Groq.

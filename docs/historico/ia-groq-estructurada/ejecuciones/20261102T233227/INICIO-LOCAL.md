# Inicio local y alcance de las pruebas

Desde `C:/Users/aleja/Downloads/App Financiera/app`:

```bash
python -B app.py --port 8765
```

Abrir `http://127.0.0.1:8765/` solo mientras el proceso esté en marcha. Este inicio normal no configura ni verifica Groq. No introducir claves en el terminal/chat o en archivos del proyecto. Cerrar el proceso al terminar. No iniciar si el puerto ya pertenece a otro proceso; no detener servicios ajenos.

Para regresión Python sin ventanas, con el intérprete ya instalado que tiene pytest (sin instalar nada):

```bash
'C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe' scripts/run_offline_regression.py --json 'C:/Users/aleja/Downloads/App Financiera/docs/ia-groq-estructurada/ejecuciones/20261102T233227/regression-new.json'
node --test tests/*.test.cjs
```

Usar un nombre de informe nuevo en cada ejecución. Pytest recoge tanto unittest como funciones pytest; sus totales no son directamente comparables con los antiguos 327 unittest parciales. El runner mantiene exclusiones GUI exactas, estados por fase y códigos de salida, sin registrar excepciones crudas. Sus guardas son del proceso Python, no un sandbox heredado por procesos hijos. Documentación completa: `RUNNER.md` en este directorio.

Tres alcances distintos:
- **Inicio normal:** IA no conectada, motor determinista y catálogo de candidatos; no son ofertas aprobadas para comparación cuantitativa.
- **Tests/fixtures:** respuestas y datos sintéticos, servidores de prueba loopback; no demuestran calidad ni conectividad de un modelo.
- **Sesión real futura:** no autorizada por estos comandos. Requiere revisión previa, una misión nueva vigente, confirmación humana de Free y entrada segura voluntaria de clave. Las misiones antiguas han caducado y no se reutilizan. El checkbox Free no verifica técnicamente facturación.

El perfil puede conservar una copia en ese navegador; tras recargar requiere nueva autorización y pulsar Guardar para nuevas escrituras. La autorización local no autoriza transmisión del perfil. Usar datos ficticios en verificaciones.

Estas son instrucciones reproducibles, no constancia de que un servidor siga activo ni de que la regresión actual haya terminado. El resultado real de esta misión estará en RESULTADOS.md.

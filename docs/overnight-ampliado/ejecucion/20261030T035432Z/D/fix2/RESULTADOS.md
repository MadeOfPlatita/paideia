# D fix2 — evidencia local sintética

- Servidor: `python -u tests/serve_d_fixture.py` en loopback `127.0.0.1:57479`; únicamente catálogo sintético, sin proveedor externo ni datos personales.
- Navegador real: cargar `/#privacidad`; evaluar el contenido de `tests/d_fix2_ui.js` en la página. `browser-red.json` muestra ambos fallos observados antes de modificar app.js; `browser-green.json` muestra ambos estados corregidos con caché desactivada. El test de carga intercepta fetch y retiene la respuesta, para observar el DOM mientras `aria-busy=true`.
- `tests/d_fix2_simulation_ui.js`: selecciona primer producto sintético, vuelve atrás y cambia a segundo producto sintético insertado en el catálogo en memoria del navegador; después sale y vuelve a entrar. `simulation-red.json` registra que la confirmación sobrevivía a la navegación; `simulation-green.json` prueba que queda sin marcar. No verifica borrado de todo el formulario: solo la confirmación.
- `simulation-prior-green.json`: prueba existente `tests/d_simulation_ui.js` pasa, incluyendo volver y cambiar importe, justificante ficticio y almacenamiento vacío.
- `privacy-no-network.json`: instrumentación de fetch y XMLHttpRequest durante confirmar, desmarcar y cambiar selección: cero llamadas; botón deshabilitado y checkbox desmarcado. La prueba cubre estas interacciones, no todos los mecanismos de red posibles.
- `node-tests.txt`: comandos reales y salida: `node --check static/app.js` correcto; `node --test tests/*.test.cjs` 33/33 correctos.
- La primera repetición verde usó JavaScript cacheado; se desactivó caché y se repitió, como consta en browser-green.json. La captura visual de pantalla falló por timeout CDP; la evidencia de navegador conservada son los resultados DOM reales en JSON, no imágenes.

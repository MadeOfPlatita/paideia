# Frontend local de Paideia

Superficie principal: **explorar y comparar metadatos**; el cuaderno de ruta y el panel contextual de Pai ayudan a moverse sin presentar una recomendación. Estilo de papel cálido y tinta azul, Georgia local para titulares y Segoe UI/sistema para lectura. Sin fuentes, librerías ni servicios remotos.

## Archivos

- `static/index.html`: shell SPA, navegación hash y CSP de mismo origen.
- `static/styles.css`: diseño responsive, foco visible, objetivos de 44 px, movimiento reducido y reglas de impresión.
- `static/app.js`: rutas, perfil en memoria, catálogo/detalle/comparación/escenarios y estados de API; usa solo DOM seguro (`textContent`, `createElement`), nunca HTML de datos ni perfil en el backend.
- `static/assets/pai-neutral.svg`: copia del SVG de Pai incluido en la documentación visual del proyecto.

## Arranque e integración

Servir desde el backend local del contrato (`127.0.0.1:8765`) y abrir por HTTP, no `file://`. La aplicación espera same-origin para `/api/status`, `/api/catalogue`, `/api/products/{id}`, `/api/compare`, `/api/calculate` y `/api/chat`. El chat se intenta solo después de una acción explícita y envía únicamente el texto escrito; no adjunta el perfil. `/api/context-preview` no se invoca desde la interfaz: el perfil y su vista previa permanecen en el navegador, y ese endpoint se reserva para fixtures sintéticas.

El catálogo solo muestra la respuesta real de la API. El cliente no incorpora candidatos de respaldo, cifras de TAE/TIN/NAV, ranking, tasa, garantía, disponibilidad ni condiciones ficticias. Los datos ausentes se etiquetan como desconocidos o pendientes. La URL primaria se valida como HTTPS antes de presentarse como enlace; la aplicación no la consulta por su cuenta.

## Privacidad y límites

- Perfil opcional por preguntas, editable desde el resumen y mantenido solo en memoria salvo acción explícita para guardar en `localStorage`. El botón global para borrar el perfil está siempre visible; almacenamiento ilegible se descarta con aviso.
- La vista previa de eventual contexto se construye localmente con los campos que el usuario marca. Confirmar el alcance solo lo recuerda en memoria; no transmite nada ni conecta el chat.
- La simulación guarda producto de referencia e importe ficticio solo en memoria, no realiza una operación ni envía el importe. El justificante es HTML imprimible desde el navegador, no un servicio de PDF.
- Este es un prototipo educativo: no hay IA conectada, catálogo listo para publicación, integración bancaria, oferta, recomendación, asesoramiento ni contratación.

## Verificación local

El comando solicitado para JavaScript es `node --check static/app.js`. También se ejecutó una prueba con el test runner integrado de Node para validar rechazo de URL no HTTPS/credentialed y descarte de snapshots de perfil inválidos. La comprobación de navegador/flujo visual queda pendiente del agente principal; este documento no afirma verificación de navegador. Al preparar esta entrega, el directorio del prototipo no contenía `app.py`; por tanto no se pudo probar el recorrido contra la API y queda pendiente al integrar el backend. El servidor backend no forma parte de la propiedad de este frontend.

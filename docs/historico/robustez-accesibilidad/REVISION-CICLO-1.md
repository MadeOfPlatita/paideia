# B9 — revisión independiente del ciclo 1

Dictamen `deleg_d80d844f`, 4 de noviembre de 2026: **passed = false**. El bloqueo no afecta a la privacidad ni al diseño, sino a tres comportamientos concretos que la corrección no cerró del todo.

## Bloqueantes

- **D1 (media) — foco tras reintentar.** En `#escenarios`, pulsar «Intentar de nuevo» con Enter deja `activeElement` en `BODY`, también después de que la petición termine. En `#simulacion` ocurre lo mismo con el reintento del catálogo. Biblioteca, ficha y comparador sí conservan el foco. `app.js:2020-2032`, `2234-2252`, `2445-2452`.
- **D2 (media) — chip de estado obsoleto.** Con `/api/status` retenido y el catálogo ya cargado, aparecen las 20 tarjetas y el chip sigue en «Servicio local sin respuesta» más de ocho segundos después; solo se corrige con otra petición o con «Revisar estado». `app.js:2806-2809`.
- **D3 (media-baja) — envío vacío sin `aria-invalid`.** La validación nativa de `required` cancela el `submit`: el foco va al primer campo, pero no hay `aria-invalid` ni mensaje inline en escenarios y ensayo. Perfil y los errores con valores no vacíos sí cumplen. `app.js:1967`, `2381-2391`, `2584`, `2602-2612`.

## Menores

- **D4** — el stepper no se solapa, pero `hyphens: auto` parte palabras («Condicione/s», «Comprensi/ón»); a 320 px con 200 % quedan 3 px de scroll por la barra superior, no por el stepper.
- **D5** — la región `role=status` del informe se reescribe con el mismo texto en cada pulsación. `comparison_report.js:223`, `251`.
- **D6** — al calcular, el botón enfocado se deshabilita y el foco cae en `BODY`. `app.js:2243`.

## Verificado correcto

Skip-link en las tres rutas con el primer Tab alcanzándolo y sin cambiar el hash; timeouts de 10,2 a 13,2 s con error reintentable y recuperación en estado, catálogo y cálculo; foco conservado al refrescar condiciones; anuncios cortos en una región viva estable; tabla de escenarios sin `aria-live`; confirmaciones A/B que devuelven el foco; un solo POST en escenarios y comparador; jerarquía `h1 → h2 → h3`; informe A/B descargable; biblioteca, ficha, comparador, ensayo, glosario y perfil operativos; los dos arreglos de claridad del historial visibles y sin `history` en el cuerpo al desmarcar. Sin rediseño: el diff de `styles.css` se limita a `.visually-hidden` y al ajuste del stepper.

Pruebas del revisor: B9 24/24, B8 28/28, B1 59 con dos observaciones, 544 pruebas Python, contratos de chat 8/8 y B4 6/6.

## Hallazgo de proceso

El revisor arrancó el servidor con el `.env` presente y una sonda mínima sin datos personales llegó al proveedor real (`external_sent: true`) antes de reiniciar con `PAIDEIA_GROQ_ENABLED=0`. Es la única llamada real de la noche y queda fuera del contador de misión; no valida nada del producto.

## Límites de la revisión

Chrome headless sin lector de pantalla real; el historial se probó con una respuesta de `/api/status` modificada, porque el servidor sin IA lo desactiva.

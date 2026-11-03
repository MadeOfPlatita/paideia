# Paideia — especificación del flujo de simulación y recibo PDF

**Estado:** propuesta de producto/UX para revisión. No es una implementación, una oferta ni un dictamen jurídico.  
**Alcance:** exclusivamente el flujo educativo de simulación, sus estados, el recibo descargable opcional y sus criterios de aceptación.  
**No incluye:** integración bancaria, contratación, asesoramiento personalizado, pagos, firma, persistencia financiera, telemetría ni despliegue.

## 1. Decisiones y límites

### Alcance aprobado en requisitos

- Paideia prioriza cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF para biblioteca/comparador.
- Se aprueba una **simulación dentro de Paideia**, con datos ficticios y sin ejecutar operaciones. No pedir documentos de identidad, credenciales bancarias ni pagos.
- La persona puede usar la aplicación sin registro; el perfil general es local y borrable. El PDF es opcional.

### Decisiones de esta propuesta (pendientes de revisión del equipo)

- Tratar cada recorrido como un ejercicio de cinco pasos compartidos, con textos y comprobaciones de riesgo específicos por familia.
- Mantener los importes del simulador solo en memoria de la pestaña; no guardarlos en el perfil ni transmitirlos.
- Usar `print CSS` como primera opción para el PDF. No incorporar jsPDF salvo que una limitación comprobada de impresión/paginación justifique el coste.
- No fijar aquí una caducidad universal: los requisitos dejan pendiente el criterio por tipo de dato. La política y el umbral de vigencia deben aprobarse para cada campo/familia antes de etiquetar un dato como actual.

Esta especificación no autoriza a mostrar una oferta vigente ni a utilizar datos de terceros sin permiso. La presencia de un producto, su emisor o una fuente en Paideia no significa relación, aval ni recomendación. Las fuentes y fechas deben ser las de la ficha realmente consultada; nunca se inventará un banco, un producto, una cotización o una verificación. Los ejemplos de prueba se etiquetarán como ficticios.

## 2. Lenguaje y límites de la experiencia

Usar «Simulación educativa», «importe de ejemplo», «Finalizar simulación» y «Descargar resumen PDF». Evitar en botones/títulos «Contratar», «Solicitar», «Firmar», «Confirmar operación», «Tu banco» o expresiones que impliquen que se ha aceptado una oferta. La acción final genera un escenario y su resumen, nada más.

Aviso persistente, breve y sereno en todas las pantallas y en el recibo:

> **Simulación educativa. No es una oferta ni una contratación; no se envía ninguna solicitud.**

Presentarlo como texto visible junto al título del flujo, sin alarmas, temporizadores, intersticiales repetidos ni lenguaje de urgencia. Repetirlo en el resultado y el PDF porque estos pueden separarse de la aplicación. No usar logotipos/sellos bancarios, firmas manuscritas, botones que enlacen a contratación o números que parezcan referencias de entidad.

No mostrar selección «mejor para ti», ranking personalizado, asignación, puntuación de idoneidad ni instrucciones de compra. La persona elige el producto o ficha que quiere explorar; los cálculos son deterministas y los datos de producto deben proceder de la ficha/fuente indicada, no de una respuesta del LLM.

## 3. Máquina común: cinco pasos

Las cinco familias usan el orden `seleccion → condiciones → importe_ficticio → comprension_riesgos → cierre_simulado`. «Recibo» es una acción posterior al cierre, no un sexto paso ni una confirmación contractual. El detalle de estados, transiciones, guards y datos por familia está en [`estados.json`](./estados.json).

| Paso | Pantalla y propósito | Avance permitido |
|---|---|---|
| 1. Selección | Elegir una ficha del catálogo o un ejemplo claramente ficticio. No preseleccionar según el perfil ni recomendar. | Hay una ficha identificable y se conoce si sus datos son reales/fuenteados o sintéticos. |
| 2. Resumen de condiciones | Mostrar condiciones materiales, costes conocidos y desconocidos, moneda, fecha efectiva/consulta, fuente primaria y estado de vigencia. No esconder condiciones promocionales o límites. | La ficha tiene fuente/procedencia suficiente para el modo elegido. Si faltan datos esenciales, solo se permite educación general; no fingir un cálculo verificable. |
| 3. Importe ficticio | Campo sin valor inicial, etiquetado «Importe de ejemplo (€); no introduzcas tu saldo real». Pedir horizonte/plazo solo cuando haga falta para ese producto. | Importe > 0 y datos obligatorios presentes. No pedir nombre, edad, DNI/NIE, cuenta, IBAN, tarjeta, firma, empleador ni extractos. |
| 4. Comprensión de riesgos | Explicación corta y pregunta educativa de la familia; ofrecer «No lo sé» y explicar sin avergonzar. Confirmar que se ha leído el resumen de riesgos, no una aceptación legal. | Riesgo mostrado y resumen leído. Si falla/no sabe, explicar y permitir responder de nuevo; no bloquear con mensajes punitivos. |
| 5. Cierre simulado | Recalcular con la misma instantánea de datos revisada; mostrar resultado, estado actual/histórico/sintético, costes y supuestos. | Sin cambios relevantes desde la revisión; cálculo reproducible o resultado marcado como incompleto. Nunca se crea una solicitud, cuenta, orden, lead o transacción. |

Cada pantalla conserva el mismo aviso breve y muestra «Volver» y «Cancelar simulación». El paso activo se anuncia como «Paso X de 5» también para lectores de pantalla. Los detalles extensos se pueden desplegar, pero la fuente/fecha, coste conocido/desconocido y la etiqueta de simulación no se ocultan tras un acordeón.

## 4. Contenido por familia

Los campos se muestran como «dato disponible», «no disponible» o «no verificado»; desconocido no equivale a cero. Las condiciones numéricas, resultados y fechas solo se copian desde la fuente/versionado de la ficha. No se añaden valores ficticios a una ficha real para hacerla parecer completa.

### Cuenta remunerada

- **Selección:** ficha exacta y entidad solo si consta en catálogo verificado; alternativa «ejemplo ficticio» marcada como tal.
- **Condiciones:** TIN/TAE con las etiquetas originales y fecha, tipo fijo/variable/promocional, plazo de promoción, saldo mínimo/máximo remunerado, requisitos o vinculaciones, comisiones/cuota y disponibilidad. Separar la cifra comunicada de cualquier cálculo propio.
- **Importe:** capital de ejemplo y horizonte. Si el tipo cambia por tramos o promociones, aplicar cada tramo solo si sus datos están documentados. No extrapolar un tipo promocional/variable a períodos no cubiertos; ofrecer un escenario parcial o indicar que no puede calcularse el total.
- **Comprensión:** «Si el tipo está sujeto a cambios o a una promoción, ¿puedes dar por hecho que seguirá igual después del período indicado?» Respuesta: no; depende de las condiciones y de los cambios publicados.
- **Cierre:** mostrar resultado bruto con período y condiciones aplicadas. No presentar resultado neto/impuestos si faltan supuestos fiscales; no llamar garantía a la remuneración.

### Depósito

- **Selección:** producto y plazo exactos; distinguir un depósito de una cuenta y de un producto estructurado. Si la clasificación no está verificada, detener el modo producto y pedir revisión de ficha.
- **Condiciones:** TIN/TAE y plazo, fechas, importes mínimo/máximo, abono de intereses, renovación, requisitos/vinculaciones, comisiones y condiciones/efecto de cancelación anticipada.
- **Importe:** capital de ejemplo dentro de límites verificados. El plazo pertenece al producto; no dejar que la interfaz lo cambie como si se mantuvieran las condiciones.
- **Comprensión:** «Si cancelas antes del vencimiento, ¿se conserva necesariamente todo el rendimiento indicado?» Respuesta: no; depende de la condición exacta de cancelación, que debe leerse.
- **Cierre:** declarar expresamente si el escenario asume mantener hasta el vencimiento y que se cumplen las condiciones descritas. Costes no informados se marcan como desconocidos, nunca como cero.

### Letras y otra deuda pública

- **Selección:** tipo de instrumento (letra, bono u obligación), identificador/clase cuando la fuente lo da, vencimiento y naturaleza del dato: subasta primaria, precio secundario, nominal u otro. No llamar cotización actual a un precio de subasta.
- **Condiciones:** precio y base (limpio/sucio si aplica), valor de reembolso, cupón/flujo según corresponda, fechas, vencimiento, fuente y fecha efectiva, comisiones conocidas y costes no disponibles. Distinguir TIR/rendimiento, cupón y TAE; no intercambiar etiquetas.
- **Importe:** capital de ejemplo, vencimiento del instrumento y escenario de mantener o vender antes. Si no hay precio/flujo apropiado para el escenario, no inventarlo.
- **Comprensión:** «Si vendes antes del vencimiento, ¿tienes asegurado recuperar el nominal o el importe inicial?» Respuesta: no; el precio de salida puede variar y el escenario de mantener hasta vencimiento no es el mismo que una venta anticipada.
- **Cierre:** separar precio/flujo de rendimiento calculado y declarar la hipótesis temporal. Si no hay precio de mercado verificable, solo ofrecer el escenario primario/histórico que la fuente respalde, con esa etiqueta; no rellenar con benchmark.

### Fondo de inversión

- **Selección:** clase/ISIN concreta si verificada, divisa y documento de producto aplicable; NAV y fecha separados de cualquier precio de mercado. No asumir que otra clase comparte costes o condiciones.
- **Condiciones:** documento, fecha/idioma, valor liquidativo y fecha, horizonte/documento de riesgos si disponible, costes originales (gestión, depositaría, otros, entrada/salida) y plazos de suscripción/reembolso. Distinguir costes del fondo de los del distribuidor.
- **Importe:** capital de ejemplo y horizonte. Una proyección futura requiere un supuesto hipotético explícito (no una rentabilidad que el sistema atribuye al producto); si no hay supuesto, mostrar costes/ejemplo de mecánica sin pronosticar valor futuro.
- **Comprensión:** «¿El valor liquidativo puede bajar y un escenario positivo garantiza el resultado?» Respuesta: puede bajar; no, un escenario no es garantía.
- **Cierre:** separar datos observados, hipótesis y costes incluidos/excluidos. El TER/OCF no se llama coste total si faltan partidas externas.

### ETF

- **Selección:** clase/ISIN y listing/mercado concretos cuando se conozcan; mostrar ticker, NAV y cotización en campos distintos. Un ticker no sustituye a la identidad de la clase.
- **Condiciones:** divisa, fecha/hora/mercado de cotización, NAV (si hay fuente) separado, costes del fondo, costes conocidos de intermediación/custodia/cambio y diferencial si está disponible. Un coste ausente no se interpreta como 0 €.
- **Importe:** capital de ejemplo e hipótesis de horizonte/variación, siempre identificada como supuesto. No recoger broker, cartera ni instrucción de orden.
- **Comprensión:** «Si el ETF tiene un coste del fondo menor, ¿eso demuestra por sí solo que toda la operación será más barata?» Respuesta: no; pueden existir diferencial y costes de intermediación/custodia/cambio.
- **Cierre:** explicar que el precio de mercado puede variar y que el coste total puede estar incompleto; no generar unidades/orden de compra ni simular liquidez perfecta.

## 5. Datos caducados, cambiados u omitidos

### Vigencia

La fecha visible se descompone, cuando existan, en fecha efectiva publicada (`as_of`) y fecha/hora de consulta (`retrieved_at`). No confundirlas. El catálogo debe registrar fuente/URL por campo relevante y una revisión aprobada para su caducidad. Como los umbrales por familia siguen pendientes, un campo sin política de vigencia verificable se clasifica `unknown`, no `fresh` por defecto.

- **Actual según política aprobada:** se puede simular como escenario de esa instantánea, sin llamarlo oferta ni garantía. Se revalida versión antes de finalizar/exportar.
- **Caducado:** no presentarlo como condición actual ni producir un recibo que parezca vigente. Si se conserva la fuente/instantánea, permitir continuar solo mediante elección explícita «Usar como escenario histórico/educativo»; poner fecha y etiqueta visible en cada resultado/recibo. Si no se conserva, no calcular.
- **Vigencia desconocida o fuente inaccesible:** no mostrar «actual» ni ordenar/comparar como si estuviera verificado. Continuar solo con valores hipotéticos claramente rotulados, sin atribuirlos a la oferta actual; de otro modo, quedarse en la ficha y explicar qué falta.
- **Fuente retirada o producto no disponible:** marcarlo como no disponible; no sustituir silenciosamente por otro producto ni completar con el LLM.

### Dato cambiado durante el flujo

Comparar una revisión/versionado de los campos materiales de producto, costes, moneda, fuente y fecha. Si alguno cambia antes del cierre o PDF: mostrar un aviso neutral («La ficha se ha actualizado; revisa qué cambió»), enumerar cambios relevantes, volver a Condiciones, invalidar resultado y comprobación de comprensión, mantener el importe solo si sigue siendo compatible y exigir revisión explícita. Si cambia moneda o límites esenciales, borrar el importe incompatible y pedirlo otra vez. Nunca recalcular en silencio ni conservar una confirmación anterior sobre condiciones distintas.

### Dato omitido/desconocido

- No rellenar con memoria del modelo, promedio, tasa por defecto ni cero. Distinguir `null`/ausente de `0` y conservar qué campo falta.
- Si falta un dato esencial para identificar la ficha, la fórmula o el período, impedir el cálculo/cierre de producto actual y ofrecer contenido educativo sin resultado.
- Si falta un coste, permitir únicamente resultado bruto si es calculable; rotular «coste total incompleto / no incluido» y no mostrar rendimiento neto ni comparación de menor coste.
- Si faltan impuestos o circunstancias tributarias, omitir cálculo neto y poner «fiscalidad no calculada»; no inferir residencia ni situación personal.
- Se puede «Omitir» una pregunta opcional. El recibo dice «no indicado» y el efecto sobre el alcance del resultado; nunca convertirlo en una respuesta inferida.

## 6. Volver, cancelar y cambiar el importe

- **Volver:** va al paso anterior sin perder entradas ficticias de la sesión. Al cambiar de producto, borrar cálculos, snapshot/condiciones y comprobaciones vinculadas al anterior; no mezclar datos de dos fichas.
- **Cambiar importe:** desde el resultado, «Cambiar importe» regresa al paso 3, conserva la ficha y condiciones y borra resultado/cálculo/comprobación de riesgos anterior. Volver a comprobar rango/unidades, recalcular y repetir la etapa de riesgos antes de finalizar.
- **Cancelar:** botón visible en todos los pasos. Si hay datos introducidos, confirmación breve: «¿Salir de esta simulación? Se borrarán los datos de ejemplo de esta pestaña. No se ha enviado ninguna solicitud». Cancelar el diálogo mantiene el flujo; confirmar vacía estado, valores y resultado en memoria. No se envía llamada de cancelación. El usuario borra manualmente cualquier PDF que ya descargó.
- **Reanudar:** no rehidratar importes/resultados al recargar, cerrar o abrir otra pestaña. Una nueva simulación empieza vacía.

## 7. Recibo exportable

El documento se denomina **«Recibo de simulación educativa»** o **«Resumen de escenario»**, no contrato, justificante bancario, confirmación de operación ni solicitud. No contiene número oficial, número de pedido/transacción, firma, sello, cuenta, beneficiario ni identidad del usuario. No inventar un emisor o producto. Si el escenario usa fixture sintético, imprimir «Datos de ejemplo ficticios»; si usa producto documentado, imprimir la fuente real exacta y aclarar que la ficha no es una oferta ni respaldo de Paideia.

### Contenido mínimo

1. Título y aviso persistente: «Simulación educativa. No es oferta ni contratación; no se envía ninguna solicitud».
2. Fecha/hora de generación local, con zona horaria indicada; **no** usarla como fecha efectiva del producto.
3. Familia, nombre exacto de la ficha, emisor solo si la ficha lo verifica, clase/ISIN cuando conste y etiqueta de datos `verificados`, `históricos`, `vigencia desconocida` o `ficticios`.
4. Fuente por campo/condición material: entidad o documento, URL, fecha efectiva (`as_of`) y consulta (`retrieved_at`), moneda. Si una fuente/fecha falta, declararlo; no generar una cita aparente.
5. Inputs ficticios (importe, período/horizonte, escenario elegido) y estado de campos omitidos. Sin información de perfil personal ni campos de destinatario.
6. Costes conocidos, quién los cobra si consta, períodos/unidades y costes desconocidos/no incluidos; indicar si el resultado es bruto. No representar ausencias como 0.
7. Resultado y método/supuestos utilizados, período, redondeo de salida y limitaciones (por ejemplo, fiscalidad excluida, condiciones promocionales no extrapoladas, venta antes de vencimiento, hipótesis de variación). Separar dato observado de supuesto hipotético.
8. Cierre claro: «Documento educativo creado por Paideia; no acredita relación con una entidad ni una operación. No es contrato ni oferta. Ningún dato se ha enviado a una entidad». Esta última frase solo se usa si la exportación realmente es completamente local; si hubiera una excepción técnica, no se publica hasta resolverla.

La generación requiere gesto explícito («Descargar resumen PDF»). No se genera ni se envía automáticamente. El flujo no hace POST, no abre enlace transaccional, no añade píxeles/recursos remotos, no envía telemetría y no adjunta perfil ni conversación. No incluir datos del ejercicio en metadatos PDF, nombre de archivo, URL, nombre de error ni logs. Nombre genérico sugerido: `paideia-resumen-simulacion.pdf`; el navegador decide la carpeta. La descarga es una copia local controlada por la persona; Paideia no puede borrar copias descargadas.

## 8. Estrategia de PDF: print CSS frente a jsPDF

### Opción propuesta para MVP: HTML semántico + print CSS

Usar una vista previa HTML accesible y una hoja de impresión con `@media print` / `@page`, invocando la impresión del navegador tras pulsar «Imprimir / Guardar como PDF». Ventajas para un recibo textual corto: una fuente de contenido, texto seleccionable/buscable, soporte nativo de Unicode/tildes, menor superficie de dependencias y ningún renderer adicional. Ocultar controles de UI en impresión, usar una columna, márgenes legibles, enlaces de fuente visibles, evitar cortes de filas/bloques y mantener el aviso en el documento.

Límite: el navegador o dispositivo decide el diálogo y las opciones «Guardar como PDF»; especialmente en móvil no debe prometerse que todos los navegadores ofrecerán la misma acción. Mostrar la vista HTML igualmente y no declarar «PDF descargado» hasta que la acción del navegador haya funcionado. No abrir impresión automáticamente. No depender de encabezados/pies ni de contadores de página CSS inconsistentes para datos críticos.

### Cuándo considerar jsPDF (no incluido en esta entrega)

Solo si la prueba en navegadores objetivo demuestra que la impresión no permite cumplir una paginación o descarga directa necesaria. La generación sería local, tras gesto explícito, con una fuente Unicode realmente embebida y probada; no descargar fuentes desde CDN ni enviar datos a un servicio PDF. Validar saltos de página, enlaces, orden de lectura, texto seleccionable, metadatos vacíos de identidad y salida con tildes/euro. Aumenta el riesgo de tipografía truncada, peso de bundle, accesibilidad y diferencias entre navegadores; no usar fuente estándar sin comprobar `áéíóúüñ¿¡€` en todos los visores.

## 9. Legibilidad, móvil, accesibilidad y privacidad

- Probar la pantalla a 320, 360/390 y 768 CSS px, zoom 200–400 %, orientación vertical/horizontal y teclado. Sin scroll horizontal de página, contenido cortado, campos pequeños ni botón fuera del viewport; controles con etiqueta persistente, foco visible y errores en texto.
- Probar la vista impresa/PDF en A4 y en escala de grises, al menos en un navegador de escritorio y Safari iOS/Chrome Android disponibles para el equipo. Cuerpo del documento objetivo ≥11 pt y metadatos/nota ≥9 pt; sin texto superpuesto, truncado o con contraste insuficiente. Los riesgos no se comunican solo por color.
- Verificar visualmente las cadenas exactas `áéíóúüñ ÁÉÍÓÚÜÑ ¿¡ €` y una frase de prueba («Simulación educativa; comisión, vencimiento y depósito»); extraer/buscar texto PDF si es viable y contrastar que no se sustituyan tildes, signos o símbolo euro.
- El simulador procesa valores en memoria de la pestaña. No guardar en `localStorage`, `sessionStorage`, cookies, URL, perfil, chat, analítica, trazas o informes de error. No incluirlos en solicitudes de red, incluido el PDF; catálogo puede cargarse por separado pero no recibe el importe.
- No pedir ni transmitir DNI/NIE, IBAN, tarjeta, firma, credenciales, nombre, correo, teléfono, cuenta bancaria ni intención de compra. No hay marketing, contacto, afiliación ni envío comercial. Un texto pegado accidentalmente se queda en el navegador, no se adjunta a un LLM.
- Al cancelar, finalizar o borrar la pestaña, eliminar el estado en memoria. No afirmar que esto elimina el archivo que la persona descargó.
- Cumplir como objetivo de diseño WCAG 2.2 AA; la conformidad no se presume por una especificación ni por pruebas automáticas. Ejecutar evaluación manual de teclado, lector de pantalla, contraste, reflow y mensajes de estado antes de publicar.

## 10. Verificación y pendientes

La lista verificable está en [`CASOS_ACEPTACION.md`](./CASOS_ACEPTACION.md). Se definen escenarios y evidencias requeridas; como no hay app de producción en este alcance, **no se afirma que las pruebas funcionales o de PDF se hayan ejecutado**.

Pendientes antes de llevarlo a una implementación o demo con productos reales:

1. Aprobación de los textos y de la política por familia para caducidad, `as_of` y costes desconocidos.
2. Revisión del catálogo/fuentes, exactitud de clase/documento y derechos de exhibición/redistribución.
3. Revisión profesional española del lenguaje y del encaje normativo antes de cualquier publicación; el disclaimer no sustituye esa revisión.
4. Probar print CSS en dispositivos reales disponibles. Evaluar jsPDF solo si la evidencia muestra un bloqueo funcional.
5. Mantener bloqueada cualquier operación real, solicitud de cliente o conexión bancaria: no forma parte de este diseño.

## Referencias internas de alcance

- [`../../REQUISITOS.md`](../../REQUISITOS.md), §§ Público y experiencia, Productos y datos, Funciones solicitadas, Privacidad y operación, alcance aprobado y validaciones pendientes (en particular simulación ficticia y sin datos bancarios; fecha/fuente; caducidad aún por definir; PDF opcional).
- [`../../investigacion/10-seguridad-calidad.md`](../../investigacion/10-seguridad-calidad.md), §§ 5, 41–46, 68–95: memoria, no operación, pruebas de privacidad/accesibilidad; documento de diseño, no pruebas ejecutadas.
- [`../../investigacion/09-rigor-financiero.md`](../../investigacion/09-rigor-financiero.md), §§ 55–96 y 126–136: métricas separadas, costes, fuentes y límites; no es autorización ni dictamen jurídico.
- [`../../investigacion-apis-02/07-deuda-instrumentos.md`](../../investigacion-apis-02/07-deuda-instrumentos.md) y [`../../investigacion-apis-02/03-etf-emisores.md`](../../investigacion-apis-02/03-etf-emisores.md): diferencias de fuente, fecha y tipo de precio/dato; sus comprobaciones no validan una integración ni derechos de redistribución.

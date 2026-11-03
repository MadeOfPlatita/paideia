# Paideia — especificación del laboratorio de escenarios

**Alcance:** diseño y metodología de la visualización; no es implementación de la interfaz ni recomendación financiera. El catálogo de productos reales y sus datos no se sustituye por estos ejemplos. La persona elige qué alternativa explorar; no hay ranking de «mejor para ti».

## 1. Principio del laboratorio: dos capas que nunca se mezclan

1. **Hecho del producto:** solo dato verificado del producto/clase exacta, con valor, unidad, fuente primaria, fecha de consulta, fecha de vigencia y condición. Ejemplos: flujos y plazo de un depósito, precio y vencimiento de una Letra, costes/KID de una clase de fondo, o precio/mercado y costes del ETF. Un dato ausente o caducado aparece como «no verificado»; no se rellena con una hipótesis ni con el LLM.
2. **Hipótesis del escenario:** aportaciones, inflación, costes desconocidos y bandas de rentabilidad que la persona modifica. Etiqueta persistente: **«Supuesto editable · no es dato del producto, previsión ni probabilidad»**.

Los productos reales permanecen seleccionables y comparables. Los campos de producto verificados se muestran en un panel separado; los supuestos no cambian ni sobreescriben su ficha. Los tres casos de `escenarios-ejemplo.json` son enteramente sintéticos para reproducir la mecánica, no sustitutos de ofertas ni cotizaciones reales. Ningún producto real se eliminó ni se «fictivizó» en este trabajo. Los controles de objetivo, plazo y riesgo sirven para aprender y ordenar la exploración, no para decidir qué producto encaja; la CNMV también señala objetivo, plazo y riesgo como elementos de la decisión de inversión.[4]

## 2. Controles y unidades

La familia la elige la persona: cuenta remunerada, depósito, Letra/deuda, fondo o ETF. Después puede escoger productos concretos de la biblioteca real y comparar hasta tres, sin ganador predeterminado. El selector de producto no convierte la comparación en idoneidad ni en selección personalizada.

| Control editable | Regla de visualización y validación |
|---|---|
| Producto/familia | Mostrar primero hechos verificados y su fuente/fecha; separar «dato del producto» de «supuesto del escenario». Mantener las familias reales disponibles. |
| Fecha inicial y final/horizonte | Fecha de valoración y fecha final iguales para las alternativas comparadas. En productos contractuales, enseñar además la fecha de vencimiento real. No extender el resultado más allá de la fecha contractual sin una nueva hipótesis explícita. |
| Aporte inicial y aportes periódicos | EUR, importe, frecuencia y fecha de cada flujo. Convención didáctica por defecto: aportación al final del mes, que no obtiene rendimiento ese mismo mes. Solo se aplica si el producto admite ese flujo; de lo contrario se marca «no comparable con esta pauta» en vez de inventar reinversión o aportaciones. |
| Costes | Separar coste inicial, por operación, custodia/intermediación/spread si corresponde y coste anual sobre saldo. Mostrar importe/unidad, quién lo cobra y fuente/fecha. Coste desconocido = «incompleto»; no asumir cero. El ejemplo imprime los cargos modelados aparte del saldo. |
| Inflación | Porcentaje anual efectivo editable, claramente rotulado como supuesto; presentar nominal y euros de poder adquisitivo de la fecha inicial. No llamarlo inflación prevista. |
| Retirada | Importe, frecuencia, primer periodo y si se indexa o no con la inflación. Acordar la fecha frente al rendimiento y los costes. Si no hay saldo suficiente, limitar el pago al saldo disponible y exponer el importe no cubierto; nunca crear saldo negativo para «completar» una retirada. |
| Supuestos de mercado | Banda baja, central y alta manuales, con rendimiento nominal efectivo anual antes de costes. Son recorridos deterministas de sensibilidad, no probabilidades, percentiles, media, escenarios más probables ni intervalos estadísticos. Cada banda se puede editar y se puede borrar/restaurar. |
| Fiscalidad | Excluida por defecto. Solo añadir una salida después de impuestos con ejercicio, supuestos fiscales y fuente identificados; nunca mezclarla silenciosamente con el bruto. |

**Comparabilidad:** EUR; misma fecha de valoración y fecha final; misma pauta y calendario de aportaciones/retiradas, y mismas convenciones de momento de flujo. Distinguir tasa anual efectiva, tasa por periodo, porcentaje anual sobre saldo, coste fijo en euros y coste por transacción. El rendimiento contractual, el resultado nominal, el resultado real y el resultado después de costes/impuestos son columnas distintas. Si el producto no admite un flujo o su dato no está completo, mostrar la limitación en lugar de comparar cifras con bases diferentes.

## 3. Motores financieros separados

### A. Flujo contractual: depósito o Letra

Para un depósito se representa el calendario contractual del producto exacto: importe, fechas, tipo(s), capitalización/pago, condiciones de vinculación, límites y costes. El motor no extrapola una TAE de promoción a plazos posteriores ni inventa renovación; si el tramo posterior no está en las condiciones verificadas, se detiene en ese vencimiento. El Banco de España explica que el cálculo de la TAE se basa en interés compuesto y en la hipótesis de reinvertir los intereses al mismo tipo; por eso se conserva como dato comparativo de sus condiciones y no se convierte automáticamente en un flujo contractual futuro.[1]

Para una Letra se parte del **precio efectivamente pagado** y del **reembolso nominal en su fecha de vencimiento**; el Tesoro describe precisamente la diferencia entre precio de adquisición y valor de reembolso como el rendimiento.[2] Si se muestra una anualización, etiquetarla «rendimiento anualizado del flujo (no TAE)», indicar las fechas/base de días y costes, y no equipararla a TAE de depósito. Mantener a vencimiento y vender antes son casos diferentes: una venta anticipada solo se simula con un precio de salida fechado y verificado, no con el nominal futuro. No se renueva automáticamente una Letra al vencimiento.

**Tratamiento promocional:** mostrar plazo promocional, periodo posterior y requisitos en líneas/segmentos separados. Si la oferta solo está verificada para los primeros meses, la gráfica contractual termina ahí. El laboratorio no anualiza ese tramo para pintar años futuros.

### B. Hipótesis de mercado: fondos y ETF

La familia y la ficha pueden ser reales, pero las rentabilidades de los recorridos son supuestos elegidos por la persona. No se extrapola la rentabilidad pasada de una ficha ni se usa el escenario moderado de un KID como valor central, previsión o promesa. Se puede enlazar el KID como documento de producto, acompañado de su contexto, sin copiar sus escenarios al motor didáctico. La norma europea exige evitar que los escenarios PRIIPs se interpreten como previsiones de la mejor estimación y pide hacer visibles sus hipótesis.[3]

Para que el JSON de muestra sea reproducible, usa tasas efectivas nominales anuales constantes por tramo y conversión mensual `factor_mes = (1 + r_anual)^(1/12)`. El coste anual sobre saldo se aplica por mes mediante `(1 - coste_anual)^(1/12)`. En cada mes: revalorizar saldo → deducir coste de saldo → añadir aporte de fin de mes → atender retirada de fin de mes hasta el efectivo disponible. Si coinciden aporte y retirada, la regla de orden se anuncia; en el ejemplo de retiradas no hay aportaciones periódicas.

En la fecha `m`, el valor real es `saldo_nominal / (1 + inflación_anual)^(m/12)`. La aportación real acumula cada aporte deflactado según su propia fecha, no compara una suma nominal de aportes de diez años con un saldo real de fecha inicial. Para hacer visible un resultado negativo, el resumen muestra por separado aportado, saldo final, retiradas pagadas, retiradas pendientes y diferencia frente a lo aportado. No se presenta pérdida hipotética como saldo de deuda.

**Etiquetas prohibidas para estas curvas:** «esperado», «probable», «garantizado», «rentabilidad que obtendrás» o «predicción». Usar «supuesto bajo / central elegido / alto», con «no son probabilidades» junto a la leyenda. No usar una campana, abanico probabilístico ni una escala de porcentaje de confianza si no hay una metodología probabilística válida.

## 4. Gráfico, tabla y diagramas de interfaz

### Decisión: SVG propio, estático y vectorial

Para esta demo elegiría SVG propio, no Chart.js/ECharts. El gráfico es una visualización ligera de pocas series, sin zoom ni selección de puntos: SVG mantiene líneas y texto vectoriales al imprimir; con `viewBox` puede adaptarse al ancho móvil; y evita cargar una biblioteca. El gráfico no será el control de interacción: los controles nativos HTML actualizan sus valores, el resumen y la tabla. La ruta de teclado llega a toda funcionalidad, las etiquetas visibles identifican controles y la tabla es la alternativa semántica completa.[6][8] El SVG lleva título y descripción breve; una tabla HTML con `caption`, encabezados y unidades contiene todos los puntos y no depende de color. Los objetivos táctiles deben respetar el mínimo WCAG aplicable y se diseñarán preferiblemente más amplios para móvil.[7] Revisar contraste de texto/estados conforme al criterio aplicable, no solo los colores de las curvas.[5]

El SVG es **no interactivo** y nunca la única representación: línea continua/discontinua/punteada y rótulo directo identifican cada recorrido además del color; resumen en lenguaje llano declara la diferencia principal. Para un flujo contractual, dibujar los flujos como hitos entre inicio y vencimiento, no como una curva suave con rendimientos intermedios inventados. La tabla se puede alcanzar con enlace «Saltar a la tabla», conserva encabezados al imprimir y, en móvil, tiene desplazamiento horizontal local con indicación explícita, no desborda toda la página. Sliders se acompañan de campo numérico con la misma etiqueta y unidad; foco visible, sin cambios automáticos de pantalla ni información solo al pasar el ratón.

En impresión, ocultar sliders/botones, convertir controles a texto de sus valores actuales e imprimir fecha, fuente, hipótesis, advertencias, SVG y tabla. No imprimir solo la captura del canvas/gráfico. Esta propuesta aún requiere prueba real de impresión en navegador y lector de pantalla.

### Escritorio (diagrama textual)

```text
┌ LABORATORIO · «Explora supuestos, no predicciones» ──────────────┐
│ [Familia: Fondo ▼] [Producto real: nombre/clase ▼] [Comparar +] │
├─ HECHOS DEL PRODUCTO ───────────┬─ SUPUESTOS EDITABLES ─────────┤
│ Fuente · fecha efectiva          │ Aporte inicial / periódico   │
│ Riesgo · liquidez · costes       │ Frecuencia · horizonte       │
│ KID/condiciones · límites        │ Costes hipotéticos · inflación│
│ [abrir ficha original]           │ Retirada · banda manual      │
├─────────────────────────────────┴───────────────────────────────┤
│ [SVG: aportado vs saldo; nominal/real; series rotuladas]        │
│ Resumen: aportado €… · saldo €… · retirado €… · pérdida posible │
│ [Tabla completa: fecha | aportado | saldo nominal | saldo real] │
└─────────────────────────────────────────────────────────────────┘
```

### Móvil (diagrama textual)

```text
[Laboratorio · no es una previsión]
[Familia ▼] [Producto real ▼]
[Hechos verificados: fuente + fecha + detalle]
[Supuestos: aporte] [frecuencia] [horizonte]
[costes] [inflación] [retirada] [banda]
[SVG responsivo, con rótulos directos]
[Resumen textual: aportado / saldo / pérdida o faltante]
[Tabla equivalente, desplazamiento local si hace falta]
```

## 5. Tres escenarios didácticos explícitos

Los cálculos siguientes son salida ejecutada de `reproducir_escenarios.py`, antes de impuestos. No describen condiciones actuales ni productos reales. Las bandas no tienen probabilidades.

1. **Contrato a vencimiento — depósito frente a Letra sintéticos.** Mismo desembolso inicial de 4.900 €, mismas fechas (01-11-2026 a 01-11-2027), inflación supuesta del 3%, costes cero y sin impuestos/reinversión. El depósito didáctico cobra 5.017,60 € nominales; la Letra didáctica reembolsa 5.000 €. En euros de la fecha inicial equivalen a 4.871,46 € y 4.854,37 €: el resultado nominal supera el desembolso, pero la pérdida de poder adquisitivo relativa a los 4.900 € iniciales es 28,54 € y 45,63 €. Es un ejemplo de flujos hipotéticos, no dos ofertas.
2. **Aportar sin retirar — fondo/ETF como mecánica de mercado.** 1.000 € iniciales + 100 €/mes al final de mes durante 120 meses; coste anual supuesto 0,6%, inflación 2%, sin costes de operación ni impuestos. Tasas manuales constantes antes de costes: −4%, +4%, +8% anual. Se aportan 13.000 € nominales (11.877,56 € en euros de la fecha inicial). Saldos finales nominales: 10.226,19 €, 15.606,34 €, 19.451,58 €; valores reales: 8.389,04 €, 12.802,63 €, 15.957,07 €. La banda baja termina por debajo de las aportaciones incluso en nominal (−2.773,81 €); el punto «central» no es una estimación de lo que ocurrirá.
3. **Retirar con caída temprana — posible agotamiento.** 10.000 € iniciales, retiradas de 150 €/mes durante 60 meses desde el mes 1, coste anual 0,6%, inflación supuesta 2,5%, sin aportes ni impuestos. Recorrido bajo: −25% el primer año y +5% anual en los cuatro siguientes; central elegido: +4% anual; alto: +8% anual. En el bajo solo se pagan 8.141,25 € de los 9.000 € solicitados; faltan 858,75 € y el saldo termina en cero. En el central se pagan 9.000 € y quedan 2.029,25 €; en el alto se pagan 9.000 € y quedan 3.486,69 €. Son secuencias deterministas para enseñar riesgo de mercado y de retiradas; no asignan ninguna posibilidad a cada resultado.

Entradas y salidas completas, con series anuales, quedan en `escenarios-ejemplo.json`. Para reproducir/verificar desde este directorio: `python reproducir_escenarios.py --check`. Para recalcular y actualizar el JSON: `python reproducir_escenarios.py --write`.

## 6. Criterios de aceptación del diseño

- El mismo cambio de input actualiza resumen, SVG y tabla; la persona distingue sin leer letra pequeña entre hecho real, hipótesis y resultado calculado.
- Aportes y resultado no se confunden: se ven capital aportado, saldo, retiradas y diferencia; una salida negativa o retirada no cubierta queda rotulada, sin verde/rojo como único canal.
- Un depósito promocional termina en su periodo verificado; una Letra no se renueva; la venta antes de vencimiento necesita un precio de salida real separado.
- Las curvas de fondos/ETF se explican como supuestos manuales; KID moderado, rentabilidad pasada y TAE promocional no rellenan el supuesto central.
- Fechas, frecuencia, divisa, unidades, costes, inflación y base nominal/real están a la vista. La comparación neutral no se ordena por rendimiento ni produce «mejor para ti».
- Teclado: todos los controles se editan y se restablecen sin ratón, con foco visible y sin trampas; cada control tiene etiqueta e instrucciones. El SVG no es el único acceso a ningún dato. Probar contraste, móvil sin scroll global, tabla en lector de pantalla y versión impresa.
- Test de personas novatas: pueden indicar cuánto aportaron, qué supuso el resultado, cuánto podrían perder/no retirar y por qué la banda central no es una predicción.

**Estado de verificación:** se ejecutó el reproductor stdlib y se compararon sus resultados con las salidas guardadas; los ejemplos y sus invariantes pasan. No se construyó frontend ni se ejecutaron pruebas visuales, de responsive, teclado, lector de pantalla o impresión; quedan como aceptación de implementación.

## Sources

[1] https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/relacionados/tiposinteres/guia-textual/latae/tae_deposito.html
[2] https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/letras-del-tesoro
[3] https://eur-lex.europa.eu/eli/reg_del/2021/2268/oj/spa
[4] https://www.cnmv.es/portal/inversor/decisiones-inversion?lang=es
[5] https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
[6] https://www.w3.org/WAI/tutorials/forms/labels
[7] https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
[8] https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html

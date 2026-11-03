# Diseño del comparador trazable (propuesta v1)

**Estado:** diseño para revisión; no acredita implementación. **Ámbito:** catálogo y comparaciones educativas en España, sin operación de contratación. Los escenarios y pruebas son ficticios.

## 1. Encaje con lo ya acordado

- **Ya requerido/aprobado:** comparar productos concretos; priorizar cuentas remuneradas, depósitos, Letras/deuda pública, fondos y ETF; mostrar fuentes, fecha efectiva/consulta, disponibilidad y condiciones; cálculos reproducibles y supuestos visibles; no inventar datos; no operar ni usar credenciales reales. «El 90% de los más populares» sigue sin universo ni métrica y no permite afirmar cobertura.[REQUISITOS.md §§Productos y datos, Alcance inicial]
- **Ya establecido como límite de diseño:** criterios iniciados y controlados por el usuario, explicaciones trazables, datos caducados fuera de una comparación engañosa, no ordenar familias distintas por una sola cifra, ni seleccionar productos según perfil ni llamar idoneidad a una salida educativa.[09-rigor-financiero.md §§1, 3, 4, 5]
- **Propuestas nuevas aquí (necesitan aprobación):** taxonomía/subfamilias exactas; estados de contratación y elegibilidad; políticas por campo para desconocido/caducado; métrica de comparación permitida por familia; tratamiento de costes parciales; desempate; y plazos máximos de vigencia por campo/fuente. No fijar caducidades ni un «producto ganador» por defecto sin aprobarlos.

Este texto aplica las referencias primarias ya recogidas en `../../investigacion/09-rigor-financiero.md` (p. ej., Banco de España [7][8], Tesoro [12], FGD [13], CNMV [9][10][23] y Ley 6/2023/MiFID II [17][18][19]). No es dictamen jurídico ni sustituye revisar fuentes y condiciones vigentes antes de publicar.

## 2. Qué compara y cómo agrupa

### Familias separadas

Propuesta de grupos que evita mezclar métricas de naturaleza diferente:

1. `remunerated_account` — cuenta remunerada.
2. `term_deposit` — depósito a plazo.
3. `treasury_bill` — Letras del Tesoro.
4. `government_bond` — bonos/obligaciones de deuda pública; desglose propuesto dentro de deuda pública.
5. `mutual_fund` — fondo no cotizado, conservando clase exacta.
6. `etf` — ETF, conservando clase/ISIN y mercado.

`government_bond` como grupo separado y el nivel «familia/subfamilia» son decisiones propuestas: los requisitos aprueban deuda pública, no esta taxonomía exacta. Una cuenta y un depósito a plazo no se fusionan por ser depósitos: sus condiciones de acceso, remuneración y salida son distintas. No inferir equivalencia solo por nombre comercial.

### Cohortes comparables dentro de familia

El modo numérico requiere mismo grupo y unidad económica suficientemente homogénea: clase/ISIN o contrato inequívoco, moneda, fecha de valoración, importe, horizonte y base de flujo comunes; métrica coherente con la familia; y datos esenciales vigentes. Ejemplos de métricas adecuadas por separado:

| Grupo | Métrica que puede mostrarse, con etiqueta y supuestos | No presentar como |
|---|---|---|
| Cuenta/deposito | TIN/TAE reportada; euros brutos calculados para importe/plazo y condiciones concretas | rentabilidad futura garantizada o TAE comparable a TIR |
| Letras | diferencia precio–reembolso y rendimiento anualizado/TIR a vencimiento, días y precio observados | TAE de depósito ni resultado de venta anticipada |
| Bono/obligación | cupón separado de TIR a precio/fecha, manteniendo vencimiento como hipótesis | rentabilidad realizada si se vende antes |
| Fondo | rentabilidad/valor liquidativo de clase y fecha comparables, con costes/riesgo aparte | precio intradía o depósito |
| ETF | retorno de precio/NAV claramente especificado, clase/mercado/fecha y costes de negociación aparte | retorno del índice o coste total reducido al TER |

La métrica común no borra las diferencias de riesgo, garantía, liquidez, tributación o condiciones. TAE, TIR, cupón, NAV y precio de mercado no son intercambiables.[09-rigor-financiero.md §3, referencias [7][9][10][12][22][23]]

### Entre familias: informativo, no ranking

**Permitido:** una matriz descriptiva lado a lado, organizada por familia, que exponga plazo, tipo de salida, incertidumbre del valor, coste conocido, divisa, protección/garantía y fuente. Si se calculan euros para un mismo importe y fecha, etiquetar cada cifra por su métrica, hipótesis y base de coste/impuesto; dejar claro que no es ordenación homogénea.

**Numéricamente inválido como ranking:** comparar directamente TAE de depósito con TIR de una Letra/bono, cupón, rentabilidad histórica/NAV de fondo, retorno de ETF o escenario PRIIPs; asignarles una puntuación única; u ordenar el conjunto por «rentabilidad», «riesgo» o «mejor». Cambian flujos, incertidumbre, valoración, liquidez, garantía, costes y/o horizonte. Igual importe/plazo no basta para hacerlos equivalentes.

**Excepción acotada:** una simulación común de flujos puede calcular importes hipotéticos a una fecha común solo si todas las entradas, costes aplicables y supuestos están completos y comparables. Debe aparecer como **escenario matemático condicionado**, no como ranking, previsión, rendimiento esperado ni recomendación. La UI conserva grupos separados y no muestra puesto global. Si falta una hipótesis esencial, solo vista descriptiva.

## 3. Orden y filtros controlados por el usuario

1. El usuario elige familias, producto/criterios de inclusión, importe, horizonte, fecha, filtros y métrica/columna por la que ordenar; puede cambiar el orden en cualquier momento. El formulario permite «desconocido/no sé» y «omitir».
2. No se crean ponderaciones, score total, orden «recomendado», patrocinio, «mejor para ti» ni valores por defecto derivados de ingresos, edad, deuda, tolerancia o capacidad de pérdida.
3. En cada familia, la ordenación usa solo el `sort_by` explícito. Nulos y desconocidos van al final en ambas direcciones; no se convierten en cero. Si hay igualdad exacta, desempate estable por `product_id` ascendente (código inmutable), mostrando `TIE_BREAK_PRODUCT_ID`. No usar aleatoriedad, orden de llegada ni resultado del LLM. Si no hay criterio elegido, ordenar por nombre normalizado y después ID, indicando «orden alfabético (no recomendación)».
4. Orden fijo de presentación entre grupos: el orden canónico de familias de este documento, nunca un orden de preferencia. La persona puede reordenar grupos visualmente; no se interpreta como recomendación.
5. `rank` solo existe dentro de una cohorte marcada `numeric_within_family` y para una métrica seleccionada. En las vistas interfamiliares/incomparables `rank = null`; resultados filtrados se muestran aparte, sin número de puesto.

### Contratación, residencia y liquidez

Son filtros independientes, no una afirmación de idoneidad:

- **Contratación:** estado documentado (`open`, `closed`, `unknown`) y canal (`online`, sucursal, intermediario, etc.) con fecha/evidencia. Estar abierto no prueba elegibilidad del usuario. «Contratable» no significa que se pueda ejecutar la contratación en Paideia.
- **Residencia:** país declarado voluntariamente por la persona (o `unknown`) frente a países/condiciones documentados del producto. No inferir residencia desde idioma, IP ni mercado de referencia español. Desconocido jamás equivale a elegible. Política elegible elegida explícitamente: `exclude`, `include_labeled` u `only_unknown`; propuesta inicial segura para un filtro estricto: `exclude` y explicar el motivo.
- **Liquidez:** comparar fecha en que se necesita disponibilidad con vencimiento/ventana de reembolso/plazo de liquidación, penalización y posibilidad de venta a precio de mercado. No equiparar «cotiza» con «liquidez sin pérdida». Si el dato de salida está desconocido, un filtro duro no puede darlo por superado.
- Registrar en la respuesta qué filtros se aplicaron, qué productos se excluyeron y por qué. «No se pudo verificar» se distingue de «no cumple».

## 4. Costes, fechas, garantías y estados

### Costes por alcance de cálculo

Estado de costes se calcula para cada producto **y consulta** (importe, horizonte, canales y operaciones):

- `complete`: todos los cargos pertinentes al alcance están cuantificados o documentados como `not_applicable`; distinguir incorporados en el valor liquidativo/tipo de los cobrados aparte y condicionales.
- `partial`: al menos un componente aplicable/desconocido o una condición de cobro no cuantificable.
- `unknown`: no se puede determinar cobertura de costes.

Componentes a registrar cuando correspondan: gestión/depositaría y otros costes del producto, cuenta/administración, custodia, suscripción/reembolso, compraventa, diferencial, cambio divisa, vinculación, saldo/tramos, cancelación/salida y comisiones de intermediación. «No informado» nunca se transforma en cero ni en «no aplicable».

Con costes parciales/desconocidos se permite ordenar por una cifra **bruta expresamente elegida** (TAE reportada, cupón, etc.) dentro de su cohorte, con rótulo visible «coste total incompleto»; prohibido afirmar menor coste, rendimiento neto o ganador total. Ordenar por `net_return` o coste total exige todos los componentes pertinentes completos y misma base. Impuestos son capa aparte: por defecto comparación bruta; estimación neta exige residencia y ejercicio fiscal declarados, reglas documentadas y supuestos visibles; si faltan, bloquear la cifra neta (`TAX_BASIS_UNKNOWN`).

### Fechas, fuente y cambio de condiciones

Cada hecho usado conserva el dato literal/valor normalizado, unidad, fuente primaria URL/documento, localizador, clase/ISIN, consultado `observed_at`, vigente `effective_from/effective_to` y política `max_age` por tipo de dato. Renderizar al menos «dato vigente desde», «verificado el», «fuente» y, cuando proceda, «próxima revisión». Fecha de consulta no sustituye fecha efectiva.

La caducidad depende de una política por campo pendiente de aprobación (no fijar un único TTL diario para todos los campos). Si caduca dato esencial de elegibilidad, precio, tasa, costes o condición, no se recalcula ni ordena numéricamente con él: mostrarlo como caducado y ofrecer datos descriptivos identificados con fecha, si no inducen a error. Si cambia una condición, crear versión nueva del producto; invalidar snapshots y cálculos dependientes, ejecutar de nuevo filtros y marcar `CONDITIONS_CHANGED`. No reescribir resultados ya guardados como si se hubieran calculado con lo nuevo.

### Garantías y protección

Mantener dimensiones separadas: flujo contractual (qué pago, a qué vencimiento y bajo qué condiciones), cobertura de garantía de depósitos (entidad, titular, límites/cobertura y elegibilidad) y riesgo de precio/mercado/custodia. Estados: `documented`, `conditional`, `none_documented`, `unknown`. Faltan alcance, entidad, límite o condición = no afirmar «garantizado». Un escenario de KID es ilustración, no garantía. Cobertura de depósitos no protege de pérdidas de mercado en fondos/ETF. Mostrar fuente y ámbito de cada afirmación; no convertir toda la deuda pública en «capital garantizado» sin precisar emisor, vencimiento y venta anticipada.[09-rigor-financiero.md §3, «Garantía contractual, garantía de depósitos y escenario»]

## 5. Separación de educación y selección regulada

El comparador admite personalización **por decisiones de la propia persona**: familias elegidas; importe/moneda/fecha/horizonte de escenario; residencia que declare; necesidad de acceso; canal; condición/coste que quiera ver; métrica y orden seleccionados. Guardar el eco de los criterios para que pueda cambiarlo. No se elimina la comparación a medida.

El perfil financiero puede adaptar el nivel/tema de una lección, no ordenar productos concretos ni decidir adecuación. Una alerta educativa es factual, condicional y auditable (hecho disparador + regla/cálculo + fuente/fecha + qué falta), p. ej. «el criterio elegido exige disponibilidad en 90 días; este depósito vence en 12 meses y la cancelación no está documentada». Evitar «te conviene», «elige», «apto», «mejor para tu perfil» o recomendaciones de compra/asignación. Un aviso educativo no desbloquea selección individual.

Separar las clases `EDUCATIONAL` (educación/criterio) y `CONTROL` (integridad/actualidad de datos), tal como declara el registro de códigos; los códigos de control existentes no requieren un prefijo `CONTROL_`. Conservar los identificadores literales del registro y versionar cualquier migración conjunta de códigos/schema. Una decisión que use perfil individual (conocimientos, tolerancia, capacidad económica, ingresos/deudas/objetivos) para recomendar instrumentos, puntuarlos o priorizarlos requiere **revisión profesional española y decisión del grupo antes de publicarse**; disclaimer solo no lo arregla. Esto identifica una cuestión para revisión, no dicta su calificación jurídica.[09-rigor-financiero.md §§1, 4, 7; REQUISITOS.md §§Perfil, Funciones]

## 6. Matriz de faltantes, caducidad y cambios

| Campo/condición | Falta o no se documenta | Caduca según política | Cambia la condición |
|---|---|---|---|
| Identidad/clase/ISIN/moneda | No unir a otros productos; excluido de cálculo exacto | revisar fuente; si no verifica identidad, sin orden numérico | crear versión; recalcular derivados |
| Contratación/canal | `unknown`, nunca «abierto»; en filtro estricto excluir o etiquetar según política | quitar afirmación de abierto; no pasar el filtro | re-ejecutar filtro, preservar versión anterior |
| País/residencia elegible | país usuario no declarado: no inferir; elegibilidad producto desconocida: no pasar filtro duro | estado pasa a desconocido hasta revalidar | invalidar elegibilidad y listado |
| Vencimiento/aviso/liquidación/penalización | liquidez desconocida; no pasa filtro duro por fecha | no asumir condiciones anteriores | re-ejecutar filtro; actualizar alerta/cálculos |
| Métrica/precio/tasa/fecha efectiva | valor null, razón `METRIC_MISSING`; sin rank en esa métrica | no rankear; dejar visible solo como histórico fechado si no engaña | recalcular con fecha/valor nuevos; indicar cambio |
| Comisiones y costes | `partial` o `unknown`, nunca cero; no ordenar neto | cobertura desconocida hasta verificar | recalcular neto solo con componentes completos |
| Fiscalidad | sin residencia/ejercicio/supuesto: bruto; neto null | invalidar cálculo afectado según vigencia fiscal | versionar regla/ejercicio y recalcular neto |
| Garantía y condiciones | `unknown`; no usar palabra «garantizado» | retirar claim hasta revalidar | reemplazar alcance/condiciones y claim |
| Fuente/localizador | no verificable: dato no sustentado; excluir de claim relevante | fuente caída no basta por sí sola, evaluar antigüedad del hecho | registrar documento nuevo y reconciliar discrepancias |
| Conflicto entre fuentes | no escoger en silencio; marcar `DATA_CONFLICT`, sin ordenar por campo | no resolver por antigüedad solamente sin política | conservar ambas evidencias y revisión humana |

Los umbrales `max_age` por campo, política de fuentes en conflicto, y excepciones para vista histórica requieren aprobarse antes de producción.

## 7. Códigos de razón y reglas invariantes

Los códigos de máquina y textos cortos propuestos están en `result-reason-codes.json`. Regla de salida: cada exclusión, ausencia de orden, cifra parcial y alerta indica código + campo/valor + evidencia/fórmula + fecha; los códigos no sustituyen la explicación en español. Invariantes mínimos:

- Nunca `rank != null` en grupo inter-familiar ni sin métrica homogénea vigente.
- Nunca `net_return` con costes parciales o fiscalidad/supuestos desconocidos.
- Nunca tratar `unknown` como `false`, cero, no aplicable o elegible.
- Un filtro excluyente afecta solo al resultado de esa consulta; no borra el producto ni modifica el perfil.
- Cambios de condiciones versionan datos y fuerzan invalidación/re-cálculo.
- El LLM redacta explicaciones a partir del resultado estructurado; no inventa valores, hechos, reason codes, orden ni conclusión de idoneidad.

Schemas: `product-record.schema.json`, `comparison-request.schema.json`, `comparison-result.schema.json`. Las reglas de negocio anteriores son más estrictas que lo que JSON Schema puede expresar por sí solo; validar además las invariantes de dominio.

## 8. Casos de aceptación

Los doce casos sintéticos completos están en `acceptance-cases.json`. Criterio de aprobación común: salida reproducible con las mismas versiones/datos/consulta; ninguna afirmación o dato inferido sin evidencia; todos los filtros, códigos y fechas aparecen en la salida. **Pendiente:** pruebas de ejecución del comparador real, porque aquí se entrega diseño/esquemas, no la implementación.

## 9. Decisiones que requieren aprobar

1. Taxonomía y si `government_bond` se separa de Letras; subgrupos y campos obligatorios por familia.
2. Allowlist de métricas y cohorte de equivalencia por familia; qué escenarios comunes se permiten.
3. Filtros desconocidos por defecto (propuesta: no pasar filtro duro; vista general puede etiquetar), y si residencia se guarda solo en consulta local.
4. Lista de componentes aplicables para declarar costes completos, política de cifra bruta/neta e impuestos.
5. `max_age` y `effective_to` por campo/fuente, quién revisa y tratamiento de fuente inaccesible/conflictos.
6. Desempate final por ID estable, orden alfabético si no hay criterio, orden visual de familias.
7. Límite entre alerta educativa y personalización basada en perfil; revisión profesional previa a cualquier cambio hacia productos concretos personalizados.
8. Confirmar que se preservan preferencias y filtros elegidos por usuario sin convertirlos en recomendación; UX/legal antes de demo pública.

## 10. Verificación prevista

En esta entrega se deben verificar el parseo JSON de schemas/casos, el total de 12 casos y la coherencia de reason codes referenciados. Aún no están probados rankings, filtros, caducidad ni invalidación sobre un motor ejecutable. Fuentes base y contexto: `../../REQUISITOS.md`; `../../investigacion/09-rigor-financiero.md` (documento de rigor, consultado 26-10-2026 en el propio informe).
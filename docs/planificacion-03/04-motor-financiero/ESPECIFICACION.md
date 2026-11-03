# Especificación del motor financiero educativo

**Paideia · España · versión de demostración**  
**Estado:** especificación y verificador local; no es motor financiero validado para producción ni está integrado en la aplicación.  
**Ámbito:** exclusivamente cálculos reproducibles de ahorro/inversión educativa. No incluye préstamos, recomendaciones, cartera, fiscalidad computable, datos de productos reales ni contratación.

## 1. Propósito y límites

El módulo `motor_financiero.py` es una referencia ejecutable e independiente, escrita con `Decimal` y biblioteca estándar. Cada resultado depende solo de los argumentos recibidos y de las hipótesis expuestas aquí. `fixtures.json` contiene **datos ficticios de prueba** (no ofertas, valores actuales ni catálogo). `test_motor_financiero.py` los verifica con `unittest`.

El código demuestra fórmulas y validación básica; no acredita exactitud contractual, idoneidad, cumplimiento normativo, seguridad, rendimiento, ni aptitud para publicar o contratar. Las fórmulas documentadas se distinguen de la implementación y de los casos aún no soportados en las secciones siguientes. No se debe presentar ninguna salida como recomendación personal, promesa, garantía de rentabilidad o asesoramiento fiscal/jurídico.

## 2. Convenciones comunes de entrada y salida

- Tasas en formato decimal: `0.04` significa 4 %; no se aceptan tasas escritas como `4` para representar 4 %.
- Importes y tasas decimales se pasan como `Decimal` o cadena decimal. `float` y booleanos se rechazan para evitar precisión binaria accidental. Los fixtures guardan decimales como cadenas JSON.
- El cálculo usa precisión fija de 34 dígitos significativos y contexto local `ROUND_HALF_UP`; no depende de cambios del contexto `Decimal` del llamador. Los resultados internos **no** se redondean a céntimos. `round_money()` redondea solo para presentación al céntimo más próximo, con empate alejándose de cero.
- Importes de entrada no negativos; principal/saldo cero se admite. Se rechazan tasas no finitas (`NaN`, `Infinity`, `-Infinity`), importes negativos y operaciones que generen un saldo o pago negativo. Se permiten tasas negativas solo si el factor de capitalización o el saldo resultante sigue siendo válido.
- Fechas: texto ISO estricto `YYYY-MM-DD`; inicio inclusivo y final exclusivo. Los días se obtienen como diferencia real entre fechas calendario, incluidos años bisiestos. Intervalos no positivos, invertidos, inválidos o con huecos en una promoción se rechazan.
- Bases explícitas: 360 o 365 días; el código no infiere convención a partir del producto. `360` y `365` no sustituyen todas las reglas contractuales posibles.
- Comisiones, gastos y penalizaciones se especifican como cantidades no negativas en euros; no se presupone ninguna comisión cero si falta el dato en un producto real.
- Toda división por período, rendimiento anualizado, TIR o importe de mercado exige denominador positivo. Las funciones fallan con `ValueError` en lugar de inventar o completar entradas.

## 3. Fórmulas documentadas e implementación

La tabla indica qué fórmula define la especificación y qué función existe **hoy** en este directorio. “Implementado” solo significa cubierto por el código y sus tests locales; no significa que el tratamiento sea válido para todo contrato o instrumento.

| Tema | Fórmula/regla documentada | Implementación local |
|---|---|---|
| Interés simple | `I = P × r × d / B`; `M = P + I`. `P`: principal, `r`: tasa anual simple, `d`: días reales, `B`: base explícita. | `simple_interest()` devuelve `I` sin redondear. |
| Interés compuesto | `M = P × (1 + j/m)^n`; `j`: TIN nominal anual, `m`: períodos/año, `n`: períodos enteros transcurridos. | `compound_amount()`. Solo períodos completos; no prorratea fracciones. |
| Conversión matemática TIN → tasa efectiva anual | `i_eff = (1 + j/m)^m − 1`, con capitalización uniforme y sin comisiones. | `effective_annual_rate()`. Es una equivalencia matemática, **no** el cálculo de la TAE contractual/regulatoria de una oferta. |
| Cuenta por tramos y promoción | En cada período `k`, para saldo inicial `S`, tramos marginales `i` y días `d_k`: `I_k = Σ [max(0, min(S, límite_i) − límite_(i−1)) × r_i × d_k / B]`. `I = Σ I_k`, `neto = S + I − comisiones`. | `tiered_account_result()`: tramos por saldo acumulado, calendario de períodos contiguos, fee opcional por período; sin capitalizar intereses entre períodos. Un último límite finito deja el exceso sin remunerar. |
| Depósito al vencimiento | `M = P + P × TIN × d/B − gastos`, con interés simple pagadero a vencimiento. | `deposit_maturity()`, fechas reales y base declarada. Es un escenario didáctico simplificado, no una liquidación contractual universal. |
| Cancelación de depósito | `pago = principal + interés_devengado − interés_perdido − fee`. | `deposit_cancellation()`: exige que pérdida de intereses no supere lo devengado. No decide por sí mismo la penalización contractual. |
| Letra del Tesoro | Rentabilidad del período `R_p = N/P − 1`; anualización lineal simple ACT/360 `R_a = R_p × 360/d`. `P`: precio total desembolsado; `N`: reembolso neto. | `bill_return()`: retorno del período y anualización simple ACT/360 en campos separados. No lo etiqueta TAE ni supone reinversión. El Tesoro publica la convención ACTUAL/360 y la relación precio/tipo para Letras de hasta un año.[3] La diferencia entre precio y reembolso es el rendimiento del instrumento.[4] |
| Bono con cupón regular | Cupón por período `C = nominal × cupón_anual/m`; último flujo `C + nominal`. TIR periódica `y` resuelve `precio = Σ CF_t/(1+y)^t`; nominal anual `m×y`; efectiva anual `(1+y)^m−1`. | `bond_cashflows()` y `bond_yield()`; raíz numérica por bisección, 34 dígitos. La TIR iguala capital invertido y valor actualizado de cobros futuros; no equivale al cupón.[5] |
| Fondo no cotizado | Valor bruto ilustrativo a la fecha/NAV indicada `unidades × NAV`; comisión explícita de reembolso se resta aparte. Gestión/depositaría y otros gastos ya reflejados en el NAV no se vuelven a restar. | `fund_redemption_value()`: NAV y fee de reembolso declarados. La CNMV distingue comisiones implícitas deducidas del valor liquidativo y comisiones explícitas de suscripción/reembolso.[6] |
| ETF | Compra: `unidades × ask + costes`; venta: `unidades × bid − costes`. El precio observable de negociación no se reemplaza por el NAV. El spread queda incorporado si se proporcionan ask y bid distintos; no se suma otra vez. | `etf_trade_cashflow()` para una operación indicada. No estima ejecución, liquidez ni desviación futura. CNMV distingue la cotización de ETF en mercado del valor liquidativo aplicable a fondos no cotizados.[8] |
| Coste recurrente estimado | Aproximación de sensibilidad: `coste ≈ valor_inicial × tasa_anual × días/base`. No es coste observado ni modelo de rentabilidad. | `ongoing_cost()`, sobre un valor inicial constante. No se resta automáticamente de un NAV o de un resultado que ya lo incorpore. |
| Aportaciones mensuales | Recurrencia por mes: fin de mes `B←B(1+r)+A`; inicio de mes `B←(B+A)(1+r)`. | `future_value_contributions()`, tasa periódica mensual, aportación fija y `timing` explícito (`beginning` / `end`). |
| Inflación | Valor real en moneda del año base: `V_real = V_nominal/(1+π)^n`. | `inflation_adjusted_value()`, donde `π > −100 %` y `n` son años enteros no negativos. |
| Redondeo | No redondear intermedios salvo que la regla del producto lo imponga; dejar trazable la regla. | `round_money()` usa `Decimal.quantize(0.01, ROUND_HALF_UP)` solo a petición. |

### 3.1 TIN, capitalización y TAE

TIN es el tipo nominal contractual; el número y las fechas de capitalización modifican el importe recibido. Para una tasa nominal `j` convertible `m` veces, la equivalencia anual matemática es `(1+j/m)^m−1`. El Banco de España explica que la TAE considera gastos/comisiones asociados y se basa en interés compuesto con la hipótesis de reinvertir los intereses al mismo tipo.[1] Por eso `effective_annual_rate()` solo compara una conversión matemática TIN-capitalización **sin gastos ni condiciones**; no reproduce la TAE declarada por entidad, ni resuelve una oferta promocional/variable, ni declara que el interés pueda reinvertirse realmente.

En una oferta real se debe mostrar por separado TIN, TAE declarada por la entidad, calendario de liquidación, costes, condiciones, duración y cancelación. El Banco de España enumera estos datos como información contractual/precontractual de un depósito.[2] Si faltan los gastos, duración o condiciones, indicar “coste/TAE no verificados” y no comparar como si fueran equivalentes.

### 3.2 Cuentas por tramos, límites y promociones

Los tramos son marginales: el límite `10000` cubre los primeros 10.000 €, no todo el saldo. Cada fila temporal puede cambiar tasas/límites para representar una promoción y el período posterior; los intervalos han de ser contiguos. Un `up_to: null` solo se permite en el último tramo y significa saldo restante ilimitado. Si no existe tramo ilimitado, el saldo sobre el último límite gana 0 % en este modelo. Los fees se suman explícitamente y se descuentan del resultado final.

Limitación importante: el saldo inicial se mantiene igual durante todos los intervalos; el interés no se capitaliza ni altera el saldo de cálculo de los períodos siguientes. No modela variaciones diarias del saldo, liquidación en fechas intermedias, condiciones de nómina, recibos, topes personales, cambio de tipos dentro del día, bonificaciones, retenciones ni una TAE de cuenta. Para acercarse a un contrato hay que cargar el calendario completo y las condiciones desde sus documentos oficiales y contrastar con la fórmula contractual.

### 3.3 Depósitos y cancelación

`deposit_maturity()` representa un depósito a plazo con interés simple por días y un gasto conocido al final. La cancelación se mantiene como función separada para impedir que el motor suponga que se devuelve todo el interés o que se pierde todo: quien la invoque debe pasar `forfeited_interest` y `fee` extraídos literalmente de las condiciones. El Banco de España indica que la información precontractual debe incluir, entre otros, duración, tipo de retribución, TAE, gastos y penalización por cancelación anticipada.[2]

No están implementados: interés compuesto intraplazo, base contractual distinta, penalización porcentual, tipo reducido desde el inicio, cancelación parcial, renovación automática, intereses liquidados periódicamente, vinculaciones ni ofertas con criterios de elegibilidad. Ninguno se infiere de una etiqueta “depósito”.

### 3.4 Letras: precio, reembolso y anualización ACT/360

La rentabilidad de una Letra es el resultado entre precio y reembolso, no un cupón periódico.[4] Para fechas reales del caso, primero se calcula el retorno del plazo `N/P−1`; después se anualiza linealmente sobre ACT/360. Por ejemplo ficticio: pagar 800 y recibir 1.000 a 180 días da 25 % por el período y 50 % simple anualizado ACT/360. Ese 50 % no es lo ganado en seis meses, no es TAE de depósito y no presupone reinvertir a esa tasa. La convención de mercado publicada por el Tesoro para Letras es ACTUAL/360.[3]

Las comisiones de compra aumentan el desembolso y las de salida reducen el reembolso. El cálculo requiere fechas de liquidación correctas y el precio/cashflows correspondientes al inversor; la fixture no usa valores de subasta ni producto real. Si se vende antes del vencimiento, el precio de venta debe reemplazar el reembolso al nominal; no se extrapola un reembolso futuro como si fuera cierto.

### 3.5 Bonos: cupón y TIR

El cupón es un flujo calculado sobre nominal; la TIR descuenta todos los cupones y el principal al precio de compra. El Tesoro describe la rentabilidad como combinación de cupones y diferencia entre precio de compra y precio de venta/amortización, y define la TIR como el tipo que iguala capital y valor actual de los cobros.[5] La función implementada calcula TIR conceptual antes de impuestos para cupones uniformes y precio de compra como si fuera directamente comparable con los flujos futuros.

No modela intereses corridos, convención de liquidación, calendario de días inhábiles, primer/último cupón irregular, amortización parcial, indexación a inflación, opciones, impago, reinversión real de cupones, venta anticipada, costes de custodia ni cálculo de TIR con flujos arbitrarios. Precio y TIR son aproximación didáctica de vencimiento, no rentabilidad garantizada o realizada. El precio de venta antes del vencimiento puede cambiar.

### 3.6 Fondos, ETF, NAV y costes

El cálculo del fondo usa unidades por NAV comunicado y una comisión explícita de reembolso. Gestión y depósito suelen estar implícitas en el NAV; si se parte de un NAV observado, restarlas de nuevo duplicaría el cargo. Suscripción/reembolso son partidas explícitas distintas.[6] La fecha/cut-off, clase, documento DFI/KID y comisiones exactas son indispensables: CNMV indica que el NAV aplicable puede publicarse después de la orden y contrasta esa operativa con el precio observable de ETF que cotiza en mercado.[8]

Para ETF, `etf_trade_cashflow()` requiere precio de mercado y `side`: el llamador debe aportar `ask` para compra y `bid` para venta. La diferencia representa el spread solo si las dos cotizaciones corresponden al mismo momento y mercado; no se calcula el spread por separado. Costes de intermediario deben ser importados de la tarifa real. El valor liquidativo del ETF puede diferir de su índice por gastos y otros efectos.[7] No comparar NAV de una clase/fecha con cotización de otro instante como si fuera la misma valoración.

`ongoing_cost()` es solo una aproximación lineal de tasa recurrente sobre valor constante. No equivale a TER futuro, no captura rendimientos diarios/seguimiento, y no debe restarse del NAV si ese gasto ya se refleja ahí. La herramienta no afirma un coste total completo si faltan TER, broker, custodia, compra/venta, cambio de divisa, spread u otros gastos.

## 4. Fiscalidad separada

No existe cálculo fiscal en `motor_financiero.py`; no se calcula rendimiento “neto de impuestos”, retención, tramos ni diferimiento. No hay tipos fiscales codificados. Una futura capa fiscal debe ser independiente, opt-in y versionada, con país/residencia, ejercicio fiscal, tipo de renta, situación/condiciones aplicables, fuente oficial fechada y reglas de vigencia; deberá etiquetar toda salida como estimación educativa y requerir revisión fiscal. “Sin retención” no se traducirá en “exento”. No se asume régimen de traspaso ni tratamiento fiscal uniforme entre Letras, bonos, fondos y ETF.

## 5. Límites y errores deliberados

| Entrada/límite | Comportamiento |
|---|---|
| Capital/saldo/unidades/coste cero | Permitido cuando la fórmula tiene sentido; principal cero produce interés cero; cero períodos de aportación produce saldo cero. |
| Principal, saldo, coste o días negativos | Rechazado. Tasas negativas sí se permiten si `1 + tasa periódica > 0` y no aparece saldo negativo. |
| `NaN`, `Infinity`, `-Infinity`, `float`, `bool` | Rechazados en parámetros decimales. |
| Comisiones negativas | Rechazadas. Si las comisiones superan venta, NAV, saldo o reembolso, se rechaza el resultado negativo. |
| Fechas inválidas, iguales o invertidas | Rechazadas; fin de intervalo exclusivo. La anualización de Letra exige días reales positivos. |
| Frecuencia de capitalización/cupones y períodos | Enteros; frecuencia positiva. El cálculo TIR solo admite cupones positivos/cero, frecuencia y períodos regulares. |
| Tasa compuesta `TIN/m <= −1` o inflación `π <= −1` | Rechazada porque el factor deja de ser positivo. |
| Convenciones de días | Solo `ACT/360` o `ACT/365F` simplificado en funciones genéricas; no `30/360`, ACT/ACT, calendario hábil ni reglas de liquidación. |
| Tramos | Límites positivos, estrictamente crecientes; ilimitado solo en último tramo. Calendario promocional contiguo. |
| Formas no admitidas | No se aproximan silenciosamente; se indica error o la falta de soporte. |

La bisección de TIR es determinista bajo precisión fija, pero el resultado es una aproximación numérica; si el precio implicara un rendimiento prácticamente −100 % o no se logra acotar una solución, la función falla explícitamente.

## 6. Parámetros/fuentes que faltan para datos de producto real

Antes de cargar un producto real, deben obtenerse y revisar documentalmente —no inferirse del nombre ni completarse con un LLM— al menos:

- **Cuentas:** titularidad/segmento remunerado, saldo elegible, base de días, saldo diario o medio, fechas de devengo/liquidación, tramos, inicio/fin promocional, condición de permanencia/vinculación, comisiones, cambio de tipo y garantías aplicables.
- **Depósitos:** TIN/TAE oficiales, periodicidad, método exacto de cálculo, base, fechas/renovación, cancelación parcial/total, pérdida de intereses/penalización, cargos y condiciones vinculadas.
- **Letras:** fecha de liquidación y vencimiento, precio realmente pagado, nominal/reembolso, comisiones de intermediación/custodia y precio si venta antes de vencimiento.
- **Bonos:** ISIN/clase, precio limpio/sucio, intereses corridos, cupón y calendario completo, base, fecha de liquidación, amortizaciones, gastos y precio de salida. Las características del emisor y riesgos no se derivan del cálculo de TIR.
- **Fondos:** ISIN/clase, NAV y fecha, hora límite, DFI/KID/folleto, comisiones de entrada/salida, gastos recurrentes, ventanas y plazo de reembolso.
- **ETF:** ISIN, mercado, moneda, timestamp y bid/ask realmente disponibles, liquidez, tipo de orden, broker, custodia, cánones, FX y gastos recurrentes. Un precio observado no garantiza ejecución.
- **Aportaciones e inflación:** fecha efectiva de cada pago, tasa por período coherente, calendario irregular y serie/índice de inflación elegidos; la especificación solo admite periodicidad mensual fija y tasa/índice aportados por el usuario.
- **Todos:** fuente primaria/licencia, fecha/hora de observación, unidad, vigencia y método; costes, liquidez, riesgo, garantía, impuestos y condiciones se muestran por separado.

No hay conexión con fuentes/API ni política de caducidad. El módulo no contiene catálogo y los valores de `fixtures.json` no deben reutilizarse como hechos de mercado.

## 7. Funcionalidades explícitamente fuera de alcance

- Ningún préstamo nuevo ni cálculo de préstamo, amortización, cuota, refinanciación, scoring crediticio o comparador de deuda.
- Ningún ranking, recomendación personal, asignación de cartera o decisión automatizada de compra.
- Ninguna compra/venta, apertura/cancelación bancaria, custodia, pago, autenticación o contratación real o ficticia.
- Ningún dato o rendimiento de producto real, ni garantía estatal, ni simulación de escenarios de mercado.
- Ninguna fiscalidad, tasa tributaria ni conclusión jurídica.

## 8. Verificación reproducible

Desde este directorio:

```sh
python -m unittest -v test_motor_financiero.py
```

**Ejecución local efectuada:** `Ran 29 tests ... OK`. Incluye fixtures sintéticas de referencia para interés simple/compuesto, equivalencia TIN-capitalización, promoción y límites por tramo, plazo y cancelación de depósito, Letra ACT/360, cupón/TIR, NAV, precio bid/ask y comisiones ETF/fondo, aportaciones en inicio/fin de mes, coste recurrente e inflación. Incluye también límites cero, tasas negativas válidas e inválidas, entradas negativas, no finitas, comisiones, redondeo y fechas (incluido año bisiesto).

**Lectura correcta del resultado:** son pruebas unitarias de esta implementación aislada; no validan contratos reales, fuentes de datos, precisión frente a un banco/mercado, integración con Paideia ni preparación para producción.

## Sources

[1] https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/relacionados/tiposinteres/guia-textual/latae/tae_deposito.html
[2] https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/cuentasdepositos/depositosplazo/guia-textual/publicidadinform
[3] https://tesoro.es/sites/default/files/calendarios/Calendario%20Tesoro%20Publico%202026%20Ingles-12.pdf
[4] https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/letras-del-tesoro
[5] https://www.tesoro.es/4-cual-es-la-rentabilidad-de-los-bonos-y-obligaciones
[6] https://www.cnmv.es/portal/inversor/fondos-comisiones?lang=es
[7] https://www.cnmv.es/DocPortal/Publicaciones/Guias/LosFondosCotizadosEnBolsa%28ETF%29.pdf
[8] https://www.cnmv.es/portal/inversor/fondos-como-invertir?lang=es

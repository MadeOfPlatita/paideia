# Mapping de campos: perfil local 05 ↔ DTO remoto

El mapping define traducciones explícitas, no igualdad de schemas. La fuente es `../../planificacion-03/05-perfil-conversacion/perfil.schema.json`; el destino de producción es `profile-projection.schema.json`. El perfil local completo y el DTO remoto son estructuras distintas. Solo se construyen los campos elegidos y autorizados para el propósito del turno.

## Campos

| Path local (05) | Campo remoto | Conversión de valor declarado |
|---|---|---|
| `respuestas.objetivo` | `objective` | `colchon_imprevistos→emergency_reserve`; `gasto_previsto→planned_expense`; `ahorro_largo_plazo→long_term_savings`; `entender_riesgo→understand_risk`; `comparar_familias→compare_families`; `aprender_conceptos→learn_concepts`; `curiosear→explore`. |
| `respuestas.horizonte` | `horizon` | `menos_6_meses→under_6_months`; `6_12_meses→6_to_12_months`; `1_3_anos→1_to_3_years`; `mas_3_anos→over_3_years`; `sin_fecha→no_fixed_date`. |
| `respuestas.liquidez` | `liquidity_need` | `acceso_cualquier_momento→anytime_access`; `planificar_fecha→planned_date`; `solo_dinero_ficticio→fictional_money_only`. |
| `respuestas.experiencia.valor.nivel` | `learning_level` | `empezando→beginner`; `leido_o_comparado→read_or_compared`; `ha_tenido_alguno→has_used_one`; `prefiere_no_contar→prefer_not_to_say`. |
| `respuestas.experiencia.valor.temas_interes` | `learning_topics` | Traducción elemento a elemento: `cuentas_remuneradas→remunerated_accounts`; `depositos→term_deposits`; `deuda_publica→government_debt`; `fondos→mutual_funds`; `etf→etf`. |
| `detalle_economico.importe_objetivo` | `target_amount_eur` | Banda EUR `{min_eur,max_eur}` a decimal-strings; moneda permanece `EUR`. |
| `detalle_economico.ingresos_netos` | `monthly_income_eur` | Banda EUR y periodicidad; periodicidad española se traduce a `weekly`, `every_14_days`, `twice_monthly`, `monthly` o `annual`. |
| `detalle_economico.gastos_esenciales` | `monthly_expenses_eur` | Mismo DTO de flujo que ingresos. No se normaliza ni deriva un «disponible» calculado. |
| `detalle_economico.deuda` | `debt` | `situacion=sin_deuda→{situation:no_debt}`; `con_deuda` contiene `balance_eur`, `monthly_payment_eur` y `annual_cost_percent`, cada subrespuesta con su estado propio. |
| `detalle_economico.deuda.saldo_eur` | `debt.value.balance_eur` | Banda EUR. Saldo declarado `0` es string `"0"`; no representa ausencia de deuda. |
| `detalle_economico.deuda.cuota` | `debt.value.monthly_payment_eur` | Banda EUR + periodicidad. El nombre remoto refleja el mapping de cuota; la periodicidad original siempre se conserva. |
| `detalle_economico.deuda.coste_anual_pct` | `debt.value.annual_cost_percent` | Rango en puntos porcentuales como decimal-strings; `max_pct=null` local significa techo 100 %, que se representa como `"100"`. |
| `detalle_economico.colchon_liquido` | `liquid_reserve_eur` | Banda EUR como decimal-strings. |
| `detalle_economico.compromisos_proximos` | `upcoming_commitments` | `hay_compromiso=false` conserva ausencia declarada; si es `true`, incluye total EUR y ventana temporal (`under_3_months`, `3_to_6_months`, `6_to_12_months`, `date_unclear`). |
| `riesgo.tolerancia` | `risk_tolerance` | `preferiria_salir→would_prefer_to_exit`; `esperaria_con_inquietud→would_wait_with_concern`; `podria_esperar_aceptando_caidas→can_wait_with_drops`. |
| `riesgo.capacidad_perdidas` | `loss_capacity` | Conserva escenario `caida_100_de_1000→drop_100_of_1000` y traduce impacto. No se mezcla con tolerancia al riesgo. |
| `supuestos_escenario` | — | No se proyecta: el schema local los define como hipótesis de escenario, no como respuestas del perfil. |
| `version_esquema`, `tipo` | — | Metadatos del perfil local; no se envían. La ruta de fixture completa comprueba su versión/tipo, pero no los adjunta al DTO. |

## Estados y valores

El `estado` español de cada respuesta se traduce sin inferencia:

| Local 05 | DTO remoto | Forma |
|---|---|---|
| `declarado` | `known` | Incluye `value`, incluso si es `0` o una opción explícita como `no_debt`. |
| `no_se` | `unknown` | Solo `state`; no incluye `value` ni cifra nula. |
| `omitido` | `omitted` | Solo `state`; distinto de desconocido. |
| `sin_preguntar` | `not_asked` | Solo `state`; distinto de omitido y desconocido. |

Para deuda: `known + situation=no_debt`, `known + situation=has_debt + balance="0"` y `unknown/omitted/not_asked` son formas distintas. No convertir `null`, cero o un estado ausente en otra forma. En rangos EUR, `max_eur=null` es la banda abierta que ya define 05; la respuesta desconocida se representa con el estado y sin `value`.

Las cifras se reciben como `Decimal` o entero y salen como decimal-string sin float, redondeo ni división. JSON parseado con el `float` estándar ya pudo perder precisión: cargar el perfil con `parse_float=Decimal`; la función rechaza `float`. Los ceros decimales finales se preservan al proyectar desde `Decimal` (por ejemplo `Decimal("1200.10") → "1200.10"`). El DTO actual restringe importes al euro porque ese es el contexto del proyecto; una ampliación de moneda requerirá contrato/versionado explícito.

## Matriz de campos permitidos por propósito (propuesta para comparar)

La función rechaza campos fuera de la matriz y exige que la lista de consentimiento coincida exactamente con la selección. Estas listas son reglas explícitas del prototipo, no una elección final sobre calidad ni sobre la cantidad de información necesaria.

| Propósito | Campos seleccionables en este prototipo |
|---|---|
| `learn_basics` | `objective`, `learning_level`, `learning_topics` |
| `debt_education` | `debt`, `objective`, `monthly_income_eur`, `monthly_expenses_eur`, `liquid_reserve_eur`, `upcoming_commitments` |
| `risk_education` | `objective`, `horizon`, `risk_tolerance`, `loss_capacity`, `upcoming_commitments` |
| `liquidity_planning` | `objective`, `horizon`, `target_amount_eur`, `monthly_expenses_eur`, `liquidity_need`, `liquid_reserve_eur`, `upcoming_commitments` |
| `product_comparison` | `objective`, `horizon`, `liquidity_need`, `risk_tolerance`, `loss_capacity`, `target_amount_eur`, `liquid_reserve_eur` |

No se fuerza una proyección «solo no financiera»: capacidad de pérdida, deuda o gastos pueden ser pertinentes para personalización educativa. Cada campo requiere aprobación explícita; la pertinencia final y la comparación con la variante completa deben resolverse con benchmark sintético, revisión del proveedor y decisión del grupo.

La allowlist no es un filtro de PII sobre texto libre y no promete detectar/limpiar toda identificación. Este mapping solo construye datos estructurados conocidos; el mensaje libre y los historiales necesitan tratamiento separado y revisión explícita.

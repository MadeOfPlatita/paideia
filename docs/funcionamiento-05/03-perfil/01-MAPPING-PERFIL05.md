# Mapping explícito UI v2 → perfil05

El destino contractual es `docs/planificacion-03/05-perfil-conversacion/perfil.schema.json` (perfil05 1.0.0). Los `key` de las preguntas son literalmente sus paths; no se crea un segundo conjunto de paths ni una proyección remota. `static/profile_model.js` mantiene este mapping y la UI usa sus definiciones para pregunta, opciones, resumen y vista previa.

| Pregunta / `key` local | Path perfil05 | Conversión explícita |
|---|---|---|
| Objetivo | `respuestas.objetivo` | Usa los valores del schema: `colchon_imprevistos`, `gasto_previsto`, `ahorro_largo_plazo`, `entender_riesgo`, `comparar_familias`, `aprender_conceptos`, `curiosear`. |
| Horizonte | `respuestas.horizonte` | `menos_6_meses`, `6_12_meses`, `1_3_anos`, `mas_3_anos`, `sin_fecha`. |
| Necesidad de liquidez | `respuestas.liquidez` | `acceso_cualquier_momento`, `planificar_fecha`, `solo_dinero_ficticio`. |
| Conocimientos/experiencia | `respuestas.experiencia` | Nivel: `empezando`, `leido_o_comparado`, `ha_tenido_alguno`, `prefiere_no_contar`; `temas_interes` usa los cinco valores de perfil05. Temas no seleccionados quedan en `[]`, sin afirmar falta de interés. |
| Importe objetivo | `detalle_economico.importe_objetivo` | EUR puntual; `min_eur` y `max_eur` reciben la misma cadena decimal y `moneda=EUR`. |
| Ingresos | `detalle_economico.ingresos_netos` | Rango puntual EUR en `importe`; `periodicidad=mensual`. No se deriva ingreso disponible. |
| Gastos esenciales | `detalle_economico.gastos_esenciales` | Rango puntual EUR en `importe`; `periodicidad=mensual`. |
| Deuda | `detalle_economico.deuda` | «No tengo deuda» → `situacion=sin_deuda`. «Con deuda» → `situacion=con_deuda` con `saldo_eur`, `cuota` y `coste_anual_pct`; cada subrespuesta acepta `declarado`, `no_se`, `omitido` o `sin_preguntar`. Saldo `"0"` sigue siendo deuda declarada. |
| Colchón líquido | `detalle_economico.colchon_liquido` | Importe EUR puntual en strings, sin periodicidad. |
| Compromisos próximos | `detalle_economico.compromisos_proximos` | No → `hay_compromiso=false`; sí → `hay_compromiso=true`, total EUR como respuesta propia y plazo `menos_3_meses`, `3_6_meses`, `6_12_meses` o `fecha_no_clara`. |
| Tolerancia | `riesgo.tolerancia` | `preferiria_salir`, `esperaria_con_inquietud`, `podria_esperar_aceptando_caidas`. |
| Capacidad/impacto de pérdida | `riesgo.capacidad_perdidas` | Escenario fijo `caida_100_de_1000`; impacto `sin_cambio_en_necesidad_o_meta`, `retrasaria_o_reduciria_meta` o `afectaria_gasto_esencial_o_compromiso`. No se combina con tolerancia. |

## Estados y unidades

`declarado`, `no_se`, `omitido` y `sin_preguntar` siguen los estados de perfil05. Solo `declarado` contiene `valor`. Una cifra conocida cero es string `"0"`; no saber, omitir, no preguntar y `max_eur=null` no se intercambian. Los campos de flujo conservan `periodicidad=mensual` y no se normalizan entre unidades.

El esquema 05 contractual define rangos EUR como JSON `number`. Para satisfacer la persistencia local exacta, este snapshot v2 usa cadenas en esos mismos paths. Es una representación de almacenamiento solo del navegador, **no** un cuerpo validado por el schema de proyección remota ni un JSON para enviar. No se convierte con `Number`, no se redondea, y no hay endpoint que acepte o transmita el mapa.

## Límites funcionales

El mapping solo organiza respuestas elegidas por la persona. No genera avisos de solvencia, etiquetas («conservador/agresivo»), ranking, selección de productos, presupuesto disponible o recomendación. La UI tampoco lee texto libre de chat para modificar el perfil. `supuestos_escenario` permanece vacío y separado de cualquier cálculo didáctico.

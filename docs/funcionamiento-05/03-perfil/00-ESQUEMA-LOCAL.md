# Esquema local v2 del perfil

## Envolvente persistida

- Clave actual: `paideia.profile.v2`.
- Forma: `{ "version": 2, "profile": <Mapa05>, "legacyAnswers": {} }`.
- `legacyAnswers` es obligatorio en la envolvente v2 y normalmente vacío. Solo conserva categorías del formato v1 que no se pueden convertir sin cambiar su significado.
- El contenido de `profile` conserva los paths y los valores enumerados de `perfil.schema.json` (versión `1.0.0`, tipo `mapa_educativo`). `supuestos_escenario` queda vacío: los supuestos de una calculadora no son respuestas del perfil.
- La cifra decimal persistida dentro de los rangos EUR/porcentaje es una cadena decimal JSON. No se convierte a `Number`, no se redondea y no se admite texto libre. El módulo valida 0–9.999.999.999,99 EUR y 0–100 %; se permiten hasta dos decimales.

## Estados

| Estado local | Significado | Forma JSON |
|---|---|---|
| `declarado` | Respuesta que la persona eligió; el valor puede ser `"0"` | `{ "estado":"declarado", "valor": ... }` |
| `no_se` | Eligió «No lo sé» | `{ "estado":"no_se" }` |
| `omitido` | Eligió «Omitir» | `{ "estado":"omitido" }` |
| `sin_preguntar` | Aún no llegó a responder; incluye continuar en blanco o terminar pronto | `{ "estado":"sin_preguntar" }` |

Los tres estados sin valor no contienen propiedad `valor`. No se interpretan como cero ni como `null`. Deuda `sin_deuda` es diferente de deuda declarada con saldo `"0"` y de una respuesta no declarada. En una deuda declarada, saldo, cuota y coste conservan estados propios.

## Paths cubiertos

| Path perfil05 | Contenido |
|---|---|
| `respuestas.objetivo` | Tema/objetivo educativo de los siete valores de perfil05 |
| `respuestas.horizonte` | Una de las cinco referencias de tiempo de perfil05 |
| `respuestas.liquidez` | Acceso inmediato, fecha planificable o dinero ficticio |
| `respuestas.experiencia` | Nivel de familiaridad y lista opcional `temas_interes` |
| `detalle_economico.importe_objetivo` | Importe EUR puntual como `min_eur=max_eur` strings |
| `detalle_economico.ingresos_netos` | Flujo mensual EUR con periodicidad `mensual` |
| `detalle_economico.gastos_esenciales` | Flujo mensual EUR con periodicidad `mensual` |
| `detalle_economico.deuda` | `sin_deuda` o saldo, cuota y coste con respuestas independientes |
| `detalle_economico.colchon_liquido` | Importe EUR puntual como `min_eur=max_eur` strings |
| `detalle_economico.compromisos_proximos` | Sin compromiso o existencia declarada, importe y plazo |
| `riesgo.tolerancia` | Preferencia declarada ante una caída ficticia |
| `riesgo.capacidad_perdidas` | Impacto separado para el escenario fijo `caida_100_de_1000` |

La estructura local se valida de forma cerrada: propiedades extra, estados con `valor`, enum fuera del contrato, número JSON en lugar de decimal-string, límites invertidos y escala inválida se rechazan. La UI de ingresos/gastos/cuota explicita periodicidad mensual; la aplicación no calcula un «disponible», solvencia, perfil de riesgo o encaje.

## Fuente de verdad e integración

El schema contractual 05 continúa en `docs/planificacion-03/05-perfil-conversacion/perfil.schema.json`. El módulo `static/profile_model.js` mantiene una única definición utilizable en navegador para los controles, el resumen, las opciones, la validación y la clave de almacenamiento; `PROFILE05_MAPPING` declara el path contractual de cada pregunta. El mapping de lectura está documentado en `01-MAPPING-PERFIL05.md`.

La UI solo conserva estas respuestas localmente. `toProfile05`/proyección remota no se ejecuta ni existe un camino automático de envío. El almacenamiento local usa decimal-strings deliberadamente; no se afirma que esa serialización sea un JSON de producción que valide tipos `number` del schema 05. Cualquier exportación/intercambio futuro necesita conversión decimal exacta, validación del contrato y autorización separada.

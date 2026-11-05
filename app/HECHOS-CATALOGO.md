# Hechos de catálogo y comparabilidad trazable

**Estado actualizado:** núcleo Python local y puro, conectado mediante `backend_services.CatalogueComparisonService` a un criterio opcional de `/api/compare`. El arranque normal carece de hechos cuantitativos y políticas aprobadas; devuelve diagnóstico y no tasas. Integración positiva solo con fixtures aisladas. Ver `BACKEND-INTEGRACION.md`. No es adaptador de fuentes, API pública, catálogo de ofertas ni motor de publicación. Los hechos positivos de los tests son exclusivamente sintéticos (`evidence_class="synthetic_test"`, IDs/localizadores `test`/`fixture://`); no se insertan en `candidatos.json` ni representan entidades u ofertas reales.

## Contrato aplicado

La interfaz implementa un DTO de hecho de un solo campo, basado en `docs/planificacion-03/14-ingesta-calidad/ESPECIFICACION.md`, las reglas de `docs/planificacion-03/07-comparador-reglas/comparador-trazable.md` y la precedencia de `docs/planificacion-03/19-integracion/CRITERIO-INTEGRACION.md`:

- `Fact` es `frozen=True`; mantiene `fact_id`, `product_id`, familia, `semantic_scope`, `field_path`, `source_id`, `source_revision_id` y `locator`.
- `value` es una cadena decimal base 10 o `None`; no se admiten `float`, comas, exponentes, `NaN` ni infinitos. `unknown` y `not_applicable` exigen `value=None`; no se infiere cero. Un valor conocido `"0.00"` sigue siendo un cero explícito.
- `unit`, `currency` y `period` se conservan sin conversión. Cada `ComparisonSpec` exige moneda con forma de código ISO 4217 de tres letras y periodo explícitos; el núcleo no valida la lista ISO completa. Si el hecho no conoce moneda o periodo, queda excluido con `CURRENCY_UNKNOWN` o `PERIOD_UNKNOWN`. Esta versión no representa moneda “no aplicable” para métricas cuantitativas.
- `effective_at` y `effective_precision` (`date`, `datetime`, `not_stated`) son independientes de `retrieved_at`. Un timestamp de recuperación no rellena una fecha efectiva desconocida.
- Vigencia y valor son ejes distintos: `validity_state` es `known`, `unknown` o `conflict`; `valid_from`/`valid_to` son fechas opcionales con intervalo `[valid_from, valid_to)`. No se supone fecha de fin cuando falta.
- `state` admite `known`, `unknown`, `conflict` y `not_applicable`.
- `permissions_by_action` se copia a un mapa inmutable. La comparación solicita una acción concreta; permiso `pending`, `unknown` o ausente genera `RIGHTS_UNRESOLVED`, no `RIGHTS_BLOCKED` ni una prohibición universal. `blocked` solo bloquea esa acción/hecho.
- `evidence_class` distingue `synthetic_test` de `production_candidate` y se devuelve en el DTO.

`semantic_scope` es obligatorio además de familia y métrica: permite que quien integra distinga, por ejemplo, `term_deposit_tae`, `fund_share_class_nav`, `market_listing_quote`, `auction_event` y `reference_series`. Los nombres son claves explícitas aportadas por el llamador; no se deducen de ticker, ISIN, clase, familia amplia o marca.

## Evaluación determinista

Interfaz:

```python
from datetime import timedelta
from catalogue_facts import Fact, ComparisonSpec, FreshnessPolicy, evaluate_comparability

result = evaluate_comparability(facts, spec, policy)
dto = result.to_dict()
```

`ComparisonSpec` requiere comparación, familia, `semantic_scope`, `field_path`, unidad, moneda, periodo, al menos dos IDs de producto distintos, acción de permiso y `as_of`. Solo sirve el hecho cuyo campo coincida exactamente. Familia, scope semántico, unidad, moneda y periodo deben coincidir; no se convierte porcentaje↔ratio, TAE↔TIR, NAV↔cotización, subasta↔benchmark ni depósito↔ETF.

`FreshnessPolicy` también es obligatoria y queda ligada a familia + scope semántico + campo + acción, con versión y límites de edad de recuperación y de fecha efectiva. No hay TTL por defecto ni TTL de producción codificado. Cada límite acepta una `timedelta` aprobada o `None` explícito (sin límite para ese eje); los tests usan solo políticas `test-only-*`. Un policy con alcance distinto se rechaza.

Reglas v1 (`ruleset_version="catalogue-fact-comparability.v1"`):

1. Un hecho ausente para un producto: `METRIC_MISSING`.
2. `unknown` o valor nulo: `METRIC_MISSING`; `not_applicable`: `METRIC_NOT_APPLICABLE`; `conflict` o varias afirmaciones incompatibles para el mismo producto/métrica: `DATA_CONFLICT`. No se elige “la última” ni se promedian valores.
3. Si varias fuentes tienen la misma semántica y valor, se mantienen sus referencias. Solo referencias que pasan los controles de acción/frescura respaldan el valor; un pendiente en otra acción no invalida la acción permitida.
4. Desajuste de familia/scope/unidad/moneda/periodo, o moneda/periodo ausentes: código específico (`FAMILY_MISMATCH`, `SCOPE_MISMATCH`, `UNIT_MISMATCH`, `CURRENCY_MISMATCH`, `CURRENCY_UNKNOWN`, `PERIOD_MISMATCH`, `PERIOD_UNKNOWN`) y `NUMERIC_BASIS_MISMATCH`.
5. La fecha efectiva ausente, futura o demasiado antigua excluye con `EFFECTIVE_DATE_UNKNOWN`, `EFFECTIVE_DATE_FUTURE` o `METRIC_STALE`. Recuperación posterior a `as_of` excluye con `RETRIEVED_AT_FUTURE`; recuperación que supera la política da `SOURCE_STALE`.
6. Vigencia desconocida/conflictiva, inicio futuro o fin alcanzado excluyen ese hecho con `VALIDITY_UNKNOWN`, `DATA_CONFLICT`, `NOT_YET_EFFECTIVE` o `FACT_EXPIRED`.
7. Derecho bloqueado: `RIGHTS_BLOCKED`; permiso pendiente/desconocido/ausente: `RIGHTS_UNRESOLVED`.
8. `quantitative_ready` es verdadero solo si quedan al menos dos productos elegibles. El DTO conserva exclusiones por producto; no calcula, ordena, asigna rangos ni crea una recomendación.

El DTO (`schema_version="catalogue-comparison.v1"`) expone criterio/versión de reglas, política de frescura, acción evaluada, IDs elegibles, valor decimal como cadena y, por producto, `eligible`, `reason_codes`, `evidence_class` y `source_refs`. Cada referencia conserva ID del hecho/fuente/revisión, locator, familia/scope/campo, unidad/moneda/periodo, intervalo de vigencia, estado, precisión/fecha efectiva, `retrieved_at` y permiso para la acción consultada. Un resultado excluido no expone como valor comparable la cifra del hecho.

## Inventario de veinte candidatos: sin promoción a hechos

El test `test_twenty_catalogue_candidates_remain_inventory_not_quantitative_facts` lee en modo solo lectura `docs/validacion-04/05-catalogo/candidatos.json`. Verifica 20 IDs (cuatro por cada una de las cinco familias inventariadas) y que existe identidad `verified` con checksum ISIN válido. Después usa solo IDs/familias como inventario de productos y evalúa métricas de prueba con **cero hechos**: los 20 quedan `METRIC_MISSING`, `value=null`, sin referencias y `quantitative_ready=false`.

No transforma `available_fields`, ISIN, checksum, estado `verified`, URL, checksum de documento ni presencia de candidato en `Fact`. El fichero original no se modifica. La identidad verificada no acredita condiciones completas, vigencia, permisos, oferta disponible o comparabilidad. Este test no cambia el recuento publicado existente (0 listos para publicación) ni activa ninguna métrica real.

## Verificación local

Sin dependencias externas:

```sh
python -B -m unittest tests.test_catalogue_facts -v
python -B -m unittest discover -s tests -v
```

Resultado ejecutado en esta entrega: 21/21 tests de `test_catalogue_facts.py` y suite local completa 80/80 OK. Los positivos usan únicamente hechos sintéticos declarados dentro de `tests/test_catalogue_facts.py`; el inventario real se usa solo para comprobar ausencia de hechos cuantitativos inferidos.

## Pendientes tras la primera integración local

El DTO se ha conectado al criterio técnico `deposit_tae_12m_eur` con tests HTTP y configuración vacía por defecto. Esto no aprueba mappings de ofertas reales ni políticas de frescura de producción. El resto de este apartado enumera los requisitos para esa integración de datos operativa.

- Primera conexión HTTP y tests completados para el criterio opcional de depósitos. Ampliar criterios y datos reales solo con mappings, evidencia y políticas aprobados; la API local no equivale a publicación.
- Definir mapping persistente entre IDs del `SnapshotRepository` y hechos aprobados; **no** crear hechos a partir de metadatos de candidatos.
- Elegir `semantic_scope` y periodo económicos con evidencia por métrica/familia; mantener separados contrato de depósito, clase de fondo/ETF, NAV/listing, evento de subasta y serie/benchmark.
- Cargar solo fuentes y revisiones permitidas, preservar evidencia, estado, locator y permiso por cada acción. La política operativa de frescura debe ser explícita, versionada y aprobada para campo + uso; los límites de test no son producción.
- Mantener `synthetic_test` fuera de la respuesta/catalogación de producción y comprobar aparte permiso para `display`, `redistribute_raw`, exportación u otros usos; aprobar `transform_extract` no concede esos usos.
- Revisar conjuntamente el contrato público con el hueco conocido de `adapter.schema.json` (nullable + estado/motivo), sin afirmar que ese schema queda corregido aquí.

Sin cambios en `app.py`, `domain.py`, `providers.py`, `context_adapter.py`, frontend ni fuentes originales. Sin API pública, DB, instalación, red externa o publicación.

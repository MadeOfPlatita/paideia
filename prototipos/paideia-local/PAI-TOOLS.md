# ToolDispatcher de Pai — `local-tools.v1`

## Alcance

`pai_tools.py` ofrece `ToolDispatcher(repository, comparison_service)` para el catálogo interno de investigación. No importa `app.py`: recibe el repositorio y el servicio de comparación ya construidos por la capa superior. El repositorio debe exponer `list_products(q=None, family=None)` y `get_product(product_id)`; el comparador, `compare(products, criterion)`. Ambas dependencias son de solo lectura desde este dispatcher.

`definitions()` devuelve cinco definiciones OpenAI `function`, compatibles con el constructor local de requests de `providers.py`. `dispatch(name, arguments)` devuelve siempre el DTO con `schema_version: "local-tools.v1"`, `tool`, `status`, `data`, `sources` y `error`. En éxito: `status: "ok"`, `error: null`; en error: `status: "error"`, `data: {}`, `sources: []` y `error: {code, message}`. Los mensajes no incluyen argumentos ni excepciones internas. Este formato de error también satisface el contrato de `ToolChatRunner`.

## Registry cerrado

Todas las definiciones tienen `additionalProperties: false`; el dispatcher vuelve a validar cada entrada antes de consultar dependencias.

| Herramienta | Argumentos exactos |
|---|---|
| `search_products` | `{query: string <=100, family: familia local|null, limit: integer 1..20}` |
| `get_product_detail` | `{product_id: ID local literal}` |
| `compare_products` | `{product_ids: 2..4 IDs únicos, criterion: "deposit_tae_12m_eur"|null}` |
| `calculate_scenario` | Las seis propiedades de `domain.calculate_scenario`: `principal`, `annual_rate_percent`, `years`, `monthly_contribution`, `method`, `inflation_percent` |
| `get_sources` | `{product_ids: 1..20 IDs únicos}` |

Familias: `cuenta_remunerada`, `deposito`, `letra_deuda_publica`, `fondo_tradicional`, `etf_ucits`. El ID debe cumplir el formato local `[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}` (p. ej. `DEP-01` o `SYN-01`); no se trata como UUID ni se convierte al UUID propuesto en el plan inicial.

Importes y porcentajes del escenario son cadenas decimales limitadas por el motor de dominio. `years` es un entero estricto entre 1 y 40 (`bool` no cuenta como entero). Se conservan las convenciones de `domain.calculate_scenario`: el motor convierte años a meses, aporta al final de cada mes y usa tasa anual efectiva/conversión mensual para compuesto. Cero es válido para importes/tasas; `-100%`, NaN/Infinity, tipos numéricos no-string para decimales y valores fuera de cota se rechazan. El dispatcher no calcula tasas ni interpreta resultados por su cuenta.

## Datos, comparación y fuentes

Las respuestas de producto solo proyectan los metadatos admitidos por el snapshot: `id`, `name`, `family`, `issuer`, `isin`, `identity_state`, `primary_url`, `as_of`, `publication_ready`, `conditions_state`, `conflicts` y `unknown_fields`. No pasan campos adicionales del repositorio. Los candidatos permanecen marcados `publication_ready: false` y `conditions_state: "pending"`; identidad no demuestra condiciones, rendimiento, disponibilidad, garantía ni idoneidad.

Una comparación con `criterion: null` es solo metadatos y no invoca `comparison_service`. Con criterio se delega en `comparison_service.compare(copias_de_productos, criterion)` y se conserva su resultado; el dispatcher no resuelve comparabilidad, derechos, frescura ni conflictos. Solo `test_only: true` hace que un resultado cuantitativo se marque como `hypothetical: true`; la salida sigue marcada no publicable. Las fuentes superiores de productos son citas de identidad, no de condiciones.

Cada cita de producto se deriva de `primary_url` y el ID literal devuelto por el repositorio. `source_ref.namespace` es `local-tools.v1` y `source_ref.id` tiene forma `identity:<ID-local>`: es un identificador interno, explícitamente no UUID. `claim_scope` es `product_identity_only`. No se recibe ni se consulta una URL del modelo; el dispatcher no hace fetch de las URLs.

## Errores y efectos

Códigos estables: `UNKNOWN_TOOL`, `INVALID_ARGUMENTS`, `PRODUCT_NOT_FOUND`, `REPOSITORY_ERROR`, `COMPARISON_UNAVAILABLE`, `COMPARISON_ERROR` e `INTERNAL_ERROR`. Una entrada inválida se rechaza antes de invocar repositorio o comparador. Los IDs bien formados pero inexistentes producen `PRODUCT_NOT_FOUND`.

No hay SQL, URL arbitraria, acceso a red, llamadas LLM, pagos, compras, selección de productos, escrituras ni persistencia en este módulo. Se copian argumentos/resultados y los productos que recibe el comparador para evitar mutaciones del repositorio inyectado.

## Pruebas offline

Desde `prototipos/paideia-local/`:

```sh
python -m unittest tests.test_pai_tools -v
python -m unittest tests.test_pai_runtime -v
```

Las pruebas de `pai_tools` usan repositorios `SYN-*` sintéticos en memoria, comparaciones sintéticas o bloqueadas y el builder de requests real en modo puramente local. No arrancan un servicio ni contactan red, proveedor, DB o catálogo cuantitativo real.

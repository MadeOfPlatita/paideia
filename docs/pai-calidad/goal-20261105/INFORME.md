# Objetivo 5-nov-2026: chat fiable y perfil que influye

Evidencia de los cinco hitos del `/goal`. Cada uno con su commit, su prueba y un
POST real contra `https://paideia-jg2n.onrender.com`.

## H1 — Varias llamadas de herramienta por turno

- Commit `d3b2793`. `providers.py` acepta hasta ocho llamadas por respuesta
  (`MAX_TOOL_CALLS_PER_TURN`) y deja de rechazar la segunda; el runner de
  `pai_runtime.py` valida el lote entero antes de ejecutar nada y las ejecuta en
  orden, dejando una llamada `assistant` con todas y un `tool` por cada una.
- Pruebas: `tests/test_pai_runtime.py` (dos calculos en el mismo turno acaban en
  texto; un lote con una llamada inválida no ejecuta ninguna) y
  `tests/test_providers.py` (nueve llamadas siguen siendo inválidas).

## H2 — El turno de herramientas ya no muere

- Causa raíz encontrada: no era el despachador. `catalogue_adapter` rechazaba el
  informe de condiciones con más de ocho métricas por producto y
  `pai_tools._project_conditions` solo admitía tasa y plazo. Cinco productos
  (FND-01, FND-04, ETF-01, ETF-03, ETF-04) documentan entre nueve y doce, así que
  cualquier búsqueda devolvía `REPOSITORY_ERROR` y el chat acababa en
  `CHAT_TOOL_ERROR` (502).
- Commits `17f2646` y `e43112d`: tope estructural de 32, proyección de las
  métricas documentadas con su unidad (TER, ISIN, SRI, comisiones, mínimos,
  divisa, réplica, vencimiento…) y validación estricta por unidad; métrica
  desconocida sigue fallando cerrado. La búsqueda se resuelve en el adaptador con
  raíz de palabra y palabras de familia.
- POST real: «¿Qué depósitos hay en el catálogo? Dime solo los nombres» → **200**,
  `catalogue.used = true`, texto del modelo retenido y datos locales con fuente.

## H3 — Redacción parcial también con calculadora

- Commit `2c6af2c`. En un turno con cálculo se quitan solo las frases con cifras
  y se conserva la explicación, con nota de cuántas se han quitado; además
  desaparece el umbral de seis palabras que tiraba restos válidos.
- POST real: «Si invierto 2000 euros al 3% anual durante 2 años, ¿cuánto tendré?»
  → **200**, respuesta no vacía («Es un escenario calculado, no una predicción…»)
  y nota «Se han quitado 1 frase(s) con cifras en un turno de calculadora…», con
  el resultado determinista aparte.

## H4 — Perfil → LLM (objetivo central)

- Commit `d2d7df7`. Tres pruebas capturan el cuerpo enviado al proveedor:
  `tests/test_profile_to_prompt.py`.
  - Los cuatro campos (`respuestas.objetivo`, `respuestas.horizonte`,
    `detalle_economico.importe_objetivo`, `detalle_economico.colchon_liquido`)
    aparecen literalmente en el prompt del sistema dentro de
    `chat-context-map-v1`.
  - Sin `context_consent` el prompt dice «No recibes ningún perfil personal» y no
    aparece ningún valor del mapa.
  - Los estados `omitido`, `no_se` y `sin_preguntar` viajan sin campo `valor`.
- El prompt aclara que esos campos se responden con lo que consta y sin invocar
  herramientas: no son condiciones de producto.
- A/B real contra producción, misma pregunta:
  - Perfil «colchón de imprevistos + 6-12 meses + 500-2.000 €»: «tu objetivo
    consta como **colchón de imprevistos** y tu horizonte como **6 a 12 meses**.
    Con ese horizonte tan corto… conviene priorizar la disponibilidad y la
    estabilidad del capital».
  - Perfil «ahorro a largo plazo + más de 3 años + 20.000-50.000 €»: «Ese
    horizonte implica que puedes asumir cierta volatilidad a cambio de
    rendimiento, pero sin olvidar que la inflación…».
  - Perfil con estados sin dato: «En tu mapa no consta el objetivo (omitido) ni el
    horizonte (marcado como «no sé»)… el importe tampoco está indicado». No
    inventa.

### Decisión de producto pendiente

Si el modelo repite cifras **del propio mapa** (por ejemplo «20.000-50.000 €»), la
puerta de cifras no las distingue de una cifra inventada y las retira. Una
pregunta que solo pedía el horizonte y el importe del mapa acabó con
`withheld_unbacked_claim` y respuesta vacía. Hay dos salidas y ninguna es obvia:
tratar como respaldadas las cifras que aparecen literalmente en la proyección, o
mantener la regla actual y aceptar que Pai no repita importes del mapa. No se ha
tocado sin esa decisión.

## H5 — `publication_ready: 0` de 20 candidatos

- Es **configuración por diseño**: `app.py` devuelve el literal `0` y todas las
  proyecciones fijan `publication_ready = False`; el catálogo es consultable pero
  no publicable mientras el producto no lo decida.
- POST real: «¿Puedo contratar ahora mismo algún producto del catálogo?» → **200**,
  sin fallo: la consulta usa el catálogo, el texto del modelo se retiene y la
  respuesta declara que se muestran datos locales con fuente, clase, fechas y
  límites, sin tasas inventadas.

## Estado de las suites

- **717 pruebas Python** y **108 Node** en verde en el último commit desplegado.
- Casos que fallan solo por contención de puerto/Tk y pasan aislados:
  `test_failed_start_is_terminal_and_explains_occupied_port` y
  `test_window_roundtrip_saves_sanitized_result_without_key`.

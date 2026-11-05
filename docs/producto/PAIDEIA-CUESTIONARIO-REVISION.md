# Revisión del cuestionario de perfil

Alcance: `app/static/profile_model.js` (12 preguntas, tres ramas).
Método: lectura y búsqueda de cada `key` en `static/`, `*.py` y `tests/`; sin ejecutar la app ni tocar código.

## 1. Dónde se consume hoy el perfil

Sólo hay tres consumidores reales, y uno es el resumen local:

1. **Chat, proyección opt-in de 4 campos.** `chat_context.py:8-13` define el DTO cerrado: `respuestas.objetivo`, `respuestas.horizonte`, `detalle_economico.importe_objetivo`, `detalle_economico.colchon_liquido`. El frontend pinta una casilla por campo (`static/app.js:930-937`) y sólo la habilita si la respuesta es `declarado`; al enviar construye `payload.context` (`static/app.js:1026-1027`). El backend valida y lo inyecta en el system prompt (`backend_services.py:542-548`).
2. **Resumen del mapa.** Las 12 se listan y se formatean en local (`static/app.js:1445-1460`).
3. **Calculadora/escenarios.** No acepta perfil: el contrato es de 6 campos fijos (`domain.py:9-16`, `domain.py:72-88`) y el formulario arranca vacío o con el ejemplo 1000/2/5 (`static/app.js:2706-2716`).
4. **Catálogo.** No acepta perfil: `search_products` sólo recibe `query`, `family`, `limit`; `compare_products`, ids y criterio (`pai_tools.py:43-160`). `catalogue_facts.py` no contiene ni una referencia a perfil, objetivo u horizonte.

El endpoint `POST /api/context-preview` sí conoce los 12 campos por propósito (`app.py:47-53`), pero exige `synthetic_fixture=true` y una fixture allowlisted: nunca acepta datos del usuario (`app.py:551-553`, `context_adapter.py:128-145`).

## 2. Pregunta → uso real → veredicto

| # | Pregunta (`key`) | Dónde se usa hoy | Veredicto | Motivo y consecuencia práctica |
|---|---|---|---|---|
| 1 | `respuestas.objetivo` (`profile_model.js:31-36`) | Chat opt-in (`chat_context.py:9`, `app.js:930`) | **Mantener, reescribir** | Orienta el tono y el ejemplo, pero su ayuda dice «no se usa para elegir productos» (l. 34) mientras el chat ya busca productos (`backend_services.py:309-311`). El usuario no entiende para qué contesta. Reescribir ayuda y opciones; `comparar_familias` ya es accionable con `compare_products`. |
| 2 | `respuestas.horizonte` (`profile_model.js:37-42`) | Chat opt-in (`chat_context.py:10`) | **Mantener, reescribir** | Es el dato que más cambia la familia de producto y ya viaja. El enunciado «si este ejemplo tuviera una meta» quedó anclado al ensayo ficticio. Consecuencia: se recoge un plazo en clave de juego cuando el chat habla de productos reales. |
| 3 | `respuestas.liquidez` (`profile_model.js:43-48`) | **Ninguno** (0 referencias fuera de `profile_model.js` y el resumen) | **Mantener y conectar** | Es el criterio que separa cuenta/depósito de fondo/ETF y `claims_catalog.py:124` lo cita como factor de decisión, pero no está en el DTO. Hoy se pregunta lo que más cambiaría la respuesta y no llega. Reescribir: «solo dinero ficticio» es un aviso, no un nivel de liquidez. |
| 4 | `respuestas.experiencia` (`profile_model.js:49-55`) | Sólo resumen y mapa legacy (`app.js:1426`) | **Reescribir** | Los 5 checkboxes de `temas_interes` no los lee ningún flujo; el `nivel` sí serviría para graduar la explicación. Fricción sin retorno. Dejar sólo `nivel` y añadirlo al DTO si se quiere usar. |
| 5 | `detalle_economico.importe_objetivo` (`profile_model.js:56-60`) | Chat opt-in (`chat_context.py:12`) | **Mantener** | Único importe con consumidor real. Además podría prefijar la calculadora, que hoy lo ignora (`app.js:2706-2716`). |
| 6 | `detalle_economico.ingresos_netos` (`profile_model.js:61-65`) | **Ninguno** | **Eliminar** | No hay evaluación de solvencia (`PERFIL-FUNCIONAL.md:9`) ni filtro por capacidad; es el dato más sensible y el de menor retorno. Se pide dinero real para nada. |
| 7 | `detalle_economico.gastos_esenciales` (`profile_model.js:66-70`) | **Ninguno** | **Eliminar** | Sólo tendría sentido junto a ingresos y colchón para una ratio que la app no calcula. Añade una pantalla y una cifra personal sin efecto. |
| 8 | `detalle_economico.deuda` (`profile_model.js:71-75`) | **Ninguno** | **Eliminar** | Subformulario de 4 campos (saldo, cuota, coste) sin consumidor: máxima fricción y máxima sensibilidad. El chat no compara deuda con inversión por diseño. |
| 9 | `detalle_economico.colchon_liquido` (`profile_model.js:76-80`) | Chat opt-in (`chat_context.py:12`) | **Eliminar** | Viaja, pero sin gastos no es interpretable: el chat sólo puede repetir la cifra. Duplica el papel de `importe_objetivo` y pide un saldo real. Si se elimina, hay que tocarlo en `chat_context.py:12` y `chat_context_model.js:3`. |
| 10 | `detalle_economico.compromisos_proximos` (`profile_model.js:81-85`) | **Ninguno** | **Eliminar** | El chat no maneja calendario ni compromisos y ningún cálculo los usa. Estructura anidada (total + plazo) para un dato muerto. |
| 11 | `riesgo.tolerancia` (`profile_model.js:86-91`) | Sólo mapa legacy (`app.js:1426`) | **Mantener y conectar** | Es la pregunta con más efecto sobre cómo explicar un fondo o un ETF y ya estaba prevista en `app.py:50,52`. Hoy se tira: el chat trata igual a quien vendería con una caída y a quien no. |
| 12 | `riesgo.capacidad_perdidas` (`profile_model.js:92-97`) | **Ninguno** | **Mantener y conectar** | Distingue tolerancia declarada de impacto real; sin ella el chat no puede matizar riesgo. Puede compartir pantalla con la 11. |

## 3. Desfases con la app de hoy

- El chat ya busca, detalla y compara productos concretos (`backend_services.py:309-311`, `pai_tools.py:49-83`), pero el cuestionario se presenta como «ejemplo ficticio» y afirma que no sirve para elegir productos (`profile_model.js:34,39,88`). El relato ya no coincide con el producto.
- El DTO sólo admite 2 enums y 2 importes (`chat_context.py:8-13`). Una respuesta con forma de flujo, deuda, compromisos o capacidad no puede viajar: `validate_context` la rechaza (`chat_context.py:31-36`) y el backend devuelve 400 `INVALID_CHAT_CONTEXT` (`backend_services.py:542-544`). No es que el dato se use mal: es que no cabe.
- El diseño anterior daba hogar a los doce campos: `CONTEXT_PURPOSE_FIELDS` (`app.py:47-53`) los reparte por propósito (`learn_basics`, `debt_education`, `risk_education`, `liquidity_planning`, `product_comparison`). El cuestionario se dimensionó para esa proyección; el chat real implementó una versión mínima de 4 campos y nadie recortó el cuestionario.
- Documentación desfasada: `docs/funcionamiento-05/03-perfil/01-MAPPING-PERFIL05.md:24` dice que «no hay endpoint que acepte o transmita el mapa» y `PERFIL-FUNCIONAL.md:16` que «el backend no recibe ni consulta el perfil». Hoy 4 campos viajan a `POST /api/chat`.
- Ocho de las doce preguntas no tienen consumidor. Dos de las cuatro que sí lo tienen son importes de baja señal; la pregunta con más valor educativo (tolerancia) se queda en el resumen.

## 4. Cuestionario mínimo viable

**A. Sin tocar backend (exactamente lo que hoy viaja):** 4 preguntas.
1. `respuestas.objetivo` (reescrita)
2. `respuestas.horizonte`
3. `detalle_economico.importe_objetivo` (opcional)
4. `detalle_economico.colchon_liquido` (opcional; es el eslabón débil del DTO)
   → cero cambios de contrato, pero se mantiene el importe menos interpretable.

**B. Recomendado (un cambio en `chat_context.py` + `chat_context_model.js`):** 6 preguntas, todas con consumidor.
1. `respuestas.objetivo` — «¿Qué quieres entender o comparar?»; opciones ligadas a familias y a riesgo.
2. `respuestas.horizonte` — «¿Cuándo podrías necesitar este dinero?», sin «si este ejemplo tuviera una meta».
3. `respuestas.liquidez` — «Si lo necesitaras antes de tiempo, ¿qué pasaría?»; fuera «solo dinero ficticio».
4. `riesgo.tolerancia` — mantener el escenario de 1.000 → 900 €, es concreto y comprensible.
5. `riesgo.capacidad_perdidas` — mantener; misma pantalla que la 4.
6. `detalle_economico.importe_objetivo` — opcional, con «No lo sé».
   → 3 campos nuevos en el DTO: `liquidez`, `tolerancia`, `capacidad_perdidas`; `colchon_liquido` sale.

**C. Descartables sin pérdida funcional:** ingresos, gastos, deuda, compromisos, colchón y `temas_interes`.

## 5. Coste de ejecutarlo

- `validateProfile` exige las claves exactas de `respuestas`, `detalle_economico` y `riesgo` (`profile_model.js:355-359`) y recorre `QUESTION_DEFS` (`:360`). Borrar preguntas invalida los snapshots v2 ya guardados, que se descartan como `invalid_saved_profile` (`:485`).
- Ruta barata: dejar de mostrar las 8 preguntas y mantener sus claves en `sin_preguntar`; no se rompe nada guardado. Ruta limpia: subir `PROFILE05_VERSION`/`SCHEMA_VERSION` y migrar.
- `api/_static/` es copia idéntica de `app/static/` (diff sin diferencias): cada cambio va dos veces.
- `tests/profile_model.test.cjs` y `profile_flow.test.cjs` cubren las 12; hay que recortarlos a la vez.

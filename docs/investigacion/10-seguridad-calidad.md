# Seguridad, privacidad y calidad — Paideia

**Alcance.** Investigación de diseño para una web académica en español, mayores de 18 años, con chat LLM opcional, comparador y flujo de simulación ficticio. Los casos de prueba que siguen son propuestas para ejecutar más adelante en entorno propio; no se han realizado ataques, pruebas de carga, despliegues, instalaciones ni llamadas a proveedores. Las licencias se comprobaron en páginas/repositorios oficiales; habrá que confirmar la licencia de la versión fijada y de sus dependencias antes de incorporarlas.

## Decisión ejecutiva

- **MVP de una semana:** biblioteca y catálogo de demostración con fecha/fuente visible; comparación y cálculos deterministas en el navegador; datos de simulación solo en memoria; perfil local limitado a preferencias y con botón de borrado; FAQ/chat de demostración sin proveedor externo. No hacer onboarding bancario ni pedir datos identificativos.
- **Chat externo después, no por defecto:** solo tras elegir proveedor, revisar condiciones de tratamiento/retención/transferencias, publicar aviso comprensible y disponer de una función backend que oculte la clave, limite el gasto y no envíe el perfil ni los datos de simulación. No existe una defensa que garantice eliminar la prompt injection; RAG y ajuste del modelo no la resuelven por sí solos.[1]
- **El LLM no decide cifras ni ejecuta acciones.** Como máximo explica material educativo o resultados ya calculados. No darle herramientas de escritura, ejecución de código, acceso a cuentas, operaciones de compra/contratación ni búsqueda libre de URLs. La comparación, las fórmulas y las etiquetas «simulado» pertenecen a código determinista y datos curados.
- **El botón final no contrata:** llamarlo «Ver simulación» o «Comparar escenarios». No hay endpoint de solicitud, cuenta, transferencia, inversión o aceptación de oferta. Mostrar “Esto es un ejercicio ficticio; no se envía ninguna solicitud ni se realiza una operación”.

## Diseño mínimo seguro y privado

### 1. Datos y perfil

- No pedir nombre, email, DNI/NIE, IBAN, tarjeta, credenciales bancarias, extractos ni identidad de entidad. Evitar también recolectar ingresos, saldos, deudas o patrimonio reales. Para el simulador, permitir importes hipotéticos opcionales; mantenerlos en memoria del navegador y no incluirlos en peticiones de red, analítica, errores ni prompts.
- El RGPD recoge que los datos personales deben ser adecuados, pertinentes y limitados a lo necesario; la AEPD también aborda minimización, transparencia, derechos y proporcionalidad al incorporar IA.[33][6]
- Si el perfil editable local se mantiene, guardar solo preferencias no financieras (p. ej. nivel educativo o formato preferido). No tratar `localStorage` como caja fuerte: OWASP advierte que un XSS puede leerlo y recomienda no almacenar allí información sensible; usar `sessionStorage` o memoria si no hace falta persistencia, y ofrecer «Borrar mis datos» visible.[35]
- Avisar antes de abrir el chat: “No escribas información personal o bancaria”. La AEPD recomienda mecanismos para impedir que se introduzcan datos personales, sensibles o confidenciales en sistemas no autorizados.[8] El aviso reduce el riesgo, pero no garantiza que el usuario no pegue datos: la mitigación principal es no adjuntar su perfil ni sus cálculos al contexto del LLM.
- No guardar conversaciones en servidor. Si el proveedor externo se habilita, declarar qué texto se envía, a quién, para qué, cuánto se conserva y los controles disponibles. Proveedor, región, uso para entrenamiento, retención, contrato de encargo y base jurídica están **pendientes**; no afirmar que el chat es anónimo o que el proveedor no retiene datos. La guía AEPD de 2020 aparece marcada «EN REVISIÓN»; tomar como referencia reciente sus orientaciones de IA agéntica V1.2 (febrero de 2026) y revisar el análisis jurídico antes de producción.[6][7]

### 2. LLM, prompt injection y salidas de herramientas

- En la primera versión, sin tools de LLM. Si después se necesita una, permitir únicamente operaciones de lectura sobre catálogo fijo (p. ej. buscar IDs existentes); el servidor valida cada ID y recalcula por su cuenta. El modelo no determina permisos ni decide qué endpoint ejecutar. OWASP relaciona la agencia excesiva con exceso de funcionalidades, permisos o autonomía.[3]
- Tratar entrada del usuario, datos recuperados y salida del modelo como **no confiables**. Separar claramente contenido de catálogo de instrucciones; no meter secretos, prompts internos, datos de usuario o variables ambientales en contexto. No permitir que el modelo ejecute código, construya SQL/rutas, haga fetch de URLs aportadas por usuarios o escriba en almacenamiento.
- Validar cualquier argumento/respuesta antes de usarlo: esquema cerrado, tamaño máximo, tipos/rangos/enum e IDs existentes; rechazar campos inesperados, JSON parcial, números no finitos y respuestas fuera de límites. Ante fallo, no “reparar” ni ejecutar: descartar, registrar solo el tipo de error (sin prompt) y mostrar fallback. OWASP pide tratar la salida como la de cualquier usuario, validar antes de pasarla a funciones y codificarla según el contexto.[2] Zod ofrece validación de esquemas en runtime para TypeScript.[17]
- El prompt del sistema es una instrucción, **no** una frontera de seguridad. Añadir pruebas con contenido directo y texto de catálogo malicioso solo en fixtures locales, y verificar que no revela instrucciones/secretos, no cambia permisos y no habilita herramientas. OWASP indica que no hay prevención infalible conocida y recomienda combinar límites, validación determinista, mínimo privilegio y separación del contenido externo.[1]

### 3. Claves, gasto y abuso de recursos

- Una web estática no puede esconder una clave en JavaScript, variables `VITE_*/NEXT_PUBLIC_*`, sourcemaps ni peticiones del navegador. Si no hay backend con secreto protegido, dejar el chat externo deshabilitado y servir FAQ/demo local. La documentación de OpenAI —aplicable como referencia si se elige ese proveedor— dice que la clave es secreta, no debe exponerse en cliente y debe cargarse en servidor desde variable de entorno o gestor de claves.[28]
- En el backend: clave por entorno/proyecto, mínimo privilegio, separación dev/prod, rotación y revocación; nunca en Git, HTML, logs ni respuestas de error. Fijar presupuesto diario/mensual del proveedor, límite de tokens de entrada/salida, longitud de mensaje, timeout, concurrencia y frecuencia antes de abrir el chat. OWASP API4 incluye límites de operaciones/tamaño/tiempo y límites de gasto de proveedores externos entre los controles relevantes.[4]
- Si se escoge Node/Fastify, `@fastify/rate-limit` puede fijar `max` y `timeWindow`, identifica por IP por defecto y devuelve `429`; verificar correctamente la IP de cliente y el proxy de hosting antes de depender de esa identidad.[20] No registrar IP completa por rutina; definir retención mínima y revisar el impacto de cualquier identificador con privacidad.
- Sin reintentos automáticos de una solicitud costosa. `429`, timeout, modelo no disponible o presupuesto agotado deben detener la llamada y mostrar el estado. Aplicar límites también al tamaño del catálogo/paginación y a cargas entrantes aunque el MVP no acepte ficheros.

### 4. Markdown, HTML y enlaces

- Preferencia: texto escapado por el framework / `textContent`, con saltos de línea; no insertar la salida del LLM con `innerHTML`. OWASP recomienda `textContent` frente a `innerHTML` para mostrar datos no confiables.[35]
- Si el Markdown es un requisito real, limitar los elementos permitidos, deshabilitar HTML crudo, aceptar solo esquemas de URL aprobados (p. ej. `https`) y sanear el HTML resultante con DOMPurify antes de insertarlo. Sin iframes, SVG, imágenes remotas ni HTML arbitrario. DOMPurify se describe como sanitizador XSS de HTML/MathML/SVG; no reemplaza el encoding contextual ni la política de URLs.[18][2]

### 5. Simulación que no recopila ni contrata

- Catálogo de demostración versionado en el repositorio; cada fila indica fuente, fecha de consulta, moneda, supuestos, comisiones y si el valor es ficticio. No llamarlo “oferta vigente” ni colocar ranking si faltan costes o condiciones.
- Inputs opcionales y claramente hipotéticos; cálculo en cliente, sin guardar. Botón “Restablecer” borra importes y resultados. Al cerrar o actualizar, no rehidratar escenarios financieros desde almacenamiento persistente.
- La pantalla de resultado incluye supuestos editables y etiqueta “simulación educativa, no oferta ni recomendación financiera”. Mantener separados TIN, TAE, comisión, interés bruto/neto, impuestos no contemplados y período. Banco de España explica que la TAE incorpora gastos y comisiones y depende del supuesto de interés compuesto/reinversión; sirve para comparar depósitos/cuentas si las condiciones comparadas son equivalentes.[27]
- Ningún texto, tool-call o botón debe poder convertir el flujo en una solicitud de contacto o contratación. No incluir formulario de datos de cliente ni integrar APIs bancarias/pagos.

## Checklist de salida priorizado

### P0 — condición para publicar el MVP

- [ ] Catálogo y cálculos ficticios identificados como tales, fuente/fecha/supuestos visibles; sin feeds o scraping no licenciados.
- [ ] Simulador funcional sin login y sin endpoint de transacción; sin PII ni datos bancarios; valores financieros solo en memoria.
- [ ] Perfil con datos mínimos, local, editable y borrable; no se envía al LLM ni a analítica. Texto y política de privacidad reflejan el flujo real.
- [ ] Chat externo apagado hasta tener backend; clave ausente del bundle del navegador, repositorio, sourcemaps, logs y mensajes de error; cuotas/budget limit configurados antes de activarlo.[28][4]
- [ ] Sin tools de escritura ni URLs arbitrarias. Todas las entradas/salidas externas pasan por límites y validación de esquema; un fallo del modelo nunca modifica datos ni realiza una operación.[1][2][3]
- [ ] Salida renderizada como texto; si se permite HTML/Markdown, parser/sanitizador y allowlist de links, más pruebas de contenido malicioso inerte.[2][18][35]
- [ ] Límites documentados de caracteres, tokens, tamaño de respuesta, concurrencia y frecuencia; respuesta `429`/timeout legible y sin reintento automático.[4][20]
- [ ] Pruebas financieras P0 (abajo) aprobadas con fixtures fijos y cálculo de referencia independiente del LLM.

### P1 — antes de invitar a un piloto público

- [ ] WCAG 2.2 nivel AA como objetivo de diseño; axe automatizado más revisión manual de teclado, zoom y lector de pantalla; corregir todos los bloqueos críticos.[25][29]
- [ ] Pruebas funcionales en móvil/desktop, borrado del perfil, estados vacíos, stale data, fallo de API y límites de gasto.
- [ ] Prueba de carga con 100 usuarios virtuales únicamente sobre staging propio, con respuestas LLM simuladas y autorización del titular del entorno; no hacer carga a proveedor/modelo externo.
- [ ] Inventario de dependencias, licencias de versiones fijadas y política básica de actualización/retirada; contrato/retención/región del proveedor revisados si se habilita IA.

## Pruebas financieras y de abuso (especificación, no ejecutada)

**P0 — integridad financiera**

1. **Ahorro/cuentas/depósitos:** fixtures con capital, plazo, tipo, periodicidad de abono, comisiones y condiciones; comprobar diferencia entre TIN y TAE, interés bruto/neto según los supuestos declarados y redondeo monetario. Casos límite: tipo cero, saldo/plazo cero, importe mínimo/máximo, comisión mayor que el interés y fin de plazo. No inferir reglas fiscales ni capitalización ausente en la ficha.
2. **Deuda:** tabla de amortización determinista; saldo inicial = principal, suma de amortización = principal (salvo política explícita de redondeo), saldo final no negativo y cuota final ajustada a céntimos. Cubrir tipo cero, cambio de período, comisión, última cuota y valores negativos/no finitos rechazados.
3. **Fondos/ETF:** escenarios hipotéticos con aportación, horizonte, variación y costes explícitos; no presentar rentabilidad pasada como futura ni retorno esperado como garantizado. Si falta TER, comisión, moneda o fecha del dato, mostrar “dato no disponible” y no ordenar como mejor.
4. **Comparador:** mismo capital, plazo, moneda y criterio; comprobar que comisión/coste cambia el resultado, que empate queda estable, y que fichas incompatibles no se comparan sin advertencia. Cada dato lleva fuente y fecha; datos viejos no se muestran como actuales.
5. **Precisión:** evitar acumulación con `float` binario sin política; usar decimal/fixed-point para dinero y definir la regla de redondeo en cada período. Resultados de referencia calculados por código independiente, no por la respuesta del LLM.

**P0 — abuso y privacidad, solo fixtures sintéticos en local**

1. **Tool/output:** respuesta malformada, esquema incompleto, campos extra, ID desconocido, importe fuera de rango y salida truncada → rechazo seguro; no ejecutar comandos/SQL/URL/operación y ofrecer respuesta de respaldo.
2. **Inyección directa/indirecta:** instrucciones hostiles dentro de pregunta o ficha de catálogo → no exponer prompt/clave/datos, no otorgar permisos ni cambiar el flujo. Es prueba de frontera y de no agencia, no una promesa de “detectar toda inyección”.
3. **XSS/Markdown:** texto de respuesta con HTML/script-looking, links con esquema no permitido y caracteres de control → render inerte, sin nodo activo, navegación ni carga externa.
4. **Privacidad:** perfil/importe simulado no aparece en petición al chat, logs, telemetría, URL, error report ni almacenamiento tras borrar; usar valores sintéticos de prueba, nunca datos de usuarios reales.
5. **Clave:** una cadena de clave ficticia de prueba no aparece en bundle, sourcemap, repositorio, respuesta ni logs; verificar también que el backend no acepta una clave desde el navegador.
6. **Abuso de API:** entradas demasiado grandes, ráfaga, solicitudes simultáneas, timeout/429 y agotamiento de presupuesto → límites aplicados, explicación simple, sin duplicar llamadas ni degradar catálogo/calculadora. OWASP destaca la falta de límites como causa de agotamiento de recursos y costes de proveedor.[4]
7. **No contratación:** completar todas las pantallas de simulación y comprobar en red/estado que no se crea usuario, lead, solicitud, transacción ni instrucción de inversión.

**P1 — accesibilidad/calidad de servicio**

- Teclado: todos los controles operables, foco visible/no oculto y orden lógico. WCAG 2.2 SC 2.1.1 exige funcionalidad operable por teclado; SC 2.4.11 evita que el foco quede totalmente oculto.[13][15]
- Contraste: al menos 4.5:1 para texto normal y 3:1 para texto grande (con las excepciones WCAG aplicables); no usar solo color para riesgo/resultado.[11]
- Controles: objetivos de puntero de al menos 24×24 CSS px o cumplir la excepción de espaciado/equivalencia; etiquetas visibles y errores descritos en texto.[12]
- Móvil/zoom: reflow sin pérdida ni scroll en dos dimensiones a 320 CSS px salvo contenido que realmente lo requiera; probar ancho móvil, 200–400% de zoom, orientación y texto ampliado.[14]
- Chat/resultados dinámicos: anunciar “consultando”, error y resultado con región de estado sin mover el foco; validar con lector de pantalla real. WCAG 4.1.3 requiere que los mensajes de estado sean programáticamente determinables sin recibir el foco.[16]
- Automatizar flujos con Playwright + axe-core, pero no tomar un scan limpio como certificación: Playwright señala que muchos problemas solo aparecen en pruebas manuales; axe-core cubre reglas de WCAG 2.2 y deja casos para revisión humana.[29][25]

## Herramientas open source mínimas y licencias verificadas

| Uso | Herramienta | Licencia upstream verificada | Recomendación / límite |
|---|---|---|---|
| Validar respuestas/argumentos en TypeScript | Zod | MIT | Una sola librería de esquema runtime; rechazar salida inválida, no “arreglarla” con el LLM.[17] |
| Salida enriquecida (solo si es necesaria) | DOMPurify | MPL-2.0 **o** Apache-2.0 | Sanear HTML generado tras reducir formato; por defecto preferir texto escapado. Licencia alternativa declarada en package.json upstream.[18][36] |
| Markdown acotado opcional | markdown-it | MIT | No renderizar Markdown arbitrario directamente; revisar opciones de HTML y URLs en la versión fijada.[19] |
| Rate limit si el backend usa Fastify | `@fastify/rate-limit` | MIT | Configura ventanas/cuotas y 429; controlar IP real si hay proxy; no sustituye límites globales/coste del proveedor.[20] |
| E2E y accesibilidad automatizada | Playwright + axe-core | Apache-2.0 + MPL-2.0 | Pruebas de rutas críticas y reglas WCAG; añadir evaluación manual.[22][25][29] |
| Carga propia | Locust | MIT | Escenarios Python con usuarios virtuales, pausas y métricas; ejecutar solo sobre staging controlado, no contra producción ajena ni proveedor LLM.[23] |

Las licencias son de los repositorios/paquetes upstream consultados, no una revisión de compatibilidad legal del producto. Fijar versiones y revisar archivos de licencia de la release y dependencias transitivas antes de instalar o distribuir. No se instaló ninguna herramienta.

## Carga controlada para 100 usuarios y límites de alcance

- Con Locust, definir un recorrido realista de catálogo → comparación → cálculo; subir gradualmente a **100 usuarios virtuales**, con pausas de lectura y una prueba de estabilidad posterior. Ejemplo de criterio inicial a aprobar por el equipo: `p95 ≤ 2 s` para catálogo/cálculo local y `<1 %` de errores inesperados; son objetivos propuestos, no un benchmark medido ni garantía del hosting.
- Ejecutar en un staging propio y aislado. Usar proveedor LLM simulado; probar el limitador aparte con identidad de test controlada. No enviar 100 VUs a una API comercial: evita coste y no prueba capacidad propia. No correr hasta que exista entorno de staging y autorización explícita.
- No inferir que “100 usuarios registrados” equivale a 100 solicitudes simultáneas. Acordar concurrencia, duración, think-time y presupuesto con el equipo. Un límite 429 intencional no cuenta como error si coincide con la política; medir latencia, errores inesperados, uso de memoria y comportamiento del fallback.

## Fallback transparente

| Fallo | Comportamiento visible |
|---|---|
| Chat deshabilitado, límite 429 o sin presupuesto | “El asistente no está disponible ahora”; mantener biblioteca, comparador y simulador funcionando. Ofrecer FAQ editorial claramente etiquetada, no una respuesta falsa “del modelo”. |
| Timeout después de enviar | Indicar que no se obtuvo respuesta y que no se reintentará automáticamente; no afirmar que el proveedor no recibió el texto si se desconoce. Ofrecer reintento manual con aviso. |
| Esquema/salida inválida | Descartar salida; mostrar contenido educativo validado o pedir reformular. Nunca presentar números inventados por el LLM. |
| Catálogo o feed no disponible | Mostrar última copia curada con fecha y etiqueta «puede estar desactualizada»; si la antigüedad afecta la comparación, no ordenar/recomendar. |
| Calculadora inválida | Explicar qué dato falta o está fuera del rango y conservar el resto de la web; sin valor aproximado silencioso. |

## Viable ahora / fuera de alcance / pendientes

**Viable con dos personas, una semana y cero euros:** simulador determinista con productos ficticios; contenido y FAQ curados; perfil local mínimo y borrable; chat simulado/desactivado sin clave; validación y límites en las pocas rutas propias; pruebas de fórmulas, privacidad, teclado y axe; checklist de operación y un escenario de 100 VUs que se ejecutará solo cuando exista staging propio.

**No prometer en este MVP:** contratación real/ficticia que active operaciones, asesoramiento o recomendación personalizada, conexión a bancos, custodia de datos financieros, precios/datos diarios de productos reales sin fuente/licencia/API y presupuesto, LLM externo sin proxy y revisión contractual, disponibilidad garantizada para 100 concurrentes, auditoría legal RGPD/financiera o certificación WCAG.

**Pendiente antes de habilitar IA o datos reales:** proveedor y coste máximo; almacenamiento de claves del hosting elegido; términos de uso/retención/entrenamiento/región y contrato de tratamiento; aviso/consentimiento si aplica; base jurídica, retención y política de logs/cookies; licencia y fecha de cada fuente de productos; revisión humana de accesibilidad y revisión jurídica de lenguaje de simulación. La orientación AEPD reciente pide enfoque de protección de datos desde el diseño y evaluación de errores/uso humano como parte de una implantación controlada.[7][8]

## Sources

[1] https://genai.owasp.org/llmrisk/llm01-prompt-injection — OWASP LLM01:2025 Prompt Injection
[2] https://genai.owasp.org/llmrisk/llm052025-improper-output-handling — OWASP LLM05:2025 Improper Output Handling
[3] https://genai.owasp.org/llmrisk/llm062025-excessive-agency — OWASP LLM06:2025 Excessive Agency
[4] https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption — OWASP API4:2023 Unrestricted Resource Consumption
[6] https://aepd.es/guias/adecuacion-rgpd-ia.pdf — AEPD: Adecuación al RGPD de tratamientos que incorporan Inteligencia Artificial (2020, en revisión)
[7] https://www.aepd.es/guias/orientaciones-ia-agentica.pdf — AEPD: Orientaciones sobre Inteligencia Artificial agéntica (V1.2, febrero de 2026)
[8] https://www.aepd.es/guias/sumario-recomendaciones-iag-aepd.pdf — AEPD: Resumen básico de obligaciones y recomendaciones para la gestión de IAG
[11] https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum — W3C WAI: WCAG 2.2, contraste mínimo
[12] https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum — W3C WAI: WCAG 2.2, tamaño mínimo del objetivo
[13] https://www.w3.org/WAI/WCAG22/Understanding/keyboard — W3C WAI: WCAG 2.2, teclado
[14] https://www.w3.org/WAI/WCAG22/Understanding/reflow — W3C WAI: WCAG 2.2, reflow
[15] https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum — W3C WAI: WCAG 2.2, foco no oculto
[16] https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html — W3C WAI: WCAG 2.2, mensajes de estado
[17] https://github.com/colinhacks/zod — Zod, repositorio oficial
[18] https://github.com/cure53/DOMPurify — DOMPurify, repositorio oficial
[19] https://github.com/markdown-it/markdown-it — markdown-it, repositorio oficial
[20] https://github.com/fastify/fastify-rate-limit — @fastify/rate-limit, repositorio oficial
[22] https://github.com/microsoft/playwright/blob/main/LICENSE — Playwright, licencia oficial
[23] https://github.com/locustio/locust — Locust, repositorio oficial
[25] https://github.com/dequelabs/axe-core — axe-core, repositorio oficial
[27] https://clientebancario.bde.es/pcb/es/menu-horizontal/podemosayudarte/tiposinteres/guia_textual/latae/tae_deposito.html — Banco de España: TAE de depósito o producto de ahorro
[28] https://platform.openai.com/docs/api-reference/authentication — OpenAI API: autenticación y protección de claves
[29] https://playwright.dev/docs/accessibility-testing — Playwright: pruebas de accesibilidad
[33] https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32016R0679 — EUR-Lex: Reglamento General de Protección de Datos (texto español)
[35] https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html — OWASP HTML5 Security Cheat Sheet
[36] https://github.com/cure53/DOMPurify/blob/main/package.json — DOMPurify package.json, metadatos de licencia

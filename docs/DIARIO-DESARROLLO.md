# Diario de desarrollo de Paideia

Bitácora del proyecto: qué se pidió, con qué herramientas y APIs se trabajó, qué
cambió, qué se probó de verdad y qué quedó pendiente. Se escribe en orden
cronológico y se corrige cuando una entrada anterior queda desmentida.

Regla de la casa: aquí no se copian claves, tokens ni datos personales. Las
credenciales viven solo en el entorno local (`app/.env`, ignorado por git) o en
el panel del proveedor, y el diario se limita a decir **dónde** están.

Las entradas antiguas se conservan tal como se escribieron: reflejan lo que se
sabía en su fecha y algunas rutas (`prototipos/paideia-local`, carpetas de
investigación) cambiaron después. El estado vigente es el del apartado anterior.
Algunas entradas dicen «repositorio público» o «pendiente de publicar»: reflejan
la decisión de ese día, no la de hoy.

## Estado al 6 de noviembre de 2026

- Aplicación completa en **https://paideia-jg2n.onrender.com** (Render, servicio
  `srv-dbltti56e07s73afrle0`). Chat con **Command Code** y modelo
  `deepseek/deepseek-v4.1-flash`.
- Escaparate congelado en **https://paideia-mu.vercel.app** (Vercel), con la IA
  apagada; se conserva como enlace secundario.
- Repositorio privado **MadeOfPlatita/paideia**; `master` solo con lo revisado y
  desplegado.
- Catálogo: 20 candidatos y 22 fichas (dos depósitos sintéticos comparables),
  **341 condiciones servidas**, todas con URL, título y fecha de la fuente o
  marcadas como desconocidas.
- Pruebas: **751 Python** y **109 Node** en verde con `app/tools/quality_gate.py`.
- El justificante del ensayo se imprime como documento A4 independiente, no como
  una copia de la web.

## Herramientas utilizadas

| Herramienta | Para qué se ha usado | Límite observado |
| --- | --- | --- |
| Hermes Agent | Asistente y orquestador de todo el trabajo: leer el repositorio, editar, probar y desplegar | Depende del proveedor de modelos y de su cuota; el modelo activo no acepta imágenes |
| Subagentes (`delegate_task`) | Investigación en paralelo (fuentes, APIs, auditorías de espaciado, revisión de fichas) | Máximo 50 por turno; cada uno ve solo su encargo, no esta conversación |
| Navegador real por CDP | Recorridos de la app, medición de huecos en píxeles, capturas y comprobación de la impresión | No sustituye a un lector de pantalla ni a una prueba con usuarios |
| `pytest` / `unittest` | Suites de backend, catálogo, perfil, privacidad y contraste | Necesita un intérprete con pytest; la puerta de calidad lo busca |
| `node --test` | Pruebas del modelo de perfil y de la interfaz | No ejecuta el navegador: eso se hace aparte |
| Servidor Python estándar | App local en `127.0.0.1` para probar sin desplegar | `ThreadingHTTPServer`, sin autenticación de usuarios |
| Git + GitHub CLI (`gh`) | Historial por hitos, repositorio privado, comprobación de visibilidad y de secretos | El despliegue de Vercel no acepta la autoría de los commits: se publica desde una copia sin `.git` |
| Render (panel + API REST) | Servicio web, variables de entorno, despliegues y estado | Plan gratuito: el servicio se duerme tras unos 15 minutos sin tráfico |
| Vercel (CLI + API + AI Gateway) | Escaparate estático y paso a modelos gratuitos | El proyecto no está conectado al repositorio privado: los despliegues son manuales |
| LM Studio local (`minicpm-ocr-1.0`) | Leer capturas de pantalla cuando el modelo no podía verlas | Transcribe, no razona sobre la interfaz |
| PowerShell, `curl`, `grep` | Tareas del sistema en Windows: parar procesos, comprobar respuestas, buscar en el código | Rutas y comillas de Windows obligan a comprobaciones dobles |

## APIs y proveedores

### Modelos de lenguaje

| Proveedor | Endpoint | Modelo usado | Dónde se usa | Estado |
| --- | --- | --- | --- | --- |
| Command Code | `https://api.commandcode.ai/v1/chat/completions` | `deepseek/deepseek-v4.1-flash` | Producción (Render) | Activo; clave solo en el panel de Render |
| Command Code (prueba) | mismo endpoint | `reflection/beam:free` | Evaluación puntual | Probado; se volvió a deepseek por decisión del objetivo |
| Groq | `https://api.groq.com/openai/v1/chat/completions` | `openai/gpt-oss-20b` (local) y `openai/gpt-oss-120b` (Render) | Desarrollo y alternativa | Configurable; no es el proveedor de producción actual |
| Vercel AI Gateway | `https://ai-gateway.vercel.sh/v1/chat/completions` | `reflection/beam-free` | Alternativa gratuita | Clave creada y proveedor admitido; no se usa en producción |

El chat solo envía una pregunta si el usuario marca el consentimiento, y solo
con los campos del mapa que haya autorizado uno a uno. Ninguna clave se ha
escrito en el repositorio, en capturas ni en el chat.

### Publicación y control de versiones

- **Render**: aplicación completa (Python + estáticos). Variables gestionadas por
  panel/API; el token de la API vive en `~/.cache/paideia/render.token` y no se
  imprime.
- **Vercel**: función WSGI que empaqueta catálogo y estáticos para el escaparate;
  el chat va apagado allí.
- **GitHub**: repositorio privado, rama `master` con commits en español, un hito
  por commit. Se comprobó por API que no hubiera secretos ni el repositorio
  público antes de la entrega.

### Fuentes de datos financieros

| Tipo | Fuentes | Cómo se usa |
| --- | --- | --- |
| Regulador | CNMV (fichas de fondos, registro, folletos) | Identidad, registro, fechas de folleto y reglamento |
| Deuda pública | Tesoro Público (valores en circulación y resultados de subasta) | ISIN, vencimiento, saldo vivo y resultados de subasta |
| Bancos | Openbank, Pibank, EBN Banco, Self Bank, Renault Bank, MyInvestor | Cuentas y depósitos: TAE, TIN, mínimos, liquidación, cancelación, garantía |
| Gestoras | Bestinver, Azvalor, Olea Gestión | Fondos: ISIN, comisiones, SRI, patrimonio, régimen, folleto |
| Emisores de ETF | BlackRock (iShares), DWS (Xtrackers), SSGA (SPDR), VanEck | TER, SRI, divisa, reparto, réplica |

Cada condición guardada lleva `source_url`, `source_title`, `accessed` y el
literal del que sale. Si la fuente no publica un dato, la ficha dice «sin dato
documentado»: no se estima, no se copia de un comparador y no se rellena por
analogía.

## Reglas de trabajo con APIs

1. Una clave, un sitio: `.env` local ignorado por git o variables del proveedor.
   Nunca en el código, en un commit, en una captura o en el chat.
2. Ningún envío a un modelo sin consentimiento explícito del usuario en esa
   petición.
3. Un contador de intentos reales (`mission_ledger.py`) cuando se hacen pruebas
   con proveedores: diario append-only, cupo y corte duro.
4. Los datos financieros se citan; lo que no está publicado se queda desconocido.
5. Las operaciones son ficticias: no se piden credenciales, documentos, pagos ni
   se ejecuta ninguna contratación.

## Entrada 1 — Lectura del planteamiento

### Prompt del usuario

> Lee el idea.md y haznos todas las preguntas que consideres necesarias

### Trabajo realizado

- Lectura del archivo IDEA.md del proyecto.
- Identificación de entregables: aplicación online, enlace en Wiki, código fuente, diario de desarrollo y demo presencial.
- Cuestionario sobre alcance, público, datos, IA, privacidad, alojamiento y diseño.

## Entrada 2 — Definición con el equipo

### Extractos de las respuestas del usuario

> Queremos tenerlo hecho en una semana

> Todo gratuito

> Paideia nombre

> Teníamos pensado como un triangulito que se llame Pai

> Un usuario compara alternativas y ve cómo cambian los escenarios con sus decisiones.

Los extractos anteriores no son la transcripción completa. Las decisiones y las cuestiones pendientes se consolidan en REQUISITOS.md.

### Decisiones recogidas

- Web educativa y de exploración financiera para mayores de edad, en español y orientada a España.
- Mascota Pai, perfil conversacional editable y chat posterior.
- Biblioteca amplia con información breve y detalle verificado al comparar.
- Deseo de datos actualizados diariamente y de servicios gratuitos, sujeto a viabilidad.
- Comparador, simuladores de interés simple/compuesto, escenarios, glosario y PDF opcional.
- Sin registro, perfil local borrable y minimización de datos.
- Demo cuyo peor caso de afluencia se estima en 100 usuarios concurrentes.

### Advertencias y decisiones no cerradas

- No se ha probado una fuente que cubra los productos deseados ni su actualización diaria.
- No se ha demostrado capacidad para 100 usuarios ni seleccionado API gratuita.
- Una preferencia por riesgo elevado no equivale a capacidad de asumir pérdidas.
- La experiencia del usuario no habilita a la aplicación como asesor profesional.
- La respuesta sobre contratación necesita aclaración; no se ha aprobado ejecutar operaciones.

## Fuentes consultadas durante la definición

- CNMV, evaluación de la idoneidad: https://cnmv.es/portal/inversor/idoneidad?lang=es
- CNMV, decisiones de inversión y entidades autorizadas: https://cnmv.es/portal/inversor/decisiones-inversion?lang=es
- Documentación de facturación y niveles de acceso de Gemini API: https://ai.google.dev/gemini-api/docs/billing

Estas consultas sirven para identificar restricciones, no acreditan cumplimiento legal ni garantizan cuotas o capacidad de un proveedor.

## Entrada 3 — Cierre del alcance inicial

### Respuestas del usuario

> 1. La simulación de contratación
> 2. Correcto
> 3. Si
> 4. Por ahora si, luego ya vamos estirando el chicle

### Decisiones confirmadas

- Incluir simulación de contratación, no limitarse a enlazar a entidades.
- Aceptar el último dato verificado si falla una actualización, con advertencia, fuente y fecha, y excluir datos inadecuados por antigüedad de las comparaciones.
- La aplicación publicada debe funcionar con los ordenadores del grupo apagados.
- Priorizar cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF; ampliar después según viabilidad.

### Criterios de seguridad para el diseño

- La simulación debe identificarse como tal, no ejecutar operaciones y utilizar datos ficticios, sin pedir credenciales, documentos personales ni pagos.
- No se han verificado todavía fuentes diarias gratuitas, capacidad del chat para 100 usuarios concurrentes ni alojamiento. La aprobación del alcance no prueba su viabilidad técnica.

## Entrada 4 — Investigación paralela y contraste

### Prompt del usuario

> Lanza todos los subagentes que puedas para investigar información, recursos, apis, repos, no seremos los primeros haciendo algo así

### Trabajo realizado

- Diez subagentes iniciales en paralelo, uno por área: cuentas/depósitos, deuda pública, fondos/ETF, LLM gratuita, alojamiento, MCP, repos similares, UX, rigor financiero y seguridad/calidad.
- El primer intento de fondos/ETF no entregó informe; se lanzó un subagente adicional con una estrategia de recuperación distinta.
- Resultado comprobado en disco: diez informes y diez JSON de fuentes. Agregación programática: 290 registros y 284 URLs distintas por comparación literal, conservando procedencia. No se presenta ese número como corroboración independiente de todos los datos.
- Se seleccionaron ocho repositorios de referencia; no se clonó ni ejecutó su código.
- El coordinador contrastó 19 URLs mediante GET públicos y guardó textos y metadatos. Entre ellas: términos Gemini, cuotas Cloudflare, documentación MCP/BdE/CNMV/Tesoro, README/licencias y tres endpoints estadísticos/de mercado.
- Se verificó el archivo de citas de la síntesis con evidencia literal; se corrigió un conflicto entre informes sobre los términos de reutilización de estadísticas del BdE.
- Se calcularon en Python escenarios teóricos de consumo de Neurons. No son pruebas de carga ni de calidad de modelos.

### Entregables

- `investigacion/00-SINTESIS.md`: conclusiones contrastadas, propuestas y límites.
- `investigacion/README.md`: índice de diez áreas.
- `investigacion/FUENTES_AGREGADAS.json`: fuentes deduplicadas con observaciones originales.
- `investigacion/evidencia-parental/`: textos y registro de comprobaciones directas.

### Límites y decisiones pendientes

No se encontraron evidencias suficientes de una API abierta gratuita que resuelva todo el catálogo contractual diario. La inferencia gratuita para cien usuarios sigue sin prueba. No se crearon cuentas, claves, despliegues ni aplicación; no se ejecutaron pruebas de carga. Proveedor, arquitectura y cambios de alcance son propuestas, no decisiones nuevas del grupo. Mantener productos reales verificados y no sustituir silenciosamente chat o catálogo por ejemplos ficticios.

## Entrada 5 — Ampliación de APIs, planificación y recuperación tras interrupción

### Extractos de prompts del grupo

> He pensado en construir aquí una base de datos propia postgresql para la LLM. Me afecta bastante eso de que no tengamos datos, lanza más subagentes buscando APIs que nos sean útiles

> te he dado una mayor capacidad de subagentes, lanza todos los que necesites para tapar todos los problemas que presenta la planificación de Paideia

> Te has quedado sin uso en mitad, continua

### Trabajo y evidencia

- Segunda ronda de diez áreas de datos; revisión de informes y JSON. El frente de fondos tradicionales falló y no se contó como entrega útil; el coordinador lo recuperó mediante fuentes primarias y descarga real de Bestinver.
- Bestinver: GET público de Excel NAV con TLS verificado, 192.506 bytes, ZIP íntegro, 10.554 observaciones y fechas únicas. Se guardó SHA-256 e inspección, sin publicar el histórico como catálogo ni acreditar su licencia.
- Recuento programático de los diez informes de APIs: 177 observaciones de fuentes y 169 URLs distintas. No son confirmaciones independientes de todo el contenido.
- Contraste: JSON YieldMeister de 70 filas globales, solo cuatro ES; su depósito Openbank dice 12 meses frente a seis en la fuente oficial enlazada. Se registró discrepancia y no se validó para comparación.
- Contraste: FundFacts pricing y requests publican cuotas diferentes (5/1.000 frente a 15/9.000 Free/Pro); se guardaron ambas evidencias y se dejó cuota efectiva sin verificar.
- Dieciséis frentes de planificación y dos auditorías cruzadas recibidas/revisadas. Se consolidó precedencia, mappings de identidad/unidades/fechas/citas/errores y gates de privacidad/seguridad sin declarar aplicación implementada.
- Se corrigieron procedencia de citas del modelo de capacidad y el cómputo de su primer burst durante el trabajo previo. Se preservan pruebas y evidencias de esa corrección.
- Se escribió una regresión de consentimiento remoto: falló con accepted_chat_processing=false aceptado; se corrigió el schema para exigir true y pasó. Cuatro tests de contrato correctos.
- Reejecución del coordinador: motor 29 tests; capacidad seis tests; tres escenarios coincidentes; ingesta siete casos/diez registros/un rechazo estructural esperado; ninguna fixture publicable. Seis meta-schemas válidos con referencias locales resueltas.

### Entregables de esta ampliación

- `ESTADO_Y_PLAN.md`: estado ejecutivo y cuatro decisiones pendientes del grupo.
- `investigacion-apis-02/00-SINTESIS.md`, `02-fondos-tradicionales.md`, `00-VALIDACION.json`, `00-FUENTES-AGREGADAS.json` y `evidencia-coordinador/`.
- `planificacion-03/17-auditoria-contratos/` y `18-auditoria-coherencia/`: hallazgos históricos contrastados.
- `planificacion-03/19-integracion/`: criterio vigente, manifest propuesto, regresión y pruebas reproducidas.

### Límites que no se dan por resueltos

No hay aplicación, PostgreSQL, cuentas cloud, proveedor LLM probado ni despliegue. Faltan proveedor/privacidad, permisos por campo/acción y muestras de catálogo, adaptación de varios contratos y QA/carga integrada. Se mantiene IA real, productos reales, operación ficticia y presupuesto 0 EUR. PostgreSQL se conserva como propuesta del grupo; JSON es opción de publicación/caché, no rechazo unilateral de la DB. La recepción documental no equivale a solucionar todos los bloqueos.

## Entrada 6 — Verificación al reanudar

- Se recuperó el estado guardado, incluidos `ESTADO_Y_PLAN.md`, la síntesis de la segunda ronda y el criterio de integración. No se reinició la investigación ni se lanzaron agentes redundantes.
- Se volvió a contar desde los diez JSON originales de APIs: 177 registros de fuentes y 169 URLs distintas.
- Se reejecutaron las comprobaciones locales: consentimiento 4/4, motor financiero 29/29, capacidad 6/6, tres escenarios reproducidos e ingesta con siete casos/diez registros/un rechazo esperado. Todas terminaron con código 0; ninguna fixture es publicable.
- Evidencia nueva: `planificacion-03/19-integracion/REANUDACION-VERIFICADA.json`. Son pruebas de referencia aisladas, no de aplicación, proveedor, PostgreSQL o concurrencia.
- Permanecen las cuatro decisiones del grupo recogidas en `ESTADO_Y_PLAN.md` y los defectos de contrato pendientes expresamente enumerados en `19-integracion/ESTADO.json`. No se crearon cuentas, servicios ni despliegues.

## Entrada 7 — Fecha y decisiones de alcance/contexto

- El grupo confirma entrega el martes 3 de noviembre; se verificó que 2026-11-03 corresponde a martes. Hora pendiente.
- Aprobados 20 productos reales, cuatro por familia, como primer objetivo ampliable y no techo. Se mantiene la intención de ampliar con evidencia y usos permitidos.
- Aceptados cupo y cola visibles del chat real, sin promesa de 100 respuestas IA simultáneas.
- El grupo acepta en principio cifras económicas seleccionadas, pero exige ponderar la calidad/funcionalidad frente al perfil completo. No se ha elegido una estrategia definitiva ni autorizado transmitir datos reales.
- Se actualizan requisitos/estado y se escribe `planificacion-03/19-integracion/EVALUACION-CONTEXTO.md`: comparación controlada sin perfil/relevante/completo, datos sintéticos, criterios y ponderación inicial propuesta con puertas no compensables de exactitud, privacidad y coste cero. No hay resultados de IA ni ganador; no se ha creado cuenta o enviado un prompt remoto.

## Entrada 8 — Recepción de validación y preparación del goal

- Recibidas y leídas cinco entregas de `deleg_2d7b1900`: Google, Groq, arnés, proyección y catálogo candidato.
- El coordinador inspeccionó código y reejecutó siete tests del arnés y veintiuno de proyección: todos OK. Dataset: seis casos; requests locales: dieciocho; llamadas/resultados LLM: cero; ningún ganador.
- Catálogo: veinte IDs únicos, cuatro por familia, catorce identidades verificadas por evidencia previa y seis propuestas; doce ISIN únicos aplicables con checksum válido. Ninguno marcado publicable. No equivale a veinte ofertas listas para comparar.
- Contraste directo de términos Google/Groq y revisión adicional de AUP Groq, con evidencia exclusiva. Se corrigió la inferencia de que la frase B2B “not for consumer use” prueba por sí sola una prohibición de aplicaciones para usuarios finales.
- Detectada frontera pendiente entre los formatos de perfil del arnés, perfil05 y proyector: sus pruebas aisladas no acreditan interoperabilidad. El goal debe implementar/testear el mapping.
- Actualizado `GOAL-NOCTURNO.md` tras la recepción: preparado para introducir como comando, no activado ni programado. No hay proceso nocturno, llamada externa autenticada, cuenta nueva o despliegue por esta revisión.
- Evidencia: `validacion-04/00-VERIFICACION-COORDINADOR.json` y `00-REVISION-COORDINADOR.md`.

## Entrada 9 — Ejecución y verificación del prototipo local

### Encargo del usuario

> Construye y verifica el prototipo local navegable de Paideia siguiendo íntegramente docs/GOAL-NOCTURNO.md y los resultados de docs/validacion-04/00-REVISION-COORDINADOR.md. Ejecuta el trabajo y las pruebas, corrige fallos y entrega evidencia; no te limites a redactar otro plan. Respeta los límites de permisos y parada del encargo.

### Resultado

- Se preservó e inspeccionó el trabajo existente en `prototipos/paideia-local/`; no se empezó de cero ni se sobrescribieron los entregables de investigación.
- Frontend HTML/CSS/JS y backend Python stdlib conectados; servidor loopback 127.0.0.1:8765. Adaptador perfil05/proyector04/materializador03 integrado con fixtures sintéticas allowlisted; ningún perfil enviado a IA.
- Verificación final: 39 tests correctos, sintaxis JS correcta, 17/17 comprobaciones HTTP y ocho rutas en cada tamaño escritorio/móvil. Se probaron perfil opcional/edición, filtros/comparación, escenario negativo con SVG y tabla, ensayo ficticio, selección local de contexto, opt-in/borrado y error/recuperación del servicio.
- Tres defectos reproducidos y corregidos: metadatos de interés simple mal etiquetados, URL de fuente que desbordaba comparador móvil y formulario de chat construido pero no insertado en DOM. Se conservaron regresiones/evidencia roja y verde.
- Se reinició únicamente el proceso gestionado de este prototipo para servir la corrección del backend. URL verificada al cerrar: http://127.0.0.1:8765/.
- Evidencia consolidada en `prototipos/paideia-local/evidence/FINAL.json`; instrucciones en README y alcance/QA en VERIFICACION.md, con siete capturas reales.

### Límites y parada

Se detiene el encargo en el hito local probado. No se instala nada, crea cuenta, activa facturación, envía información real ni despliega. IA, comparación de calidad, condiciones/derechos de ofertas, perfil UI completo, PostgreSQL, actualización diaria y capacidad de cien usuarios permanecen pendientes. El inventario de veinte candidatos no se anuncia como veinte ofertas verificadas y el error de chat no se hace pasar por una respuesta IA.

## Entrada 10 — Diseño rechazado, backend primero

- El grupo indica: «El diseño no me gusta nada, pero primero hagamos el backend y funcionamiento, el diseño lo último».
- Se registra que la dirección visual del prototipo no está aprobada; se congela el trabajo estético y se mantiene la UI como herramienta de prueba.
- Se despachan dos implementaciones con tests offline y salidas exclusivas: adaptador de IA y núcleo de hechos/comparabilidad. Lote `deleg_171ec57c`; detalle y límites en `PRIORIDAD-BACKEND.md`.
- No se atribuyen al backend módulos aún no recibidos; tampoco se hacen llamadas reales, se leen claves o se habilita facturación. La integración y pruebas HTTP de los módulos se realizarán después de revisión.

## Entrada 11 — Integración funcional del backend

- Recibidas y revisadas las dos entregas de `deleg_171ec57c`; reproducida la suite de 80 tests sin el error de `_parse_iso_date` observado anteriormente por un agente; el fallo no se reproduce con los archivos finales.
- Integrados `providers.py` y `catalogue_facts.py` con `app.py` mediante `backend_services.py`; chat deshabilitado y hechos/política vacíos por defecto. Sin cambios de frontend/diseño, instalaciones, claves reales o llamadas externas.
- Consentimiento remoto exacto, rechazo de perfiles/roles/modelos del cliente, errores HTTP seguros, cero reintentos y sin razonamiento interno en respuestas. Herramientas no solicitadas rechazadas, sin ejecución ni segunda llamada.
- Comparabilidad opcional con códigos/fuentes/fechas/permisos por uso; los positivos HTTP son exclusivamente `SYN-*` aislados. No se inventó ninguna oferta. Política ausente y métrica ausente son estados distintos.
- Eliminado el límite accidental de exactamente veinte candidatos; prueba de crecimiento a veintiuno sintéticos sin modificar el catálogo real.
- Regresión roja→verde de secreto ficticio escapado en JSON: el adaptador comprueba también el resultado decodificado y argumentos anidados antes de devolverlos.
- Verificación final del coordinador: **94 tests OK, 19/19 checks HTTP y sintaxis JS correcta**. Reiniciado solo el servidor gestionado de esta aplicación; el probe del proceso viejo falló antes y el actualizado pasó.
- Informe: `../prototipos/paideia-local/BACKEND-INTEGRACION.md`; evidencia: `evidence/BACKEND-INTEGRACION.json` y salidas de pruebas. IA real, A/B/C, dispatcher, condiciones publicables, perfil completo, DB/hosting/ingesta/carga siguen pendientes; diseño al final.

## Entrada 12 — Recorrido funcional y alternativa sin PostgreSQL

- El grupo aprueba las prioridades funcionales y cuestiona si PostgreSQL hace falta utilizando APIs; pide lanzar los subagentes necesarios.
- Se separa fuente de datos (API) de persistencia/caché/normalización. No se decide PostgreSQL por inercia ni se elimina unilateralmente: se prepara comparación con pruebas locales propias.
- Escrito `funcionamiento-05/00-CONTRATO.md` antes del despacho; siete frentes independientes en `deleg_09c6c535`, salidas exclusivas y recepción pendiente. Detalle en `00-COORDINACION.md`.
- Implementación: herramientas, orquestación, perfil funcional y admisión/cupo. Investigación acotada: condiciones reales y alojamiento. Spike: APIs fake directas frente a caché persistente y fallos/reinicio.
- Sin diseño nuevo, cuentas, claves reales, APIs autenticadas, instalaciones, DB real, pago o despliegue por esta aprobación. No se anuncian pruebas de IA real ni resultados de agentes aún no recibidos.

## Entrada 13 — Recepción de siete frentes e integración funcional

- Recibidas/revisadas las siete entregas de `deleg_09c6c535`. Se reprodujeron las suites y el experimento de snapshot sin crear DB, usar cuentas/claves reales ni llamar un LLM.
- Integrados ToolDispatcher/ToolChatRunner/admisión en LocalChatService y HTTP: reserva por cada upstream, cola 202/posición/reanudación manual y errores controlados; deshabilitado por defecto y con consentimiento/uso de catálogo como gates.
- Corregidos con rojo→verde: consentimiento faltante en formulario, respuesta 200 válida descartada, búsqueda de veinte candidatos que excedía el presupuesto de request y pérdida del código específico de límite/timeout en la ruta admitida.
- Perfil con cuatro preguntas iniciales y ramas voluntarias económicas/riesgo probado en navegador contra API real. Diferencia cero/no saber/omitir/sin preguntar; edición exacta, guardado solo opt-in, borrado de copia y memoria y ausencia de envío del perfil. Representación decimal string local no equivale al schema remoto numérico original.
- Resultado final: 155 tests Python, 13 Node, 19/19 HTTP, 16 combinaciones ruta/escritorio-móvil. Admisión: sus 18 tests repetidos veinte veces sin fallo. Spike: once tests y experimento 6/6 reproducidos; cien lecturas fake: directa100 requests frente a snapshot1/99hits, no chats.
- Datos recontados: veinte candidatos/cuatro por familia, 62 hechos numéricos (45 known del borrador/17 conflict), 53 sin fecha efectiva; cero candidatos listos cuantitativamente. No se cargó el borrador ni se actualizaron las identidades originales por inferencia.
- Caché/JSON versionado recomendado condicionalmente para catálogo, sin PostgreSQL impuesto. Presupuesto/cola requieren estado durable/coherente; se contrastó que KV tiene consistencia eventual y no se asume contador atómico global. Hosting sigue como hipótesis, sin despliegue.
- Se comprobaron citas/evidencias de informes; se corrigió el exceso de llamar prohibición contractual a la advertencia de Render Free. El patch fallido de un extracto Cloudflare no se dio por aplicado; archivo actual y citas verificados.
- Se detuvieron los servidores de prueba 8766/8767; se conserva solo el normal8765 con IA no conectada. Captura adicional del padre falló por timeout, con evidencias DOM/red ya guardadas; errores de harness separados de defectos de app.
- Evidencia consolidada: `funcionamiento-05/08-integracion/REVISION-COORDINADOR.md`, `VERIFICACION.json`, salidas de pruebas y browser/. IA real/A-B-C/contexto, ofertas aprobadas/ingesta, presupuesto durable, alojamiento/carga pública y diseño permanecen pendientes.

## Corrección del cuestionario — continuidad y selección obligatoria

Se reprodujeron ambos problemas indicados por el grupo: salida tras cuatro preguntas y avance en blanco. Se conectaron las doce preguntas en un recorrido con tres bloques; Continuar exige respuesta válida o elección explícita No lo sé/Omitir, también en subcampos de deuda. Pausa/reanudación desde el primer pendiente, edición sin borrar ante vacío. Sin rediseño ni envío de perfil.

Verificación: 155 Python, 15 Node, 19/19 HTTP, dos JavaScript correctos y 16 aserciones de navegador. Evidencias rojas/verdes y salida real de regresión en funcionamiento-05/09-cuestionario/. No actualiza las limitaciones de IA, datos ni alojamiento.

## IA real — preparación de acceso seguro

El grupo autorizó IA real, confirmó cuenta Groq por email y eligió ventana local segura ante el fallo del gestor protegido. Se implementó/probó `secure_groq_smoke.py`: campo oculto, confirmación Free, no lectura de claves del entorno ni persistencia, una petición fija sin perfil/reintentos, informe seguro separado de test-only. Cuatro nuevas regresiones rojo→verde; suite159 y Node15 correctas. Ventana real abierta y visibilidad comprobada. No se afirma llamada externa hasta leer evidencia real; chat web no activado.

## Primera llamada real a Groq verificada

Recibida notificación de la ventana y leído el destino exacto `prototipos/paideia-local/evidence/REAL-IA-SMOKE.json`: fecha UTC2026-10-29T16:34:20.977120+00:00, modelo openai/gpt-oss-20b, una llamada, HTTP200, test_only:false, sin truncado/rechazo/perfil. Conectividad real acreditada. La respuesta «ahorrar ... sin riesgo» es financieramente demasiado absoluta: no se da por aprobada la calidad. Evidencia/valoración en funcionamiento-05/10-ia-real/RESULTADO-REAL.md. No se activó chat web ni se hicieron nuevas llamadas/reutilización de clave automáticamente.

## Bloque autónomo — sesión limitada y QA local

Revisadas entregas de calidad/chat; el primer agente de sesión quedó bloqueado sin implementación y no se dio por terminado. Coordinador corrigió con rojo→verde el registro de tools por subset y añadió scope servidor calculator_only, sin aprobar catálogo. Nuevo agente entregó lanzador; revisión propia añadió borrado de referencia de clave al consumir el cupo24. También se actualizó prompt educativo tras simplificación 'ahorro sin riesgo', sin dar por aprobada calidad.

Regresión182Python/20Node y19/19HTTP tras restaurar servidor8765parado. Ventana temporal nueva abierta y visible, clave no leída: confirmación Free y benchmark opcional separados, máx24peticiones hasta17:40:20UTC. Evaluación A/B/C de seis casos y dieciocho solicitudes preparada y validada con constructor Groq. Sin nuevas llamadas externas por parte del coordinador ni activación automática; pendiente autorización segura y lectura de evidencias reales. Ver funcionamiento-05/11-hora-autonoma/04-coordinador/REVISION-LANZADOR.md.

## Cierre del bloque autónomo de IA

Dos turnos web reales en sesión temporal: calculate_scenario ejecutada con1030EUR y texto truncado visible; respuesta conceptual posterior completa sobre riesgos/inflación. Último contador runtime4intentos (benchmark1+cálculo2+conceptual1), sin perfil. A/B/C detenido tras1intento sin resultado válido, sin retry ni ganador; no se adivina causa original. Se mejoraron diagnósticos/brevedad offline.

Revisión independiente detectó TOCTOU y, tras primer fix, autocierre de última reserva. Sesiónreal detenida preventivamente,8768cerradoverificado, clave no reutilizada. Dos ciclos mínimos con TDD;195Python,20Node,19HTTP,probepropio y veredicto independiente final favorable en rutas revisadas. Garantía lógica de compromiso, no instante físico ni cancelación enflight. Normal8765disponible sinIA. Bloque cerrado antes17:40:20UTC, sin ampliarplazo ni reabrir sesión. Pendientes nueva validación real de los últimos cambios y A/B/C/contexto, catálogo publicable, persistencia/cupos y hosting. Informe: funcionamiento-05/11-hora-autonoma/CIERRE.md.

## Recorrido académico de escenarios — aceptado con fuentes propias

Adaptación de una sola pantalla para el trabajo de Alejandro: guía Empezar/ajustar → Comparar/entender → Guardar, ejemplo ficticio explícito en A, copia A→B, resumen de diferencias y descarga HTML ya existente. Sin código de terceros y sin tocar el resto de la aplicación.

TDD por cortes, con RED/GREEN de orden, ejemplo, copia, diferencias y navegación; integración de 33 comprobaciones por tamaño. El revisor independiente reprodujo un defecto real: en la guía «Guardar», Enter desplazaba al informe pero dejaba el foco en el enlace y el Tab siguiente volvía a Capital inicial de A. Corregido en el handler común con `tabindex=-1` y foco `preventScroll` (manteniendo el scroll), con RED propio en los tres destinos y 24 combinaciones de Enter/Tab reales.

Dictamen independiente final del cambio **favorable** (`passed: true`, sin problemas de seguridad ni errores lógicos), con 9/9 comprobaciones de foco y 33/33 del recorrido en 1280 y 390 px, y descarga HTML real con cinco tablas verificada en `revision/`. Evidencias en `docs/recorrido-escenarios-academico/` (`implementacion/`, `revision/`, `revision-foco-1/`, `correccion-foco-1/`, `coordinador/`) y guion para exponerlo en `GUION-DEMO.md`. Límites declarados y no superados: sin impresión nativa ni PDF desde el panel, sin auditoría global de accesibilidad/seguridad, sin persistencia de filtros o selección, y sin activar Pai.

## Ejecución del encargo de pendientes — B0 y B1.1-B1.2

Inicio de `docs/GOAL-PENDIENTES-20261103.md`, sin diseño. B0: comprobado que no hay claves en archivos del proyecto, que `.gitignore` cubre `.env`, que el arranque sin entorno deja el chat en `not_configured` y que el estado expone el cupo (6/minuto, 60/día) que la interfaz muestra como «Llamadas usadas hoy». B1.1: el prompt de Pai usa el mapa adjunto y pide solo el dato que falta. B1.2: una respuesta real de 256 tokens salió truncada; el techo quedó configurable hasta 900 con 800 en el chat, validado por el adaptador, y la misma pregunta devolvió 487 caracteres sin truncar. Regresión 383 Python y 41 Node. Queda de B1 el historial, el filtro de calidad, los errores reales y la rúbrica de diez preguntas.

## B2 y B3 — condiciones reales y comparación utilizable

El catálogo dejó de ser solo metadatos. Se añadió `catalogue_conditions.py`, que convierte lo documentado en condiciones con estado (`known`, `unknown`, `conflict`, `stale`) y motivo, y `conditions_service.py`, que lo expone en `/api/conditions`, en la ficha y en la comparación. Las condiciones transcritas a mano (`data/condiciones.json`) mandan sobre el literal y distinguen tramos con requisito.

Lecturas del día documentadas en `docs/catalogo-condiciones-20261103/EVIDENCIA.md`: EBN Banco 12 meses 3,10 % TAE (oficial, documento 29-09-2026), Self Bank 12 meses 2,75 % (prensa), Pibank 3,03 % vencido el 31-10-2026, Openbank 6 meses con dos tramos. La comparación a 12 meses ya funciona con EBN y Self Bank; Pibank y Openbank quedan fuera con motivo escrito.

En la interfaz: tasas con estado en la biblioteca, sección separada para los productos transcritos, bloque de condiciones en la ficha y salto a Escenarios con la tasa importada como supuesto editable. **B7 (publicación) queda bloqueado** hasta que el equipo decida visibilidad y licencia del repositorio y la cuenta de hosting.

## B7 — repositorio publicado

Código subido a **https://github.com/MadeOfPlatita/paideia** (público). El equipo decidió que la profesora lo corrija desde el repositorio, así que debe poder descargarse y ejecutarse en su equipo: el README explica el arranque sin dependencias y qué es simulado. Sin licencia de reutilización; derechos de los autores. `.env` fuera del repositorio y sin claves en el contenido publicado.

El enlace público de la web sigue pendiente: el servidor actual es `ThreadingHTTPServer` en loopback y Cloudflare Workers usa el modelo `fetch`, de modo que hay que portar la capa HTTP. Esa parte necesita la cuenta de Cloudflare del equipo.

## B7 — web pública en Vercel

Cloudflare quedó descartado: sus Python Workers fallan al desplegar con `ModuleNotFoundError: workers` incluso con el proyecto oficial (issue abierto). Se portó la capa HTTP a una función WSGI para Vercel (`api/index.py`), reutilizando el motor y las condiciones; el catálogo y los estáticos se empaquetan en el build. Probada primero en local y después sobre la URL pública: catálogo, ficha, comparación (EBN 3,10 % / Self Bank 2,75 %, `quantitative_ready: true`) y cálculo (4.255,02 €) coinciden con la app local.

Aplicación publicada en **https://paideia-mu.vercel.app**. El chat de IA va apagado en la web pública y la interfaz lo indica; la clave no se sube a un servidor ajeno. Repositorio privado hasta la entrega, por decisión del equipo.

## B6 — detenido tras revisión final

El segundo ciclo no supera la revisión independiente. Persisten defectos confirmados de paridad, estados y vigencia, además de un caso del ensayo B5 para ACC-01 que no se cubrió con Openbank. No se hace un tercer ciclo ni se presenta B6 como terminado. Detalle y límites en `informe-b6/REVISION-CICLO-2.md`.

## B5 — ensayo ficticio con producto documentado

**Actualización:** la aceptación inicial solo acreditó Openbank; la revisión B6 posterior halló un caso ACC-01 con condiciones falsamente ausentes. La aceptación general queda pendiente.

Se conservó el recorrido de cinco pasos y se añadieron hechos con fuente, fecha y estado sin presentarlos como ofertas vigentes. El primer dictamen independiente fue desfavorable; tras un ciclo de corrección, el segundo informó resultado favorable, incluidos el recorrido con Openbank sin POST, recuperación y paridad de datos local/WSGI. Evidencia y límites en `ensayo-b5/EVIDENCIA.md`; cambios locales, sin publicación. El cálculo y los importes siguen siendo ficticios.

## B4 — Pai con catálogo

**Actualización final de misión:** tras dos ciclos la revisión independiente volvió a rechazar B4; se ha detenido sin aceptar ni publicar. `pai-catalogo-20261103/REVISION-CICLO-2.md` conserva casos y límites.

## B9 — robustez y accesibilidad funcional

## B1 — avisos de error del chat

Se distinguen límite y timeout sin prometer que una petición incierta no llegó al proveedor. El segundo ciclo recibió revisión independiente favorable acotada, con una observación pendiente de reproducir; B1 en su conjunto sigue sin aprobarse por calidad y riesgos del filtro. `pai-calidad/REVISION-ERRORES-CICLO-2.md`.

## B9 — detalle

La segunda corrección obtuvo revisión independiente favorable para el alcance local. Mejora foco, recuperación de errores y validación; se mantiene un desplazamiento horizontal residual en escritorio a 320 px y no se ha ensayado con lector de pantalla real. Sin publicación. Ver `robustez-accesibilidad/REVISION-CICLO-2.md`.

## B8 — privacidad del chat (aceptado)

El diagnóstico con pruebas RED demostró cuatro defectos reales: el consentimiento negaba enviar el mapa mientras el cuerpo lo llevaba, con la IA pública apagada la interfaz afirmaba «no se envía nada» y hacía un POST que recibía 405, el borrado no distinguía historial ni lo ya enviado al proveedor, y otra pestaña resucitaba la copia borrada.

El ciclo 1 corrigió textos, gate de envío, alcance del borrado, avisos de fallo de almacenamiento y revocación entre pestañas por `storage`. La revisión independiente `deleg_f88b1fa6` aprobó los cuatro objetivos pero falló el bloqueo porque `chatIsConfigured()` devolvía verdadero con un `/api/status` sin bloque `ai`. El ciclo 2 lo cerró: sin `ai` o sin `status` textual no hay envío, se añadió la prueba `B8-2b` (roja antes del arreglo, verde después) y el aviso se actualiza si falla el estado.

La revisión final `deleg_604d244d` dio dictamen favorable con 72 comprobaciones propias y reproducción independiente del caso en rojo. Sin rediseño, sin proveedor real y sin publicar. Evidencia y límites en `privacidad-capacidad/EVIDENCIA.md`.

**Rectificación:** no consta revisión independiente favorable de B4 y una respuesta atribuyó a una fuente oficial un dato de fuente secundaria; su aceptación sigue pendiente. El servidor local que estaba en modo de depuración se detuvo; el chat público continúa desactivado.

El equipo aprobó abrir el catálogo a Pai y se hizo con un ámbito nuevo, `catalogue_read`: búsqueda, ficha y calculadora. Comparar sigue siendo cosa del comparador. El adaptador une los candidatos con los cuatro productos transcritos y adjunta cada condición con su estado y su fuente; la proyección se valida campo a campo antes de salir al modelo.

Probado con Groq real: preguntando por EBN responde 3,1 % con la URL oficial; preguntando por EBN frente a Self Bank responde 3,1 % frente a 2,75 % y avisa de que la fuente de Self Bank es secundaria. Por el camino hubo que aceptar llamadas sin `family`/`limit`, normalizar guiones tipográficos en los identificadores y subir el límite de rondas a tres.

## Misión de 4 h 30 min — 4 de noviembre de 2026

Trabajo local con el encargo `GOAL-PAIDEIA-4H30-20261104.md`: prioridad en una experiencia útil de Pai con productos trazables, sin rediseño y sin publicar nada que no estuviera revisado.

**Trazabilidad del catálogo.** Las condiciones derivadas del snapshot citaban la fuente como un id interno (`"1"`, `"2"`) sin URL: la ficha de ACC-01 mostraba «2,61 % TAE» sin enlace. Ahora `catalogue_conditions.derive(..., sources=...)` resuelve esos ids con el ledger real de fuentes (`docs/validacion-04/05-catalogo/evidencia/sources-ledger.json`), añade `source_refs` con URL, título y fecha de consulta y falla cerrado (`SOURCE_UNRESOLVED`) si un id no resuelve. La app local lee el ledger y la función WSGI lo lleva empaquetado.

Los dos depósitos comparables (`DEP-EBN-12` y `DEP-SELF-12`) existían en las condiciones y en el comparador pero no tenían ficha: `/api/products/<id>` devolvía `product: null`. Ahora tienen ficha mínima con lo transcrito y `conditions_state: "documented"`, sin entrar en la lista de 20 candidatos. El conflicto documentado de ACC-02 se sustituía por una frase genérica; ahora la ficha muestra el texto literal, mientras la lista y el comparador de metadatos siguen sin publicar cifras.

**Ensayo ficticio.** El paso de condiciones decía «Condiciones no documentadas» con una tasa documentada delante porque solo miraba `entry.source`; ahora usa también `source_refs`. Verificado en navegador con ACC-01: 2,61 % TAE, vigencia hasta 2026-11-18 y fuente enlazada.

**Pai con catálogo.** La proyección de herramientas descartaba `source_refs`; ahora las condiciones del chat llevan la fuente enlazada con título y fecha, con atribución «parcial» y clase «desconocida» cuando el registro no declara si es oficial o secundaria. El DTO de `/api/chat` ya no degrada esa condición a «desconocida», y un turno de catálogo con lista vacía deja de suprimir una explicación conceptual: no hay nada que atribuir y se mantiene el aviso de texto no validado.

**Contador global de intentos.** `mission_ledger.py` cuenta cada envío real antes de abrir la conexión, con manifest por perfil fuera del repositorio (`Paideia/ledger-missions`), diario append-only con `fsync`, corte duro y lock entre procesos; cubre las dos rutinas que abren HTTPS al proveedor (`providers._post` y `secure_groq_session._guarded_https_post`). La primera revisión independiente encontró un bypass por la ruta de sesión contada, el corte que solo dejaba de contar, la colisión con el directorio de la misión nocturna y la falta de `send_state` en el HTTP; los cuatro se corrigieron y se verificaron.

**Prueba real autorizada.** Con el cupo confirmado, se hicieron diez preguntas ficticias de la rúbrica desde la interfaz real: 15 intentos contados de 100. Tres respuestas conceptuales se mostraron, dos escenarios devolvieron el cálculo determinista correcto (1.000 € al 2 % compuesto dos años: 1.040,40 € y 40,40 €) y cinco quedaron suprimidas por el filtro léxico, incluidas preguntas legítimas sobre TIN/TAE o fuentes oficiales. Es un falso positivo del filtro, no una prueba de calidad del modelo: se documenta como límite y no se presenta a Pai como asesor validado.

**Maquetas.** Tres propuestas aisladas de la pantalla Comparar en `docs/diseno-ideas/maquetas/`, con datos ficticios, sin red y sin tocar la aplicación.

## 5 de noviembre — del prototipo local a la aplicación publicada

El prototipo vivía en `127.0.0.1` y no servía para la entrega: la profesora
necesita abrir un enlace. Se descartó Cloudflare (sus Python Workers fallan con
`ModuleNotFoundError: workers`) y se portó la capa HTTP a una función WSGI para
Vercel, con catálogo y estáticos empaquetados en el build.

Después se dio el paso a **Render**, que sí ejecuta la app completa: blueprint,
origen público declarado, rechazo de orígenes ajenos y un `main()` que no abre
`0.0.0.0` sin origen. El chat se conectó al proveedor y se comprobó con POST
reales. El escaparate de Vercel se congeló como enlace secundario.

## 5 de noviembre — proveedores de modelos y hitos H1-H5

Se añadieron tres proveedores con un registro único en `app/providers.py`
(Groq, Command Code y Vercel AI Gateway), seleccionables por variable de
entorno, con modelo validado y espera de 60 s para modelos que razonan.

Con el chat ya en producción se cerraron cinco hitos, cada uno con código,
prueba y POST real contra la URL pública:

- **H1**: varias llamadas de herramienta en un mismo turno (hasta el tope del
  runner), no solo una.
- **H2**: el turno de catálogo sin resultados deja una nota fija en vez de una
  respuesta vacía.
- **H3**: se redactan solo las frases con cifras sin respaldo, conservando el
  resto del texto.
- **H4**: el perfil autorizado se declara en la respuesta y cambia lo que
  responde Pai (A/B real con horizonte corto y largo).
- **H5**: `publication_ready` es configuración, no un dato: ninguna ficha está
  aprobada para publicación y el chat lo dice.

Evidencia: `docs/operacion/verificacion-h4-h5-20261105.json`.

## 5-6 de noviembre — repositorio presentable

Se borraron 886 archivos de bitácoras y documentos que se contradecían, y se
reescribieron la portada y el índice de `docs/`. Quedó lo que la app lee, lo que
las pruebas necesitan y lo que explica el producto. Después se podaron más
carpetas históricas conservando los fixtures que usa el código.

## 6 de noviembre — justificante con forma de documento

El justificante del ensayo salía en blanco al imprimir por una regla de impresión
demasiado amplia y, al arreglarla, seguía siendo una copia de la web. Ahora se
genera un documento A4 aparte (`receipt_print.css` + `buildReceiptDocument`):
membrete, expediente, sello de ensayo, carátula, condiciones con fuente, importe,
exclusiones y líneas de firma sin validez. En pantalla no existe; solo al
imprimir, y con marca de agua «ENSAYO FICTICIO».

## 6 de noviembre — fichas completas y auditoría del catálogo

La auditoría de las 20 fichas encontró que el mapeo de métricas descartaba 134 de
las 223 condiciones transcritas. Se añadieron las 51 métricas que faltaban (TIN,
TAE posterior, comisiones, garantía, elegibilidad, liquidación, divisa, subasta,
patrimonio, fechas…) y las condiciones servidas pasaron de 90 a 341.

Después se transcribieron 141 condiciones nuevas de fuentes oficiales: depósitos
de Openbank, Pibank, EBN y Self Bank; resultados de subasta de tres letras; y
folleto, DFI y ficha de Olea Neutral y Azvalor. Se corrigieron dos errores de
datos: el saldo vivo de las letras estaba dividido por mil y Pibank había
prorrogado su oferta hasta el 30/11/2026.

Evidencia: `docs/catalogo/investigacion-2026-11-06.json` y
`docs/catalogo/cobertura-2026-11-06.json`.

## 6 de noviembre — espaciado entre cajas

Privacidad y otras rutas tenían cajas pegadas: cuando dos bloques no eran
hermanos del mismo tipo (nota + sección, vista previa + confirmación) el hueco
caía a 0 px. Se pasó `.page-shell` a una rejilla de una columna con hueco
uniforme (20 px en escritorio, 16 en móvil), se quitaron los márgenes sueltos y
se subieron las rejillas de tarjetas. Ocho auditores independientes midieron las
rutas y sus hallazgos se incorporaron en una segunda pasada (bandeja de
selección, resultados curados, panel de Pai, escenarios, justificante, menú,
pie). Verificado en producción: mínimo 20 px en escritorio y 16 en móvil.

## 6 de noviembre — «Tu mapa» confirma cada respuesta

El cuestionario saltaba a la siguiente pregunta en el mismo clic, así que no se
veía qué se había respondido. Ahora cada respuesta queda en un box con la
pregunta anterior, el valor y el botón **Continuar**; «Cambiar respuesta» vuelve
al formulario con la selección puesta y el foco cae en Continuar para seguir con
el teclado.

## Cómo se verifica hoy

- `python app/tools/quality_gate.py` ejecuta **751 pruebas Python** y **109 de
  Node**; devuelve código distinto de cero si algo falla.
- Recorridos de navegador sobre la app servida: ocho rutas en escritorio y móvil,
  medición de huecos, desbordes y foco.
- Comprobaciones contra la URL pública: `/api/status`, `/api/conditions`,
  `/api/products/<id>` y el flujo del chat con preguntas ficticias.
- La evidencia se guarda en `docs/` en JSON o Markdown, con fecha.

## Límites vigentes

- El catálogo no es publicable: son borradores internos con fuente, no ofertas.
- Los cuatro ETF siguen por debajo del resto en campos (SRI, patrimonio, mercado,
  préstamo de valores); ACC-02/03/04 y los fondos Bestinver tienen huecos
  menores.
- La IA depende de un proveedor externo y de su cuota; si falla, el chat lo dice
  y no inventa una respuesta.
- Render en plan gratuito duerme el servicio tras unos minutos sin tráfico.
- Vercel es un escaparate congelado, no la app funcional.
- No hay cuentas de usuario, ni pagos, ni operaciones reales, ni datos personales.

## Registro a mantener al desarrollar

En cada bloque de trabajo se anotarán el prompt o su extracto identificado como tal, herramienta/modelo si se conoce, cambios realizados, decisiones, pruebas ejecutadas con su resultado real y limitaciones pendientes. No se anotarán claves ni información personal de prueba.

## Entrada — 7 de noviembre de 2026: Pai explica la práctica y vuelve a leer el catálogo

Petición del usuario: «le preguntas cómo montar un colchón y no sabe nada… no solo
hablo de colchones, sino el resto de términos y definiciones».

Cambios:

- El prompt separa dos registros: **dato de catálogo** (máximo tres frases, solo
  con herramientas) y **explicación práctica** (definición breve, tres a cinco
  pasos, ejemplo con los datos del mapa, hasta ocho frases, y qué vigilar). Las
  referencias generales se etiquetan como método y los importes del usuario no se
  redactan; las tasas de producto sin fuente siguen redactándose.
- Al ampliar las fichas a 341 condiciones, el turno de herramientas quedó roto:
  la proyección al modelo solo conocía 25 métricas, exigía valores de texto y
  cortaba en 32 condiciones por producto. Olea (33) y Azvalor (34) superaban el
  tope. Ahora las unidades salen del propio catálogo, el tope es 64 y los datos
  guardan literales de texto.
- El DTO del chat cortaba en 8 condiciones y marcaba el producto como «condiciones
  desconocidas»; además contaba como ilegible toda métrica que no fuera tasa o
  plazo. Ahora publica tasa y plazo (12 como máximo, con nota de recorte) y omite
  el resto sin desacreditar la ficha.
- La búsqueda acepta la familia en plural, con acento o sin él («depósitos»,
  «cuentas», «ETFs») y la consulta omitida equivale a listar; el contrato sigue
  cerrado a `null` explícito, campos abiertos y familias inventadas.
- La interfaz espera 45 s en vez de 12 y el proveedor admite 1.600 tokens de
  salida (1.200 en el chat), para que una respuesta práctica no se corte.

Pruebas y evidencia:

- `771 Python + 109 Node` en la puerta de calidad, exit 0.
- Nuevas pruebas: contrato de proyección sobre las 341 condiciones servidas,
  normalización de búsqueda y recorte declarado del DTO.
- En producción (`https://paideia-jg2n.onrender.com`, commit `fcad01d`): la
  pregunta por la TAE de la Cuenta Contigo responde «Condiciones documentadas;
  atribución parcial · TAE 2,61 % documentada, fuente oficial»; la pregunta por el
  colchón devuelve definición, pasos concretos (objetivo 3-6 meses, calcular la
  cifra, cuenta separada, automatizar, revisar) y qué dato falta.

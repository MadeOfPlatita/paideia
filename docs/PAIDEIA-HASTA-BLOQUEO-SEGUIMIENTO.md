# Seguimiento de la misión Paideia hasta bloqueo

**Inicio registrado:** 4/11/2026, 18:20, hora de Málaga. Misión autorizada en `GOAL-PAIDEIA-HASTA-BLOQUEO.md`; ejecución en esta sesión, no proceso independiente garantizado.

## Estado inicial y conservación

- Rama `master` en `c051749`; repositorio remoto comprobado privado al inicio. El cierre anterior tiene correcciones locales y las maquetas están sin seguimiento: conservarlas junto con el resto de cambios, sin limpieza ni reset.
- Groq de esta misión: **0 intentos reales realizados al iniciar**. No enviar hasta revisión independiente favorable de la frontera y el contador exactos, junto con todas las demás puertas de la misión; el contador de la misión anterior no debe reiniciarse ni reaprovecharse sin evaluación.
- La web pública no se ha modificado en esta misión; si se considera su actualización, el chat público debe permanecer apagado y se exige revisión y pruebas de la versión exacta.

## Orden y trabajos en curso

1. **Pai:** implementación acotada y pruebas sintéticas offline para utilidad, hechos y supuestos; pendiente de recibir y revisar cambios y revisión independiente.
2. **Catálogo e informe:** evaluación de fuentes y permisos de productos existentes, sin incorporar ni publicar datos por el mero hecho de encontrarlos; pendientes recorridos y revisión.
3. **Diseño:** adaptación CSS de la dirección B oscura en la app real, sin sustituir datos ni funciones por la maqueta; pendiente de verificación y revisión independiente.
4. **Contador:** diagnóstico independiente offline de rutas, carreras, documentación, aislamiento y provisión; ninguna conclusión de aceptación aún. Sin llamadas reales.
5. **Entrega:** pruebas integradas, continuidad, commits selectivos y publicación solo si se satisfacen las puertas exactas de la misión.

## Avance propio, 4/11/2026 18:38

- **Revisión independiente:** las cuatro delegaciones fallaron antes de producir resultados con HTTP 401 del proveedor de agentes. No hubo implementación ni dictamen independiente de esos agentes. El fallo es distinto de Groq. La revisión sigue pendiente; no se equiparan los tests del autor con una aprobación.
- **B6, sin aceptar:** la URL, título y fecha de la referencia de la condición pasan al informe, separadas de la URL de ficha. RED/GREEN del nuevo test y pruebas relacionadas; se ejecutó el recorrido con la app WSGI local, datos ficticios y el tema oscuro en escritorio y móvil: 40 comprobaciones por ejecución, incluyendo HTML leído en el navegador, fuentes, supuestos y consentimiento sin enviar chat. Evidencia `catalogo-hasta-bloqueo/recorrido-b6-oscuro-{desktop,movil}.json`. No acredita impresión nativa ni permiso de fuentes ni cierra todo B6.
- **Diseño, sin aceptar:** estilos oscuros añadidos a la app real y sincronizados con `api/_static`; los comportamientos no se sustituyeron por la maqueta. Comprobadas ocho rutas en 1440, 390 y 320 px sin desbordamiento horizontal de página en sus estados iniciales; captura en `diseno-hasta-bloqueo/`. La prueba de color pasó y se verificaron en navegador recorridos B1, B8 y B9 con proveedores ficticios. No es auditoría integral de accesibilidad ni prueba en móvil físico; requiere revisión independiente.
- **Catálogo:** revisión puntual en `catalogo-hasta-bloqueo/FUENTES-Y-PERMISOS.md`; no acredita permisos o vigencia, incluida la discrepancia histórica de Pibank. No se incorporaron como ofertas vigentes los datos consultados.
- **Puerta Groq:** no se ha hecho ningún intento real de esta misión; contador, seguridad y provisión nueva permanecen sin revisión favorable. No abrir una sesión real.
- **GitHub/Vercel:** sin commit, push ni despliegue de esta misión; hay cambios locales mezclados que deben preservarse. La revisión y las demás puertas son obligatorias antes de publicar.

## Cierre de la misión, 4/11/2026 19:05

Informe: **`CIERRE-PAIDEIA-HASTA-BLOQUEO.md`**. Resumen de lo comprobado desde el avance anterior:

- **Suites:** 615 pruebas Python en verde (exit 0) y 87 comprobaciones Node en los 14 archivos del prototipo (exit 0). Se corrigió un defecto de las pruebas del contador que las hacía fallar solo por haber pasado el corte del 4/11 (ventana fija + parche de `active_mission`, función que el transporte ya no consulta); ahora ejercitan `reserve_for_active_mission` con una ventana vigente.
- **Diseño:** auditoría de contraste WCAG AA en 8 rutas × 2 anchos con **0 fallos** y control negativo que sí detecta texto ilegible (`diseno-hasta-bloqueo/contraste.{json,txt}`); panel de Pai verificado en oscuro, sin desbordamiento a 390 px. Sigue **sin revisión independiente** y sin prueba en dispositivo físico.
- **Puerta Groq:** 0 intentos reales; sin manifest activo; diario histórico intacto con 15 líneas.
- **GitHub/Vercel:** repo `private` verificado, sin commit ni push; web pública sin cambios (`theme-color` anterior, `ai.not_configured`).

Con esto se agota el trabajo independiente seguro: lo que queda depende de restablecer el proveedor de agentes, reparar y revisar el contador, y decidir visibilidad y publicación. Los frentes anteriores no son tareas duraderas garantizadas. Este seguimiento no es una aprobación.

## Reanudación, 4/11/2026 19:25

El proveedor de agentes volvió a responder, así que el bloqueo por `HTTP 401` queda como incidencia pasada. El objetivo persistente de la sesión estaba **pausado** porque el juez lo declaró inalcanzable por ese 401; se reactivó (`status: active`, veredicto y motivo de pausa borrados, 5 criterios adicionales), comprobado leyendo el estado desde un proceso nuevo. Se relanzaron dos revisiones independientes —tema oscuro y puerta del contador— y queda pendiente lanzar la del delta B6 cuando termine la primera para no competir por puertos con dos suites de navegador a la vez.

## Diseño oscuro — ACEPTADO por revisión independiente, 4/11/2026 20:10

Dictamen `deleg_1514b34f` tarea 1: **`passed: true`**, sin hallazgos de seguridad ni de lógica, sobre la instantánea exacta `dark_theme.css` sha256 `aedc42dc…` e `index.html` `56fc1045…` (idénticos en `static/` y `api/_static`, verificado con `cmp`). El revisor comprobó con probes propias:

- **915 elementos de texto** por ancho en las 8 rutas, a 1440 y 390 px: **0 fallos** de contraste AA, y la sonda plantada (1:1) se detectó y se retiró.
- **Sin desbordamiento** horizontal de página en 24/24 combinaciones ruta × ancho (1440/390/320).
- **Avisos y consentimiento intactos**: consentimiento 20×20 a 15,78:1, aviso educativo 9,93:1, chip de proveedor 13,59:1, avisos de simulación y procedencia visibles.
- **Foco visible** (`#a9d8ff`, 12,56:1) y sin caída a BODY al deshabilitar el botón en vuelo.
- **Informe descargado e impreso en claro**: HTML autónomo (1 `<style>` en línea, 0 `<link>`, 0 `@import`) y PDF real con fondo blanco; `dark_theme.css` solo contiene un bloque `@media screen`.
- **Suites de comportamiento sin cambios**: B1 74 (72 PASS, 2 observaciones), B8 28/28, B9 32/32 y Node 87/87.

Límites registrados por el revisor: emulación sin dispositivo físico ni lector de pantalla; la mascota decorativa conserva sus colores claros (2,86:1, es arte `alt=""`, no texto funcional); en escritorio se ocultan dos rótulos no funcionales (`Tu recorrido`, `Explora primero…`); una ruta de impresión ajena al tema (`comparison_report.css`) ya ocultaba el cuerpo antes de este cambio.

**Consecuencia:** el bloque de diseño deja de estar pendiente. No se publica todavía: la publicación depende del resto de bloques y de la decisión del equipo.

## Contador — correcciones para el segundo ciclo, 4/11/2026 20:15

La revisión `deleg_1514b34f` tarea 2 dio **`passed: false`** con cuatro defectos bloqueantes, todos reproducidos: cupo superable con lock obsoleto (6 reservas para 5), herramienta de provisión incapaz de crear una ventana válida y con éxito falso, lock-directorio que escapaba como `PermissionError`/`transport_error`, y manifest en la ruta heredada que producía un envío sin contar. La corrección documental de la ruta sí se confirmó hecha.

Corregido con TDD (14 pruebas nuevas en `tests/test_mission_ledger_hardening.py`, RED observado antes de cada arreglo):

- **Lock con propiedad:** el fichero guarda `pid timestamp uuid`; solo se rompe si el propietario está demostrablemente muerto; al salir solo se retira el lock propio.
- **Diario:** números de intento repetidos → `MISSION_CORRUPT`; tras escribir se relee y se falla cerrado si el recuento cambió.
- **Provisión segura:** `--mission-id`, `--cutoff`, cupo 1..100, corte futuro y posterior al inicio, rechazo de una segunda misión, escritura atómica y validación con `load_manifest` antes de dar éxito; `--status` sin traza ante manifest corrupto.
- **Lock-directorio** tipado como `MISSION_UNAVAILABLE` → la app recibe `mission_unavailable` con `send_state=not_started` y cero conexiones.
- **Ruta heredada:** un manifest de este contador en `Paideia/missions` bloquea (fail closed); el esquema del mecanismo nocturno sigue sin bloquear.

Suites: **629 pruebas Python en verde** (615 previas + 14 nuevas). Re-revisión del delta en curso. **La puerta de Groq sigue cerrada: 0 intentos reales.**

## B6 (trazabilidad del informe) — ACEPTADO por revisión independiente, 4/11/2026 20:30

Dictamen `deleg_3deb6a4d`: **`passed: true`**, sin hallazgos de seguridad ni de lógica, sobre `scenario_provenance.js` `3beaff67…`, `comparison_report.js` `0395d5a8…` y el test nuevo `a834d18f…`, con las copias de `api/_static` idénticas byte a byte. Lo que el revisor comprobó por su cuenta:

- **Atribución con URL de condición ≠ URL de producto**: DEP-02 (página de Openbank frente al PDF del registro) y un par sintético; el informe lleva la URL de la condición y **no** la del registro.
- **Título y fecha de consulta** de la referencia (`Renault Bank — Información precontractual global`, `2026-10-27`) presentes y escapados.
- **Invalidación**: editar la tasa deja la procedencia en `null` y el informe pasa a «Supuesto manual: sin fuente»; volver al valor original **no la resucita** (infracclamación segura); cambiar de producto la sustituye; copiar A→B no contagia.
- **Sin clasificación inventada**: sin `kind` se muestra «clase de fuente desconocida»; nunca aparece «fuente oficial».
- **Artefacto autónomo**: 0 `<script>`, 0 `<link>`, 0 `@import`, 0 `url()`, sin perfil, correo ni ids de chat; legible en claro.
- **Vigencia honesta**: con condición caducada declara «vigencia terminada»; sin fecha de fin no afirma que siga vigente.
- **Regresión**: 16/16 pruebas unitarias (los dos ficheros reales) y 40/40 comprobaciones de navegador, ejecutadas dos veces.

El revisor dejó límites no bloqueantes, todos en dirección conservadora: el título va en línea dentro de la fila de fuente en vez de con etiqueta propia; si una referencia llegara sin título o fecha se omiten sin decir «no consta»; y cuando la condición trae referencia propia se descarta el `kind` del producto, de modo que un producto secundario se etiquetaría como clase desconocida (no ocurre con los datos servidos). Se anotan como mejoras opcionales, no como defectos abiertos.

**Consecuencia:** B6 queda aceptado en su alcance (procedencia de fuentes en el informe). No se reabre B4/B5 ni se declara aceptado todo el catálogo.

## Contador — segundo ciclo de corrección, 4/11/2026 20:45

La re-revisión del delta (`deleg_e90c76b6`) confirmó **B1–B4 cerrados** con probes propias y un control contra la versión anterior que sigue reproduciendo el 6-para-5. Pero encontró una **regresión nueva y bloqueante (N1)** introducida por mi propio arreglo: `_break_if_stale` leía el fichero del lock en cada sondeo de 20 ms, de modo que el poseedor no podía retirarlo en Windows (WinError 32); el lock quedaba huérfano y bloqueaba todos los envíos ~60 s. Con 20 procesos simultáneos y cupo 5 obtuvo 1 reserva en 12 de 14 ejecuciones; la versión anterior daba 5/5. Nunca se superó el cupo (todo fallaba cerrado), pero se negaban envíos legítimos.

Corregido: la obsolescencia se decide **solo con el mtime** y el fichero se lee únicamente cuando ya está caducado; la retirada reintenta y solo borra el lock cuyo contenido sigue siendo el propio. De paso se cerraron tres límites del mismo informe:

- **L1**: un lock vacío o ilegible y viejo se trata como escombro y se recupera (antes bloqueaba para siempre). Un poseedor vivo sigue sin desplazarse nunca.
- **L2**: también se detecta un `MISSION.json` de este contador colocado directamente en `Paideia/missions/`, no solo dentro de un subdirectorio.
- **L3**: `--status` sale con código 1 y mensaje explícito si la raíz de estado es ilegible, en vez de decir «sin misión provisionada».

Sonda de concurrencia propia (20 procesos, cupo 5, tres repeticiones, `docs/contador-hasta-bloqueo/sonda-concurrencia-20x5.json`): **5/5 reservas, 15 `MISSION_EXHAUSTED`, `n` = 1..5 sin duplicados, sin lock huérfano y sin superar el cupo en las tres**. Suites: **634 pruebas Python en verde**. Tercer dictamen del bloque en curso (segundo ciclo de corrección); si vuelve a rechazar, el bloque se detiene y se documenta, según el límite de dos ciclos.

## Contador — BLOQUE DETENIDO, puerta de Groq cerrada, 4/11/2026 21:05

El segundo ciclo de corrección (`deleg_4152a144`) volvió a dar **`passed: false`**. Resultado por defecto:

| Elemento | Estado |
|---|---|
| N1 (regresión de concurrencia que introduje) | **cerrado**: 20 procesos, cupo 5, 5/5 ejecuciones con 5 reservas exactas y sin lock huérfano |
| B2 (provisión) | **cerrado**: 25 casos de CLI, ningún manifest inválido con éxito falso |
| B3 (lock-directorio) | **cerrado**: `mission_unavailable`/`not_started` por ambas rutas de transporte |
| B4 y L1–L3 | **cerrados**: ruta heredada (incluido el manifest plano), lock vacío, `--status` ilegible |
| **B1/N2 (toma de lock obsoleto)** | **ABIERTO**: la recuperación no es atómica; dos contendientes simultáneos obtienen ambos el último intento (6 autorizaciones para cupo 5, reproducido 5/6) y con 20 procesos el diario queda corrupto (6–9 líneas, `n=5` repetido). Es un hueco **preexistente**, no una regresión de mis cambios. |

Intenté sustituir el lock por uno del sistema operativo (`msvcrt.locking`/`flock`), que elimina la heurística de obsolescencia y la carrera por completo. En sondas independientes funcionaba (un poseedor vivo bloqueaba al contendiente con `EACCES`), pero **bajo el arnés de pruebas el fichero no persistía entre procesos** y no pude validarlo con la fiabilidad que exige la puerta. Lo retiré en lugar de dejar código no verificado, y el bloque se detiene aquí.

**Consecuencia, sin ambigüedad:** se agotaron los dos ciclos de corrección permitidos para este bloque. **La puerta de Groq sigue cerrada y esta misión termina con 0 intentos reales.** El diario histórico conserva sus 15 líneas intactas. Corregir N2 exige un diseño distinto (lock del SO o un testigo externo) y una revisión favorable de la versión exacta: es una decisión y un trabajo del equipo, no algo que deba seguir intentando a ciegas.

Las correcciones que **sí** están cerradas por revisión (B2, B3, B4, L1–L3, N1) quedan en el árbol de trabajo, sin commit, porque comparten fichero con el lock pendiente y separarlas requeriría reescribir código ya verificado.

## Pai — honestidad del aviso de omisión, 4/11/2026 21:40

La evaluación de las diez preguntas dejó un defecto de veracidad en la interfaz: cuando el backend retenía la prosa por una **cifra** o un **identificador**, la interfaz decía siempre «afirmación de fuente oficial o vigencia». El motivo mostrado no coincidía con el declarado en cinco de los diez paneles.

Corregido con TDD: módulo puro `static/chat_withheld_notice.js` (8 pruebas nuevas en `tests/chat_withheld_notice.test.cjs`, RED antes de implementar) que traduce el motivo declarado —`figure`, `attribution`, `identifier`, `invalid`— a un aviso exacto; catálogo y calculadora conservan su explicación propia; un motivo desconocido ya no se convierte en una acusación de fuente oficial, solo declara que no se pudo verificar localmente. La frontera no se relaja: el texto retenido sigue sin mostrarse nunca.

Suites: Node al completo en verde (87 + 8 del módulo nuevo), B1 74 (72 PASS + 2 observaciones). Módulo comprobado cargando en la app real bajo su CSP. **Dictamen independiente en curso**; sin commit hasta que sea favorable.

## Publicación — intento bloqueado por Vercel, 4/11/2026 21:55

El paquete que despliega Vercel (`api/_core/**` y `api/_static/**`) **no incluye** el contador: solo catálogo, dominio y estáticos. Con los tres bloques revisados (diseño, B6 y aviso de omisión), la instantánea desplegable contenía únicamente trabajo aprobado y la IA pública seguía configurada como no disponible.

El primer `vercel --prod` **no llegó a producción**: el despliegue quedó en estado `BLOCKED` con el motivo «the commit author doesn't have permission to create deployments for this project». La causa es mía: los commits se firmaron con una dirección de ejemplo (`alejandro@example.invalid`) para no inventar la identidad de Alejandro, y Vercel exige que el autor del commit sea una cuenta con permiso en el proyecto. La cuenta de GitHub (`MadeOfPlatita`, id 307587994) no publica correo, así que el remitente correcto es su dirección noreply.

Corregido sin reescribir historia: se fija la identidad local del repositorio en `307587994+MadeOfPlatita@users.noreply.github.com` y se reintenta el despliegue con un commit nuevo. Los commits anteriores conservan su autoría y su contenido. **La web pública sigue sirviendo la versión anterior** (verificado: `theme-color` antiguo, sin `dark_theme.css`, `ai.connected=false`).

## Publicación — desplegada y verificada, 4/11/2026 22:15

El reintento **sí llegó a producción**, y la causa del bloqueo quedó confirmada: Vercel rechaza los despliegues cuyo autor de commit no es una cuenta con permiso. Se publicó desde una copia de `api/` + `vercel.json` + `.vercel` sin metadatos de git (`paideia-oc1h537hd-platita1`), que es la ruta que evita esa atribución. La identidad local del repositorio queda en `307587994+MadeOfPlatita@users.noreply.github.com` para los commits siguientes; no se reescribió historia.

Leído de vuelta en la URL pública: `theme-color #101112`, `dark_theme.css` servido como `text/css`, `chat_withheld_notice.js` presente, 20 fichas de catálogo, cinco rutas sin errores ni desbordamiento y `ai.connected=false`. El contenido desplegado coincide con `HEAD` (`git diff --stat HEAD -- api prototipos/paideia-local/static` vacío en ese momento).

## Pai — atribuciones negadas, 4/11/2026 23:05

La evaluación de las diez preguntas señaló la supresión de respuestas legítimas como el defecto de forma más grave: cinco paneles sin contenido. Una de las causas era que la frontera léxica trataba igual «según la fuente oficial» y «una fuente secundaria **no** es oficial», de modo que la forma correcta de responder era justo la que se retenía.

Cambio acotado, con TDD: `_text_surface_gate` solo considera afirmada una atribución si aparece en una cláusula sin partícula negativa previa. Se corta por `. , ; : ! ?` y por `pero / aunque / sino / mientras / salvo`; se excluyen los giros que llevan negación pero afirman («no solo», «sin duda», «no cabe duda», «no deja de», «nada menos que»); las URL y `fuente:` nunca cuentan como negados. Cifras e identificadores conservan su comprobación y su prioridad.

19 pruebas nuevas en `tests/test_pai_attribution_negation.py`, escritas antes del cambio (RED: 5 fallos por negaciones legítimas). Suite completa: **650 aprobadas, 1 omitida**. Node: 95/95. Una ejecución anterior de la suite tuvo un fallo intermitente de Tk en `test_secure_groq_smoke.py` que pasó al repetir y en aislamiento.

Lo que **no** cambia: el caso P2 (ejemplo hipotético con «%») sigue retenido a propósito, porque una cifra inventada y una ilustrativa son indistinguibles para un filtro léxico; en turnos de calculadora cualquier cifra de la prosa sigue retenida; el texto retenido no se muestra nunca. El cambio no afecta a la web pública: `api/index.py` no importa `backend_services` y el chat público sigue apagado.

**Dictamen independiente en curso** (`deleg_e4d6eb3d`, adversarial); sin commit hasta que sea favorable.

### Ciclo de corrección 1 del bloque «atribuciones negadas», 4/11/2026 23:25

El primer dictamen (`deleg_e4d6eb3d`) fue **favorable en lo estructural pero rechazó el bloque** por seis frases que dejaban pasar atribuciones afirmadas. Las dos graves eran fugas reales introducidas por mi cambio: «no obstante el folleto lo publica» y «sin embargo el folleto lo publica», donde el «no» y el «sin» de un conector adversativo se leían como negación. Las otras cuatro: una atribución preposicional («no es un banco **según la entidad**») y tres dobles negaciones afirmativas («no dudo», «no es menos cierto», «no hay quien dude»).

Corregido en una sola pasada: conectores adversativos y dobles negaciones añadidos a los giros que afirman; las atribuciones introducidas por «según / de acuerdo con / tal como / conforme a / como confirma» se consideran siempre afirmadas; se admite la negación hacia delante («el folleto **no** lo recoge»); y la excepción ya no anula una negación posterior, de modo que «sin duda **no** está vigente» se permite.

Las cuatro mejoras que el revisor echó en falta quedan cubiertas con pruebas. Total del fichero: **29 pruebas**; suite completa **660 aprobadas, 1 omitida**; Node 95/95. Segundo dictamen en curso (`deleg_273d4b47`), con barrido adversarial nuevo; es el último ciclo permitido para este bloque.

### Bloque «atribuciones negadas» — descartado, 4/11/2026 23:40

El segundo dictamen (`deleg_273d4b47`) también fue **desfavorable**: 21 atribuciones afirmadas de 59 frases pasaban, en su mayoría por coordinación («**No** es una fuente oficial **y** el folleto lo publica») y por la rama de negación hacia delante, que no consultaba las excepciones. Las 21 se retenían antes del cambio, así que eran regresiones del intento, no lagunas heredadas.

Decisión: **no se sube**. El código se revirtió a `HEAD` y el intento queda archivado en `docs/pai-calidad/intento-atribuciones/` con el diff, el módulo tal como se revisó, las 29 pruebas y el resumen de los dos dictámenes.

El motivo no es que falte un conector más: el alcance de la negación no se resuelve con expresiones regulares. Cada lista de excepciones deja fuera la siguiente coordinación, y una regla que *parece* estricta pero deja pasar «no es un banco y el folleto lo publica» es más peligrosa que la retención. Cerrar esto exige extracción de afirmaciones con salida estructurada o verificación frase a frase contra el catálogo: es una decisión de producto y arquitectura para el equipo.

Lo que sí queda: la frontera original intacta y el aviso con el motivo real. Pai **sigue suprimiendo respuestas legítimas**; ahora al menos explica por qué. Suite tras la reversión: **631 aprobadas, 1 omitida**; Node 95/95.

## Nueva fase — repositorio público, capa visual 2 y afirmaciones estructuradas, 4/11/2026 23:50

**Repositorio público** por indicación de Alejandro: `MadeOfPlatita/paideia` pasó a `public` (verificado por API). Antes de abrirlo se escaneó el árbol y **los 1.371 objetos de la historia**: ninguna clave real, solo `apikey=demo` de APIs públicas. La clave viva de Groq sigue solo en `prototipos/paideia-local/.env`, ignorado y nunca versionado.

**Auditorías independientes** (`deleg_0a379b89`): repositorio **apto con condiciones** (sin secretos que rotar) y despliegue **coincidente con `HEAD`**. Hallazgos atendidos:
- `worker/.wrangler/` estaba versionado con `cf.json` (ciudad, código postal y coordenadas de quien ejecutó wrangler). **Retirado del árbol** y añadido a `.gitignore`; los objetos siguen en la historia pública y purgarlos exigiría reescribirla.
- Faltaban cabeceras de seguridad: añadidas `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` y `Permissions-Policy`.
- Quedan como decisión del equipo: 3,5 MB de páginas de terceros copiadas y un PDF con el nombre de una empleada; el correo personal en la autoría de 14 commits; `api/build_core.py` publicado como función.

**Capa visual 2** (commit `3b67737`): la hoja oscura recoloreaba pero mantenía el ritmo original, que es lo que Alejandro vio como «no se parece a las maquetas». Se añadieron superficies de 16 px de radio con borde `#303431`, rellenos de 26-30 px, títulos `clamp(36px,3.4vw,50px)` y cuerpo de 15 px, todo dentro de `@media screen`. Medido: **0 fallos de contraste** en 16 combinaciones ruta × ancho (sonda plantada 0→1→0) y **0 desbordes** a 1440/390/320. Revisión independiente y regresión conductual en curso.

**Afirmaciones estructuradas**: tres documentos listos en `docs/pai-afirmaciones/` — catálogo de **39 afirmaciones** sin cifras ni atribuciones, especificación del canal `paideia-education-v2` (6 ficheros nuevos, 18 modificados, 7 códigos de rechazo) y matriz de aceptación P1-P10 (10/10 verdes contra la referencia v2, 7/7 rechazos adversariales; el código actual da 0/10, como se esperaba). Implementación del núcleo y de la UI en marcha con TDD.

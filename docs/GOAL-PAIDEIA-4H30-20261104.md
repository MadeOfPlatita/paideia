# Paideia — misión de hasta cuatro horas y media

## Activación, horario y recuperación

- **Estado:** documento preparado; guardar este archivo no activa `/goal` ni crea un proceso persistente. La ejecución empieza solo al recibir el comando de activación.
- Raíz: `C:/Users/aleja/Downloads/App Financiera`. Corte absoluto **4/11/2026 a las 16:21:47, hora de Málaga (UTC+01:00)**, calculado desde las 11:51:47. Si se activa tarde no se amplía. Consultar el reloj al empezar, después de cada interrupción y antes de iniciar un bloque; no iniciar más trabajo al alcanzar el corte. Cerrar de forma segura lo ya iniciado e indicar la hora real.
- Hay una corrección local de Pai en curso (`deleg_59a6f84b`, tarea 0). Si sigue activa, recoger su resultado y revisar los archivos reales antes de editar las mismas zonas: no duplicar trabajadores ni sobrescribir sus cambios. Si ya ha terminado, leer su resultado y verificar el árbol antes de continuar. La investigación independiente de arquitectura es de solo lectura. La misión nocturna anterior terminó: su límite temporal no se prolonga ni se reescribe; sus hallazgos y evidencias se conservan.
- Antes de tocar código, leer `docs/REQUISITOS.md`, `docs/CIERRE-NOCHE-20261104.md`, `docs/ESTADO_Y_PLAN.md`, `docs/pai-catalogo-20261103/REVISION-POSTERIOR.md`, `docs/informe-b6/REVISION-CICLO-2.md`, `docs/pai-calidad/REVISION-FILTRO-Y-ERRORES.md` y este documento. Comprobar rama, `git status`, remoto y procesos. Confirmar el orden de bloques de abajo y el estado de archivos en curso, sin esperar una confirmación adicional del usuario. El árbol tiene cambios y archivos nuevos sin commit: nunca restaurar, resetear, limpiar ni sobrescribir trabajo preexistente.

## Producto y prioridades

Paideia es un **asesor educativo LLM de productos financieros**, no una colección de tests: el objetivo es que una persona pueda hacer preguntas, recibir explicaciones útiles con límites, usar opcionalmente su mapa con consentimiento, consultar fichas reales con fuentes y fechas, comparar sin inventar datos, experimentar con escenarios y conservar un informe. Las pruebas y revisiones son puertas de calidad, no el entregable.

Conservar perfil local, consentimientos, biblioteca, comparador, escenarios A/B y su informe HTML, ensayo ficticio de cinco pasos, glosario, accesibilidad y chat Groq. No reconstruirlos. La interfaz actual es funcional pero su diseño final no está aprobado. El usuario autorizó **maquetas visuales aisladas**, no cambiar el diseño de la app durante esta misión.

## Autorizaciones decididas por Alejandro

1. **Groq real:** hasta **100 intentos HTTP reales en total iniciados desde el entorno local**, incluidos errores, rondas de herramientas y resultados inciertos. «En local» indica desde dónde se inicia la prueba; el proveedor procesa la petición externamente. Usar solo preguntas y datos ficticios, consentimiento específico y sin perfil completo. El límite es un máximo, no una meta de consumo. Conservar además los límites existentes, incluido el diario de la configuración ordinaria; no elevarlos automáticamente para alcanzar 100.
2. **Condición previa para Groq:** un contador duradero global y una frontera de envío deben impedir el bypass entre procesos, rutas y reinicios, contar cada intento antes de enviar y respetar el corte. Actualmente `app.py` usa una ruta ordinaria que no garantiza ese control y ya hubo una llamada accidental en la misión anterior. **Mientras esa condición no esté demostrada y revisada de forma independiente, cero llamadas reales.** No usar `app.py` para pruebas mientras pueda cargar la configuración real; preferir WSGI público sin IA y fixtures sintéticos cerrados. No usar el contador viejo como si la nueva misión estuviera inicializada. No probar clave inválida con credenciales reales ni provocar gasto o cuota a propósito. Parar ante error de seguridad, cuota, coste inesperado o falta de garantía de plan gratuito.
3. **GitHub:** se autorizan commits y push **solo al repositorio privado** `MadeOfPlatita/paideia`, únicamente de cambios revisados y aprobados. Antes de cada push comprobar remoto y `visibility=private` con `gh`; inspeccionar archivos explícitos y secretos sin mostrarlos. No usar `git add -A` a ciegas, ni subir una mezcla de cambios aprobados y no aprobados si no es separable con seguridad. No cambiar la visibilidad; si no es privado, no subir. El equipo ha solicitado que siga privado.
4. **Vercel:** se autoriza actualizar la web pública **solo después de una revisión independiente favorable, pruebas reales adecuadas y revisión del contenido exacto a desplegar**. Nunca desplegar el árbol mezclado si incluye bloques rechazados, credenciales o datos no aprobados. No activar chat público ni exponer una clave por el mero hecho de autorizar despliegue: requiere además que la frontera de seguridad, privacidad, coste y calidad esté aprobada. Verificar mediante lectura de la URL pública tras el despliegue. No hay auto-deploy supuesto.
5. **Diseño:** se permiten maquetas aisladas y no publicadas de las ideas de `docs/diseno-ideas/PROPUESTAS.md`, con datos ficticios, sin modificar HTML/CSS/JS de la app real, sin tocar branding ni aplicar un rediseño. No interpretarlas como aprobación visual. Funcionalidad primero; referencias de webs reales como inspiración, no copiar marcas o activos sin permiso.

## Límites comunes

- Claves solo en `prototipos/paideia-local/.env` ignorado por Git. No leer, imprimir, modificar ni registrar ese archivo; nunca poner claves, códigos o datos personales en chat, argumentos, evidencias, capturas o Git. No pedir al usuario que pegue credenciales en chat.
- No pagos, tarjeta, servicios de pago, cuentas nuevas, datos personales, operaciones reales de inversión ni PostgreSQL. La contratación permanece ficticia. No publicar documentos originales de terceros ni usar datos sin verificar permisos; conservar transcripciones con fuente, fecha, alcance y estado.
- El mapa es opcional; no enviar perfil completo. Historial y campos del mapa requieren consentimiento separado, desactivados por defecto, y borrado visible. No afirmar que borrar localmente borra lo ya enviado.
- No presentar texto de IA, un filtro léxico, una prueba sintética ni una tasa consultada como verdad o vigencia certificada. Cálculos fuera del modelo, con supuestos explícitos; la prosa del modelo nunca valida por coincidencia de números. No sugerir contratación personalizada como hecho seguro ni garantías absolutas.
- Trabajo en bloques con alcance; máximo dos ciclos de corrección/revisión por bloque **dentro de esta misión**. Los ciclos de la misión nocturna ya cerrada se preservan; no se borran ni se presentan como aprobados. Tras dos fallos o una dependencia humana/externa, detener ese bloque y seguir solo con trabajo independiente. Para bloques de finanzas, privacidad, proveedor o cambios de frontend relevantes, exigir revisión independiente y comprobación decisiva del coordinador antes de aceptar. El paso de un test escrito por el autor no basta. Actualizar `docs/ESTADO_Y_PLAN.md`, `docs/DIARIO_DESARROLLO.md` y `docs/PLAN-PAI-PENDIENTES.md` al cerrar cada bloque, con alcance, evidencias y límites.

## Orden de trabajo y criterios

### 1. Pai útil y trazable — primero

Recoger la corrección en curso. Cerrar los fallos demostrados: el motor local debe entregar y mostrar el resultado y sus supuestos sin confundir capital, interés y saldo; en las fichas deben verse conflictos, campos desconocidos y fuentes de las condiciones; condiciones malformadas, métricas/unidades incompatibles, ausencia real y fuentes vencidas no se deben confundir. Las fuentes deben corresponder al dato, con clase y fecha. Evitar que el proveedor sin herramientas presente hechos financieros inventados como verificados; no hacer pasar una regex por comprobación semántica. Preservar respuestas conceptuales útiles mediante componentes existentes cuando sea posible.

**Aceptación:** recorrido HTTP y navegador real con proveedor sintético cerrado, incluidos casos adversarios, texto escapado, consentimiento, cálculo determinista y errores; revisión independiente. No afirmar calidad real de modelo por superar fixtures. Guardar evidencia en `docs/pai-catalogo-20261103/`.

### 2. Catálogo, comparador, ensayo e informe

Revisar fuentes, fechas, vigencia, atribución y permisos de los productos existentes; arreglar discrepancias y distinguir campos ausentes, conflictivos o caducados. Completar el comparador y el informe sin asociar tasas o fuentes a productos equivocados; preservar el escenario hipotético como tal. Corregir el ensayo cuando una ficha con condiciones aparezca incorrectamente como vacía. Incorporar productos reales solo si se verifican identidad, hechos, fecha y uso permitido: el objetivo de 20 candidatos no significa 20 ofertas vigentes. Preparar ingesta/refresco si es viable sin servicios de pago; si no, mantener última información documentada con fecha y aviso. No inventar tasas ni extrapolar cobertura del mercado.

**Aceptación:** recorrido de ficha → comparación → escenario → informe y ensayo en navegador con datos ficticios y hechos documentados; exportación HTML abierta e inspeccionada, fuentes y límites visibles; paridad de APIs local/WSGI cuando corresponda; revisión independiente. No afirmar impresión física o PDF nativo sin probarlos. Evidencia en `docs/informe-b6/` y `docs/ensayo-b5/`.

### 3. Presupuesto y pruebas de Pai

Revisar los componentes existentes `mission_budget.py`, `secure_groq_session.py`, `pai_setup.py` y `providers.py` antes de construir nuevas capas. Unir de verdad ruta de app, admisión, herramientas, transporte y contador de la nueva misión; el modo seguro debe fallar cerrado y no caer a la ruta sin contador. Preservar el uso ordinario una vez finalizada la misión y documentar los límites de confianza, sin prometer protección contra quien controle el propio proceso o un rollback total local. Probar primero offline con el transporte del código instrumentado sin conexiones, procesos/reinicios, intentos fallidos, herramientas y corte; revisión independiente. Solo entonces probar Groq real con el máximo global anterior y datos ficticios. Registrar cada intento sin secretos y no reintentar automáticamente. Probar utilidad contextual, errores y rúbrica de `docs/pai-calidad/RUBRICA-DIEZ-PREGUNTAS.md` en la medida que el presupuesto y la seguridad permitan; no provocar errores reales intencionalmente con claves inválidas.

**Aceptación:** contador real reconciliable, corte y no bypass demostrados antes de red; respuestas realmente obtenidas solo se atribuyen a Groq cuando se hayan obtenido, con límites y sin inferir calidad general de una muestra. Si falla una puerta, seguir offline y dejar explícito el bloqueo. Evidencia `docs/pai-calidad/` y una carpeta nueva de misión sin secretos.

### 4. Privacidad, robustez y accesibilidad

Conservar el consentimiento separado, borrado y aislamiento entre pestañas; verificar la funcionalidad tras los cambios del chat. Revisar estados de carga/error, teclado y foco, e investigar el desplazamiento residual de escritorio a 320 px sin rediseñar. El historial preparado para prueba no se da por habilitado con proveedor real sin validación y consentimiento. Diferenciar emulación de dispositivo real y revisión automática de lector de pantalla real.

**Aceptación:** recorrido útil en navegador local con datos ficticios y pruebas relevantes; ningún POST con IA desactivada, ninguna transmisión sin consentimiento; revisión independiente para cambios de riesgo. Evidencia en `docs/privacidad-capacidad/` y `docs/robustez-accesibilidad/`.

### 5. Maquetas aisladas y entrega

Si la funcionalidad lo permite, preparar hasta tres maquetas aisladas basadas en `docs/diseno-ideas/PROPUESTAS.md`, con comparador, Pai, ficha y móvil de muestra; etiquetas de datos ficticios, sin conexiones a servicios ni assets privativos copiados. Validarlas visualmente en navegador, guardar rutas y explicar ventajas, costes y límites; no elegir por el equipo ni aplicar estilos a la app real.

Actualizar guion de demo y entrega, comprobar que el repositorio sigue privado y que la profesora necesitará invitación o un cambio de visibilidad al entregar. Integrar y separar cambios revisados antes de cualquier commit o despliegue. No modificar la web pública si la revisión o las pruebas no aprueban el árbol exacto. Si se despliega, verificar la URL y dejar claro qué versión y qué funciones están activas.

**Aceptación:** rutas de maquetas o bloqueo documentado; estado exacto de Git/Vercel; sin credenciales en artefactos; guion de demostración fiel. Evidencia en `docs/diseno-ideas/` y `docs/entrega-noche/`.

## Cierre

Antes del corte o al terminar antes, escribir `docs/CIERRE-4H30-20261104.md`: hora real, qué puede hacer el usuario y dónde, qué se comprobó realmente, intentos reales de Groq contabilizados, qué se aceptó o bloqueó y por qué, estado de cambios y remoto, si hubo o no despliegue y sus URLs verificadas, límites y acciones del equipo. No dejar servidores de pruebas propios sin control; no parar procesos ajenos. Si una tarea sigue en curso al corte, detener de forma segura y dejar estado verificable sin prometer interrupción exacta.

Una misión `/goal` es de esta sesión y depende de presupuesto de turnos, cuota, conexión y que el ordenador/sesión permanezcan operativos: no garantiza cuatro horas y media ni sobrevive necesariamente a suspensión o cierre. No afirmar que existe un proceso independiente duradero si no se ha creado y verificado. Detener al completar lo posible o al encontrar bloqueos: no llenar tiempo con pruebas o consultas repetitivas.

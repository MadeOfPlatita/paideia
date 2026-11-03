# Paideia — objetivo nocturno ampliado de funcionamiento

**ESTADO: PREPARADO, NO ACTIVADO.** Guardar este documento no activa `/goal`, cron ni proceso. El usuario solicitó preparar un objetivo más amplio y comunicó que le queda aproximadamente un 55 % de la cuota de 5 horas; es su estimación, no una medición ni garantía de duración.

## Resultado y reloj

Construir y verificar el máximo conjunto coherente de mejoras de backend/funcionamiento descritas abajo, priorizadas por dependencia y valor para la demo. Entregar código ejecutado, pruebas, evidencia y punto de reanudación, no solo un plan. La aceptación es por hitos: no llamar terminada una funcionalidad si no se ha integrado y probado en su superficie real; tampoco declarar Paideia completa por tener fixtures verdes.

**Corte absoluto:** 2026-10-30T08:00:00+01:00 (2026-10-30T07:00:00Z), acordado para esta noche. Antes de cualquier trabajo comprobar hora real. Si ya venció, parar y pedir nueva ventana; no desplazar la fecha ni reiniciar el plazo por reanudación, reinicio o delegaciones. Terminar antes si todo el alcance factible está aceptado. Al llegar al corte cerrar procesos locales propios, registrar estado y parar; no iniciar un trabajo largo en los últimos minutos.

## Límites no negociables

- **Solo offline para Paideia:** cero llamadas a Groq u otros proveedores de IA, APIs financieras, modelos locales para fingir esas llamadas o datos personales reales. Modelos/herramientas de Hermes consumen el usage que el usuario tiene; no hay garantía de que dure hasta las 08:00.
- No abrir ventanas de credenciales, leer claves de entorno/archivos/historial/clipboard/procesos ni pedirlas por chat. No reutilizar claves ni modificar o borrar manifestos, ledgers o diarios de misiones anteriores.
- Sin pagos, tarjetas, cambios de plan, altas de cuentas, instalar o ejecutar código descargado, bases de datos, despliegues, publicación, cron, servicios permanentes o cambios de configuración de Hermes. No cambiar modelo ni límites de turns de Hermes. Sin investigación web general durante la noche.
- Presupuesto económico de producto 0 €. Perfil local voluntario y borrable; no nombres reales, DNI, bancos ni credenciales. Cualquier contexto remoto requerirá decisión separada. Contratación 100 % ficticia, sin envío comercial, pagos, firma ni identidad.
- No rediseñar. Mejorar organización, validación y mensajes funcionales sí; diseño estético al final.
- Candidatos de catálogo y datos históricos de investigación no son ofertas publicables. **No inventar precios, tasas, licencias, permisos, fechas, cobertura ni TTL real**. Escenarios positivos solo en fixtures sintéticas claramente aisladas y rotuladas; no incorporar fixtures al catálogo publicado ni declarar que un producto es comparable por pasar un test.
- Probar procesos propios en loopback, nunca matar procesos ajenos. Comprobar procesos/puertos. No inicializar Git o crear commits si no es repo. Mantener máx. dos trabajadores simultáneos, rutas exclusivas, sin delegaciones generales masivas; no sondear hijos, procesar sus entregas.

## Punto de partida comprobado

Raíz `C:/Users/aleja/Downloads/App Financiera`; app `prototipos/paideia-local/`. Leer primero `docs/ia-calidad-estructurada/ejecucion/20261030T032529Z/RESULTADOS.md`, `CONTRATO.md`, `MIGRACION-TESTS.md` y `PENDIENTE-GROQ.md`. Esa sección estructurada fue comprobada con fixture test_only: 270 Python,32 Node,19 HTTP, navegador y revisión independiente, **solo para el código/alcance de aquel momento**. No afirmar que una suite antigua es la actual sin ejecutarla.

`providers.py` produce `ChatResult`; la modalidad estructurada en `backend_services.py` exige `select_education` aislado y test_only; `structured_education.py` cierra selección IDs y motor local. Falta un adaptador auténtico entre ambos contratos. **No** fingir Groq como test_only, habilitar proveedor real ni usar `external_sent:false` si se hubiera enviado externamente. Una etiqueta test_only no impide de por sí la red. El modo de prosa legacy conserva un contraejemplo léxico y no está aprobado.

Catálogo: `catalogue_facts.py`, `backend_services.py`, `docs/funcionamiento-05/04-datos-reales/` y `spikes/005-api-cache-vs-direct/`; ese spike no es una ingesta operativa. Los informes antiguos registran cero candidatos cuantitativos listos: leer su fecha y nunca presentar ese conteo como auditoría nueva si no se repite. `CONTRATO-LOCAL.md` documenta una simulación sin operación financiera. `static/profile_model.js` mantiene estados y decimales de navegador.

## Activación y control de trabajo

1. Crear una carpeta NUEVA bajo `docs/overnight-ampliado/ejecucion/<UTC>/` con hora real de inicio, corte fijo, procesos/puertos, instrucciones, permisos y checkpoint por hito. No usar evidencias de otras ejecuciones como resultados nuevos. Cargar skills pertinentes: TDD, debugging, revisión, dogfood, catálogo si corresponde.
2. Reproducir baseline focalizada y guardar fallos anteriores. Leer el código y tests precisos antes de editar. Distribuir trabajos con archivos exclusivos si se delega. TDD en cada comportamiento: prueba roja verificable, corrección mínima, verde y regresión; conservar la salida roja y no borrar/saltar pruebas para fabricar verde.
3. Resolver dependencias y probar los DTOs conectados, no solo suites aisladas. Si los agentes reportan completed con bloqueos, tratarlos como bloqueos. Aceptar resultados solo después de inspeccionar artefactos y reproducir pruebas decisivas.
4. Priorizar los hitos A→B→C→D. Hito E es opcional si hay tiempo; no detener A o B porque C/E requieran una decisión humana. Dentro de cada hito ejecutar, corregir y entregar el corte vertical útil más pequeño; no iniciar trabajo nuevo si no hay tiempo razonable para probar y cerrar.
5. Revisar de forma independiente cualquier frontera de seguridad o datos. Máximo dos ciclos de corrección y nueva revisión por hallazgo; si sigue fallando, mantener función afectada desactivada y registrar bloqueo sin arrastrar cambios dudosos al estado final.

## A. Adaptador offline hacia selección estructurada — prioridad 1

Construir un adaptador aislado entre el DTO normal de `providers.py` y la selección cerrada `paideia-education-v1` del backend. Transporte exclusivamente inyectado y ficticio; no emplear la implementación HTTPS real ni cargar claves. Un único request controlado por turno: sin reintentos implícitos, sin herramientas adicionales y sin aumentar `max_tokens`, modelo ni presupuestos de proveedor.

Validar parseo completo (incluidas claves JSON duplicadas, UTF-8, tamaño, estructura, `finish_reason`, rechazo, truncado, ID desconocido, campos extra, prosa y claims/cifras inventados). Rechazar sin exponer texto privado, razonamiento, respuestas crudas ni secretos ficticios; nunca convertir excepción arbitraria en salida pública. No aceptar datos de cálculo, fuentes o supuestos del proveedor. `scenario` solo procede del usuario en el mismo request validado y el cálculo solo de `domain.calculate_scenario`; comprobar turnos cruzados, error del motor y cero reserva/reintentos ocultos. Si el protocolo nativo Groq no soporta un contrato concreto, usar y marcar un seam abstracto fake con la limitación; no inventar compatibilidad.

Conectar la modalidad estructurada a un proveedor específicamente ficticio a través del adaptador, manteniendo barreras `test_only`, consentimiento, sin perfil/historial y procedencia correcta. No modificar el constructor para permitir proveedor externo sin nuevo encargo. No usar una condición `test_only` como única prueba de ausencia de red: probar transporte fake explícito y ninguna llamada al transporte HTTPS. En navegador y HTTP, probar éxito, rechazo, ausencia de fallback a prosa, cálculo con supuestos explícitos y una respuesta adulterada. No hacer promesas sobre que UI verifique matemáticamente un servidor comprometido.

Crear evaluación sintética estructurada: casos con selección esperada y casos adversariales; separar validez formal de pertinencia educativa y exponer métricas reales del fixture, sin puntuaciones generadas ni ganador automático. No ejecutar el A/B/C real anterior ni mezclar sus variantes basadas en prosa con el nuevo formato. Guardar `winner:null` cuando falte evidencia real. Documentar frontera futura de admisión, ledger compartido, consentimiento y activación real, sin implementarla como ya autorizada.

## B. Catálogo: normalización, permisos y diagnóstico — prioridad 2

Comprobar el mapping real de familia/scope/acción entre `catalogue_facts.py`, loader, repositorio, UI y comparación, incluido `display` frente a `app_display`; diseñar contrato explícito, no convertir de forma permisiva dos conceptos diferentes. Un hecho comparable exige identidad, semántica, unidad/periodo/moneda compatibles, fuente/fechas, acción autorizada y política de frescura explícita. Ausencia/desconocido/conflicto/bloqueo/política vacía deben cerrar la comparación y dar motivos útiles; nunca convertir nulo en cero.

Escribir pruebas con fixtures sintéticas aisladas: permiso pendiente vs autorizado de prueba, acciones no equivalentes, datos futuros/caducados, fallo de origen, duplicados y familias heterogéneas. Un caso positivo solo puede ser sintético y decirlo en DTO/UI/test; en el catálogo real no inventar ni promocionar ofertas. Integrar por HTTP/comparador navegador con evidencias de exclusión, no solo testar una función de utilidad. Si para hacerlo se necesitan derechos o TTL real no aprobados, conservar el fail-closed e informar ese bloqueo, continuar otros hitos.

## C. Ingesta/snapshot local segura — prioridad 3

Reutilizar `spikes/005-api-cache-vs-direct/` y su documentación; inspeccionar contrato actual primero. Implementar si es viable un pipeline/repository local para candidatos **sintéticos**, con schema/versiones, origen/fecha por campo, validación íntegra previa a promoción, escritura temporal en la misma carpeta y reemplazo seguro, rechazo que conserva último bueno, reinicio y detección de corrupción; registrar si se hace o no `fsync` y qué garantiza realmente el filesystem. No inventar TTL; sin política/permiso explícitos, datos caducados no deben utilizarse. No usar red ni DB y no escribir sobre `candidatos.json`, hechos reales, ni `mission-ledger`.

Ensayar fallo de validación, temporal/reemplazo inyectado, JSON corrupto/truncado, fuente parcial, reinicio y lector; probar integración con app y DTO, no solo nuevo módulo. Si coordinación entre múltiples procesos no está resuelta, limitar expresamente a un escritor/proceso, no afirmar atomicidad distribuida ni durabilidad frente a pérdida eléctrica. No publicar snapshots reales ni activar un job automático.

## D. Perfil y contratación ficticia — prioridad 4

Primero inspeccionar funciones reales: no reinventar un flujo que ya existe. Corregir y probar solo huecos reproducidos. Perfil: cero/no_se/omitido/sin_preguntar y decimales-string siguen distintos; `localStorage` solo opt-in, borrado y revocación; no meter perfil en solicitudes de chat ni servidor sin consentimiento nuevo. Si hay conversión a otro schema, hacer mapping explícito con validación completa y no activar envío externo.

Simulación: selección de candidato identificativo, condiciones desconocidas, importe hipotético y justificante local inequívocamente educativo, sin cuenta bancaria, DNI, tarjeta, firma, pago ni envío comercial. Un caso de navegador debe comprobar flujos reales desde formulario y rastrear solicitudes; no dejar que una TAE hipotética parezca condición real del producto. Mantener diseño sin rediseño.

## E. Resistencia y entrega opcional

Si A–D están cerrados y queda tiempo, reforzar tests de errores, cola/cancelación, CSP/inputs, accesibilidad funcional y móvil, sin presentar estrés local de fixtures como capacidad de 100 chats concurrentes. No avanzar hosting/deploy/cuentas ni pagos. No hacer tareas de relleno para agotar cuota.

## Verificación y entrega

- Por cada hito: código integrado, pruebas, evidencia con paths/comandos/códigos de salida y matriz aprobado/parcial/bloqueado/no iniciado. Registrar estado actual del catálogo y sus fechas sin extrapolar.
- Ejecutar al final `python -B -m unittest discover -s tests -p 'test_*.py' -q`, `node --test tests/*.test.cjs`, sintaxis de scripts tocados y `python -B verify_http.py` con servidor propio recién iniciado si está disponible. No confundir HTTP de servidor normal con evidencia de modalidad fake; añadir recorrido integrado con servidor fixture nuevo y navegador. Si falla precondición, conservar fallo y resolver sin instalaciones.
- Revisión independiente de implementación y contratos; máximo dos ciclos de corrección. No dar por aprobado si una revisión falla o evidencia falta. No afirmar seguridad universal, calidad real de modelo, 100 chats simultáneos, ofertas publicables ni despliegue.
- Cerrar fixture/servidores propios, verificar puertos, guardar estado completo y pruebas. `RESULTADOS.md` y `RESULTADOS.json`, `ARQUITECTURA.md` y `PENDIENTE-EQUIPO.md` deben contener próximos pasos y explicar lo que necesita permiso humano. Adjuntar instrucciones de prueba local comprobadas, sin credenciales.
- Cuando venza plazo, falte usage, se cumplan hitos o haya bloqueo real, parar y entregar resultado parcial honesto. No preguntar por credenciales durante la ausencia del usuario. El objetivo se completa al cerrar todos los hitos factibles verificados o al llegar a una parada autorizada con checkpoint explícito; nunca confundir documento de bloqueo con un hito implementado.

`/goal` es objetivo de esta sesión, no un cron ni proceso independiente; la continuación puede detenerse al agotar turns/usage o si Hermes/PC se cierran o duermen. El usuario decidirá si lo activa y no se modifican configuraciones para alargarlo. Fuente oficial: https://hermes-agent.nousresearch.com/docs/user-guide/features/goals .

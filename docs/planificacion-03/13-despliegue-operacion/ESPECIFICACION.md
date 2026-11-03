# Paideia — especificación de despliegue y operación (propuesta)

**Estado:** propuesta documental; no es un despliegue ni una decisión de proveedor.  
**Base:** requisitos del proyecto y consulta de documentación oficial del 26-10-2026.  
**Presupuesto:** objetivo de 0 €, no coste garantizado. No se crean cuentas, no se elige dominio, no se activa facturación y no se guardan secretos en este documento. Las decisiones y cuentas siguen a cargo de Alejandro/José Manuel.

## 1. Dictamen y límites de alcance

- **Ruta online preferida:** SPA estática en Cloudflare Pages (usar el subdominio asignado, sin comprar dominio) + Cloudflare Worker como única puerta a `/api/chat` + catálogo público versionado servido como estático. El navegador nunca habla con PostgreSQL ni recibe claves de proveedor.
- **PostgreSQL:** local para desarrollo/pruebas. Una base gestionada pública —Neon, Supabase u otra que decida el agente de API y el equipo— es **opcional y bloqueada** hasta validar el plan Free, región, conectividad desde Worker/Actions, límites, pausa/cold start, copias, exportación, retención, requisitos de tarjeta y riesgo de cargos. No se compara ni selecciona proveedor aquí. No se guardan perfiles, prompts ni respuestas en esa base.
- Para el catálogo de la primera demo, preferir un snapshot JSON completo y revisado que se publique con la versión de la web. PostgreSQL puede ser el origen de preparación/validación; no debe ser requisito para servir biblioteca, glosario o simuladores. Así una pausa de la base no retira la parte estática.
- **IA:** el proveedor/modelo no está aprobado. El Worker solo será proxy cerrado, con ruta/modelo permitidos, validación de tamaño y esquema, límite operativo y secreto en configuración del servicio. Nunca proxy abierto ni clave en JavaScript, URL, repositorio o `localStorage`.
- **No se promete:** 100 usuarios concurrentes, disponibilidad/SLA, chat online mientras las cuentas/modelo/cuotas no estén aprobados y probados, ni actualización diaria puntual. El límite de solicitudes diarias no equivale a concurrencia. Cloudflare Workers Free documenta 100.000 solicitudes/día y 10 ms de CPU por petición.[12] Workers AI Free asigna 10.000 Neurons/día y las operaciones posteriores al límite fallan.[13] Workers Paid tiene un mínimo publicado de 5 USD/mes por cuenta, por lo que no se activa para esta propuesta de 0 €.[25]
- Cloudflare Pages Free publica 500 builds/mes y un build simultáneo; eso no compensa fallos de Actions ni convierte el cron en SLA.[22][26]

## 2. Topología propuesta

```text
Equipo (entorno local)                    Visitantes
PostgreSQL localhost                       navegador sin cuenta
  └─ migraciones + datos ficticios            ├─ Pages: SPA + catálogo estático
  └─ prepara/valida snapshot                   └─ POST /api/chat (solo si se habilita IA)
                                                  └─ Worker
GitHub repo / Actions                              ├─ valida petición/origen/límites
  ├─ CI en PR                                       └─ LLM aprobado (Secret del Worker)
  ├─ ingesta manual/programada → candidato
  └─ revisión del snapshot → producción        PostgreSQL cloud (opcional)
                                                     └─ solo Worker/job autorizado,
                                                        nunca el navegador
```

El perfil de Pai permanece en el navegador y es borrable, conforme a los requisitos. Antes de enviar un turno a un LLM externo, la UI debe explicar qué campos mínimos salen del dispositivo; no incluir nombre, DNI, credenciales ni identificadores innecesarios. Sin consentimiento/aviso y proveedor aprobado, la IA queda desactivada. Un servicio público no depende del PC doméstico: el PC solo sirve para desarrollar y operar manualmente; la demo offline es otra modalidad y no satisface por sí sola el requisito de disponibilidad online.

### Frontend y entornos

- **Primario: Cloudflare Pages.** PR/branch de prueba en preview; producción solo desde `main` tras revisión. Pages da URLs únicas de preview y aliases por rama; previews no equivalen a producción.[21] El rollback de Pages restaura una versión de producción creada correctamente; una preview no es destino de rollback.[10]
- **Alternativa online condicionada: Vercel Hobby**, solo si el titular confirma que el uso educativo de grupo y sus condiciones encajan. Su plan Hobby es gratuito pero está dirigido a proyectos personales/usuarios individuales y su guía limita a uso personal no comercial; no asumir que el grupo cumple sin confirmarlo.[23][24] No cambiar el proxy ni guardar claves en el frontend.
- **Alternativa de contingencia explícita:** demo estática reducida/offline con datos ficticios/versionados, perfil local y respuestas preescritas; sin llamada LLM, cuenta, DB ni actualización. Puede enseñarse desde una copia local preparada, tras comprobar que la SPA se abre en el navegador. No presentarla como el servicio web online ni decir que el chat seguirá disponible con el PC apagado.
- No comprar ni configurar dominio propio; primero validar el subdominio del hosting. Deshabilitar funciones/servicios que añadan coste. Revisar límites y facturación antes de cada alta.

### Base de datos local y cloud

**Local dev (recomendada al construir):** PostgreSQL escuchando solo en localhost; DB/rol exclusivos de desarrollo, datos sintéticos o catálogo autorizado; sin IP pública, no reutilizar credenciales cloud en una laptop y no incluir dumps ni `.env` en Git. Copiar `.env.example` sin valores reales; credenciales reales solo en un archivo ignorado localmente.

**Cloud pública (opcional, tras decisión del agente API):** “pública” significa que el endpoint gestionado podría ser enrutable, no que la base sea pública para el navegador. TLS requerido; acceso solo desde componentes de servidor autorizados y con secreto fuera de Git; restringir IP/origen si el proveedor lo permite; usar conexión/pooler compatible con Workers y confirmar límites de conexiones antes de elegirla. No abrir reglas a `0.0.0.0/0` como atajo. El Worker no tiene acceso de escritura general: lectura de catálogo o API de ingesta con permisos mínimos. Si no se puede restringir el acceso del proveedor a un servicio desplegado, no guardar datos privados allí.

**Caveat Free/cold start:**

- Neon Free suspende el compute tras 5 minutos inactivo.[14]
- Al reactivarlo puede añadirse cold start; Neon documenta normalmente unos cientos de milisegundos, aparte de red y otros servicios.[15]
- Neon advierte que Free es para prototipos y debe evitarse en producción si se exige disponibilidad ininterrumpida.[16]
- Supabase Free puede pausar proyectos con poca actividad durante una ventana de 7 días.[17]
- Supabase recomienda exportar los datos Free y mantener copias fuera del servicio.[18]
- Son condiciones que hay que revalidar al elegir proveedor/plan, no promesas de latencia o recuperación. Si DB se duerme/pausa, la biblioteca estática seguirá disponible; chat o consultas dependientes de DB degradan con mensaje y sin reintentos infinitos. Worker/API debe tener timeout acotado, reintento limitado e idempotente y fallback estático.

## 3. Repositorio, licencia y CI

1. Designar propietario del repo, administradores y quién aprueba publicación. Activar 2FA y limitar escritura. El repo y la licencia siguen pendientes de aprobación por el equipo.
2. Crear el repo primero **privado** mientras se revisan titularidad, datos, claves y licencia. Publicarlo tras aprobación expresa; no describirlo como open source ni añadir una licencia por suposición. GitHub remite a orientación para escoger licencia apropiada.[9]
3. Ramas: `main` protegida; trabajo mediante PR; revisión humana antes de merge y publicación. CI de PR corre tests/lint/schema validation con `contents: read`; sin secretos de producción y sin escritura al repo. Reducir `GITHUB_TOKEN` y tokens externos al permiso mínimo. No ejecutar Actions privilegiadas contra código no confiable de forks; GitHub no pasa secretos normales a runners de workflows de forks.[5][6]
4. `Actions`: workflow de PR para validaciones; workflow de catálogo en `workflow_dispatch` y, si se acepta, cron informativo. La ingesta se programa fuera del minuto `:00`, pero el cron puede retrasarse o descartarse con carga; la rutina debe detectar que falta una ejecución y permitir relanzamiento manual. Nunca anunciar “datos actualizados diariamente” basándose solo en la expresión cron.[7][26]
5. La única tarea que promueve snapshots necesita permiso de escritura acotado al repo/datos, protegido, con aprobación humana si el proveedor/plan lo permite. No dar al job permisos administrativos sobre la cuenta. Revisar y fijar dependencias/actions a versiones inmutables conforme a la guía de seguridad.[5]
6. GitHub Environments: `staging` y `production` separados. Un job no accede a secretos de un environment hasta superar sus reglas configuradas; configurar reviewers/restricciones cuando estén disponibles en el plan.[8] En staging usar datos sintéticos, DB vacía/aislada y secretos distintos. Pull requests no reciben secretos de producción.

## 4. Ingesta de catálogo y “último bueno”

**Bloqueo de dato:** no hay APIs/fuentes/licencias/coberturas aprobadas. No se ejecuta ni se programa una ingesta real hasta identificar por familia (cuenta, depósito, deuda pública, fondo, ETF) permiso, licencia, límites y significado de campos. Si no hay fuente autorizada, la demo usa una muestra etiquetada como ficticia/manual, no una actualización diaria inventada.

Procedimiento de ingesta propuesto:

1. Fetch desde una fuente permitida a `candidate/`; registrar fuente, URL, instante UTC de consulta, fecha efectiva, versión de esquema y atribución/licencia.
2. Validar respuesta completa y campos obligatorios; ids únicos, tipos/rangos/unidades, fecha y frescura por familia; no completar ausencias con IA. Rechazar cuerpo parcial, registros rotos, fuente/licencia desconocida o lote fuera de rango.
3. Ejecutar tests deterministas y diff de cambios. Fallo = no reemplazar snapshot productivo; emitir solo el código de error y mantener candidato para diagnóstico sin guardar payload sensible.
4. Publicar el candidato únicamente tras revisión/merge. El commit/tags identifican `catalog_version`, `source_checked_at`, `data_effective_at` y hash del archivo; `current` siempre apunta al último snapshot íntegro y revisado. Conservar el último bueno (commit/tag anterior) y el último workflow exitoso; no borrar datos anteriores en un job fallido.
5. Mostrar en producto la fecha de consulta, fecha efectiva, fuente y advertencia de antigüedad. Aplicar reglas de caducidad pendientes; si un campo no es apto, excluirlo de comparaciones y explicar por qué. No usar cron como evidencia de vigencia.
6. Revisar el estado de Actions y antigüedad agregada del catálogo. Umbral/owner de alerta debe definirse antes de producción; manual dispatch vuelve a intentarse tras corregir causa, sin duplicar escrituras.

Si se usa PostgreSQL cloud para ingesta, el job obtiene únicamente su secreto de `staging` o de la acción de producción aprobada, usa un rol de ingesta restringido y no una cuenta superuser. El snapshot versionado sigue siendo el respaldo/publicación reproducible.

## 5. Migraciones y privilegios PostgreSQL

- Guardar migraciones SQL numeradas, revisadas y append-only en `db/migrations/`; cada versión registra identificador, propósito y compatibilidad esperada. No editar una migración aplicada: crear la siguiente.
- Orden: crear base/roles por una persona autorizada; aplicar migraciones a DB local; validar desde copia de datos sintéticos; luego staging; respaldar/exportar según capacidad del proveedor; aprobar producción; migrar una vez con una identidad de migración y comprobar versión/schema antes de desplegar app compatible. No auto-migrar en el arranque de cada Worker/instancia.
- Separar expansión y retirada: primero cambios compatibles con versión previa, despliegue y observación; borrar/renombrar columnas solo en una migración posterior. Si una migración destructiva falla, parar y decidir restauración o migración correctiva con responsable; no ejecutar `DROP` a ciegas.
- Roles lógicos sugeridos (nombres descriptivos, **no creados**): `paideia_owner` (bootstrap/administración manual; no runtime), `paideia_migrator` (DDL solo durante despliegue aprobado), `paideia_ingest` (escrituras de catálogo solamente si DB), `paideia_reader` (SELECT al catálogo si hace falta en runtime). Revocar privilegios no requeridos; ninguna app se conecta como owner/superuser. PostgreSQL gestiona permisos mediante roles.[1] La identidad del rol determina los privilegios disponibles; configurar permisos deliberadamente.[19][20]
- Para el servicio online, preferir cero conexión a DB desde la app si sirve snapshot estático. Si se necesita lectura del catálogo, permiso SELECT solo a tablas necesarias; si la ingesta escribe, rol distinto; no aceptar SQL, tabla, connection string ni URL de proveedor arbitraria del cliente.
- Contraseñas, endpoints y tokens separados por ambiente, aleatorios, con rotación tras exposición. No insertar valores reales en migraciones, capturas, issues, logs o fixtures.

### CLI PostgreSQL documentada — referencia, no ejecutar ahora

Estos ejemplos son solo para planificar una copia/exportación y una restauración de prueba; requieren elegir DB, usuario/host y destino por el operador. No se incluyen credenciales en línea de comandos ni se ejecutan aquí. PostgreSQL documenta la forma básica de `pg_dump` y restauración de dump SQL con `psql -X`.[4]

```sh
# Exportación lógica de una base a SQL (sustituir DBNAME y ruta):
pg_dump DBNAME > DBNAME.sql

# Restauración de ese SQL en una base vacía creada previamente para la prueba:
psql -X DBNAME_RESTORE < DBNAME.sql
```

El dump de una base no equivale necesariamente a una copia completa de roles/cluster.[2] PostgreSQL advierte que `pg_dump` no suele ser la opción adecuada como único método de copias regulares de una base productiva.[4] Si se emplea un archivo de `pg_dump`, `pg_restore` lo reconstruye; al restaurar, el destino puede ejecutar código arbitrario elegido por superusuarios de origen, así que hay que inspeccionar dumps no confiables.[3] Verificar el archivo y practicar restore en staging con una copia no sensible. No usar `--clean` ni restaurar sobre producción como procedimiento normal. No se propone CLI de migrador ni de Wrangler/GitHub: herramienta y configuración no elegidas.

## 6. Secretos, proxy y privacidad operativa

- Guardar clave LLM en Secret del Worker (Cloudflare documenta secretos como texto cifrado enlazado al Worker); guardar por separado credenciales de DB si se aprueba DB cloud.[11] Usar secretos de Actions solo para el job y environment estrictamente necesario. Las instrucciones UI de GitHub están en la página oficial; no poner valores en archivos o comandos mostrados en capturas.[6]
- Tener secrets distintos para staging y prod, permisos mínimos y una persona responsable de rotación/revocación. No copiar secrets entre environments. No exponer al cliente excepto claves públicas de widget explícitamente diseñadas para ser públicas. No escribir valores ni mensajes HTTP que los incluyan en logs.
- El Worker: permitir solo `POST /api/chat`, origen de la web y modelos/rutas aprobadas; validar JSON, tamaño total, historial/tokens, timeouts, método y respuesta; cuota de uso agregada y comportamiento 429/503. Rechazar URL de LLM/DB recibida del cliente. Si la cuota se agota o falla el proveedor, deshabilitar chat temporalmente y conservar funciones no IA.
- Respetar métricas separadas: Workers Free requests/day y CPU por invocación; Workers AI Neurons/day/modelo y tasa específica. No traducir límites publicados a concurrencia; 100 solicitudes simultáneas requieren prueba controlada con permiso del proveedor y prompts sintéticos. Si no hay permiso o un criterio de aceptación acordado, no lanzar esa carga ni anunciar 100 concurrentes.
- Sin cuentas/proveedor aprobados todavía, no se crea ninguna API key ni se comparte dato real. Confirmar las condiciones de privacidad del LLM y qué contexto se envía antes de autorizar chat público.

## 7. Flujo local → staging → producción

| Fase | Entrada y checks | Promoción/resultado |
|---|---|---|
| Local | SPA + PostgreSQL local; datos sintéticos/manuales; tests de migración, simuladores, catálogo y fallback offline. Sin credenciales cloud. | PR con cambios, migraciones revisadas, fuente/fixture y tests. |
| Preview | Preview aislada de la rama; validar móvil/desktop, accesibilidad básica, fechas/avisos, consola/errores y que no se filtran secretos. Nunca usar datos/cookies de producción. | Revisión de ambos responsables; no publicar a clase aún. |
| Staging | Environment y secrets propios; DB vacía y datos sintéticos; probar ingesta de candidato, migración, endpoints, fallos, rollback de frontend y restore de DB si se adopta. | Checklist de staging firmado por ambos; registrar commit y resultados sin prompts/PII. |
| Producción | Promover el commit de `main` ya probado; URL del proveedor; revisar quotas/alerts, fuente y catálogo, política/aviso IA, coste y fallback; smoke test sintético. | Publicar enlace solo tras aprobación; vigilar el primer uso y tener un operador que pueda apagar IA. |

Un push a producción no actualiza licencias/datos por sí solo. Las cuentas, permisos, decisión de titularidad/licencia y responsables técnicos siguen bloqueando la apertura pública. Las cuotas Free y los límites pueden cambiar; validar en el dashboard justo antes de publicar.

## 8. Rollback, backup y recuperación

**Rollback de código estático:** Cloudflare Pages → proyecto → Deployments → seleccionar último deployment de producción que pasó smoke tests → confirmar rollback; la documentación dice que las previews no sirven como destino.[10] Rollback de Pages no revierte Worker, secrets, DB ni catálogo externo. Registrar el SHA que se vuelve a publicar; el Worker debe volver a su versión de código/configuración compatible por su propio mecanismo, probado antes en staging. No inferir del rollback de Pages que la DB también retrocedió.

**Catálogo:** restaurar el commit/tag del último `catalog_version` íntegro, no regenerar sobre el dato roto. Verificar fuente, fecha efectiva y hash; dejar una advertencia de antigüedad si corresponde.

**Base:** antes de producción el proveedor elegido debe documentar backup, retención, exportación, recuperación, región, coste, ventana de retención, posible pausa y proceso de restore. Acordar RPO/RTO realistas con los responsables; hoy no están definidos. Exportación lógica programada/manual en almacenamiento separado y privado si los datos lo requieren, comprobar integridad y ensayar restore en staging. No asumir que Free aporta PITR o una copia duradera. Supabase recomienda export off-site para Free; la disponibilidad de backups automáticos depende del plan, según su guía.[18] Eliminar proyecto podría hacer irrecuperables sus datos y backups del proveedor; verificar antes de cualquier borrado.[18]

**Procedimiento de incidente:** congelar ingesta y releases; mostrar modo degradado; no ampliar permisos ni actualizar plan para sortear límite; guardar timestamp, commit, versión del catálogo y error agregado sin cuerpo ni identificador de usuario; decidir entre rollback de app, último snapshot o restore de base con owner presente; smoke-test y registrar causa/cambio. Restore destructivo requiere confirmación del responsable y destino de prueba siempre que sea posible.

## 9. Monitorización mínima sin PII

- Revisar manualmente después de cada release: commit desplegado, estado de build/preview, errores 4xx/5xx agregados, latencia agregada, uso agregado de cuotas de Worker/LLM, última ingesta exitosa, `catalog_version`, `source_checked_at`, fecha efectiva y edad del dato. Umbrales (p.ej. caducidad por familia, alertas y operador) son pendientes, no se inventan en esta propuesta.
- El workflow publica estado de ejecución, commit y conteos de registros; jamás payload bruto de API, prompts, respuestas, perfil, datos financieros de usuario, connection strings, headers/cookies, API key, IP o texto de errores que puedan contenerlos. Configurar logging para redacción/retención mínima; desactivar trazas de cuerpo y analítica no revisada.
- No usar perfiles ni prompts de usuarios reales para test/load-test. Métricas solo agregadas; aviso a operador si falla ingesta o alcanza el umbral de uso, sin identificar usuarios. No añadir proveedor de observabilidad pago ni dominio de alertas por defecto.
- Validar antes de publicar cómo se comporta la app sin IA, sin DB, con cuota agotada, snapshot vencido, token inválido, respuesta lenta, 429 y error de red. No prometer disponibilidad continuada basándose en cron o una pantalla verde.

## 10. Pasos que quedan a cargo del equipo (no realizados)

1. Confirmar titularidad del producto/repositorio, quién puede publicar y quién opera incidentes; elegir licencia con orientación adecuada antes de marcarlo open source.[9]
2. Aprobar repo GitHub; añadir 2FA y los dos responsables; revisar acceso público/privado y branch protection.
3. Crear cuentas necesarias (GitHub y, tras decisión, Cloudflare). Comprobar país/identidad, tarjeta exigida, límites Free, condiciones de facturación y cancelación dentro del panel oficial. Este runbook no afirma que el alta sea sin tarjeta.
4. Configurar Pages preview/producción bajo el subdominio asignado; no configurar ni comprar dominio. Mantener Workers/IA en Free y no activar Workers Paid (5 USD/mes mínimo publicado).[25]
5. Aprobar proveedor/modelo LLM y tratamiento de datos; confirmar cuota gratis, facturación, términos, español, longitud, tasa, concurrencia y fallback. Solo entonces crear secreto de staging y probar; producción separado.
6. Esperar recomendación del agente API antes de elegir DB cloud. Si no existe plan Free con condiciones y copias aceptables, quedarse con PostgreSQL local para desarrollo y snapshots estáticos; el DB cloud seguirá como feature no lanzada.
7. Seleccionar fuente de datos/licencias por familia y caducidad, implementar proceso con último bueno, y definir responsable/alarma para cron retrasado.
8. Acordar y ejecutar (por el equipo en staging, con autorización) prueba de concurrencia/errores y ensayo de rollback/restore; documentar resultados reales antes de cualquier declaración de capacidad.
9. Aprobar aviso de privacidad, texto educativo/no asesoramiento, edad/uso y contingencia de IA con quien corresponda. No se ha realizado revisión legal.
10. Publicar el enlace de producción solo al completar `checklist.json`. Si algún bloqueo sigue abierto, mostrar demo reducida como alternativa explícita, no como servicio online ya resuelto.

## Sources

[1] https://www.postgresql.org/docs/current/user-manag.html
[2] https://www.postgresql.org/docs/current/app-pgdump.html
[3] https://www.postgresql.org/docs/current/app-pgrestore.html
[4] https://www.postgresql.org/docs/current/backup-dump.html
[5] https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
[6] https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
[7] https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[8] https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
[9] https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
[10] https://developers.cloudflare.com/pages/configuration/rollbacks
[11] https://developers.cloudflare.com/workers/configuration/secrets
[12] https://developers.cloudflare.com/workers/platform/limits
[13] https://developers.cloudflare.com/workers-ai/platform/pricing
[14] https://neon.tech/docs/guides/scale-to-zero-guide
[15] https://neon.tech/docs/connect/connection-latency
[16] https://neon.tech/docs/get-started-with-neon/production-checklist
[17] https://supabase.com/docs/guides/platform/free-project-pausing
[18] https://supabase.com/docs/guides/platform/backups
[19] https://www.postgresql.org/docs/current/database-roles.html
[20] https://www.postgresql.org/docs/current/ddl-priv.html
[21] https://developers.cloudflare.com/pages/configuration/preview-deployments
[22] https://developers.cloudflare.com/pages/platform/limits
[23] https://vercel.com/docs/plans/hobby
[24] https://vercel.com/docs/limits/fair-use-guidelines
[25] https://developers.cloudflare.com/workers/platform/pricing
[26] https://docs.github.com/en/actions/how-tos/troubleshoot-workflows

# Documentación de Paideia

Índice de lo que se conserva en `docs/`. La regla es simple: aquí solo queda lo
que la aplicación lee, lo que las pruebas necesitan o lo que hace falta para
entender y desplegar el producto. Los cuadernos de trabajo y las bitácoras de
misiones anteriores se retiraron del repositorio; siguen en el historial de git
si alguien los necesita.

## Para usar la app

| Carpeta | Qué contiene | Por qué se queda |
| --- | --- | --- |
| `producto/` | Requisitos, estado, idea y límites vigentes (`CUPO-Y-LIMITES.md`) | Explica **qué promete** la app y qué no |
| `operacion/` | Despliegue en Render, auditorías recientes y seguridad | Pasos para publicarla y evidencia de las revisiones |
| `DIARIO-DESARROLLO.md` | Bitácora: encargos, herramientas, APIs, cambios, pruebas y límites | Es el diario de desarrollo que pide la entrega |
| `HERRAMIENTAS.md` | Lista corta de herramientas, modelos, servicios y fuentes | Consulta rápida sin leer toda la bitácora |

Empieza por el [`README.md`](../README.md) de la raíz y sigue por
`producto/REQUISITOS.md`.

## Datos que la aplicación lee en ejecución

| Carpeta | Qué contiene | Quién la usa |
| --- | --- | --- |
| `validacion-04/05-catalogo/` | `candidatos.json` y `evidencia/sources-ledger.json` | El servidor, al construir el catálogo y sus fuentes |
| `validacion-04/03-benchmark/` | `dataset.json` | El banco de pruebas de calidad de contexto |
| `validacion-04/04-contexto/fixtures/` | Perfiles sintéticos completos | Fixture de las pruebas de contexto |
| `catalogo/` | Transcripción de condiciones con URL y fecha | Script de fusión del catálogo (`app/scripts/merge_conditions.py`) |

Estos ficheros son **dato de producción**, no documentación: si se mueven, cambian
las rutas de `app/app.py` y `app/conditions_service.py`. La copia curada que ve
el usuario está en `app/data/condiciones.json`.

## Material de apoyo y pruebas

| Carpeta | Qué contiene | Por qué se queda |
| --- | --- | --- |
| `pai-afirmaciones/` | Catálogo cerrado de afirmaciones y su especificación | Origen literal del canal de afirmaciones (`app/claims_catalog.py`) |
| `planificacion-03/` | Esquema del perfil de conversación | Fixture de las pruebas del perfil |
| `ia-real-siguiente/` | Manifiestos de misión usados por el contador | Fixture de las pruebas de misión |
| `mision-nocturna-20261104/` | Manifiesto de la misión nocturna | Lo lee `app/pai_setup.py` para identificar la misión |

## Lo que se retiró

- Bitácoras de misiones anteriores, informes de calidad y evidencias de sesiones
  de usuario: eran registro de trabajo, no estado del producto.
- Investigación de APIs y notas de proveedores que no usa la app.
- Intentos descartados (Cloudflare Workers, spikes, pruebas antiguas) y capturas
  de auditoría.

Todo ello permanece en el historial de git. Si necesitas una pieza concreta,
búscala con `git log --diff-filter=D -- <ruta>`.

## Convenciones

- Los documentos van en español, con la fecha en el nombre cuando son evidencia
  (`AUDITORIA-SONDAS-20261105.md`).
- Lo que describe el producto debe poder comprobarse contra el código o contra
  una ejecución; si no, se marca como límite o hipótesis.
- Nada de claves, tokens ni datos personales: solo nombres de variables.

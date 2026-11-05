# Índice de documentación

Qué mirar primero y qué es histórico. Las carpetas con fecha son archivos de una
misión concreta: se conservan como evidencia, no como estado vigente.

## Vigente

| Documento | Qué contiene |
| --- | --- |
| `README.md` (raíz) | Qué es Paideia, enlaces, cómo ejecutarla y límites |
| `DESPLIEGUE-RENDER.md` | Cómo está desplegada la demo, variables y comprobaciones |
| `AUDITORIA-NOCHE-20261105.md` | Lista de defectos abiertos y su prioridad |
| `CIERRE-PAIDEIA-HASTA-BLOQUEO.md` | Cierre de la misión anterior y bloqueos reales |
| `INFORME-NOCHE-20261105.md` | Qué se cambió esta noche, con evidencia y límites |
| `CUPO-Y-LIMITES.md` | Qué protege el contador de llamadas y qué no |

## Producto

| Documento | Qué contiene |
| --- | --- |
| `PAIDEIA-CUESTIONARIO-REVISION.md` | Por qué el perfil pasa de 12 a 7 preguntas |
| `catalogo/TRANSCRIPCION-2026-11-05.md` | Qué se transcribió de cada producto y qué falta |
| `catalogo/transcripcion-2026-11-05.json` | Condiciones con URL, título y fecha |
| `pai-afirmaciones/CATALOGO.md` | Afirmaciones cerradas que Pai puede componer |
| `pai-afirmaciones/ESPECIFICACION.md` | Contrato técnico del canal estructurado |
| `seguridad/AUDITORIA-REPO-PUBLICO.md` | Secretos, rutas y datos retirados del índice |
| `seguridad/AUDITORIA-DESPLIEGUE.md` | Cabeceras y diferencias entre despliegues |

## Archivo por misión

Cada carpeta guarda lo que se hizo un día concreto, con sus capturas y JSON:

- `catalogo-condiciones-20261103/`, `catalogo-hasta-bloqueo/` — catálogo.
- `diseno-hasta-bloqueo/`, `diseno-ideas/` — dirección visual y maquetas.
- `contador-hasta-bloqueo/` — contador de misión (N2 sigue abierto).
- `pai-calidad/` — intentos de Pai, incluido el de atribuciones rechazado.
- `mision-4h30/`, `mision-nocturna-20261104/`, `overnight-ampliado/`,
  `noche-funcional/` — misiones nocturnas anteriores.
- `investigacion-apis-02/`, `planificacion-03/` — investigación y planificación.
- `correcciones-qa-*`, `qa-usuarios-*`, `demo-usuario-*` — pruebas de usuario.
- `GOAL-*.md` — objetivos de misiones pasadas; el vigente se gestiona en la app.

## Reglas de esta carpeta

- Un documento nuevo entra en «Vigente» o en la carpeta de su misión, nunca en
  las dos.
- Las capturas y volcados pesados no se versionan (`*.body`, `*.raw` en
  `.gitignore`); el informe que los cita, sí.
- Si un documento deja de ser cierto, se corrige o se mueve al archivo; no se
  deja contradiciendo al README.

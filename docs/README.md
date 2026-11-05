# Documentación de Paideia

Qué mirar primero, dónde está cada cosa y qué es histórico. Las carpetas con
fecha son evidencia de una misión concreta: se conservan, no son estado vigente.

## Vigente

| Documento | Qué contiene |
| --- | --- |
| `../README.md` | Qué es Paideia, enlaces, cómo ejecutarla y límites |
| `operacion/DESPLIEGUE-RENDER.md` | Cómo está desplegada la demo, variables y comprobaciones |
| `operacion/AUDITORIA-NOCHE-20261105.md` | Defectos detectados y cuáles quedaron corregidos |
| `producto/CUPO-Y-LIMITES.md` | Qué protege el contador de llamadas y qué no |
| `producto/ESTADO_Y_PLAN.md` | En qué punto está el producto y qué falta |
| `producto/REQUISITOS.md` | Requisitos del trabajo |
| `producto/PAIDEIA-CUESTIONARIO-REVISION.md` | Por qué el perfil pregunta solo cuatro cosas |

## Producto y datos

| Documento | Qué contiene |
| --- | --- |
| `catalogo/TRANSCRIPCION-2026-11-05.md` | Qué se transcribió de cada producto y qué falta |
| `catalogo/transcripcion-2026-11-05.json` | Condiciones con URL, título y fecha |
| `pai-afirmaciones/CATALOGO.md` | Afirmaciones cerradas que Pai puede componer |
| `pai-afirmaciones/ESPECIFICACION.md` | Contrato técnico del canal estructurado |
| `planificacion-03/05-perfil-conversacion/perfil.schema.json` | Esquema v2 del perfil |
| `validacion-04/05-catalogo/candidatos.json` | Instantánea del catálogo que lee la app |
| `operacion/seguridad/AUDITORIA-REPO-PUBLICO.md` | Secretos, rutas y datos retirados del índice |
| `operacion/seguridad/AUDITORIA-DESPLIEGUE.md` | Cabeceras y diferencias entre despliegues |

## Misiones y evidencia

Todo lo que cuenta *cómo* se llegó hasta aquí está en `historico/`, agrupado por
misión y con sus capturas y volcados:

- `historico/mision-4h30/`, `historico/noche-funcional/`, `historico/overnight-ampliado/`
- `historico/catalogo-condiciones-20261103/`, `historico/catalogo-hasta-bloqueo/`
- `historico/diseno-ideas/`, `historico/diseno-hasta-bloqueo/` — dirección visual
- `historico/contador-hasta-bloqueo/` — contador de misión (N2 sigue abierto)
- `historico/pai-calidad/` — intentos de Pai, incluido el rechazado
- `historico/GOAL-*.md`, `historico/CIERRE-*.md`, `historico/INFORME-*.md`

Los manifiestos que el código necesita (`mision-nocturna-20261104/`,
`ia-real-siguiente/`) se quedan en la raíz de `docs/` a propósito: moverlos
rompería las pruebas.

## Qué no se versiona

- Claves: viven en `.env` (ignorado) o en el panel del proveedor.
- Capturas y volcados pesados: solo el informe que los cita.
- Intentos descartados: `archivo/` (Cloudflare, spikes, pruebas antiguas).

## Reglas

- Un documento nuevo entra en la carpeta que le toca, sin duplicarse.
- Si un documento deja de ser cierto, se corrige o se mueve a `historico/`.
- Nada de nombres con fechas en la raíz del repositorio.

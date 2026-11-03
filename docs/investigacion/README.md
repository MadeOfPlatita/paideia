# Investigación de Paideia

## Lectura recomendada

Empezar por [00-SINTESIS.md](00-SINTESIS.md): conclusiones, límites, contraste propio y propuestas aún no aprobadas. No hay aplicación construida ni desplegada en esta fase.

## Estado de la investigación

Se lanzaron diez subagentes en paralelo y un undécimo de recuperación para fondos/ETF. Los diez temas tienen informe y JSON de fuentes comprobados. La investigación está completada; sus propuestas técnicas no se han implementado.

| Tema | Informe | Estado |
|---|---|---|
| Cuentas y depósitos | [01-cuentas-depositos.md](01-cuentas-depositos.md) | Recibido |
| Deuda pública | [02-deuda-publica.md](02-deuda-publica.md) | Recibido |
| Fondos y ETF | [03-fondos-etf.md](03-fondos-etf.md) | Recibido |
| IA gratuita | [04-llm-gratuita.md](04-llm-gratuita.md) | Recibido |
| Alojamiento y arquitectura | [05-alojamiento-arquitectura.md](05-alojamiento-arquitectura.md) | Recibido |
| MCP financiero | [06-mcp-financiero.md](06-mcp-financiero.md) | Recibido |
| Repositorios similares | [07-repos-similares.md](07-repos-similares.md) | Recibido |
| UX y recursos | [08-ux-recursos.md](08-ux-recursos.md) | Recibido |
| Rigor financiero | [09-rigor-financiero.md](09-rigor-financiero.md) | Recibido |
| Seguridad y calidad | [10-seguridad-calidad.md](10-seguridad-calidad.md) | Recibido |

Cada informe recibido tiene su JSON `NN-fuentes.json`. Las referencias numeradas pertenecen exclusivamente al informe correspondiente; no deben mezclarse entre documentos.

## Trazabilidad

- `FUENTES_AGREGADAS.json`: deduplicación por URL literal, conservando procedencia y observaciones de cada informe. Diez informes, 290 registros, 284 URLs únicas. No son 284 fuentes independientemente corroboradas.
- `evidencia-parental/COMPROBACIONES.json`: 19 solicitudes HTTP de contraste del coordinador y sus textos leídos.
- `ledger-sintesis.json`: referencias y extractos exactos para la síntesis, verificados mediante el script de citas.

Los informes son investigación, no pruebas de funcionamiento de repositorios o garantías legales. Las recomendaciones no aprobadas no sustituyen los requisitos acordados en `../REQUISITOS.md`.

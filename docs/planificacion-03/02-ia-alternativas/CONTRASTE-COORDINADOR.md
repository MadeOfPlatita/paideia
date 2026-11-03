# Contraste directo del coordinador — alternativas de IA

## Corrección importante de la matriz original

Al abrir directamente las URLs oficiales con solicitudes HTTP, las dos páginas Mistral citadas en la matriz redirigieron a contenido distinto del extracto usado por el subagente. Se conserva la URL solicitada y la URL final, sin atribuir el cambio a una fecha que no se ha comprobado.

La URL de niveles de uso redirige a `admin/billing-usage/usage-limits`. Su texto actual afirma que Free permite crear API keys y usar el consumo mensual incluido dentro de los límites del panel.[1] No respalda la afirmación categórica de que ese Free sea exclusivamente evaluación y prohíba una demo pública. Esto NO demuestra permiso de producción pública: los términos del servicio, límites de la cuenta, modelos elegibles y tratamiento de datos siguen sin validar.

La URL de controles de privacidad redirige a un artículo oficial sobre opt-out. Ese artículo describe una opción específica de Studio/API para impedir que llamadas y datos relacionados se usen para mejorar los servicios; los controles de Vibe y API son separados.[2] Por tanto, no se debe afirmar sin revisar configuración y contrato que todo uso de la API esté excluido de entrenamiento por defecto.

La documentación de limitaciones sí afirma que la API se sirve desde centros de datos de la UE por defecto.[4] No equivale a una garantía exclusiva sobre todos los tratamientos, retención, soporte o subencargados.

## SambaNova

El contraste directo confirma que el nivel Free se aplica sin método de pago asociado y que la tabla Free para GPT-OSS 120B indica 20 RPM, 20 RPD y 200.000 TPD.[3] Eso lo limita como proveedor único para la clase; no demuestra por sí solo una prohibición de prototipos públicos. No se han creado cuentas ni probado modelos.

## Decisión provisional corregida

- Mistral debe permanecer como candidato pendiente de prueba y revisión contractual, no descartarse basándose en la etiqueta antigua de Experiment.
- No se ha aprobado ni demostrado su cuota suficiente para cien usuarios.
- No enviar perfiles automáticamente ni crear claves/cuentas como parte de esta investigación.
- La matriz original debe leerse con esta corrección. Las conclusiones sobre otros proveedores no se extienden a Mistral por analogía.

## Evidencia

Textos completos normalizados y metadatos: `../00-evidencia-integracion/`. El registro de citas de este contraste es `../00-ledger-integracion.json`. Esta revisión es documental; no acredita integración, rendimiento o cumplimiento jurídico.

## Sources

[1] https://docs.mistral.ai/admin/user-management-finops/tier
[2] https://docs.mistral.ai/admin/monitor-comply/privacy-data-controls
[3] https://docs.sambanova.ai/docs/en/models/rate-limits
[4] https://docs.mistral.ai/resources/known-limitations

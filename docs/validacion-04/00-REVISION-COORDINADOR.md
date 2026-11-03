# Ronda 04 — revisión del coordinador y entrada al goal

## Estado

Cinco entregas recibidas y leídas. Se inspeccionó el código propio antes de ejecutar pruebas; los resultados locales se conservaron en `00-VERIFICACION-COORDINADOR.json`. No hay llamada LLM, cuenta creada, PostgreSQL, aplicación integrada ni despliegue por esta revisión. El `/goal` está preparado en `../GOAL-NOCTURNO.md`, no activado ni programado.

## Pruebas reproducidas

| Entrega | Ejecución del coordinador | Resultado y alcance |
|---|---|---|
| Arnés A/B/C | `python -B -m unittest -v test_benchmark` | 7 tests OK; preparación local, no calidad de IA. |
| Dataset | `python -B pai_context_benchmark.py validate` | 6 casos sintéticos válidos, cero llamadas/resultados. |
| Resumen de evaluación | `python -B pai_context_benchmark.py summary` | Cero llamadas/resultados; ganador null. |
| Requests existentes | Recuento de archivos y manifiesto | 18, seis casos por tres variantes. |
| Proyección | `python -B -m unittest -v` en 04-contexto | 21 tests OK; selección/consentimiento, estados, exactitud decimal y schemas locales. |
| Catálogo | Recuento y checksum propio | 20 IDs únicos, cuatro por familia; 14 identidades marcadas verified y seis proposed; 12 ISIN únicos aplicables, todos pasan formato y checksum. |

El recuento de estados no es una corroboración independiente de las catorce identidades. Las seis propuestas dependen de snippets; ningún candidato está marcado listo para publicación. No confundir permiso desconocido con prohibición jurídica universal, ni identidad con oferta actual disponible.

## Proveedores: contraste y cautelas

### Google

El coordinador recuperó directamente los términos y corroboró: «You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom.» El mismo texto define Gemini API Paid mediante proyecto Cloud asociado a facturación activa.[1]

Esto separa la evaluación interna del despliegue a usuarios españoles. No usar Gemini Free como backend público aprobado bajo el presupuesto/condiciones actuales; tampoco afirmar que todo uso gratuito en España está prohibido. No se activó facturación y no hay prueba de cuenta/modelo. Los modelos y cuotas del informe del agente siguen siendo documentación, no disponibilidad observada en una cuenta.

### Groq

El acuerdo permite expresamente integrar las APIs en Customer Applications y ponerlas a disposición de End Users. Por tanto, la frase introductoria «not for consumer use» no demuestra por sí sola una prohibición general de aplicaciones con usuarios finales; debe leerse con esas definiciones y obligaciones.[2]

Se revisó además la AUP que el agente había dejado pendiente. Prohíbe decisiones automatizadas con impacto material perjudicial sobre derechos sin supervisión humana en dominios de alto riesgo, incluida finanzas; exige respetar límites y prohíbe eludirlos mediante varias cuentas u organizaciones.[3]

Estas cláusulas no equivalen a un aval jurídico de Paideia ni autorizan asesoramiento profesional. El disclaimer de servicios indica que no debe usarse el modelo para consejo financiero/profesional.[2] Conservar educación, cálculos deterministas y fuentes; revisar la función concreta antes de publicar. No elevar por defecto toda incertidumbre a «es obligatorio obtener permiso escrito del proveedor»: el informe delegado conserva esa recomendación como cautela, no como requisito textual universal.

**Primer candidato técnico para un smoke interno posterior:** Groq `openai/gpt-oss-20b`, con `openai/gpt-oss-120b` como comparador según el informe del frente 02. Siguen pendientes acceso gratuito real, cuotas de cuenta, condiciones aplicables, español y tools; no hay proveedor operativo ni ganador. Mantener nombres canónicos del manifest de Pai, no copiar aliases distintos del informe Groq.

## Incompatibilidad que el goal debe resolver antes de integración

El arnés A/B/C usa un perfil de benchmark propio (campos y números enteros/null); el proyector de 04 consume el perfil local 05 y produce un DTO con estados y cadenas decimales. Sus tests aislados NO demuestran que se conecten. Implementar mapping explícito o un adaptador de requests que preserve semántica, cifras y consentimiento; añadir tests conjuntos antes de usarlo en backend o atribuir minimización al flujo completo. La fixture de perfil completo del proyector no es una habilitación de esa ruta para perfiles reales.

## Catálogo y prototipo

Los veinte son candidatos ampliables, no veinte ofertas listas para comparar o publicar. Hay conflictos MyInvestor y Openbank conservados. Para el prototipo, separar candidatos/fuentes y campos pendientes de los productos publicables/comparables. Una demostración sintética claramente marcada sirve para probar UI/cálculo, pero no cumple el requisito de catálogo real y no debe ocupar su lugar silenciosamente. Si permisos o condiciones bloquean todo el catálogo operativo, comunicar ese bloqueo y continuar solo las partes independientes.

## Disposición del goal

- La condición de recibir y revisar el lote se cumple para preparación del encargo.
- El texto incorpora los resultados reales y el mapping pendiente.
- No activa `/goal`, no crea un trabajo durable y no empieza un proceso nocturno por sí solo.
- Siguiente ejecución: prototipo local y tests; IA externa solo después de acceso/autorización seguros y límites pequeños. Sin pagos, instalaciones, servicios cloud ni datos personales.

## Sources

[1] https://ai.google.dev/gemini-api/terms
[2] https://console.groq.com/docs/legal/services-agreement
[3] https://console.groq.com/docs/legal/ai-policy

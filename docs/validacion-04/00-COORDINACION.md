# Paideia — validación operativa, ronda 04

## Encargo vigente

El grupo pide priorizar Google/Gemini y Groq como candidatos gratuitos y lanzar subagentes para desbloquear lo pendiente. La preferencia de cerrar respuestas con siguiente paso y acción del equipo se guardó en memoria de usuario; las afirmaciones cambiantes sobre planes se comprueban en fuentes, no se fijan como hechos permanentes en memoria.

Entrega: martes 3 de noviembre de 2026. Presupuesto: 0 EUR. Primer catálogo: 20 productos reales, cuatro por familia, ampliable. IA real con contexto cuya calidad debe compararse antes de decidir resumen frente a perfil completo. Cupo/cola aceptados. Perfil local y tratamiento externo son fronteras distintas.

## Lote despachado

ID: `deleg_2d7b1900`. Cinco entregas recibidas y revisadas. Siete tests del arnés y veintiuno de proyección reejecutados, seis casos/dieciocho requests y catálogo recontados. Leer `00-REVISION-COORDINADOR.md` y `00-VERIFICACION-COORDINADOR.json`. Falta mapping conjunto y ejecución LLM real. Goal preparado en `../GOAL-NOCTURNO.md`, no activado.

| Frente | Directorio exclusivo | Entrega y verificación necesaria |
|---|---|---|
| Google/Gemini | `01-google/` | Fuentes oficiales actuales; free/modelos/tools, EEE y tratamiento de datos; no confundir existencia de cuota con permiso de publicación. |
| GroqCloud | `02-groq/` | Modelos/tools, cuotas y condiciones actuales; ruta de acceso y smoke gratuito acotado. |
| Comparación de contexto | `03-benchmark/` | Arnés stdlib y seis casos sintéticos; ejecución offline y tests reales, sin respuestas de IA inventadas. |
| Proyección remota | `04-contexto/` | DTO/schema y función pura; consentimiento, selección, cifras exactas y desconocidos; tests locales. |
| Catálogo inicial ampliable | `05-catalogo/` | Candidatos reales 4 por familia, identidad y fuentes; contar verificados/propuestos/pendientes; campos y derechos separados. |

## Restricciones y coordinación

- No crear cuentas, claves, pagos, facturación, DB, instalaciones ni despliegues por este encargo.
- No enviar perfiles reales ni ejecutar llamadas autenticadas. El arnés prepara una prueba futura; offline no mide calidad LLM.
- Cada agente escribe solo en su directorio, incluidos ledger y evidencia. Nunca resetear citas compartidas.
- Proveedores: máximo ocho páginas oficiales por frente y dos intentos por fallo. Catálogo: una consulta pública adicional por candidato y dos intentos por fuente fallida; guardar lotes.
- Los agentes de benchmark y proyección documentan formatos/supuestos y no esperan al otro. El coordinador debe probar el mapping antes de afirmar interoperabilidad.
- Conservar los contrastes anteriores; resolver discrepancias con texto primario actual y URL solicitada/resuelta. No repetir investigación general de APIs.

## Secuencia de aceptación

1. Recibir y leer entregables, verificar procedencia y separar acceso gratuito de aptitud para el caso de uso.
2. Inspeccionar y reejecutar código local propio; validar dataset/catálogos/conteos y enlace entre proyección y arnés.
3. Elegir un primer candidato que supere las condiciones documentales. Si requiere cuenta/clave, explicar al equipo cómo configurarla por una vía segura, sin pegar secretos en chat ni activar pago.
4. Solo con acceso y autorización adecuados, ejecutar smoke sintético y comparación real acotada; conservar respuestas/consumo/errores reales y evaluar con el equipo. No seleccionar ganador desde pruebas offline.
5. Integrar después con aplicación/DB/hosting autorizados. Estas tareas aún no están ejecutadas.

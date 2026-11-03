# Paideia — verificación y entrega del prototipo local

## Resultado

Prototipo local navegable con frontend HTML/CSS/JavaScript, backend Python de biblioteca estándar y datos de investigación en snapshot de solo lectura. URL verificada: **http://127.0.0.1:8765/**. No se ha desplegado en Internet. El servidor se limita a 127.0.0.1.

Se conservaron los archivos existentes, se inspeccionaron y ejercitaron, se corrigieron defectos y se reinició el proceso local para servir el código actualizado. El proyecto no es un repositorio Git; no se afirma commit ni diff de Git.

## Funciones ejercitadas

- Perfil de seis preguntas, una por vez, resumen y edición; respuestas opcionales y estado local.
- Biblioteca con veinte candidatos de investigación y filtros. Identidad y condiciones pendientes diferenciadas; no se exponen tasas/NAV como ofertas verificadas.
- Selección de dos a cuatro candidatos y comparación de metadatos sin ranking ni falsa rentabilidad.
- Interés simple/compuesto con aportaciones al final de mes, inflación, gráfica SVG y tabla. Se comprobó un escenario negativo con pérdida visible.
- Ensayo de cinco pasos con candidato real solo como referencia identificativa, importe ficticio y justificante HTML inequívocamente no contractual; sin operación ni envío comercial.
- Vista previa de campos del perfil calculada en navegador, sin envío del objeto a la API. Persistencia solo por opt-in, con guardado y borrado confirmado probados usando cifras sintéticas.
- Glosario y privacidad. Foco visible mediante teclado comprobado de forma puntual, no auditoría completa de accesibilidad.
- Formulario de prueba de chat con consentimiento y un único POST local de `message`; HTTP 503 se presenta como IA no conectada. Ninguna respuesta prefabricada se hace pasar por IA.
- Estado de servicio sin red y recuperación al restablecerla. Los recursos observados permanecieron en el origen local.

## Pruebas y evidencia

| Comprobación | Resultado |
|---|---|
| `python -B -m unittest discover -s tests -v` | 39 tests OK: dominio, backend HTTP y adaptador de contexto. |
| `node --check static/app.js` | Correcto; repetido tras montar el formulario. |
| `python -B verify_http.py --base-url http://127.0.0.1:8765 --out evidence/http-final.json` | 17/17 comprobaciones HTTP correctas. |
| Navegación en navegador | Ocho rutas en escritorio y ocho en móvil de 390 px; dieciséis pares ruta/tamaño comprobados. |
| Chat en navegador | Sin consentimiento: cero requests. Con confirmación: un POST local y mensaje de IA no conectada, sin adjuntar perfil. |
| Red observada | Únicamente `http://127.0.0.1:8765`; sin errores JavaScript observados en la sesión instrumentada. |

Los conteos provienen de `evidence/tests-final.json`, `http-final.json`, `browser-final.json` y `routes-final.jsonl`. Las exploraciones preliminares incluyen intentos incompletos y mediciones antes de completar requests: se conservan, pero no se agregan como aceptación final.

## Defectos reproducidos y corregidos

1. **Convención del interés simple.** La fórmula era simple, pero sus metadatos declaraban interés compuesto efectivo. Se añadió una regresión que falló y se corrigieron los metadatos según método; la suite final pasa. Archivo `rate-convention-red.json`.
2. **Desbordamiento en móvil.** Una URL de fuente en comparación generaba 477 px de contenido con viewport de 390. La regla de partición solo se aplicaba a tarjetas de biblioteca. Se amplió a todas las fuentes y se verificó 390/390. Archivos `mobile-overflow-red.json` y `mobile-overflow-green.json`. La prueba final usa `clientWidth`, no `innerWidth`, que podía ocultar el fallo al expandirse.
3. **Chat sin formulario visible.** Se construía el form pero nunca se añadía al panel. Se reprodujo su ausencia en el DOM, se montó y se comprobaron consentimiento, único intento y error honesto. Archivo `chat-browser-green.json`.

Capturas reales: `00-inicio.png`, `01-perfil.png`, `02-comparacion.png`, `03-escenarios.png`, `04-ensayo.png`, `05-movil.png` y `06-comparador-movil.png`, dentro de `evidence/`. No son bocetos sintetizados.

## Integración del contexto

`context_adapter.py` carga el proyector 04 y el materializador del arnés 03 desde sus fuentes originales. Los tests prueban selección, consentimiento, conservación decimal, bases A/B/C iguales y ausencia de red. La ruta HTTP de preview solo recibe un ID de fixture sintética allowlisted; no admite un perfil financiero aportado por el navegador. La variante completa continúa limitada a la fixture sintética exacta.

Esto valida el adaptador local, no una comparación de calidad entre modelos. No hay respuestas LLM ni ganador A/B/C. La UI cotidiana usa un perfil reducido propio y vista previa local; conectar sus campos al DTO completo y a una IA real sigue siendo trabajo posterior.

## Bloqueos y límites que permanecen

- Sin proveedor IA configurado/autorizado, sin llamadas a Google/Groq y sin calidad/latencia medidas.
- Los veinte candidatos no son un catálogo de ofertas publicables ni comparación cuantitativa contractual. Faltan condiciones, permisos y solución de conflictos concretos.
- PostgreSQL y hosting públicos no creados; el snapshot es un adaptador temporal local, no una sustitución aprobada de esa arquitectura.
- Sin ingesta diaria, carga de cien usuarios, revisión jurídica o endurecimiento de producción. El uso de `http.server` es para este prototipo loopback, no para exponerlo directamente a Internet.
- Perfil UI todavía de seis preguntas; no cubre todos los ingresos, deudas, compromisos y capacidad de pérdida de la planificación.
- Impresión HTML disponible en código; no se probó impresora ni se generó PDF en esta entrega.
- Detalles menores de pulido: el encabezado del comparador conserva “Compare” y el aviso genérico de borrar copia puede ser más preciso cuando también se reinicia el mapa. No impiden el recorrido verificado; no se afirma que la UI esté libre de defectos.

## Cómo abrir, arrancar y parar

Si la URL responde, ya hay un servidor: no arrancar una segunda copia en el mismo puerto. Si no responde, abrir una terminal en esta carpeta y ejecutar `python app.py --port 8765`, o usar `iniciar.cmd`. No se instala nada. Parar con Ctrl+C en esa terminal; si está gestionado por Hermes, detener únicamente el proceso identificado de este prototipo.

## Parada del encargo

Se detiene la construcción local en el hito navegable probado. Las siguientes dependencias requieren revisar el diseño con el grupo y configurar acceso/condiciones del proveedor, datos y publicación. No se activaron pagos, cuentas, instalaciones, servicios cloud, envío de perfiles reales ni cargas a terceros para evitar esos bloqueos.

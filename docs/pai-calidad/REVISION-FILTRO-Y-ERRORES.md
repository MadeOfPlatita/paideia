# Pai — diagnóstico offline de calidad y errores

4/11/2026. Diagnóstico independiente `deleg_310040db`, con proveedores sintéticos y sin red ni credenciales. No valida calidad del modelo real ni sustituye una muestra de respuestas reales.

## Filtro financiero

`financial_quality.py:1-15` se define expresamente como filtro léxico limitado, no verificador de hechos. El coordinador confirmó offline que estas tres frases no activan ni el filtro léxico ni el detector de afirmaciones sin respaldo de `backend_services.py`: «Este depósito no conlleva ningún riesgo», «Te recomiendo contratar este depósito» y «La TAE del 3,25 % sigue en vigor». Las cifras son ficticias. No se concluye que Groq haya producido esas respuestas; sí que no deben considerarse bloqueadas por estos dos detectores.

El revisor detectó además huecos de garantías y recomendaciones, y falsos positivos en frases que niegan una vigencia. Las atribuciones y vigencias no respaldadas son la misma clase de problema por la que se detuvo B4 tras sus dos ciclos; no se abre un tercero. El texto del prompt y el aviso genérico de que no se ha validado semánticamente no son una verificación de cada afirmación.

## Errores y tiempos

Con un proveedor ficticio, el backend distingue 429, timeout y autenticación mediante códigos y respuestas estáticas, sin reintento automático. Los mensajes de 429 y timeout son demasiado parecidos. No se han provocado esos errores con Groq real ni con una clave inválida real.

El timeout del navegador es 12 s (`static/app.js`) y el del proveedor puede llegar a 20 s (`pai_setup.py`): el navegador puede interrumpir la espera antes de que termine el servidor. El riesgo de reenviar un turno aún en curso es una inferencia por configuración, no un caso observado con proveedor real. No se ha probado cancelación del proveedor. No usar el resultado como prueba de que se cumple el presupuesto nocturno.

## Rúbrica y límite de aceptación

El conjunto A/B/C de `docs/validacion-04/03-benchmark/` tiene seis casos y una plantilla de revisión humana, no diez respuestas reales calificadas. `context_quality_benchmark.py` aplica el filtro léxico y no evalúa automáticamente todas las dimensiones o errores críticos. No hay suficientes respuestas reales de la misión para calificar diez preguntas: la única sonda real fue accidental y no sirve para validar calidad. La rúbrica preparada en `RUBRICA-DIEZ-PREGUNTAS.md` es un plan sin resultados; B1 no queda aceptado como asesor de calidad ni se habilita historial con proveedor real.

No se modificó código en esta revisión. Las recomendaciones, garantías y reclamaciones financieras siguen siendo riesgos abiertos para una revisión posterior autorizada; no se recomienda presentar el chat local con catálogo como aceptado.

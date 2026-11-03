# Gemini API / Google AI Studio para Paideia

**Evaluación documental oficial: 27 de octubre de 2026.** Se revisaron ocho páginas oficiales actuales y sus textos guardados en `evidencia/`. No se crearon cuentas, no se generaron/solicitaron claves, no se configuró facturación, no se aceptaron términos ni se hicieron llamadas autenticadas o pruebas del modelo.

## Veredicto

**No apto como API gratuita para publicar Paideia al público de España.**[1]  
Los términos vigentes exigen usar únicamente *Paid Services* al poner un *API Client* a disposición de usuarios del EEE; Paideia sería un sitio web/app de ese tipo.[1]  
El nivel gratuito existe y España figura como región disponible, pero la disponibilidad de la cuota no elimina esa restricción contractual.[1][5][8]

**Sí es un candidato limitado a evaluación sintética interna**, no un permiso ya confirmado para el proyecto académico.[1]  
No se debe confundir probar directamente AI Studio o una cuota gratuita con servir una aplicación a usuarios del EEE.[1][5]  
Además, Google restringe el uso de AI Studio/Gemini API a desarrolladores con fines profesionales o empresariales, “not for consumer use”; la documentación no aclara si un proyecto universitario público de educación financiera entra en ese ámbito.[1]

Para publicación, hacen falta dos cambios/confirmaciones: (1) confirmar por escrito con Google que el uso académico y el servicio web educativo a consumidores encajan en sus términos; y (2) una ruta Paid válida para usuarios del EEE.[1] El flujo documentado de Paid Tier requiere Cloud Billing, método de pago y, para prepago, un mínimo de 5 USD o equivalente; eso no cumple el presupuesto actual de 0 EUR/no tarjeta.[5] Hasta entonces: **sin Gemini API pública en Paideia; no anunciar una integración probada**.

## Cláusula EEE corroborada, con contexto

- **URL solicitada:** `https://ai.google.dev/gemini-api/terms`
- **URL final observada en navegador:** `https://ai.google.dev/gemini-api/terms?hl=en`; el navegador también resolvió automáticamente la variante española `https://ai.google.dev/gemini-api/terms?hl=es-419`. Es la misma página de términos con selector de idioma, no una versión archivada.[1]
- La página señala vigencia desde el **23 de marzo de 2026** y última actualización del **28 de abril de 2026**.[1]
- En `Use Restrictions`, después de la restricción de propósito profesional/empresarial y de acceso desde regiones disponibles, el texto actual dice:

> “You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom.”[1]

La definición de *API Clients* en la misma página incluye sitios web, aplicaciones y otros servicios.[1] Por tanto, no es una prohibición general de experimentar gratis en cualquier lugar: es una restricción específica para ofrecer un API Client a usuarios del EEE.[1]

La misma página distingue los dos conceptos que no deben mezclarse:

1. **Servicio gratuito:** AI Studio directo y la cuota no pagada de Gemini API se definen como *Unpaid Services*.[1]
2. **Datos de una persona en el EEE:** los términos de uso de datos de Paid Services se aplican también a todos los servicios gratuitos, incluido AI Studio y la cuota gratuita de Gemini API.[1] Eso regula el tratamiento de datos; **no convierte por sí solo la cuota gratuita en autorización para exponer una API Client gratuita a usuarios españoles**.[1]
3. **Servicio API clasificado como Paid:** los términos dicen que el acceso a Gemini API es Paid cuando se hace mediante un proyecto Cloud con una cuenta de facturación activa.[1] Eso no equivale a una garantía de coste cero: el flujo publicado para subir de Free Tier a Paid Tier pide facturación y prepago mínimo (o presenta un flujo Postpay para cuentas elegibles).[5]
4. Google confirma que el Free Tier está disponible en muchos lugares y la lista oficial incluye España.[5][8] Eso acredita disponibilidad regional, no permiso para la aplicación pública española bajo la cláusula EEE.[1]

**Corrección concreta a cualquier lectura anterior:** “Free = prohibido” es demasiado amplio; el nivel gratuito existe, y AI Studio directo es un caso distinto.[1][5]  
Pero “el Free Tier existe en España, por tanto vale para publicar Paideia” también es incorrecto: para un API Client ofrecido a usuarios del EEE, la regla actual exige Paid Services.[1][5][8]

## Candidato de modelo (uno, para probar; ninguno aprobado para producción)

**Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)** es el candidato más razonable para una prueba sintética: la documentación lo marca como estable y soporta *function calling* y salidas estructuradas; describe el modelo como eficiente para tareas de alto volumen, traducción y procesamiento simple.[3][6]

La página de modelo **no enumera una garantía o matriz de calidad para español de España**.[6]  
“Traducción” no demuestra precisión financiera en español.[3]  
Por eso queda como **candidato para una prueba española**, no como capacidad lingüística o calidad ya verificada.[3][6]  
No se hizo ninguna llamada de modelo.

En la tabla Standard vigente, la entrada y salida del Free Tier figuran “Free of charge”; en Paid, la entrada es **0,30 USD/1M tokens** y la salida **2,50 USD/1M tokens**.[3]  
La misma tabla indica uso para mejorar productos en Free (`Yes`) y no en Paid (`No`).[3]  
Para usuarios en el EEE se aplica además la regla regional de datos de los términos, descrita abajo; no debe leerse la celda `Yes` aislada como la regla completa para una solicitud desde el EEE.[1][3]

El *function calling* del modelo permite plantear herramientas propias, pero no prueba un conector ni una ejecución segura.[6] Para Paideia, limitarlo a funciones explícitas de consulta de catálogo de solo lectura y cálculos puros; sin operaciones, escrituras, credenciales bancarias ni SQL libre. La autorización y validación de argumentos deben imponerse en la aplicación, no confiarse al modelo.[6]

**No incluir Google Search grounding** en el diseño gratuito: para este modelo la tabla de Gemini API marca esa función como no disponible en Free Tier (la nota solo la ofrece para probar en AI Studio).[3] Los términos dicen que el grounding de búsqueda vía API es Paid y que Google guarda prompt, contexto y resultado durante **30 días**, con uso para depuración/pruebas del sistema de grounding.[1] Un catálogo propio de fuentes verificadas, consultado por una herramienta limitada, encaja mejor con el control de Paideia.

## Tratamiento de datos y condiciones financieras

- En el caso general de Unpaid Services, Google puede usar lo enviado y las respuestas para desarrollar/mejorar productos y tecnologías de aprendizaje automático; revisores humanos pueden leer, anotar y procesar entradas y salidas.[1] Google dice que las desvincula de cuenta, clave y proyecto antes de la revisión, y ordena no enviar datos personales, sensibles o confidenciales.[1]
- **Excepción regional relevante:** si se está en el EEE, los términos de uso de datos de Paid Services se aplican también a los servicios gratuitos.[1] En esa modalidad, Google dice que no usa prompts/respuestas para mejorar productos, pero registra prompts/respuestas durante un periodo limitado para seguridad, prevención de infracciones y obligaciones legales/regulatorias.[1] El texto no da una duración numérica para esos registros y permite almacenamiento/caché transitorio en países donde Google o sus agentes tengan instalaciones. No es una promesa de retención cero.[1]
- Los Google APIs Terms subyacentes también exigen una política de privacidad clara para el API Client y conceden a Google una licencia amplia sobre el contenido presentado para prestar, proteger y mejorar APIs, sujeta a esos términos/políticas.[2] Los Additional Terms de Gemini dan el contexto específico de datos de Paid/Unpaid y prevalecen si hay conflicto; no interpreto eso como borrado automático ni como garantía de cero retención.[1][2]
- La clave/API credential debe mantenerse confidencial y no incluirse en un proyecto de código abierto.[2] En consecuencia, no se puede incrustar una clave Gemini en el JavaScript de la web pública de Paideia ni subirla al repositorio.[2]
- El descargo actual de Google indica que no se debe confiar en el modelo para asesoramiento financiero/profesional y que el contenido es informativo.[1] La política prohíbe decisiones automatizadas sin supervisión humana que tengan impacto material perjudicial sobre derechos individuales en dominios de alto riesgo, incluida finanzas, y prohíbe inducir a error sobre experiencia financiera.[7]
- El uso educativo puede reducir el riesgo si Paideia explica y enseña, conserva los cálculos en código, muestra supuestos/fuentes y no afirma ser asesor autorizado.[1][7]  
  La excepción educativa de la política es discrecional y se refiere a esa política; no sustituye la regla EEE Paid-only ni resuelve por sí sola “business/professional, not consumer use”.[1][7]
- Los términos exigen usuario de 18 años o más y no permiten un API Client dirigido a menores o al que probablemente accedan.[1] Paideia define su audiencia como adulta, pero antes de publicar debe revisar si eso basta o necesita medidas de acceso/edad; una etiqueta de audiencia no es automáticamente una verificación efectiva.[1]

## Cuotas: documentación frente al panel

Google mide RPM, tokens de entrada por minuto (TPM) y solicitudes al día (RPD); se aplican por proyecto, no por clave, y el RPD se reinicia a medianoche del Pacífico.[4] La página vigente remite al panel de AI Studio para ver los límites activos y dice que los límites especificados no se garantizan y que la capacidad real puede variar.[4]

La documentación consultada **no da un valor interactivo Free Tier de RPM/TPM/RPD utilizable como cuota garantizada para este proyecto/modelo**.[4] El panel de cuenta/proyecto no se abrió y sus valores siguen **sin verificar**. No se afirma capacidad para 100 usuarios concurrentes; una cola/cupo visible puede manejar rechazos, pero no demuestra capacidad suficiente.[4]

## Acceso gratuito: pasos exactos para el usuario (sin compartir una clave)

1. Con una cuenta Google existente de una persona adulta, abrir [Google AI Studio](https://aistudio.google.com/) y elegir **Gemini 3.5 Flash-Lite**.[5][6]  
   La página de modelo ofrece acceso a “Try in Google AI Studio”; no se requiere crear una cuenta por nuestra parte.[3][5][6]
2. Para una prueba programática sintética, abrir [API keys](https://aistudio.google.com/api-keys).[5] La documentación dice que a usuarios nuevos se les crea por defecto un proyecto y una clave; comprobar que el proyecto seleccionado está en **Free Tier** antes de probar.[5]
3. No pulsar **Set up billing**, no activar Cloud Billing, no comprar créditos ni facilitar método de pago.[5] Si el flujo solicita tarjeta/facturación, detenerse: los documentos no prometen explícitamente que cada cuenta pueda completar el alta gratuita sin tarjeta, y Paid no encaja con el presupuesto acordado.[5]
4. Antes de cualquier prueba programática, abrir el panel de límites de AI Studio para ese proyecto/modelo y anotar RPM/TPM/RPD reales.[4] No extrapolar los límites documentados a concurrencia de usuarios.[4]
5. Ejecutar solo perfiles sintéticos del protocolo de evaluación ya aprobado; probar español de España y *function calling* con herramientas ficticias/solo lectura. No enviar perfiles financieros reales, ni pegar una API key en el chat, HTML, repositorio público o frontend.[1][2] Si se usa clave, guardarla fuera del repositorio y solo en un entorno servidor controlado.[2]

## Prueba decisiva y estado final

**Para decidir publicación:** la prueba decisiva no es que AI Studio acepte una petición gratuita; es acreditar una ruta Paid permitida para usuarios de España y resolver por escrito la ambigüedad sobre el servicio académico, público y consumidor.[1]  
Con 0 EUR/no tarjeta, la documentación actual no ofrece una ruta de producción demostrada.[1][5]  
**Decisión: descartar Gemini API Free como backend público de Paideia España; conservar Gemini 3.5 Flash-Lite solo para evaluación interna con datos sintéticos, sujeta a que el propio usuario acepte los términos aplicables y confirme que su cuenta obtiene el acceso gratuito sin facturación.**[1][5]

**No verificado:** alta sin tarjeta en una cuenta concreta, cuotas efectivas del panel, latencia, calidad en español, ejecución de herramientas, política de logs del proyecto, volumen/concurrencia, integración, protección del secreto, despliegue o revisión jurídica. Este informe no acredita integración ni publicación.

## Sources

[1] https://ai.google.dev/gemini-api/terms — Gemini API Additional Terms of Service
[2] https://developers.google.com/terms — Google APIs Terms of Service
[3] https://ai.google.dev/gemini-api/docs/pricing — Gemini Developer API pricing
[4] https://ai.google.dev/gemini-api/docs/rate-limits — Gemini API rate limits
[5] https://ai.google.dev/gemini-api/docs/billing — Gemini API billing
[6] https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite — Gemini 3.5 Flash-Lite model documentation
[7] https://policies.google.com/terms/generative-ai/use-policy — Generative AI Prohibited Use Policy
[8] https://ai.google.dev/gemini-api/docs/available-regions — Available regions for Google AI Studio and Gemini API

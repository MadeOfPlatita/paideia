# B4 — revisión independiente de la corrección 2

Dictamen `deleg_f2509b23`: **desfavorable**, 4/11/2026. Dos ciclos agotados; se detiene B4 sin aceptar y sin publicar. No se permite un tercer ciclo en esta misión.

La revisión reprodujo en HTTP y Chromium, con proveedor sintético y sin salida externa, respuestas que presentan una fuente secundaria como oficial o una tasa vencida como vigente cuando el modelo no invoca herramientas. El filtro de frases no evita todas esas variantes; el aviso genérico no valida la afirmación. También encontró que condiciones malformadas podían presentarse como ausencia de condiciones y que la proyección del chat omitía conflictos y campos desconocidos.

Se comprobaron mejoras para los turnos que usan herramientas: texto libre retenido y fichas con procedencia, consentimiento, identificación exacta, rechazo de herramientas no permitidas, tratamiento de excepciones y ausencia de datos sintéticos privados en logs. Estas pruebas offline no acreditan calidad de Groq ni resuelven las fuentes o condiciones compartidas de B6. Artefactos en el scratch del perfil `b4_indep/` (sujetos a limpieza), transcripción `deleg_f2509b23`.

No ejecutar Groq real mientras falten salvaguardas y contador de la misión aprobados. Conservar los cambios existentes sin desplegar; la protección parcial y la retención del texto son funcionalidad distinta del chat original y aún no están aprobadas.

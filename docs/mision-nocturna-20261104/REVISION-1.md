# Cupo de misión nocturna — revisión independiente

Revisión `deleg_dc116995`, 4/11/2026: **desfavorable para autorizar llamadas reales**. El ledger probado offline conserva reservas en reinicios y falla cerrado ante corrupción parcial, y el transporte contado comprueba el plazo antes de la petición; pero la ruta normal de la aplicación y utilidades legadas no están conectadas al mismo presupuesto, y una copia del árbol puede crear otro ledger. La restauración coordinada de todos los ficheros de estado tampoco puede detectarse con testigos exclusivamente locales. Además, la conexión TCP/TLS puede iniciarse antes de comprobar la guarda previa al POST.

No se ha inicializado la misión real ni se han hecho llamadas reales en esta misión. No es un sandbox frente a control arbitrario de Python o del sistema; el presupuesto solo puede afirmarse dentro de las rutas realmente integradas y verificadas. Se observaron también fallos cerrados de disponibilidad en inicialización y límites de las pruebas.

Evidencia técnica temporal `cache/scratch/night-review/` del perfil Hermes (sujeta a limpieza), transcripción `deleg_dc116995`. La siguiente corrección debe tratar la identidad global de la misión y el bypass de la aplicación sin afirmar protección contra manipulación arbitraria. Sin integración y revisión favorable, mantener las pruebas Groq deshabilitadas.

# B4 — revisión independiente de la corrección 1

Dictamen `deleg_b93dc16b`: **desfavorable**, 4/11/2026. La capa offline conserva mejor clase y fecha de fuente, pero el usuario aún puede recibir una afirmación incorrecta sin ver la clase secundaria, la fecha ni la advertencia de que el texto no se ha validado. La fuente de algunas condiciones de snapshot no se resuelve y un error del servicio de condiciones puede presentarse como ausencia de datos. También se observó sobreafirmación de estado, discrepancias entre clase de condición y de cita, y normalización de identificadores malformados antes de validarlos.

La revisión usó proveedores sintéticos y servidores de prueba loopback; reprodujo una respuesta falsa que llamaba oficial a una fuente secundaria y otra que declaraba vigente una tasa vencida. No se probó el comportamiento actual de Groq, el despliegue ni un móvil físico. Confirmó los límites de consentimiento y ámbito y que los logs de depuración ya no imprimían los argumentos en la prueba realizada. Los defectos compartidos de fechas/datos B6 permanecen fuera de esta corrección y B6 sigue detenido.

Se inicia el segundo y último ciclo de B4. No aceptar por el mero hecho de mostrar avisos o pasar validaciones de estructura: la salida libre del modelo no es automáticamente verdadera. Evidencia y transcripción técnica: `deleg_b93dc16b`.

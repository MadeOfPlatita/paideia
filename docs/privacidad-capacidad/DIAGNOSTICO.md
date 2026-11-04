# B8 — diagnóstico de privacidad, revisión offline

Fecha: 4/11/2026. Revisión independiente `deleg_ea8976dd`; app local y WSGI en loopback, chat sintético y datos ficticios. Sin credenciales, `.env`, Groq ni red externa. Hallazgos pendientes de verificación/coordinación; no es aceptación del bloque.

## Hallazgos prioritarios

1. Avisos afirman que el mapa no se envía al chat ni al proveedor, pero una proyección de campos expresamente seleccionados sí viaja en `POST /api/chat` tras consentimiento. No es el perfil completo. Los avisos deben distinguir almacenamiento, envío de pregunta y envío de campos elegidos.
2. Con chat público desactivado, la interfaz aún permite enviar un POST al servidor WSGI y recibe 405; no se envía al proveedor, pero afirmar que «no se envía nada» no describe el tráfico navegador-servidor. No se probó Vercel ni sus registros.
3. Borrar el perfil no borra automáticamente historial ni texto del chat; hace falta una descripción clara del alcance y que la eliminación local no borra lo ya enviado al proveedor. El botón separado de borrar historial sí funcionó en el fixture.
4. La eliminación en una vista puede ser seguida de un autoguardado de otra vista del mismo origen: prueba con iframe same-origin que vuelve a escribir la clave después de borrar. La garantía de borrar «todas» las copias requiere tratar esa concurrencia o limitar explícitamente su alcance; un iframe no es prueba directa de dos ventanas físicas.
5. Una copia previa cargada sin consentimiento de nuevo autoguardado puede presentarse como estado «incompleto o desconocido» y el aviso aparece duplicado. Revisar sin alterar las protecciones de revocación.
6. Falta en Privacidad una explicación comprensible de pregunta, campos seleccionados, historial autorizado, proveedor y límites de retención. La configuración concreta de ZDR no se ha comprobado; fuentes públicas en `FUENTES-GROQ.md`.

## Lo que se informó comprobado

Sin opt-in inicial no había almacenamiento; guardado local y borrado ordinario de versión actual y legacy funcionaron, y el fallo de borrado generó aviso. Historial en memoria se borró con su control propio y no persistió tras recargar. La vista previa de contexto no hizo una petición en la prueba. No se validaron datos del proveedor real, dos ventanas físicas, teléfono, lector de pantalla ni plataforma Vercel.

Evidencia temporal sin datos reales: `cache/scratch/b8-privacidad/evidencia/` en el perfil Hermes, sujeto a limpieza; transcripción `deleg_ea8976dd`. `backend_services.py` cambió durante la revisión: revalidar hallazgos que lo involucren en la versión final antes de corregir o aceptar.

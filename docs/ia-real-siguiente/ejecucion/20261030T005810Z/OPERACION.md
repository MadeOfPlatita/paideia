# Nuevo bloque tras la incidencia de ventana

Autorizado expresamente después de corregir el problema. Se mantienen los archivos y el corte del bloque anterior, cerrado con0intentos. El nuevo ID y el corte están fijados en MISSION.json y en la lista explícita de autorizaciones del cargador; no se aceptan manifestos arbitrarios. No reiniciar cupo/corte al reabrir.

Corregido con TDD: fallo de arranque ya no deja siguientes clics silenciosos; ventana pendiente detecta vencimiento, limpia la entrada y deshabilita inicio con mensaje explícito. Los errores son categorías seguras, sin excepción cruda ni claves. No se ha demostrado la causa histórica exacta del botón del usuario.

Coordinador reprodujo4tests Tk con invocación real de botón en ventanas propias ocultas y transporte ficticio, y la regresión238Python/24Node/19HTTP. Revisión independiente del cambio y la nueva autorización pendiente antes de abrir ventana real. Hasta clave voluntaria+Free no se hace ninguna petición real. A/B/C manual separado, despuésQA mínima. Perfil/historial externos continúan desactivados.

Desde prototipos/paideia-local usar secure_groq_session.py --mission con la ruta absoluta al MISSION.json de esta carpeta. Los recibos se aíslan porrun_id; conservar ledger y diario, no autoreparar ni resetear. Tras autorizar enventana: QA conceptual breve y cálculo determinista ficticio; luego evaluar A/B/C si se autoriza y no hubo error. Parar ante error, cuota o corte, sin reintentos automáticos.

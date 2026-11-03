# Revisiones iniciales A/B

A (`deleg_931f4ba8`, tarea1): aprobada para archivos actuales; cinco pruebas dirigidas más sondeo independiente de app sin Tk, HTTP loopback, error explícito antes de inicializar presupuesto y dobles de widgets sin consentimiento. Sugerencia no bloqueante: añadir permanente prueba que falta Tk impide inicializar MissionBudget.

B (misma entrega tarea2): no hubo preocupación de seguridad en los sondeos de procedencia, pero **no aprobada como conjunto** por dos errores de contrato/pruebas: código de rechazo estructurado cambió a CHAT_INVALID_PROVIDER y test de status configura adaptador estructurado como legacy. Salida `passed` fue lista de pruebas y no booleano; no interpretarla como aprobación. Se ha delegado conservar código estructurado y migrar setup del test, con regreso a revisión posterior. Regresión global aún 356 aprobadas, 23 fallidas en el primer corte. Nada autoriza integración real ni retirar guardas.

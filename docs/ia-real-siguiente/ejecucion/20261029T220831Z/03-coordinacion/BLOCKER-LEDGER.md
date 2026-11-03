# Revisión previa de ledger

La revisión independiente encontró corrupción intermedia de diario aceptada. No demostró reposición de cuota ni llamadas externas, pero viola la parada ante corrupción exigida por el encargo. GUI real sigue cerrada,0modelcalls. Se delegó corrección mínima de diario encadenado (no basta comprobar formato de hash); no se borra ni se repara estado de misión automáticamente.

Una búsqueda acotada de archivos de ledger en esta carpeta real no encontró registros inicializados: el formato nuevo no requiere borrar presupuesto real previo. Los tests usan directorios temporales. La garantía se limita al operador/filesystem local confiable; no se pretende resistir borrado/restauración coordinada de todos los archivos por su propietario.

Después del fix: reproducir reserva/restart/corrupción intermedia y ejecutar revisión antes de ventana. Mantener corte original y24intentos, sin ampliar tokens/modelo ni consumir cuota para depurar.

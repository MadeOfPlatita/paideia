# Corrección acotada de negación — offline

El guard mantiene el indicador `ABSOLUTE_NO_RISK` y la normalización NFKC y eliminación de caracteres de formato. Se limita la búsqueda de marcadores al último segmento separado por `y` o `pero`, y se restringe `no` a formas léxicas reconocidas de refutación previa o negación de predicado. Se reconoce también la refutación posterior `no es posible`. No se han cambiado los fixtures, transporte, proveedor ni configuración.

La prueba nueva reproduce en rojo los tres ejemplos solicitados y el contraejemplo con `pero`; después pasan en verde. Incluye además dos negaciones ajenas sin conjunción y los cuatro ejemplos de negación/refutación que se debían preservar. En la última ejecución: 17 pruebas de calidad financiera, 255 pruebas Python y 24 Node, todas correctas, con dobles de prueba locales; no se usaron redes externas ni modelos reales.

## Límites

Son reglas léxicas delimitadas, no un analizador gramatical ni una comprobación semántica o financiera. La división por conjunciones y la lista de verbos pueden producir falsos positivos o negativos en frases complejas o variantes no contempladas; por ejemplo, `No es posible ahorrar sin riesgo` no queda cubierta por la regla de refutación *posterior*. Una salida sin indicadores no es aprobación de calidad ni prueba de ausencia de riesgo.

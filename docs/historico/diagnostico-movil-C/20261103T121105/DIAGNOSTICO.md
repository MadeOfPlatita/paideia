# Diagnóstico reproducible del mecanismo de evaluación

Estado: experimento concluido, revisión independiente pendiente. No se modificaron la aplicación ni el script de integración.

## Evidencia previa
Los ficheros mobile.json y mobile-attempt1.json de la revisión anterior registran Runtime.evaluate timed out con una expresión async IIFE. El transcript abreviado no contiene las llamadas completas, por lo que no demuestra cada detalle del lanzamiento pasado. Se conserva ese límite: una ejecución actual satisfactoria no demuestra por sí sola la causa histórica.

## Experimento 1, suficiente para discriminar la hipótesis
Hipótesis: esperar una promesa larga dentro de la evaluación supera su ventana síncrona; lanzar y recoger después evita ese límite sin cambiar el test.

En documento nuevo http://127.0.0.1:18874/, DOM complete y CDP móvil390×844:

- `js('new Promise(resolve=>setTimeout(()=>resolve("finished"),6500))')` falló con Runtime.evaluate timed out en **5.026s**.
- Misma promesa, mismo retraso y documento: asignar resultado enwindow y terminar la expresión con `"started"` devolvió ese marcador en **0.016s**.
- Tras una espera acotada, la lectura corta devolvió `finished`.
- Resultado íntegro en `EXPERIMENTO-1.json`. Demuestra una diferencia del mecanismo del arnés, sin ejecutar código financiero. No se gasta un segundo experimento por rutina.

Esto proporciona una explicación reproducible compatible con los fallos anteriores: la promesa supera el límite de evaluación, no requiere un defecto de la aplicación. No se afirma que fuera la única causa histórica ni se ha modificado Hermes para ampliar ese límite.

## Aplicación del mecanismo al test intacto
Se leyó `tests/c_integration_browser.js` como expresión ya invocada. Lanzamiento:

```javascript
window.__acceptanceResult = null;
(TEST_IIFE).then(
  r => window.__acceptanceResult = r,
  e => window.__acceptanceResult = {ok:false, error:String(e)}
);
"started"
```

TEST_IIFE significa el contenido literal del fichero, no un nombre existente en la aplicación. No añadir otra invocación, top-level await ni envolver en f-strings Python con llaves.

La primera recogida a8s seguía pendiente y una aserción del coordinador la trató prematuramente como fallo. Se conserva `coordinator-mobile.json`; no es un veredicto del test. La segunda recogida completó **27/27**, sin nueva ejecución del script: `coordinator-mobile-final.json`. Por tanto tampoco se debe interpretar un marcador pending como fallo de aplicación. Pestaña observada hidden; no se demuestra cuánto contribuyó esa condición a la duración.

## Métricas, sin ocultar escalado
Antes del experimento y del test, en Inicio: clientWidth390,scrollWidth448,innerWidth448,visualViewport390×844,scale1. Después del recorrido C: clientWidth390,scrollWidth390,innerWidth390,visualViewport390×844,scale1. Se conserva la diferencia inicial: no es una certificación de diseño sin desbordamientos de toda la web ni prueba en móvil físico. No se cambia CSS, viewport o assertions para obtener verde. El alcance de aceptación pendiente es biblioteca/comparación/ayudas; cualquier defecto nuevo confirmado exige detenerse.

## Revisión separada y límites
Revisor independiente despachado deleg_46008d2c, sesión y servidor propios, resultados exclusivos en independiente/. Debe reproducir escritorio/móvil con documentos nuevos y probes propios. El coordinador no acepta C basándose solo en su pase móvil.

Qwen no se fuerza aquí: el límite de tiempo es observable con herramientas y una consulta estática al modelo no añade evidencia. Ponytail se aplica evitando cambios de producción, dependencias y wrappers permanentes. No se repiten suites Python/Node intactas. Las nuevas escrituras son solo documentación y evidencia del diagnóstico.

# Pai con catálogo — revisión posterior a la misión

**Resultado:** no aceptado, revisión independiente `deleg_ae747a38`. Trabajo local a petición posterior del equipo; sin Groq real, credenciales ni publicación.

## Hallazgos principales

1. **Cálculo:** la barrera comprueba si la cifra está entre los supuestos o resultados, pero no a qué magnitud corresponde. Con capital de 1.000 € e interés de 60,90 €, permitió mostrar «El interés obtenido es 1.000,00 euros». El resultado correcto del motor no llegaba al usuario en ese turno. Reproducido por coordinador y por el revisor mediante HTTP y navegador sintéticos.
2. **Conflictos:** la respuesta JSON los incluye, pero la interfaz no muestra los detalles del conflicto ni los campos desconocidos. En búsquedas tampoco ofrece siempre el enlace de la fuente de la condición.
3. **Texto no verificado:** la barrera léxica deja pasar paráfrasis, cifras en palabras y algunas recomendaciones, garantías y afirmaciones de vigencia. No es un verificador semántico y no debe describirse como tal. La calidad del proveedor real no fue medida.
4. **Condiciones y fuentes:** se detectaron combinaciones incoherentes de unidad/métrica y valores desconocidos que pueden mostrarse; el presupuesto agregado de fuentes y la proyección de detalle necesitan límites.

## Mejoras comprobadas en el intento

Las condiciones estructuralmente malformadas producen un error explícito en los casos probados, sin presentarse como ausencia de datos; consentimiento, ámbito de herramientas y mensajes sanitizados funcionaron en las pruebas acotadas. Estas mejoras no subsanan los fallos anteriores ni acreditan el bloque completo.

## Seguimiento

Se trabaja en mostrar el cálculo y supuestos deterministas, conflictos, fuentes y errores de forma legible, con pruebas offline; nada se ha publicado. Se estudia cómo conservar una conversación conceptual útil sin presentar texto libre no comprobado como hecho financiero. La solución necesita revisión independiente y no equivale a una prueba de calidad de Groq real.

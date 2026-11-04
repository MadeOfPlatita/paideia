# Paquete y guion de entrega — preparación

## Estado publicado comprobado

La web pública **https://paideia-mu.vercel.app** abrió correctamente en navegador: cabecera «Versión pública · IA no conectada», `/api/status` con modo `public_serverless` y estado de IA `not_configured`. No se envió ninguna pregunta ni se activó el chat. Esta comprobación se hace desde el mismo equipo; no acredita por sí sola que abra desde otro dispositivo ni desde otro país.

El repositorio **https://github.com/MadeOfPlatita/paideia** se volvió privado a petición del equipo después de comprobar que estaba público; se verificó en GitHub. Los cambios de la misión nocturna no se han publicado ni subido.

## Qué se puede enseñar hoy con seguridad

- Biblioteca con 20 candidatos y cuatro fichas transcritas con fuente y fecha.
- Comparación de depósitos a 12 meses: EBN 3,10 % frente a Self Bank 2,75 %, con aviso de que la segunda fuente es secundaria.
- Escenarios A/B, cálculo del motor, gráficos, tabla e informe HTML descargable. Guion de cuatro minutos: `docs/recorrido-escenarios-academico/GUION-DEMO.md`.
- Ensayo ficticio de cinco pasos con Openbank y cierre de no envío.
- Glosario y ayuda contextual.

## Qué no se debe presentar como terminado

- La IA en la web pública está apagada. El chat local existe, pero B4 (catálogo por el modelo) quedó detenido sin aprobar y el historial no está habilitado.
- B6 (fuentes y fechas dentro del informe del comparador) quedó detenido tras dos revisiones desfavorables; el informe de escenarios es sólido, pero no debe atribuírsele la trazabilidad de condiciones que aún falla.
- El ensayo está acreditado con Openbank, no con todos los productos.
- No se certifica impresión nativa en PDF, diálogo de impresora, móvil físico ni accesibilidad con lector de pantalla.
- El repositorio es privado: la profesora necesitará una invitación o que el equipo lo haga público al entregar.
- No se ha desplegado nada de esta misión en Vercel.

## Plan B sin conexión

1. Para una demo local sin IA en Git Bash, usar `cd prototipos/paideia-local && PAIDEIA_GROQ_ENABLED=0 python app.py --port 8765` y abrir `http://127.0.0.1:8765/`. El código local contiene cambios aún no aprobados de B4 y B6; no presentarlos como terminados. No retirar el indicador de IA apagada durante la misión.
2. Si no hay navegador o proyector, usar el HTML del informe descargado en `docs/recorrido-escenarios-academico/coordinador/` o mostrar las capturas de `docs/correcciones-qa-20261103T172201/`.
3. Llevar el guion impreso y las cifras esperadas: 4.255,02 € / 4.000,00 € / 3.853,91 € para A; 4.388,32 € / 3.974,64 € para B.

## Checklist del equipo antes de entregar

1. Antes de entregar, invitar al usuario de GitHub de la profesora o decidir hacer público el repositorio.
2. Confirmar que el enlace de Vercel abre desde un móvil o desde otra red.
3. Revisar la lista de «Qué no se debe presentar como terminado» y retirar de la exposición cualquier promesa que la contradiga.
4. Actualizar el diario de desarrollo con la autoría y el uso de IA ya documentado.

## Pendiente de terceros (no resuelto por esta misión)

- **Profesora:** el repositorio es privado; se necesita su usuario de GitHub para invitarla o una decisión de hacerlo público al entregar.
- **Proveedor de IA (Groq):** una sonda accidental llegó al proveedor fuera del contador de misión; no se autoriza seguir probando mientras el límite global no esté garantizado. La web pública sigue con el chat apagado y el chat local depende de su configuración local. No presentar esa sonda como validación del producto.
- **Licencia:** no se ha añadido ninguna licencia al repositorio. Es una decisión del equipo, no un olvido; si el trabajo se entrega públicamente conviene elegirla antes.
- **Despliegue:** la versión publicada en Vercel es anterior a los cambios de esta misión. Publicar B8, B9 y las correcciones de claridad exige un `npx vercel --prod` manual tras revisar y aprobar la mezcla, y antes revisar que no viaje ningún cambio de B4/B6, que siguen detenidos.
- **Impresión en PDF:** el informe HTML de escenarios se descarga y se imprime desde el navegador; no se ha verificado en una impresora física ni en móvil real.

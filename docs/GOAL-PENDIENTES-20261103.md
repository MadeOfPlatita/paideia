# Paideia — todo lo pendiente, sin diseño

## Cómo usar este encargo

Este documento no activa nada. Se ejecuta con `/goal` y la instrucción de abajo. **Excluye por completo el rediseño visual**: no se cambia paleta, tipografía global, composición ni identidad. Solo se admiten ajustes funcionales de legibilidad, jerarquía de texto y accesibilidad que no impliquen rediseño.

**Corte:** 2 ciclos de corrección por bloque y se detiene ese bloque. Parar antes si falta una cuenta, una clave, una decisión del equipo o se agota la cuota. Registrar siempre: qué funciona, con qué evidencia, qué queda y por qué.

## Estado verificado al preparar este encargo (3/11/2026)

- Pai responde con Groq real desde `prototipos/paideia-local/.env` (modelo `openai/gpt-oss-20b`, timeout 20 s, 6 llamadas/minuto, 60/día, sin reintentos).
- Pai **calcula** con el motor local (`calculate_scenario`, ámbito solo-calculadora) y recibe el **mapa** solo con consentimiento y campos marcados.
- Escenarios A/B, resumen de diferencias e informe HTML descargable: aceptados con revisión independiente.
- Perfil local, biblioteca de 20 candidatos (solo metadatos), comparador de metadatos, ensayo ficticio en 5 pasos y glosario: funcionan.
- Regresión actual: 383 pruebas Python y 41 Node.
- **No existe enlace público**, ni condiciones reales de producto, ni PDF, ni historial de chat.

## B0 — Cierre operativo y seguridad (primero, corto)

1. Revocar en Groq la clave que estuvo escrita dentro de `.gitignore` y confirmar que la activa solo vive en `.env` (ignorado).
2. Verificar que `.env.example` existe, que el arranque sin clave deja el chat apagado y que nada imprime secretos.
3. Mostrar en la interfaz el cupo del chat y su consumo (llamadas del día) sin exponer detalles internos.

**Aceptación:** repo sin secretos, chat apagado sin `.env`, cupo visible.

## B1 — Pai como asesor (calidad, no funciones nuevas)

1. Ajustar el prompt para que **use el mapa** de forma proactiva: que mencione objetivo/horizonte cuando aporten, pida el dato que falta en vez de suponerlo y no repita cifras como certeza.
2. Evaluar subir el techo de salida de 256 tokens dentro de los límites validados del adaptador, con prueba que lo respalde; si no se sube, dejar constancia de por qué.
3. Decidir el historial de conversación: hoy solo funciona en modo prueba. Si se aprueba, habilitarlo con consentimiento propio, dos turnos y borrado visible.
4. Revisar el filtro de calidad financiera con diez respuestas reales: cuántos falsos positivos y negativos produce.
5. Comprobar errores reales: clave inválida, 429, timeout y cupo agotado, con mensaje útil y sin reintento oculto.
6. Rúbrica breve de calidad sobre diez preguntas (relevancia, exactitud, límites, longitud), con las respuestas guardadas. Sin afirmar calidad general a partir de una muestra.

**Aceptación:** el modelo usa el mapa cuando procede; errores explicados; evaluación registrada con sus límites.

## B2 — Catálogo con condiciones reales (hueco principal)

1. Documentar fuentes y permisos por familia: cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF.
2. Completar 20 productos reales con identidad, familia, condiciones cuantitativas, liquidez, plazo, costes, riesgo, garantía, **fuente y fecha del dato**.
3. Definir reglas de caducidad por tipo de dato y excluir de la comparación lo que pueda inducir a error.
4. Establecer cómo se refresca (manual o API) y qué ve el usuario si falla: último dato verificado con fecha y aviso.
5. Ficha de producto con separación explícita entre dato, supuesto y ejemplo.

**Aceptación:** ficha y comparación muestran condiciones con fuente y fecha; ningún dato sin origen; nada marcado como actual sin serlo.

## B3 — Comparador con condiciones

1. Comparar hasta tres productos con criterios en orden fijo: liquidez, plazo, costes, garantía/pérdida y rendimiento con su periodo.
2. Motivos de no comparabilidad explícitos, sin ranking ni «mejor para ti».
3. Botón «Explorar escenarios» que lleve los supuestos del producto, marcando la tasa como supuesto manual.
4. Estados de sin datos, dato obsoleto y error, con acciones de recuperación.

**Aceptación:** comparación trazable, sin recomendación implícita, con los tres estados probados.

## B4 — Pai y catálogo

1. Decidir si se aprueba el uso externo del catálogo por el modelo (hoy bloqueado por diseño).
2. Si se aprueba: habilitar solo búsqueda y detalle, sin comparar ni calcular por esa vía, y probar que no puede saltarse el ámbito.
3. Cuando cite un producto, debe arrastrar fuente y fecha; si no hay dato, debe decirlo.

**Aceptación:** respuestas con producto citado llevan fuente y fecha; sin aprobación, sigue bloqueado y se informa.

## B5 — Ensayo de contratación ficticia

1. Partir de un producto real documentado del catálogo, con sus hechos y su fecha.
2. Recorrido completo de cinco pasos con comprensión de riesgos y cierre explícito de que no se envió nada.
3. Sin pedir documentos, credenciales, tarjeta ni datos personales.

**Aceptación:** recorrido completo con producto real; la operación y los importes siguen siendo ficticios y así se declara.

## B6 — Informe

1. Decidir el PDF: impresión nativa del navegador o generación de archivo, sin dependencias nuevas si es posible.
2. Añadir fuentes y fechas de los productos al informe del comparador.
3. Abrir el archivo generado y comprobar contenido, paginación y ausencia de perfil.

**Aceptación:** informe utilizable con cifras, supuestos, fuentes y fecha; declarar qué se comprobó y qué no (diálogo nativo, impresora).

## B7 — Publicación y entrega (bloqueante para la Wiki)

1. Repositorio GitHub con la cuenta del equipo; licencia y visibilidad decididas explícitamente.
2. Hosting gratuito acorde a la decisión de alojamiento ya documentada. Hoy `app.py` solo escucha en `127.0.0.1` y rechaza Host/Origin externos: requiere adaptación y prueba, no solo cambiar el bind.
3. Enlace público comprobado desde fuera del equipo, sin secretos en el repositorio.
4. Paquete de entrega: HTML/CSS/JS y diario de desarrollo actualizado con prompts, uso de IA y decisiones.
5. Guion de demo de tres minutos y plan B sin conexión.

**Aceptación:** URL que abre desde otro dispositivo; repositorio sin `.env`; paquete descargable.

## B8 — Privacidad, términos y capacidad

1. Aviso de privacidad actualizado: qué se envía al proveedor, qué se queda local y cómo se borra.
2. Borrado de perfil e historial comprobado en la interfaz.
3. Revisar términos del proveedor: uso educativo, límites, tratamiento de datos.
4. Medir el límite real de carga con una prueba razonable; documentar cuántos usuarios aguanta sin prometer 100 concurrentes.

**Aceptación:** aviso coherente con lo que hace el código; límites declarados con evidencia.

## B9 — Robustez y accesibilidad funcional (sin rediseño)

1. Estados de carga, error y vacío en todas las pantallas.
2. Recorrido completo con teclado en chat, biblioteca, comparador y escenarios.
3. Sin desbordamiento horizontal en 320, 390, 768 y 1280 px.
4. Prueba en un móvil real si hay dispositivo disponible; si no, declararlo como pendiente.

**Aceptación:** ninguna función exige ratón; ningún ancho rompe la lectura.

## B10 — Verificación y cierre

1. Por bloque: pruebas ejecutadas, evidencia guardada y revisión independiente cuando haya riesgo.
2. No contar pruebas como avance funcional: el avance es lo que el usuario puede hacer.
3. Actualizar `docs/ESTADO_Y_PLAN.md`, `docs/DIARIO_DESARROLLO.md` y `docs/PLAN-PAI-PENDIENTES.md` al cerrar cada bloque.

## Fuera de alcance (no hacer)

Rediseño visual completo; tercer escenario; gráficos conjuntos; cálculo inverso por objetivo; persistencia de escenarios; cuentas de usuario; pagos; datos personales; operaciones reales; PostgreSQL; servicios que exijan tarjeta; reescribir el motor de cálculo.

## Orden recomendado

B0 → B1.1/B1.2 → B2 → B3 → B7 (para desbloquear la entrega) → B4 → B5 → B6 → B8 → B9 → B1.3-B1.6 en paralelo si hay hueco.

# B9 — revisión independiente final del ciclo 2

**Dictamen `deleg_c29be119`: favorable para las correcciones D1–D6**, 4/11/2026. Revisión con navegador Chrome headless y servidor sintético en loopback; sin proveedor real ni lectura de `.env`. No acredita accesibilidad general, lector de pantalla ni dispositivo físico.

Se verificó el foco al reintentar en escenarios y ensayo, incluido un segundo fallo; recuperación del estado con un único reintento acotado; validación de campos vacíos con foco, `aria-invalid` y descripción; reflujo del stepper y navegación; ausencia de mutaciones redundantes en la región viva; y conservación del foco durante el cálculo. Las regresiones B8 y del historial se ejercieron por separado, con fixtures ficticios. El coordinador ejecutó `tests/b9_accessibility.test.cjs`: 32 comprobaciones favorables.

**Límite residual comprobado:** con viewport de 320 px al 200 % y scrollbar clásica de escritorio, `clientWidth=305`, `scrollWidth=320`: persisten 15 px de desplazamiento horizontal asociados al `min-width:320px` preexistente. En la emulación móvil medida no se observó. Las etiquetas del stepper ocupan de dos a cuatro líneas: no se certifica comodidad de lectura. Esto no se interpreta como ausencia universal de desbordamiento.

Los cuatro archivos revisados coinciden con los hashes calculados por el coordinador y con sus copias públicas locales:

- `app.js`: `413aeb289e5f2cc087c3d4604b6221f4dd4f5748d13859adbf2913d15af79044`
- `styles.css`: `4df2d4d2794a5ffcb70b8d0cd780b1a50d546a1c6513286e4d469cf511d7b3fe`
- `comparison_report.js`: `3afc0b23bbcc67712654d5d0490224ccccb4a1996bcdae9b7e3a1ff038d77b90`
- `index.html`: `0f67ca8162decaf6c959a26ea5812913a621a44bcab6d83a97adb0fa3a66cc20`

B9 queda aceptado **únicamente para el alcance local revisado**, con las limitaciones anteriores; no desplegado. La revisión anterior y sus bloqueantes quedan conservados en `REVISION-CICLO-1.md`.

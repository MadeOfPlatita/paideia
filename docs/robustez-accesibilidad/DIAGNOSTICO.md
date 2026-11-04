# B9 — robustez y accesibilidad funcional: diagnóstico

Diagnóstico de solo lectura, 4 de noviembre de 2026, en Chrome headless con emulación de viewport. Trece defectos reproducidos: 2 altos, 6 medios y 5 bajos. Ningún archivo del repositorio se modificó durante el diagnóstico. La corrección es un ciclo posterior y no toca el diseño visual.

## Altos

1. **El skip-link navega a Inicio y no enfoca el contenido.** En `#biblioteca` o `#escenarios`, al pulsar el enlace se va a `#inicio` y el foco no llega a `#main-content`. Además, el foco inicial está en el `h1`, así que el primer Tab salta al buscador y nunca pasa por el skip-link ni la cabecera. `index.html:24`, `app.js:313-321`, `248-251`, `2712`.
2. **No hay timeout de red.** Si `/api/status`, `/api/catalogue` o `/api/calculate` no responden, la interfaz queda en «Comprobando…», «Cargando…» o «Calculando…» sin error, sin cancelar y sin reintentar. Se recupera sola si la petición termina. `app.js:51-71`.

## Medios

3. **«Intentar de nuevo» destruye el foco y el éxito no se anuncia.** Al pulsar, el botón desaparece y el foco cae en `BODY`; con 20 tarjetas cargadas sigue ahí y no hay región viva. La ficha es la excepción: enfoca el panel. `app.js:1402-1414`, `1483-1489`, `1729`, `1870-1873`, `1422`, `2296`.
4. **Carga y éxito silenciosos.** Solo hay `aria-busy`; ninguna región viva anuncia «Cargando…» ni el resultado. `app.js:1622`, `1773`, `1626`, `2413`, `2252`.
5. **El refresco de condiciones roba el foco.** Con `/api/conditions` retenido, el foco salta de «Ver detalle» a `BODY` en biblioteca y del selector al `h1` en el ensayo. `app.js:1332-1345`.
6. **Errores de formulario no asociados al control.** Se anuncian por `role=alert`, pero el campo no lleva `aria-invalid` ni `aria-describedby`, y en escenarios no se enfoca. La búsqueda de biblioteca ya lo hace bien. `app.js:1153-1157`, `1172-1176`, `2179-2182`, `2244-2248`, `2434-2443`.
7. **Stepper del ensayo ilegible a 320 px y al 200 %.** Cada columna mide 58 px y «Condiciones» e «Comprensión» se desbordan («CondicionesImporte», «ComprensiónJustificante»). `app.js:2256-2265`, `styles.css:319-320`, `402-403`.
8. **La región viva de comparación de escenarios se reconstruye en cada tecla.** Cinco pulsaciones producen cinco reemplazos completos de una sección `aria-live`, con riesgo de reanunciar la tabla entera. `app.js:2044-2063`, `2085`, `2151`.

## Bajos

9. La confirmación en línea devuelve el foco a `BODY`. `app.js:2197-2210`, `2227-2235`.
10. El error de escenarios no ofrece reintento explícito y el botón sigue activo durante el cálculo. `app.js:1937-1939`, `2239-2248`.
11. Salto de encabezado `h1` → `h3` en los resultados de biblioteca. `app.js:1379`, `1622-1625`.
12. El chip de estado queda obsoleto tras recuperar: la biblioteca carga 20 tarjetas y el chip sigue diciendo «Servicio local sin respuesta». `app.js:2637-2671`.
13. Envíos duplicados: tres clics producen tres `POST /api/compare` y seis `POST /api/calculate`. `app.js:1769`, `2183`, `2239-2248`.

## Comprobado sin defecto

Sin scroll horizontal de página en 320, 390, 768 y 1280 px en las ocho rutas; el único solapamiento real a 320 px es el stepper. Ningún texto por debajo de 4,5:1 (3:1 en texto grande); mínimo 4,86 en terracota. Foco visible de 3 px en todos los controles recorridos. Cero controles sin nombre accesible. Ayuda contextual: Enter abre, Tab llega a «Cerrar», Escape cierra y devuelve el foco. Sin JavaScript se muestra el aviso `noscript`, no una pantalla en blanco. Las tablas mantienen semántica a 320 px.

## Límites

Emulación de viewport por CDP, no dispositivo físico. El 200 % se aproxima con ventana de 640×450 y con `font-size: 32px`; no se usó lector de pantalla real, ni táctil, ni Safari o Firefox, ni alto contraste del sistema. No se evaluó el flujo del chat ni se reabrió B8. La copia pública `api/_static` reproduce los mismos defectos de skip-link y stepper.

## Artefactos

Informe completo, scripts, JSON y capturas en el directorio temporal del equipo `%TEMP%\b9\` (`B9-INFORME.md`, `probe_*.cjs`, `*.png`). Son artefactos de sesión y pueden limpiarse; lo permanente es este documento y la prueba `tests/b9_accessibility.test.cjs` que crea la corrección.

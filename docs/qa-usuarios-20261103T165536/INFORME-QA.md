# QA exploratoria — resultado consolidado de tres testers

**Objetivo:** usar la web como una persona, especialmente el guardado del informe que Alejandro no puede completar. App: http://127.0.0.1:8765/. Datos ficticios, sesiones aisladas y sin modificar la sesión del usuario ni producción.

## Resultado ejecutivo
No se ha acreditado que el usuario pueda completar el guardado del informe. El módulo prepara el documento y dispara `beforeprint`, pero eso no prueba que aparezca un diálogo utilizable ni que se guarde un fichero. La descarga del adjunto de Hermes es otro flujo: sigue sin diagnóstico y no se considera resuelta por repetir el enlace.

La consolidación prioriza **cuatro asuntos**: uno de prioridad alta por el flujo bloqueado y su verificación inconclusa, dos de severidad media confirmados y uno de claridad de severidad baja. No se presentan como cuatro errores de código demostrados. Recuento y deduplicación en `RESUMEN-QA.json`, generado por `consolidar.py`, con aserciones sobre los archivos de evidencia.

| ID | Prioridad / severidad | Asunto | Estado de evidencia |
|---|---|---|---|
| QA-01 | 1 / alta por impacto | Guardar el informe no es un recorrido acreditado y falta orientación útil tras pulsar | Fallo comunicado por el usuario; destino del diálogo/archivo y causa técnica inconclusos |
| QA-02 | 2 / media | Inicio móvil desborda horizontalmente | Reproducido por tester y coordinador |
| QA-03 | 3 / media | Tabla comparativa no identifica plazos diferentes | Captura y código confirman la omisión |
| QA-04 | 4 / baja | Recarga pierde filtro/selección sin explicar el carácter temporal | Observación de UX; no exige persistencia nueva |

## QA-01 — Guardado y orientación
**Ruta:** /#escenarios. Completar y calcular A y B; pulsar Imprimir / guardar como PDF.

**Esperado:** poder completar el guardado o recibir indicaciones útiles si el entorno no permite abrir impresión. Cancelar no es guardar.

**Observado:** documento preparado y un `beforeprint`; estado visible sigue diciendo que ambos escenarios están actualizados. No se verificó diálogo nativo, cancelación ni archivo guardado. Tras editar/recalcular, la protección de resultados obsoletos funciona; un nuevo clic no produjo otro `beforeprint` observable en la ventana medida. No se sabe si había un diálogo pendiente o supresión del entorno. No se capturó consola completa fiable.

**Causa conocida:** el botón llama `window.print()` y no descarga por sí solo un PDF. **Causa del fallo concreto del host: no establecida.** No se sustituyó window.print ni se generó PDF mediante CDP durante esta QA.

**Recomendación:** comprobar la interacción nativa en navegador completo y panel Hermes; ofrecer una salida de archivo compatible y mensajes claros si no hay impresión. No anunciar éxito de guardado por eventos de impresión. La descarga del adjunto Hermes debe investigarse por separado.

**Evidencia:** `exportacion/report.md`, `exportacion/evidence.json`, capturas `exportacion/screenshots/01-tras-pulsar.png` y `04-reintento.png`. Los originales creados por el worker en prototipos/paideia-local/docs se conservan; se copiaron a esta carpeta para consolidar, sin tocar fuentes.

## QA-02 — Inicio móvil desborda
**Pasos:** abrir Inicio en emulación 390×844; desplazarse hasta los campos ficticios del chat.

**Esperado:** lectura dentro del ancho del viewport.

**Observado:** clientWidth 390, scrollWidth 448, innerWidth 448 y visualViewport 390. Dos spans con cadenas de contexto salen por la derecha: respuestas.objetivo alcanza x=448,17 y detalle_economico.importe_objetivo x=430,11. El coordinador reprodujo las medidas y capturó esa zona; la primera captura de la parte superior no mostraba los spans y no se usa como prueba visual del recorte inferior.

**Recomendación:** permitir ajuste de esas cadenas en el contenedor concreto, no rediseñar la aplicación ni ocultar contenido funcional.

**Evidencia:** `biblioteca-navegacion/evidence.json`, `coordinador/reproduccion-home-formato.json`, `coordinador/home-contexto-desbordado.png`. Biblioteca y diagnóstico sí quedaron en 390/390 en los puntos medidos; eso no absuelve Inicio.

## QA-03 — Plazos distintos sin contexto en el resumen
**Pasos:** calcular un escenario a cinco años y otro a diez; leer solo la tabla de comparación.

**Esperado:** ver los horizontes o un aviso de que no representan el mismo instante.

**Observado:** columnas Escenario, Estado, Aportado, Saldo nominal y Saldo real. Los plazos están en los detalles inferiores, pero no en el resumen. La captura del tester y `static/app.js:1598–1616` lo confirman. El PDF sí contiene la aclaración; no se extrapola su presencia a la pantalla.

**Recomendación:** incluir el plazo de cada fila o una advertencia condicional; no prohibir comparar ni declarar un ganador.

**Evidencia:** `escenarios/evidence.json` y `escenarios/screenshots/comparacion-horizontes.png`.

## QA-04 — Estado temporal poco claro
**Pasos:** filtrar depósitos, seleccionar dos y recargar.

**Observado:** vuelve a todas las familias y a cero seleccionados. La interfaz dice que la selección no cambia sin pulsar, pero no aclara la excepción de recargar.

**Recomendación:** explicar que la selección/filtros son temporales. No hay requisito verificado de persistencia ni autorización para añadir guardado automático por este hallazgo.

**Evidencia:** `biblioteca-navegacion/report.md` y `evidence.json`.

## Hallazgo descartado como defecto
El tester señaló que 2784,43 € no separa miles mientras 18.784,43 € sí. El coordinador comprobó el mismo comportamiento en `Intl.NumberFormat('es-ES')`: es una convención del formateador para cuatro y cinco cifras. No se considera un error financiero ni de cálculo. Si se prefiere agrupar siempre, sería una decisión de presentación, no una corrección obligatoria demostrada.

## Qué funcionó en la exploración
- Cálculo con hipótesis iguales produce valores iguales; edición invalida solo el escenario modificado y deja vigente el otro.
- Resultados se conservaron al navegar y volver dentro de la misma sesión. No implica persistencia tras recargar.
- Validaciones básicas, cero y tasa negativa se pudieron ejercitar; no se verificó cada error en backend ni una respuesta de red pendiente.
- Biblioteca, fichas, selección y comparación mixta se usaron sin perfil ni IA. Los avisos distinguen candidatos y condiciones pendientes; diagnóstico de depósitos expone motivos sin inventar rentabilidades.
- Ayudas y navegación se pudieron usar; no es una auditoría de accesibilidad.

## No comprobado
Guardar/cancelar mediante diálogo nativo; descarga del adjunto Hermes; consola completa; comparaciones finales de tres/cuatro productos; todos los campos, fichas y ayudas; lectores de pantalla, dispositivo físico, carga y proveedores reales. Los screenshots de página no permiten descartar un diálogo nativo fuera de ella.

## Cambios y runtime
No se corrigió código, no se instalaron dependencias ni se habilitaron proveedores. Los testers usaron sesiones propias. El servidor de demo 8765 del coordinador se mantiene para el usuario; no había servidores nuevos que cerrar.

## Siguiente paso
Priorizar una solución de guardado que funcione desde el entorno del usuario, con una prueba real del archivo final. Después, ajuste acotado de cadenas largas en Inicio y aviso de plazos en el resumen. Las correcciones requieren un encargo separado; esta entrega es QA y diagnóstico, no una reparación ya realizada.

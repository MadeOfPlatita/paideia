# Paideia — prototipo local

**Prototipo local navegable verificado.** Frontend HTML/CSS/JS y backend Python stdlib conectados. No hay proveedor LLM conectado, PostgreSQL creado ni publicación cloud; el catálogo solo compara metadatos internos, no condiciones financieras pendientes. La aplicación completa de producción sigue sin terminar.

## IA real — sesión temporal, no producción

La sesión8768 está detenida preventivamente por revisión de seguridad (carrera de revocación/plazo); no se reabre automáticamente. El recorrido real del chat se verificó en8768: calculadora ejecutada y respuesta externa (truncada), más respuesta conceptual breve externa sin truncado. Sesión autorizada por ventana, clave en memoria,24intentos y vencimiento29octubre2026 17:40:20UTC; después no se abre ni envía con este lanzador de misión. El servidor normal8765 sigue sin proveedor. El benchmark A/B/C se detuvo tras su primera petición y no tiene ganador ni evaluación completa.

Código posterior añade diagnóstico sanitizado y brevedad al prompt, probado offline pero no aplicado a la sesión viva sin reiniciar/reintroducir la clave. Evidencia: ../../docs/funcionamiento-05/11-hora-autonoma/05-real/. Última regresión195Python/20Node/19HTTP. La corrección de revocación y del último intento está verificada offline; veredicto independiente final favorable en las rutas revisadas. No se reabre la IA ni se amplía el plazo automáticamente. No perfiles reales, hosting, nuevas ofertas ni aprobación global de calidad.

## Corrección del cuestionario

Doce preguntas consecutivas en tres bloques, sin abrir ramas extra. Continuar bloquea respuestas vacías; No lo sé/Omitir siguen disponibles. Pausa y reanudación desde el primer campo pendiente. Ver PERFIL-FUNCIONAL.md y ../../docs/funcionamiento-05/09-cuestionario/VERIFICACION.md. Regresión actual: 155 Python, 15 Node, 19/19 HTTP; no IA real ni despliegue.

## Estado funcional actualizado — hito previo

Ver `../../docs/funcionamiento-05/08-integracion/REVISION-COORDINADOR.md` y `VERIFICACION.json`: 155 tests Python, 13 Node, 19/19 HTTP y ocho rutas escritorio/móvil. Perfil ampliado opcional, herramientas/orquestación/cupo/cola integrados en la frontera local. IA real y A/B/C sin ejecutar; no se han cargado ofertas numéricas ni desplegado. PostgreSQL no es obligatorio para el catálogo de lectura; snapshot versionado es la propuesta mínima en evaluación. Cuotas de producción necesitan estado durable/coherente independiente.

## Arranque y parada

Desde esta carpeta, con Python ya disponible:

```sh
python app.py --port 8765
```

Abrir `http://127.0.0.1:8765/`. Para parar: Ctrl+C en la terminal que lo ejecuta. No abrir index.html con file://. `iniciar.cmd` facilita el arranque en Windows; no instala nada ni cambia configuración.

## Pruebas

```sh
python -B -m unittest discover -s tests -v
node --check static/app.js
python verify_http.py --base-url http://127.0.0.1:8765 --out evidence/http-green.json
```

La última orden requiere tener el servidor local en marcha. `verify_http.py` rechaza URLs externas. No ejecuta pruebas contra Google, Groq u otros proveedores.

## Alcance y límites

- Web local en español, perfil sin identificadores personales y persistencia local voluntaria.
- API local de metadatos de candidatos, comparación educativa y escenarios deterministas.
- Los veinte candidatos son un inventario de investigación **no listo para publicación**. No son veinte ofertas contratables con condiciones verificadas. Tasas/NAV con permisos pendientes no se exponen como hechos.
- El laboratorio acepta hipótesis del usuario, no pronósticos ni condiciones atribuidas a un banco. Importes brutos, sin fiscalidad ni costes de producto.
- Simulación sin transacción, leads, IBAN, DNI, tarjetas o solicitud comercial; justificante imprimible no es contrato.
- El chat debe mostrar no conectado, no fingir respuestas de IA. La comparación real A/B/C continúa pendiente hasta acceso/autorización del proveedor.
- Snapshot de lectura; no se impone PostgreSQL. APIs como fuente y persistencia/caché son decisiones separadas; no se ha creado DB ni validado un almacén cloud.
- No hay instalación de dependencias, cuentas nuevas, facturación ni despliegue por este prototipo.

## Fuentes internas

El contrato local está en `CONTRATO-LOCAL.md`; alcance aprobado en `../../docs/REQUISITOS.md`; límites de la ronda04 en `../../docs/validacion-04/00-REVISION-COORDINADOR.md`. Los originales se conservan sin modificación.

## Verificación ejecutada

- `python -B -m unittest discover -s tests -v`: 39 tests correctos de dominio, backend HTTP y adaptador perfil05 → proyector04 → materializador03.
- `node --check static/app.js`: correcto.
- `python -B verify_http.py --base-url http://127.0.0.1:8765 --out evidence/http-final.json`: 17/17 comprobaciones correctas sobre servidor real local.
- Navegador real: ocho rutas en escritorio y las mismas ocho en móvil de 390 px. Sin desbordamiento horizontal en la comprobación final; no se afirma auditoría completa de accesibilidad.
- Recorrido probado: perfil de seis preguntas, filtros de ETF, selección de dos candidatos/comparación, escenario negativo con gráfica y tabla, ensayo de cinco pasos con justificante ficticio, vista previa sin peticiones de perfil, opt-in de almacenamiento y borrado confirmado.
- Chat: formulario local requiere confirmación, realiza un único POST con `message` y muestra HTTP 503 sin inventar IA. Se comprobó estado sin red y recuperación. No hubo conexión a Google/Groq.

Resultados: `evidence/tests-final.json`, `evidence/http-final.json`, `evidence/browser-final.json`. Capturas PNG en `evidence/`. La exploración preliminar se conserva y no se cuenta como pruebas finales superadas.

## Correcciones verificadas

1. Metadatos de cálculo: el interés simple ya no se describe como una tasa compuesta efectiva. Regresión roja conservada en `evidence/rate-convention-red.json`; suite final verde.
2. URLs largas: corregido desbordamiento del comparador móvil, de 477 px a 390 px con viewport de 390. Evidencias `mobile-overflow-red.json` y `mobile-overflow-green.json`.
3. Formulario de chat: se construía pero no se montaba en la página. Se reprodujo su ausencia, se añadió al DOM y se verificó consentimiento/503 con `chat-browser-green.json`.

## Límites de esta entrega

- El perfil de la UI tiene seis preguntas; todavía no recoge toda la situación financiera prevista. El adaptador rico se prueba con fixtures sintéticas independientes, no se transmite el perfil del navegador.
- Candidatos reales: inventario interno, no catálogo de ofertas listo para publicación ni comparación cuantitativa.
- No hay IA real configurada, benchmark de calidad, actualización diaria, PostgreSQL, alojamiento público ni prueba de 100 usuarios.
- El justificante es HTML con CSS de impresión; no se ha probado una impresora ni generado un PDF en esta verificación.
- La arquitectura y validación son de prototipo local, no endurecimiento de producción. Revisar privacidad, proveedor, permisos y despliegue antes de publicar.

Informe de QA y alcance: `VERIFICACION.md`.


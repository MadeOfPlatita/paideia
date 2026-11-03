# Paideia — decisiones de publicación, licencias y límites

**Estado:** propuesta para aprobar por Alejandro y José Manuel; no es una decisión ya adoptada. **Uso:** criterio de publicación y lista de bloqueos. No es dictamen jurídico ni sustituye revisión profesional en España.

## 1. Propuesta ejecutiva

1. **Licencia del código propio:** proponer MIT para el código que Paideia controle, pendiente de confirmar titularidad y consentimiento de ambos autores. Es sencilla y permite reutilización amplia, también en derivados cerrados; si el grupo quiere exigir que quien ofrezca una versión modificada por red comparta su código, comparar antes AGPL-3.0. MIT permite usar, modificar, redistribuir y vender el software, sujeto a conservar aviso de copyright y licencia en copias o partes sustanciales.[1] AGPL añade condiciones copyleft y una obligación de ofrecer el código fuente de la versión modificada a quienes la usan por red, según sus términos.[3]
2. **Separar las capas de derechos:** `LICENSE` de Paideia no es una licencia general para tasas, catálogos, bases de datos, fichas/KID/DFI, imágenes, marcas, logos, repositorios secundarios ni servicios de terceros. Registrar derechos por fuente y campo. La licencia MIT/Apache/AGPL de un repositorio solo permite lo que su titular licenciara dentro de ese trabajo; no probar que una ficha o base distinta sea reutilizable.[1][2][3]
3. **Regla de permiso desconocido:** `UNKNOWN / permiso no comprobado` equivale a **no incorporar, cachear, mostrar ni redistribuir el contenido** hasta verificar términos aplicables o recibir autorización escrita. Se puede conservar para revisión una URL, título, fecha de consulta y nota propia; no copiar una ficha, descargar una base ni sustituir el bloqueo con datos inventados. Si un producto real no puede publicarse con derechos verificados, se deja fuera de la comparación hasta resolverlo.
4. **Conservar perfil y personalización educativa:** mantener el perfil individual editable y local, como piden los requisitos; usarlo para adaptar explicaciones, ejemplos didácticos y qué conceptos aclarar. No usarlo en v1 para seleccionar, priorizar, puntuar o asignar productos concretos. Esto no elimina el perfil ni impone ejemplos ficticios como catálogo; mantiene separada la educación personalizada de la selección de producto.[local: REQUISITOS.md, «Perfil» y «Privacidad y operación»; 09-rigor-financiero.md, §§1 y 4]
5. **Producto concreto:** permitir comparación neutral y trazable de productos reales que la persona haya elegido, una vez verificados los derechos de cada campo y su fuente. Mantener datos, costes, fechas, riesgos y filtros explícitos; no decir «mejor para ti», generar una cartera, ni ordenar por el perfil. Un filtro o presentación puede cambiar de naturaleza según cómo funcione; no se declara automáticamente seguro por llamarlo comparador.[5][7]
6. **Antes de recomendaciones personalizadas:** bloquear la publicación de cualquier función que, a partir de ingresos, pérdidas asumibles, horizonte, liquidez, tolerancia o experiencia, recomiende un ISIN/producto, ordene productos, sugiera asignaciones o diga que uno es adecuado para esa persona. Requiere revisión profesional española del flujo real, producto y contexto de distribución; si procede, determinar autorización, entidad y controles necesarios. La Ley 6/2023 define el asesoramiento como servicio de inversión y regula la información de idoneidad en ese supuesto.[5][6] ESMA trata de forma específica si hay recomendación, si se presenta como adecuada, si considera circunstancias, si se dirige exclusivamente al público y el papel de los disclaimers; el acceso público a una web no resuelve por sí solo cada salida personalizada.[7]
7. **Gratuidad y disclaimer:** no concluir que lo gratuito esté universalmente prohibido ni que sea una exención. En las fuentes consultadas no se identifica una prohibición general solo por no cobrar; tampoco se deduce que no cobrar saque una función del análisis. Un disclaimer no cambia el comportamiento efectivo de la función ni basta para aprobar una recomendación personalizada.[5][7]
8. **Datos:** reutilizar estadísticas estándar del Banco de España solo dentro de sus condiciones publicadas: preservar contenido y metadatos, no distorsionar el significado, atribuir, incluir fecha de actualización cuando exista, no implicar apoyo institucional y no extender el permiso a datos de terceros.[4] Para ECB, Tesoro, CNMV, entidades, proveedores comerciales y datos de mercado, la investigación existente no acredita permiso general de cache o redistribución: mantenerlos pendientes hasta revisar los términos exactos por campo.[local: 00-SINTESIS.md, §§2 y 7; 07-repos-similares.md, §§4 y 5]

## 2. Licencias de código: matriz de publicación

| Licencia | Qué puede permitir para el código cubierto | Condiciones y límite relevante | Decisión Paideia |
|---|---|---|---|
| **MIT** | Uso, copia, modificación, combinación, publicación, distribución, sublicencia y venta del software cubierto.[1] | Mantener el aviso de copyright y el texto de permiso en copias o partes sustanciales; se ofrece «tal cual» y excluye garantías en los términos de la licencia.[1] No da por sí sola derechos sobre activos que no estén licenciados por quien controla esos activos. | **Propuesta** para el código original de Paideia, sujeta a aprobación de titulares. Acepta forks cerrados y uso comercial por terceros. |
| **Apache-2.0** | Reutilización, modificación y distribución del código cubierto con una licencia permisiva. | Conservar licencia/avisos, marcar cambios y reproducir avisos de atribución de `NOTICE` cuando exista; la licencia no concede derechos de marca del licenciante.[2] | Aceptarla para una dependencia solo tras inventariar versión, avisos y cambios; no copiar un repositorio completo sin revisión archivo a archivo. |
| **AGPL-3.0** | Ejecutar, modificar y redistribuir trabajos cubiertos bajo las condiciones copyleft. | Si se ofrece por red una versión modificada cubierta, la licencia exige ofrecer a sus usuarios el código fuente de esa versión bajo las condiciones aplicables.[3] Comprobar compatibilidad y alcance antes de combinarla con otros componentes. | No propuesta como licencia inicial, salvo que el grupo quiera expresamente reciprocidad para servicios web y pueda cumplirla. Usar repos AGPL como referencia visual/funcional no incorpora su código. |

**Límite común:** ninguna de estas licencias prueba automáticamente permiso para usar logos/nombres de marca, fichas profesionales, documentos de producto, bases de datos, precios ni datos incluidos en un subdirectorio o submódulo con licencia distinta. Verificar `LICENSE`, `NOTICE`, encabezados, subrepos/submódulos, `data/`, `assets/`, documentación y dependencias transitivas por separado. Apache-2.0 exige conservar avisos de `NOTICE` si los hay; no confundir `NOTICE` con permiso para copiar marcas.[2]

### Atribución y archivos a preparar al aprobar

- `LICENSE`: texto completo de la licencia elegida y titular/año correctos. Confirmar antes qué persona(s) tienen derechos sobre cada contribución; no asignar titularidad por defecto.
- `THIRD_PARTY_NOTICES.md` (o `NOTICE` cuando corresponda): titular, dependencia, licencia, avisos exigidos, modificaciones y ubicación del texto original. MIT no exige un `NOTICE` común, pero conservar los avisos upstream sí es el mínimo; Apache puede exigir avisos de su `NOTICE`.[1][2]
- `DEPENDENCIAS.md` o SBOM exportable: nombre, versión exacta fijada, licencia/SPDX, origen, directa/transitiva, fichero que la introduce, cambios, avisos, fuente de la licencia y responsable de verificación.
- Inventario independiente de datos y assets: URL/propietario, campo o archivo, permiso de acceso/cache/display/derivado/PDF/redistribución, atribución, vencimiento de permiso y fecha de revisión. No etiquetar bases de datos, logos o textos como MIT porque el código que los presenta lo sea.
- No se han instalado ni elegido dependencias en este trabajo. Chart.js/ECharts, Lucide, Motion/CSS y jsPDF aparecen como posibilidades en la síntesis, no como dependencias aprobadas ni como licencias verificadas.[local: 00-SINTESIS.md, §6]

## 3. Frontera de producto: mantener personalización sin prescribir

| Salida | Propuesta para v1 | Límite de publicación |
|---|---|---|
| **Perfil educativo individual** | Conservar objetivo, horizonte, liquidez, conocimientos y datos declarados; adaptar vocabulario, orden de lecciones, ejemplos y simulaciones educativas. Mostrar qué declaró la persona y qué no informó; no inferir huecos. | Perfil local y borrable, como en requisitos. No convertirlo en puntuación de idoneidad, orden de productos o señal para el LLM que elija un producto. Si un proveedor externo recibe datos del perfil, informar y revisar sus condiciones; el almacenamiento local no resuelve la transmisión externa.[local: REQUISITOS.md, §§2, 3 y 5; 09-rigor-financiero.md, §2] |
| **Comparador de productos reales** | La persona elige productos/familia y criterios; comparar campos verificados en paralelo y explicar TAE/TIN/TIR, costes, liquidez y riesgos con fuente/fecha. No afirmar equivalencia entre familias ni omitir condiciones. | No mostrar el campo si su permiso, fuente, clase o vigencia no está comprobado. No ordenar por el perfil ni inferir «ganador». Revisar profesionalmente cualquier filtro/orden que pueda parecer selección personal.[5][7] |
| **Educación sobre un producto concreto** | Explicar qué significa un campo o documento de un producto real que la persona abrió, usando información autorizada y citada, sin valorar si le conviene a esa persona. | No transformar una explicación individual en recomendación («encaja contigo», «compra», «elige», asignación o sustitución). Si la respuesta usa perfil para valorar adecuación, bloquear y remitir a revisión.[5][6][7] |
| **Recomendación individual** | Ninguna en v1. | Bloqueo hasta revisión regulatoria profesional y decisión documentada del equipo. El cuestionario de conocimientos, capacidad de pérdidas, situación financiera y objetivos/tolerancia es propio del análisis de idoneidad cuando se presta asesoramiento; no es solo una preferencia de interfaz.[6] |
| **Simulación** | Mantener la simulación sin órdenes ni contratación real, claramente rotulada. El cálculo ilustrativo puede usar parámetros que la persona introduzca y explicar supuestos. | Los valores ficticios pueden usarse en test o en una escena que el grupo apruebe como simulada; no sustituir por ellos el catálogo de productos reales ni inventar condiciones contractuales.[local: REQUISITOS.md, §§32–41; 09-rigor-financiero.md, §§3 y 5] |

La Ley 6/2023 excluye de la definición citada ciertas recomendaciones genéricas no personalizadas, pero advierte que pueden ser comunicaciones comerciales; el alcance de una función depende de su contenido y contexto. La misma ley enumera conocimientos/experiencia, situación financiera —incluida capacidad de soportar pérdidas— y objetivos —incluida tolerancia al riesgo— para idoneidad cuando se presta asesoramiento.[5][6] No usar «accesible gratis en internet» o «no es asesoramiento» como atajo para clasificar un output individual.[7]

## 4. Bloqueos y aprobaciones pendientes

| Decisión pendiente | Responsable/condición para cerrar |
|---|---|
| MIT u otra licencia y titularidad de cada contribución | Alejandro y José Manuel confirman titularidad y eligen por escrito. |
| Archivos/repo externos que realmente se copiarán | No hay selección acordada. Lista por archivo, licencia, avisos y compatibilidad antes de copiar. |
| Derechos de cada proveedor/campo/producto, incluidos datasets y fichas profesionales | Revisar términos/licencias o recibir autorización explícita para acceso, caché, display, PDF/redistribución y retención. No basta que el dato esté en una web o en un API. |
| Tiempos de caché/retención por fuente | Definirlos con los términos de la fuente; si no los aclaran, solicitar permiso. No fijar una retención universal. |
| Uso externo de perfil/LLM y retención del proveedor | Revisar antes de transmitir datos personales/financieros. Mantener perfil local; no exportarlo por defecto ni guardarlo en logs del proyecto. |
| Comparación filtrada versus ranking por perfil | Conservar selección manual neutral; revisar el diseño concreto si una regla usa perfil o produce ranking. |
| Recomendación perfil→producto concreto | Consulta profesional española antes de publicar; clasificar servicio/productos, presentación, canal y requisitos aplicables. No es dictamen vinculante.[5][6][7] |

## 5. Puerta de desbloqueo para publicar

Marcar una función como `PUBLICABLE` solo si se cumplen todos los puntos aplicables:

- Cada campo mostrado tiene fuente identificable, producto/clase exacta, valor/unidad, fecha de consulta y fecha efectiva, calidad/antigüedad y estado de permiso.
- Los permisos separan **acceder**, **cachear**, **mostrar**, **transformar**, **exportar a PDF** y **redistribuir**; donde el permiso sea desconocido, el campo queda bloqueado y se enlaza a la fuente original sin copiar contenido.
- Se conserva atribución y cualquier aviso/`NOTICE`; dependencias directas y transitivas están inventariadas con versión fijada.
- Perfil y comparador no generan una decisión de idoneidad ni recomendación individual sin revisión profesional documentada.
- El perfil no se borra ni se reemplaza por datos inventados como atajo. Se mantiene local/borrable y su uso didáctico sigue explícito.
- Las decisiones y autorizaciones no se presentan como aprobadas hasta que el grupo las firme; este documento no constituye autorización de datos ni dictamen legal.

## Fuentes y documentos de contexto

Fuentes primarias con extractos literales en `evidencia.json`. Contexto de proyecto: [REQUISITOS.md](../../REQUISITOS.md), [00-SINTESIS.md](../../investigacion/00-SINTESIS.md), [07-repos-similares.md](../../investigacion/07-repos-similares.md) y [09-rigor-financiero.md](../../investigacion/09-rigor-financiero.md).

## Sources

[1] https://opensource.org/license/mit — The MIT License (OSI)
    > "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."
    > "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software"
    > "THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED"
[2] https://www.apache.org/licenses/LICENSE-2.0.txt — Apache License 2.0
    > "If the Work includes a "NOTICE" text file as part of its distribution, then any Derivative Works that You distribute must include a readable copy of the attribution notices contained within such NOTICE file"
    > "This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work and reproducing the content of the NOTICE file."
    > "Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works in Source or Object form."
[3] https://www.gnu.org/licenses/agpl-3.0.txt — GNU Affero General Public License v3
    > "It requires the operator of a network server to provide the source code of the modified version running there to the users of that server."
[4] https://www.bde.es/wbe/en/estadisticas/recursos/terminos/terminos-de-uso.html — Banco de España — Terms of Use of Statistics
    > "The Banco de España must always be cited as the source, in one of the following ways:"
    > "However, this policy does not imply a right to access confidential data nor does it apply to third-party data."
    > "The content of the information and its metadata may not be altered."
    > "The meaning of the information may not be distorted."
    > "The date of the last update of the reused information must be mentioned, whenever it is available in the original."
[5] https://boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2023-7053/texto/bloque/a1-37 — BOE — Ley 6/2023, artículo 125
    > "No se considerará que constituya asesoramiento, a los efectos de lo dispuesto en este apartado, las recomendaciones de carácter genérico y no personalizadas que se puedan realizar en el ámbito de la comercialización de valores e instrumentos financieros. Dichas recomendaciones tendrán el valor de comunicaciones de carácter comercial. Asimismo, tampoco se considerará recomendación personalizada las recomendaciones que se divulguen exclusivamente al público."
[6] https://boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2023-7053/texto/bloque/a2-16 — BOE — Ley 6/2023, artículo 204
    > "obtendrá la información necesaria sobre los conocimientos y experiencia del cliente o posible cliente en el ámbito de inversión correspondiente al tipo concreto de producto o servicio, su situación financiera, incluida su capacidad para soportar pérdidas, y sus objetivos de inversión incluida su tolerancia al riesgo"
[7] https://www.esma.europa.eu/sites/default/files/2023-07/ESMA35-43-3861_Supervisory_briefing_on_understanding_the_definition_of_advice_under_MiFID_II.pdf — ESMA — Supervisory briefing on definition of advice under MiFID II (2023)
    > "Perimeter issues around the definition of personal recommendation, including disclaimers to the client and failing to use known client information in an attempt to try avoiding the qualification as investment advice."
    > "This supervisory briefing might also be used to analyse whether a non-regulated person or entity is engaged in an activity that could be qualified as investment advice (as defined by MiFID II) and they may therefore require an authorisation."
    > "Is the recommendation presented as suitable?"
    > "Is the recommendation issued otherwise than exclusively to the public?"

# Ofertas bancarias españolas: fichas primarias e importadores acotados

**Comprobación:** 26-10-2026, hora local.[1][2][3]
Alcance: fuentes oficiales públicas, lectura anónima; sin alta, credenciales, pago ni instalación.[1][2][3]
Se priorizan cuatro vías, pero solo se probaron tres fuentes directas.[1][2][3]

## Decisión

La vía de coste cero viable es un catálogo pequeño basado en fichas contractuales PDF y páginas oficiales, con normalización y aprobación humana; en esta muestra no apareció una API/CSV/JSON pública documentada para ofertas comerciales individuales.[1][2][3]
Las tres solicitudes directas devolvieron un PDF o HTML, no un feed de productos; el resultado no demuestra que ningún proveedor tenga una integración privada o no documentada.[1][2][3]

**No confundir:** MyInvestor enlaza una descarga Excel de movimientos de una cuenta de cliente; no es una tabla pública de ofertas.[2]
El dossier general del proyecto ya documenta CSV/SDMX del Banco de España y BCE como series estadísticas agregadas, no como condiciones de una cuenta o depósito individual (`docs/investigacion/01-cuentas-depositos.md`).

No se obtuvo permiso explícito para automatización, conservación de snapshots o redistribución; el acceso de lectura usado aquí no se trata como autorización de producción.[unverified]

## Prioridad de importación

| Prioridad | Entidad / oferta real observada | Ruta primaria | Importador viable hoy | Límite importante |
|---|---|---|---|---|
| 1 | **Renault Bank — Cuenta Contigo y Depósito Tú+** | PDF precontractual oficial de 6 páginas, descargado y extraído; cubre elegibilidad, remuneración, cancelación, renovación y FGDR.[1] | Extracción PDF → propuesta de campos → revisión humana. Vigilar PDF/tarifario solo después de revisar permiso. | El PDF no contiene un cap de saldo remunerado ni una tabla completa de los tipos actuales del Depósito Tú+; indica que los tipos del depósito se consultan al contratar. No convertir el límite del fondo de garantía en cap comercial.[1] |
| 2 | **MyInvestor — Cuenta corriente remunerada** | Página oficial HTML con oferta, cap, cadencia, liquidez y enlace a bases legales PDF `https://cdn.myinvestor.es/public/legal/BBLL_cuenta_remunerada_post-sep26.pdf`.[2] | Parser de contenido visible solo como borrador; control humano contra el PDF legal antes de publicar. | Una misma página contiene una promo de 6 meses, tramos por inversión y un FAQ con condiciones anteriores. No extraer el primer porcentaje encontrado como si fuera una única tarifa vigente.[2] |
| 3 | **Trade Republic — remuneración de efectivo** | Página oficial `es-es/interes`; GET anónimo dio HTTP 200, pero el HTML visible extraído solo expone el titular «3,04 % TAE».[3] | Solo extracción humana/contraste con documentación legal accesible sin login. No automatizar el titular como ficha completa. | En el HTML probado no se observaron cap, elegibilidad, vigencia, nómina, plazo, penalización ni FGD; no se verificó que residentes españoles puedan acceder a esa condición concreta.[3] |
| 4 | **Openbank — depósito a 6 meses** | El registro de investigación anterior del repositorio incluye el PDF oficial `https://www.openbank.es/assets/static/pdf/Productos/302_923_31_Deposito_6/302_923_31_Deposito_6.pdf`; no se volvió a solicitar en esta ronda. | Importador PDF-first con revisión humana, una vez descargada y validada la versión actual. | **Candidato pendiente, no condición actual verificada aquí.** No copiar tipos o vigencias del registro anterior al catálogo vivo sin comprobar el PDF actual. |

ING, Bankinter, N26 y Revolut no se probaron en esta tanda por el límite de tres fuentes directas; su ausencia no significa que no publiquen fichas o integraciones.[unverified]

### Condiciones capturadas en la fuente primaria

**Renault Bank — Cuenta Contigo.** La ficha permite contratar a personas mayores de 18 años con residencia fiscal en España y sin obligaciones fiscales en otro país; exige un solo titular y que los ingresos procedan de una cuenta española propia.[1]
No exige nómina en el texto revisado.[1]
La cuenta no cobra comisiones y su cancelación es gratuita, salvo que siga vinculada a otro producto que requiera mantenerla abierta.[1]

Para nuevas contrataciones entre el **21-10-2026 y el 18-11-2026**, la ficha anuncia **2,61 % TAE**, calculada con **3,00 % TIN hasta el 31-03-2027**; desde el 01-04-2027 el TIN será el que la entidad comercialice entonces, no una promesa de mantener el 3,00 %.[1]
Para clientes que contrataron hasta el 20-10-2026, la ficha separa el régimen general de **2,27 % TAE**, vigente hasta el 03-11-2026.[1]

El documento no fija una frecuencia universal de abono: dice que se pacta al contratar.[1]
El interés se calcula sobre saldo diario.[1]
La entidad identifica el fondo francés FGDR y la cobertura de hasta **100.000 € por titular y entidad**.[1]

**Renault Bank — Depósito Tú+.** Es un depósito a plazo, pero la ficha no proporciona una tabla de tipos TIN/TAE aplicables a cada plazo: remite a las condiciones vigentes en la web y al proceso de contratación.[1]
Indica que no se permite cancelación anticipada; la renovación es automática por el mismo plazo al tipo que esté publicado en el vencimiento, con posibilidad de oponerse a ella.[1]
No se deben inventar tramos, plazo mínimo/máximo o penalización monetaria donde el PDF no los especifica.[1]

**MyInvestor — Cuenta remunerada.** La cabecera de la página ofrece **2,5 % TAE durante los primeros seis meses**, sin comisiones, nómina ni requisitos, y la página indica saldo máximo remunerado de **70.000 €**, liquidación mensual y disponibilidad del dinero.[2]
Identifica el FGD español, hasta 100.000 € por titular y entidad.[2]

La misma página contiene una condición posterior para cuentas abiertas desde el 01-09-2026 (2,50 % TAE seis meses y luego 0,30 % TAE desde el séptimo), además de un bloque que muestra tipos condicionados a invertir 300/600/900 €/mes.[2]
También conserva un FAQ que dice 1,25 % TAE el primer año y 0,30 % desde el segundo.[2]
Es una inconsistencia visible de contenido: el importador debe guardar los bloques por separado y dejar la tarifa en revisión hasta contrastar el PDF legal enlazado; no mezclar campaña, tramos de inversión y FAQ anterior.[2]

**Trade Republic — efectivo.** El titular de la página probada dice **3,04 % TAE sobre el efectivo**.[3]
El cuerpo HTML capturado no aporta condiciones suficientes para completar una ficha minorista ni comprobar el alcance español.[3]

## CSV, JSON y feeds: resultado acotado

En las páginas/artefactos oficiales probados no encontré una tabla pública de tipos de producto en CSV/JSON ni documentación de un feed de ofertas.[1][2][3]
Lo que sí hay aquí son documentos PDF y páginas HTML; las páginas públicas no constituyen por sí solas permiso de extracción o redistribución.[1][2][3]

El Excel de MyInvestor es una exportación de movimientos de la cuenta del propio cliente desde la app; no lo trataría como catálogo público ni como feed de precios.[2]
Para series agregadas oficiales, reutilizar el análisis del Banco de España/BCE en el dossier existente y mantenerlas fuera de `offers`: sus tasas no sustituyen la TAE/TIN contractual de una oferta individual.[unverified]

## Esquema recomendado en PostgreSQL

### Propuesta de columnas/relaciones para PostgreSQL (esquema de importación, no datos de oferta)

```text
provider, legal_entity, brand, product_name, product_type, currency
country_eligibility, tax_residency, holder_count, age_min
offer_tier(balance_min, balance_max, TIN, TAE, rate_kind, condition_type, condition_threshold)
offer_tier(valid_from, valid_to, promo_duration, after_promo_rate, after_promo_condition)
deposit(term_days/months, minimum_opening, maximum_opening, early_cancellation, auto_renewal)
fees, interest_payout_frequency, guarantee_scheme, guarantee_country, guarantee_limit, limit_basis
source_url, document_title, document_version, effective_date, checked_at, source_valid_from, source_valid_to
snapshot_path/hash, parser_version, human_review_status
```

Si el documento no da un campo, almacenarlo como `unknown`/`null` más una nota, nunca como cero o como “sin condición”.
Para fechas, distinguir `checked_at` (cuándo consultó Paideia) de `source_valid_from/source_valid_to` (vigencia declarada por el banco).
La fecha de consulta diaria no cambia por sí sola la fecha de vigencia de la oferta.

## Importadores factibles sin prometer cobertura

1. **PDF contractual (Renault; Openbank tras revalidar):** lista permitida de URLs oficiales → descarga manual o controlada → guardar el PDF original → extraer texto/tablas → cargar una propuesta a staging → cotejo humano de los campos de dinero, fecha y garantía → publicar solo la versión aprobada.[1]
El `TAE/TIN` del depósito Tú+ se obtiene de la oferta efectiva al contratar, no de su ficha global.[1]
2. **HTML + PDF de bases (MyInvestor):** extraer secciones identificadas de la página, guardar URL y captura de fecha, y leer las bases legales enlazadas para resolver la divergencia.[2]
El parser puede proponer valores, pero no actualizar el catálogo público sin revisión.[2]
3. **Página dinámica/insuficiente (Trade Republic):** mantener la URL como punto de verificación humana; el GET de HTML probado no es un importador de ficha completa.[3]
4. **Monitorización, no “cambio diario”:** después de comprobar términos y derechos, un proceso diario podría registrar `last_checked_at`, encabezados si existen y hash/diff del documento para abrir una tarea de revisión.
Solo se marca un cambio de oferta cuando el documento/condiciones comparadas lo acreditan; una comprobación diaria sin cambio no convierte una tasa en diaria ni garantiza que el banco haya cambiado la oferta.

## Pruebas de lectura realizadas

Se hicieron **tres solicitudes públicas** de URLs distintas, sin autenticación ni reintentos tras obtener respuesta: un PDF de Renault Bank y páginas HTML de MyInvestor y Trade Republic.[1][2][3]
El tamaño de la respuesta MyInvestor fue 903.286 bytes; conviene usar peticiones condicionadas y límites de tamaño antes de programar cualquier monitor.[2]

| URL | Resultado / tipo | Campos observados | Evidencia cruda y extracción |
|---|---|---|---|
| Renault Bank, información precontractual | HTTP 200; `application/pdf`; 159.434 bytes.[1] | Elegibilidad España/edad/titular; Cuenta Contigo con TAE/TIN y fechas de promoción; gastos/cancelación; Depósito Tú+ sin cancelación anticipada y renovación; FGDR francés.[1] | `docs/investigacion-apis-02/evidence/renault-precontractual.pdf` y `renault-precontractual-utf8.txt` |
| MyInvestor, cuenta remunerada | HTTP 200; `text/html; charset=utf-8`; 903.286 bytes.[2] | 2,5 % TAE/6 meses; cap 70.000 €; no nómina/no comisiones; abono mensual; FGD; bloques de FAQ contradictorios.[2] | `docs/investigacion-apis-02/evidence/myinvestor-account.html` y `myinvestor-account.txt` |
| Trade Republic, interés | HTTP 200; `text/html; charset=utf-8`; 58.315 bytes.[3] | Solo el titular con 3,04 % TAE; no se observaron el resto de campos contractuales en el HTML visible.[3] | `docs/investigacion-apis-02/evidence/trade-republic-interest.html` y `trade-republic-interest.txt` |

**Resultado de producto:** dos páginas/documentos primarios contienen suficientes condiciones para iniciar una importación controlada; Trade Republic requiere comprobación humana adicional y Openbank sigue siendo un objetivo de prueba, no un dato vigente confirmado.[1][2][3]
No se ha demostrado cobertura de mercado del 90 % ni se ha prometido.

## Sources

[1] https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf — Información precontractual global - Renault Bank
[2] https://myinvestor.es/cuentas-tarjetas/cuentas — Cuenta corriente remunerada - MyInvestor
[3] https://traderepublic.com/es-es/interes — Interés sobre efectivo - Trade Republic

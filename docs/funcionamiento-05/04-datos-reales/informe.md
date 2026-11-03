# Cierre de brechas del catálogo real

**Corte de recuperación:** 2026-10-28. **Estado:** borrador local; no publicado, no integrado ni cargado en la aplicación.

## Resultado medible

- **20 candidatos**, 4 por familia. Los 14 estados originales `verified` y 6 `proposed` se mantienen auditables; identidad real no significa condiciones completas ni oferta lista para comparar.
- Las propuestas ACC-03, ACC-04 y DEP-03 quedaron verificadas por lectura primaria.[3][4][6]
- DEP-04, FND-03 y FND-04 también quedaron verificadas por páginas primarias.[7][11][12]
- `facts-draft.json`: **62** observaciones numéricas compatibles con `catalogue_facts.Fact` (45 `known`, 17 `conflict`), **43** pares candidato/campo con observación numérica en esta ronda, repartidos en **16/20** candidatos. Se conservaron **17** observaciones numéricas previas con recuperación solo por fecha; no se inventó hora para convertirlas a `retrieved_at`.
- `brechas-no-numericas.csv`: **20** filas, una por candidato, con identidad, condiciones observadas, fechas/conflictos, huecos y bloqueo de suficiencia.
- **0/20 candidatos y 0/5 familias están listos para comparación cuantitativa/publicación.** Todas las acciones de reutilización (lectura automatizada, copia/cache, transformación, display, redistribución raw, PDF y retención) siguen `pending`; la lectura pública puntual no resuelve permisos y no constituye opinión legal.
- Presupuesto: **20 asignaciones dirigidas** (una por candidato), 16 URLs actuales distintas y 17 intentos; hubo un fallo del extractor EBN seguido de una lectura normal de navegador. No hubo búsquedas genéricas, WAF/auth/TLS bypass ni descargas de históricos o holdings. Ese fallo se recuperó dentro del máximo de dos intentos para esa fuente.

| Familia | Candidatos | Facts numéricos actuales | Pares candidato/campo | Candidatos con observación actual | Suficiente para comparar |
|---|---:|---:|---:|---:|---:|
| Cuenta remunerada | 4 | 17 | 12 | 4 | 0/4 |
| Depósito | 4 | 26 | 12 | 3 | 0/4 |
| Letra de deuda pública | 4 | 4 | 4 | 4 | 0/4 |
| Fondo tradicional | 4 | 8 | 8 | 2 | 0/4 |
| ETF UCITS | 4 | 7 | 7 | 3 | 0/4 |
| **Total** | **20** | **62** | **43** | **16** | **0/20** |

## Campos decisivos y conflictos conservados

- **Cuentas.**
  - Renault Bank: el extracto recuperado muestra 2,27 % TAE con condiciones hasta 20/10; el extracto previo guarda una promoción 2,61 % TAE del 21/10 al 18/11 y TIN hasta 31/03/2027. Se mantienen como intervalos distintos, no se empalman.[1]
  - MyInvestor mezcla tramos condicionados, 2,50 % durante seis meses, 1,25 % durante un año para otra cohorte y 0,30 % posterior; no se escogió una lectura y las bases legales actuales no se recuperaron.[2]
  - Openbank anuncia 3,25 % TAE/3,20 % TIN durante un año por Bizum y para nuevos clientes; el bono por recibos no se incorporó a la tasa.[3]
  - Pibank conserva el conflicto literal entre 0,00 % TIN en el ejemplo y 2,00 % TIN en la FAQ, con 2,02 % TAE en ambos bloques.[4]
- **Depósitos.**
  - La ficha oficial Openbank es Depósito Open 6 Meses, vigente desde 08/10/2026; 3,25 % TAE/3,22 % TIN depende de mantenerlo seis meses y cumplir ingresos. La fila YieldMeister sigue diciendo 12m; ambos registros permanecen separados.[5][17]
  - El depósito Pibank es de 12 meses, 3,03 % TAE/3,00 % TIN, oferta hasta 31/10 y rescate que descuenta intereses abonados; no se extrapoló más allá de esa fecha.[6]
  - En EBN se guardaron TAE/TIN por plazo y el encabezado «hasta 2,85 %» sin tenor; la tabla incluye 3,10 % a 48 meses, por lo que no se asignó el techo a un plazo ni se inventó vigencia.[7]
- **Deuda pública.** La tabla del Tesoro identifica ISIN y vencimientos, pero es una tabla de valores en circulación, no una oferta de subasta ni una cotización.[8] La lectura nueva da importes vivos de 8.028,8 y 6.713,1 millones EUR para DEBT-01/04, mientras el snapshot previo con fecha efectiva 16/10/2026 conserva 8.780,5 y 9.010,2; como el extracto nuevo no retuvo el pie de fecha, la diferencia queda abierta.[8] No hay precio, yield ejecutable ni resultado de subasta trazado a esos ISIN en la evidencia reunida.
- **Fondos.**
  - La ficha CNMV de OLEA acredita identidad/registro y fechas documentales, no disponibilidad minorista ni NAV.[10]
  - Azvalor expone 1,80 % de comisión de gestión y mínimos de suscripción, pero no NAV fechado ni SRI.[11]
  - Para Bestinver Internacional se retienen NAV 78,69 € sin fecha en página directa y 77,19 € sin fecha en snippet previo; no se elige uno.[12]
  - El NAV 140,3 € de Bestinver Bolsa a 23/10 procede del extracto primario previo; la relectura no volvió a exponer ese bloque.[9]
- **ETF UCITS.**
  - El KID iShares identifica la clase EUR Acc y fecha 03/09/2026; SRI 4/7 viene del extracto previo. Los costes 0,12 % recurrente/0,01 % operación solo están en el campo estructurado previo, sin cita primaria literal guardada, y quedan marcados como tales.[13]
  - DWS publica NAV 104,46 USD/TER 0,15 % a 23/10 y también una NAV de 93,23 EUR a esa fecha sin mapping inequívoco a la clase del candidato; solo se asignó el valor USD.[14]
  - State Street conserva NAV oficial 424,41 EUR y cierre de mercado 424,85 EUR como campos distintos, ambos al 27/10; NAV no se trató como precio.[15]
  - VanEck publica NAV USD 102,82 y TER 0,35 % a 27/10; se excluyó el retorno YTD y se dejó pendiente el SRI/KID español.[16]

## Bloqueos exactos para poder comparar

1. **Cuentas:** reconciliar MyInvestor con bases legales y cohorte; confirmar fecha efectiva de promociones, TIN y saldo máximo/moneda contractual donde falten; conocer tasa postpromoción y requisitos individuales; mantener como conflicto el TIN de Pibank.
2. **Depósitos:** obtener ficha vigente, plazo común y condiciones de bonificación/cancelación comparables; DEP-01 no tiene tarifas por tenor; confirmar vigencia tras 31/10 para Pibank; resolver cabecera/tabla EBN y conflicto Openbank/YieldMeister.
3. **Deuda:** asociar por ISIN fecha de emisión, convocatoria/resultado de subasta, precio/yield adjudicado y, si existe, cotización secundaria fechada; no convertir saldo vivo en precio ni rendimiento.
4. **Fondos/ETF:** completar NAV con efectiva, clase/divisa, KID/SRI y costes totales; para ETF conservar separados NAV oficial, NAV indicativo y precio de mercado. No comparar NAV absolutos de fondos distintos como rendimiento ni presentar rentabilidad pasada como futura.
5. **Todos:** falta verificación de permisos por acción; no existe política TTL/frescura aprobada. Los hechos permanecen `production_candidate` por identidad real, no como oferta publicable.

## Artefactos y límites

- `facts-draft.json` contiene valores numéricos decimales en `facts`; identidad, fechas, condiciones y gaps están en `candidates`, `fact_metadata`, `prior_numeric_observations` y el CSV. Los 17 registros previos con fecha de recuperación sin hora no se normalizaron a medianoche. No se definió TTL.
- `evidence/source-excerpts.md`, `evidence/source-evidence-manifest.json`, `evidence/retrieval-log.json` y `evidence/sources-ledger.json` son exclusivos de esta tarea. El ledger usa IDs propios y cruza los IDs de fuentes originales; las citas de este informe se renderizaron desde ese ledger.
- No se modificó `candidatos.json`, no se cargó catálogo en la app, no se creó DB/credencial/instalación/despliegue y no se copiaron históricos de NAV/holdings.

## Sources

[1] https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf
    > "La remuneración del dinero que tengas en la cuenta “Contigo” será de un tipo de interés del 2,27% TAE."
    > "Promoción aplicable exclusivamente a nuevos clientes que contraten la Cuenta Contigo entre el 21/10/2026 y el 18/11/2026, ambos inclusive."
[2] https://myinvestor.es/cuentas-tarjetas/cuentas
    > "Durante los primeros 6 meses desde la fecha de apertura: 2,50 % TAE (2,472 % TIN)."
    > "A partir del séptimo mes: 0,30 % TAE (0,300 % TIN)."
    > "Durante los primeros 12 meses desde la apertura: 1,25 % TAE (1,243 % TIN anual)."
    > "1,75 % TAE"
    > "Si inviertes 600 € al mes."
    > "Si inviertes 300 € al mes."
    > "Para un saldo máximo de 70.000 €."
    > "Si inviertes 900 € al mes: 2,5 % TAE."
    > "1,25 % TAE"
    > "Cuentas abiertas desde el 1 septiembre de 2026:"
[3] https://www.openbank.es/cuenta-remunerada
    > "3,25% TAE1 y 3,20% TIN"
    > "Durante todo un año por traer Bizum."
[4] https://www.pibank.es/cuenta-remunerada
    > "Interés nominal anual 0,00% (TAE 2,02%) calculado a 1 año"
    > "la Cuenta Remunerada Pibank se aplica al 2,02% TAE (2,00% TIN)"
[5] https://www.openbank.es/assets/static/pdf/Productos/302_923_31_Deposito_6/302_923_31_Deposito_6.pdf
    > "Vigente desde 08.10.2026"
    > "En caso de que los fondos se mantuvieran depositados íntegramente en el depósito durante 6 meses"
    > "El importe mínimo para la contratación es de 1 euro."
[6] https://www.pibank.es/deposito-bancario-plazo-fijo
    > "Tipo de interés nominal anual 3,00% (3,03% TAE) aplicable durante 12 meses. Oferta válida hasta el 31/10/2026."
    > "Sin importe mínimo ni máximo"
[7] https://www.ebnbanco.com/ahorro/deposito-sinycon-plus
    > "2,75% TAE* (2,72% TIN) A 12 MESES"
    > "2,40% TAE (3 meses)"
    > "2,40% TAE (3 meses): Por ejemplo, para un depósito a 3 meses, con una TAE del 2,40% (2,38% TIN) y por un importe de 5.000 €, los intereses que recibirá en total ascenderían a 29,75€ brutos."
    > "2,50% TAE (6 meses): Por ejemplo, para un depósito a 6 meses, con una TAE del 2,50% (2,48% TIN) y por un importe de 5.000 €, los intereses que recibirá en total ascenderían a 62,00€ brutos."
    > "2,75% TAE (12 meses): Por ejemplo, para un depósito a 12 meses, con una TAE del 2,75% (2,72% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 136,00€ brutos."
    > "2,75% TAE (18 meses): Por ejemplo, para un depósito a 18 meses, con una TAE del 2,75% (2,72% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 204,00€ brutos."
    > "2,80% TAE (24 meses): Por ejemplo, para un depósito a 24 meses, con una TAE del 2,80% (2,77% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 277,00€ brutos."
    > "2,80% TAE (36 meses): Por ejemplo, para un depósito a 36 meses, con una TAE del 2,80% (2,77% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 415,50€ brutos."
    > "2,90% TAE (42 meses): Por ejemplo, para un depósito a 42 meses, con una TAE del 2,90% (2,87% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 502,25€ brutos."
    > "3,10% TAE (48 meses): Por ejemplo, para un depósito a 48 meses, con una TAE del 3,10% (2,97% TIN) y por un importe de 5.000€, los intereses que recibirá en total ascenderían a 612,25€ brutos."
[8] https://www.tesoro.es/en/deuda-publica/valores-del-tesoro/valores-en-circulacion
    > "ES0L02701156 | 01/15/2027 | 8,028.8"
    > "ES0L02702055 | 02/05/2027 | 8,597.1"
    > "ES0L02703053 | 03/05/2027 | 8,623.1"
    > "ES0L02704093 | 04/09/2027 | 6,713.1"
    > "Data as at 10/16/2026. The outstanding amount for each reference is updated on its corresponding settlement date."
[9] https://www.bestinver.es/fondos-de-inversion/bestinver-bolsa
    > "Valor liquidativo: 140,3 €"
[10] https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447
    > "4231 | 14/05/2010 | ES0118537002 | 01/10/2026"
[11] https://www.azvalor.com/fondos-de-inversion/azvalor-internacional
    > "Comisión de gestión 1,80% anual sobre patrimonio"
    > "suscripción mínima 5.000€ (500€ para menores de 25 años)"
[12] https://www.bestinver.es/fondos-de-inversion/bestinver-internacional
    > "Valor liquidativo: 78,69 €"
[13] https://www.blackrock.com/es/profesionales/literature/kiid/eu-priips-ishares-core-msci-europe-ucits-etf-eur-acc-ie00b4k48x80-es.pdf
    > "La fecha de este documento es 03 septiembre 2026."
    > "Hemos clasificado este producto en la clase de riesgo 4 en una escala de 7"
[14] https://etf.dws.com/en-lu/IE000CXLGK86-s-p-500-equal-weight-ucits-etf-2d
    > "NAV (23.10.2026): 104.46 USD All-in-fee (TER): 0.15%"
    > "NAV, As of 23.10.2026"
[15] https://www.ssga.com/se/en_gb/intermediary/etfs/state-street-spdr-msci-europe-industrials-ucits-etf-stq-fp
    > "NAV EUR (Official NAV) €424,41 as of 27 Oct 2026"
    > "TER | 0,18%"
    > "Closing Price | €424,85"
[16] https://www.vaneck.com/uk/en/investments/semiconductor-etf/overview?al=en&audience=retail&disclaimer=true
    > "NAV $102.82 as of 27 Oct 2026"
    > "Total Expense Ratio 0.35%"
    > "Main Risk Factors: Liquidity risks, equity market risk, industry or sector concentration risk."
[17] https://yieldmeister.com/api/v1/rates
    > "Depósito Plazo Fijo 12m"

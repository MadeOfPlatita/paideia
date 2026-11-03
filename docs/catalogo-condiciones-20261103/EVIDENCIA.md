# Condiciones verificadas — lectura del 3/11/2026

Lectura directa de páginas oficiales para sustituir literales ambiguos del snapshot. Cada fila conserva URL, fecha de consulta y el literal de la fuente. No se copian documentos completos ni se redistribuyen.

## Depósito Open 6 meses — Openbank

- Fuente: https://www.openbank.es/deposito-a-plazo-fijo · consultada 2026-11-03.
- Producto: depósito a plazo fijo de **6 meses**, desde 1 €, sin máximo y sin comisiones.
- Tasa con nómina o ingreso mensual ≥ 900 € mantenido al menos 4 meses: **3,25 % TAE / 3,22 % TIN**.
- Tasa sin domiciliar nada: **2,75 % TAE / 2,73 % TIN**.
- Cancelación anticipada: remunera al **0,20 % TAE / 0,20 % TIN** por el tiempo mantenido.
- Garantía: FGD español, 100.000 € por titular y entidad. Indicador de riesgo 1/6.
- Lo que la página **no** fecha: vigencia de las tasas. No se presenta como «actual» sin fecha efectiva.
- Incidencia resuelta: el snapshot arrastraba un conflicto con un agregador que lo describía a 12 meses; la fuente oficial dice **6 meses**. Se conserva la observación del conflicto, ya no se usa el dato del agregador.

## Depósito Pibank 12 meses — Pibank (Banco Pichincha España)

- Fuente: https://pibank.es/deposito-bancario-plazo-fijo · consultada 2026-11-03.
- Producto: depósito a **12 meses**, sin importe mínimo ni máximo, abono trimestral de intereses, cancelación parcial y total con penalización (se descuentan los intereses recibidos).
- Condición: **3,00 % TIN anual / 3,03 % TAE**, aplicable durante 12 meses.
- **Vigencia declarada en la propia ficha: hasta el 31/10/2026.** A fecha de esta lectura la oferta ya está vencida: la app debe marcarla `stale` y no mostrarla como tasa vigente.
- Requiere cuenta asociada (Cuenta Remunerada Pibank o Nómina). Cuenta remunerada: 2,00 % TIN / 2,02 % TAE, liquidación mensual.
- Garantía: FGD español, 100.000 €. Indicador de riesgo 1/6.

## Depósito Nuevo Ahorro 12 meses — EBN Banco

- Fuente: https://www.ebnbanco.com/ahorro/deposito-nuevo-ahorro/ · consultada 2026-11-03; información precontractual fechada **2026-09-29**.
- Producto: depósito a **12 meses**, capital garantizado, liquidación de intereses al vencimiento.
- Condición: **3,10 % TAE / 3,06 % TIN**. Ejemplo oficial: 5.000 € a 12 meses → 153 € brutos.
- Importes: mínimo **5.000 €**, máximo **400.000 €**. Requiere incremento de saldo en depósitos del banco.
- Cancelación anticipada: **no permitida**. Garantía: FGD España, 100.000 €. Riesgo 1/6.

## Depósito a 12 meses — Self Bank

- Fuente secundaria: https://www.rankia.com/blog/mejores-depositos/7489106-mejores-depositos-bancarios-octubre-2026 · consultada 2026-11-03. **Página oficial pendiente.**
- Producto: **12 meses**, **2,75 % TAE / 2,72 % TIN**, sin vinculación adicional, intereses trimestrales.
- Importes: 6.000 €–1.000.000 €. Requiere cuenta Self y dinero nuevo.
- Se marca `secondary_press`: la app lo muestra como tal y no lo equipara a una ficha oficial.

## Consecuencia para el comparador (actualizada)

A 12 meses ya hay **dos** productos con tasa documentada: **EBN 3,10 %** (oficial) y **Self Bank 2,75 %** (prensa). Pibank 3,03 % queda fuera por vencido. Openbank 6 meses no entra en esa comparación por plazo, y sus dos tramos (2,75 % sin nómina / 3,25 % con nómina ≥900 €) se muestran por separado. El comparador puede operar con dos productos y debe declarar la clase de fuente de cada uno.

## Pendiente de este bloque

1. Mostrar estas condiciones en biblioteca, ficha y comparador (solo la tasa base; los tramos con requisito, aparte).
2. Conseguir la página oficial de Self Bank para dejar de depender de prensa.
3. Registrar permiso de visualización por fuente antes de publicar.

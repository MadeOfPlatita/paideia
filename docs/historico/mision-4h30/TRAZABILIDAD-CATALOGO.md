# Trazabilidad del catálogo — fuentes, fichas y conflictos (4/11/2026)

## Qué se corrigió y por qué

**1. Los `source_ids` numéricos del snapshot no llegaban a una URL.** Las condiciones
derivadas del snapshot citaban la fuente como `"1"` o `"2"`: un identificador interno
sin enlace. En la ficha de `ACC-01` se mostraba «2,61 % TAE» sin fuente enlazable.
El registro real de esas fuentes existe en
`docs/validacion-04/05-catalogo/evidencia/sources-ledger.json` (id → URL, título y
fecha de consulta) y ahora se usa:

- `catalogue_conditions.derive(..., sources=...)` resuelve cada id a su URL y añade
  `source_refs` con URL, título y fecha.
- Si se pasa un registro y algún id no resuelve, la condición **no** se publica como
  conocida: queda `unknown` con motivo `SOURCE_UNRESOLVED` (fallo cerrado). Las cifras
  no se muestran sin fuente verificable.
- La app local lo carga con `conditions_service`; la función WSGI lleva el registro
  empaquetado (`SOURCES` en `api/_core/catalogue_data.py`, generado por
  `api/build_core.py`).

Comprobado por HTTP en la app local:

```
ACC-01 annual_rate_percent 2.61 known DOCUMENTED_PROMO_TAE
  source_ids: ["https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf"]
  source_refs: [{url: …RenaultBank.pdf, title: "Renault Bank — Información precontractual global", accessed: "2026-10-27"}]
```

**2. Los dos depósitos comparables no tenían ficha.** `DEP-EBN-12` y `DEP-SELF-12`
existen solo como condiciones transcritas (`data/condiciones.json`): aparecían en
`/api/conditions` y en el comparador, pero `/api/products/<id>` devolvía
`product: null`. Ahora la app local construye su ficha mínima con lo transcrito
(nombre, entidad, familia, URL y fecha de consulta) y `conditions_state: "documented"`.
La lista de candidatos sigue siendo la del snapshot (20): los transcritos solo se
añaden a la consulta por id, no a la lista.

**3. El conflicto documentado se sustituía por una frase genérica.** La ficha de
`ACC-02` (MyInvestor) mostraba «Conflicto de fuentes o condiciones pendiente de
revisión» en lugar de decir qué discrepa. Ahora la ficha muestra el texto literal
documentado; la lista y el comparador de metadatos conservan la regla de no publicar
cifras sueltas (invariante ya cubierta por pruebas), con el aviso de «ver la ficha».

Visto en el navegador real sobre la app local:

- `ACC-02` — «Tasa anual (TAE): sin cifra utilizable · en conflicto; fuentes en
  conflicto · La misma página mezcla 2,50 % TAE/6 meses y un FAQ con 1,25 % TAE/12
  meses…», y el bloque «Conflictos que siguen abiertos» con el mismo texto.
- `DEP-EBN-12` — ficha con «Tasa anual (TAE): 3,10 % TAE · documentada por la fuente;
  fuente oficial», «Plazo: 12 meses» y enlace a la web de EBN Banco.
- `DEP-SELF-12` — ficha con 2,75 % TAE y fuente de prensa (identidad
  `press_documented`, no oficial).
- `DEP-03` (Pibank) — la tasa se mantiene en estado vencido, no vigente.

## Pruebas añadidas

- `app/tests/test_catalogue_sources.py` (7): resolución de ids,
  `source_refs` con título y fecha, ids sin URL no indexados, registro vacío y
  parcialmente resuelto fallan cerrado, comportamiento histórico sin registro y
  declaración del estado del registro.
- `app/tests/test_curated_product_record.py` (4): ficha de los
  transcritos en local y en WSGI, paridad de campos y conflicto literal en la ficha.

## Límites que se mantienen

- Los permisos de publicación de las fuentes siguen sin revisar: todo el catálogo va
  marcado `not_for_publication` y `publication_ready: false`.
- `DEP-SELF-12` depende de una fuente secundaria (prensa) y así se etiqueta.
- `DEP-03` está vencido; se muestra como vencido, no como oferta actual.
- La lista de candidatos no incorpora tasas: el comparador de metadatos sigue sin
  publicar cifras; las tasas solo aparecen en el bloque de condiciones y en la ficha,
  con su estado y su fuente.

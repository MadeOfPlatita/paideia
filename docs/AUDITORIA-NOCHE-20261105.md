# Auditoría de la noche (2026-11-05)

Lista de trabajo del objetivo activo. Los tres primeros puntos son los que pidió
el usuario; el resto sale de revisar lo que la app hace hoy.

Carga asumida: una demo pública para clase, una persona a la vez, con tope de 300
llamadas al día y datos ficticios.

## Must fix

1. ~~**Fondos y ETF no muestran nada de lo transcrito.**~~ **Hecho**: `ad3bb9b` (DOCUMENTED_METRICS + ficha). De sus condiciones se
   guardan TER, ISIN, comisiones, SRI, mínimo y resto en `documented`
   (`data/condiciones.json`), pero la ficha solo pinta tasa y plazo, que esas
   familias no tienen. Resultado: 7 fichas con «sin datos» aunque el dato exista.
   Arreglo: llevar esas métricas a la ficha con su fuente, sin inventar las que
   falten.

2. ~~**Tres preguntas del perfil se piden y no se usan.**~~ **Hecho**: ya no se preguntan (4 en total); conectarlas queda como decisión. Liquidez, tolerancia y
   capacidad de pérdida se guardan, pero el DTO del chat (`chat_context.py`)
   solo acepta objetivo, horizonte, importe y colchón. O se envían con
   consentimiento por campo, o se dejan de preguntar.

3. ~~**El cupo diario vive en memoria.**~~ **Documentado**: `docs/CUPO-Y-LIMITES.md`. Cualquier redespliegue de Render lo deja
   a cero; el «300 al día» es un freno de gasto, no una cuota. Arreglo: estado
   duradero o límite real documentado.

4. ~~**Rama muerta de «temas que te interesan».**~~ **Hecho**: eliminada de `app.js`. `app.js:1265-1283` conserva la
   rama de `question.topics`, pero ningún cuestionario la define desde que
   Experiencia dejó de pedir temas. Son ~10 líneas y una condición de lectura que
   ya no se cumple.

5. ~~**`documented` no lo lee nadie.**~~ **Hecho**: alimenta la ficha. Se escriben 223 condiciones con literal,
   URL y fecha, y la app solo consume `tiers` y `term_months`. Es el material del
   punto 1; si no se usa, sobra.

## Should fix

6. **`PROFILE05_MAPPING` solo lo usan las pruebas.** La app ya no lo consume.
   Se puede dejar como contrato del esquema o retirarlo con sus pruebas.

7. ~~**El recorte de etiquetas desconocidas empareja por texto.**~~ **Hecho**: prueba de etiqueta sin regla. Si mañana una
   ficha transcrita documenta «divisa explícita», la etiqueta desaparecería sin
   que nadie lo decida. Falta una prueba de que una etiqueta sin regla no se
   toca.

8. ~~**El estado `partial` no se distingue en la interfaz.**~~ **Hecho**: la cabecera ya no dice «pendientes». Una ficha con
   condiciones parciales se muestra igual que una documentada; conviene que lo
   diga.

## Nice to have

9. `docs/` acumula informes de seis misiones; falta un índice que diga cuál es
   el vigente.

## Fuera de alcance esta noche

- Vercel: congelado como escaparate, enlaza a Render.
- Contador de misión (N2): sigue sin aprobación; no se toca.
- Publicar el repositorio: el usuario lo hará al entregar.

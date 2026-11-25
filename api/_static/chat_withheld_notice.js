'use strict';
// Motivo visible de una respuesta retenida. Función pura y cerrada: no inventa el
// motivo cuando el backend no lo declara; en ese caso dice solo que no se pudo
// verificar localmente, sin acusar de «fuente oficial».
(function (root, factory) {
  const model = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = model;
  if (root) root.PaideiaWithheldNotice = model;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  // Lo que la persona lee al principio de una respuesta con datos de catálogo. Antes
  // era jerga de ingeniería («los datos vienen del catálogo local», «la explicación
  // va limpia de cifras»): describía cómo está hecha la respuesta en vez de decir
  // qué se ha usado. Medido en pantalla, era la primera frase que se leía.
  const CATALOGUE = 'Esto sale de las fichas que tengo del catálogo, con su fuente y su fecha.';
  const CALCULATION = 'La cuenta la ha hecho la calculadora de la app con los datos que me diste; no la he estimado yo.';
  const GENERIC = 'No puedo darte esto como dato comprobado; lo que sigue es orientación, no una cifra verificada.';
  const REASONS = Object.freeze({
    figure: 'Se ha omitido el texto del modelo: contenía una cifra, un importe o un porcentaje sin datos locales que lo respalden. No se presenta como prosa verificada y, si el turno no aportó datos del motor o del catálogo, no se muestra ninguna cifra.',
    attribution: 'Se ha omitido el texto del modelo: atribuía una fuente, una vigencia o una confirmación sin datos locales que la respalden. No se presenta como dato verificado.',
    identifier: 'Se ha omitido el texto del modelo: nombraba un identificador de producto sin datos locales que lo respalden. Los identificadores solo se muestran desde el catálogo local.',
    invalid: 'Se ha omitido el texto del modelo porque no tiene una forma que la frontera local pueda comprobar; no se presenta como dato verificado.'
  });

  function notice(input) {
    const value = input && typeof input === 'object' ? input : {};
    if (value.catalogueUsed === true) return CATALOGUE;
    if (value.hasCalculation === true) return CALCULATION;
    const reason = typeof value.reason === 'string' ? value.reason : '';
    return Object.prototype.hasOwnProperty.call(REASONS, reason) ? REASONS[reason] : GENERIC;
  }

  return Object.freeze({ notice, reasons: Object.keys(REASONS) });
});

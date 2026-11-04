'use strict';
// Motivo visible de una respuesta retenida. Función pura y cerrada: no inventa el
// motivo cuando el backend no lo declara; en ese caso dice solo que no se pudo
// verificar localmente, sin acusar de «fuente oficial».
(function (root, factory) {
  const model = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = model;
  if (root) root.PaideiaWithheldNotice = model;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const CATALOGUE = 'El texto del modelo no se muestra en esta consulta de catálogo: no está validado y no puede adjudicar fuentes ni tasas. Se muestran los datos locales con su clase, fechas y límites.';
  const CALCULATION = 'Se ha omitido el texto del modelo en este turno de calculadora: una cifra de la prosa puede atribuirse al concepto equivocado. Se muestra el resultado y los supuestos del motor local.';
  const GENERIC = 'Se ha omitido el texto del modelo porque no se pudo verificar localmente. No se presenta como dato.';
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

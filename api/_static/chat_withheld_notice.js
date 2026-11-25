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
    figure: 'Se han quitado del texto las frases con cifras que no puedo respaldar; el resto del razonamiento es del modelo, no un dato verificado.',
    attribution: 'Se han quitado del texto las frases que atribuían una fuente, una vigencia o una confirmación sin datos locales que las respalden.',
    identifier: 'Se han quitado del texto los nombres de producto o identificadores que no puedo respaldar con el catálogo local.',
    invalid: 'El texto del modelo no tiene una forma que pueda comprobar; no se presenta como dato verificado.'
  });

  // Cuando NO se ha quitado nada, no hay nada que declarar: decir «se ha omitido el
  // texto del modelo» en un turno donde la prosa sí se muestra es una contradicción
  // visible en pantalla (medido: el bloque de trazabilidad decía «se ha omitido»
  // justo debajo de la prosa mostrada).
  const NONE = '';

  function notice(input) {
    const value = input && typeof input === 'object' ? input : {};
    if (value.catalogueUsed === true) return CATALOGUE;
    if (value.hasCalculation === true) return CALCULATION;
    const reason = typeof value.reason === 'string' ? value.reason : '';
    return Object.prototype.hasOwnProperty.call(REASONS, reason) ? REASONS[reason] : GENERIC;
  }

  return Object.freeze({ notice, reasons: Object.keys(REASONS) });
});

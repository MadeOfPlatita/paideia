'use strict';
(function(root,factory){ const model=factory(); if(typeof module!=='undefined' && module.exports) module.exports=model; if(root) root.PaideiaChatContext=model; })(typeof globalThis!=='undefined'?globalThis:this,function(){
  const fields=Object.freeze(['respuestas.objetivo','respuestas.horizonte','detalle_economico.importe_objetivo','detalle_economico.colchon_liquido']);
  const synthetic=Object.freeze({respuestas:{objetivo:{estado:'declarado',valor:'aprender_conceptos'},horizonte:{estado:'no_se'}},detalle_economico:{importe_objetivo:{estado:'declarado',valor:{min_eur:'0',max_eur:'0.00',moneda:'EUR'}},colchon_liquido:{estado:'omitido'}}});
  let turns=[];
  function project(profile,selection){
    if(!Array.isArray(selection)||!selection.length||new Set(selection).size!==selection.length||selection.some(k=>!fields.includes(k))) throw new Error('Selección no válida');
    const result={}; for(const key of selection){const [group,name]=key.split('.'); const answer=profile?.[group]?.[name]; if(!answer) throw new Error('Campo ausente'); result[key]=JSON.parse(JSON.stringify(answer));}
    return {version:'chat-context-map-v1',fields:result};
  }
  function add(user,assistant){
    if(typeof user!=='string'||typeof assistant!=='string'||!user.length||!assistant.length||user.length>1000||assistant.length>1000) throw new Error('Límite de historial alcanzado; borra el historial para continuar.');
    turns=turns.concat([{role:'user',content:user},{role:'assistant',content:assistant}]).slice(-4);
  }
  function history(){return turns.map(m=>({...m}));} function clear(){turns=[];}
  return Object.freeze({fields,synthetic,project,add,history,clear});
});

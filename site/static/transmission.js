/* Shared, deterministic voltage classification for desktop and public map. */
(function(root){
 'use strict';
 const fields=new Set(['tensao','tensaokv','valniveltensaokv','tensaonominal','tensaonominalkv','voltage','voltagekv']);
 const normalize=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
 const colors={'13.8':'#9e8700','23':'#5745a1','23.1':'#bf5b00','34.5':'#9c27b0','35':'#087f8c','35.5':'#99613c','36':'#a3185b','38.5':'#527300','54':'#264a93','69':'#008c82','93':'#9b4c9b','98.08':'#b57100','132':'#5c7a3d','138':'#228b3b','230':'#1565d8','345':'#d42a96','440':'#743bd1','500':'#f07800','525':'#a54800','600':'#d02525','765':'#811c27','800':'#d34d61'};
 function parse(value){
  if(typeof value==='number')return Number.isFinite(value)&&value>0?String(Number(value.toFixed(6))):null;
  if(typeof value!=='string')return null;
  const text=value.trim().replace(/^±\s*/,'').replace(/\s*k\s*v\s*$/i,'').replace(',','.');
  if(!/^\d+(?:\.\d+)?$/.test(text))return null;
  const number=Number(text);return number>0?String(Number(number.toFixed(6))):null;
 }
 function voltage(properties){
  const attrs=properties.attributes||properties.voltage_fields||{};
  for(const [field,value]of Object.entries(attrs))if(fields.has(normalize(field))){const key=parse(value);if(key!==null)return key}
  return null;
 }
 function color(key){
  if(key===null)return '#7a838d';
  if(colors[key])return colors[key];
  let hash=2166136261;for(const c of key){hash^=c.charCodeAt(0);hash=Math.imul(hash,16777619)}
  return `hsl(${(hash>>>0)%360} 70% 37%)`;
 }
 function classify(feature){
  const p=feature.properties||{},type=feature.geometry?.type||'';
  if(!type.includes('LineString')||!normalize(p.layer_name||'').includes('transmiss'))return null;
  const key=voltage(p);return {key,label:key===null?'Tensão não informada':Number(key).toLocaleString('pt-BR',{maximumFractionDigits:6})+' kV',color:color(key),dashArray:key===null?'6 5':null};
 }
 root.EnerTransmission={parse,voltage,color,classify};
})(globalThis);

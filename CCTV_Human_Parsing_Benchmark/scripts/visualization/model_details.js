"use strict";
const data=window.GALLERY_DATA;
const el=id=>document.getElementById(id);
const query=new URLSearchParams(location.search);
const images=[...new Set(data.cases.map(c=>c.image_id))];
function option(select,value,label){const o=document.createElement("option");o.value=value;o.textContent=label;select.append(o);}
images.forEach(id=>option(el("image"),id,id));
data.models.forEach(m=>option(el("model"),m.id,m.id));
if(data.models.some(m=>m.id===query.get("model")))el("model").value=query.get("model");
const initial=data.cases.find(c=>c.id===query.get("roi"));
if(initial)el("image").value=initial.image_id;
function fillROIs(wanted){el("roi").replaceChildren();data.cases.filter(c=>c.image_id===el("image").value).forEach(c=>option(el("roi"),c.id,`ROI ${c.opportunity_index+1} · ${c.width}×${c.height}px`));if(wanted&&[...el("roi").options].some(o=>o.value===wanted))el("roi").value=wanted;}
function current(){return data.cases.find(c=>c.id===el("roi").value);}
function sizePanels(){const c=current();if(!c)return;const zoom=Number(el("zoom").value)/100;const width=document.querySelector(".viewport").clientWidth;const fit=Math.min((width-6)/c.width,570/c.height);document.querySelectorAll(".stack").forEach(n=>{n.style.width=`${c.width*fit*zoom}px`;n.style.height=`${c.height*fit*zoom}px`;});el("zoomValue").textContent=`${zoom.toFixed(2)}× fit`;}
function opacity(){document.querySelectorAll(".mask").forEach(n=>n.style.opacity=Number(el("alpha").value)/100);el("alphaValue").textContent=`${el("alpha").value}%`;}
let previousCase=null;
function render(){const c=current();const m=data.models.find(m=>m.id===el("model").value);const assets=c.models[m.id];const ownership=el("ownership").value;const palette=el("palette").value;
 ["rgb0","rgb1","rgb2"].forEach(id=>el(id).src=c.rgb);
 el("gt").src=c.gt;el("prediction").src=assets[`${ownership}_${palette}`];
 el("predictionTitle").textContent=m.id;
 el("info").textContent=`${c.image_id} · ${c.id} · source ROI ${c.width}×${c.height}px · original crop [${c.crop_xyxy.join(", ")}] · frozen YOLO confidence ${c.YOLO_score.toFixed(3)} (detector confidence)`;
 const gt=c.GT_person_id===null?"ROI นี้ไม่มี GT person ที่จับคู่ จึงไม่มี GT target tasks ให้เทียบ ไม่ใช่ GT background":`GT person ${c.GT_person_id} · targets ที่ประเมิน: ${c.eligible_targets.join(", ")||"ไม่มีใน ROI นี้"}`;
 el("warning").textContent=gt+(ownership==="raw"?" · กำลังดู output ก่อน YOLO clip: diagnostic เท่านั้น ไม่ใช่ mask ที่ใช้คิดคะแนน":" · output หลัง ownership เป็นชุดที่ใช้คิดคะแนน");
 const legend=palette==="native"?data.native_catalogs[m.family]:data.common_legend;
 el("legend").replaceChildren();legend.forEach(r=>{const span=document.createElement("span"),swatch=document.createElement("i"),label=document.createElement("span");swatch.style.background=`rgb(${r.color.join(",")})`;label.textContent=`${r.id}: ${r.name}`;span.append(swatch,label);el("legend").append(span);});
 el("nativeDownload").href=assets[`${ownership}_integer`];el("caseContact").href=c.contact;el("sceneOverview").href=c.sceneOverview;
 const u=new URL(location.href);u.searchParams.set("model",m.id);u.searchParams.set("roi",c.id);try{history.replaceState(null,"",u);}catch{/* Local file origins may disallow history changes. */}
 sizePanels();opacity();if(previousCase!==c.id)document.querySelectorAll(".viewport").forEach(n=>{n.scrollLeft=0;n.scrollTop=0;});previousCase=c.id;}
el("image").addEventListener("change",()=>{fillROIs();render();});
["roi","model","palette","ownership"].forEach(id=>el(id).addEventListener("change",render));
el("alpha").addEventListener("input",opacity);el("zoom").addEventListener("input",sizePanels);window.addEventListener("resize",sizePanels);
function step(delta){const idx=data.cases.findIndex(c=>c.id===el("roi").value);const next=data.cases[(idx+delta+data.cases.length)%data.cases.length];el("image").value=next.image_id;fillROIs(next.id);render();}
el("previous").addEventListener("click",()=>step(-1));el("next").addEventListener("click",()=>step(1));
let syncing=false;document.querySelectorAll(".viewport").forEach(pane=>pane.addEventListener("scroll",()=>{if(syncing)return;syncing=true;document.querySelectorAll(".viewport").forEach(other=>{if(other!==pane){other.scrollLeft=pane.scrollLeft;other.scrollTop=pane.scrollTop;}});requestAnimationFrame(()=>syncing=false);}));
fillROIs(initial?.id);render();

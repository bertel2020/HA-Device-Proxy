// GENERATED FILE - do not edit. Edit panel-src/src/ and run: node panel-src/build.mjs
var lt=Object.defineProperty;var ct=(r,e,t)=>e in r?lt(r,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):r[e]=t;var f=(r,e,t)=>ct(r,typeof e!="symbol"?e+"":e,t);var ne=globalThis,ie=ne.ShadowRoot&&(ne.ShadyCSS===void 0||ne.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,ge=Symbol(),Ne=new WeakMap,q=class{constructor(e,t,n){if(this._$cssResult$=!0,n!==ge)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(ie&&e===void 0){let n=t!==void 0&&t.length===1;n&&(e=Ne.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),n&&Ne.set(t,e))}return e}toString(){return this.cssText}},Pe=r=>new q(typeof r=="string"?r:r+"",void 0,ge),g=(r,...e)=>{let t=r.length===1?r[0]:e.reduce((n,i,o)=>n+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+r[o+1],r[0]);return new q(t,r,ge)},Re=(r,e)=>{if(ie)r.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let n=document.createElement("style"),i=ne.litNonce;i!==void 0&&n.setAttribute("nonce",i),n.textContent=t.cssText,r.appendChild(n)}},ve=ie?r=>r:r=>r instanceof CSSStyleSheet?(e=>{let t="";for(let n of e.cssRules)t+=n.cssText;return Pe(t)})(r):r;var{is:dt,defineProperty:pt,getOwnPropertyDescriptor:ht,getOwnPropertyNames:ut,getOwnPropertySymbols:ft,getPrototypeOf:mt}=Object,ae=globalThis,He=ae.trustedTypes,bt=He?He.emptyScript:"",gt=ae.reactiveElementPolyfillSupport,K=(r,e)=>r,$e={toAttribute(r,e){switch(e){case Boolean:r=r?bt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,e){let t=r;switch(e){case Boolean:t=r!==null;break;case Number:t=r===null?null:Number(r);break;case Object:case Array:try{t=JSON.parse(r)}catch{t=null}}return t}},Be=(r,e)=>!dt(r,e),Fe={attribute:!0,type:String,converter:$e,reflect:!1,useDefault:!1,hasChanged:Be};Symbol.metadata??=Symbol("metadata"),ae.litPropertyMetadata??=new WeakMap;var k=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=Fe){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),i=this.getPropertyDescriptor(e,n,t);i!==void 0&&pt(this.prototype,e,i)}}static getPropertyDescriptor(e,t,n){let{get:i,set:o}=ht(this.prototype,e)??{get(){return this[t]},set(a){this[t]=a}};return{get:i,set(a){let c=i?.call(this);o?.call(this,a),this.requestUpdate(e,c,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??Fe}static _$Ei(){if(this.hasOwnProperty(K("elementProperties")))return;let e=mt(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(K("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(K("properties"))){let t=this.properties,n=[...ut(t),...ft(t)];for(let i of n)this.createProperty(i,t[i])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[n,i]of t)this.elementProperties.set(n,i)}this._$Eh=new Map;for(let[t,n]of this.elementProperties){let i=this._$Eu(t,n);i!==void 0&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let i of n)t.unshift(ve(i))}else e!==void 0&&t.push(ve(e));return t}static _$Eu(e,t){let n=t.attribute;return n===!1?void 0:typeof n=="string"?n:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Re(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,n);if(i!==void 0&&n.reflect===!0){let o=(n.converter?.toAttribute!==void 0?n.converter:$e).toAttribute(t,n.type);this._$Em=e,o==null?this.removeAttribute(i):this.setAttribute(i,o),this._$Em=null}}_$AK(e,t){let n=this.constructor,i=n._$Eh.get(e);if(i!==void 0&&this._$Em!==i){let o=n.getPropertyOptions(i),a=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:$e;this._$Em=i;let c=a.fromAttribute(t,o.type);this[i]=c??this._$Ej?.get(i)??c,this._$Em=null}}requestUpdate(e,t,n,i=!1,o){if(e!==void 0){let a=this.constructor;if(i===!1&&(o=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??Be)(o,t)||n.useDefault&&n.reflect&&o===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:i,wrapped:o},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),o!==!0||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),i===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,o]of this._$Ep)this[i]=o;this._$Ep=void 0}let n=this.constructor.elementProperties;if(n.size>0)for(let[i,o]of n){let{wrapped:a}=o,c=this[i];a!==!0||this._$AL.has(i)||c===void 0||this.C(i,void 0,o,c)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(n=>n.hostUpdate?.()),this.update(t)):this._$EM()}catch(n){throw e=!1,this._$EM(),n}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};k.elementStyles=[],k.shadowRootOptions={mode:"open"},k[K("elementProperties")]=new Map,k[K("finalized")]=new Map,gt?.({ReactiveElement:k}),(ae.reactiveElementVersions??=[]).push("2.1.2");var Ae=globalThis,Ue=r=>r,re=Ae.trustedTypes,je=re?re.createPolicy("lit-html",{createHTML:r=>r}):void 0,Ke="$lit$",A=`lit$${Math.random().toFixed(9).slice(2)}$`,Ze="?"+A,vt=`<${Ze}>`,L=document,Y=()=>L.createComment(""),J=r=>r===null||typeof r!="object"&&typeof r!="function",Ce=Array.isArray,$t=r=>Ce(r)||typeof r?.[Symbol.iterator]=="function",xe=`[ 	
\f\r]`,Z=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Ie=/-->/g,Ve=/>/g,E=RegExp(`>|${xe}(?:([^\\s"'>=/]+)(${xe}*=${xe}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ge=/'/g,We=/"/g,Ye=/^(?:script|style|textarea|title)$/i,Te=r=>(e,...t)=>({_$litType$:r,strings:e,values:t}),l=Te(1),oe=Te(2),Kt=Te(3),z=Symbol.for("lit-noChange"),$=Symbol.for("lit-nothing"),qe=new WeakMap,D=L.createTreeWalker(L,129);function Je(r,e){if(!Ce(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return je!==void 0?je.createHTML(e):e}var xt=(r,e)=>{let t=r.length-1,n=[],i,o=e===2?"<svg>":e===3?"<math>":"",a=Z;for(let c=0;c<t;c++){let d=r[c],u,b,p=-1,y=0;for(;y<d.length&&(a.lastIndex=y,b=a.exec(d),b!==null);)y=a.lastIndex,a===Z?b[1]==="!--"?a=Ie:b[1]!==void 0?a=Ve:b[2]!==void 0?(Ye.test(b[2])&&(i=RegExp("</"+b[2],"g")),a=E):b[3]!==void 0&&(a=E):a===E?b[0]===">"?(a=i??Z,p=-1):b[1]===void 0?p=-2:(p=a.lastIndex-b[2].length,u=b[1],a=b[3]===void 0?E:b[3]==='"'?We:Ge):a===We||a===Ge?a=E:a===Ie||a===Ve?a=Z:(a=E,i=void 0);let S=a===E&&r[c+1].startsWith("/>")?" ":"";o+=a===Z?d+vt:p>=0?(n.push(u),d.slice(0,p)+Ke+d.slice(p)+A+S):d+A+(p===-2?c:S)}return[Je(r,o+(r[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),n]},X=class r{constructor({strings:e,_$litType$:t},n){let i;this.parts=[];let o=0,a=0,c=e.length-1,d=this.parts,[u,b]=xt(e,t);if(this.el=r.createElement(u,n),D.currentNode=this.el.content,t===2||t===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(i=D.nextNode())!==null&&d.length<c;){if(i.nodeType===1){if(i.hasAttributes())for(let p of i.getAttributeNames())if(p.endsWith(Ke)){let y=b[a++],S=i.getAttribute(p).split(A),se=/([.?@])?(.*)/.exec(y);d.push({type:1,index:o,name:se[2],strings:S,ctor:se[1]==="."?_e:se[1]==="?"?we:se[1]==="@"?ke:M}),i.removeAttribute(p)}else p.startsWith(A)&&(d.push({type:6,index:o}),i.removeAttribute(p));if(Ye.test(i.tagName)){let p=i.textContent.split(A),y=p.length-1;if(y>0){i.textContent=re?re.emptyScript:"";for(let S=0;S<y;S++)i.append(p[S],Y()),D.nextNode(),d.push({type:2,index:++o});i.append(p[y],Y())}}}else if(i.nodeType===8)if(i.data===Ze)d.push({type:2,index:o});else{let p=-1;for(;(p=i.data.indexOf(A,p+1))!==-1;)d.push({type:7,index:o}),p+=A.length-1}o++}}static createElement(e,t){let n=L.createElement("template");return n.innerHTML=e,n}};function O(r,e,t=r,n){if(e===z)return e;let i=n!==void 0?t._$Co?.[n]:t._$Cl,o=J(e)?void 0:e._$litDirective$;return i?.constructor!==o&&(i?._$AO?.(!1),o===void 0?i=void 0:(i=new o(r),i._$AT(r,t,n)),n!==void 0?(t._$Co??=[])[n]=i:t._$Cl=i),i!==void 0&&(e=O(r,i._$AS(r,e.values),i,n)),e}var ye=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,i=(e?.creationScope??L).importNode(t,!0);D.currentNode=i;let o=D.nextNode(),a=0,c=0,d=n[0];for(;d!==void 0;){if(a===d.index){let u;d.type===2?u=new Q(o,o.nextSibling,this,e):d.type===1?u=new d.ctor(o,d.name,d.strings,this,e):d.type===6&&(u=new Se(o,this,e)),this._$AV.push(u),d=n[++c]}a!==d?.index&&(o=D.nextNode(),a++)}return D.currentNode=L,i}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings!==void 0?(n._$AI(e,n,t),t+=n.strings.length-2):n._$AI(e[t])),t++}},Q=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,i){this.type=2,this._$AH=$,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=O(this,e,t),J(e)?e===$||e==null||e===""?(this._$AH!==$&&this._$AR(),this._$AH=$):e!==this._$AH&&e!==z&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):$t(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==$&&J(this._$AH)?this._$AA.nextSibling.data=e:this.T(L.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,i=typeof n=="number"?this._$AC(e):(n.el===void 0&&(n.el=X.createElement(Je(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===i)this._$AH.p(t);else{let o=new ye(i,this),a=o.u(this.options);o.p(t),this.T(a),this._$AH=o}}_$AC(e){let t=qe.get(e.strings);return t===void 0&&qe.set(e.strings,t=new X(e)),t}k(e){Ce(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,n,i=0;for(let o of e)i===t.length?t.push(n=new r(this.O(Y()),this.O(Y()),this,this.options)):n=t[i],n._$AI(o),i++;i<t.length&&(this._$AR(n&&n._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let n=Ue(e).nextSibling;Ue(e).remove(),e=n}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},M=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,i,o){this.type=1,this._$AH=$,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=o,n.length>2||n[0]!==""||n[1]!==""?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=$}_$AI(e,t=this,n,i){let o=this.strings,a=!1;if(o===void 0)e=O(this,e,t,0),a=!J(e)||e!==this._$AH&&e!==z,a&&(this._$AH=e);else{let c=e,d,u;for(e=o[0],d=0;d<o.length-1;d++)u=O(this,c[n+d],t,d),u===z&&(u=this._$AH[d]),a||=!J(u)||u!==this._$AH[d],u===$?e=$:e!==$&&(e+=(u??"")+o[d+1]),this._$AH[d]=u}a&&!i&&this.j(e)}j(e){e===$?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},_e=class extends M{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===$?void 0:e}},we=class extends M{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==$)}},ke=class extends M{constructor(e,t,n,i,o){super(e,t,n,i,o),this.type=5}_$AI(e,t=this){if((e=O(this,e,t,0)??$)===z)return;let n=this._$AH,i=e===$&&n!==$||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,o=e!==$&&(n===$||i);i&&this.element.removeEventListener(this.name,this,n),o&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},Se=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){O(this,e)}};var yt=Ae.litHtmlPolyfillSupport;yt?.(X,Q),(Ae.litHtmlVersions??=[]).push("3.3.3");var Xe=(r,e,t)=>{let n=t?.renderBefore??e,i=n._$litPart$;if(i===void 0){let o=t?.renderBefore??null;n._$litPart$=i=new Q(e.insertBefore(Y(),o),o,void 0,t??{})}return i._$AI(r),i};var Ee=globalThis,_=class extends k{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Xe(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}};_._$litElement$=!0,_.finalized=!0,Ee.litElementHydrateSupport?.({LitElement:_});var _t=Ee.litElementPolyfillSupport;_t?.({LitElement:_});(Ee.litElementVersions??=[]).push("4.2.2");var wt=new URL(".",location.href.split("#")[0]),ee=r=>new URL(r,wt).href,De=class extends Error{constructor(e,t){super(t&&t.error||`HTTP ${e}`),this.status=e,this.data=t||{}}};async function h(r,{method:e="GET",body:t}={}){let n=await fetch(ee(r),{method:e,credentials:"same-origin",headers:t===void 0?{}:{"Content-Type":"application/json"},body:t===void 0?void 0:JSON.stringify(t)}),o=(n.headers.get("content-type")||"").includes("json")?await n.json():await n.text();if(!n.ok)throw new De(n.status,typeof o=="object"?o:{error:o});return o}var kt=["alias","present","tty","usb","running","pending","clients","kept_open","bytes_from_device","bytes_to_device","rate_from_device","rate_to_device","last_data","line_errors","latency","addresses"],Qe=r=>Object.fromEntries(Object.entries(r).filter(([e])=>!kt.includes(e))),le=r=>r.id?h(`api/connections/${r.id}`,{method:"PUT",body:{connection:r}}):h("api/connections",{method:"POST",body:{connection:r}});var et={de:{appTitle:"Ser2Net",running:"ser2net l\xE4uft",notRunning:"ser2net l\xE4uft nicht",navConnections:"Verbindungen",navEvents:"Ereignisse",navTrace:"Mitschnitt",navSettings:"Einstellungen",navMain:"Bereiche",breadcrumb:"Pfad",connectionsTitle:"Verbindungen",connectionsSub:"Serielle Ger\xE4te, die \xFCber das Netzwerk bereitgestellt werden.",importExport:"Import / Export",addConnection:"Verbindung hinzuf\xFCgen",tileActive:"Aktiv",tileOf:"von {n}",tileClients:"Clients verbunden",tileErrors:"Leitungsfehler",tileReach:"Erreichbar aus",listen_local:"nur dieser Rechner",listen_lan:"LAN \xB7 nur private Netze",listen_all:"alle Netze",stRunning:"L\xE4uft",stDisabled:"Deaktiviert",stMissing:"Ger\xE4t fehlt",stWaiting:"Wartet auf ser2net",stPending:"\xC4nderung wartet",clients:"Clients",clientsOf:"{n} von {m}",noClients:"Keine Clients verbunden.",disabledText:"Verbindung ist deaktiviert \u2013 Port geschlossen.",missingText:"Ger\xE4t nicht angeschlossen.",since:"seit {t}",copy:"Kopieren",copied:"Kopiert",edit:"Bearbeiten",details:"Details",switchLabel:"{name} aktiv",emptyTitle:"Noch keine Verbindungen",emptyText:"Lege eine Verbindung an oder \xFCbernimm deine bestehende ser2net-Konfiguration.",emptyImport:"ser2net.yaml / ser2net.conf importieren",customActive:"Eigene ser2net.yaml ist aktiv",customActiveText:"Die Formulare sind gespeichert, werden aber nicht verwendet. Ports von ser2net:",toSettings:"Zu den Einstellungen",stuck:"Client {a} liest nicht",lineErrors:"{n} Leitungsfehler",latencyRO:"FTDI-Latenz nicht \xE4nderbar",keptOpen:"Ger\xE4t offen gehalten",live:"Live-Daten",liveSub:"Gelesen aus dem Mitschnitt von ser2net \u2013 belegt keinen Client-Platz.",pause:"Pausieren",resume:"Fortsetzen",hexOnly:"Nur Hex",hexAscii:"Hex + ASCII",liveEmpty:"Noch keine Daten. ser2net \xF6ffnet das Ger\xE4t erst, wenn ein Client verbunden ist \u2013 oder mit \u201EGer\xE4t offen halten\u201C.",clientTh:"Client",sinceTh:"Verbunden seit",toClient:"an Client",fromClient:"vom Client",queued:"Warteschlange",addresses:"Adressen zum Kopieren",target_ha:"Home Assistant (Integrationen)",target_apps:"Andere Apps (z. B. Z-Wave JS UI)",target_lan:"Andere Rechner im LAN",notReachable:"nicht erreichbar mit dieser Einstellung",lanUnknown:"LAN-Adresse unbekannt",configuration:"Konfiguration",line:"Leitung",noLineErrors:"keine Fehler",lineUnsupported:"Der Treiber z\xE4hlt keine Fehler.",lineClosed:"Z\xE4hlt nur, solange das Ger\xE4t offen ist.",frame:"Frame",parity:"Parit\xE4t",overrun:"Overrun",brk:"Break",bufOverrun:"Puffer",dataFromDevice:"Daten vom Ger\xE4t",lastData:"Letzte Daten",never:"noch nie",recent:"Verlauf",allEvents:"Alle Ereignisse",device:"Ger\xE4t",resolved:"Aufgel\xF6st",usb:"USB",serialNo:"Seriennr.",interface:"Schnittstelle",network:"Netzwerk",newConnection:"Neue Verbindung",editConnection:"Verbindung bearbeiten",template:"Vorlage",templateSub:"F\xFCllt die Felder passend vor. Alles bleibt \xE4nderbar.",tpl_ehz_sml:"eHZ SML",tpl_ehz_d0:"eHZ D0",tpl_zwave:"Z-Wave-Stick",tpl_generic:"Allgemein",tplsub_ehz_sml:"9600 8N1 \xB7 bis 5 Clients",tplsub_ehz_d0:"9600 7E1 \xB7 bis 5 Clients",tplsub_zwave:"115200 8N1 \xB7 nodelay",tplsub_generic:"9600 8N1 \xB7 1 Client",basics:"Grunddaten",name:"Name",enabled:"Aktiv",enabledText:"Nach dem Speichern bereitstellen",devicePick:"Ger\xE4t",deviceOther:"Anderer Pfad \u2026",devicePath:"Pfad",usedBy:"belegt: {n}",noSerial:"ohne Seriennr.",ambiguous:"Mehrere gleiche Adapter ohne Seriennummer: Auswahl \xFCber den USB-Port (by-path). In Proxmox diese Ger\xE4te nach Port durchreichen.",ifNet:"Schnittstelle und Netzwerk",baud:"Baudrate",format:"Format",dataBits:"Datenbits",parityF:"Parit\xE4t",stopBits:"Stoppbits",port:"TCP-Port",maxClients:"Max. Clients",maxClientsHint:"Mehr als 1 nur, wenn das Ger\xE4t das vertr\xE4gt.",mode:"Modus",mode_raw:"Bytes unver\xE4ndert durchreichen \u2013 passt f\xFCr die meisten Integrationen.",mode_rfc2217:"Clients stellen Baudrate und Leitungen selbst ein (rfc2217://\u2026).",mode_telnet:"F\xFCr Terminal-Zugriff per telnet.",advanced:"Erweitert",advancedSub:"ser2net-Optionen \xB7 alles optional",open:"aufklappen",closeA:"zuklappen",set:"{n} gesetzt",serialSide:"Serielle Seite",connectionSide:"Verbindung",tcpSide:"TCP",appSide:"App",o_local:"Modem-Steuerleitungen (CD) ignorieren",o_rtscts:"Hardware-Flusskontrolle",o_xonxoff:"Software-Flusskontrolle",o_hangup_when_done:"DTR fallen lassen, wenn der letzte Client geht",o_nobreak:"Break-Signal unterdr\xFCcken",o_low_latency:"FTDI-Latenz 1 ms statt 16 ms",o_kickolduser:"Bei vollem Limit einen alten Client trennen",o_chardelay:"Bytes sammeln und geb\xFCndelt senden",o_nodelay:"Nagle aus \u2013 weniger Latenz",o_keep_open:"Ger\xE4t offen halten (die App verbindet sich selbst, belegt einen Platz)",o_stuck_disconnect:"Clients trennen, wenn einer nicht mehr liest",o_notify_missing:"Benachrichtigen, wenn das Ger\xE4t fehlt",o_notify_no_client:"Benachrichtigen, wenn kein Client verbunden ist",dtr:"DTR beim \xD6ffnen",rts:"RTS beim \xD6ffnen",lineDefault:"unver\xE4ndert",on:"an",off:"aus",rs485:"RS485",rs485Hint:"z. B. 0:0:rts_on_send \u2013 leer = aus",timeout:"Timeout (s, 0 = nie)",retry:"Neuer Versuch nach (s, 0 = Standard)",remaddr:"Erlaubte Clients (remaddr)",remaddrHint:"Leer: nach der globalen Einstellung. Adressen oder Netze, mit Leerzeichen getrennt.",banner:"Banner",openstr:"openstr",closestr:"closestr",bind:"Bind-Adresse",bindHint:"Leer: nach der globalen Einstellung.",extra:"Weitere Optionen",extraHint:"Eine pro Zeile: name: wert",traceMode:"Mitschnitt aufzeichnen",silence:"Warnen, wenn keine Daten seit (min, 0 = nie)",tr_off:"aus",tr_rx:"vom Ger\xE4t",tr_tx:"zum Ger\xE4t",tr_both:"beide Richtungen",preview:"Vorschau ser2net.yaml",previewSub:"So wird die Verbindung an ser2net \xFCbergeben.",save:"Speichern",cancel:"Abbrechen",delete:"L\xF6schen",saveHint:"Nur diese Verbindung wird neu aufgebaut. Andere bleiben verbunden.",saved:"Gespeichert.",savedRebuilt:"Gespeichert. Neu aufgebaut: {n}.",savedReconnect:" Clients neu verbunden: {n}.",deleteConfirm:"Verbindung \u201E{n}\u201C l\xF6schen? Ihre Clients werden getrennt.",errorsBelow:"Bitte die markierten Felder pr\xFCfen.",importTitle:"Import / Export",stepChoose:"Datei w\xE4hlen",stepPreview:"Vorschau pr\xFCfen",stepDone:"\xDCbernommen",importChoose:"ser2net.yaml oder ser2net.conf ausw\xE4hlen",importDrop:"Datei ausw\xE4hlen oder Inhalt einf\xFCgen",importFormats:"ser2net 4 (YAML, Version 1 und 2) oder ser2net 3 (ser2net.conf)",chooseFile:"Datei ausw\xE4hlen",pasteHere:"\u2026 oder den Inhalt hier einf\xFCgen",readPreview:"Vorschau",otherFile:"Andere Datei",format_0:"ser2net 3 (ser2net.conf)",format_1:"ser2net 4 \xB7 YAML Version 1",format_2:"ser2net 4 \xB7 YAML Version 2",found:"{n} Verbindungen gefunden",merge:"Erg\xE4nzen",mergeSub:"Vorhandene bleiben; bei Kollisionen w\xE4hlst du pro Verbindung",replaceAll:"Alles ersetzen",replaceAllSub:"Vorhandene Verbindungen werden entfernt",result:"Ergebnis",resOk:"wird \xFCbernommen",resNotes:"mit Hinweisen",resNo:"nicht \xFCbertragbar",resConflict:"Kollision",onConflict:"Bei Kollision",c_replace:"vorhandene ersetzen",c_new_port:"neuer Port",c_skip:"\xFCberspringen",take:"\xDCbernehmen",selected:"{n} von {m} ausgew\xE4hlt",apply:"{n} \xFCbernehmen",doneTitle:"{n} Verbindungen \xFCbernommen",doneText:"Der vorherige Stand liegt in der Konfig-Historie.",toConnections:"Zu den Verbindungen",exportTitle:"Export",exportText:"Die Verbindungen als ser2net-4-ser2net.yaml \u2013 zum Sichern oder f\xFCr einen anderen Rechner.",exportDisabled:"Deaktivierte Verbindungen mitnehmen",download:"ser2net.yaml herunterladen",ownTitle:"Datei lieber direkt verwenden?",ownText:"F\xFCr Sonderf\xE4lle, die die Formulare nicht abbilden.",toSource:"Konfigurationsquelle umstellen",fileNotes:"Hinweise zur Datei",eventsTitle:"Ereignisse",eventsSub:"Live-Log der App und Historie.",tabLive:"Live-Log",tabHistory:"Historie",allConnections:"Alle Verbindungen",search:"Suche",searchPh:"z. B. getrennt, 192.168.1.20",lv_info:"Info",lv_warning:"Warnung",lv_error:"Fehler",lv_debug:"Debug",entries:"{n} Eintr\xE4ge",both:"Beide",paused:"Pausiert",liveState:"Live",noEntries:"Keine Eintr\xE4ge f\xFCr diesen Filter.",drops:"Abbr\xFCche ({d} T.)",availability:"Verf\xFCgbar",stable:"stabil",unstable:"{n}\xD7 getrennt",timeline:"Zeitleiste",retention:"Aufbewahrung {d} Tage",today:"Heute",yesterday:"Gestern",summed:"{n}\xD7 zusammengefasst",traceTitle:"Mitschnitt",traceSub:"Bytes zwischen Ger\xE4t und Clients. Aufzeichnen trennt keine Clients; Dateien rotieren automatisch.",recording:"zeichnet auf \xB7 {m}",notRecording:"keine Aufzeichnung",files:"Dateien",fileTh:"Datei",sizeTh:"Gr\xF6\xDFe",changedTh:"Ge\xE4ndert",rotation:"Rotation: {mb} MB je Datei \xB7 {k} \xE4ltere behalten",change:"\xE4ndern",deleteFile:"\u201E{n}\u201C l\xF6schen?",settingsTitle:"Einstellungen",sNet:"Netzwerk",sNetSub:"Gilt f\xFCr alle Verbindungen ohne eigene Bind-Adresse oder remaddr.",net_local:"Nur dieser Rechner",netsub_local:"127.0.0.1 \xB7 nur Home Assistant",net_lan:"LAN",netsub_lan:"nur aus privaten Netzen (empfohlen)",net_all:"Alle Netze",netsub_all:"ohne Einschr\xE4nkung",netWarn:"ser2net hat keine Anmeldung. Wer den Port erreicht, kann das Ger\xE4t lesen und steuern.",sSource:"Konfigurationsquelle",sSourceSub:"Formulare oder eine eigene ser2net.yaml f\xFCr Sonderf\xE4lle.",forms:"Formulare",own:"Eigene ser2net.yaml",ownWarn:"Solange die eigene Datei aktiv ist, werden die Formulare nicht verwendet. Ohne admin-Abschnitt: die App f\xFCgt ihren eigenen an.",check:"Pr\xFCfen",saveFile:"Speichern",saveUse:"Speichern und verwenden",checkOk:"G\xFCltig \xB7 {n} Verbindungen",notChecked:"Noch nicht gepr\xFCft",sHistory:"Konfig-Historie",sHistorySub:"die letzten 20 St\xE4nde",current:"aktuell",diff:"Unterschiede",hide:"Ausblenden",restore:"Wiederherstellen",restoreConfirm:"Diesen Stand wiederherstellen? Ge\xE4nderte Verbindungen werden neu aufgebaut.",src_ui:"Oberfl\xE4che",src_import:"Import",src_custom:"eigene Datei",src_restore:"Wiederherstellung",src_test:"Test",sLogging:"Logging und Speicher",logLevel:"Log-Level",historyDays:"Historie aufbewahren (Tage)",traceMb:"Mitschnitt: Gr\xF6\xDFe je Datei (MB)",traceKeep:"Mitschnitt: \xE4ltere Dateien",debounceCount:"Wiederholungen zusammenfassen ab",debounceMinutes:"innerhalb von (min)",sAbout:"\xDCber",app:"App",license:"Lizenz MIT",source:"Quelle",error:"Fehler",loading:"L\xE4dt \u2026",confirm:"Best\xE4tigen",yes:"Ja",no:"Nein",close:"Schlie\xDFen",language:"Sprache",connectionLost:"Keine Verbindung zur App \u2013 zeige den letzten Stand."},en:{appTitle:"Ser2Net",running:"ser2net running",notRunning:"ser2net not running",navConnections:"Connections",navEvents:"Events",navTrace:"Trace",navSettings:"Settings",navMain:"Sections",breadcrumb:"Path",connectionsTitle:"Connections",connectionsSub:"Serial devices shared over the network.",importExport:"Import / export",addConnection:"Add connection",tileActive:"Active",tileOf:"of {n}",tileClients:"Clients connected",tileErrors:"Line errors",tileReach:"Reachable from",listen_local:"this host only",listen_lan:"LAN \xB7 private networks only",listen_all:"all networks",stRunning:"Running",stDisabled:"Disabled",stMissing:"Device missing",stWaiting:"Waiting for ser2net",stPending:"Change pending",clients:"Clients",clientsOf:"{n} of {m}",noClients:"No clients connected.",disabledText:"Connection disabled \u2013 port closed.",missingText:"Device not plugged in.",since:"since {t}",copy:"Copy",copied:"Copied",edit:"Edit",details:"Details",switchLabel:"{name} active",emptyTitle:"No connections yet",emptyText:"Add a connection or take over your existing ser2net configuration.",emptyImport:"Import ser2net.yaml / ser2net.conf",customActive:"Your own ser2net.yaml is in use",customActiveText:"The forms are kept but not used. ser2net's ports:",toSettings:"To the settings",stuck:"Client {a} does not read",lineErrors:"{n} line errors",latencyRO:"FTDI latency cannot be changed",keptOpen:"Device kept open",live:"Live data",liveSub:"Read from ser2net's trace \u2013 takes no client place.",pause:"Pause",resume:"Resume",hexOnly:"Hex only",hexAscii:"Hex + ASCII",liveEmpty:"No data yet. ser2net opens the device only while a client is connected \u2013 or with \u201Ckeep device open\u201D.",clientTh:"Client",sinceTh:"Connected since",toClient:"to client",fromClient:"from client",queued:"Queue",addresses:"Addresses to copy",target_ha:"Home Assistant (integrations)",target_apps:"Other apps (e.g. Z-Wave JS UI)",target_lan:"Other computers in the LAN",notReachable:"not reachable with this setting",lanUnknown:"LAN address unknown",configuration:"Configuration",line:"Line",noLineErrors:"no errors",lineUnsupported:"The driver does not count errors.",lineClosed:"Counted only while the device is open.",frame:"Frame",parity:"Parity",overrun:"Overrun",brk:"Break",bufOverrun:"Buffer",dataFromDevice:"Data from the device",lastData:"Last data",never:"never",recent:"Recent",allEvents:"All events",device:"Device",resolved:"Resolved",usb:"USB",serialNo:"Serial no.",interface:"Interface",network:"Network",newConnection:"New connection",editConnection:"Edit connection",template:"Template",templateSub:"Fills in the fields; everything stays editable.",tpl_ehz_sml:"eHZ SML",tpl_ehz_d0:"eHZ D0",tpl_zwave:"Z-Wave stick",tpl_generic:"Generic",tplsub_ehz_sml:"9600 8N1 \xB7 up to 5 clients",tplsub_ehz_d0:"9600 7E1 \xB7 up to 5 clients",tplsub_zwave:"115200 8N1 \xB7 nodelay",tplsub_generic:"9600 8N1 \xB7 1 client",basics:"Basics",name:"Name",enabled:"Active",enabledText:"Share after saving",devicePick:"Device",deviceOther:"Other path \u2026",devicePath:"Path",usedBy:"used: {n}",noSerial:"no serial no.",ambiguous:"Several identical adapters without a serial number: chosen by USB port (by-path). In Proxmox pass these through by port.",ifNet:"Interface and network",baud:"Baud rate",format:"Format",dataBits:"Data bits",parityF:"Parity",stopBits:"Stop bits",port:"TCP port",maxClients:"Max. clients",maxClientsHint:"More than 1 only if the device copes with it.",mode:"Mode",mode_raw:"Bytes passed on unchanged \u2013 fits most integrations.",mode_rfc2217:"Clients set baud rate and lines themselves (rfc2217://\u2026).",mode_telnet:"For terminal access with telnet.",advanced:"Advanced",advancedSub:"ser2net options \xB7 all optional",open:"open",closeA:"close",set:"{n} set",serialSide:"Serial side",connectionSide:"Connection",tcpSide:"TCP",appSide:"App",o_local:"Ignore the modem lines (CD)",o_rtscts:"Hardware flow control",o_xonxoff:"Software flow control",o_hangup_when_done:"Drop DTR when the last client leaves",o_nobreak:"Suppress the break signal",o_low_latency:"FTDI latency 1 ms instead of 16 ms",o_kickolduser:"Disconnect an old client when full",o_chardelay:"Collect bytes and send them together",o_nodelay:"Nagle off \u2013 less latency",o_keep_open:"Keep the device open (the app connects itself, takes a place)",o_stuck_disconnect:"Disconnect the clients when one stops reading",o_notify_missing:"Notify when the device is missing",o_notify_no_client:"Notify when no client is connected",dtr:"DTR on open",rts:"RTS on open",lineDefault:"unchanged",on:"on",off:"off",rs485:"RS485",rs485Hint:"e.g. 0:0:rts_on_send \u2013 empty = off",timeout:"Timeout (s, 0 = never)",retry:"Retry after (s, 0 = default)",remaddr:"Allowed clients (remaddr)",remaddrHint:"Empty: as the global setting. Addresses or networks, separated by spaces.",banner:"Banner",openstr:"openstr",closestr:"closestr",bind:"Bind address",bindHint:"Empty: as the global setting.",extra:"Further options",extraHint:"One per line: name: value",traceMode:"Record trace",silence:"Warn when no data for (min, 0 = never)",tr_off:"off",tr_rx:"from the device",tr_tx:"to the device",tr_both:"both directions",preview:"Preview ser2net.yaml",previewSub:"This is what ser2net gets.",save:"Save",cancel:"Cancel",delete:"Delete",saveHint:"Only this connection is rebuilt. The others stay connected.",saved:"Saved.",savedRebuilt:"Saved. Rebuilt: {n}.",savedReconnect:" Clients reconnected: {n}.",deleteConfirm:"Delete connection \u201C{n}\u201D? Its clients are disconnected.",errorsBelow:"Please check the marked fields.",importTitle:"Import / export",stepChoose:"Choose file",stepPreview:"Check preview",stepDone:"Done",importChoose:"Choose ser2net.yaml or ser2net.conf",importDrop:"Choose a file or paste its content",importFormats:"ser2net 4 (YAML, version 1 and 2) or ser2net 3 (ser2net.conf)",chooseFile:"Choose file",pasteHere:"\u2026 or paste the content here",readPreview:"Preview",otherFile:"Other file",format_0:"ser2net 3 (ser2net.conf)",format_1:"ser2net 4 \xB7 YAML version 1",format_2:"ser2net 4 \xB7 YAML version 2",found:"{n} connections found",merge:"Add",mergeSub:"Existing ones stay; on a collision you choose per connection",replaceAll:"Replace all",replaceAllSub:"Existing connections are removed",result:"Result",resOk:"taken over",resNotes:"with notes",resNo:"cannot be taken over",resConflict:"collision",onConflict:"On collision",c_replace:"replace existing",c_new_port:"new port",c_skip:"skip",take:"Take over",selected:"{n} of {m} selected",apply:"Take over {n}",doneTitle:"{n} connections taken over",doneText:"The previous state is in the configuration history.",toConnections:"To the connections",exportTitle:"Export",exportText:"The connections as a ser2net 4 ser2net.yaml \u2013 as a backup or for another computer.",exportDisabled:"Include disabled connections",download:"Download ser2net.yaml",ownTitle:"Rather use the file as it is?",ownText:"For setups the forms cannot express.",toSource:"Change the configuration source",fileNotes:"Notes on the file",eventsTitle:"Events",eventsSub:"The app's live log and history.",tabLive:"Live log",tabHistory:"History",allConnections:"All connections",search:"Search",searchPh:"e.g. disconnected, 192.168.1.20",lv_info:"Info",lv_warning:"Warning",lv_error:"Error",lv_debug:"Debug",entries:"{n} entries",both:"Both",paused:"Paused",liveState:"Live",noEntries:"No entries for this filter.",drops:"Drops ({d} d)",availability:"Available",stable:"stable",unstable:"{n}\xD7 disconnected",timeline:"Timeline",retention:"Kept {d} days",today:"Today",yesterday:"Yesterday",summed:"{n}\xD7 summed up",traceTitle:"Trace",traceSub:"Bytes between device and clients. Recording disconnects no client; files rotate on their own.",recording:"recording \xB7 {m}",notRecording:"not recording",files:"Files",fileTh:"File",sizeTh:"Size",changedTh:"Changed",rotation:"Rotation: {mb} MB per file \xB7 {k} older kept",change:"change",deleteFile:"Delete \u201C{n}\u201D?",settingsTitle:"Settings",sNet:"Network",sNetSub:"Applies to all connections without their own bind address or remaddr.",net_local:"This host only",netsub_local:"127.0.0.1 \xB7 Home Assistant only",net_lan:"LAN",netsub_lan:"private networks only (recommended)",net_all:"All networks",netsub_all:"no limit",netWarn:"ser2net has no login. Whoever reaches the port can read and control the device.",sSource:"Configuration source",sSourceSub:"Forms, or your own ser2net.yaml for special cases.",forms:"Forms",own:"Own ser2net.yaml",ownWarn:"While your own file is in use, the forms are not used. No admin section: the app adds its own.",check:"Check",saveFile:"Save",saveUse:"Save and use",checkOk:"Valid \xB7 {n} connections",notChecked:"Not checked yet",sHistory:"Configuration history",sHistorySub:"the last 20 versions",current:"current",diff:"Differences",hide:"Hide",restore:"Restore",restoreConfirm:"Restore this version? Changed connections are rebuilt.",src_ui:"web interface",src_import:"import",src_custom:"own file",src_restore:"restore",src_test:"test",sLogging:"Logging and storage",logLevel:"Log level",historyDays:"Keep history (days)",traceMb:"Trace: size per file (MB)",traceKeep:"Trace: older files",debounceCount:"Sum up repeats from",debounceMinutes:"within (min)",sAbout:"About",app:"App",license:"License MIT",source:"Source",error:"Error",loading:"Loading \u2026",confirm:"Confirm",yes:"Yes",no:"No",close:"Close",language:"Language",connectionLost:"No connection to the app \u2013 showing the last state."}},St={de:{app_started:"Gestartet mit {connections} Verbindungen, {active} aktiv",connection_loaded:"{state}: {device} \xB7 {format} \xB7 {mode} \xB7 Port {port} \xB7 bis {max_clients} Clients",config_changed:"Konfiguration gespeichert: {summary}",clients_reconnect:"{count} Client(s) getrennt, damit die \xC4nderung greift",client_connected:"Client verbunden: {address}",client_disconnected:"Client getrennt: {address}",client_stuck:"Client {address} liest nicht ({queued} Bytes warten) \u2013 alle Clients dieser Verbindung werden gebremst",stuck_disconnected:"Clients getrennt, weil {address} nicht las",device:"Ger\xE4t gefunden: {device} \u2192 {target}",device_back:"Ger\xE4t wieder da: {device} \u2192 {target}",device_missing:"Ger\xE4t fehlt: {device}",keep_open_failed:"Ger\xE4t konnte nicht offen gehalten werden: {error}",ser2net_restart:"ser2net beendet (Code {code}), Neustart in {delay} s",line_errors:"Leitungsfehler seit Start: {frame} Frame, {parity} Parit\xE4t, {overrun} Overrun, {buffer_overrun} Puffer, {break} Break",latency_read_only:"FTDI-Latenz lie\xDF sich nicht auf 1 ms setzen: /sys ist f\xFCr die App schreibgesch\xFCtzt",custom_saved:"Eigene ser2net.yaml gespeichert ({connections} Verbindungen)",custom_invalid:"Eigene ser2net.yaml nicht verwendbar \u2013 nichts wird bereitgestellt",imported:"Import: {taken} \xFCbernommen, {skipped} \xFCbersprungen, {notes} Hinweise",import_failed:"Import fehlgeschlagen"},en:{}},tt={de:{device_missing:"Ger\xE4t {device} ist gerade nicht angeschlossen.",device_unstable:"{device} kann sich nach einem Neustart \xE4ndern \u2013 besser einen by-id- oder by-path-Namen w\xE4hlen.",device_renamed:"{device} durch den stabilen Namen {stable} ersetzt.",option_extra:"Option {option} \xFCbernommen als \u201Eweitere Option\u201C.",option_dropped:"Option {option} nicht \xFCbernommen.",serial_option_dropped:"Serielle Option {option} nicht \xFCbernommen.",legacy_option_dropped:"Option {option} nicht \xFCbernommen.",accepter_option_dropped:"Accepter-Option {option} nicht \xFCbernommen.",remaddr_port_dropped:"remaddr {address}: der Client-Port f\xE4llt weg.",remaddr_dropped:"remaddr {address} nicht lesbar, weggelassen.",trace_files_moved:"Trace-Dateien werden durch den Mitschnitt der App ersetzt.",external_file:"Option {option} liest eine externe Datei \u2013 bitte pr\xFCfen.",accepter_unsupported:"Accepter {accepter} wird nicht unterst\xFCtzt (nur TCP, telnet, RFC2217).",connector_unsupported:"Connector {connector} wird nicht unterst\xFCtzt (nur serielle Ger\xE4te).",invalid:"Ung\xFCltig: {errors}",admin_ignored:"Admin-Abschnitt ignoriert \u2013 die App hat ihren eigenen.",include_ignored:"include {path} ignoriert.",section_ignored:"Abschnitt {section} ignoriert.",define_unresolved:"Nicht aufgel\xF6ste Defines: {names}.",no_connections:"Keine Verbindungen in der Datei.",default_ignored:"DEFAULT {name} ignoriert.",line_unreadable:"Zeile nicht lesbar: {line}",yaml:"YAML-Fehler in Zeile {line}: {message}",admin_present:"Die Datei hat einen admin-Abschnitt \u2013 bitte entfernen, die App f\xFCgt ihren eigenen an.",port_twice:"Port {port} doppelt: {names}.",port_reserved:"Port {port} ist f\xFCr die App reserviert.",legacy_format:"Das alte Format (ser2net.conf) kann ser2net 4 nicht lesen \u2013 bitte importieren.",unreadable:"Datei nicht lesbar: {error}"},en:{device_missing:"Device {device} is not plugged in right now.",device_unstable:"{device} may change after a restart \u2013 better choose a by-id or by-path name.",device_renamed:"{device} replaced by its stable name {stable}.",option_extra:"Option {option} kept as a further option.",option_dropped:"Option {option} not taken over.",serial_option_dropped:"Serial option {option} not taken over.",legacy_option_dropped:"Option {option} not taken over.",accepter_option_dropped:"Accepter option {option} not taken over.",remaddr_port_dropped:"remaddr {address}: the client port is dropped.",remaddr_dropped:"remaddr {address} unreadable, left out.",trace_files_moved:"Trace files are replaced by the app's trace.",external_file:"Option {option} reads an external file \u2013 please check.",accepter_unsupported:"Accepter {accepter} is not supported (TCP, telnet, RFC2217 only).",connector_unsupported:"Connector {connector} is not supported (serial devices only).",invalid:"Invalid: {errors}",admin_ignored:"Admin section ignored \u2013 the app has its own.",include_ignored:"include {path} ignored.",section_ignored:"Section {section} ignored.",define_unresolved:"Unresolved defines: {names}.",no_connections:"No connections in the file.",default_ignored:"DEFAULT {name} ignored.",line_unreadable:"Line unreadable: {line}",yaml:"YAML error in line {line}: {message}",admin_present:"The file has an admin section \u2013 please remove it, the app adds its own.",port_twice:"Port {port} twice: {names}.",port_reserved:"Port {port} is reserved for the app.",legacy_format:"ser2net 4 cannot read the old format (ser2net.conf) \u2013 please import it.",unreadable:"File unreadable: {error}"}},At=[[/^between (\d+) and (\d+)$/,"zwischen $1 und $2"],[/^(\d+) to (\d+) seconds$/,"$1 bis $2 Sekunden"],[/^(\d+) to (\d+) minutes$/,"$1 bis $2 Minuten"],[/^(\d+) to (\d+) days$/,"$1 bis $2 Tage"],[/^(\d+) to (\d+) characters$/,"$1 bis $2 Zeichen"],[/^(\d+) to (\d+) files$/,"$1 bis $2 Dateien"],[/^(\d+) to (\d+) MB$/,"$1 bis $2 MB"],[/^(\d+) to (\d+)$/,"$1 bis $2"],[/^(\d+) or (\d+)$/,"$1 oder $2"],[/^a path under \/dev without commas or spaces$/,"ein Pfad unter /dev ohne Kommas und Leerzeichen"],[/^an IP address of this host$/,"eine IP-Adresse dieses Rechners"],[/^also used by (.+)$/,"schon verwendet von $1"],[/^another connection has this name$/,"eine andere Verbindung hei\xDFt schon so"],[/^used by the app's web interface$/,"von der Weboberfl\xE4che der App belegt"],[/^at least 2 when the device is kept open \(the app uses one\)$/,"mindestens 2, wenn das Ger\xE4t offen gehalten wird (die App belegt einen Platz)"],[/^'(.+)' is not an option name$/,"\u201E$1\u201C ist kein Optionsname"],[/^(.+) has its own field$/,"$1 hat ein eigenes Feld"],[/^'(.+)' is not an address or network$/,"\u201E$1\u201C ist keine Adresse und kein Netz"],[/^no address or network given$/,"keine Adresse und kein Netz angegeben"],[/^is missing$/,"fehlt"],[/^has the wrong type$/,"hat den falschen Typ"],[/^one of (.+)$/,"eins von: $1"],[/^off or <delay before>:<delay after>\[:<conf>\]$/,"off oder <vorher>:<nachher>[:<conf>]"]];function Le(r){if(v!=="de")return r;for(let[e,t]of At)if(e.test(r))return r.replace(e,t);return r}var Ct=(()=>{try{return localStorage.getItem("ser2net.lang")}catch{return null}})(),v=Ct||((navigator.language||"en").toLowerCase().startsWith("de")?"de":"en");function st(r){v=r;try{localStorage.setItem("ser2net.lang",r)}catch{}}var ze=(r,e={})=>r.replace(/\{(\w+)\}/g,(t,n)=>{let i=e[n];return i===void 0?t:i===null?"\u2013":Array.isArray(i)?i.join(", "):typeof i=="object"?JSON.stringify(i):String(i)}),s=(r,e)=>ze(et[v][r]??et.en[r]??r,e),Tt={de:{active:"aktiv",disabled:"deaktiviert"},en:{}},Et={de:{added:"hinzugef\xFCgt",removed:"entfernt",enabled:"aktiviert",disabled:"deaktiviert",settings:"Einstellungen"},en:{added:"added",removed:"removed",enabled:"enabled",disabled:"disabled",settings:"settings"}};function Oe(r){let e=Et[v];return(r||[]).map(t=>{let n=t.connection||e.settings;return t.fields?`${n}: ${t.fields.join(", ")}`:`${n} ${e[t.change]||t.change}`}).join("; ")}function N(r){let e=St[v][r.kind];if(!e)return r.message;let t={...r.params};return t.state&&(t.state=Tt[v][t.state]||t.state),r.kind==="config_changed"&&t.changes&&(t.summary=Oe(t.changes)),ze(e,t)}function C(r){let e=tt[v][r.code]||tt.en[r.code];if(!e)return r.code;let t={...r};return t.errors&&typeof t.errors=="object"&&(t.errors=Object.entries(t.errors).map(([n,i])=>n?`${n}: ${i}`:i).join("; ")),ze(e,t)}var ce=g`
  :host {
    --bg: #f3f4f6; --surface: #ffffff; --surface-2: #f5f7f9; --line: #e1e5ea; --line-2: #eef0f3;
    --text: #1b1f24; --muted: #5b6270; --accent: #0a6aa8; --accent-hover: #07507f; --accent-soft: #eaf3fa;
    --ok: #1e6b34; --ok-soft: #e6f4ea; --warn: #8a4b00; --warn-soft: #fff1de; --warn-line: #f3d19e;
    --bad: #a1261b; --bad-soft: #fdecea; --bad-line: #f2b8b5; --neutral-soft: #eef1f4; --neutral: #3a414c;
    --code-bg: #14181d; --code-text: #d7dee6; --focus: #7db8e0; --input-line: #c3cbd5; --on-accent: #ffffff;
    color: var(--text); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-size: 14px;
  }
  @media (prefers-color-scheme: dark) {
    :host {
      --bg: #111418; --surface: #1b1f24; --surface-2: #22272e; --line: #2d333b; --line-2: #262c33;
      --text: #e6e9ed; --muted: #9aa4b1; --accent: #5bb2ea; --accent-hover: #8ccaf2; --accent-soft: #16324a;
      --ok: #7fd49a; --ok-soft: #173a24; --warn: #f2c27a; --warn-soft: #3a2a12; --warn-line: #6b4a1c;
      --bad: #f2a29a; --bad-soft: #3d1c19; --bad-line: #6e2f2a; --neutral-soft: #2a3038; --neutral: #c5ccd5;
      --code-bg: #0b0e11; --input-line: #3a424c; --on-accent: #0b1a26;
    }
  }
`,de=g`
  * { box-sizing: border-box; }
  a { color: var(--accent); }
  a:hover { color: var(--accent-hover); }
  h1 { margin: 0; font-size: 26px; font-weight: 500; }
  h2 { margin: 0; font-size: 16px; font-weight: 500; }
  p { margin: 0; }
  .sub { color: var(--muted); margin-top: 6px; }
  .hint { font-size: 12px; color: var(--muted); }
  .mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 14px; min-width: 0; }
  .row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .stack { display: flex; flex-direction: column; gap: 20px; }
  .cols { display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; }
  .main-col { flex: 999 1 560px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
  .side-col { flex: 1 1 300px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 40px; padding: 0 18px;
    border-radius: 20px; font-family: inherit; font-size: 14px; font-weight: 500; text-decoration: none; cursor: pointer;
    border: 1px solid transparent; background: none; color: var(--accent); }
  .btn[disabled] { opacity: .55; cursor: default; }
  .btn-p { background: var(--accent); color: var(--on-accent); }
  .btn-p:hover:not([disabled]) { background: var(--accent-hover); color: var(--on-accent); }
  .btn-s { background: var(--surface); border-color: var(--input-line); }
  .btn-s:hover:not([disabled]), .btn-g:hover:not([disabled]) { background: var(--accent-soft); color: var(--accent-hover); }
  .btn-g { padding: 0 12px; }
  .btn-d { color: var(--bad); padding: 0 12px; }
  .btn-d:hover { background: var(--bad-soft); }
  .chip { display: inline-flex; align-items: center; gap: 6px; min-height: 24px; padding: 0 10px; border-radius: 12px;
    background: var(--neutral-soft); color: var(--neutral); font-size: 12px; font-weight: 500; white-space: nowrap; }
  .chip.ok { background: var(--ok-soft); color: var(--ok); } .chip.warn { background: var(--warn-soft); color: var(--warn); }
  .chip.bad { background: var(--bad-soft); color: var(--bad); } .chip.info { background: var(--accent-soft); color: var(--accent-hover); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
  .note { border-radius: 12px; padding: 12px 14px; }
  .note.warn { background: var(--warn-soft); border: 1px solid var(--warn-line); color: var(--warn); }
  .note.bad { background: var(--bad-soft); border: 1px solid var(--bad-line); color: var(--bad); }
  .note.ok { background: var(--ok-soft); color: var(--ok); }
  .note.info { background: var(--accent-soft); color: var(--accent-hover); }
  .code { background: var(--code-bg); color: var(--code-text); border-radius: 12px; padding: 14px 16px; font-size: 12px;
    line-height: 1.7; white-space: pre; overflow-x: auto; font-family: "Roboto Mono", ui-monospace, Menlo, monospace; }
  .well { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
  .fld { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
  .lbl { font-size: 12px; font-weight: 500; color: var(--muted); }
  .err { font-size: 12px; color: var(--bad); }
  .inp { min-height: 42px; padding: 0 12px; border: 1px solid var(--input-line); border-radius: 10px; font: inherit;
    color: var(--text); background: var(--surface); width: 100%; }
  .inp[aria-invalid="true"] { border-color: var(--bad); }
  textarea.inp { padding: 10px 12px; min-height: 84px; resize: vertical; }
  .inp.mono { font-family: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
  .chk { display: flex; align-items: flex-start; gap: 10px; min-height: 32px; cursor: pointer; }
  .chk input { width: 18px; height: 18px; margin: 2px 0 0; accent-color: var(--accent); flex: none; }
  .seg { display: inline-flex; border: 1px solid var(--input-line); border-radius: 10px; overflow: hidden; align-self: flex-start; }
  .seg button { min-height: 38px; padding: 0 14px; border: none; cursor: pointer; font-family: inherit; font-size: 13px; font-weight: 500;
    background: var(--surface); color: var(--text); }
  .seg button + button { border-left: 1px solid var(--input-line); }
  .seg button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); }
  .choice { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-height: 60px; padding: 12px 14px;
    border-radius: 12px; cursor: pointer; text-align: left; font: inherit; color: var(--text); background: var(--surface); border: 1px solid var(--input-line); }
  .choice[aria-pressed="true"], .choice[aria-checked="true"] { background: var(--accent-soft); border: 2px solid var(--accent); }
  .choices { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
  table { width: 100%; border-collapse: collapse; }
  th { font-weight: 500; font-size: 12px; color: var(--muted); text-align: left; padding: 8px; border-bottom: 1px solid var(--line); }
  td { padding: 10px 8px; border-bottom: 1px solid var(--line-2); vertical-align: top; }
  .scroll { overflow-x: auto; }
  .switch { flex: none; position: relative; width: 52px; height: 32px; border-radius: 16px; border: none; cursor: pointer; padding: 0; background: #aeb6c1; }
  .switch[aria-checked="true"] { background: var(--accent); }
  .switch span { position: absolute; top: 4px; left: 4px; width: 24px; height: 24px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: left .15s; }
  .switch[aria-checked="true"] span { left: 24px; }
  .switch[disabled] { opacity: .5; cursor: default; }
  button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 2px; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .crumb { font-size: 13px; color: var(--muted); }
`;var nt=(r=36)=>l`<svg width=${r} height=${r} viewBox="0 0 128 128" aria-hidden="true" style="flex:none">
  <rect width="128" height="128" rx="28" fill="#0A6AA8"></rect>
  <g fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
    <path d="M16 46H70L64 82H22Z"></path><path d="M67 64H84M84 64L104 40M84 64H108M84 64L104 88"></path></g>
  <g fill="#FFFFFF"><circle cx="104" cy="40" r="11"></circle><circle cx="108" cy="64" r="11"></circle><circle cx="104" cy="88" r="11"></circle></g></svg>`,Dt={plus:"M12 5v14M5 12h14",upload:"M12 15V3M7 8l5-5 5 5M5 21h14",download:"M12 3v12M7 10l5 5 5-5M5 21h14",copy:"M9 9h12v12H9zM5 15V5a2 2 0 0 1 2-2h10",warn:"M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",info:"M12 16v-4M12 8h.01M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",file:"M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5"},x=(r,e=18)=>l`<svg width=${e} height=${e} viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${oe`<path d=${Dt[r]}></path>`}</svg>`;function T(r){if(r==null)return"\u2013";let e=["B","kB","MB","GB"],t=r,n=0;for(;t>=1e3&&n<e.length-1;)t/=1e3,n++;return`${t.toLocaleString(v,{maximumFractionDigits:n?1:0})} ${e[n]}`}var pe=r=>`${T(Math.round(r||0))}/s`;function w(r,e=!0,t=!1){if(!r)return s("never");let n=new Date(r*1e3),i=new Date,o=n.toLocaleTimeString(v,{hour:"2-digit",minute:"2-digit",...t?{second:"2-digit"}:{}});if(!e||n.toDateString()===i.toDateString())return o;let a=new Date(i.getTime()-864e5);return n.toDateString()===a.toDateString()?`${s("yesterday")} ${o}`:`${n.toLocaleDateString(v,{day:"2-digit",month:"2-digit"})} ${o}`}function he(r){if(!r)return s("never");let e=Math.max(0,Date.now()/1e3-r),t=new Intl.RelativeTimeFormat(v,{numeric:"auto"});return e<60?t.format(-Math.round(e),"second"):e<3600?t.format(-Math.round(e/60),"minute"):e<86400?t.format(-Math.round(e/3600),"hour"):t.format(-Math.round(e/86400),"day")}var P=r=>`${r.baud} ${r.data_bits}${r.parity.toUpperCase()}${r.stop_bits}`,ue=(r,e,t,n=!1)=>l`<button type="button" class="switch" role="switch"
  aria-checked=${r?"true":"false"} aria-label=${e} ?disabled=${n} @click=${()=>t(!r)}><span></span></button>`;async function fe(r){try{return await navigator.clipboard.writeText(r),!0}catch{let e=document.createElement("textarea");e.value=r,e.style.position="fixed",e.style.opacity="0",document.body.appendChild(e),e.select();let t=document.execCommand("copy");return e.remove(),t}}function me(r,e){return r.enabled?r.present===!1?["stMissing","bad"]:e?r.pending==="reconfigured"?["stPending","info"]:["stRunning","ok"]:["stWaiting","warn"]:["stDisabled",""]}var Me=r=>{let t=r.addresses.find(n=>n.target==="lan"&&n.reachable)||r.addresses.find(n=>n.target==="ha");return t?Object.values(t.urls)[0]:""},te=r=>{location.hash=r};function R(r,e,t){return new Promise(n=>{let i=document.createElement("s2n-confirm");i.message=e,i.confirmLabel=t||s("confirm"),i.addEventListener("done",o=>{i.remove(),n(o.detail)}),(r.shadowRoot||document.body).appendChild(i)})}var Lt=2e3,zt=1500,H=class extends _{constructor(){super(),this.state=null,this.events=[],this.offline=!1,this.toast="",this._seq=0,this.route=this._parse(),this._onHash=()=>{this.route=this._parse(),window.scrollTo(0,0)}}connectedCallback(){super.connectedCallback(),window.addEventListener("hashchange",this._onHash),this.addEventListener("s2n-refresh",()=>this.refresh()),this.addEventListener("s2n-toast",e=>this.showToast(e.detail)),this.addEventListener("s2n-lang",e=>{st(e.detail),document.documentElement.lang=e.detail,this.requestUpdate(),this._relayLang()}),document.documentElement.lang=v,this._loadHistory(),this.refresh(),this._timer=setInterval(()=>this.refresh(),Lt)}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("hashchange",this._onHash),clearInterval(this._timer)}_relayLang(){this.renderRoot.querySelectorAll("main > *").forEach(e=>e.requestUpdate&&e.requestUpdate())}_parse(){let e=(location.hash.replace(/^#\/?/,"")||"connections").split("/");return{page:e[0],id:e[1]||""}}async _loadHistory(){try{let e=await h("api/history?limit=300"),t=new Set(this.events.map(n=>n.id));this.events=[...e.reverse().filter(n=>!t.has(n.id)),...this.events]}catch{}}async refresh(){try{let[e,t]=await Promise.all([h("api/state"),h(`api/events?after=${this._seq}`)]);if(this.state=e,t.length){this._seq=t[t.length-1].seq;let n=new Map(this.events.map((o,a)=>[o.id??`s${o.seq}`,a])),i=[...this.events];for(let o of t){let a=o.id??`s${o.seq}`;n.has(a)?i[n.get(a)]=o:(n.set(a,i.length),i.push(o))}this.events=i.slice(-zt)}this.offline=!1}catch{this.offline=!0}}showToast(e){this.toast=e,clearTimeout(this._toastTimer),this._toastTimer=setTimeout(()=>{this.toast=""},4500)}_page(){let{page:e,id:t}=this.route,n=this.state,i=this.events;if(!n)return l`<p class="hint">${s("loading")}</p>`;switch(e){case"connection":return l`<s2n-detail .state=${n} .events=${i} .connectionId=${t}></s2n-detail>`;case"edit":return l`<s2n-edit .state=${n} .connectionId=${t}></s2n-edit>`;case"import":return l`<s2n-import .state=${n}></s2n-import>`;case"events":return l`<s2n-events .state=${n} .events=${i}></s2n-events>`;case"trace":return l`<s2n-trace .state=${n} .selected=${t}></s2n-trace>`;case"settings":return l`<s2n-settings .state=${n}></s2n-settings>`;default:return l`<s2n-connections .state=${n}></s2n-connections>`}}render(){let e=this.state,t=this.route.page,n=["connection","edit","import"].includes(t)?"connections":t,i=(a,c)=>l`<a href="#/${a}" aria-current=${n===a?"page":"false"}>${s(c)}</a>`,o=e&&e.ser2net_running;return l`
      <header><div class="bar">
        <div class="brand">${nt()}<div><b>${s("appTitle")}</b>
          <span class="hint">${e?`App ${e.version} \xB7 ser2net ${e.ser2net_version||"?"}`:""}</span></div>
          ${e?l`<span class="chip ${o?"ok":"bad"}"><span class="dot"></span>${s(o?"running":"notRunning")}</span>`:""}
        </div>
        <nav aria-label=${s("navMain")}>
          ${i("connections","navConnections")}${i("events","navEvents")}${i("trace","navTrace")}${i("settings","navSettings")}
        </nav>
      </div></header>
      ${this.offline?l`<div class="offline"><div class="note warn" role="status">${s("connectionLost")}</div></div>`:""}
      <main>${this._page()}</main>
      ${this.toast?l`<div class="toast" role="status">${this.toast}</div>`:""}`}};f(H,"properties",{state:{state:!0},events:{state:!0},route:{state:!0},offline:{state:!0},toast:{state:!0}}),f(H,"styles",[ce,de,g`
    :host { display: block; min-height: 100vh; background: var(--bg); }
    header { background: var(--surface); border-bottom: 1px solid var(--line); }
    .bar { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 0 24px; }
    .brand { display: flex; align-items: center; gap: 12px; padding: 14px 0; }
    .brand b { font-size: 18px; display: block; line-height: 1.2; }
    nav { display: flex; flex-wrap: wrap; }
    nav a { display: inline-flex; align-items: center; min-height: 48px; padding: 0 16px; font-weight: 500; color: var(--muted); text-decoration: none; border-bottom: 3px solid transparent; }
    nav a:hover { color: var(--text); }
    nav a[aria-current="page"] { color: var(--accent); border-bottom-color: var(--accent); }
    main { max-width: 1200px; margin: 0 auto; padding: 24px 24px 48px; }
    .offline { max-width: 1200px; margin: 12px auto 0; padding: 0 24px; }
    .toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--text); color: var(--surface);
      padding: 12px 18px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.25); max-width: min(560px, calc(100vw - 32px)); z-index: 10; }
    @media (max-width: 600px) { .bar, main, .offline { padding-left: 16px; padding-right: 16px; } }
  `]);var m=class extends _{refresh(){this.dispatchEvent(new CustomEvent("s2n-refresh",{bubbles:!0,composed:!0}))}toast(e){this.dispatchEvent(new CustomEvent("s2n-toast",{detail:e,bubbles:!0,composed:!0}))}connection(e){return this.state?.connections.find(t=>t.id===e)}};f(m,"styles",[ce,de,g`:host { display: block; } .head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 20px; }`]);var F=class extends _{firstUpdated(){this.renderRoot.querySelector(".btn-g").focus()}_done(e){this.dispatchEvent(new CustomEvent("done",{detail:e}))}render(){return l`<div class="back" @keydown=${e=>e.key==="Escape"&&this._done(!1)}>
      <div class="box" role="alertdialog" aria-modal="true" aria-label=${s("confirm")}>
        <p>${this.message}</p>
        <div class="actions"><button class="btn btn-g" @click=${()=>this._done(!1)}>${s("cancel")}</button>
          <button class="btn btn-p" @click=${()=>this._done(!0)}>${this.confirmLabel}</button></div>
      </div></div>`}};f(F,"properties",{message:{},confirmLabel:{}}),f(F,"styles",[ce,de,g`
    .back { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 20; padding: 16px; }
    .box { background: var(--surface); border-radius: 16px; padding: 24px; max-width: 440px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
  `]);var B=class extends m{async _enable(e,t){this.busy=e.id;try{await h(`api/connections/${e.id}/enabled`,{method:"POST",body:{enabled:t}}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}finally{this.busy=""}}async _copy(e){await fe(Me(e))&&(this.copied=e.id,setTimeout(()=>{this.copied===e.id&&(this.copied="")},2e3))}_card(e,t,n){let[i,o]=me(e,t),a=!e.enabled,c=e.enabled&&e.present===!1,d=e.line_errors?Object.values(e.line_errors).reduce((p,y)=>p+y,0):0,u=[P(e),e.mode,`Port ${e.port}`];e.nodelay&&u.push("nodelay"),(e.latency==="set"||e.latency==="already")&&u.push("FTDI 1 ms"),e.trace!=="off"&&u.push(s("recording",{m:s(`tr_${e.trace}`)}));let b=e.clients.filter(p=>p.stuck);return l`<section class="card conn ${a?"off":""} ${c?"missing":""}" aria-label=${e.name}>
      <div class="top">
        <div style="min-width:0">
          <div class="title"><h2>${e.name}</h2><span class="chip ${o}"><span class="dot"></span>${s(i)}</span></div>
          <div class="dev mono">${e.device}${e.tty&&e.tty!==e.device?l` → ${e.tty}`:""}</div>
        </div>
        ${ue(e.enabled,s("switchLabel",{name:e.name}),p=>this._enable(e,p),n||this.busy===e.id)}
      </div>
      <div class="chips">
        ${u.map(p=>l`<span class="chip">${p}</span>`)}
        ${e.kept_open?l`<span class="chip info">${s("keptOpen")}</span>`:""}
        ${d?l`<span class="chip warn">${s("lineErrors",{n:d})}</span>`:""}
        ${e.latency==="read_only"?l`<span class="chip warn">${s("latencyRO")}</span>`:""}
        ${b.map(p=>l`<span class="chip bad">${s("stuck",{a:p.address})}</span>`)}
      </div>
      <div class="clients">
        <div class="row hint" style="font-weight:500"><span>${s("clients")}</span>
          <span>${s("clientsOf",{n:e.clients.length,m:e.max_clients})}${e.enabled&&e.present?l` · ${pe(e.rate_from_device)}`:""}</span></div>
        ${e.clients.map(p=>l`<div class="client"><span><span class="mono" style="font-size:13px">${p.address}</span></span>
          <span class="hint">${p.since?s("since",{t:he(p.since)}):""}</span></div>`)}
        ${e.clients.length?"":l`<div class="hint" style="font-size:14px">${a?s("disabledText"):c?s("missingText"):s("noClients")}</div>`}
      </div>
      <div class="foot">
        <div class="addr"><span class="mono">${Me(e)}</span>
          <button class="btn btn-g" style="min-height:36px" @click=${()=>this._copy(e)} aria-label=${s("copy")}>${x("copy",16)}${this.copied===e.id?s("copied"):s("copy")}</button></div>
        <div style="display:flex;gap:4px"><a class="btn btn-g" href="#/edit/${e.id}">${s("edit")}</a><a class="btn btn-s" href="#/connection/${e.id}">${s("details")}</a></div>
      </div>
    </section>`}render(){let e=this.state,t=e.source==="custom",n=e.connections,i=n.filter(c=>c.enabled).length,o=n.reduce((c,d)=>c+d.clients.length,0),a=n.reduce((c,d)=>c+(d.line_errors?Object.values(d.line_errors).reduce((u,b)=>u+b,0):0),0);return l`
      <div class="head">
        <div><h1>${s("connectionsTitle")}</h1><p class="sub">${s("connectionsSub")}</p></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <a class="btn btn-s" href="#/import">${x("upload")}${s("importExport")}</a>
          <a class="btn btn-p" href="#/edit/new">${x("plus")}${s("addConnection")}</a>
        </div>
      </div>
      ${t?l`<div class="note info" style="margin-bottom:20px">
        <b>${s("customActive")}</b> · ${s("customActiveText")}
        ${e.custom_ports.map(c=>l` <span class="chip">${c.alias} · ${c.clients.length}</span>`)}
        · <a href="#/settings">${s("toSettings")}</a></div>`:""}
      <div class="tiles">
        <div class="tile"><span class="lbl">${s("tileActive")}</span><b>${i} <small>${s("tileOf",{n:n.length})}</small></b></div>
        <div class="tile"><span class="lbl">${s("tileClients")}</span><b>${o}</b></div>
        <div class="tile"><span class="lbl">${s("tileErrors")}</span><b style=${a?"color:var(--warn)":""}>${a}</b></div>
        <div class="tile"><span class="lbl">${s("tileReach")}</span><b style="font-size:16px;margin-top:10px">${s(`listen_${e.settings.listen}`)}</b></div>
      </div>
      ${n.length?l`<div class="cards">${n.map(c=>this._card(c,e.ser2net_running,t))}</div>`:l`
        <section class="card empty"><h2>${s("emptyTitle")}</h2><p class="hint" style="font-size:14px">${s("emptyText")}</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">
            <a class="btn btn-s" href="#/import">${x("upload")}${s("emptyImport")}</a>
            <a class="btn btn-p" href="#/edit/new">${x("plus")}${s("addConnection")}</a></div></section>`}`}};f(B,"properties",{state:{attribute:!1},copied:{state:!0},busy:{state:!0}}),f(B,"styles",[...m.styles,g`
    .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
    .tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 20px; }
    .tile b { display: block; font-size: 28px; font-weight: 500; margin-top: 4px; }
    .tile small { font-size: 15px; color: var(--muted); font-weight: 400; }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 480px), 1fr)); gap: 16px; }
    .conn.off { background: var(--surface-2); }
    .conn.missing { border-color: var(--bad-line); }
    .top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .title { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
    .title h2 { font-size: 18px; }
    .dev { font-size: 12px; color: var(--muted); overflow-wrap: anywhere; margin-top: 6px; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .clients { border-top: 1px solid var(--line-2); padding-top: 12px; display: flex; flex-direction: column; gap: 8px; }
    .client { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 12px; }
    .foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; }
    .addr { display: flex; align-items: center; gap: 4px; background: var(--surface-2); border-radius: 10px; padding: 2px 2px 2px 12px; min-width: 0; max-width: 100%; }
    .addr .mono { font-size: 13px; overflow-wrap: anywhere; }
    .empty { text-align: center; padding: 48px 20px; align-items: center; }
  `]);var Ot=1e3,Mt=90,U=class extends m{constructor(){super(),this.chunks=[],this.paused=!1,this.ascii=!0,this._samples=[],this._after=0}connectedCallback(){super.connectedCallback(),this._timer=setInterval(()=>this._poll(),Ot),this._poll()}disconnectedCallback(){super.disconnectedCallback(),clearInterval(this._timer)}willUpdate(e){if(e.has("connectionId")&&(this.chunks=[],this._after=0,this._samples=[]),e.has("state")){let t=this.connection(this.connectionId);t&&(this._samples=[...this._samples,t.rate_from_device].slice(-Mt))}}async _poll(){if(!(this.paused||!this.connectionId))try{let e=await h(`api/live/${this.connectionId}?after=${this._after}`);e.length&&(this._after=e[e.length-1].seq,this.chunks=[...this.chunks,...e].slice(-300))}catch{}}async _enable(e,t){try{await h(`api/connections/${e.id}/enabled`,{method:"POST",body:{enabled:t}}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}}async _copy(e,t){await fe(t)&&(this.copied=e,setTimeout(()=>{this.copied===e&&(this.copied="")},2e3))}_live(){let e=this.chunks.slice(-120).reverse();return l`<section class="card" aria-labelledby="t-live">
      <div class="row"><div><h2 id="t-live">${s("live")}</h2><p class="hint">${s("liveSub")}</p></div>
        <div style="display:flex;gap:4px">
          <button class="btn btn-g" aria-pressed=${this.ascii?"true":"false"} @click=${()=>{this.ascii=!this.ascii}}>${this.ascii?s("hexOnly"):s("hexAscii")}</button>
          <button class="btn btn-g" @click=${()=>{this.paused=!this.paused}}>${this.paused?s("resume"):s("pause")}</button>
        </div></div>
      ${e.length?l`<div class="code live" style="padding:8px 4px"><table><tbody>
        ${e.map(t=>l`<tr>
          <td style="color:#8f9ba8">${new Date(t.ts*1e3).toLocaleTimeString(void 0,{hour12:!1})}.${String(Math.floor(t.ts*1e3)%1e3).padStart(3,"0")}</td>
          <td><span class="dir ${t.direction==="rx"?"rx":t.direction==="tx"?"tx":"mark"}">${t.direction.toUpperCase()}</span></td>
          <td>${t.direction==="open"||t.direction==="close"?t.text:t.hex}</td>
          ${this.ascii&&t.hex?l`<td style="color:#9fb3c8">${t.text.replace(/[^\x20-\x7e]/g,".")}</td>`:""}
        </tr>`)}</tbody></table></div>`:l`<div class="well hint" style="font-size:14px">${s("liveEmpty")}</div>`}
    </section>`}_sparkline(){let e=this._samples.length>1?this._samples:[0,0],t=Math.max(...e,1),n=300/(e.length-1),i=e.map((o,a)=>`${(a*n).toFixed(1)},${(66-o/t*56).toFixed(1)}`);return l`<svg viewBox="0 0 300 70" width="100%" height="70" role="img" aria-label=${s("dataFromDevice")}>
      ${oe`<path d="M0,70 L${i.join(" L")} L300,70 Z" fill="var(--accent-soft)"></path>
      <path d="M${i.join(" L")}" fill="none" stroke="var(--accent)" stroke-width="2"></path>`}</svg>`}render(){let e=this.state,t=this.connection(this.connectionId);if(!t)return l`<p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a></p><p>${s("error")}</p>`;let[n,i]=me(t,e.ser2net_running),o=this.events.filter(d=>d.connection===t.id).slice(-6).reverse(),a=t.line_errors,c=t.usb;return l`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${t.name}</p>
      <div class="head" style="margin-top:12px">
        <div class="row" style="justify-content:flex-start"><h1>${t.name}</h1>
          <span class="chip ${i}"><span class="dot"></span>${s(n)}</span>
          ${t.kept_open?l`<span class="chip info">${s("keptOpen")}</span>`:""}</div>
        <div class="row">
          <a class="btn btn-s" href="#/trace/${t.id}">${s("navTrace")}</a>
          <a class="btn btn-s" href="#/edit/${t.id}">${s("edit")}</a>
          ${ue(t.enabled,s("switchLabel",{name:t.name}),d=>this._enable(t,d),e.source==="custom")}
        </div>
      </div>
      <div class="cols">
        <div class="main-col">
          ${this._live()}
          <section class="card" aria-labelledby="t-clients">
            <div class="row"><h2 id="t-clients">${s("clients")}</h2><span class="hint" style="font-size:13px">${s("clientsOf",{n:t.clients.length,m:t.max_clients})}</span></div>
            ${t.clients.length?l`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${s("clientTh")}</th><th>${s("sinceTh")}</th><th style="text-align:right">${s("toClient")}</th><th style="text-align:right">${s("fromClient")}</th><th style="text-align:right">${s("queued")}</th></tr></thead>
              <tbody>${t.clients.map(d=>l`<tr>
                <td class="mono" style="font-size:12px">${d.address} ${d.stuck?l`<span class="chip bad">${s("stuck",{a:""})}</span>`:""}</td>
                <td>${d.since?w(d.since):"\u2013"}</td><td style="text-align:right">${T(d.bytes_to_client)}</td>
                <td style="text-align:right">${T(d.bytes_from_client)}</td><td style="text-align:right">${T(d.queued)}</td></tr>`)}</tbody></table></div>`:l`<p class="hint" style="font-size:14px">${s("noClients")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-addr">
            <h2 id="t-addr">${s("addresses")}</h2>
            ${t.addresses.map(d=>l`<div class="well row">
              <div style="min-width:0"><div class="hint">${s(`target_${d.target}`)}</div>
                ${d.reachable?Object.entries(d.urls).map(([u,b])=>l`<div class="row" style="justify-content:flex-start;gap:4px">
                  <span class="mono" style="font-size:13px;overflow-wrap:anywhere">${b}</span>
                  <button class="btn btn-g" style="min-height:32px" @click=${()=>this._copy(`${d.target}${u}`,b)}>${this.copied===`${d.target}${u}`?s("copied"):s("copy")}</button></div>`):l`<div class="hint">${d.host?s("notReachable"):s("lanUnknown")}</div>`}
              </div></div>`)}
          </section>
          <section class="card" aria-labelledby="t-conf">
            <div class="row"><h2 id="t-conf">${s("configuration")}</h2><a href="#/edit/${t.id}" style="font-size:13px">${s("edit")}</a></div>
            <div class="kv">
              <span>${s("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${t.device}</span>
              <span>${s("resolved")}</span><span class="mono" style="font-size:13px">${t.tty||"\u2013"}</span>
              ${c?l`<span>${s("usb")}</span><span>${[c.manufacturer,c.product].filter(Boolean).join(" \xB7 ")||`${c.vendor_id}:${c.product_id}`}${c.serial?` \xB7 ${s("serialNo")} ${c.serial}`:""}${c.driver?` \xB7 ${c.driver}`:""}</span>`:""}
              <span>${s("interface")}</span><span>${P(t)}${t.rtscts?" \xB7 RTS/CTS":""}${t.xonxoff?" \xB7 XON/XOFF":""}${t.local?" \xB7 local":""}</span>
              <span>${s("network")}</span><span>${t.mode} · Port ${t.port} · ${t.bind||s(`listen_${e.settings.listen}`)}</span>
            </div>
          </section>
        </div>
        <aside class="side-col">
          <section class="card" aria-labelledby="t-line">
            <div class="row"><h2 id="t-line">${s("line")}</h2>
              ${a&&!Object.values(a).some(Boolean)?l`<span class="chip ok">${s("noLineErrors")}</span>`:""}</div>
            ${a?l`<div class="counters">
              ${[["frame",a.frame],["parity",a.parity],["overrun",a.overrun],["brk",a.break],["bufOverrun",a.buffer_overrun]].map(([d,u])=>l`<div class="well"><span class="hint">${s(d)}</span><b style=${u?"color:var(--warn)":""}>${u}</b></div>`)}</div>`:l`<p class="hint">${t.line_errors===null&&t.clients.length?s("lineUnsupported"):s("lineClosed")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-rate">
            <div class="row"><h2 id="t-rate">${s("dataFromDevice")}</h2><b style="font-size:18px;font-weight:500">${pe(t.rate_from_device)}</b></div>
            ${this._sparkline()}
            <div class="row hint"><span>${s("lastData")}: ${t.last_data?he(t.last_data):s("never")}</span><span>${T(t.bytes_from_device)}</span></div>
          </section>
          <section class="card" aria-labelledby="t-recent">
            <div class="row"><h2 id="t-recent">${s("recent")}</h2><a href="#/events" style="font-size:13px">${s("allEvents")}</a></div>
            <ol>${o.map(d=>l`<li><span class="dot" style="color:${d.level==="warning"?"var(--warn)":d.level==="error"?"var(--bad)":"var(--ok)"}"></span>
              <div><div>${N(d)}${d.count>1?l` <span class="chip">${s("summed",{n:d.count})}</span>`:""}</div><div class="hint">${w(d.ts)}</div></div></li>`)}</ol>
          </section>
        </aside>
      </div>`}};f(U,"properties",{state:{attribute:!1},events:{attribute:!1},connectionId:{},chunks:{state:!0},paused:{state:!0},ascii:{state:!0},copied:{state:!0}}),f(U,"styles",[...m.styles,g`
    .kv { display: grid; grid-template-columns: minmax(110px, 170px) minmax(0, 1fr); gap: 10px 16px; }
    .kv > :nth-child(odd) { color: var(--muted); }
    .counters { display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px; }
    .counters b { display: block; font-size: 20px; font-weight: 500; }
    .live { max-height: 340px; overflow: auto; }
    .live table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .live td { border: none; padding: 2px 8px; white-space: pre; }
    .dir { display: inline-block; min-width: 30px; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
    ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
    li { display: flex; gap: 10px; } li .dot { margin-top: 6px; }
  `]);var be={name:"",device:"",port:3333,enabled:!0,template:"generic",baud:9600,data_bits:8,parity:"n",stop_bits:1,mode:"raw",max_clients:1,local:!0,rtscts:!1,xonxoff:!1,hangup_when_done:!1,nobreak:!1,dtr:"",rts:"",rs485:"",low_latency:!1,timeout:0,kickolduser:!1,chardelay:!0,remaddr:"",banner:"",openstr:"",closestr:"",connector_retry_time:0,nodelay:!1,bind:"",extra:[],keep_open:!1,stuck_disconnect:!1,trace:"off",notify_missing:!0,notify_no_client:!1,silence_minutes:0},it={ehz_sml:{baud:9600,data_bits:8,parity:"n",stop_bits:1,max_clients:5,chardelay:!0,nodelay:!1},ehz_d0:{baud:9600,data_bits:7,parity:"e",stop_bits:1,max_clients:5,chardelay:!0,nodelay:!1},zwave:{baud:115200,data_bits:8,parity:"n",stop_bits:1,max_clients:2,chardelay:!1,nodelay:!0},generic:{baud:9600,data_bits:8,parity:"n",stop_bits:1,max_clients:1,chardelay:!0,nodelay:!1}},Nt=[300,1200,2400,4800,9600,19200,38400,57600,115200,230400,460800,921600],at=["rtscts","xonxoff","hangup_when_done","nobreak","low_latency","kickolduser","nodelay","keep_open","stuck_disconnect"],Pt=r=>r.map(([e,t])=>`${e}: ${t}`).join(`
`),Rt=r=>r.split(`
`).map(e=>e.trim()).filter(Boolean).map(e=>{let t=e.indexOf(":");return t<0?[e,""]:[e.slice(0,t).trim(),e.slice(t+1).trim()]}),rt=r=>Object.fromEntries(Object.entries(r||{}).map(([e,t])=>[e.replace(/^connections\.\d+\./,""),t])),j=class extends m{willUpdate(e){(e.has("connectionId")||this.draft===void 0&&this.state)&&this._load()}_load(){let e=this.connection(this.connectionId);if(e){let t={};for(let n of[...Object.keys(be),"id"])t[n]=e[n];this.draft=t}else{let t=this.state.connections.map(i=>i.port),n=this.state.devices.find(i=>!i.used_by);this.draft={...be,port:t.length?Math.max(...t)+1:3333,device:n?n.stable:""}}this.extraRaw=Pt(this.draft.extra),this.otherDevice=!!this.draft.device&&!this.state.devices.some(t=>t.stable===this.draft.device||t.by_id.includes(this.draft.device)||t.by_path.includes(this.draft.device)),this.errors={},this.touched=new Set(e?Object.keys(be):[]),this.advanced=at.some(t=>this.draft[t])||!!(this.draft.remaddr||this.draft.bind||this.draft.extra.length||this.draft.timeout),this._preview()}_set(e){this.draft={...this.draft,...e},this.touched=new Set([...this.touched,...Object.keys(e)]),clearTimeout(this._pt),this._pt=setTimeout(()=>this._preview(),300)}async _preview(){try{let e=await h("api/preview",{method:"POST",body:{connection:this.draft}});this.yaml=e.yaml,this.errors=rt(e.errors)}catch{}}async _save(e){e.preventDefault(),this.saving=!0,this.touched=new Set(Object.keys(be));try{let t=await le(this.draft),n=t.rebuilt.length?s("savedRebuilt",{n:t.rebuilt.join(", ")}):s("saved");t.disconnected.length&&(n+=s("savedReconnect",{n:t.disconnected.join(", ")})),this.toast(n),this.refresh(),te(`#/connection/${this.draft.id||t.id}`)}catch(t){this.errors=rt(t.data.errors),this.toast(t.data.errors?s("errorsBelow"):`${s("error")}: ${t.message}`)}finally{this.saving=!1}}async _delete(){if(await R(this,s("deleteConfirm",{n:this.draft.name}),s("delete")))try{await h(`api/connections/${this.draft.id}`,{method:"DELETE"}),this.refresh(),te("#/connections")}catch(e){this.toast(`${s("error")}: ${e.message}`)}}_shown(){return Object.fromEntries(Object.entries(this.errors).filter(([e])=>this.touched.has(e)))}_err(e){let t=this._shown();return t[e]?l`<span class="err" id="e-${e}">${Le(t[e])}</span>`:""}_input(e,t,{type:n="text",hint:i="",mono:o=!1,number:a=!1}={}){let c=this.draft[e];return l`<label class="fld"><span class="lbl">${t}</span>
      <input class="inp ${o?"mono":""}" type=${n} .value=${String(c??"")} inputmode=${a?"numeric":"text"}
        aria-invalid=${this._shown()[e]?"true":"false"} aria-describedby="e-${e}"
        @input=${d=>this._set({[e]:a?Number(d.target.value||0):d.target.value})}>
      ${this._err(e)}${i?l`<span class="hint">${i}</span>`:""}</label>`}_check(e){return l`<label class="chk"><input type="checkbox" .checked=${!!this.draft[e]} @change=${t=>this._set({[e]:t.target.checked})}>
      <span>${s(`o_${e}`)}${e!=="keep_open"&&e!=="stuck_disconnect"&&!e.startsWith("notify")?l`<br><span class="hint mono">${e.replace(/_/g,"-")}</span>`:""}</span></label>`}_deviceLabel(e){let t=[e.manufacturer,e.product].filter(Boolean).join(" ")||e.driver||e.tty,n=e.serial?`${s("serialNo")} ${e.serial}`:s("noSerial"),i=e.used_by&&e.used_by!==this.draft.name?` (${s("usedBy",{n:e.used_by})})`:"";return`${t} \xB7 ${n} \xB7 ${e.tty}${i}`}render(){let e=this.draft;if(!e)return l`<p class="hint">${s("loading")}</p>`;let t=this.state.devices,n=t.find(a=>a.stable===e.device||a.by_id.includes(e.device)||a.by_path.includes(e.device)),i=at.filter(a=>e[a]).length+["remaddr","bind","rs485","banner","openstr","closestr"].filter(a=>e[a]).length+(e.extra.length?1:0),o=!e.id;return l`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${o?s("newConnection"):e.name}</p>
      <h1 style="margin:12px 0 20px">${o?s("newConnection"):s("editConnection")}</h1>
      <div class="cols"><form class="main-col" @submit=${this._save} novalidate>
        <section class="card" aria-labelledby="t-tpl">
          <div><h2 id="t-tpl">${s("template")}</h2><p class="hint" style="margin-top:4px">${s("templateSub")}</p></div>
          <div class="choices">${Object.keys(it).map(a=>l`<button type="button" class="choice" aria-pressed=${e.template===a?"true":"false"}
            @click=${()=>this._set({template:a,...it[a]})}><b style="font-weight:500">${s(`tpl_${a}`)}</b><span class="hint">${s(`tplsub_${a}`)}</span></button>`)}</div>
        </section>

        <section class="card" aria-labelledby="t-base">
          <h2 id="t-base">${s("basics")}</h2>
          <div class="grid2">${this._input("name",s("name"))}
            <div class="fld"><span class="lbl">${s("enabled")}</span><label class="chk" style="min-height:42px;align-items:center">
              <input type="checkbox" .checked=${e.enabled} @change=${a=>this._set({enabled:a.target.checked})}><span>${s("enabledText")}</span></label></div></div>
          <label class="fld"><span class="lbl">${s("devicePick")}</span>
            <select class="inp" aria-invalid=${this._shown().device?"true":"false"} @change=${a=>{if(a.target.value==="__other"){this.otherDevice=!0;return}this.otherDevice=!1,this._set({device:a.target.value})}}>
              ${e.device?"":l`<option value="" selected>–</option>`}
              ${t.map(a=>l`<option value=${a.stable} ?selected=${!this.otherDevice&&n===a}>${this._deviceLabel(a)}</option>`)}
              <option value="__other" ?selected=${this.otherDevice}>${s("deviceOther")}</option>
            </select>
            ${this.otherDevice?l`<input class="inp mono" .value=${e.device} placeholder="/dev/serial/by-id/…" @input=${a=>this._set({device:a.target.value})}>`:l`<span class="hint mono" style="overflow-wrap:anywhere">${e.device}</span>`}
            ${this._err("device")}</label>
          ${n&&n.ambiguous?l`<div class="note warn" role="note">${s("ambiguous")}</div>`:""}
        </section>

        <section class="card" aria-labelledby="t-if">
          <h2 id="t-if">${s("ifNet")}</h2>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("baud")}</span><select class="inp" @change=${a=>this._set({baud:Number(a.target.value)})}>
              ${[...new Set([...Nt,e.baud])].sort((a,c)=>a-c).map(a=>l`<option value=${a} ?selected=${a===e.baud}>${a}</option>`)}</select>${this._err("baud")}</label>
            <label class="fld"><span class="lbl">${s("dataBits")} · ${s("parityF")} · ${s("stopBits")}</span>
              <div style="display:flex;gap:6px">
                <select class="inp" aria-label=${s("dataBits")} @change=${a=>this._set({data_bits:Number(a.target.value)})}>${[5,6,7,8].map(a=>l`<option ?selected=${a===e.data_bits}>${a}</option>`)}</select>
                <select class="inp" aria-label=${s("parityF")} @change=${a=>this._set({parity:a.target.value})}>${["n","e","o","m","s"].map(a=>l`<option value=${a} ?selected=${a===e.parity}>${a.toUpperCase()}</option>`)}</select>
                <select class="inp" aria-label=${s("stopBits")} @change=${a=>this._set({stop_bits:Number(a.target.value)})}>${[1,2].map(a=>l`<option ?selected=${a===e.stop_bits}>${a}</option>`)}</select>
              </div></label>
            ${this._input("port",s("port"),{number:!0})}
            ${this._input("max_clients",s("maxClients"),{number:!0,hint:s("maxClientsHint")})}
          </div>
          <div class="fld"><span class="lbl" id="l-mode">${s("mode")}</span>
            <div class="seg" role="group" aria-labelledby="l-mode">${["raw","rfc2217","telnet"].map(a=>l`<button type="button" aria-pressed=${e.mode===a?"true":"false"} @click=${()=>this._set({mode:a})}>${a==="rfc2217"?"RFC2217":a}</button>`)}</div>
            <span class="hint">${s(`mode_${e.mode}`)}</span></div>
        </section>

        <section class="card" aria-labelledby="t-adv">
          <button type="button" class="toggle-head" aria-expanded=${this.advanced?"true":"false"} @click=${()=>{this.advanced=!this.advanced}}>
            <span><h2 id="t-adv">${s("advanced")}</h2><span class="hint">${s("advancedSub")}</span></span>
            <span class="chip">${s("set",{n:i})} · ${this.advanced?s("closeA"):s("open")}</span></button>
          ${this.advanced?l`
            <fieldset><legend>${s("serialSide")}</legend>
              <div class="opts">${["local","rtscts","xonxoff","hangup_when_done","nobreak"].map(a=>this._check(a))}
                ${n&&n.ftdi||e.low_latency?this._check("low_latency"):""}</div>
              <div class="grid2">
                ${["dtr","rts"].map(a=>l`<label class="fld"><span class="lbl">${s(a)}</span><select class="inp" @change=${c=>this._set({[a]:c.target.value})}>
                  ${[["",s("lineDefault")],["on",s("on")],["off",s("off")]].map(([c,d])=>l`<option value=${c} ?selected=${e[a]===c}>${d}</option>`)}</select></label>`)}
                ${this._input("rs485",s("rs485"),{mono:!0,hint:s("rs485Hint")})}
              </div></fieldset>
            <fieldset><legend>${s("connectionSide")}</legend>
              <div class="opts">${this._check("kickolduser")}${this._check("chardelay")}</div>
              <div class="grid2">${this._input("timeout",s("timeout"),{number:!0})}${this._input("connector_retry_time",s("retry"),{number:!0})}</div>
              ${this._input("remaddr",s("remaddr"),{mono:!0,hint:s("remaddrHint")})}
              <div class="grid2">${this._input("banner",s("banner"))}${this._input("openstr",s("openstr"),{mono:!0})}${this._input("closestr",s("closestr"),{mono:!0})}</div>
            </fieldset>
            <fieldset><legend>${s("tcpSide")}</legend>
              <div class="opts">${this._check("nodelay")}</div>
              ${this._input("bind",s("bind"),{mono:!0,hint:s("bindHint")})}
            </fieldset>
            <label class="fld"><span class="lbl">${s("extra")}</span>
              <textarea class="inp mono" rows="3" .value=${this.extraRaw} aria-invalid=${this._shown().extra?"true":"false"}
                @input=${a=>{this.extraRaw=a.target.value,this._set({extra:Rt(a.target.value)})}}></textarea>
              ${this._err("extra")}<span class="hint">${s("extraHint")}</span></label>`:""}
        </section>

        <section class="card" aria-labelledby="t-app">
          <h2 id="t-app">${s("appSide")}</h2>
          <div class="opts">${this._check("keep_open")}${this._check("stuck_disconnect")}${this._check("notify_missing")}${this._check("notify_no_client")}</div>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("traceMode")}</span><select class="inp" @change=${a=>this._set({trace:a.target.value})}>
              ${["off","rx","tx","both"].map(a=>l`<option value=${a} ?selected=${e.trace===a}>${s(`tr_${a}`)}</option>`)}</select></label>
            ${this._input("silence_minutes",s("silence"),{number:!0})}
          </div>
        </section>

        <div class="actions">
          <span class="hint" style="display:flex;align-items:center;gap:8px">${x("info",16)}${s("saveHint")}</span>
          <div style="display:flex;gap:8px">
            ${o?"":l`<button type="button" class="btn btn-d" @click=${this._delete}>${s("delete")}</button>`}
            <a class="btn btn-g" href=${o?"#/connections":`#/connection/${e.id}`}>${s("cancel")}</a>
            <button type="submit" class="btn btn-p" ?disabled=${this.saving}>${s("save")}</button>
          </div>
        </div>
      </form>

      <aside class="side-col">
        <section class="card" aria-labelledby="t-prev">
          <div><h2 id="t-prev">${s("preview")}</h2><p class="hint" style="margin-top:4px">${s("previewSub")}</p></div>
          <div class="code">${this.yaml||"\u2026"}</div>
          ${Object.keys(this._shown()).length?l`<div class="note bad">${Object.entries(this._shown()).map(([a,c])=>l`<div><span class="mono">${a}</span>: ${Le(c)}</div>`)}</div>`:""}
        </section>
      </aside></div>`}};f(j,"properties",{state:{attribute:!1},connectionId:{},draft:{state:!0},errors:{state:!0},yaml:{state:!0},advanced:{state:!0},otherDevice:{state:!0},saving:{state:!0},extraRaw:{state:!0},touched:{state:!0}}),f(j,"styles",[...m.styles,g`
    form { display: contents; }
    fieldset { border: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
    legend { padding: 0; margin-bottom: 8px; font-size: 13px; font-weight: 500; }
    .opts { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 6px 16px; }
    .toggle-head { display: flex; align-items: center; justify-content: space-between; width: 100%; background: none; border: none; padding: 0;
      min-height: 44px; cursor: pointer; font: inherit; color: inherit; text-align: left; }
    .actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  `]);var Ht=["info","warning","error","debug"],I=class extends m{constructor(){super(),this.tab="live",this.conn="",this.query="",this.levels=new Set(["info","warning","error"]),this.paused=null}async _loadHistory(){let e=this.state.settings.history_days,t=Date.now()/1e3-e*86400;try{[this.stats,this.history]=await Promise.all([h(`api/stats?days=${Math.min(e,30)}`),h(`api/history?since=${t}&limit=2000${this.conn?`&connection=${this.conn}`:""}`)])}catch(n){this.toast(`${s("error")}: ${n.message}`)}}_filtered(e){let t=this.query.trim().toLowerCase();return e.filter(n=>this.levels.has(n.level)&&(!this.conn||n.connection===this.conn)&&(!t||`${n.name} ${N(n)}`.toLowerCase().includes(t)))}_live(){let e=this.paused||this.events,t=this._filtered(e).slice(-500).reverse(),n={info:"info",warning:"warn",error:"bad",debug:""};return l`<section class="card" style="padding:0;gap:0;overflow:hidden" aria-label=${s("tabLive")}>
      <div class="row" style="padding:12px 16px;border-bottom:1px solid var(--line)">
        <span class="hint" style="font-size:13px;display:flex;align-items:center;gap:8px"><span class="dot" style="color:${this.paused?"var(--muted)":"var(--ok)"}"></span>
          ${this.paused?s("paused"):s("liveState")} · ${s("entries",{n:t.length})}</span>
        <button class="btn btn-g" @click=${()=>{this.paused=this.paused?null:[...this.events]}}>${this.paused?s("resume"):s("pause")}</button></div>
      <div class="log" role="log">${t.map(i=>l`<div class="line">
        <span class="mono hint">${w(i.ts,!0,!0)}</span><span class="chip ${n[i.level]}" style="justify-content:center">${s(`lv_${i.level}`)}</span>
        <span style="overflow-wrap:anywhere"><b style="font-weight:500">[${i.name}]</b> ${N(i)}${i.count>1?l` <span class="chip">${s("summed",{n:i.count})}</span>`:""}</span></div>`)}
        ${t.length?"":l`<p class="hint" style="padding:32px 16px;text-align:center;font-size:14px">${s("noEntries")}</p>`}</div>
    </section>`}_historyView(){if(!this.stats||!this.history)return l`<p class="hint">${s("loading")}</p>`;let e=this.stats.days,t=this.state.connections.filter(o=>!this.conn||o.id===this.conn),n=new Map;for(let o of this._filtered(this.history)){let a=new Date(o.ts*1e3).toDateString();n.has(a)||n.set(a,[]),n.get(a).push(o)}let i=o=>{let a=new Date().toDateString(),c=new Date(Date.now()-864e5).toDateString();return o===a?s("today"):o===c?s("yesterday"):new Date(o).toLocaleDateString(v,{weekday:"short",day:"2-digit",month:"2-digit"})};return l`
      <div class="stats">${t.map(o=>{let a=this.stats.connections[o.id]||{drops:0,availability:1,per_day:Array(e).fill(0)},c=Math.max(...a.per_day,1);return l`<section class="card" aria-label=${o.name} style="gap:10px">
          <div class="row"><b style="font-weight:500">${o.name}</b><span class="chip ${a.drops?"warn":"ok"}">${a.drops?s("unstable",{n:a.drops}):s("stable")}</span></div>
          <div style="display:flex;gap:20px">
            <div><div class="hint">${s("drops",{d:e})}</div><div style="font-size:22px;font-weight:500">${a.drops}</div></div>
            <div><div class="hint">${s("availability")}</div><div style="font-size:22px;font-weight:500">${(a.availability*100).toLocaleString(v,{maximumFractionDigits:2})} %</div></div></div>
          <div class="bars" role="img" aria-label="${s("drops",{d:e})}: ${a.drops}">${a.per_day.map(d=>l`<span style="height:${d?20+d/c*80:8}%;${d?"background:var(--warn)":""}"></span>`)}</div>
        </section>`})}</div>
      <section class="card" aria-labelledby="t-tl">
        <div class="row"><h2 id="t-tl">${s("timeline")}</h2><span class="hint">${s("retention",{d:this.state.settings.history_days})}</span></div>
        ${[...n.entries()].slice(0,30).map(([o,a])=>l`<div class="day">
          <div class="hint" style="font-weight:500;text-transform:uppercase;letter-spacing:.04em">${i(o)}</div>
          ${a.slice(0,50).map(c=>l`<div class="item"><span class="mono hint">${w(c.ts,!1)}</span>
            <span class="dot" style="color:${c.level==="warning"?"var(--warn)":c.level==="error"?"var(--bad)":"var(--muted)"}"></span>
            <span><b style="font-weight:500">${c.name}</b> · ${N(c)}${c.count>1?l` <span class="chip">${s("summed",{n:c.count})}</span>`:""}</span></div>`)}
        </div>`)}
        ${n.size?"":l`<p class="hint" style="font-size:14px">${s("noEntries")}</p>`}
      </section>`}render(){let e=(t,n)=>l`<button role="tab" aria-selected=${this.tab===t?"true":"false"}
      @click=${()=>{this.tab=t,t==="history"&&this._loadHistory()}}>${s(n)}</button>`;return l`
      <div class="head"><div><h1>${s("eventsTitle")}</h1><p class="sub">${s("eventsSub")}</p></div>
        <div class="tabs" role="tablist">${e("live","tabLive")}${e("history","tabHistory")}</div></div>
      <div class="filters">
        <label class="fld"><span class="lbl">${s("navConnections")}</span>
          <select class="inp" @change=${t=>{this.conn=t.target.value,this.tab==="history"&&this._loadHistory()}}>
            <option value="">${s("allConnections")}</option>
            ${this.state.connections.map(t=>l`<option value=${t.id} ?selected=${this.conn===t.id}>${t.name}</option>`)}</select></label>
        <label class="fld" style="flex:1 1 220px"><span class="lbl">${s("search")}</span>
          <input class="inp" type="search" .value=${this.query} placeholder=${s("searchPh")} @input=${t=>{this.query=t.target.value}}></label>
        <div role="group" aria-label="Level" style="display:flex;flex-wrap:wrap;gap:6px">${Ht.map(t=>l`<button class="lv ${t}" aria-pressed=${this.levels.has(t)?"true":"false"}
          @click=${()=>{let n=new Set(this.levels);n.has(t)?n.delete(t):n.add(t),this.levels=n}}>${s(`lv_${t}`)}</button>`)}</div>
      </div>
      ${this.tab==="live"?this._live():this._historyView()}`}};f(I,"properties",{state:{attribute:!1},events:{attribute:!1},tab:{state:!0},conn:{state:!0},query:{state:!0},levels:{state:!0},paused:{state:!0},stats:{state:!0},history:{state:!0}}),f(I,"styles",[...m.styles,g`
    .tabs { display: inline-flex; background: var(--line); border-radius: 22px; padding: 4px; }
    .tabs button { min-height: 40px; padding: 0 18px; border: none; border-radius: 18px; cursor: pointer; font: inherit; font-weight: 500; background: transparent; color: var(--muted); }
    .tabs button[aria-selected="true"] { background: var(--surface); color: var(--accent-hover); box-shadow: 0 1px 2px rgba(0,0,0,.12); }
    .filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; margin-bottom: 20px; }
    .lv { min-height: 40px; padding: 0 14px; border-radius: 20px; cursor: pointer; font: inherit; font-size: 13px; font-weight: 500; border: 1px solid var(--input-line); background: var(--surface); color: var(--muted); }
    .lv[aria-pressed="true"].info { background: var(--accent-soft); color: var(--accent-hover); border-color: var(--accent); }
    .lv[aria-pressed="true"].warning { background: var(--warn-soft); color: var(--warn); border-color: var(--warn); }
    .lv[aria-pressed="true"].error { background: var(--bad-soft); color: var(--bad); border-color: var(--bad); }
    .lv[aria-pressed="true"].debug { background: var(--neutral-soft); color: var(--neutral); border-color: var(--neutral); }
    .log { max-height: 640px; overflow: auto; }
    .line { display: grid; grid-template-columns: 130px 78px minmax(0, 1fr); gap: 12px; align-items: baseline; padding: 8px 16px; border-bottom: 1px solid var(--line-2); }
    @media (max-width: 600px) { .line { grid-template-columns: auto auto; } .line > :last-child { grid-column: 1 / -1; } }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .bars { display: flex; align-items: flex-end; gap: 2px; height: 36px; }
    .bars span { flex: 1; min-width: 2px; border-radius: 2px; background: var(--line); }
    .day { display: flex; flex-direction: column; gap: 8px; }
    .item { display: grid; grid-template-columns: 56px 12px minmax(0, 1fr); gap: 10px; align-items: baseline; }
  `]);var V=class extends m{constructor(){super(),this.text="",this.replaceAll=!1,this.take=new Set,this.choice={},this.disabled=!0}async _file(e){e&&(this.text=await e.text(),this._preview())}async _preview(){this.error="";try{this.preview=await h("api/import/preview",{method:"POST",body:{text:this.text}}),this.take=new Set(this.preview.items.filter(e=>e.connection&&!Object.keys(e.conflicts).length).map(e=>e.alias)),this.choice=Object.fromEntries(this.preview.items.filter(e=>Object.keys(e.conflicts).length).map(e=>[e.alias,"skip"]))}catch(e){this.error=e.data.note?C(e.data.note):e.message}}async _apply(){this.busy=!0;let e=[...this.preview.items.filter(t=>t.connection&&(this.take.has(t.alias)||this.choice[t.alias]&&this.choice[t.alias]!=="skip")).map(t=>t.alias)];try{let t=await h("api/import",{method:"POST",body:{text:this.text,replace_all:this.replaceAll,take:e,on_conflict:this.choice}});this.done=t,this.refresh()}catch(t){this.toast(`${s("error")}: ${t.data.note?C(t.data.note):t.message}`)}finally{this.busy=!1}}_steps(e){return l`<ol class="steps" aria-label=${s("importTitle")}>${["stepChoose","stepPreview","stepDone"].map((t,n)=>l`<li class=${n===e?"on":n<e?"past":""} aria-current=${n===e?"step":"false"}>
      <span class="num">${n<e?"\u2713":n+1}</span>${s(t)}</li>`)}</ol>`}_choose(){return l`<section class="card" aria-labelledby="t-file"><h2 id="t-file">${s("importChoose")}</h2>
      <div class="drop" @dragover=${e=>{e.preventDefault(),e.currentTarget.classList.add("over")}}
        @dragleave=${e=>e.currentTarget.classList.remove("over")}
        @drop=${e=>{e.preventDefault(),e.currentTarget.classList.remove("over"),this._file(e.dataTransfer.files[0])}}>
        ${x("upload",40)}<b style="font-size:16px;font-weight:500">${s("importDrop")}</b><span class="hint">${s("importFormats")}</span>
        <label class="btn btn-p">${s("chooseFile")}<input type="file" class="sr" accept=".yaml,.yml,.conf,text/plain" @change=${e=>this._file(e.target.files[0])}></label>
      </div>
      <label class="fld"><span class="lbl">${s("pasteHere")}</span>
        <textarea class="inp mono" rows="6" .value=${this.text} @input=${e=>{this.text=e.target.value}}></textarea></label>
      ${this.error?l`<div class="note bad" role="alert">${this.error}</div>`:""}
      <div><button class="btn btn-s" ?disabled=${!this.text.trim()} @click=${this._preview}>${s("readPreview")}</button></div>
    </section>`}_result(e){return e.connection?Object.keys(e.conflicts).length&&!this.replaceAll?l`<span class="chip bad">${s("resConflict")}: ${Object.entries(e.conflicts).map(([t,n])=>`${t} \u2194 ${n}`).join(", ")}</span>`:e.notes.length?l`<span class="chip warn">${s("resNotes")}</span>`:l`<span class="chip ok">${s("resOk")}</span>`:l`<span class="chip bad">${s("resNo")}</span>`}_previewView(){let e=this.preview,n=e.items.filter(i=>i.connection).filter(i=>this.take.has(i.alias)||this.choice[i.alias]&&this.choice[i.alias]!=="skip").length;return l`<section class="card" aria-labelledby="t-prev">
      <div class="row"><div style="display:flex;align-items:center;gap:12px">${x("file",28)}
        <div><h2 id="t-prev">${s(`format_${e.version}`)}</h2><span class="hint">${s("found",{n:e.items.length})}</span></div></div>
        <button class="btn btn-g" @click=${()=>{this.preview=null}}>${s("otherFile")}</button></div>
      <div class="choices" role="radiogroup">${[[!1,"merge","mergeSub"],[!0,"replaceAll","replaceAllSub"]].map(([i,o,a])=>l`
        <button type="button" class="choice" role="radio" aria-checked=${this.replaceAll===i?"true":"false"} @click=${()=>{this.replaceAll=i}}>
          <b style="font-weight:500">${s(o)}</b><span class="hint">${s(a)}</span></button>`)}</div>
      ${e.notes.length?l`<div class="note warn"><b>${s("fileNotes")}</b>${e.notes.map(i=>l`<div>${C(i)}</div>`)}</div>`:""}
      <div class="scroll"><table style="min-width:680px"><thead><tr><th><span class="sr">${s("take")}</span></th><th>${s("name")}</th><th>${s("port")}</th><th>${s("device")}</th><th>${s("result")}</th></tr></thead>
        <tbody>${e.items.map(i=>{let o=i.connection,a=Object.keys(i.conflicts).length&&!this.replaceAll;return l`<tr>
            <td>${o&&!a?l`<input type="checkbox" style="width:18px;height:18px;accent-color:var(--accent)" aria-label="${i.alias} ${s("take")}"
              .checked=${this.take.has(i.alias)} @change=${c=>{let d=new Set(this.take);c.target.checked?d.add(i.alias):d.delete(i.alias),this.take=d}}>`:""}</td>
            <td><b style="font-weight:500">${i.alias}</b>${o?l`<div class="hint">${P(o)} · ${o.mode} · max. ${o.max_clients}${o.enabled?"":" \xB7 off"}</div>`:""}</td>
            <td class="mono">${o?o.port:""}</td>
            <td class="mono" style="font-size:12px;overflow-wrap:anywhere;max-width:260px">${o?o.device:""}</td>
            <td>${this._result(i)}
              ${i.notes.length?l`<ul class="notes">${i.notes.map(c=>l`<li>${C(c)}</li>`)}</ul>`:""}
              ${a?l`<label class="fld" style="margin-top:8px"><span class="hint">${s("onConflict")}</span>
                <select class="inp" style="min-height:36px" @change=${c=>{this.choice={...this.choice,[i.alias]:c.target.value}}}>
                  ${["skip","replace","new_port"].filter(c=>c!=="new_port"||!i.conflicts.device).map(c=>l`<option value=${c} ?selected=${this.choice[i.alias]===c}>${s(`c_${c}`)}</option>`)}
                </select></label>`:""}
            </td></tr>`})}</tbody></table></div>
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:16px">
        <span class="hint" style="font-size:13px">${s("selected",{n,m:e.items.length})}</span>
        <div style="display:flex;gap:8px"><a class="btn btn-g" href="#/connections">${s("cancel")}</a>
          <button class="btn btn-p" ?disabled=${!n||this.busy} @click=${this._apply}>${s("apply",{n})}</button></div>
      </div></section>`}render(){let e=this.done?2:this.preview?1:0;return l`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${s("importTitle")}</p>
      <h1 style="margin:12px 0 20px">${s("importTitle")}</h1>
      <div class="cols"><div class="main-col">
        ${this._steps(e)}
        ${this.done?l`<section class="card" style="align-items:flex-start"><span class="chip ok">${s("stepDone")}</span>
          <h2>${s("doneTitle",{n:this.done.changes.filter(t=>t.change==="added").length})}</h2><p class="hint" style="font-size:14px">${s("doneText")}</p>
          <div style="display:flex;gap:8px"><a class="btn btn-p" href="#/connections">${s("toConnections")}</a><a class="btn btn-s" href="#/settings">${s("sHistory")}</a></div></section>`:this.preview?this._previewView():this._choose()}
      </div>
      <aside class="side-col">
        <section class="card" aria-labelledby="t-exp"><h2 id="t-exp">${s("exportTitle")}</h2><p class="hint" style="font-size:14px">${s("exportText")}</p>
          <label class="chk"><input type="checkbox" .checked=${this.disabled} @change=${t=>{this.disabled=t.target.checked}}><span>${s("exportDisabled")}</span></label>
          <a class="btn btn-s" style="align-self:flex-start" href=${ee(`api/export?disabled=${this.disabled?1:0}`)} download>${x("download")}${s("download")}</a></section>
        <section class="card" aria-labelledby="t-own"><h2 id="t-own">${s("ownTitle")}</h2><p class="hint" style="font-size:14px">${s("ownText")}</p>
          <a href="#/settings">${s("toSource")}</a></section>
      </aside></div>`}};f(V,"properties",{state:{attribute:!1},text:{state:!0},preview:{state:!0},replaceAll:{state:!0},take:{state:!0},choice:{state:!0},done:{state:!0},error:{state:!0},disabled:{state:!0},busy:{state:!0}}),f(V,"styles",[...m.styles,g`
    .steps { list-style: none; margin: 0 0 20px; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
    .steps li { display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 0 14px 0 6px; border-radius: 18px; font-weight: 500;
      background: var(--surface); border: 1px solid var(--line); color: var(--muted); }
    .steps li.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-hover); }
    .steps li.past { color: var(--accent-hover); }
    .num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; background: var(--line); color: var(--muted); }
    .on .num, .past .num { background: var(--accent); color: var(--on-accent); }
    .drop { border: 2px dashed var(--input-line); border-radius: 16px; padding: 32px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; text-align: center; background: var(--surface-2); }
    .drop.over { border-color: var(--accent); background: var(--accent-soft); }
    td .notes { margin: 6px 0 0; padding-left: 16px; font-size: 12px; color: var(--muted); }
  `]);var ot=["history_days","trace_file_mb","trace_keep","debounce_count","debounce_minutes"],Ft={history_days:"historyDays",trace_file_mb:"traceMb",trace_keep:"traceKeep",debounce_count:"debounceCount",debounce_minutes:"debounceMinutes"};function Bt(r,e){let t=r.split(`
`),n=e.split(`
`),i=new Set(t),o=new Set(n),a=[];for(let c of n)a.push(i.has(c)?`  ${c}`:`+ ${c}`);for(let c of t)o.has(c)||a.push(`- ${c}`);return a.filter(c=>!c.startsWith("  ")).join(`
`)||"  (\u2013)"}var G=class extends m{connectedCallback(){super.connectedCallback(),this.open=-1,this.diffs={},this._loadVersions(),this._loadCustom()}willUpdate(){!this.draft&&this.state&&(this.draft={...this.state.settings})}async _loadVersions(){try{this.versions=await h("api/versions")}catch{this.versions=[]}}async _loadCustom(){try{this.custom=await h("api/custom"),this.customText=this.custom.text,this.customCheck=this.custom.exists?this.custom.check:null}catch{}}async _saveSettings(e){try{await h("api/settings",{method:"PUT",body:{settings:e}}),this.toast(s("saved")),this.refresh(),this._loadVersions()}catch(t){this.toast(t.data.errors?Object.values(t.data.errors).join("; "):`${s("error")}: ${t.message}`)}}async _check(){try{this.customCheck=await h("api/custom/check",{method:"POST",body:{text:this.customText}})}catch(e){this.toast(e.message)}}async _saveCustom(e){try{await h("api/custom",{method:"PUT",body:{text:this.customText,use:e}}),this.toast(s("saved")),this.refresh(),this._loadCustom(),this._loadVersions()}catch(t){t.data.check?this.customCheck=t.data.check:this.toast(`${s("error")}: ${t.message}`)}}async _toggleDiff(e){if(this.open===e){this.open=-1;return}this.open=e;let t=this.versions[e],n=this.versions[e+1];if(this.diffs[t.id]===void 0)try{let i=await h(`api/versions/${t.id}`),o=n?await h(`api/versions/${n.id}`):{connections:[]};this.diffs={...this.diffs,[t.id]:Bt(JSON.stringify(o,null,1),JSON.stringify(i,null,1))}}catch{this.diffs={...this.diffs,[t.id]:"\u2013"}}}async _restore(e){if(await R(this,s("restoreConfirm"),s("restore")))try{await h(`api/versions/${e.id}/restore`,{method:"POST"}),this.toast(s("saved")),this.refresh(),this._loadVersions()}catch(t){this.toast(`${s("error")}: ${t.message}`)}}_changeLine(e){return Oe(e.changes)||e.summary}render(){let e=this.state,t=this.draft;if(!t)return"";let n=e.source==="custom",i=this.customCheck;return l`<div class="layout">
      <nav class="side" aria-label=${s("settingsTitle")}>
        <h1 style="margin:0 0 12px 12px">${s("settingsTitle")}</h1>
        ${[["net","sNet"],["src","sSource"],["hist","sHistory"],["log","sLogging"],["about","sAbout"]].map(([o,a])=>l`<a href="#/settings" @click=${c=>{c.preventDefault(),this.renderRoot.getElementById(o).scrollIntoView({behavior:"smooth"})}}>${s(a)}</a>`)}
      </nav>
      <div class="content">
        <section id="net" class="card" aria-labelledby="t-net">
          <div><h2 id="t-net">${s("sNet")}</h2><p class="hint" style="margin-top:4px">${s("sNetSub")}</p></div>
          <div class="choices" role="radiogroup" aria-labelledby="t-net">${["local","lan","all"].map(o=>l`<button type="button" class="choice" role="radio"
            aria-checked=${e.settings.listen===o?"true":"false"} @click=${()=>this._saveSettings({listen:o})}>
            <b style="font-weight:500">${s(`net_${o}`)}</b><span class="hint">${s(`netsub_${o}`)}</span></button>`)}</div>
          ${e.settings.listen==="all"?l`<div class="note bad" role="alert">${s("netWarn")}</div>`:""}
        </section>

        <section id="src" class="card" aria-labelledby="t-src">
          <div class="row"><div><h2 id="t-src">${s("sSource")}</h2><p class="hint" style="margin-top:4px">${s("sSourceSub")}</p></div>
            <div class="seg" role="group" aria-labelledby="t-src">
              <button aria-pressed=${n?"false":"true"} @click=${()=>this._saveSettings({source:"forms"})}>${s("forms")}</button>
              <button aria-pressed=${n?"true":"false"} ?disabled=${!this.custom?.exists} @click=${()=>this._saveSettings({source:"custom"})}>${s("own")}</button></div></div>
          <div class="note warn" role="note">${s("ownWarn")}</div>
          <textarea class="inp mono editor" aria-label="ser2net.yaml" .value=${this.customText||""} @input=${o=>{this.customText=o.target.value,this.customCheck=null}}></textarea>
          <div class="row">
            ${i?i.errors.length?l`<div class="note bad" style="flex:1">${i.errors.map(o=>l`<div>${C(o)}</div>`)}</div>`:l`<span class="chip ok">${s("checkOk",{n:i.connections.length})}</span>`:l`<span class="hint">${s("notChecked")}</span>`}
            <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn btn-s" @click=${this._check}>${s("check")}</button>
              <button class="btn btn-s" @click=${()=>this._saveCustom(!1)}>${s("saveFile")}</button>
              <button class="btn btn-p" @click=${()=>this._saveCustom(!0)}>${s("saveUse")}</button></div>
          </div>
          ${i&&i.notes.length?l`<div class="hint">${i.notes.map(o=>l`<div>${C(o)}</div>`)}</div>`:""}
        </section>

        <section id="hist" class="card" aria-labelledby="t-hist">
          <div class="row"><h2 id="t-hist">${s("sHistory")}</h2><span class="hint">${s("sHistorySub")}</span></div>
          <ol>${(this.versions||[]).map((o,a)=>l`<li>
            <div class="row"><div style="min-width:0"><div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center"><span style="font-weight:500">${this._changeLine(o)}</span>
              ${a===0?l`<span class="chip info">${s("current")}</span>`:""}</div>
              <div class="hint">${w(o.ts)} · ${s(`src_${o.source}`)}</div></div>
              <div style="display:flex;gap:4px"><button class="btn btn-g" aria-expanded=${this.open===a?"true":"false"} @click=${()=>this._toggleDiff(a)}>${this.open===a?s("hide"):s("diff")}</button>
                ${a?l`<button class="btn btn-s" @click=${()=>this._restore(o)}>${s("restore")}</button>`:""}</div></div>
            ${this.open===a?l`<div class="code" style="background:var(--surface-2);color:var(--text)">${this.diffs[o.id]??s("loading")}</div>`:""}
          </li>`)}</ol>
        </section>

        <section id="log" class="card" aria-labelledby="t-log">
          <h2 id="t-log">${s("sLogging")}</h2>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("logLevel")}</span><select class="inp" @change=${o=>{this.draft={...t,log_level:o.target.value}}}>
              ${["info","debug"].map(o=>l`<option ?selected=${t.log_level===o}>${o}</option>`)}</select></label>
            ${ot.map(o=>l`<label class="fld"><span class="lbl">${s(Ft[o])}</span>
              <input class="inp" inputmode="numeric" .value=${String(t[o])} @input=${a=>{this.draft={...t,[o]:Number(a.target.value||0)}}}></label>`)}
            <label class="fld"><span class="lbl">${s("language")}</span><select class="inp" @change=${o=>this.dispatchEvent(new CustomEvent("s2n-lang",{detail:o.target.value,bubbles:!0,composed:!0}))}>
              <option value="de" ?selected=${v==="de"}>Deutsch</option><option value="en" ?selected=${v==="en"}>English</option></select></label>
          </div>
          <div><button class="btn btn-p" @click=${()=>this._saveSettings(Object.fromEntries(["log_level",...ot].map(o=>[o,t[o]])))}>${s("save")}</button></div>
        </section>

        <section id="about" class="card" aria-labelledby="t-about">
          <h2 id="t-about">${s("sAbout")}</h2>
          <div style="display:grid;grid-template-columns:minmax(120px,180px) minmax(0,1fr);gap:8px 16px">
            <span class="hint" style="font-size:14px">${s("app")}</span><span>${e.version} · ${s("license")}</span>
            <span class="hint" style="font-size:14px">ser2net</span><span>${e.ser2net_version||"?"} (GPL-2.0)</span>
            <span class="hint" style="font-size:14px">${s("source")}</span><a href="https://github.com/bertel2020/HA-Ser2Net" target="_blank" rel="noopener">github.com/bertel2020/HA-Ser2Net</a>
          </div>
        </section>
      </div></div>`}};f(G,"properties",{state:{attribute:!1},draft:{state:!0},custom:{state:!0},customText:{state:!0},customCheck:{state:!0},versions:{state:!0},open:{state:!0},diffs:{state:!0}}),f(G,"styles",[...m.styles,g`
    .layout { display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start; }
    .side { flex: 1 1 200px; display: flex; flex-direction: column; gap: 2px; }
    .side a { display: flex; align-items: center; min-height: 40px; padding: 0 12px; border-radius: 10px; text-decoration: none; color: var(--neutral); }
    .side a:hover { background: var(--line); color: var(--text); }
    .content { flex: 999 1 640px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
    .card { scroll-margin-top: 16px; }
    ol { list-style: none; margin: 0; padding: 0; }
    li { border-top: 1px solid var(--line-2); padding: 12px 0; display: flex; flex-direction: column; gap: 10px; }
    textarea.editor { min-height: 260px; font-size: 12px; line-height: 1.6; background: var(--code-bg); color: var(--code-text); border-color: var(--code-bg); }
  `]);var Ut=["off","rx","tx","both"],W=class extends m{constructor(){super(),this.chunks=[],this.paused=!1,this.ascii=!0,this._after=0}connectedCallback(){super.connectedCallback(),this._timer=setInterval(()=>this._poll(),1e3)}disconnectedCallback(){super.disconnectedCallback(),clearInterval(this._timer)}willUpdate(e){e.has("selected")&&(this.chunks=[],this._after=0),!this.selected&&this.state?.connections.length&&(this.selected=this.state.connections[0].id)}async _poll(){if(!(this.paused||!this.selected))try{let e=await h(`api/live/${this.selected}?after=${this._after}`);e.length&&(this._after=e[e.length-1].seq,this.chunks=[...this.chunks,...e].slice(-400))}catch{}}async _mode(e,t){try{await le({...Qe(e),trace:t}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}}async _delete(e){if(await R(this,s("deleteFile",{n:e}),s("delete")))try{await h(`api/trace/${encodeURIComponent(e)}`,{method:"DELETE"}),this.refresh()}catch(t){this.toast(`${s("error")}: ${t.message}`)}}render(){let e=this.state,t=this.connection(this.selected),n=e.trace_files;return l`
      <div class="head"><div><h1>${s("traceTitle")}</h1><p class="sub">${s("traceSub")}</p></div></div>
      <div class="cols">
        <section class="card side-col" style="gap:4px;padding:12px" aria-labelledby="t-conns">
          <h2 id="t-conns" style="padding:8px 8px 4px">${s("navConnections")}</h2>
          ${e.connections.map(i=>l`<div class="conn ${i.id===this.selected?"on":""}">
            <button class="pick" aria-current=${i.id===this.selected?"true":"false"} @click=${()=>te(`#/trace/${i.id}`)}>
              <b style="font-weight:500">${i.name}</b><span class="hint">${i.trace==="off"?s("notRecording"):s("recording",{m:s(`tr_${i.trace}`)})}</span></button>
            <div class="seg" role="group" aria-label="${s("traceMode")} ${i.name}">${Ut.map(o=>l`<button type="button" aria-pressed=${i.trace===o?"true":"false"}
              ?disabled=${e.source==="custom"} @click=${()=>this._mode(i,o)}>${o==="off"?s("off"):o==="both"?s("both"):o.toUpperCase()}</button>`)}</div>
          </div>`)}
          <p class="hint" style="padding:10px 8px 4px">${s("rotation",{mb:e.settings.trace_file_mb,k:e.settings.trace_keep})} · <a href="#/settings">${s("change")}</a></p>
        </section>
        <div class="main-col">
          <section class="card" style="padding:0;gap:0;overflow:hidden" aria-labelledby="t-view">
            <div class="row" style="padding:14px 16px;border-bottom:1px solid var(--line)">
              <h2 id="t-view">${t?t.name:"\u2013"}</h2>
              <div style="display:flex;gap:4px">
                <button class="btn btn-g" @click=${()=>{this.ascii=!this.ascii}}>${this.ascii?s("hexOnly"):s("hexAscii")}</button>
                <button class="btn btn-g" @click=${()=>{this.paused=!this.paused}}>${this.paused?s("resume"):s("pause")}</button></div></div>
            ${this.chunks.length?l`<div class="code view" style="border-radius:0"><table><tbody>${this.chunks.slice(-200).reverse().map(i=>l`<tr>
              <td style="color:#8f9ba8">${new Date(i.ts*1e3).toLocaleTimeString(void 0,{hour12:!1})}</td>
              <td><span class="dir ${i.direction==="rx"?"rx":i.direction==="tx"?"tx":"mark"}">${i.direction.toUpperCase()}</span></td>
              <td>${i.hex||i.text}</td>${this.ascii&&i.hex?l`<td style="color:#9fb3c8">${i.text.replace(/[^\x20-\x7e]/g,".")}</td>`:""}</tr>`)}</tbody></table></div>`:l`<p class="hint" style="padding:32px 20px;text-align:center;font-size:14px">${s("liveEmpty")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-files">
            <div class="row"><h2 id="t-files">${s("files")}</h2><span class="hint mono">/addon_configs/…_ser2net/trace/</span></div>
            ${n.length?l`<div class="scroll"><table style="min-width:520px"><thead><tr><th>${s("fileTh")}</th><th>${s("changedTh")}</th><th style="text-align:right">${s("sizeTh")}</th><th><span class="sr">${s("delete")}</span></th></tr></thead>
              <tbody>${n.map(i=>l`<tr><td class="mono" style="font-size:13px">${i.name}</td><td>${w(i.modified)}</td><td style="text-align:right">${T(i.size)}</td>
                <td style="text-align:right;white-space:nowrap;padding:4px 0 4px 8px">
                  <a class="btn btn-g" href=${ee(`api/trace/${encodeURIComponent(i.name)}`)} download aria-label="${i.name} ${s("download")}">${x("download",16)}</a>
                  <button class="btn btn-d" @click=${()=>this._delete(i.name)}>${s("delete")}</button></td></tr>`)}</tbody></table></div>`:l`<p class="hint" style="font-size:14px">–</p>`}
          </section>
        </div>
      </div>`}};f(W,"properties",{state:{attribute:!1},selected:{},chunks:{state:!0},paused:{state:!0},ascii:{state:!0}}),f(W,"styles",[...m.styles,g`
    .conn { display: flex; flex-direction: column; gap: 8px; padding: 10px 12px; border-radius: 12px; border: 1px solid transparent; }
    .conn.on { background: var(--accent-soft); border-color: var(--accent); }
    .pick { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; background: none; border: none; padding: 0; cursor: pointer; font: inherit; color: inherit; text-align: left; min-height: 40px; justify-content: center; width: 100%; }
    .view { max-height: 460px; overflow: auto; padding: 8px 4px; }
    .view table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .view td { border: none; padding: 2px 8px; white-space: pre; }
    .dir { display: inline-block; min-width: 30px; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
  `]);var jt={"ser2net-app":H,"s2n-confirm":F,"s2n-connections":B,"s2n-detail":U,"s2n-edit":j,"s2n-events":I,"s2n-import":V,"s2n-settings":G,"s2n-trace":W};for(let[r,e]of Object.entries(jt))customElements.get(r)||customElements.define(r,e);
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/

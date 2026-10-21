// GENERATED FILE - do not edit. Edit panel-src/src/ and run: node panel-src/build.mjs
var ht=Object.defineProperty;var ut=(o,e,t)=>e in o?ht(o,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):o[e]=t;var m=(o,e,t)=>ut(o,typeof e!="symbol"?e+"":e,t);var ce=globalThis,de=ce.ShadowRoot&&(ce.ShadyCSS===void 0||ce.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,xe=Symbol(),Oe=new WeakMap,ee=class{constructor(e,t,n){if(this._$cssResult$=!0,n!==xe)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(de&&e===void 0){let n=t!==void 0&&t.length===1;n&&(e=Oe.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),n&&Oe.set(t,e))}return e}toString(){return this.cssText}},Ue=o=>new ee(typeof o=="string"?o:o+"",void 0,xe),v=(o,...e)=>{let t=o.length===1?o[0]:e.reduce((n,i,a)=>n+(l=>{if(l._$cssResult$===!0)return l.cssText;if(typeof l=="number")return l;throw Error("Value passed to 'css' function must be a 'css' function result: "+l+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+o[a+1],o[0]);return new ee(t,o,xe)},Be=(o,e)=>{if(de)o.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let n=document.createElement("style"),i=ce.litNonce;i!==void 0&&n.setAttribute("nonce",i),n.textContent=t.cssText,o.appendChild(n)}},we=de?o=>o:o=>o instanceof CSSStyleSheet?(e=>{let t="";for(let n of e.cssRules)t+=n.cssText;return Ue(t)})(o):o;var{is:bt,defineProperty:mt,getOwnPropertyDescriptor:ft,getOwnPropertyNames:gt,getOwnPropertySymbols:vt,getPrototypeOf:$t}=Object,pe=globalThis,qe=pe.trustedTypes,yt=qe?qe.emptyScript:"",_t=pe.reactiveElementPolyfillSupport,te=(o,e)=>o,ke={toAttribute(o,e){switch(e){case Boolean:o=o?yt:null;break;case Object:case Array:o=o==null?o:JSON.stringify(o)}return o},fromAttribute(o,e){let t=o;switch(e){case Boolean:t=o!==null;break;case Number:t=o===null?null:Number(o);break;case Object:case Array:try{t=JSON.parse(o)}catch{t=null}}return t}},Ve=(o,e)=>!bt(o,e),Ie={attribute:!0,type:String,converter:ke,reflect:!1,useDefault:!1,hasChanged:Ve};Symbol.metadata??=Symbol("metadata"),pe.litPropertyMetadata??=new WeakMap;var A=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=Ie){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),i=this.getPropertyDescriptor(e,n,t);i!==void 0&&mt(this.prototype,e,i)}}static getPropertyDescriptor(e,t,n){let{get:i,set:a}=ft(this.prototype,e)??{get(){return this[t]},set(l){this[t]=l}};return{get:i,set(l){let c=i?.call(this);a?.call(this,l),this.requestUpdate(e,c,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??Ie}static _$Ei(){if(this.hasOwnProperty(te("elementProperties")))return;let e=$t(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(te("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(te("properties"))){let t=this.properties,n=[...gt(t),...vt(t)];for(let i of n)this.createProperty(i,t[i])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[n,i]of t)this.elementProperties.set(n,i)}this._$Eh=new Map;for(let[t,n]of this.elementProperties){let i=this._$Eu(t,n);i!==void 0&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let i of n)t.unshift(we(i))}else e!==void 0&&t.push(we(e));return t}static _$Eu(e,t){let n=t.attribute;return n===!1?void 0:typeof n=="string"?n:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Be(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,n);if(i!==void 0&&n.reflect===!0){let a=(n.converter?.toAttribute!==void 0?n.converter:ke).toAttribute(t,n.type);this._$Em=e,a==null?this.removeAttribute(i):this.setAttribute(i,a),this._$Em=null}}_$AK(e,t){let n=this.constructor,i=n._$Eh.get(e);if(i!==void 0&&this._$Em!==i){let a=n.getPropertyOptions(i),l=typeof a.converter=="function"?{fromAttribute:a.converter}:a.converter?.fromAttribute!==void 0?a.converter:ke;this._$Em=i;let c=l.fromAttribute(t,a.type);this[i]=c??this._$Ej?.get(i)??c,this._$Em=null}}requestUpdate(e,t,n,i=!1,a){if(e!==void 0){let l=this.constructor;if(i===!1&&(a=this[e]),n??=l.getPropertyOptions(e),!((n.hasChanged??Ve)(a,t)||n.useDefault&&n.reflect&&a===this._$Ej?.get(e)&&!this.hasAttribute(l._$Eu(e,n))))return;this.C(e,t,n)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:i,wrapped:a},l){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,l??t??this[e]),a!==!0||l!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),i===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,a]of this._$Ep)this[i]=a;this._$Ep=void 0}let n=this.constructor.elementProperties;if(n.size>0)for(let[i,a]of n){let{wrapped:l}=a,c=this[i];l!==!0||this._$AL.has(i)||c===void 0||this.C(i,void 0,a,c)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(n=>n.hostUpdate?.()),this.update(t)):this._$EM()}catch(n){throw e=!1,this._$EM(),n}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};A.elementStyles=[],A.shadowRootOptions={mode:"open"},A[te("elementProperties")]=new Map,A[te("finalized")]=new Map,_t?.({ReactiveElement:A}),(pe.reactiveElementVersions??=[]).push("2.1.2");var Me=globalThis,je=o=>o,he=Me.trustedTypes,Ge=he?he.createPolicy("lit-html",{createHTML:o=>o}):void 0,Je="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,Xe="?"+C,xt=`<${Xe}>`,L=document,ne=()=>L.createComment(""),ie=o=>o===null||typeof o!="object"&&typeof o!="function",Pe=Array.isArray,wt=o=>Pe(o)||typeof o?.[Symbol.iterator]=="function",Se=`[ 	
\f\r]`,se=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,We=/-->/g,Ke=/>/g,M=RegExp(`>|${Se}(?:([^\\s"'>=/]+)(${Se}*=${Se}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ze=/'/g,Qe=/"/g,et=/^(?:script|style|textarea|title)$/i,Le=o=>(e,...t)=>({_$litType$:o,strings:e,values:t}),r=Le(1),ue=Le(2),ss=Le(3),z=Symbol.for("lit-noChange"),y=Symbol.for("lit-nothing"),Ye=new WeakMap,P=L.createTreeWalker(L,129);function tt(o,e){if(!Pe(o)||!o.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ge!==void 0?Ge.createHTML(e):e}var kt=(o,e)=>{let t=o.length-1,n=[],i,a=e===2?"<svg>":e===3?"<math>":"",l=se;for(let c=0;c<t;c++){let d=o[c],u,p,b=-1,x=0;for(;x<d.length&&(l.lastIndex=x,p=l.exec(d),p!==null);)x=l.lastIndex,l===se?p[1]==="!--"?l=We:p[1]!==void 0?l=Ke:p[2]!==void 0?(et.test(p[2])&&(i=RegExp("</"+p[2],"g")),l=M):p[3]!==void 0&&(l=M):l===M?p[0]===">"?(l=i??se,b=-1):p[1]===void 0?b=-2:(b=l.lastIndex-p[2].length,u=p[1],l=p[3]===void 0?M:p[3]==='"'?Qe:Ze):l===Qe||l===Ze?l=M:l===We||l===Ke?l=se:(l=M,i=void 0);let g=l===M&&o[c+1].startsWith("/>")?" ":"";a+=l===se?d+xt:b>=0?(n.push(u),d.slice(0,b)+Je+d.slice(b)+C+g):d+C+(b===-2?c:g)}return[tt(o,a+(o[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),n]},ae=class o{constructor({strings:e,_$litType$:t},n){let i;this.parts=[];let a=0,l=0,c=e.length-1,d=this.parts,[u,p]=kt(e,t);if(this.el=o.createElement(u,n),P.currentNode=this.el.content,t===2||t===3){let b=this.el.content.firstChild;b.replaceWith(...b.childNodes)}for(;(i=P.nextNode())!==null&&d.length<c;){if(i.nodeType===1){if(i.hasAttributes())for(let b of i.getAttributeNames())if(b.endsWith(Je)){let x=p[l++],g=i.getAttribute(b).split(C),H=/([.?@])?(.*)/.exec(x);d.push({type:1,index:a,name:H[2],strings:g,ctor:H[1]==="."?Ce:H[1]==="?"?Te:H[1]==="@"?Ee:O}),i.removeAttribute(b)}else b.startsWith(C)&&(d.push({type:6,index:a}),i.removeAttribute(b));if(et.test(i.tagName)){let b=i.textContent.split(C),x=b.length-1;if(x>0){i.textContent=he?he.emptyScript:"";for(let g=0;g<x;g++)i.append(b[g],ne()),P.nextNode(),d.push({type:2,index:++a});i.append(b[x],ne())}}}else if(i.nodeType===8)if(i.data===Xe)d.push({type:2,index:a});else{let b=-1;for(;(b=i.data.indexOf(C,b+1))!==-1;)d.push({type:7,index:a}),b+=C.length-1}a++}}static createElement(e,t){let n=L.createElement("template");return n.innerHTML=e,n}};function F(o,e,t=o,n){if(e===z)return e;let i=n!==void 0?t._$Co?.[n]:t._$Cl,a=ie(e)?void 0:e._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(o),i._$AT(o,t,n)),n!==void 0?(t._$Co??=[])[n]=i:t._$Cl=i),i!==void 0&&(e=F(o,i._$AS(o,e.values),i,n)),e}var Ae=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,i=(e?.creationScope??L).importNode(t,!0);P.currentNode=i;let a=P.nextNode(),l=0,c=0,d=n[0];for(;d!==void 0;){if(l===d.index){let u;d.type===2?u=new re(a,a.nextSibling,this,e):d.type===1?u=new d.ctor(a,d.name,d.strings,this,e):d.type===6&&(u=new De(a,this,e)),this._$AV.push(u),d=n[++c]}l!==d?.index&&(a=P.nextNode(),l++)}return P.currentNode=L,i}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings!==void 0?(n._$AI(e,n,t),t+=n.strings.length-2):n._$AI(e[t])),t++}},re=class o{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,i){this.type=2,this._$AH=y,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=F(this,e,t),ie(e)?e===y||e==null||e===""?(this._$AH!==y&&this._$AR(),this._$AH=y):e!==this._$AH&&e!==z&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):wt(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==y&&ie(this._$AH)?this._$AA.nextSibling.data=e:this.T(L.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,i=typeof n=="number"?this._$AC(e):(n.el===void 0&&(n.el=ae.createElement(tt(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===i)this._$AH.p(t);else{let a=new Ae(i,this),l=a.u(this.options);a.p(t),this.T(l),this._$AH=a}}_$AC(e){let t=Ye.get(e.strings);return t===void 0&&Ye.set(e.strings,t=new ae(e)),t}k(e){Pe(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,n,i=0;for(let a of e)i===t.length?t.push(n=new o(this.O(ne()),this.O(ne()),this,this.options)):n=t[i],n._$AI(a),i++;i<t.length&&(this._$AR(n&&n._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let n=je(e).nextSibling;je(e).remove(),e=n}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},O=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,i,a){this.type=1,this._$AH=y,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=a,n.length>2||n[0]!==""||n[1]!==""?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=y}_$AI(e,t=this,n,i){let a=this.strings,l=!1;if(a===void 0)e=F(this,e,t,0),l=!ie(e)||e!==this._$AH&&e!==z,l&&(this._$AH=e);else{let c=e,d,u;for(e=a[0],d=0;d<a.length-1;d++)u=F(this,c[n+d],t,d),u===z&&(u=this._$AH[d]),l||=!ie(u)||u!==this._$AH[d],u===y?e=y:e!==y&&(e+=(u??"")+a[d+1]),this._$AH[d]=u}l&&!i&&this.j(e)}j(e){e===y?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},Ce=class extends O{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===y?void 0:e}},Te=class extends O{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==y)}},Ee=class extends O{constructor(e,t,n,i,a){super(e,t,n,i,a),this.type=5}_$AI(e,t=this){if((e=F(this,e,t,0)??y)===z)return;let n=this._$AH,i=e===y&&n!==y||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,a=e!==y&&(n===y||i);i&&this.element.removeEventListener(this.name,this,n),a&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},De=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){F(this,e)}};var St=Me.litHtmlPolyfillSupport;St?.(ae,re),(Me.litHtmlVersions??=[]).push("3.3.3");var st=(o,e,t)=>{let n=t?.renderBefore??e,i=n._$litPart$;if(i===void 0){let a=t?.renderBefore??null;n._$litPart$=i=new re(e.insertBefore(ne(),a),a,void 0,t??{})}return i._$AI(o),i};var ze=globalThis,k=class extends A{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=st(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}};k._$litElement$=!0,k.finalized=!0,ze.litElementHydrateSupport?.({LitElement:k});var At=ze.litElementPolyfillSupport;At?.({LitElement:k});(ze.litElementVersions??=[]).push("4.2.2");var Ct=new URL(".",location.href.split("#")[0]),R=o=>new URL(o,Ct).href,Re=class extends Error{constructor(e,t){super(t&&t.error||`HTTP ${e}`),this.status=e,this.data=t||{}}};async function h(o,{method:e="GET",body:t}={}){let n=await fetch(R(o),{method:e,credentials:"same-origin",headers:t===void 0?{}:{"Content-Type":"application/json"},body:t===void 0?void 0:JSON.stringify(t)}),a=(n.headers.get("content-type")||"").includes("json")?await n.json():await n.text();if(!n.ok)throw new Re(n.status,typeof a=="object"?a:{error:a});return a}var Tt=["alias","present","tty","usb","running","pending","clients","kept_open","bytes_from_device","bytes_to_device","rate_from_device","rate_to_device","last_data","line_errors","latency","addresses","modbus"],be=o=>Object.fromEntries(Object.entries(o).filter(([e])=>!Tt.includes(e))),U=o=>o.id?h(`api/connections/${o.id}`,{method:"PUT",body:{connection:o}}):h("api/connections",{method:"POST",body:{connection:o}});var nt={de:{portWarn:"Achtung: {w}. Speichern geht trotzdem; die Verbindung startet, sobald der Port frei ist.",appTitle:"Device Proxy",running:"ser2net l\xE4uft",notRunning:"ser2net l\xE4uft nicht",appRunning:"L\xE4uft",problems:"{n} mit Problem",navConnections:"Verbindungen",navEvents:"Ereignisse",navTrace:"Mitschnitt",navSettings:"Einstellungen",navMain:"Bereiche",breadcrumb:"Pfad",connectionsTitle:"Verbindungen",connectionsSub:"Serielle Ger\xE4te und Modbus-Ger\xE4te, geteilt \xFCber das Netzwerk.",importExport:"Import / Export",addConnection:"Verbindung hinzuf\xFCgen",tileActive:"Aktiv",tileOf:"von {n}",tileClients:"Clients verbunden",tileErrors:"Leitungsfehler",tileReach:"Erreichbar aus",listen_local:"nur dieser Rechner",listen_lan:"LAN \xB7 nur private Netze",listen_all:"alle Netze",stRunning:"L\xE4uft",stDisabled:"Deaktiviert",stMissing:"Ger\xE4t fehlt",stWaiting:"Wartet auf ser2net",stPending:"\xC4nderung wartet",clients:"Clients",clientsOf:"{n} von {m}",noClients:"Keine Clients verbunden.",disabledText:"Verbindung ist deaktiviert \u2013 Port geschlossen.",missingText:"Ger\xE4t nicht angeschlossen.",since:"seit {t}",copy:"Kopieren",copied:"Kopiert",edit:"Bearbeiten",details:"Details",switchLabel:"{name} aktiv",emptyTitle:"Noch keine Verbindungen",emptyText:"Lege eine Verbindung an oder \xFCbernimm deine bestehende ser2net- oder modbus-proxy-Konfiguration.",emptyImport:"ser2net.yaml / ser2net.conf importieren",customActive:"Eigene ser2net.yaml ist aktiv",customActiveText:"Die Formulare sind gespeichert, werden aber nicht verwendet. Ports von ser2net:",toSettings:"Zu den Einstellungen",stuck:"Client {a} liest nicht",lineErrors:"{n} Leitungsfehler",latencyRO:"FTDI-Latenz nicht \xE4nderbar",keptOpen:"Ger\xE4t offen gehalten",live:"Live-Daten",liveSub:"Gelesen aus dem Mitschnitt von ser2net \u2013 belegt keinen Client-Platz.",pause:"Pausieren",resume:"Fortsetzen",hexOnly:"Nur Hex",hexAscii:"Hex + ASCII",liveEmpty:"Noch keine Daten. ser2net \xF6ffnet das Ger\xE4t erst, wenn ein Client verbunden ist \u2013 oder mit \u201EGer\xE4t offen halten\u201C.",clientTh:"Client",sinceTh:"Verbunden seit",toClient:"an Client",fromClient:"vom Client",queued:"Warteschlange",addresses:"Adressen zum Kopieren",target_ha:"Home Assistant (Integrationen)",target_apps:"Andere Apps (z. B. Z-Wave JS UI)",target_lan:"Andere Rechner im LAN",notReachable:"nicht erreichbar mit dieser Einstellung",lanUnknown:"LAN-Adresse unbekannt",configuration:"Konfiguration",line:"Leitung",noLineErrors:"keine Fehler",lineUnsupported:"Der Treiber z\xE4hlt keine Fehler.",lineClosed:"Z\xE4hlt nur, solange das Ger\xE4t offen ist.",frame:"Frame",parity:"Parit\xE4t",overrun:"Overrun",brk:"Break",bufOverrun:"Puffer",dataFromDevice:"Daten vom Ger\xE4t",lastData:"Letzte Daten",never:"noch nie",recent:"Verlauf",allEvents:"Alle Ereignisse",device:"Ger\xE4t",resolved:"Aufgel\xF6st",usb:"USB",serialNo:"Seriennr.",interface:"Schnittstelle",network:"Netzwerk",newConnection:"Neue Verbindung",editConnection:"Verbindung bearbeiten",template:"Vorlage",templateSub:"F\xFCllt die Felder passend vor. Alles bleibt \xE4nderbar.",tpl_ehz_sml:"eHZ SML",tpl_ehz_d0:"eHZ D0",tpl_zwave:"Z-Wave-Stick",tpl_generic:"Allgemein",tplsub_ehz_sml:"9600 8N1 \xB7 bis 5 Clients",tplsub_ehz_d0:"9600 7E1 \xB7 bis 5 Clients",tplsub_zwave:"115200 8N1 \xB7 nodelay",tplsub_generic:"9600 8N1 \xB7 1 Client",basics:"Grunddaten",name:"Name",enabled:"Aktiv",enabledText:"Nach dem Speichern bereitstellen",devicePick:"Ger\xE4t",deviceOther:"Anderer Pfad \u2026",devicePath:"Pfad",usedBy:"belegt: {n}",noSerial:"ohne Seriennr.",ambiguous:"Mehrere gleiche Adapter ohne Seriennummer: Auswahl \xFCber den USB-Port (by-path). In Proxmox diese Ger\xE4te nach Port durchreichen.",ifNet:"Schnittstelle und Netzwerk",baud:"Baudrate",format:"Format",dataBits:"Datenbits",parityF:"Parit\xE4t",stopBits:"Stoppbits",port:"TCP-Port",maxClients:"Max. Clients",maxClientsHint:"Mehr als 1 nur, wenn das Ger\xE4t das vertr\xE4gt.",mode:"Modus",mode_raw:"Bytes unver\xE4ndert durchreichen \u2013 passt f\xFCr die meisten Integrationen.",mode_rfc2217:"Clients stellen Baudrate und Leitungen selbst ein (rfc2217://\u2026).",mode_telnet:"F\xFCr Terminal-Zugriff per telnet.",advanced:"Erweitert",advancedSub:"ser2net-Optionen \xB7 alles optional",open:"aufklappen",closeA:"zuklappen",set:"{n} gesetzt",serialSide:"Serielle Seite",connectionSide:"Verbindung",tcpSide:"TCP",appSide:"App",o_local:"Modem-Steuerleitungen (CD) ignorieren",o_rtscts:"Hardware-Flusskontrolle",o_xonxoff:"Software-Flusskontrolle",o_hangup_when_done:"DTR fallen lassen, wenn der letzte Client geht",o_nobreak:"Break-Signal unterdr\xFCcken",o_low_latency:"FTDI-Latenz 1 ms statt 16 ms",o_kickolduser:"Bei vollem Limit einen alten Client trennen",o_chardelay:"Bytes sammeln und geb\xFCndelt senden",o_nodelay:"Nagle aus \u2013 weniger Latenz",o_keep_open:"Ger\xE4t offen halten (die App verbindet sich selbst, belegt einen Platz)",o_stuck_disconnect:"Clients trennen, wenn einer nicht mehr liest",o_notify_missing:"Benachrichtigen, wenn das Ger\xE4t fehlt oder nicht antwortet",o_notify_no_client:"Benachrichtigen, wenn kein Client verbunden ist",dtr:"DTR beim \xD6ffnen",rts:"RTS beim \xD6ffnen",lineDefault:"unver\xE4ndert",on:"an",off:"aus",rs485:"RS485",rs485Hint:"z. B. 0:0:rts_on_send \u2013 leer = aus",timeout:"Timeout (s, 0 = nie)",retry:"Neuer Versuch nach (s, 0 = Standard)",remaddr:"Erlaubte Clients (remaddr)",remaddrHint:"Leer: nach der globalen Einstellung. Adressen oder Netze, mit Leerzeichen getrennt.",banner:"Banner",openstr:"openstr",closestr:"closestr",bind:"Bind-Adresse",bindHint:"Leer: nach der globalen Einstellung.",extra:"Weitere Optionen",extraHint:"Eine pro Zeile: name: wert",traceMode:"Mitschnitt aufzeichnen",silence:"Warnen, wenn keine Daten seit (min, 0 = nie)",tr_off:"aus",tr_rx:"vom Ger\xE4t",tr_tx:"zum Ger\xE4t",tr_both:"beide Richtungen",preview:"Vorschau ser2net.yaml",previewSub:"So wird die Verbindung an ser2net \xFCbergeben.",save:"Speichern",cancel:"Abbrechen",delete:"L\xF6schen",saveHint:"Nur diese Verbindung wird neu aufgebaut. Andere bleiben verbunden.",saved:"Gespeichert.",savedRebuilt:"Gespeichert. Neu aufgebaut: {n}.",savedReconnect:" Clients neu verbunden: {n}.",deleteConfirm:"Verbindung \u201E{n}\u201C l\xF6schen? Ihre Clients werden getrennt.",errorsBelow:"Bitte die markierten Felder pr\xFCfen.",importTitle:"Import / Export",stepChoose:"Datei w\xE4hlen",stepPreview:"Vorschau pr\xFCfen",stepDone:"\xDCbernommen",importChoose:"ser2net.yaml, ser2net.conf oder Modbus-Proxy-Konfiguration ausw\xE4hlen",importDrop:"Datei ausw\xE4hlen oder Inhalt einf\xFCgen",importFormats:"ser2net 4 (YAML, Version 1 und 2), ser2net 3 (ser2net.conf) oder die Optionen von ha-modbusproxy (YAML aus dessen Konfigurations-Tab) bzw. modbus-proxy",chooseFile:"Datei ausw\xE4hlen",pasteHere:"\u2026 oder den Inhalt hier einf\xFCgen",readPreview:"Vorschau",otherFile:"Andere Datei",format_0:"ser2net 3 (ser2net.conf)",format_1:"ser2net 4 \xB7 YAML Version 1",format_2:"ser2net 4 \xB7 YAML Version 2",format_10:"ha-modbusproxy (Optionen)",format_11:"modbus-proxy",found:"{n} Verbindungen gefunden",merge:"Erg\xE4nzen",mergeSub:"Vorhandene bleiben; bei Kollisionen w\xE4hlst du pro Verbindung",replaceAll:"Alles ersetzen",replaceAllSub:"Vorhandene Verbindungen werden entfernt",result:"Ergebnis",resOk:"wird \xFCbernommen",resNotes:"mit Hinweisen",resNo:"nicht \xFCbertragbar",resConflict:"Kollision",onConflict:"Bei Kollision",c_replace:"vorhandene ersetzen",c_new_port:"neuer Port",c_skip:"\xFCberspringen",take:"\xDCbernehmen",selected:"{n} von {m} ausgew\xE4hlt",apply:"{n} \xFCbernehmen",doneTitle:"{n} Verbindungen \xFCbernommen",doneText:"Der vorherige Stand liegt in der Konfig-Historie.",toConnections:"Zu den Verbindungen",exportTitle:"Export",exportText:"Die Verbindungen als ser2net-4-ser2net.yaml \u2013 zum Sichern oder f\xFCr einen anderen Rechner.",exportDisabled:"Deaktivierte Verbindungen mitnehmen",download:"ser2net.yaml herunterladen",ownTitle:"Datei lieber direkt verwenden?",ownText:"F\xFCr Sonderf\xE4lle, die die Formulare nicht abbilden.",toSource:"Konfigurationsquelle umstellen",fileNotes:"Hinweise zur Datei",eventsTitle:"Ereignisse",eventsSub:"Live-Log der App und Historie.",tabLive:"Live-Log",tabHistory:"Historie",allConnections:"Alle Verbindungen",search:"Suche",searchPh:"z. B. getrennt, 192.168.1.20",lv_info:"Info",lv_warning:"Warnung",lv_error:"Fehler",lv_debug:"Debug",entries:"{n} Eintr\xE4ge",both:"Beide",paused:"Pausiert",liveState:"Live",noEntries:"Keine Eintr\xE4ge f\xFCr diesen Filter.",drops:"Abbr\xFCche ({d} T.)",availability:"Verf\xFCgbar",stable:"stabil",unstable:"{n}\xD7 getrennt",timeline:"Zeitleiste",retention:"Aufbewahrung {d} Tage",today:"Heute",yesterday:"Gestern",summed:"{n}\xD7 zusammengefasst",traceTitle:"Mitschnitt",traceSub:"Bytes zwischen Ger\xE4t und Clients. Aufzeichnen trennt keine Clients; Dateien rotieren automatisch.",recording:"zeichnet auf \xB7 {m}",notRecording:"keine Aufzeichnung",files:"Dateien",fileTh:"Datei",sizeTh:"Gr\xF6\xDFe",changedTh:"Ge\xE4ndert",rotation:"Rotation: {mb} MB je Datei \xB7 {k} \xE4ltere behalten",change:"\xE4ndern",deleteFile:"\u201E{n}\u201C l\xF6schen?",settingsTitle:"Einstellungen",sNet:"Netzwerk",sNetSub:"Gilt f\xFCr alle Verbindungen ohne eigene Bind-Adresse oder remaddr.",net_local:"Nur dieser Rechner",netsub_local:"127.0.0.1 \xB7 nur Home Assistant",net_apps:"Home Assistant + Apps",netsub_apps:"127.0.0.0/8 und 172.30.32.0/23 \xB7 nicht aus dem LAN",net_lan:"LAN",netsub_lan:"nur aus privaten Netzen",net_all:"Alle Netze",netsub_all:"ohne Einschr\xE4nkung",netWarn:"ser2net hat keine Anmeldung. Wer den Port erreicht, kann das Ger\xE4t lesen und steuern.",sSource:"Konfigurationsquelle",sSourceSub:"Formulare oder eine eigene ser2net.yaml f\xFCr Sonderf\xE4lle.",forms:"Formulare",own:"Eigene ser2net.yaml",ownWarn:"Solange die eigene Datei aktiv ist, werden die Formulare nicht verwendet. Ohne admin-Abschnitt: die App f\xFCgt ihren eigenen an.",check:"Pr\xFCfen",saveFile:"Speichern",saveUse:"Speichern und verwenden",checkOk:"G\xFCltig \xB7 {n} Verbindungen",notChecked:"Noch nicht gepr\xFCft",sHistory:"Konfig-Historie",sHistorySub:"die letzten 20 St\xE4nde",current:"aktuell",diff:"Unterschiede",hide:"Ausblenden",restore:"Wiederherstellen",listenConfirm:"Erreichbarkeit \xE4ndern? Die Clients aller Verbindungen werden dabei getrennt.",ownConfirm:"Eigene ser2net.yaml verwenden? Alle Verbindungen aus den Formularen werden abgeschaltet.",restoreConfirm:"Diesen Stand wiederherstellen? Ge\xE4nderte Verbindungen werden neu aufgebaut.",src_ui:"Oberfl\xE4che",src_import:"Import",src_custom:"eigene Datei",src_restore:"Wiederherstellung",src_test:"Test",sLogging:"Logging und Speicher",logLevel:"Log-Level",historyDays:"Historie aufbewahren (Tage)",traceMb:"Mitschnitt: Gr\xF6\xDFe je Datei (MB)",traceKeep:"Mitschnitt: \xE4ltere Dateien",debounceCount:"Wiederholungen zusammenfassen ab",debounceMinutes:"innerhalb von (min)",sAbout:"\xDCber",app:"App",license:"Lizenz MIT",source:"Quelle",tools:"Werkzeuge",meterCheck:"Z\xE4hlerdaten pr\xFCfen",meterCheckSub:"Wertet die Daten der letzten 30 s als SML oder D0 aus.",proto_sml:"SML",proto_d0:"D0 (Text)",proto_unknown:"kein Z\xE4hlerprotokoll erkannt",telegrams:"{n} Telegramme",validCrc:"{n} g\xFCltig (CRC)",validD0:"{n} vollst\xE4ndig",noData30:"In den letzten 30 s kamen keine Daten.",baudDetect:"Baudrate erkennen",baudDetectSub:"H\xF6rt jede Baudrate und jedes Format kurz ab; sendet nichts.",baudConfirm:"F\xFCr die Erkennung gibt ser2net das Ger\xE4t bis zu etwa einer Minute frei \u2013 die Clients dieser Verbindung werden getrennt und verbinden sich danach neu. Starten?",start:"Starten",detecting:"Pr\xFCfe {d} von {t} \u2026",detected:"Erkannt: {b} {f}",noDetect:"Nichts Eindeutiges erkannt.",applyThis:"\xDCbernehmen",candidates:"Beste Treffer",score:"Treffer","obis_1-0:1.8.0":"Bezug gesamt","obis_1-0:2.8.0":"Einspeisung gesamt","obis_1-0:16.7.0":"Leistung","obis_1-0:1.8.1":"Bezug Tarif 1","obis_1-0:1.8.2":"Bezug Tarif 2",sNotify:"Benachrichtigungen",sNotifySub:"Als Meldung im Glocken-Symbol von Home Assistant; optional zus\xE4tzlich aufs Handy.",notifyGrace:"Melden, wenn ein Problem l\xE4nger dauert als (s)",notifyDismiss:"Meldung entfernen, wenn das Problem behoben ist",notifyService:"Zus\xE4tzlich senden an (notify-Dienst)",notifyNone:"nicht senden",notifyResolved:"Auch melden, wenn es wieder in Ordnung ist",notifyStuck:"Ein Client liest nicht mehr",notifyLine:"Leitungsfehler steigen",notifySer2net:"ser2net startet immer wieder neu",notifyLanguage:"Sprache der Meldungen",noClientMinutes:"\u201EKein Client\u201C melden nach (min)",notifyPerConnection:"Ger\xE4t fehlt, kein Client und keine Daten stellst du pro Verbindung ein.",sMqtt:"MQTT-Entit\xE4ten",sMqttSub:"Pro Verbindung ein Ger\xE4t in Home Assistant: angeschlossen, Clients, Datenrate, letzte Daten, Leitungsfehler und ein Schalter; bei Modbus erreichbar, Anfragen, ohne Antwort und Antwortzeit.",mqttOn:"Entit\xE4ten \xFCber MQTT anlegen",mqttBroker:"Broker: {b}",mqttNoBroker:"Kein MQTT-Broker in Home Assistant gefunden (z. B. das Mosquitto-Add-on) \u2013 Entit\xE4ten sind aus.",mqttConnected:"verbunden",mqttDisconnected:"nicht verbunden",mqttPrefix:"Discovery-Pr\xE4fix",mqttBase:"Basis-Topic",mqttInterval:"Zust\xE4nde senden alle (s)",mqttNames:"Namen der Entit\xE4ten folgen der Sprache der Meldungen.",src_mqtt:"MQTT-Schalter",sDiag:"Diagnose",sDiagSub:"ZIP mit Versionen, Konfiguration, Status, Ger\xE4ten und Ereignissen \u2013 ohne IP-Adressen, Clients nur gez\xE4hlt.",diagDownload:"Diagnose-Paket herunterladen",kind:"Art",kindSub:"Was soll geteilt werden?",kind_serial:"Serielles Ger\xE4t",kind_modbus:"Modbus-Ger\xE4t",kindsub_serial:"USB oder seriell \xFCber ser2net, z. B. Z\xE4hler, Z-Wave-Stick",kindsub_modbus:"Modbus TCP oder RTU f\xFCr mehrere Modbus-TCP-Clients, z. B. Wechselrichter",mbDevice:"Modbus-Ger\xE4t",mbLink:"Verbindung zum Ger\xE4t",link_tcp:"Modbus TCP",link_rtu:"Modbus RTU (seriell)",link_rtu_tcp:"RTU \xFCber TCP",linksub_tcp:"Ger\xE4t im Netzwerk, z. B. Wechselrichter, W\xE4rmepumpe, Batterie.",linksub_rtu:"RS485-Adapter an diesem Rechner \u2013 die App \xF6ffnet ihn selbst.",linksub_rtu_tcp:"RS485-Ethernet-Wandler im transparenten Modus.",mbHost:"Adresse des Ger\xE4ts",mbHostHint:"IP-Adresse oder Hostname",mbHostPort:"Port des Ger\xE4ts",mbProxy:"Proxy",mbPort:"TCP-Port f\xFCr die Clients",mbPortHint:"Hier verbinden sich die Integrationen (Standard 502).",mbClientsHint:"Modbus-TCP-Clients gleichzeitig.",mbTimeout:"Antwort-Timeout (ms)",mbTimeoutHint:"So lange wartet der Proxy auf das Ger\xE4t.",mbRetries:"Weitere Versuche",mbConnectDelay:"Pause nach dem Verbinden (ms)",mbConnectDelayHint:"F\xFCr Ger\xE4te, die nach dem Verbindungsaufbau kurz brauchen (connection_time).",mbGap:"Pause zwischen Anfragen (ms)",mbGapHint:"F\xFCr langsame Ger\xE4te; 0 = sofort.",advancedSubMb:"Clients und Netzwerk \xB7 alles optional",mbIdle:"Unt\xE4tige Clients trennen nach (s, 0 = nie)",allowed:"Erlaubte Clients",trmb_off:"aus",trmb_rx:"Antworten",trmb_tx:"Anfragen",trmb_both:"Anfragen und Antworten",mbPreview:"So arbeitet der Proxy",mbPreviewSub:"Alle Anfragen gehen nacheinander \xFCber eine Verbindung zum Ger\xE4t.",mbFlowClients:"Bis zu {n} Clients",mbFlowQueue:"Warteschlange",mbFlowQueueSub:"eine Anfrage nach der anderen \xB7 Timeout {ms} ms \xB7 {n} weitere Versuche",stPortBusy:"Port belegt",stStarting:"Startet",stUnreachable:"Nicht erreichbar",mbAvg:"\xD8 {ms} ms",mbFailedN:"{n} ohne Antwort",mbDownText:"Ger\xE4t nicht erreichbar: {e}",liveSubMb:"Anfragen an das Ger\xE4t und seine Antworten, mit Unit-ID und Funktion.",liveEmptyMb:"Noch keine Anfragen. Sobald ein Client fragt, erscheinen hier Anfragen und Antworten.",mbRequests:"Anfragen",mbFailed:"ohne Antwort",mbConf:"Timeout {ms} ms \xB7 {n} weitere Versuche",mbGapShort:"Pause {ms} ms",mbStats:"Modbus",mbReachable:"erreichbar",mbUnreachable:"nicht erreichbar",mbUnknown:"noch unbekannt",mbAnswered:"beantwortet",mbExceptions:"Ausnahmen",mbTimeouts:"Timeouts",mbErrors:"Fehler",mbQueue:"Warteschlange",mbWrite:"Schreibzugriff",mbWriteSub:"Modbus hat keine Anmeldung: wer den Port erreicht, kann sonst Register am Ger\xE4t \xE4ndern.",wa_all:"Alle Clients",wa_listed:"Nur diese",wa_none:"Niemand",wasub_all:"Lesen und Schreiben f\xFCr jeden Client, wie bei ha-modbusproxy.",wasub_listed:"Lesen f\xFCr alle, schreiben nur f\xFCr die genannten Adressen.",wasub_none:"Nur lesen. Schreibbefehle bekommen die Ausnahme 0x01 (unzul\xE4ssige Funktion).",mbWriteClients:"D\xFCrfen schreiben",mbWriteClientsHint:"Adressen oder Netze. Home Assistant: 127.0.0.1, andere Apps: 172.30.32.0/23.",mbProbe:"Pr\xFCfabfrage",mbProbeSub:"Liest ein Register, wenn eine Weile niemand gefragt hat: \u201Eerreichbar\u201C stimmt dann auch ohne Clients, und das Ger\xE4t trennt die Verbindung nicht wegen Leerlauf.",mbProbeSeconds:"Nach Ruhe von (s, 0 = aus)",mbUnit:"Unit-ID",mbFunction:"Funktion",mbAddress:"Register",mbAddressHint:"Adresse ab 0, wie im Telegramm (z. B. 40001 \u2192 0).",fc_3:"03 \xB7 Holding-Register",fc_4:"04 \xB7 Input-Register",mbProbes:"Pr\xFCfabfragen",mbProbeVal:"nach {s} s \xB7 Unit {u} \xB7 FC0{f} \xB7 Register {a}",mbReadTitle:"Register lesen",mbReadSub:"Fragt das Ger\xE4t direkt \u2013 der Reihe nach mit den Clients, ohne den Zwischenspeicher.",mbCount:"Anzahl",mbReadBtn:"Lesen",mbUnsigned:"ohne Vorzeichen",mbSigned:"mit Vorzeichen",mbBit:"Wert",mbReadTime:"Antwort nach {ms} ms",fc_1:"01 \xB7 Coils",fc_2:"02 \xB7 Diskrete Eing\xE4nge",mbNoAnswer:"Keine Antwort.",mbException:"Ausnahme {c}: {n}",ex_1:"Funktion nicht unterst\xFCtzt",ex_2:"Adresse ung\xFCltig",ex_3:"Wert ung\xFCltig",ex_4:"Ger\xE4tefehler",ex_5:"best\xE4tigt, in Arbeit",ex_6:"Ger\xE4t besch\xE4ftigt",ex_10:"Weg zum Ger\xE4t nicht verf\xFCgbar",ex_11:"Ger\xE4t antwortet nicht",mbScanTitle:"Bus scannen",mbScanSub:"Sucht, welche Unit-IDs antworten (liest Register 0). Bei 247 Units und 200 ms dauert das bis zu etwa zwei Minuten; die Clients kommen zwischendurch dran.",mbFirst:"Von Unit",mbLast:"Bis Unit",mbScanTimeout:"Warten je Unit (ms)",mbScanNone:"Keine Unit hat geantwortet.",mbUnits:"Pro Unit-ID",mbUnitsSub:"Anfragen der Clients je Ger\xE4t am Bus",mbTimeShort:"\xD8 Antwort",mbUnitMap:"Unit-IDs umschreiben",mbUnitMapHint:"Client-Unit=Ger\xE4te-Unit, z. B. 1=3, 2=5 \u2013 f\xFCr Clients, die fest Unit 1 erwarten. Leer: unver\xE4ndert.",mbUnitMapShort:"Unit-IDs",mbLinks:"Verbindungen zum Ger\xE4t",mbLinksHint:"Mehr als 1 nur, wenn das Ger\xE4t so viele gleichzeitig erlaubt; dann laufen Anfragen parallel.",mbLinksShort:"Verbindungen zum Ger\xE4t",mbLinksVal:"{o} von {n} offen",haSnippetComment:"sensors:, switches: \u2026 siehe Doku der Modbus-Integration",haSnippet:"In Home Assistant verwenden",haSnippetSub:"F\xFCr die Modbus-Integration in configuration.yaml. Integrationen mit eigener Einrichtung (z. B. SolarEdge Modbus Multi) brauchen nur Host {h} und Port {p}.",mbBlocked:"abgewiesen",mbCached:"aus Zwischenspeicher",mbCacheShort:"Zwischenspeicher",mbCache:"Lesewerte zwischenspeichern (ms, 0 = aus)",mbCacheHint:"Gleiche Leseanfragen mehrerer Clients innerhalb dieser Zeit fragen das Ger\xE4t nur einmal. Schreiben leert den Speicher.",mbTime:"Antwortzeit \xD8 / max",mbTimeVal:"{a} / {m} ms",mbLastAnswer:"Letzte Antwort",mbListenError:"Port kann nicht ge\xF6ffnet werden: {e}",mbLastError:"Letzter Fehler",error:"Fehler",loading:"L\xE4dt \u2026",confirm:"Best\xE4tigen",yes:"Ja",no:"Nein",close:"Schlie\xDFen",language:"Sprache",connectionLost:"Keine Verbindung zur App \u2013 zeige den letzten Stand."},en:{portWarn:"Note: {w}. Saving still works; the connection starts as soon as the port is free.",appTitle:"Device Proxy",running:"ser2net running",notRunning:"ser2net not running",appRunning:"Running",problems:"{n} with a problem",navConnections:"Connections",navEvents:"Events",navTrace:"Trace",navSettings:"Settings",navMain:"Sections",breadcrumb:"Path",connectionsTitle:"Connections",connectionsSub:"Serial and Modbus devices, shared over the network.",importExport:"Import / export",addConnection:"Add connection",tileActive:"Active",tileOf:"of {n}",tileClients:"Clients connected",tileErrors:"Line errors",tileReach:"Reachable from",listen_local:"this host only",listen_lan:"LAN \xB7 private networks only",listen_all:"all networks",stRunning:"Running",stDisabled:"Disabled",stMissing:"Device missing",stWaiting:"Waiting for ser2net",stPending:"Change pending",clients:"Clients",clientsOf:"{n} of {m}",noClients:"No clients connected.",disabledText:"Connection disabled \u2013 port closed.",missingText:"Device not plugged in.",since:"since {t}",copy:"Copy",copied:"Copied",edit:"Edit",details:"Details",switchLabel:"{name} active",emptyTitle:"No connections yet",emptyText:"Add a connection or take over your existing ser2net or modbus-proxy configuration.",emptyImport:"Import ser2net.yaml / ser2net.conf",customActive:"Your own ser2net.yaml is in use",customActiveText:"The forms are kept but not used. ser2net's ports:",toSettings:"To the settings",stuck:"Client {a} does not read",lineErrors:"{n} line errors",latencyRO:"FTDI latency cannot be changed",keptOpen:"Device kept open",live:"Live data",liveSub:"Read from ser2net's trace \u2013 takes no client place.",pause:"Pause",resume:"Resume",hexOnly:"Hex only",hexAscii:"Hex + ASCII",liveEmpty:"No data yet. ser2net opens the device only while a client is connected \u2013 or with \u201Ckeep device open\u201D.",clientTh:"Client",sinceTh:"Connected since",toClient:"to client",fromClient:"from client",queued:"Queue",addresses:"Addresses to copy",target_ha:"Home Assistant (integrations)",target_apps:"Other apps (e.g. Z-Wave JS UI)",target_lan:"Other computers in the LAN",notReachable:"not reachable with this setting",lanUnknown:"LAN address unknown",configuration:"Configuration",line:"Line",noLineErrors:"no errors",lineUnsupported:"The driver does not count errors.",lineClosed:"Counted only while the device is open.",frame:"Frame",parity:"Parity",overrun:"Overrun",brk:"Break",bufOverrun:"Buffer",dataFromDevice:"Data from the device",lastData:"Last data",never:"never",recent:"Recent",allEvents:"All events",device:"Device",resolved:"Resolved",usb:"USB",serialNo:"Serial no.",interface:"Interface",network:"Network",newConnection:"New connection",editConnection:"Edit connection",template:"Template",templateSub:"Fills in the fields; everything stays editable.",tpl_ehz_sml:"eHZ SML",tpl_ehz_d0:"eHZ D0",tpl_zwave:"Z-Wave stick",tpl_generic:"Generic",tplsub_ehz_sml:"9600 8N1 \xB7 up to 5 clients",tplsub_ehz_d0:"9600 7E1 \xB7 up to 5 clients",tplsub_zwave:"115200 8N1 \xB7 nodelay",tplsub_generic:"9600 8N1 \xB7 1 client",basics:"Basics",name:"Name",enabled:"Active",enabledText:"Share after saving",devicePick:"Device",deviceOther:"Other path \u2026",devicePath:"Path",usedBy:"used: {n}",noSerial:"no serial no.",ambiguous:"Several identical adapters without a serial number: chosen by USB port (by-path). In Proxmox pass these through by port.",ifNet:"Interface and network",baud:"Baud rate",format:"Format",dataBits:"Data bits",parityF:"Parity",stopBits:"Stop bits",port:"TCP port",maxClients:"Max. clients",maxClientsHint:"More than 1 only if the device copes with it.",mode:"Mode",mode_raw:"Bytes passed on unchanged \u2013 fits most integrations.",mode_rfc2217:"Clients set baud rate and lines themselves (rfc2217://\u2026).",mode_telnet:"For terminal access with telnet.",advanced:"Advanced",advancedSub:"ser2net options \xB7 all optional",open:"open",closeA:"close",set:"{n} set",serialSide:"Serial side",connectionSide:"Connection",tcpSide:"TCP",appSide:"App",o_local:"Ignore the modem lines (CD)",o_rtscts:"Hardware flow control",o_xonxoff:"Software flow control",o_hangup_when_done:"Drop DTR when the last client leaves",o_nobreak:"Suppress the break signal",o_low_latency:"FTDI latency 1 ms instead of 16 ms",o_kickolduser:"Disconnect an old client when full",o_chardelay:"Collect bytes and send them together",o_nodelay:"Nagle off \u2013 less latency",o_keep_open:"Keep the device open (the app connects itself, takes a place)",o_stuck_disconnect:"Disconnect the clients when one stops reading",o_notify_missing:"Notify when the device is missing or does not answer",o_notify_no_client:"Notify when no client is connected",dtr:"DTR on open",rts:"RTS on open",lineDefault:"unchanged",on:"on",off:"off",rs485:"RS485",rs485Hint:"e.g. 0:0:rts_on_send \u2013 empty = off",timeout:"Timeout (s, 0 = never)",retry:"Retry after (s, 0 = default)",remaddr:"Allowed clients (remaddr)",remaddrHint:"Empty: as the global setting. Addresses or networks, separated by spaces.",banner:"Banner",openstr:"openstr",closestr:"closestr",bind:"Bind address",bindHint:"Empty: as the global setting.",extra:"Further options",extraHint:"One per line: name: value",traceMode:"Record trace",silence:"Warn when no data for (min, 0 = never)",tr_off:"off",tr_rx:"from the device",tr_tx:"to the device",tr_both:"both directions",preview:"Preview ser2net.yaml",previewSub:"This is what ser2net gets.",save:"Save",cancel:"Cancel",delete:"Delete",saveHint:"Only this connection is rebuilt. The others stay connected.",saved:"Saved.",savedRebuilt:"Saved. Rebuilt: {n}.",savedReconnect:" Clients reconnected: {n}.",deleteConfirm:"Delete connection \u201C{n}\u201D? Its clients are disconnected.",errorsBelow:"Please check the marked fields.",importTitle:"Import / export",stepChoose:"Choose file",stepPreview:"Check preview",stepDone:"Done",importChoose:"Choose ser2net.yaml, ser2net.conf or a Modbus proxy configuration",importDrop:"Choose a file or paste its content",importFormats:"ser2net 4 (YAML, version 1 and 2), ser2net 3 (ser2net.conf) or the options of ha-modbusproxy (YAML from its configuration tab) or modbus-proxy",chooseFile:"Choose file",pasteHere:"\u2026 or paste the content here",readPreview:"Preview",otherFile:"Other file",format_0:"ser2net 3 (ser2net.conf)",format_1:"ser2net 4 \xB7 YAML version 1",format_2:"ser2net 4 \xB7 YAML version 2",format_10:"ha-modbusproxy (options)",format_11:"modbus-proxy",found:"{n} connections found",merge:"Add",mergeSub:"Existing ones stay; on a collision you choose per connection",replaceAll:"Replace all",replaceAllSub:"Existing connections are removed",result:"Result",resOk:"taken over",resNotes:"with notes",resNo:"cannot be taken over",resConflict:"collision",onConflict:"On collision",c_replace:"replace existing",c_new_port:"new port",c_skip:"skip",take:"Take over",selected:"{n} of {m} selected",apply:"Take over {n}",doneTitle:"{n} connections taken over",doneText:"The previous state is in the configuration history.",toConnections:"To the connections",exportTitle:"Export",exportText:"The connections as a ser2net 4 ser2net.yaml \u2013 as a backup or for another computer.",exportDisabled:"Include disabled connections",download:"Download ser2net.yaml",ownTitle:"Rather use the file as it is?",ownText:"For setups the forms cannot express.",toSource:"Change the configuration source",fileNotes:"Notes on the file",eventsTitle:"Events",eventsSub:"The app's live log and history.",tabLive:"Live log",tabHistory:"History",allConnections:"All connections",search:"Search",searchPh:"e.g. disconnected, 192.168.1.20",lv_info:"Info",lv_warning:"Warning",lv_error:"Error",lv_debug:"Debug",entries:"{n} entries",both:"Both",paused:"Paused",liveState:"Live",noEntries:"No entries for this filter.",drops:"Drops ({d} d)",availability:"Available",stable:"stable",unstable:"{n}\xD7 disconnected",timeline:"Timeline",retention:"Kept {d} days",today:"Today",yesterday:"Yesterday",summed:"{n}\xD7 summed up",traceTitle:"Trace",traceSub:"Bytes between device and clients. Recording disconnects no client; files rotate on their own.",recording:"recording \xB7 {m}",notRecording:"not recording",files:"Files",fileTh:"File",sizeTh:"Size",changedTh:"Changed",rotation:"Rotation: {mb} MB per file \xB7 {k} older kept",change:"change",deleteFile:"Delete \u201C{n}\u201D?",settingsTitle:"Settings",sNet:"Network",sNetSub:"Applies to all connections without their own bind address or remaddr.",net_local:"This host only",netsub_local:"127.0.0.1 \xB7 Home Assistant only",net_apps:"Home Assistant + apps",netsub_apps:"127.0.0.0/8 and 172.30.32.0/23 \xB7 not from the LAN",net_lan:"LAN",netsub_lan:"private networks only",net_all:"All networks",netsub_all:"no limit",netWarn:"ser2net has no login. Whoever reaches the port can read and control the device.",sSource:"Configuration source",sSourceSub:"Forms, or your own ser2net.yaml for special cases.",forms:"Forms",own:"Own ser2net.yaml",ownWarn:"While your own file is in use, the forms are not used. No admin section: the app adds its own.",check:"Check",saveFile:"Save",saveUse:"Save and use",checkOk:"Valid \xB7 {n} connections",notChecked:"Not checked yet",sHistory:"Configuration history",sHistorySub:"the last 20 versions",current:"current",diff:"Differences",hide:"Hide",restore:"Restore",listenConfirm:"Change who can reach the devices? The clients of all connections are disconnected.",ownConfirm:"Use your own ser2net.yaml? All connections from the forms are switched off.",restoreConfirm:"Restore this version? Changed connections are rebuilt.",src_ui:"web interface",src_import:"import",src_custom:"own file",src_restore:"restore",src_test:"test",sLogging:"Logging and storage",logLevel:"Log level",historyDays:"Keep history (days)",traceMb:"Trace: size per file (MB)",traceKeep:"Trace: older files",debounceCount:"Sum up repeats from",debounceMinutes:"within (min)",sAbout:"About",app:"App",license:"License MIT",source:"Source",tools:"Tools",meterCheck:"Check meter data",meterCheckSub:"Reads the data of the last 30 s as SML or D0.",proto_sml:"SML",proto_d0:"D0 (text)",proto_unknown:"no meter protocol found",telegrams:"{n} telegrams",validCrc:"{n} valid (CRC)",validD0:"{n} complete",noData30:"No data in the last 30 s.",baudDetect:"Detect baud rate",baudDetectSub:"Listens briefly at each baud rate and format; sends nothing.",baudConfirm:"For the detection ser2net lets go of the device for up to about a minute \u2013 this connection's clients are disconnected and connect again afterwards. Start?",start:"Start",detecting:"Checking {d} of {t} \u2026",detected:"Found: {b} {f}",noDetect:"Nothing clear found.",applyThis:"Use this",candidates:"Best matches",score:"Match","obis_1-0:1.8.0":"Import total","obis_1-0:2.8.0":"Export total","obis_1-0:16.7.0":"Power","obis_1-0:1.8.1":"Import tariff 1","obis_1-0:1.8.2":"Import tariff 2",sNotify:"Notifications",sNotifySub:"As a notification under Home Assistant's bell; optionally also to a phone.",notifyGrace:"Report when a problem lasts longer than (s)",notifyDismiss:"Remove the notification when the problem is gone",notifyService:"Also send to (notify service)",notifyNone:"do not send",notifyResolved:"Also report when it is OK again",notifyStuck:"A client stops reading",notifyLine:"Line errors rise",notifySer2net:"ser2net keeps restarting",notifyLanguage:"Language of the notifications",noClientMinutes:"Report \u201Cno client\u201D after (min)",notifyPerConnection:"Device missing, no client and no data are set per connection.",sMqtt:"MQTT entities",sMqttSub:"One device per connection in Home Assistant: connected, clients, data rate, last data, line errors and a switch; for Modbus reachable, requests, unanswered and answer time.",mqttOn:"Create entities over MQTT",mqttBroker:"Broker: {b}",mqttNoBroker:"No MQTT broker found in Home Assistant (e.g. the Mosquitto add-on) \u2013 entities are off.",mqttConnected:"connected",mqttDisconnected:"not connected",mqttPrefix:"Discovery prefix",mqttBase:"Base topic",mqttInterval:"Send states every (s)",mqttNames:"Entity names follow the language of the notifications.",src_mqtt:"MQTT switch",sDiag:"Diagnostics",sDiagSub:"ZIP with versions, configuration, status, devices and events \u2013 without IP addresses, clients only counted.",diagDownload:"Download diagnostics",kind:"Kind",kindSub:"What is to be shared?",kind_serial:"Serial device",kind_modbus:"Modbus device",kindsub_serial:"USB or serial through ser2net, e.g. meters, Z-Wave stick",kindsub_modbus:"Modbus TCP or RTU for several Modbus TCP clients, e.g. inverters",mbDevice:"Modbus device",mbLink:"Connection to the device",link_tcp:"Modbus TCP",link_rtu:"Modbus RTU (serial)",link_rtu_tcp:"RTU over TCP",linksub_tcp:"A device in the network, e.g. inverter, heat pump, battery.",linksub_rtu:"An RS485 adapter on this host \u2013 the app opens it itself.",linksub_rtu_tcp:"An RS485-to-Ethernet converter in transparent mode.",mbHost:"Device address",mbHostHint:"IP address or host name",mbHostPort:"Device port",mbProxy:"Proxy",mbPort:"TCP port for the clients",mbPortHint:"The integrations connect here (default 502).",mbClientsHint:"Modbus TCP clients at the same time.",mbTimeout:"Answer timeout (ms)",mbTimeoutHint:"How long the proxy waits for the device.",mbRetries:"Further attempts",mbConnectDelay:"Pause after connecting (ms)",mbConnectDelayHint:"For devices that need a moment after the connection is made (connection_time).",mbGap:"Pause between requests (ms)",mbGapHint:"For slow devices; 0 = at once.",advancedSubMb:"Clients and network \xB7 all optional",mbIdle:"Disconnect idle clients after (s, 0 = never)",allowed:"Allowed clients",trmb_off:"off",trmb_rx:"answers",trmb_tx:"requests",trmb_both:"requests and answers",mbPreview:"How the proxy works",mbPreviewSub:"All requests go to the device one after another over one connection.",mbFlowClients:"Up to {n} clients",mbFlowQueue:"Queue",mbFlowQueueSub:"one request after the other \xB7 timeout {ms} ms \xB7 {n} further attempts",stPortBusy:"Port in use",stStarting:"Starting",stUnreachable:"Not reachable",mbAvg:"avg {ms} ms",mbFailedN:"{n} unanswered",mbDownText:"Device not reachable: {e}",liveSubMb:"Requests to the device and its answers, with unit id and function.",liveEmptyMb:"No requests yet. As soon as a client asks, requests and answers show here.",mbRequests:"Requests",mbFailed:"unanswered",mbConf:"timeout {ms} ms \xB7 {n} further attempts",mbGapShort:"pause {ms} ms",mbStats:"Modbus",mbReachable:"reachable",mbUnreachable:"not reachable",mbUnknown:"not known yet",mbAnswered:"answered",mbExceptions:"exceptions",mbTimeouts:"timeouts",mbErrors:"errors",mbQueue:"queue",mbWrite:"Write access",mbWriteSub:"Modbus has no login: otherwise whoever reaches the port can change registers on the device.",wa_all:"All clients",wa_listed:"Only these",wa_none:"Nobody",wasub_all:"Read and write for every client, as with ha-modbusproxy.",wasub_listed:"Read for all, write only for the addresses given.",wasub_none:"Read only. Writes get exception 0x01 (illegal function).",mbWriteClients:"May write",mbWriteClientsHint:"Addresses or networks. Home Assistant: 127.0.0.1, other apps: 172.30.32.0/23.",mbProbe:"Probe",mbProbeSub:"Reads one register when nobody asked for a while: \u201Creachable\u201D is then right without clients too, and the device does not close the connection for being idle.",mbProbeSeconds:"After a quiet time of (s, 0 = off)",mbUnit:"Unit id",mbFunction:"Function",mbAddress:"Register",mbAddressHint:"Address from 0, as in the frame (e.g. 40001 \u2192 0).",fc_3:"03 \xB7 holding registers",fc_4:"04 \xB7 input registers",mbProbes:"probes",mbProbeVal:"after {s} s \xB7 unit {u} \xB7 FC0{f} \xB7 register {a}",mbReadTitle:"Read registers",mbReadSub:"Asks the device directly \u2013 in turn with the clients, without the cache.",mbCount:"Count",mbReadBtn:"Read",mbUnsigned:"unsigned",mbSigned:"signed",mbBit:"Value",mbReadTime:"Answer after {ms} ms",fc_1:"01 \xB7 coils",fc_2:"02 \xB7 discrete inputs",mbNoAnswer:"No answer.",mbException:"Exception {c}: {n}",ex_1:"illegal function",ex_2:"illegal data address",ex_3:"illegal data value",ex_4:"server device failure",ex_5:"acknowledge, in progress",ex_6:"server device busy",ex_10:"gateway path unavailable",ex_11:"device does not answer",mbScanTitle:"Scan the bus",mbScanSub:"Finds the unit ids that answer (reads register 0). With 247 units and 200 ms this takes up to about two minutes; the clients get their turns in between.",mbFirst:"From unit",mbLast:"To unit",mbScanTimeout:"Wait per unit (ms)",mbScanNone:"No unit answered.",mbUnits:"Per unit id",mbUnitsSub:"The clients' requests per device on the bus",mbTimeShort:"avg answer",mbUnitMap:"Rewrite unit ids",mbUnitMapHint:"client unit=device unit, e.g. 1=3, 2=5 \u2013 for clients that always ask unit 1. Empty: unchanged.",mbUnitMapShort:"Unit ids",mbLinks:"Connections to the device",mbLinksHint:"More than 1 only when the device allows that many at once; requests then run in parallel.",mbLinksShort:"Connections to the device",mbLinksVal:"{o} of {n} open",haSnippetComment:"sensors:, switches: \u2026 see the Modbus integration's documentation",haSnippet:"Use in Home Assistant",haSnippetSub:"For the Modbus integration in configuration.yaml. Integrations with their own setup (e.g. SolarEdge Modbus Multi) only need host {h} and port {p}.",mbBlocked:"refused",mbCached:"from cache",mbCacheShort:"Cache",mbCache:"Cache reads (ms, 0 = off)",mbCacheHint:"The same read from several clients within this time asks the device once. A write empties the cache.",mbTime:"Answer time avg / max",mbTimeVal:"{a} / {m} ms",mbLastAnswer:"Last answer",mbListenError:"Port cannot be opened: {e}",mbLastError:"Last error",error:"Error",loading:"Loading \u2026",confirm:"Confirm",yes:"Yes",no:"No",close:"Close",language:"Language",connectionLost:"No connection to the app \u2013 showing the last state."}},Et={de:{app_started:"Gestartet mit {connections} Verbindungen, {active} aktiv",connection_loaded:"{state}: {device} \xB7 {format} \xB7 {mode} \xB7 Port {port} \xB7 bis {max_clients} Clients",config_changed:"Konfiguration gespeichert: {summary}",clients_reconnect:"{count} Client(s) getrennt, damit die \xC4nderung greift",client_connected:"Client verbunden: {address}",client_disconnected:"Client getrennt: {address}",client_stuck:"Client {address} liest nicht ({queued} Bytes warten) \u2013 alle Clients dieser Verbindung werden gebremst",stuck_disconnected:"Clients getrennt, weil {address} nicht las",device:"Ger\xE4t gefunden: {device} \u2192 {target}",device_back:"Ger\xE4t wieder da: {device} \u2192 {target}",device_missing:"Ger\xE4t fehlt: {device}",modbus_loaded:"{state}: Modbus {link} {target} \xB7 Port {port} \xB7 bis {max_clients} Clients",modbus_down:"Ger\xE4t nicht erreichbar: {target} ({error})",modbus_back:"Ger\xE4t wieder erreichbar: {target}",listen_failed:"Port {port} kann nicht ge\xF6ffnet werden: {error}",client_refused:"Client abgewiesen, alle Pl\xE4tze belegt: {address}",write_blocked:"Schreiben abgewiesen (Funktion {function}) von {address}",keep_open_failed:"Ger\xE4t konnte nicht offen gehalten werden: {error}",ser2net_restart:"ser2net beendet (Code {code}), Neustart in {delay} s",line_errors:"Leitungsfehler seit Start: {frame} Frame, {parity} Parit\xE4t, {overrun} Overrun, {buffer_overrun} Puffer, {break} Break",latency_read_only:"FTDI-Latenz lie\xDF sich nicht auf 1 ms setzen: /sys ist f\xFCr die App schreibgesch\xFCtzt",custom_saved:"Eigene ser2net.yaml gespeichert ({connections} Verbindungen)",custom_invalid:"Eigene ser2net.yaml nicht verwendbar \u2013 nichts wird bereitgestellt",imported:"Import: {taken} \xFCbernommen, {skipped} \xFCbersprungen, {notes} Hinweise",import_failed:"Import fehlgeschlagen"},en:{}},it={de:{device_missing:"Ger\xE4t {device} ist gerade nicht angeschlossen.",device_unstable:"{device} kann sich nach einem Neustart \xE4ndern \u2013 besser einen by-id- oder by-path-Namen w\xE4hlen.",device_renamed:"{device} durch den stabilen Namen {stable} ersetzt.",option_extra:"Option {option} \xFCbernommen als \u201Eweitere Option\u201C.",option_dropped:"Option {option} nicht \xFCbernommen.",serial_option_dropped:"Serielle Option {option} nicht \xFCbernommen.",legacy_option_dropped:"Option {option} nicht \xFCbernommen.",accepter_option_dropped:"Accepter-Option {option} nicht \xFCbernommen.",remaddr_port_dropped:"remaddr {address}: der Client-Port f\xE4llt weg.",remaddr_dropped:"remaddr {address} nicht lesbar, weggelassen.",trace_files_moved:"Trace-Dateien werden durch den Mitschnitt der App ersetzt.",external_file:"Option {option} liest eine externe Datei \u2013 bitte pr\xFCfen.",accepter_unsupported:"Accepter {accepter} wird nicht unterst\xFCtzt (nur TCP, telnet, RFC2217).",connector_unsupported:"Connector {connector} wird nicht unterst\xFCtzt (nur serielle Ger\xE4te).",invalid:"Ung\xFCltig: {errors}",admin_ignored:"Admin-Abschnitt ignoriert \u2013 die App hat ihren eigenen.",include_ignored:"include {path} ignoriert.",section_ignored:"Abschnitt {section} ignoriert.",define_unresolved:"Nicht aufgel\xF6ste Defines: {names}.",no_connections:"Keine Verbindungen in der Datei.",default_ignored:"DEFAULT {name} ignoriert.",line_unreadable:"Zeile nicht lesbar: {line}",yaml:"YAML-Fehler in Zeile {line}: {message}",admin_present:"Die Datei hat einen admin-Abschnitt \u2013 bitte entfernen, die App f\xFCgt ihren eigenen an.",port_twice:"Port {port} doppelt: {names}.",port_reserved:"Port {port} ist f\xFCr die App reserviert.",port_modbus:"Port {port} ({name}) belegt schon der Modbus-Proxy \u201E{modbus}\u201C.",legacy_format:"Das alte Format (ser2net.conf) kann ser2net 4 nicht lesen \u2013 bitte importieren.",unreadable:"Datei nicht lesbar: {error}",modbus_stop_old:"Vor dem \xDCbernehmen ha-modbusproxy stoppen \u2013 beide k\xF6nnen nicht am selben Port lauschen."},en:{device_missing:"Device {device} is not plugged in right now.",device_unstable:"{device} may change after a restart \u2013 better choose a by-id or by-path name.",device_renamed:"{device} replaced by its stable name {stable}.",option_extra:"Option {option} kept as a further option.",option_dropped:"Option {option} not taken over.",serial_option_dropped:"Serial option {option} not taken over.",legacy_option_dropped:"Option {option} not taken over.",accepter_option_dropped:"Accepter option {option} not taken over.",remaddr_port_dropped:"remaddr {address}: the client port is dropped.",remaddr_dropped:"remaddr {address} unreadable, left out.",trace_files_moved:"Trace files are replaced by the app's trace.",external_file:"Option {option} reads an external file \u2013 please check.",accepter_unsupported:"Accepter {accepter} is not supported (TCP, telnet, RFC2217 only).",connector_unsupported:"Connector {connector} is not supported (serial devices only).",invalid:"Invalid: {errors}",admin_ignored:"Admin section ignored \u2013 the app has its own.",include_ignored:"include {path} ignored.",section_ignored:"Section {section} ignored.",define_unresolved:"Unresolved defines: {names}.",no_connections:"No connections in the file.",default_ignored:"DEFAULT {name} ignored.",line_unreadable:"Line unreadable: {line}",yaml:"YAML error in line {line}: {message}",admin_present:"The file has an admin section \u2013 please remove it, the app adds its own.",port_twice:"Port {port} twice: {names}.",port_reserved:"Port {port} is reserved for the app.",port_modbus:'Port {port} ({name}) is held by the Modbus proxy "{modbus}" already.',legacy_format:"ser2net 4 cannot read the old format (ser2net.conf) \u2013 please import it.",unreadable:"File unreadable: {error}",modbus_stop_old:"Stop ha-modbusproxy before taking over \u2013 both cannot listen on the same port."}},Dt=[[/^between (\d+) and (\d+)$/,"zwischen $1 und $2"],[/^(\d+) to (\d+) seconds$/,"$1 bis $2 Sekunden"],[/^(\d+) to (\d+) minutes$/,"$1 bis $2 Minuten"],[/^(\d+) to (\d+) days$/,"$1 bis $2 Tage"],[/^(\d+) to (\d+) characters$/,"$1 bis $2 Zeichen"],[/^(\d+) to (\d+) files$/,"$1 bis $2 Dateien"],[/^0 or (\d+) to (\d+) seconds$/,"0 oder $1 bis $2 Sekunden"],[/^'(.+)' is not unit=unit \(0 to 255\)$/,"\u201E$1\u201C ist nicht Unit=Unit (0 bis 255)"],[/^unit (\d+) twice$/,"Unit $1 doppelt"],[/^1 for a serial device$/,"1 bei einem seriellen Ger\xE4t"],[/^in use by another program$/,"von einem anderen Programm belegt"],[/^the bind address is not on this host$/,"die Bind-Adresse gibt es auf diesem Rechner nicht"],[/^(\d+) to (\d+) MB$/,"$1 bis $2 MB"],[/^(\d+) to (\d+) ms$/,"$1 bis $2 ms"],[/^a host name or IP address$/,"ein Hostname oder eine IP-Adresse"],[/^is this connection's own port$/,"ist der eigene Port dieser Verbindung"],[/^(\d+) to (\d+)$/,"$1 bis $2"],[/^(\d+) or (\d+)$/,"$1 oder $2"],[/^a path under \/dev without commas or spaces$/,"ein Pfad unter /dev ohne Kommas und Leerzeichen"],[/^an IP address of this host$/,"eine IP-Adresse dieses Rechners"],[/^also used by (.+)$/,"schon verwendet von $1"],[/^another connection has this name$/,"eine andere Verbindung hei\xDFt schon so"],[/^used by the app's web interface$/,"von der Weboberfl\xE4che der App belegt"],[/^at least 2 when the device is kept open \(the app uses one\)$/,"mindestens 2, wenn das Ger\xE4t offen gehalten wird (die App belegt einen Platz)"],[/^'(.+)' is not an option name$/,"\u201E$1\u201C ist kein Optionsname"],[/^(.+) has its own field$/,"$1 hat ein eigenes Feld"],[/^'(.+)' is not an address or network$/,"\u201E$1\u201C ist keine Adresse und kein Netz"],[/^no address or network given$/,"keine Adresse und kein Netz angegeben"],[/^a notify service name like (.+)$/,"ein Notify-Dienst wie $1"],[/^an MQTT topic without wildcards$/,"ein MQTT-Topic ohne Platzhalter"],[/^at most (\d+) characters$/,"h\xF6chstens $1 Zeichen"],[/^de or en$/,"de oder en"],[/^is not an id of this app$/,"ist keine ID dieser App"],[/^n, e, o, m or s$/,"n, e, o, m oder s"],[/^on, off or empty$/,"on, off oder leer"],[/^not 0 on RTU: a broadcast, nothing answers it$/,"nicht 0 bei RTU: ein Broadcast, auf den nie jemand antwortet"],[/^is missing$/,"fehlt"],[/^has the wrong type$/,"hat den falschen Typ"],[/^one of (.+)$/,"eins von: $1"],[/^off or <delay before>:<delay after>\[:<conf>\]$/,"off oder <vorher>:<nachher>[:<conf>]"]];function N(o){if($!=="de")return o;for(let[e,t]of Dt)if(e.test(o))return o.replace(e,t);return o}var Mt=(()=>{if(typeof window>"u")return null;try{return localStorage.getItem("device_proxy.lang")}catch{return null}})(),$=Mt||((globalThis.navigator?.language||"en").toLowerCase().startsWith("de")?"de":"en");function at(o){$=o;try{localStorage.setItem("device_proxy.lang",o)}catch{}}var Ne=(o,e={})=>o.replace(/\{(\w+)\}/g,(t,n)=>{let i=e[n];return i===void 0?t:i===null?"\u2013":Array.isArray(i)?i.join(", "):typeof i=="object"?JSON.stringify(i):String(i)}),s=(o,e)=>Ne(nt[$][o]??nt.en[o]??o,e),Pt={de:{active:"aktiv",disabled:"deaktiviert"},en:{}},Lt={de:{added:"hinzugef\xFCgt",removed:"entfernt",enabled:"aktiviert",disabled:"deaktiviert",settings:"Einstellungen"},en:{added:"added",removed:"removed",enabled:"enabled",disabled:"disabled",settings:"settings"}};function He(o){let e=Lt[$];return(o||[]).map(t=>{let n=t.connection||e.settings;return t.fields?`${n}: ${t.fields.join(", ")}`:`${n} ${e[t.change]||t.change}`}).join("; ")}function B(o){let e=Et[$][o.kind];if(!e)return o.message;let t={...o.params};return t.state&&(t.state=Pt[$][t.state]||t.state),o.kind==="config_changed"&&t.changes&&(t.summary=He(t.changes)),$==="de"&&t.error==="no answer"&&(t.error="keine Antwort"),Ne(e,t)}function T(o){let e=it[$][o.code]||it.en[o.code];if(!e)return o.code;let t={...o};return t.errors&&typeof t.errors=="object"&&(t.errors=Object.entries(t.errors).map(([n,i])=>n?`${n}: ${i}`:i).join("; ")),Ne(e,t)}var me=v`
  :host {
    --bg: light-dark(#f3f4f6, #111418); --surface: light-dark(#ffffff, #1b1f24); --surface-2: light-dark(#f5f7f9, #22272e); --line: light-dark(#e1e5ea, #2d333b);
    --line-2: light-dark(#eef0f3, #262c33); --text: light-dark(#1b1f24, #e6e9ed); --muted: light-dark(#5b6270, #9aa4b1); --accent: light-dark(#0a6aa8, #5bb2ea);
    --accent-hover: light-dark(#07507f, #8ccaf2); --accent-soft: light-dark(#eaf3fa, #16324a); --ok: light-dark(#1e6b34, #7fd49a); --ok-soft: light-dark(#e6f4ea, #173a24);
    --warn: light-dark(#8a4b00, #f2c27a); --warn-soft: light-dark(#fff1de, #3a2a12); --warn-line: light-dark(#f3d19e, #6b4a1c); --bad: light-dark(#a1261b, #f2a29a);
    --bad-soft: light-dark(#fdecea, #3d1c19); --bad-line: light-dark(#f2b8b5, #6e2f2a); --neutral-soft: light-dark(#eef1f4, #2a3038); --neutral: light-dark(#3a414c, #c5ccd5);
    --code-bg: light-dark(#14181d, #0b0e11); --code-text: #d7dee6; --focus: #7db8e0; --input-line: light-dark(#c3cbd5, #3a424c);
    --on-accent: light-dark(#ffffff, #0b1a26);
    color: var(--text); font-family: Roboto, "Noto Sans", system-ui, -apple-system, sans-serif; font-size: 14px;
  }
`,fe=v`
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
`;function zt(o){let e=document.createElement("span");e.style.color=o,document.body.append(e);let t=getComputedStyle(e).color.match(/\d+(\.\d+)?/g);if(e.remove(),!t||t.length<3)return null;let[n,i,a]=t.slice(0,3).map(Number);return(.2126*n+.7152*i+.0722*a)/255}function Rt(){try{if(!window.parent||window.parent===window)return null;let o=window.parent.document.documentElement,e=window.parent.getComputedStyle(o).getPropertyValue("--primary-background-color").trim(),t=e?zt(e):null;return t===null?null:t<.5}catch{return null}}function ge(){let o=Rt();document.documentElement.style.colorScheme=o===null?"light dark":o?"dark":"light"}var rt=(o=36)=>r`<svg width=${o} height=${o} viewBox="0 0 128 128" aria-hidden="true" style="flex:none">
  <rect width="128" height="128" rx="28" fill="#0A6AA8"></rect>
  <g fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
    <path d="M16 46H70L64 82H22Z"></path><path d="M67 64H84M84 64L104 40M84 64H108M84 64L104 88"></path></g>
  <g fill="#FFFFFF"><circle cx="104" cy="40" r="11"></circle><circle cx="108" cy="64" r="11"></circle><circle cx="104" cy="88" r="11"></circle></g></svg>`,Nt={plus:"M12 5v14M5 12h14",upload:"M12 15V3M7 8l5-5 5 5M5 21h14",download:"M12 3v12M7 10l5 5 5-5M5 21h14",copy:"M9 9h12v12H9zM5 15V5a2 2 0 0 1 2-2h10",warn:"M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",info:"M12 16v-4M12 8h.01M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",file:"M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5",serial:"M3 8h14l-2 8H5zM7 12h.01M10 12h.01M13 12h.01M17 12h4",modbus:"M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01M12 10v4"},_=(o,e=18)=>r`<svg width=${e} height=${e} viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ue`<path d=${Nt[o]}></path>`}</svg>`;function E(o){if(o==null)return"\u2013";let e=["B","kB","MB","GB"],t=o,n=0;for(;t>=1e3&&n<e.length-1;)t/=1e3,n++;return`${t.toLocaleString($,{maximumFractionDigits:n?1:0})} ${e[n]}`}var ve=o=>`${E(Math.round(o||0))}/s`;function w(o,e=!0,t=!1){if(!o)return s("never");let n=new Date(o*1e3),i=new Date,a=n.toLocaleTimeString($,{hour:"2-digit",minute:"2-digit",...t?{second:"2-digit"}:{}});if(!e||n.toDateString()===i.toDateString())return a;let l=new Date(i.getTime()-864e5);return n.toDateString()===l.toDateString()?`${s("yesterday")} ${a}`:`${n.toLocaleDateString($,{day:"2-digit",month:"2-digit"})} ${a}`}function q(o){if(!o)return s("never");let e=Math.max(0,Date.now()/1e3-o),t=new Intl.RelativeTimeFormat($,{numeric:"auto"});return e<60?t.format(-Math.round(e),"second"):e<3600?t.format(-Math.round(e/60),"minute"):e<86400?t.format(-Math.round(e/3600),"hour"):t.format(-Math.round(e/86400),"day")}var I=o=>o.link==="rtu"?o.device:`${o.host.includes(":")?`[${o.host}]`:o.host}:${o.host_port}`,D=o=>`${o.baud} ${o.data_bits}${o.parity.toUpperCase()}${o.stop_bits}`,$e=(o,e,t,n=!1)=>r`<button type="button" class="switch" role="switch"
  aria-checked=${o?"true":"false"} aria-label=${e} ?disabled=${n} @click=${()=>t(!o)}><span></span></button>`;async function ye(o){try{return await navigator.clipboard.writeText(o),!0}catch{let e=document.createElement("textarea");e.value=o,e.style.position="fixed",e.style.opacity="0",document.body.appendChild(e),e.select();let t=document.execCommand("copy");return e.remove(),t}}function V(o,e){if(!o.enabled)return["stDisabled",""];if(o.present===!1)return["stMissing","bad"];if(o.kind==="modbus"){let t=o.modbus||{};return t.listen_error?["stPortBusy","bad"]:t.listening?t.reachable===!1?["stUnreachable","bad"]:["stRunning","ok"]:["stStarting","warn"]}return e?o.pending==="reconfigured"?["stPending","info"]:["stRunning","ok"]:["stWaiting","warn"]}var Fe=o=>{let t=o.addresses.find(n=>n.target==="lan"&&n.reachable)||o.addresses.find(n=>n.target==="ha");return t?Object.values(t.urls)[0]:""},oe=o=>{location.hash=o};function S(o,e,t){return new Promise(n=>{let i=document.createElement("dp-confirm");i.message=e,i.confirmLabel=t||s("confirm"),i.addEventListener("done",a=>{i.remove(),n(a.detail)}),(o.shadowRoot||document.body).appendChild(i)})}var Ht=2e3,Ft=1500,j=class extends k{constructor(){super(),this.state=null,this.events=[],this.offline=!1,this.toast="",this._seq=0,this.route=this._parse(),this._onHash=()=>{this.route=this._parse(),window.scrollTo(0,0)}}connectedCallback(){super.connectedCallback(),window.addEventListener("hashchange",this._onHash),this.addEventListener("dp-refresh",()=>this.refresh()),this.addEventListener("dp-toast",e=>this.showToast(e.detail)),this.addEventListener("dp-lang",e=>{at(e.detail),document.documentElement.lang=e.detail,this.requestUpdate(),this._relayLang()}),document.documentElement.lang=$,this._loadHistory(),this.refresh(),this._onVisible=()=>{document.hidden||(ge(),this.refresh())},document.addEventListener("visibilitychange",this._onVisible),ge(),this._timer=setInterval(()=>{document.hidden||(ge(),this.refresh())},Ht)}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("hashchange",this._onHash),document.removeEventListener("visibilitychange",this._onVisible),clearInterval(this._timer)}_relayLang(){this.renderRoot.querySelectorAll("main > *").forEach(e=>e.requestUpdate&&e.requestUpdate())}_parse(){let e=(location.hash.replace(/^#\/?/,"")||"connections").split("/");return{page:e[0],id:e[1]||""}}async _loadHistory(){try{let e=await h("api/history?limit=300"),t=new Set(this.events.map(n=>n.id));this.events=[...e.reverse().filter(n=>!t.has(n.id)),...this.events]}catch{}}async refresh(){try{let[e,t]=await Promise.all([h("api/state"),h(`api/events?after=${this._seq}`)]);if(this.state=e,t.length){this._seq=t[t.length-1].seq;let n=new Map(this.events.map((a,l)=>[a.id??`s${a.seq}`,l])),i=[...this.events];for(let a of t){let l=a.id??`s${a.seq}`;n.has(l)?i[n.get(l)]=a:(n.set(l,i.length),i.push(a))}this.events=i.slice(-Ft)}this.offline=!1}catch{this.offline=!0}}showToast(e){this.toast=e,clearTimeout(this._toastTimer),this._toastTimer=setTimeout(()=>{this.toast=""},4500)}_page(){let{page:e,id:t}=this.route,n=this.state,i=this.events;if(!n)return r`<p class="hint">${s("loading")}</p>`;switch(e){case"connection":return r`<dp-detail .state=${n} .events=${i} .connectionId=${t}></dp-detail>`;case"edit":return r`<dp-edit .state=${n} .connectionId=${t}></dp-edit>`;case"import":return r`<dp-import .state=${n}></dp-import>`;case"events":return r`<dp-events .state=${n} .events=${i}></dp-events>`;case"trace":return r`<dp-trace .state=${n} .selected=${t}></dp-trace>`;case"settings":return r`<dp-settings .state=${n}></dp-settings>`;default:return r`<dp-connections .state=${n}></dp-connections>`}}render(){let e=this.state,t=this.route.page,n=["connection","edit","import"].includes(t)?"connections":t,i=(d,u)=>r`<a href="#/${d}" aria-current=${n===d?"page":"false"}>${s(u)}</a>`,a=e&&e.ser2net_running,l=e&&(e.source==="custom"||e.connections.some(d=>d.kind!=="modbus")),c=e?e.connections.filter(d=>V(d,a)[1]==="bad").length:0;return r`
      <header><div class="bar">
        <div class="brand">${rt()}<div><b>${s("appTitle")}</b>
          <span class="hint">${e?`App ${e.version}${l?` \xB7 ser2net ${e.ser2net_version||"?"}`:""}`:""}</span></div>
          ${e&&l?r`<span class="chip ${a?"ok":"bad"}"><span class="dot"></span>${s(a?"running":"notRunning")}</span>`:""}
          ${e&&c?r`<a class="chip warn" href="#/connections" style="text-decoration:none"><span class="dot"></span>${s("problems",{n:c})}</a>`:e&&!l?r`<span class="chip ok"><span class="dot"></span>${s("appRunning")}</span>`:""}
        </div>

        <nav aria-label=${s("navMain")}>
          ${i("connections","navConnections")}${i("events","navEvents")}${i("trace","navTrace")}${i("settings","navSettings")}
        </nav>
      </div></header>
      ${this.offline?r`<div class="offline"><div class="note warn" role="status">${s("connectionLost")}</div></div>`:""}
      <main>${this._page()}</main>
      ${this.toast?r`<div class="toast" role="status">${this.toast}</div>`:""}`}};m(j,"properties",{state:{state:!0},events:{state:!0},route:{state:!0},offline:{state:!0},toast:{state:!0}}),m(j,"styles",[me,fe,v`
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
  `]);var f=class extends k{refresh(){this.dispatchEvent(new CustomEvent("dp-refresh",{bubbles:!0,composed:!0}))}toast(e){this.dispatchEvent(new CustomEvent("dp-toast",{detail:e,bubbles:!0,composed:!0}))}connection(e){return this.state?.connections.find(t=>t.id===e)}};m(f,"styles",[me,fe,v`:host { display: block; } .head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 20px; }`]);var G=class extends k{firstUpdated(){this.renderRoot.querySelector(".btn-g").focus()}_done(e){this.dispatchEvent(new CustomEvent("done",{detail:e}))}render(){return r`<div class="back" @keydown=${e=>e.key==="Escape"&&this._done(!1)}>
      <div class="box" role="alertdialog" aria-modal="true" aria-label=${s("confirm")}>
        <p>${this.message}</p>
        <div class="actions"><button class="btn btn-g" @click=${()=>this._done(!1)}>${s("cancel")}</button>
          <button class="btn btn-p" @click=${()=>this._done(!0)}>${this.confirmLabel}</button></div>
      </div></div>`}};m(G,"properties",{message:{},confirmLabel:{}}),m(G,"styles",[me,fe,v`
    .back { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 20; padding: 16px; }
    .box { background: var(--surface); border-radius: 16px; padding: 24px; max-width: 440px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
  `]);var W=class extends f{async _enable(e,t){this.busy=e.id;try{await h(`api/connections/${e.id}/enabled`,{method:"POST",body:{enabled:t}}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}finally{this.busy=""}}async _copy(e){await ye(Fe(e))&&(this.copied=e.id,setTimeout(()=>{this.copied===e.id&&(this.copied="")},2e3))}_card(e,t,n){e.kind==="modbus"&&(n=!1);let[i,a]=V(e,t),l=!e.enabled,c=e.enabled&&e.present===!1,d=e.line_errors?Object.values(e.line_errors).reduce((g,H)=>g+H,0):0,u=e.kind==="modbus",p=e.modbus||{},b=u?[s(`link_${e.link}`),`Port ${e.port}`]:[D(e),e.mode,`Port ${e.port}`];u&&e.link==="rtu"&&b.splice(1,0,D(e)),u&&p.answered&&b.push(s("mbAvg",{ms:p.time_avg_ms})),e.nodelay&&!u&&b.push("nodelay"),(e.latency==="set"||e.latency==="already")&&b.push("FTDI 1 ms"),e.trace!=="off"&&b.push(s("recording",{m:s(`tr_${e.trace}`)}));let x=e.clients.filter(g=>g.stuck);return r`<section class="card conn ${l?"off":""} ${c?"missing":""}" aria-label=${e.name}>
      <div class="top">
        <div style="min-width:0">
          <div class="title"><span class="hint" style="display:flex" title=${s(`kind_${e.kind}`)}>${_(e.kind,20)}</span><h2>${e.name}</h2><span class="chip ${a}"><span class="dot"></span>${s(i)}</span></div>
          <div class="dev mono">${u?I(e):e.device}${e.tty&&e.tty!==e.device?r` → ${e.tty}`:""}</div>
        </div>
        ${$e(e.enabled,s("switchLabel",{name:e.name}),g=>this._enable(e,g),n||this.busy===e.id)}
      </div>
      <div class="chips">
        ${b.map(g=>r`<span class="chip">${g}</span>`)}
        ${e.kept_open?r`<span class="chip info">${s("keptOpen")}</span>`:""}
        ${d?r`<span class="chip warn">${s("lineErrors",{n:d})}</span>`:""}
        ${e.latency==="read_only"?r`<span class="chip warn">${s("latencyRO")}</span>`:""}
        ${u&&p.failed?r`<span class="chip warn">${s("mbFailedN",{n:p.failed})}</span>`:""}
        ${x.map(g=>r`<span class="chip bad">${s("stuck",{a:g.address})}</span>`)}
      </div>
      <div class="clients">
        <div class="row hint" style="font-weight:500"><span>${s("clients")}</span>
          <span>${s("clientsOf",{n:e.clients.length,m:e.max_clients})}${e.enabled&&(e.present||u)?r` · ${ve(e.rate_from_device)}`:""}</span></div>
        ${e.clients.map(g=>r`<div class="client"><span><span class="mono" style="font-size:13px">${g.address}</span></span>
          <span class="hint">${g.since?s("since",{t:q(g.since)}):""}</span></div>`)}
        ${e.clients.length?"":r`<div class="hint" style="font-size:14px">${l?s("disabledText"):c?s("missingText"):u&&p.reachable===!1?s("mbDownText",{e:p.last_error||"?"}):s("noClients")}</div>`}
      </div>
      <div class="foot">
        <div class="addr"><span class="mono">${Fe(e)}</span>
          <button class="btn btn-g" style="min-height:36px" @click=${()=>this._copy(e)} aria-label=${s("copy")}>${_("copy",16)}${this.copied===e.id?s("copied"):s("copy")}</button></div>
        <div style="display:flex;gap:4px"><a class="btn btn-g" href="#/edit/${e.id}">${s("edit")}</a><a class="btn btn-s" href="#/connection/${e.id}">${s("details")}</a></div>
      </div>
    </section>`}render(){let e=this.state,t=e.source==="custom",n=e.connections,i=n.filter(c=>c.enabled).length,a=n.reduce((c,d)=>c+d.clients.length,0),l=n.reduce((c,d)=>c+(d.line_errors?Object.values(d.line_errors).reduce((u,p)=>u+p,0):0),0);return r`
      <div class="head">
        <div><h1>${s("connectionsTitle")}</h1><p class="sub">${s("connectionsSub")}</p></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <a class="btn btn-s" href="#/import">${_("upload")}${s("importExport")}</a>
          <a class="btn btn-p" href="#/edit/new">${_("plus")}${s("addConnection")}</a>
        </div>
      </div>
      ${t?r`<div class="note info" style="margin-bottom:20px">
        <b>${s("customActive")}</b> · ${s("customActiveText")}
        ${e.custom_ports.map(c=>r` <span class="chip">${c.alias} · ${c.clients.length}</span>`)}
        · <a href="#/settings">${s("toSettings")}</a></div>`:""}
      <div class="tiles">
        <div class="tile"><span class="lbl">${s("tileActive")}</span><b>${i} <small>${s("tileOf",{n:n.length})}</small></b></div>
        <div class="tile"><span class="lbl">${s("tileClients")}</span><b>${a}</b></div>
        <div class="tile"><span class="lbl">${s("tileErrors")}</span><b style=${l?"color:var(--warn)":""}>${l}</b></div>
        <div class="tile"><span class="lbl">${s("tileReach")}</span><b style="font-size:16px;margin-top:10px">${s(`listen_${e.settings.listen}`)}</b></div>
      </div>
      ${n.length?r`<div class="cards">${n.map(c=>this._card(c,e.ser2net_running,t))}</div>`:r`
        <section class="card empty"><h2>${s("emptyTitle")}</h2><p class="hint" style="font-size:14px">${s("emptyText")}</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">
            <a class="btn btn-s" href="#/import">${_("upload")}${s("emptyImport")}</a>
            <a class="btn btn-p" href="#/edit/new">${_("plus")}${s("addConnection")}</a></div></section>`}`}};m(W,"properties",{state:{attribute:!1},copied:{state:!0},busy:{state:!0}}),m(W,"styles",[...f.styles,v`
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
  `]);var Ot=1e3,Ut=90,K=class extends f{constructor(){super(),this.chunks=[],this.paused=!1,this.ascii=!0,this._samples=[],this._after=0,this.mbForm={unit:1,function:3,address:0,count:10},this.scanForm={first:1,last:247,timeout_ms:200}}connectedCallback(){super.connectedCallback(),this._timer=setInterval(()=>this._poll(),Ot),this._poll()}disconnectedCallback(){super.disconnectedCallback(),clearInterval(this._timer)}willUpdate(e){if(e.has("connectionId")&&(this.chunks=[],this._after=0,this._samples=[]),e.has("state")){let t=this.connection(this.connectionId);t&&(this._samples=[...this._samples,t.rate_from_device].slice(-Ut))}}async _poll(){if(!(this.paused||!this.connectionId||document.hidden))try{let e=await h(`api/live/${this.connectionId}?after=${this._after}`);e.length&&(this._after=e[e.length-1].seq,this.chunks=[...this.chunks,...e].slice(-300))}catch{}}async _enable(e,t){try{await h(`api/connections/${e.id}/enabled`,{method:"POST",body:{enabled:t}}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}}async _checkMeter(){try{this.meter=await h(`api/tools/${this.connectionId}/meter`)}catch(e){this.toast(`${s("error")}: ${e.message}`)}}async _detect(){if(await S(this,s("baudConfirm"),s("start")))try{let{job:e}=await h(`api/tools/${this.connectionId}/detect`,{method:"POST"});this.job={state:"running",done:0,total:0};let t=setInterval(async()=>{try{this.job=await h(`api/jobs/${e}`),this.job.state!=="running"&&clearInterval(t)}catch{clearInterval(t)}},1e3)}catch(e){this.toast(`${s("error")}: ${e.message}`)}}async _useCandidate(e,t){try{await U({...be(e),baud:t.baud,data_bits:t.data_bits,parity:t.parity,stop_bits:t.stop_bits}),this.toast(s("saved")),this.job=null,this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}}async _mbRead(){try{this.mbResult={...await h(`api/tools/${this.connectionId}/modbus/read`,{method:"POST",body:this.mbForm}),form:{...this.mbForm}}}catch(e){this.toast(`${s("error")}: ${e.message}`)}}async _mbScan(){try{let{job:e}=await h(`api/tools/${this.connectionId}/modbus/scan`,{method:"POST",body:this.scanForm});this.scan={state:"running",done:0,total:this.scanForm.last-this.scanForm.first+1,results:[]};let t=setInterval(async()=>{try{this.scan=await h(`api/jobs/${e}`),this.scan.state!=="running"&&clearInterval(t)}catch{clearInterval(t)}},1e3)}catch(e){this.toast(`${s("error")}: ${e.message}`)}}_num(e,t,n,i){return r`<label class="fld"><span class="lbl">${n}</span><input class="inp" inputmode="numeric" .value=${String(e[t])}
      @input=${a=>{this[i]={...this[i],[t]:Number(a.target.value||0)}}}></label>`}_modbusTools(e){let t=this.mbForm,n=this.mbResult,i=this.scan,a=d=>d>32767?d-65536:d,l=d=>`0x${d.toString(16).toUpperCase().padStart(4,"0")}`,c=d=>d==null?s("mbNoAnswer"):s("mbException",{c:d.toString(16).toUpperCase().padStart(2,"0"),n:s(`ex_${d}`)});return r`<section class="card" aria-labelledby="t-mtools">
      <h2 id="t-mtools">${s("tools")}</h2>
      <div><b style="font-weight:500">${s("mbReadTitle")}</b><p class="hint">${s("mbReadSub")}</p></div>
      <div class="grid4">
        ${this._num(t,"unit",s("mbUnit"),"mbForm")}
        <label class="fld"><span class="lbl">${s("mbFunction")}</span><select class="inp" @change=${d=>{this.mbForm={...t,function:Number(d.target.value)}}}>
          ${[3,4,1,2].map(d=>r`<option value=${d} ?selected=${t.function===d}>${s(`fc_${d}`)}</option>`)}</select></label>
        ${this._num(t,"address",s("mbAddress"),"mbForm")}
        ${this._num(t,"count",s("mbCount"),"mbForm")}
      </div>
      <div><button class="btn btn-s" ?disabled=${!e.enabled} @click=${this._mbRead}>${s("mbReadBtn")}</button></div>
      ${n?n.ok?r`<div class="scroll"><table style="min-width:360px"><thead><tr><th>${s("mbAddress")}</th>
          ${n.form.function>=3?r`<th style="text-align:right">${s("mbUnsigned")}</th><th style="text-align:right">${s("mbSigned")}</th><th style="text-align:right">Hex</th>`:r`<th style="text-align:right">${s("mbBit")}</th>`}</tr></thead>
          <tbody>${n.values.map((d,u)=>r`<tr><td class="mono">${n.form.address+u}</td>
            ${n.form.function>=3?r`<td style="text-align:right">${d}</td><td style="text-align:right">${a(d)}</td><td class="mono" style="text-align:right">${l(d)}</td>`:r`<td style="text-align:right">${d}</td>`}</tr>`)}</tbody></table></div>
          <p class="hint">${s("mbReadTime",{ms:n.time_ms})}</p>`:r`<div class="note warn">${c(n.exception)}</div>`:""}
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:12px"><div><b style="font-weight:500">${s("mbScanTitle")}</b><p class="hint">${s("mbScanSub")}</p></div></div>
      <div class="grid4">
        ${this._num(this.scanForm,"first",s("mbFirst"),"scanForm")}
        ${this._num(this.scanForm,"last",s("mbLast"),"scanForm")}
        ${this._num(this.scanForm,"timeout_ms",s("mbScanTimeout"),"scanForm")}
        <div class="fld"><span class="lbl">&nbsp;</span><button class="btn btn-s" ?disabled=${!e.enabled||i&&i.state==="running"} @click=${this._mbScan}>${s("start")}</button></div>
      </div>
      ${i?r`${i.state==="running"?r`<p class="hint" role="status">${s("detecting",{d:i.done,t:i.total})}</p>`:""}
        ${i.state==="failed"?r`<div class="note bad">${s("error")}: ${i.error}</div>`:""}
        ${i.results.length?r`<div style="display:flex;flex-wrap:wrap;gap:6px">${i.results.map(d=>r`<button class="chip ${d.exception===null?"ok":"info"}" style="cursor:pointer;border:none"
          title=${d.exception===null?"":c(d.exception)} @click=${()=>{this.mbForm={...this.mbForm,unit:d.unit}}}>Unit ${d.unit}</button>`)}</div>`:i.state==="done"?r`<p class="hint">${s("mbScanNone")}</p>`:""}`:""}
    </section>`}_tools(e){let t=this.meter,n=this.job,i=n&&n.state==="done"?n.results.filter(c=>c.score>=.6):[],a=c=>`${c.baud} ${c.data_bits}${c.parity.toUpperCase()}${c.stop_bits}`,l=c=>typeof c.value=="number"&&c.unit==="Wh"?`${(c.value/1e3).toLocaleString(void 0,{maximumFractionDigits:3})} kWh`:`${c.value} ${c.unit}`;return r`<section class="card" aria-labelledby="t-tools">
      <h2 id="t-tools">${s("tools")}</h2>
      <div class="row"><div><b style="font-weight:500">${s("meterCheck")}</b><p class="hint">${s("meterCheckSub")}</p></div>
        <button class="btn btn-s" @click=${this._checkMeter}>${s("meterCheck")}</button></div>
      ${t?t.bytes?r`<div class="well" style="display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;flex-wrap:wrap;gap:6px"><span class="chip ${t.protocol==="unknown"?"warn":"info"}">${s(`proto_${t.protocol}`)}</span>
            ${t.telegrams?r`<span class="chip">${s("telegrams",{n:t.telegrams})}</span>
              <span class="chip ${t.valid===t.telegrams?"ok":"warn"}">${s(t.protocol==="sml"?"validCrc":"validD0",{n:t.valid})}</span>`:""}</div>
          ${t.readings.length?r`<table><tbody>${t.readings.slice(0,12).map(c=>r`<tr><td class="mono" style="font-size:12px">${c.obis}</td><td>${c.name?s(`obis_${c.obis}`):""}</td><td style="text-align:right">${l(c)}</td></tr>`)}</tbody></table>`:""}
        </div>`:r`<p class="hint">${s("noData30")}</p>`:""}
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:12px"><div><b style="font-weight:500">${s("baudDetect")}</b><p class="hint">${s("baudDetectSub")}</p></div>
        <button class="btn btn-s" ?disabled=${n&&n.state==="running"} @click=${this._detect}>${s("baudDetect")}</button></div>
      ${n?n.state==="running"?r`<p class="hint" role="status">${s("detecting",{d:n.done,t:n.total||"\u2026"})}</p>`:n.state==="failed"?r`<div class="note bad">${s("error")}: ${n.error}</div>`:i.length?r`<div class="note ok"><b>${s("detected",{b:i[0].baud,f:a(i[0]).split(" ")[1]})}</b> · ${s(`proto_${i[0].protocol}`)}</div>
          <div class="hint">${s("candidates")}:</div>
          ${i.slice(0,3).map(c=>r`<div class="row well"><span class="mono">${a(c)}</span><span class="hint">${s("score")} ${Math.round(c.score*100)} %</span>
            <button class="btn btn-g" @click=${()=>this._useCandidate(e,c)}>${s("applyThis")}</button></div>`)}`:r`<div class="note warn">${s("noDetect")}</div>`:""}
    </section>`}async _copy(e,t){await ye(t)&&(this.copied=e,setTimeout(()=>{this.copied===e&&(this.copied="")},2e3))}_live(e){let t=this.chunks.slice(-120).reverse();return r`<section class="card" aria-labelledby="t-live">
      <div class="row"><div><h2 id="t-live">${s("live")}</h2><p class="hint">${s(e?"liveSubMb":"liveSub")}</p></div>
        <div style="display:flex;gap:4px">
          ${e?"":r`<button class="btn btn-g" aria-pressed=${this.ascii?"true":"false"} @click=${()=>{this.ascii=!this.ascii}}>${this.ascii?s("hexOnly"):s("hexAscii")}</button>`}
          <button class="btn btn-g" @click=${()=>{this.paused=!this.paused}}>${this.paused?s("resume"):s("pause")}</button>
        </div></div>
      ${t.length?r`<div class="code live" style="padding:8px 4px"><table><tbody>
        ${t.map(n=>r`<tr>
          <td style="color:#8f9ba8">${new Date(n.ts*1e3).toLocaleTimeString(void 0,{hour12:!1})}.${String(Math.floor(n.ts*1e3)%1e3).padStart(3,"0")}</td>
          <td><span class="dir ${n.direction==="rx"?"rx":n.direction==="tx"?"tx":"mark"}">${n.direction.toUpperCase()}</span></td>
          ${n.info?r`<td style="color:#9fb3c8">${n.info}</td>`:""}
          <td>${n.direction==="open"||n.direction==="close"?n.text:n.hex}</td>
          ${!n.info&&this.ascii&&n.hex?r`<td style="color:#9fb3c8">${n.text.replace(/[^\x20-\x7e]/g,".")}</td>`:""}
        </tr>`)}</tbody></table></div>`:r`<div class="well hint" style="font-size:14px">${s(e?"liveEmptyMb":"liveEmpty")}</div>`}
    </section>`}_haSnippet(e){let t=e.addresses.find(i=>i.target==="ha");if(!t||!t.reachable)return"";let n=`modbus:
  - name: ${JSON.stringify(e.name)}
    type: tcp
    host: ${t.host}
    port: ${e.port}
    # ${s("haSnippetComment")}`;return r`<section class="card" aria-labelledby="t-ha">
      <div class="row"><div><h2 id="t-ha">${s("haSnippet")}</h2><p class="hint" style="margin-top:4px">${s("haSnippetSub",{h:t.host,p:e.port})}</p></div>
        <button class="btn btn-g" @click=${()=>this._copy("ha-yaml",n)}>${this.copied==="ha-yaml"?s("copied"):s("copy")}</button></div>
      <div class="code">${n}</div>
    </section>`}_modbusCard(e){let t=e.reachable===!0?["mbReachable","ok"]:e.reachable===!1?["mbUnreachable","bad"]:["mbUnknown",""],n=[["mbRequests",e.requests],["mbAnswered",e.answered],["mbExceptions",e.exceptions],["mbTimeouts",e.timeouts],["mbErrors",e.errors],["mbQueue",`${e.queue??0} / ${e.queue_max??0}`]];return e.blocked&&n.push(["mbBlocked",e.blocked]),e.cached&&n.push(["mbCached",e.cached]),e.probes&&n.push(["mbProbes",e.probes]),r`<section class="card" aria-labelledby="t-mb">
      <div class="row"><h2 id="t-mb">${s("mbStats")}</h2><span class="chip ${t[1]}"><span class="dot"></span>${s(t[0])}</span></div>
      <div class="counters">${n.map(([i,a])=>r`<div class="well"><span class="hint">${s(i)}</span>
        <b style=${(i==="mbTimeouts"||i==="mbErrors")&&a?"color:var(--warn)":""}>${a??0}</b></div>`)}</div>
      <div class="row hint"><span>${s("mbTime")}</span><span>${e.answered?s("mbTimeVal",{a:e.time_avg_ms,m:e.time_max_ms}):"\u2013"}</span></div>
      <div class="row hint"><span>${s("mbLastAnswer")}</span><span>${e.last_answer?q(e.last_answer):s("never")}</span></div>
      ${e.listen_error?r`<div class="note bad">${s("mbListenError",{e:e.listen_error})}</div>`:""}
      ${e.last_error?r`<div class="note ${e.reachable===!1?"bad":"warn"}">${s("mbLastError")}: ${e.last_error}${e.last_error_at?` \xB7 ${w(e.last_error_at,!0,!0)}`:""}</div>`:""}
    </section>`}_sparkline(){let e=this._samples.length>1?this._samples:[0,0],t=Math.max(...e,1),n=300/(e.length-1),i=e.map((a,l)=>`${(l*n).toFixed(1)},${(66-a/t*56).toFixed(1)}`);return r`<svg viewBox="0 0 300 70" width="100%" height="70" role="img" aria-label=${s("dataFromDevice")}>
      ${ue`<path d="M0,70 L${i.join(" L")} L300,70 Z" fill="var(--accent-soft)"></path>
      <path d="M${i.join(" L")}" fill="none" stroke="var(--accent)" stroke-width="2"></path>`}</svg>`}render(){let e=this.state,t=this.connection(this.connectionId);if(!t)return r`<p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a></p><p>${s("error")}</p>`;let[n,i]=V(t,e.ser2net_running),a=this.events.filter(p=>p.connection===t.id).slice(-6).reverse(),l=t.line_errors,c=t.usb,d=t.kind==="modbus",u=t.modbus||{};return r`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${t.name}</p>
      <div class="head" style="margin-top:12px">
        <div class="row" style="justify-content:flex-start"><h1>${t.name}</h1>
          <span class="chip ${i}"><span class="dot"></span>${s(n)}</span>
          ${t.kept_open?r`<span class="chip info">${s("keptOpen")}</span>`:""}</div>
        <div class="row">
          <a class="btn btn-s" href="#/trace/${t.id}">${s("navTrace")}</a>
          <a class="btn btn-s" href="#/edit/${t.id}">${s("edit")}</a>
          ${$e(t.enabled,s("switchLabel",{name:t.name}),p=>this._enable(t,p),e.source==="custom"&&!d)}
        </div>
      </div>
      <div class="cols">
        <div class="main-col">
          ${this._live(d)}
          ${d?this._modbusTools(t):this.state.source==="custom"?"":this._tools(t)}
          <section class="card" aria-labelledby="t-clients">
            <div class="row"><h2 id="t-clients">${s("clients")}</h2><span class="hint" style="font-size:13px">${s("clientsOf",{n:t.clients.length,m:t.max_clients})}</span></div>
            ${t.clients.length&&d?r`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${s("clientTh")}</th><th>${s("sinceTh")}</th><th style="text-align:right">${s("mbRequests")}</th><th style="text-align:right">${s("mbFailed")}</th><th style="text-align:right">${s("mbBlocked")}</th></tr></thead>
              <tbody>${t.clients.map(p=>r`<tr><td class="mono" style="font-size:12px">${p.address}</td><td>${p.since?w(p.since):"\u2013"}</td>
                <td style="text-align:right">${p.requests}</td><td style="text-align:right;${p.failed?"color:var(--warn)":""}">${p.failed}</td><td style="text-align:right">${p.blocked}</td></tr>`)}</tbody></table></div>`:t.clients.length?r`<div class="scroll"><table style="min-width:520px"><thead><tr>
              <th>${s("clientTh")}</th><th>${s("sinceTh")}</th><th style="text-align:right">${s("toClient")}</th><th style="text-align:right">${s("fromClient")}</th><th style="text-align:right">${s("queued")}</th></tr></thead>
              <tbody>${t.clients.map(p=>r`<tr>
                <td class="mono" style="font-size:12px">${p.address} ${p.stuck?r`<span class="chip bad">${s("stuck",{a:""})}</span>`:""}</td>
                <td>${p.since?w(p.since):"\u2013"}</td><td style="text-align:right">${E(p.bytes_to_client)}</td>
                <td style="text-align:right">${E(p.bytes_from_client)}</td><td style="text-align:right">${E(p.queued)}</td></tr>`)}</tbody></table></div>`:r`<p class="hint" style="font-size:14px">${s("noClients")}</p>`}
          </section>
          ${d&&(u.units||[]).length?r`<section class="card" aria-labelledby="t-units">
            <div class="row"><h2 id="t-units">${s("mbUnits")}</h2><span class="hint" style="font-size:13px">${s("mbUnitsSub")}</span></div>
            <div class="scroll"><table style="min-width:520px"><thead><tr><th>${s("mbUnit")}</th><th style="text-align:right">${s("mbRequests")}</th>
              <th style="text-align:right">${s("mbExceptions")}</th><th style="text-align:right">${s("mbFailed")}</th><th style="text-align:right">${s("mbTimeShort")}</th><th>${s("mbLastAnswer")}</th></tr></thead>
              <tbody>${u.units.map(p=>r`<tr><td class="mono">${p.unit}</td><td style="text-align:right">${p.requests}</td>
                <td style="text-align:right">${p.exceptions}</td><td style="text-align:right;${p.failed?"color:var(--warn)":""}">${p.failed}</td>
                <td style="text-align:right">${p.answered?`${p.time_avg_ms} ms`:"\u2013"}</td><td>${p.last_answer?q(p.last_answer):s("never")}</td></tr>`)}</tbody></table></div>
          </section>`:""}
          ${d?this._haSnippet(t):""}
          <section class="card" aria-labelledby="t-addr">

            <h2 id="t-addr">${s("addresses")}</h2>
            ${t.addresses.map(p=>r`<div class="well row">
              <div style="min-width:0"><div class="hint">${s(`target_${p.target}`)}</div>
                ${p.reachable?Object.entries(p.urls).map(([b,x])=>r`<div class="row" style="justify-content:flex-start;gap:4px">
                  <span class="mono" style="font-size:13px;overflow-wrap:anywhere">${x}</span>
                  <button class="btn btn-g" style="min-height:32px" @click=${()=>this._copy(`${p.target}${b}`,x)}>${this.copied===`${p.target}${b}`?s("copied"):s("copy")}</button></div>`):r`<div class="hint">${p.host?s("notReachable"):s("lanUnknown")}</div>`}
              </div></div>`)}
          </section>
          <section class="card" aria-labelledby="t-conf">
            <div class="row"><h2 id="t-conf">${s("configuration")}</h2><a href="#/edit/${t.id}" style="font-size:13px">${s("edit")}</a></div>
            ${d?r`<div class="kv">
              <span>${s("mbLink")}</span><span>${s(`link_${t.link}`)}</span>
              <span>${s("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${I(t)}${t.link==="rtu"?` \xB7 ${D(t)}`:""}</span>
              ${t.link==="rtu"?r`<span>${s("resolved")}</span><span class="mono" style="font-size:13px">${t.tty||"\u2013"}</span>`:""}
              ${t.device_connections>1?r`<span>${s("mbLinksShort")}</span><span>${s("mbLinksVal",{o:u.links_open??0,n:t.device_connections})}</span>`:""}
              <span>${s("mbProxy")}</span><span>${s("mbConf",{ms:t.request_timeout_ms,n:t.retries})}
${t.request_gap_ms?` \xB7 ${s("mbGapShort",{ms:t.request_gap_ms})}`:""}</span>
              <span>${s("network")}</span><span>Modbus TCP · Port ${t.port} · ${t.bind||s(`listen_${e.settings.listen}`)}</span>
              ${t.cache_ms?r`<span>${s("mbCacheShort")}</span><span>${t.cache_ms} ms</span>`:""}
              ${t.unit_map?r`<span>${s("mbUnitMapShort")}</span><span class="mono">${t.unit_map}</span>`:""}

              ${t.probe_seconds?r`<span>${s("mbProbe")}</span><span>${s("mbProbeVal",{s:t.probe_seconds,u:t.probe_unit,f:t.probe_function,a:t.probe_address})}</span>`:""}

              <span>${s("mbWrite")}</span>
<span>${s(`wa_${t.write_access}`)}${t.write_access==="listed"?r` · <span class="mono">${t.write_clients}</span>`:""}</span>

            </div>`:r`<div class="kv">
              <span>${s("device")}</span><span class="mono" style="font-size:13px;overflow-wrap:anywhere">${t.device}</span>
              <span>${s("resolved")}</span><span class="mono" style="font-size:13px">${t.tty||"\u2013"}</span>
              ${c?r`<span>${s("usb")}</span><span>${[c.manufacturer,c.product].filter(Boolean).join(" \xB7 ")||`${c.vendor_id}:${c.product_id}`}${c.serial?` \xB7 ${s("serialNo")} ${c.serial}`:""}${c.driver?` \xB7 ${c.driver}`:""}</span>`:""}
              <span>${s("interface")}</span><span>${D(t)}${t.rtscts?" \xB7 RTS/CTS":""}${t.xonxoff?" \xB7 XON/XOFF":""}${t.local?" \xB7 local":""}</span>
              <span>${s("network")}</span><span>${t.mode} · Port ${t.port} · ${t.bind||s(`listen_${e.settings.listen}`)}</span>
            </div>`}
          </section>
        </div>
        <aside class="side-col">
          ${d?this._modbusCard(u):r`<section class="card" aria-labelledby="t-line">
            <div class="row"><h2 id="t-line">${s("line")}</h2>
              ${l&&!Object.values(l).some(Boolean)?r`<span class="chip ok">${s("noLineErrors")}</span>`:""}</div>
            ${l?r`<div class="counters">
              ${[["frame",l.frame],["parity",l.parity],["overrun",l.overrun],["brk",l.break],["bufOverrun",l.buffer_overrun]].map(([p,b])=>r`<div class="well"><span class="hint">${s(p)}</span><b style=${b?"color:var(--warn)":""}>${b}</b></div>`)}</div>`:r`<p class="hint">${t.line_errors===null&&t.clients.length?s("lineUnsupported"):s("lineClosed")}</p>`}
          </section>`}
          <section class="card" aria-labelledby="t-rate">
            <div class="row"><h2 id="t-rate">${s("dataFromDevice")}</h2><b style="font-size:18px;font-weight:500">${ve(t.rate_from_device)}</b></div>
            ${this._sparkline()}
            <div class="row hint"><span>${s("lastData")}: ${t.last_data?q(t.last_data):s("never")}</span><span>${E(t.bytes_from_device)}</span></div>
          </section>
          <section class="card" aria-labelledby="t-recent">
            <div class="row"><h2 id="t-recent">${s("recent")}</h2><a href="#/events" style="font-size:13px">${s("allEvents")}</a></div>
            <ol>${a.map(p=>r`<li><span class="dot" style="color:${p.level==="warning"?"var(--warn)":p.level==="error"?"var(--bad)":"var(--ok)"}"></span>
              <div><div>${B(p)}${p.count>1?r` <span class="chip">${s("summed",{n:p.count})}</span>`:""}</div><div class="hint">${w(p.ts)}</div></div></li>`)}</ol>
          </section>
        </aside>
      </div>`}};m(K,"properties",{state:{attribute:!1},events:{attribute:!1},connectionId:{},chunks:{state:!0},paused:{state:!0},ascii:{state:!0},copied:{state:!0},meter:{state:!0},job:{state:!0},mbForm:{state:!0},mbResult:{state:!0},scan:{state:!0},scanForm:{state:!0}}),m(K,"styles",[...f.styles,v`
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
    .grid4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; }

  `]);var le={name:"",device:"",port:3333,enabled:!0,template:"generic",baud:9600,data_bits:8,parity:"n",stop_bits:1,mode:"raw",max_clients:1,local:!0,rtscts:!1,xonxoff:!1,hangup_when_done:!1,nobreak:!1,dtr:"",rts:"",rs485:"",low_latency:!1,timeout:0,kickolduser:!1,chardelay:!0,remaddr:"",banner:"",openstr:"",closestr:"",connector_retry_time:0,nodelay:!1,bind:"",extra:[],keep_open:!1,stuck_disconnect:!1,trace:"off",notify_missing:!0,notify_no_client:!1,silence_minutes:0,kind:"serial",link:"tcp",host:"",host_port:502,request_timeout_ms:3e3,connect_delay_ms:0,retries:1,request_gap_ms:0,write_access:"all",write_clients:"",cache_ms:0,unit_map:"",device_connections:1,probe_seconds:0,probe_unit:1,probe_function:3,probe_address:0},Bt={kind:"modbus",template:"modbus",link:"tcp",max_clients:10,mode:"raw",keep_open:!1,stuck_disconnect:!1,silence_minutes:0,write_access:"listed",write_clients:"127.0.0.1, 172.30.32.0/23"},qt=["tcp","rtu","rtu_tcp"],dt="127.0.0.1, 172.30.32.0/23",_e={ehz_sml:{baud:9600,data_bits:8,parity:"n",stop_bits:1,max_clients:5,chardelay:!0,nodelay:!1},ehz_d0:{baud:9600,data_bits:7,parity:"e",stop_bits:1,max_clients:5,chardelay:!0,nodelay:!1},zwave:{baud:115200,data_bits:8,parity:"n",stop_bits:1,max_clients:2,chardelay:!1,nodelay:!0,remaddr:dt},generic:{baud:9600,data_bits:8,parity:"n",stop_bits:1,max_clients:1,chardelay:!0,nodelay:!1}},It=[300,1200,2400,4800,9600,19200,38400,57600,115200,230400,460800,921600],ot=["kickolduser","low_latency"],lt=["rtscts","xonxoff","hangup_when_done","nobreak","low_latency","kickolduser","nodelay","keep_open","stuck_disconnect"],Vt=o=>o.map(([e,t])=>`${e}: ${t}`).join(`
`),jt=o=>o.split(`
`).map(e=>e.trim()).filter(Boolean).map(e=>{let t=e.indexOf(":");return t<0?[e,""]:[e.slice(0,t).trim(),e.slice(t+1).trim()]}),ct=o=>Object.fromEntries(Object.entries(o||{}).map(([e,t])=>[e.replace(/^connections\.\d+\./,""),t])),Z=class extends f{willUpdate(e){(e.has("connectionId")||this.draft===void 0&&this.state)&&this._load()}_load(){let e=this.connection(this.connectionId);if(e){let t={};for(let n of[...Object.keys(le),"id"])t[n]=e[n];this.draft=t}else this.draft={...le,...this._fresh("serial")};this.extraRaw=Vt(this.draft.extra),this.otherDevice=!!this.draft.device&&!this.state.devices.some(t=>t.stable===this.draft.device||t.by_id.includes(this.draft.device)||t.by_path.includes(this.draft.device)),this.errors={},this.touched=new Set(e?Object.keys(le):[]),this.advanced=(this.draft.kind==="modbus"?ot:lt).some(t=>this.draft[t])||!!(this.draft.unit_map||this.draft.remaddr||this.draft.bind||this.draft.extra.length||this.draft.timeout),this._preview()}_fresh(e){let t=this.state.connections.map(a=>a.port),n=this.state.devices.find(a=>!a.used_by);if(e==="modbus"){let a=502;for(;t.includes(a);)a++;return{...Bt,port:a,device:""}}let i=t.filter(a=>a>=1024);return{kind:"serial",template:"generic",..._e.generic,port:i.length?Math.max(...i)+1:3333,device:n?n.stable:""}}_kind(e){e!==this.draft.kind&&(this.otherDevice=!1,this._set(e==="modbus"?{...this._fresh("modbus")}:{...le,...this._fresh("serial"),name:this.draft.name,enabled:this.draft.enabled}))}_set(e){this.draft={...this.draft,...e},this.touched=new Set([...this.touched,...Object.keys(e)]),clearTimeout(this._pt),this._pt=setTimeout(()=>this._preview(),300)}async _preview(){try{let e=await h("api/preview",{method:"POST",body:{connection:this.draft}});this.yaml=e.yaml,this.errors=ct(e.errors),this.warnings=e.warnings||{}}catch{}}async _save(e){e.preventDefault(),this.saving=!0,this.touched=new Set(Object.keys(le));try{let t=await U(this.draft),n=t.rebuilt.length?s("savedRebuilt",{n:t.rebuilt.join(", ")}):s("saved");t.disconnected.length&&(n+=s("savedReconnect",{n:t.disconnected.join(", ")})),this.toast(n),this.refresh(),oe(`#/connection/${this.draft.id||t.id}`)}catch(t){this.errors=ct(t.data.errors),this.toast(t.data.errors?s("errorsBelow"):`${s("error")}: ${t.message}`)}finally{this.saving=!1}}async _delete(){if(await S(this,s("deleteConfirm",{n:this.draft.name}),s("delete")))try{await h(`api/connections/${this.draft.id}`,{method:"DELETE"}),this.refresh(),oe("#/connections")}catch(e){this.toast(`${s("error")}: ${e.message}`)}}_shown(){return Object.fromEntries(Object.entries(this.errors).filter(([e])=>this.touched.has(e)))}_err(e){let t=this._shown();if(t[e])return r`<span class="err" id="e-${e}">${N(t[e])}</span>`;let n=(this.warnings||{})[e];return n?r`<span class="hint" id="e-${e}" style="color:var(--warn)">${s("portWarn",{w:N(n)})}</span>`:""}_input(e,t,{type:n="text",hint:i="",mono:a=!1,number:l=!1}={}){let c=this.draft[e];return r`<label class="fld"><span class="lbl">${t}</span>
      <input class="inp ${a?"mono":""}" type=${n} .value=${String(c??"")} inputmode=${l?"numeric":"text"}
        aria-invalid=${this._shown()[e]?"true":"false"} aria-describedby="e-${e}"
        @input=${d=>this._set({[e]:l?Number(d.target.value||0):d.target.value})}>
      ${this._err(e)}${i?r`<span class="hint">${i}</span>`:""}</label>`}_check(e,t=!1){let n=!t&&e!=="keep_open"&&e!=="stuck_disconnect"&&!e.startsWith("notify");return r`<label class="chk"><input type="checkbox" .checked=${!!this.draft[e]} @change=${i=>this._set({[e]:i.target.checked})}>
      <span>${s(`o_${e}`)}${n?r`<br><span class="hint mono">${e.replace(/_/g,"-")}</span>`:""}</span></label>`}_devicePicker(e){let t=this.draft,n=this.state.devices;return r`<label class="fld"><span class="lbl">${s("devicePick")}</span>
        <select class="inp" aria-invalid=${this._shown().device?"true":"false"} @change=${i=>{if(i.target.value==="__other"){this.otherDevice=!0;return}this.otherDevice=!1,this._set({device:i.target.value})}}>
          ${t.device?"":r`<option value="" selected>–</option>`}
          ${n.map(i=>r`<option value=${i.stable} ?selected=${!this.otherDevice&&e===i}>${this._deviceLabel(i)}</option>`)}
          <option value="__other" ?selected=${this.otherDevice}>${s("deviceOther")}</option>
        </select>
        ${this.otherDevice?r`<input class="inp mono" .value=${t.device} placeholder="/dev/serial/by-id/…" @input=${i=>this._set({device:i.target.value})}>`:r`<span class="hint mono" style="overflow-wrap:anywhere">${t.device}</span>`}
        ${this._err("device")}</label>
      ${e&&e.ambiguous?r`<div class="note warn" role="note">${s("ambiguous")}</div>`:""}`}_serialFormat(){let e=this.draft;return r`<label class="fld"><span class="lbl">${s("baud")}</span><select class="inp" @change=${t=>this._set({baud:Number(t.target.value)})}>
        ${[...new Set([...It,e.baud])].sort((t,n)=>t-n).map(t=>r`<option value=${t} ?selected=${t===e.baud}>${t}</option>`)}</select>${this._err("baud")}</label>
      <label class="fld"><span class="lbl">${s("dataBits")} · ${s("parityF")} · ${s("stopBits")}</span>
        <div style="display:flex;gap:6px">
          <select class="inp" aria-label=${s("dataBits")} @change=${t=>this._set({data_bits:Number(t.target.value)})}>${[5,6,7,8].map(t=>r`<option ?selected=${t===e.data_bits}>${t}</option>`)}</select>
          <select class="inp" aria-label=${s("parityF")} @change=${t=>this._set({parity:t.target.value})}>${["n","e","o","m","s"].map(t=>r`<option value=${t} ?selected=${t===e.parity}>${t.toUpperCase()}</option>`)}</select>
          <select class="inp" aria-label=${s("stopBits")} @change=${t=>this._set({stop_bits:Number(t.target.value)})}>${[1,2].map(t=>r`<option ?selected=${t===e.stop_bits}>${t}</option>`)}</select>
        </div></label>`}_modbusSections(e){let t=this.draft,n=ot.filter(i=>t[i]).length+["remaddr","bind","timeout","unit_map"].filter(i=>t[i]).length;return r`
      <section class="card" aria-labelledby="t-mdev">
        <h2 id="t-mdev">${s("mbDevice")}</h2>
        <div class="fld"><span class="lbl" id="l-link">${s("mbLink")}</span>
          <div class="seg" role="group" aria-labelledby="l-link">${qt.map(i=>r`<button type="button" aria-pressed=${t.link===i?"true":"false"}
            @click=${()=>this._set(i==="rtu"?{link:i,device_connections:1,device:t.device||(this.state.devices.find(a=>!a.used_by)||{}).stable||""}:{link:i})}>${s(`link_${i}`)}</button>`)}</div>

          <span class="hint">${s(`linksub_${t.link}`)}</span></div>
        ${t.link==="rtu"?r`${this._devicePicker(e)}<div class="grid2">${this._serialFormat()}</div>`:r`<div class="grid2">
          ${this._input("host",s("mbHost"),{mono:!0,hint:s("mbHostHint")})}${this._input("host_port",s("mbHostPort"),{number:!0})}</div>`}
      </section>

      <section class="card" aria-labelledby="t-proxy">
        <h2 id="t-proxy">${s("mbProxy")}</h2>
        <div class="grid2">
          ${this._input("port",s("mbPort"),{number:!0,hint:s("mbPortHint")})}
          ${this._input("max_clients",s("maxClients"),{number:!0,hint:s("mbClientsHint")})}
          ${this._input("request_timeout_ms",s("mbTimeout"),{number:!0,hint:s("mbTimeoutHint")})}
          ${this._input("retries",s("mbRetries"),{number:!0})}
          ${this._input("connect_delay_ms",s("mbConnectDelay"),{number:!0,hint:t.link==="rtu"?"":s("mbConnectDelayHint")})}
          ${this._input("request_gap_ms",s("mbGap"),{number:!0,hint:s("mbGapHint")})}
          ${this._input("cache_ms",s("mbCache"),{number:!0,hint:s("mbCacheHint")})}
          ${t.link==="rtu"?"":this._input("device_connections",s("mbLinks"),{number:!0,hint:s("mbLinksHint")})}

        </div>
      </section>

      <section class="card" aria-labelledby="t-probe">
        <div><h2 id="t-probe">${s("mbProbe")}</h2><p class="hint" style="margin-top:4px">${s("mbProbeSub")}</p></div>
        <div class="grid2">
          ${this._input("probe_seconds",s("mbProbeSeconds"),{number:!0})}
          ${t.probe_seconds?r`${this._input("probe_unit",s("mbUnit"),{number:!0})}
            <label class="fld"><span class="lbl">${s("mbFunction")}</span><select class="inp" @change=${i=>this._set({probe_function:Number(i.target.value)})}>
              ${[3,4].map(i=>r`<option value=${i} ?selected=${t.probe_function===i}>${s(`fc_${i}`)}</option>`)}</select></label>
            ${this._input("probe_address",s("mbAddress"),{number:!0,hint:s("mbAddressHint")})}`:""}
        </div>
      </section>

      <section class="card" aria-labelledby="t-write">

        <div><h2 id="t-write">${s("mbWrite")}</h2><p class="hint" style="margin-top:4px">${s("mbWriteSub")}</p></div>
        <div class="seg" role="group" aria-labelledby="t-write">${["all","listed","none"].map(i=>r`<button type="button" aria-pressed=${t.write_access===i?"true":"false"}
          @click=${()=>this._set({write_access:i})}>${s(`wa_${i}`)}</button>`)}</div>
        <span class="hint">${s(`wasub_${t.write_access}`)}</span>
        ${t.write_access==="listed"?this._input("write_clients",s("mbWriteClients"),{mono:!0,hint:s("mbWriteClientsHint")}):""}
      </section>

      <section class="card" aria-labelledby="t-adv">
        <button type="button" class="toggle-head" aria-expanded=${this.advanced?"true":"false"} @click=${()=>{this.advanced=!this.advanced}}>
          <span><h2 id="t-adv">${s("advanced")}</h2><span class="hint">${s("advancedSubMb")}</span></span>

          <span class="chip">${s("set",{n})} · ${this.advanced?s("closeA"):s("open")}</span></button>
        ${this.advanced?r`
          <div class="opts">${this._check("kickolduser",!0)}${t.link==="rtu"&&(e&&e.ftdi||t.low_latency)?this._check("low_latency",!0):""}</div>
          ${this._input("timeout",s("mbIdle"),{number:!0})}
          ${this._input("unit_map",s("mbUnitMap"),{mono:!0,hint:s("mbUnitMapHint")})}

          ${this._input("remaddr",s("allowed"),{mono:!0,hint:s("remaddrHint")})}
          ${this._input("bind",s("bind"),{mono:!0,hint:s("bindHint")})}`:""}
      </section>

      <section class="card" aria-labelledby="t-app">
        <h2 id="t-app">${s("appSide")}</h2>
        <div class="opts">${this._check("notify_missing")}${this._check("notify_no_client")}</div>
        <label class="fld"><span class="lbl">${s("traceMode")}</span><select class="inp" @change=${i=>this._set({trace:i.target.value})}>
          ${["off","rx","tx","both"].map(i=>r`<option value=${i} ?selected=${t.trace===i}>${s(`trmb_${i}`)}</option>`)}</select></label>
      </section>`}_modbusPreview(){let e=this.draft,t=e.link==="rtu"?`${e.device||"\u2013"} \xB7 ${e.baud} ${e.data_bits}${e.parity.toUpperCase()}${e.stop_bits}`:`${e.host||"\u2013"}:${e.host_port}`;return r`<section class="card" aria-labelledby="t-prev">
      <div><h2 id="t-prev">${s("mbPreview")}</h2><p class="hint" style="margin-top:4px">${s("mbPreviewSub")}</p></div>
      <ol class="flow">
        <li><b>${s("mbFlowClients",{n:e.max_clients})}</b><span class="hint">Modbus TCP → ${s("port")} ${e.port}</span></li>
        <li><b>${s("mbFlowQueue")}</b><span class="hint">${s("mbFlowQueueSub",{ms:e.request_timeout_ms,n:e.retries})}</span></li>
        <li><b>${s(`link_${e.link}`)}</b><span class="hint mono" style="overflow-wrap:anywhere">${t}</span></li>
      </ol>
      ${Object.keys(this._shown()).length?r`<div class="note bad">${Object.entries(this._shown()).map(([n,i])=>r`<div><span class="mono">${n}</span>: ${N(i)}</div>`)}</div>`:""}
    </section>`}_deviceLabel(e){let t=[e.manufacturer,e.product].filter(Boolean).join(" ")||e.driver||e.tty,n=e.serial?`${s("serialNo")} ${e.serial}`:s("noSerial"),i=e.used_by&&e.used_by!==this.draft.name?` (${s("usedBy",{n:e.used_by})})`:"";return`${t} \xB7 ${n} \xB7 ${e.tty}${i}`}render(){let e=this.draft;if(!e)return r`<p class="hint">${s("loading")}</p>`;let n=this.state.devices.find(l=>l.stable===e.device||l.by_id.includes(e.device)||l.by_path.includes(e.device)),i=lt.filter(l=>e[l]).length+["remaddr","bind","rs485","banner","openstr","closestr"].filter(l=>e[l]).length+(e.extra.length?1:0),a=!e.id;return r`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${a?s("newConnection"):e.name}</p>
      <h1 style="margin:12px 0 20px">${a?s("newConnection"):s("editConnection")}</h1>
      <div class="cols"><form class="main-col" @submit=${this._save} novalidate>
        ${a?r`<section class="card" aria-labelledby="t-kind">
          <div><h2 id="t-kind">${s("kind")}</h2><p class="hint" style="margin-top:4px">${s("kindSub")}</p></div>
          <div class="choices">${["serial","modbus"].map(l=>r`<button type="button" class="choice" aria-pressed=${e.kind===l?"true":"false"}
            @click=${()=>this._kind(l)}><b style="font-weight:500;display:flex;align-items:center;gap:8px">${_(l,18)}${s(`kind_${l}`)}</b><span class="hint">${s(`kindsub_${l}`)}</span></button>`)}</div>
        </section>`:""}
        ${e.kind==="modbus"?r`<section class="card" aria-labelledby="t-base">
          <h2 id="t-base">${s("basics")}</h2>
          <div class="grid2">${this._input("name",s("name"))}
            <div class="fld"><span class="lbl">${s("enabled")}</span><label class="chk" style="min-height:42px;align-items:center">
              <input type="checkbox" .checked=${e.enabled} @change=${l=>this._set({enabled:l.target.checked})}><span>${s("enabledText")}</span></label></div></div>
        </section>${this._modbusSections(n)}`:r`
        <section class="card" aria-labelledby="t-tpl">
          <div><h2 id="t-tpl">${s("template")}</h2><p class="hint" style="margin-top:4px">${s("templateSub")}</p></div>
          <div class="choices">${Object.keys(_e).map(l=>r`<button type="button" class="choice" aria-pressed=${e.template===l?"true":"false"}
            @click=${()=>this._set({template:l,..._e[l],remaddr:_e[l].remaddr??(e.remaddr===dt?"":e.remaddr)})}><b style="font-weight:500">${s(`tpl_${l}`)}</b><span class="hint">${s(`tplsub_${l}`)}</span></button>`)}</div>
        </section>

        <section class="card" aria-labelledby="t-base">
          <h2 id="t-base">${s("basics")}</h2>
          <div class="grid2">${this._input("name",s("name"))}
            <div class="fld"><span class="lbl">${s("enabled")}</span><label class="chk" style="min-height:42px;align-items:center">
              <input type="checkbox" .checked=${e.enabled} @change=${l=>this._set({enabled:l.target.checked})}><span>${s("enabledText")}</span></label></div></div>
          ${this._devicePicker(n)}
        </section>

        <section class="card" aria-labelledby="t-if">
          <h2 id="t-if">${s("ifNet")}</h2>
          <div class="grid2">
            ${this._serialFormat()}
            ${this._input("port",s("port"),{number:!0})}
            ${this._input("max_clients",s("maxClients"),{number:!0,hint:s("maxClientsHint")})}
          </div>
          <div class="fld"><span class="lbl" id="l-mode">${s("mode")}</span>
            <div class="seg" role="group" aria-labelledby="l-mode">${["raw","rfc2217","telnet"].map(l=>r`<button type="button" aria-pressed=${e.mode===l?"true":"false"} @click=${()=>this._set({mode:l})}>${l==="rfc2217"?"RFC2217":l}</button>`)}</div>
            <span class="hint">${s(`mode_${e.mode}`)}</span></div>
        </section>

        <section class="card" aria-labelledby="t-adv">
          <button type="button" class="toggle-head" aria-expanded=${this.advanced?"true":"false"} @click=${()=>{this.advanced=!this.advanced}}>
            <span><h2 id="t-adv">${s("advanced")}</h2><span class="hint">${s("advancedSub")}</span></span>
            <span class="chip">${s("set",{n:i})} · ${this.advanced?s("closeA"):s("open")}</span></button>
          ${this.advanced?r`
            <fieldset><legend>${s("serialSide")}</legend>
              <div class="opts">${["local","rtscts","xonxoff","hangup_when_done","nobreak"].map(l=>this._check(l))}
                ${n&&n.ftdi||e.low_latency?this._check("low_latency"):""}</div>
              <div class="grid2">
                ${["dtr","rts"].map(l=>r`<label class="fld"><span class="lbl">${s(l)}</span><select class="inp" @change=${c=>this._set({[l]:c.target.value})}>
                  ${[["",s("lineDefault")],["on",s("on")],["off",s("off")]].map(([c,d])=>r`<option value=${c} ?selected=${e[l]===c}>${d}</option>`)}</select></label>`)}
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
                @input=${l=>{this.extraRaw=l.target.value,this._set({extra:jt(l.target.value)})}}></textarea>
              ${this._err("extra")}<span class="hint">${s("extraHint")}</span></label>`:""}
        </section>

        <section class="card" aria-labelledby="t-app">
          <h2 id="t-app">${s("appSide")}</h2>
          <div class="opts">${this._check("keep_open")}${this._check("stuck_disconnect")}${this._check("notify_missing")}${this._check("notify_no_client")}</div>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("traceMode")}</span><select class="inp" @change=${l=>this._set({trace:l.target.value})}>
              ${["off","rx","tx","both"].map(l=>r`<option value=${l} ?selected=${e.trace===l}>${s(`tr_${l}`)}</option>`)}</select></label>
            ${this._input("silence_minutes",s("silence"),{number:!0})}
          </div>
        </section>`}

        <div class="actions">
          <span class="hint" style="display:flex;align-items:center;gap:8px">${_("info",16)}${s("saveHint")}</span>
          <div style="display:flex;gap:8px">
            ${a?"":r`<button type="button" class="btn btn-d" @click=${this._delete}>${s("delete")}</button>`}
            <a class="btn btn-g" href=${a?"#/connections":`#/connection/${e.id}`}>${s("cancel")}</a>
            <button type="submit" class="btn btn-p" ?disabled=${this.saving}>${s("save")}</button>
          </div>
        </div>
      </form>

      <aside class="side-col">
        ${e.kind==="modbus"?this._modbusPreview():r`<section class="card" aria-labelledby="t-prev">
          <div><h2 id="t-prev">${s("preview")}</h2><p class="hint" style="margin-top:4px">${s("previewSub")}</p></div>
          <div class="code">${this.yaml||"\u2026"}</div>
          ${Object.keys(this._shown()).length?r`<div class="note bad">${Object.entries(this._shown()).map(([l,c])=>r`<div><span class="mono">${l}</span>: ${N(c)}</div>`)}</div>`:""}
        </section>`}
      </aside></div>`}};m(Z,"properties",{state:{attribute:!1},connectionId:{},draft:{state:!0},errors:{state:!0},yaml:{state:!0},advanced:{state:!0},otherDevice:{state:!0},saving:{state:!0},extraRaw:{state:!0},touched:{state:!0},warnings:{state:!0}}),m(Z,"styles",[...f.styles,v`
    form { display: contents; }
    fieldset { border: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
    legend { padding: 0; margin-bottom: 8px; font-size: 13px; font-weight: 500; }
    .opts { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 6px 16px; }
    .toggle-head { display: flex; align-items: center; justify-content: space-between; width: 100%; background: none; border: none; padding: 0;
      min-height: 44px; cursor: pointer; font: inherit; color: inherit; text-align: left; }
    .flow { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
    .flow li { display: flex; flex-direction: column; gap: 2px; padding: 10px 12px; border-radius: 12px; background: var(--surface-2); }
    .flow li + li::before { content: "↓"; color: var(--muted); margin: -4px 0 2px; }
    .actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  `]);var Gt=["info","warning","error","debug"],Q=class extends f{constructor(){super(),this.tab="live",this.conn="",this.query="",this.levels=new Set(["info","warning","error"]),this.paused=null}async _loadHistory(){let e=this.state.settings.history_days,t=Date.now()/1e3-e*86400;try{[this.stats,this.history]=await Promise.all([h(`api/stats?days=${Math.min(e,30)}`),h(`api/history?since=${t}&limit=2000${this.conn?`&connection=${this.conn}`:""}`)])}catch(n){this.toast(`${s("error")}: ${n.message}`)}}_filtered(e){let t=this.query.trim().toLowerCase();return e.filter(n=>this.levels.has(n.level)&&(!this.conn||n.connection===this.conn)&&(!t||`${n.name} ${B(n)}`.toLowerCase().includes(t)))}_live(){let e=this.paused||this.events,t=this._filtered(e).slice(-500).reverse(),n={info:"info",warning:"warn",error:"bad",debug:""};return r`<section class="card" style="padding:0;gap:0;overflow:hidden" aria-label=${s("tabLive")}>
      <div class="row" style="padding:12px 16px;border-bottom:1px solid var(--line)">
        <span class="hint" style="font-size:13px;display:flex;align-items:center;gap:8px"><span class="dot" style="color:${this.paused?"var(--muted)":"var(--ok)"}"></span>
          ${this.paused?s("paused"):s("liveState")} · ${s("entries",{n:t.length})}</span>
        <button class="btn btn-g" @click=${()=>{this.paused=this.paused?null:[...this.events]}}>${this.paused?s("resume"):s("pause")}</button></div>
      <div class="log" role="log">${t.map(i=>r`<div class="line">
        <span class="mono hint">${w(i.ts,!0,!0)}</span><span class="chip ${n[i.level]}" style="justify-content:center">${s(`lv_${i.level}`)}</span>
        <span style="overflow-wrap:anywhere"><b style="font-weight:500">[${i.name}]</b> ${B(i)}${i.count>1?r` <span class="chip">${s("summed",{n:i.count})}</span>`:""}</span></div>`)}
        ${t.length?"":r`<p class="hint" style="padding:32px 16px;text-align:center;font-size:14px">${s("noEntries")}</p>`}</div>
    </section>`}_historyView(){if(!this.stats||!this.history)return r`<p class="hint">${s("loading")}</p>`;let e=this.stats.days,t=this.state.connections.filter(a=>!this.conn||a.id===this.conn),n=new Map;for(let a of this._filtered(this.history)){let l=new Date(a.ts*1e3).toDateString();n.has(l)||n.set(l,[]),n.get(l).push(a)}let i=a=>{let l=new Date().toDateString(),c=new Date(Date.now()-864e5).toDateString();return a===l?s("today"):a===c?s("yesterday"):new Date(a).toLocaleDateString($,{weekday:"short",day:"2-digit",month:"2-digit"})};return r`
      <div class="stats">${t.map(a=>{let l=this.stats.connections[a.id]||{drops:0,availability:1,per_day:Array(e).fill(0)},c=Math.max(...l.per_day,1);return r`<section class="card" aria-label=${a.name} style="gap:10px">
          <div class="row"><b style="font-weight:500">${a.name}</b><span class="chip ${l.drops?"warn":"ok"}">${l.drops?s("unstable",{n:l.drops}):s("stable")}</span></div>
          <div style="display:flex;gap:20px">
            <div><div class="hint">${s("drops",{d:e})}</div><div style="font-size:22px;font-weight:500">${l.drops}</div></div>
            <div><div class="hint">${s("availability")}</div><div style="font-size:22px;font-weight:500">${(l.availability*100).toLocaleString($,{maximumFractionDigits:2})} %</div></div></div>
          <div class="bars" role="img" aria-label="${s("drops",{d:e})}: ${l.drops}">${l.per_day.map(d=>r`<span style="height:${d?20+d/c*80:8}%;${d?"background:var(--warn)":""}"></span>`)}</div>
        </section>`})}</div>
      <section class="card" aria-labelledby="t-tl">
        <div class="row"><h2 id="t-tl">${s("timeline")}</h2><span class="hint">${s("retention",{d:this.state.settings.history_days})}</span></div>
        ${[...n.entries()].slice(0,30).map(([a,l])=>r`<div class="day">
          <div class="hint" style="font-weight:500;text-transform:uppercase;letter-spacing:.04em">${i(a)}</div>
          ${l.slice(0,50).map(c=>r`<div class="item"><span class="mono hint">${w(c.ts,!1)}</span>
            <span class="dot" style="color:${c.level==="warning"?"var(--warn)":c.level==="error"?"var(--bad)":"var(--muted)"}"></span>
            <span><b style="font-weight:500">${c.name}</b> · ${B(c)}${c.count>1?r` <span class="chip">${s("summed",{n:c.count})}</span>`:""}</span></div>`)}
        </div>`)}
        ${n.size?"":r`<p class="hint" style="font-size:14px">${s("noEntries")}</p>`}
      </section>`}render(){let e=(t,n)=>r`<button role="tab" aria-selected=${this.tab===t?"true":"false"}
      @click=${()=>{this.tab=t,t==="history"&&this._loadHistory()}}>${s(n)}</button>`;return r`
      <div class="head"><div><h1>${s("eventsTitle")}</h1><p class="sub">${s("eventsSub")}</p></div>
        <div class="tabs" role="tablist">${e("live","tabLive")}${e("history","tabHistory")}</div></div>
      <div class="filters">
        <label class="fld"><span class="lbl">${s("navConnections")}</span>
          <select class="inp" @change=${t=>{this.conn=t.target.value,this.tab==="history"&&this._loadHistory()}}>
            <option value="">${s("allConnections")}</option>
            ${this.state.connections.map(t=>r`<option value=${t.id} ?selected=${this.conn===t.id}>${t.name}</option>`)}</select></label>
        <label class="fld" style="flex:1 1 220px"><span class="lbl">${s("search")}</span>
          <input class="inp" type="search" .value=${this.query} placeholder=${s("searchPh")} @input=${t=>{this.query=t.target.value}}></label>
        <div role="group" aria-label="Level" style="display:flex;flex-wrap:wrap;gap:6px">${Gt.map(t=>r`<button class="lv ${t}" aria-pressed=${this.levels.has(t)?"true":"false"}
          @click=${()=>{let n=new Set(this.levels);n.has(t)?n.delete(t):n.add(t),this.levels=n}}>${s(`lv_${t}`)}</button>`)}</div>
      </div>
      ${this.tab==="live"?this._live():this._historyView()}`}};m(Q,"properties",{state:{attribute:!1},events:{attribute:!1},tab:{state:!0},conn:{state:!0},query:{state:!0},levels:{state:!0},paused:{state:!0},stats:{state:!0},history:{state:!0}}),m(Q,"styles",[...f.styles,v`
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
  `]);var Y=class extends f{constructor(){super(),this.text="",this.replaceAll=!1,this.take=new Set,this.choice={},this.disabled=!0}async _file(e){e&&(this.text=await e.text(),this._preview())}async _preview(){this.error="";try{this.preview=await h("api/import/preview",{method:"POST",body:{text:this.text}}),this.take=new Set(this.preview.items.filter(e=>e.connection&&!Object.keys(e.conflicts).length).map(e=>e.alias)),this.choice=Object.fromEntries(this.preview.items.filter(e=>Object.keys(e.conflicts).length).map(e=>[e.alias,"skip"]))}catch(e){this.error=e.data.note?T(e.data.note):e.message}}async _apply(){this.busy=!0;let e=[...this.preview.items.filter(t=>t.connection&&(this.take.has(t.alias)||this.choice[t.alias]&&this.choice[t.alias]!=="skip")).map(t=>t.alias)];try{let t=await h("api/import",{method:"POST",body:{text:this.text,replace_all:this.replaceAll,take:e,on_conflict:this.choice}});this.done=t,this.refresh()}catch(t){this.toast(`${s("error")}: ${t.data.note?T(t.data.note):t.message}`)}finally{this.busy=!1}}_steps(e){return r`<ol class="steps" aria-label=${s("importTitle")}>${["stepChoose","stepPreview","stepDone"].map((t,n)=>r`<li class=${n===e?"on":n<e?"past":""} aria-current=${n===e?"step":"false"}>
      <span class="num">${n<e?"\u2713":n+1}</span>${s(t)}</li>`)}</ol>`}_choose(){return r`<section class="card" aria-labelledby="t-file"><h2 id="t-file">${s("importChoose")}</h2>
      <div class="drop" @dragover=${e=>{e.preventDefault(),e.currentTarget.classList.add("over")}}
        @dragleave=${e=>e.currentTarget.classList.remove("over")}
        @drop=${e=>{e.preventDefault(),e.currentTarget.classList.remove("over"),this._file(e.dataTransfer.files[0])}}>
        ${_("upload",40)}<b style="font-size:16px;font-weight:500">${s("importDrop")}</b><span class="hint">${s("importFormats")}</span>
        <label class="btn btn-p">${s("chooseFile")}<input type="file" class="sr" accept=".yaml,.yml,.conf,.json,text/plain" @change=${e=>this._file(e.target.files[0])}></label>
      </div>
      <label class="fld"><span class="lbl">${s("pasteHere")}</span>
        <textarea class="inp mono" rows="6" .value=${this.text} @input=${e=>{this.text=e.target.value}}></textarea></label>
      ${this.error?r`<div class="note bad" role="alert">${this.error}</div>`:""}
      <div><button class="btn btn-s" ?disabled=${!this.text.trim()} @click=${this._preview}>${s("readPreview")}</button></div>
    </section>`}_result(e){return e.connection?Object.keys(e.conflicts).length&&!this.replaceAll?r`<span class="chip bad">${s("resConflict")}: ${Object.entries(e.conflicts).map(([t,n])=>`${t} \u2194 ${n}`).join(", ")}</span>`:e.notes.length?r`<span class="chip warn">${s("resNotes")}</span>`:r`<span class="chip ok">${s("resOk")}</span>`:r`<span class="chip bad">${s("resNo")}</span>`}_previewView(){let e=this.preview,n=e.items.filter(i=>i.connection).filter(i=>this.take.has(i.alias)||this.choice[i.alias]&&this.choice[i.alias]!=="skip").length;return r`<section class="card" aria-labelledby="t-prev">
      <div class="row"><div style="display:flex;align-items:center;gap:12px">${_("file",28)}
        <div><h2 id="t-prev">${s(`format_${e.version}`)}</h2><span class="hint">${s("found",{n:e.items.length})}</span></div></div>
        <button class="btn btn-g" @click=${()=>{this.preview=null}}>${s("otherFile")}</button></div>
      <div class="choices" role="radiogroup">${[[!1,"merge","mergeSub"],[!0,"replaceAll","replaceAllSub"]].map(([i,a,l])=>r`
        <button type="button" class="choice" role="radio" aria-checked=${this.replaceAll===i?"true":"false"} @click=${()=>{this.replaceAll=i}}>
          <b style="font-weight:500">${s(a)}</b><span class="hint">${s(l)}</span></button>`)}</div>
      ${e.notes.length?r`<div class="note warn"><b>${s("fileNotes")}</b>${e.notes.map(i=>r`<div>${T(i)}</div>`)}</div>`:""}
      <div class="scroll"><table style="min-width:680px"><thead><tr><th><span class="sr">${s("take")}</span></th><th>${s("name")}</th><th>${s("port")}</th><th>${s("device")}</th><th>${s("result")}</th></tr></thead>
        <tbody>${e.items.map(i=>{let a=i.connection,l=Object.keys(i.conflicts).length&&!this.replaceAll;return r`<tr>
            <td>${a&&!l?r`<input type="checkbox" style="width:18px;height:18px;accent-color:var(--accent)" aria-label="${i.alias} ${s("take")}"
              .checked=${this.take.has(i.alias)} @change=${c=>{let d=new Set(this.take);c.target.checked?d.add(i.alias):d.delete(i.alias),this.take=d}}>`:""}</td>
            <td><b style="font-weight:500">${i.alias}</b>${a?r`<div class="hint">${a.kind==="modbus"?s(`link_${a.link}`):`${D(a)} \xB7 ${a.mode}`} · max. ${a.max_clients}${a.enabled?"":" \xB7 off"}</div>`:""}</td>
            <td class="mono">${a?a.port:""}</td>
            <td class="mono" style="font-size:12px;overflow-wrap:anywhere;max-width:260px">${a?a.kind==="modbus"?I(a):a.device:""}</td>
            <td>${this._result(i)}
              ${i.notes.length?r`<ul class="notes">${i.notes.map(c=>r`<li>${T(c)}</li>`)}</ul>`:""}
              ${l?r`<label class="fld" style="margin-top:8px"><span class="hint">${s("onConflict")}</span>
                <select class="inp" style="min-height:36px" @change=${c=>{this.choice={...this.choice,[i.alias]:c.target.value}}}>
                  ${["skip","replace","new_port"].filter(c=>c!=="new_port"||!i.conflicts.device).map(c=>r`<option value=${c} ?selected=${this.choice[i.alias]===c}>${s(`c_${c}`)}</option>`)}
                </select></label>`:""}
            </td></tr>`})}</tbody></table></div>
      <div class="row" style="border-top:1px solid var(--line-2);padding-top:16px">
        <span class="hint" style="font-size:13px">${s("selected",{n,m:e.items.length})}</span>
        <div style="display:flex;gap:8px"><a class="btn btn-g" href="#/connections">${s("cancel")}</a>
          <button class="btn btn-p" ?disabled=${!n||this.busy} @click=${this._apply}>${s("apply",{n})}</button></div>
      </div></section>`}render(){let e=this.done?2:this.preview?1:0;return r`
      <p class="crumb"><a href="#/connections">${s("connectionsTitle")}</a> › ${s("importTitle")}</p>
      <h1 style="margin:12px 0 20px">${s("importTitle")}</h1>
      <div class="cols"><div class="main-col">
        ${this._steps(e)}
        ${this.done?r`<section class="card" style="align-items:flex-start"><span class="chip ok">${s("stepDone")}</span>
          <h2>${s("doneTitle",{n:this.done.changes.filter(t=>t.change==="added").length})}</h2><p class="hint" style="font-size:14px">${s("doneText")}</p>
          <div style="display:flex;gap:8px"><a class="btn btn-p" href="#/connections">${s("toConnections")}</a><a class="btn btn-s" href="#/settings">${s("sHistory")}</a></div></section>`:this.preview?this._previewView():this._choose()}
      </div>
      <aside class="side-col">
        <section class="card" aria-labelledby="t-exp"><h2 id="t-exp">${s("exportTitle")}</h2><p class="hint" style="font-size:14px">${s("exportText")}</p>
          <label class="chk"><input type="checkbox" .checked=${this.disabled} @change=${t=>{this.disabled=t.target.checked}}><span>${s("exportDisabled")}</span></label>
          <a class="btn btn-s" style="align-self:flex-start" href=${R(`api/export?disabled=${this.disabled?1:0}`)} download>${_("download")}${s("download")}</a></section>
        <section class="card" aria-labelledby="t-own"><h2 id="t-own">${s("ownTitle")}</h2><p class="hint" style="font-size:14px">${s("ownText")}</p>
          <a href="#/settings">${s("toSource")}</a></section>
      </aside></div>`}};m(Y,"properties",{state:{attribute:!1},text:{state:!0},preview:{state:!0},replaceAll:{state:!0},take:{state:!0},choice:{state:!0},done:{state:!0},error:{state:!0},disabled:{state:!0},busy:{state:!0}}),m(Y,"styles",[...f.styles,v`
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
  `]);var pt=["history_days","trace_file_mb","trace_keep","debounce_count","debounce_minutes"],Wt={history_days:"historyDays",trace_file_mb:"traceMb",trace_keep:"traceKeep",debounce_count:"debounceCount",debounce_minutes:"debounceMinutes"};function Kt(o,e){let t=o.split(`
`),n=e.split(`
`),i=new Set(t),a=new Set(n),l=[];for(let c of n)l.push(i.has(c)?`  ${c}`:`+ ${c}`);for(let c of t)a.has(c)||l.push(`- ${c}`);return l.filter(c=>!c.startsWith("  ")).join(`
`)||"  (\u2013)"}var J=class extends f{connectedCallback(){super.connectedCallback(),this.open=-1,this.diffs={},this._loadVersions(),this._loadCustom(),h("api/notify/services").then(e=>{this.services=e}).catch(()=>{this.services=[]})}willUpdate(){!this.draft&&this.state&&(this.draft={...this.state.settings})}async _loadVersions(){try{this.versions=await h("api/versions")}catch{this.versions=[]}}async _loadCustom(){try{this.custom=await h("api/custom"),this.customText=this.custom.text,this.customCheck=this.custom.exists?this.custom.check:null}catch{}}async _saveSettings(e){try{await h("api/settings",{method:"PUT",body:{settings:e}}),this.toast(s("saved")),this.refresh(),this._loadVersions()}catch(t){this.toast(t.data.errors?Object.values(t.data.errors).map(N).join("; "):`${s("error")}: ${t.message}`)}}async _changeListen(e){e!==this.state.settings.listen&&await S(this,s("listenConfirm"),s("confirm"))&&this._saveSettings({listen:e})}async _useOwn(){this.state.settings.source!=="custom"&&await S(this,s("ownConfirm"),s("confirm"))&&this._saveSettings({source:"custom"})}async _check(){try{this.customCheck=await h("api/custom/check",{method:"POST",body:{text:this.customText}})}catch(e){this.toast(e.message)}}async _saveCustom(e){try{await h("api/custom",{method:"PUT",body:{text:this.customText,use:e}}),this.toast(s("saved")),this.refresh(),this._loadCustom(),this._loadVersions()}catch(t){t.data.check?this.customCheck=t.data.check:this.toast(`${s("error")}: ${t.message}`)}}async _toggleDiff(e){if(this.open===e){this.open=-1;return}this.open=e;let t=this.versions[e],n=this.versions[e+1];if(this.diffs[t.id]===void 0)try{let i=await h(`api/versions/${t.id}`),a=n?await h(`api/versions/${n.id}`):{connections:[]};this.diffs={...this.diffs,[t.id]:Kt(JSON.stringify(a,null,1),JSON.stringify(i,null,1))}}catch{this.diffs={...this.diffs,[t.id]:"\u2013"}}}async _restore(e){if(await S(this,s("restoreConfirm"),s("restore")))try{await h(`api/versions/${e.id}/restore`,{method:"POST"}),this.toast(s("saved")),this.refresh(),this._loadVersions()}catch(t){this.toast(`${s("error")}: ${t.message}`)}}_changeLine(e){return He(e.changes)||e.summary}render(){let e=this.state,t=this.draft;if(!t)return"";let n=e.source==="custom",i=this.customCheck;return r`<div class="layout">
      <nav class="side" aria-label=${s("settingsTitle")}>
        <h1 style="margin:0 0 12px 12px">${s("settingsTitle")}</h1>
        ${[["net","sNet"],["src","sSource"],["hist","sHistory"],["notify","sNotify"],["mqtt","sMqtt"],["log","sLogging"],["diag","sDiag"],["about","sAbout"]].map(([a,l])=>r`<a href="#/settings" @click=${c=>{c.preventDefault(),this.renderRoot.getElementById(a).scrollIntoView({behavior:"smooth"})}}>${s(l)}</a>`)}
      </nav>
      <div class="content">
        <section id="net" class="card" aria-labelledby="t-net">
          <div><h2 id="t-net">${s("sNet")}</h2><p class="hint" style="margin-top:4px">${s("sNetSub")}</p></div>
          <div class="choices" role="radiogroup" aria-labelledby="t-net">${["local","apps","lan","all"].map(a=>r`<button type="button" class="choice" role="radio"
            aria-checked=${e.settings.listen===a?"true":"false"} @click=${()=>this._changeListen(a)}>
            <b style="font-weight:500">${s(`net_${a}`)}</b><span class="hint">${s(`netsub_${a}`)}</span></button>`)}</div>
          ${e.settings.listen==="all"?r`<div class="note bad" role="alert">${s("netWarn")}</div>`:""}
        </section>

        <section id="src" class="card" aria-labelledby="t-src">
          <div class="row"><div><h2 id="t-src">${s("sSource")}</h2><p class="hint" style="margin-top:4px">${s("sSourceSub")}</p></div>
            <div class="seg" role="group" aria-labelledby="t-src">
              <button aria-pressed=${n?"false":"true"} @click=${()=>this._saveSettings({source:"forms"})}>${s("forms")}</button>
              <button aria-pressed=${n?"true":"false"} ?disabled=${!this.custom?.exists} @click=${()=>this._useOwn()}>${s("own")}</button></div></div>
          <div class="note warn" role="note">${s("ownWarn")}</div>
          <textarea class="inp mono editor" aria-label="ser2net.yaml" .value=${this.customText||""} @input=${a=>{this.customText=a.target.value,this.customCheck=null}}></textarea>
          <div class="row">
            ${i?i.errors.length?r`<div class="note bad" style="flex:1">${i.errors.map(a=>r`<div>${T(a)}</div>`)}</div>`:r`<span class="chip ok">${s("checkOk",{n:i.connections.length})}</span>`:r`<span class="hint">${s("notChecked")}</span>`}
            <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn btn-s" @click=${this._check}>${s("check")}</button>
              <button class="btn btn-s" @click=${()=>this._saveCustom(!1)}>${s("saveFile")}</button>
              <button class="btn btn-p" @click=${()=>this._saveCustom(!0)}>${s("saveUse")}</button></div>
          </div>
          ${i&&i.notes.length?r`<div class="hint">${i.notes.map(a=>r`<div>${T(a)}</div>`)}</div>`:""}
        </section>

        <section id="hist" class="card" aria-labelledby="t-hist">
          <div class="row"><h2 id="t-hist">${s("sHistory")}</h2><span class="hint">${s("sHistorySub")}</span></div>
          <ol>${(this.versions||[]).map((a,l)=>r`<li>
            <div class="row"><div style="min-width:0"><div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center"><span style="font-weight:500">${this._changeLine(a)}</span>
              ${l===0?r`<span class="chip info">${s("current")}</span>`:""}</div>
              <div class="hint">${w(a.ts)} · ${s(`src_${a.source}`)}</div></div>
              <div style="display:flex;gap:4px"><button class="btn btn-g" aria-expanded=${this.open===l?"true":"false"} @click=${()=>this._toggleDiff(l)}>${this.open===l?s("hide"):s("diff")}</button>
                ${l?r`<button class="btn btn-s" @click=${()=>this._restore(a)}>${s("restore")}</button>`:""}</div></div>
            ${this.open===l?r`<div class="code" style="background:var(--surface-2);color:var(--text)">${this.diffs[a.id]??s("loading")}</div>`:""}
          </li>`)}</ol>
        </section>

        <section id="notify" class="card" aria-labelledby="t-notify">
          <div><h2 id="t-notify">${s("sNotify")}</h2><p class="hint" style="margin-top:4px">${s("sNotifySub")}</p></div>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("notifyGrace")}</span><input class="inp" inputmode="numeric" .value=${String(t.notify_grace)}
              @input=${a=>{this.draft={...t,notify_grace:Number(a.target.value||0)}}}></label>
            <label class="fld"><span class="lbl">${s("noClientMinutes")}</span><input class="inp" inputmode="numeric" .value=${String(t.no_client_minutes)}
              @input=${a=>{this.draft={...t,no_client_minutes:Number(a.target.value||0)}}}></label>
            <label class="fld"><span class="lbl">${s("notifyService")}</span><select class="inp" @change=${a=>{this.draft={...t,notify_service:a.target.value}}}>
              <option value="" ?selected=${!t.notify_service}>${s("notifyNone")}</option>
              ${[...new Set([...this.services||[],...t.notify_service?[t.notify_service]:[]])].map(a=>r`<option value=${a} ?selected=${t.notify_service===a}>notify.${a}</option>`)}</select></label>
            <label class="fld"><span class="lbl">${s("notifyLanguage")}</span><select class="inp" @change=${a=>{this.draft={...t,notify_language:a.target.value}}}>
              <option value="de" ?selected=${t.notify_language==="de"}>Deutsch</option><option value="en" ?selected=${t.notify_language==="en"}>English</option></select></label>
          </div>
          <div class="grid2" style="gap:6px 16px">${[["notify_dismiss","notifyDismiss"],["notify_resolved","notifyResolved"],["notify_stuck","notifyStuck"],["notify_line_errors","notifyLine"],["notify_ser2net","notifySer2net"]].map(([a,l])=>r`<label class="chk"><input type="checkbox" .checked=${!!t[a]} @change=${c=>{this.draft={...this.draft,[a]:c.target.checked}}}><span>${s(l)}</span></label>`)}</div>
          <p class="hint">${s("notifyPerConnection")}</p>
          <div><button class="btn btn-p" @click=${()=>this._saveSettings(Object.fromEntries(["notify_grace","no_client_minutes","notify_service","notify_language","notify_dismiss","notify_resolved","notify_stuck","notify_line_errors","notify_ser2net"].map(a=>[a,this.draft[a]])))}>${s("save")}</button></div>
        </section>

        <section id="mqtt" class="card" aria-labelledby="t-mqtt">
          <div class="row"><div><h2 id="t-mqtt">${s("sMqtt")}</h2><p class="hint" style="margin-top:4px">${s("sMqttSub")}</p></div>
            ${e.mqtt.broker?r`<span class="chip ${e.mqtt.connected?"ok":"warn"}">${e.mqtt.connected?s("mqttConnected"):s("mqttDisconnected")}</span>`:""}</div>
          ${e.mqtt.broker?r`<p class="hint">${s("mqttBroker",{b:e.mqtt.broker})}${e.mqtt.error?` \xB7 ${e.mqtt.error}`:""}</p>`:e.settings.mqtt_enabled?r`<div class="note warn">${s("mqttNoBroker")}</div>`:""}
          <label class="chk"><input type="checkbox" .checked=${!!t.mqtt_enabled} @change=${a=>{this.draft={...this.draft,mqtt_enabled:a.target.checked}}}><span>${s("mqttOn")}</span></label>
          <div class="grid2">
            ${[["mqtt_prefix","mqttPrefix"],["mqtt_base","mqttBase"]].map(([a,l])=>r`<label class="fld"><span class="lbl">${s(l)}</span>
              <input class="inp mono" .value=${t[a]} @input=${c=>{this.draft={...this.draft,[a]:c.target.value}}}></label>`)}
            <label class="fld"><span class="lbl">${s("mqttInterval")}</span><input class="inp" inputmode="numeric" .value=${String(t.mqtt_interval)}
              @input=${a=>{this.draft={...this.draft,mqtt_interval:Number(a.target.value||0)}}}></label>
          </div>
          <p class="hint">${s("mqttNames")}</p>
          <div><button class="btn btn-p" @click=${()=>this._saveSettings(Object.fromEntries(["mqtt_enabled","mqtt_prefix","mqtt_base","mqtt_interval"].map(a=>[a,this.draft[a]])))}>${s("save")}</button></div>
        </section>

        <section id="log" class="card" aria-labelledby="t-log">
          <h2 id="t-log">${s("sLogging")}</h2>
          <div class="grid2">
            <label class="fld"><span class="lbl">${s("logLevel")}</span><select class="inp" @change=${a=>{this.draft={...t,log_level:a.target.value}}}>
              ${["info","debug"].map(a=>r`<option ?selected=${t.log_level===a}>${a}</option>`)}</select></label>
            ${pt.map(a=>r`<label class="fld"><span class="lbl">${s(Wt[a])}</span>
              <input class="inp" inputmode="numeric" .value=${String(t[a])} @input=${l=>{this.draft={...t,[a]:Number(l.target.value||0)}}}></label>`)}
            <label class="fld"><span class="lbl">${s("language")}</span><select class="inp" @change=${a=>this.dispatchEvent(new CustomEvent("dp-lang",{detail:a.target.value,bubbles:!0,composed:!0}))}>
              <option value="de" ?selected=${$==="de"}>Deutsch</option><option value="en" ?selected=${$==="en"}>English</option></select></label>
          </div>
          <div><button class="btn btn-p" @click=${()=>this._saveSettings(Object.fromEntries(["log_level",...pt].map(a=>[a,t[a]])))}>${s("save")}</button></div>
        </section>

        <section id="diag" class="card" aria-labelledby="t-diag">
          <div class="row"><div><h2 id="t-diag">${s("sDiag")}</h2><p class="hint" style="margin-top:4px">${s("sDiagSub")}</p></div>
            <a class="btn btn-s" href=${R("api/diagnostics")} download>${s("diagDownload")}</a></div>
        </section>

        <section id="about" class="card" aria-labelledby="t-about">
          <h2 id="t-about">${s("sAbout")}</h2>
          <div style="display:grid;grid-template-columns:minmax(120px,180px) minmax(0,1fr);gap:8px 16px">
            <span class="hint" style="font-size:14px">${s("app")}</span><span>${e.version} · ${s("license")}</span>
            <span class="hint" style="font-size:14px">ser2net</span><span>${e.ser2net_version||"?"} (GPL-2.0)</span>
            <span class="hint" style="font-size:14px">${s("source")}</span><a href="https://github.com/bertel2020/HA-Device-Proxy" target="_blank" rel="noopener">github.com/bertel2020/HA-Device-Proxy</a>
          </div>
        </section>
      </div></div>`}};m(J,"properties",{state:{attribute:!1},draft:{state:!0},custom:{state:!0},customText:{state:!0},customCheck:{state:!0},versions:{state:!0},open:{state:!0},diffs:{state:!0},services:{state:!0}}),m(J,"styles",[...f.styles,v`
    .layout { display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start; }
    .side { flex: 1 1 200px; display: flex; flex-direction: column; gap: 2px; }
    .side a { display: flex; align-items: center; min-height: 40px; padding: 0 12px; border-radius: 10px; text-decoration: none; color: var(--neutral); }
    .side a:hover { background: var(--line); color: var(--text); }
    .content { flex: 999 1 640px; min-width: 0; display: flex; flex-direction: column; gap: 20px; }
    .card { scroll-margin-top: 16px; }
    ol { list-style: none; margin: 0; padding: 0; }
    li { border-top: 1px solid var(--line-2); padding: 12px 0; display: flex; flex-direction: column; gap: 10px; }
    textarea.editor { min-height: 260px; font-size: 12px; line-height: 1.6; background: var(--code-bg); color: var(--code-text); border-color: var(--code-bg); }
  `]);var Zt=["off","rx","tx","both"],X=class extends f{constructor(){super(),this.chunks=[],this.paused=!1,this.ascii=!0,this._after=0}connectedCallback(){super.connectedCallback(),this._timer=setInterval(()=>this._poll(),1e3)}disconnectedCallback(){super.disconnectedCallback(),clearInterval(this._timer)}willUpdate(e){e.has("selected")&&(this.chunks=[],this._after=0),!this.selected&&this.state?.connections.length&&(this.selected=this.state.connections[0].id)}async _poll(){if(!(this.paused||!this.selected||document.hidden))try{let e=await h(`api/live/${this.selected}?after=${this._after}`);e.length&&(this._after=e[e.length-1].seq,this.chunks=[...this.chunks,...e].slice(-400))}catch{}}async _mode(e,t){try{await U({...be(e),trace:t}),this.refresh()}catch(n){this.toast(`${s("error")}: ${n.message}`)}}async _delete(e){if(await S(this,s("deleteFile",{n:e}),s("delete")))try{await h(`api/trace/${encodeURIComponent(e)}`,{method:"DELETE"}),this.refresh()}catch(t){this.toast(`${s("error")}: ${t.message}`)}}render(){let e=this.state,t=this.connection(this.selected),n=e.trace_files;return r`
      <div class="head"><div><h1>${s("traceTitle")}</h1><p class="sub">${s("traceSub")}</p></div></div>
      <div class="cols">
        <section class="card side-col" style="gap:4px;padding:12px" aria-labelledby="t-conns">
          <h2 id="t-conns" style="padding:8px 8px 4px">${s("navConnections")}</h2>
          ${e.connections.map(i=>r`<div class="conn ${i.id===this.selected?"on":""}">
            <button class="pick" aria-current=${i.id===this.selected?"true":"false"} @click=${()=>oe(`#/trace/${i.id}`)}>
              <b style="font-weight:500">${i.name}</b><span class="hint">${i.trace==="off"?s("notRecording"):s("recording",{m:s(`tr_${i.trace}`)})}</span></button>
            <div class="seg" role="group" aria-label="${s("traceMode")} ${i.name}">${Zt.map(a=>r`<button type="button" aria-pressed=${i.trace===a?"true":"false"}
              ?disabled=${e.source==="custom"&&i.kind!=="modbus"} @click=${()=>this._mode(i,a)}>${a==="off"?s("off"):a==="both"?s("both"):a.toUpperCase()}</button>`)}</div>
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
            ${this.chunks.length?r`<div class="code view" style="border-radius:0"><table><tbody>${this.chunks.slice(-200).reverse().map(i=>r`<tr>
              <td style="color:#8f9ba8">${new Date(i.ts*1e3).toLocaleTimeString(void 0,{hour12:!1})}</td>
              <td><span class="dir ${i.direction==="rx"?"rx":i.direction==="tx"?"tx":"mark"}">${i.direction.toUpperCase()}</span></td>
              ${i.info?r`<td style="color:#9fb3c8">${i.info}</td>`:""}<td>${i.hex||i.text}</td>${!i.info&&this.ascii&&i.hex?r`<td style="color:#9fb3c8">${i.text.replace(/[^\x20-\x7e]/g,".")}</td>`:""}</tr>`)}</tbody></table></div>`:r`<p class="hint" style="padding:32px 20px;text-align:center;font-size:14px">${s(t&&t.kind==="modbus"?"liveEmptyMb":"liveEmpty")}</p>`}
          </section>
          <section class="card" aria-labelledby="t-files">
            <div class="row"><h2 id="t-files">${s("files")}</h2><span class="hint mono">/addon_configs/…_device_proxy/trace/</span></div>
            ${n.length?r`<div class="scroll"><table style="min-width:520px"><thead><tr><th>${s("fileTh")}</th><th>${s("changedTh")}</th><th style="text-align:right">${s("sizeTh")}</th><th><span class="sr">${s("delete")}</span></th></tr></thead>
              <tbody>${n.map(i=>r`<tr><td class="mono" style="font-size:13px">${i.name}</td><td>${w(i.modified)}</td><td style="text-align:right">${E(i.size)}</td>
                <td style="text-align:right;white-space:nowrap;padding:4px 0 4px 8px">
                  <a class="btn btn-g" href=${R(`api/trace/${encodeURIComponent(i.name)}`)} download aria-label="${i.name} ${s("download")}">${_("download",16)}</a>
                  <button class="btn btn-d" @click=${()=>this._delete(i.name)}>${s("delete")}</button></td></tr>`)}</tbody></table></div>`:r`<p class="hint" style="font-size:14px">–</p>`}
          </section>
        </div>
      </div>`}};m(X,"properties",{state:{attribute:!1},selected:{},chunks:{state:!0},paused:{state:!0},ascii:{state:!0}}),m(X,"styles",[...f.styles,v`
    .conn { display: flex; flex-direction: column; gap: 8px; padding: 10px 12px; border-radius: 12px; border: 1px solid transparent; }
    .conn.on { background: var(--accent-soft); border-color: var(--accent); }
    .pick { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; background: none; border: none; padding: 0; cursor: pointer; font: inherit; color: inherit; text-align: left; min-height: 40px; justify-content: center; width: 100%; }
    .view { max-height: 460px; overflow: auto; padding: 8px 4px; }
    .view table { font-family: "Roboto Mono", ui-monospace, Menlo, monospace; font-size: 12px; color: var(--code-text); }
    .view td { border: none; padding: 2px 8px; white-space: pre; }
    .dir { display: inline-block; min-width: 30px; text-align: center; border-radius: 6px; padding: 0 6px; }
    .rx { background: #1f3a52; color: #9ccbf0; } .tx { background: #4a3a1c; color: #f4c77d; } .mark { background: #2a3038; color: #c5ccd5; }
  `]);var Qt={"device-proxy":j,"dp-confirm":G,"dp-connections":W,"dp-detail":K,"dp-edit":Z,"dp-events":Q,"dp-import":Y,"dp-settings":J,"dp-trace":X};for(let[o,e]of Object.entries(Qt))customElements.get(o)||customElements.define(o,e);
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

"""
LA FOSSE, SON DÔME ET SES PÉRIMÈTRES, EN TROIS DIMENSIONS, DANS LA PAGE.

Ce fichier porte les textes de la section et le programme qui la dessine. La
géométrie, elle, vient de outils/convertir_fosse.py, qui la tire des DXF.

─── DEUX ÉTATS, ET LA RAISON DE N'EN FAIRE QU'UN SEUL OBJET ────────────────────
En filigrane, le dessin tourne lentement derrière le texte et n'intercepte aucun
clic : sur un téléphone, une toile qui capterait le glissement rendrait la page
impossible à faire défiler. Au clic sur le bouton, la MÊME toile passe au premier
plan, devient orientable, et se referme.

C'est bien la même toile qui se déplace d'un parent à l'autre, et non deux. Un
contexte WebGL ne survit pas à sa toile : en créer un second doublerait la mémoire
graphique, et certains navigateurs abandonnent le premier contexte sans prévenir.

─── POURQUOI PAS UNE BIBLIOTHÈQUE 3D ──────────────────────────────────────────
La scène tient en quelques maillages immobiles, une caméra en orbite et une
lumière directionnelle. Une bibliothèque généraliste apporterait cent soixante
kilooctets pour les quelques centaines de lignes qui suivent, sur un site dont une
page entière en pèse cinquante. Elle apporterait aussi une dépendance de plus à
suivre dans le temps.
"""

# ══ LES TEXTES DE LA SECTION ══════════════════════════════════════════════════
#
# Le surtitre, le titre, la phrase, le libellé du bouton, celui de la fermeture,
# et l'aide à la manipulation. La phrase dit d'où vient le dessin : un tir réel,
# une topographie réelle. C'est ce qui le distingue d'une illustration.

FOSSE3D = {
    'fr': ("EN TROIS DIMENSIONS", "La fosse, le tir et son dôme",
           "Le dôme balistique calculé sur un tir réel, posé sur la topographie de la fosse. C'est la géométrie dont BlastClear tire le périmètre d'évacuation.",
           "Explorer en 3D", "Fermer",
           "Faites glisser pour tourner, la molette pour approcher."),
    'en': ("IN THREE DIMENSIONS", "The pit, the blast and its dome",
           "The ballistic dome computed on a real blast, set on the pit's own topography. This is the geometry BlastClear draws the clearance perimeter from.",
           "Explore in 3D", "Close",
           "Drag to turn, scroll to zoom."),
    'es': ("EN TRES DIMENSIONES", "La corta, la voladura y su cúpula",
           "La cúpula balística calculada sobre una voladura real, apoyada en la topografía de la corta. Es la geometría de la que BlastClear extrae el perímetro de evacuación.",
           "Explorar en 3D", "Cerrar",
           "Arrastre para girar, la rueda para acercar."),
    'pt': ("EM TRÊS DIMENSÕES", "A corta, o fogo e a sua cúpula",
           "A cúpula balística calculada sobre um fogo real, assente na topografia da corta. É a geometria de que o BlastClear extrai o perímetro de evacuação.",
           "Explorar em 3D", "Fechar",
           "Arraste para rodar, a roda para aproximar."),
    'it': ("IN TRE DIMENSIONI", "La cava, la volata e la sua cupola",
           "La cupola balistica calcolata su una volata reale, posata sulla topografia della cava. È la geometria da cui BlastClear ricava il perimetro di evacuazione.",
           "Esplora in 3D", "Chiudi",
           "Trascini per ruotare, la rotella per avvicinare."),
    'de': ("DREIDIMENSIONAL", "Der Tagebau, die Sprengung und ihre Kuppel",
           "Die ballistische Kuppel, berechnet für eine reale Sprengung und auf das Gelände des Tagebaus gelegt. Aus dieser Geometrie leitet BlastClear den Evakuierungsperimeter ab.",
           "In 3D erkunden", "Schließen",
           "Ziehen zum Drehen, Mausrad zum Heranholen."),
    'nl': ("IN DRIE DIMENSIES", "De groeve, het schot en zijn koepel",
           "De ballistische koepel, berekend op een werkelijk schot en op de topografie van de groeve gelegd. Uit deze geometrie leidt BlastClear de evacuatieperimeter af.",
           "Verken in 3D", "Sluiten",
           "Sleep om te draaien, scrol om in te zoomen."),
    'sv': ("I TRE DIMENSIONER", "Dagbrottet, salvan och dess kupol",
           "Den ballistiska kupolen, beräknad på en verklig salva och lagd på dagbrottets topografi. Det är den geometri som BlastClear hämtar utrymningsperimetern ur.",
           "Utforska i 3D", "Stäng",
           "Dra för att vrida, rulla för att zooma."),
    'no': ("I TRE DIMENSJONER", "Dagbruddet, salven og kuppelen",
           "Den ballistiske kuppelen, beregnet på en virkelig salve og lagt på dagbruddets terreng. Det er denne geometrien BlastClear henter evakueringsperimeteren fra.",
           "Utforsk i 3D", "Lukk",
           "Dra for å snu, rull for å zoome."),
    'da': ("I TRE DIMENSIONER", "Bruddet, sprængningen og dens kuppel",
           "Den ballistiske kuppel, beregnet på en virkelig sprængning og lagt på bruddets terræn. Det er den geometri, BlastClear henter evakueringsperimeteren fra.",
           "Udforsk i 3D", "Luk",
           "Træk for at dreje, rul for at zoome."),
    'af': ("IN DRIE DIMENSIES", "Die groef, die skoot en sy koepel",
           "Die ballistiese koepel, bereken op 'n werklike skoot en op die groef se eie topografie geplaas. Dit is die meetkunde waaruit BlastClear die ontruimingsomtrek trek.",
           "Verken in 3D", "Maak toe",
           "Sleep om te draai, rol om in te zoem."),
    'tr': ("ÜÇ BOYUTTA", "Ocak, atım ve kubbesi",
           "Gerçek bir atım için hesaplanan ve ocağın topoğrafyasına oturtulan balistik kubbe. BlastClear tahliye çevresini bu geometriden çıkarır.",
           "3B olarak keşfedin", "Kapat",
           "Döndürmek için sürükleyin, yakınlaştırmak için tekerleği kullanın."),
    'zh': ("三维视图", "矿坑、爆区与弹道穹顶",
           "基于真实爆区计算的弹道穹顶，叠加在矿坑实际地形之上。BlastClear 正是由这一几何体推导出疏散警戒范围。",
           "以三维查看", "关闭",
           "拖动可旋转，滚轮可缩放。"),
}


# ══ LES NOMS DES COUCHES ET DES VUES ══════════════════════════════════════════
#
# ─── LE CERCLE PORTE SON RAYON DANS SON NOM, ET C'EST LE POINT ────────────────
# « Cercle 300 m » n'est pas un décor : c'est la règle empirique que le dôme
# remplace. Les deux tracés sont posés au même endroit, à la même altitude, pour
# qu'on voie d'un coup d'œil où le cercle est trop large et où il est trop court.
# Son nom doit donc dire ce qu'il est, non « cercle de référence ».
#
# ─── LES POINTS CARDINAUX SONT CEUX DU RELEVÉ ─────────────────────────────────
# L'axe des X de la scène garde l'est du plan minier, et son Z pointe le sud : la
# conversion l'impose une fois pour toutes. « Est » désigne donc bien l'est du
# site, non une direction d'écran.

#
# ─── LE RAYON N'EST ÉCRIT QU'UNE FOIS ─────────────────────────────────────────
# Il figurait en toutes lettres dans les treize libellés, et changer de rayon les
# a tous laissés à mentir. Il vient désormais d'une seule valeur, celle-là même
# qui engendre le cercle, et les libellés la reçoivent.

RAYON_CERCLE_M = 500

COUCHES3D = {
    'fr': ("Calques", "Fosse", "Dôme", "Contour du tir", "Périmètre 3D", "Cercle {r} m"),
    'en': ("Layers", "Pit", "Dome", "Blast outline", "3D perimeter", "{r} m circle"),
    'es': ("Capas", "Corta", "Cúpula", "Contorno de la voladura", "Perímetro 3D", "Círculo de {r} m"),
    'pt': ("Camadas", "Corta", "Cúpula", "Contorno do fogo", "Perímetro 3D", "Círculo de {r} m"),
    'it': ("Livelli", "Cava", "Cupola", "Contorno della volata", "Perimetro 3D", "Cerchio da {r} m"),
    'de': ("Ebenen", "Tagebau", "Kuppel", "Sprengungskontur", "3D-Perimeter", "{r}-m-Kreis"),
    'nl': ("Lagen", "Groeve", "Koepel", "Schotcontour", "3D-perimeter", "Cirkel van {r} m"),
    'sv': ("Lager", "Dagbrott", "Kupol", "Salvans kontur", "3D-perimeter", "{r} m-cirkel"),
    'no': ("Lag", "Dagbrudd", "Kuppel", "Salvens kontur", "3D-perimeter", "{r} m-sirkel"),
    'da': ("Lag", "Brud", "Kuppel", "Sprængningens kontur", "3D-perimeter", "{r} m-cirkel"),
    'af': ("Lae", "Groef", "Koepel", "Skootkontoer", "3D-omtrek", "{r} m-sirkel"),
    'tr': ("Katmanlar", "Ocak", "Kubbe", "Atım konturu", "3B çevre", "{r} m çember"),
    'zh': ("图层", "矿坑", "穹顶", "爆区轮廓", "三维警戒范围", "{r} m 圆"),
}


def couches_traduites(code: str) -> list[str]:
    """Les noms des couches, le rayon du cercle mis en place."""
    t = COUCHES3D.get(code) or COUCHES3D['en']
    return [m.replace('{r}', str(RAYON_CERCLE_M)) for m in t]

VUES3D = {
    'fr': ("Haut", "Bas", "Nord", "Sud", "Est", "Ouest"),
    'en': ("Top", "Bottom", "North", "South", "East", "West"),
    'es': ("Cenital", "Inferior", "Norte", "Sur", "Este", "Oeste"),
    'pt': ("Topo", "Base", "Norte", "Sul", "Este", "Oeste"),
    'it': ("Alto", "Basso", "Nord", "Sud", "Est", "Ovest"),
    'de': ("Oben", "Unten", "Nord", "Süd", "Ost", "West"),
    'nl': ("Boven", "Onder", "Noord", "Zuid", "Oost", "West"),
    'sv': ("Ovan", "Under", "Norr", "Söder", "Öster", "Väster"),
    'no': ("Over", "Under", "Nord", "Sør", "Øst", "Vest"),
    'da': ("Over", "Under", "Nord", "Syd", "Øst", "Vest"),
    'af': ("Bo", "Onder", "Noord", "Suid", "Oos", "Wes"),
    'tr': ("Üst", "Alt", "Kuzey", "Güney", "Doğu", "Batı"),
    'zh': ("俯视", "仰视", "北", "南", "东", "西"),
}


# ══ LE STYLE ══════════════════════════════════════════════════════════════════

CSS_FOSSE = """
/* ══ LA FOSSE EN FILIGRANE ═════════════════════════════════════════════════
   La toile occupe toute la section et passe DERRIÈRE le texte. Elle
   n'intercepte aucun clic : sur téléphone, une toile qui capterait le
   glissement empêcherait de faire défiler la page, ce qui est un prix
   qu'aucun décor ne vaut.

   Sa faible opacité est ce qui en fait un filigrane. Le texte, lui, reste au
   contraste plein : c'est le fond qui s'efface, jamais ce qui se lit. */
.dc-fosse{position:relative;overflow:hidden}
.dc-fosse-toile{position:absolute;inset:0;width:100%;height:100%;
  pointer-events:none;opacity:0;transition:opacity .9s ease}
.dc-fosse-toile.dc-vue{opacity:1}
.dc-fosse>*:not(.dc-fosse-toile){position:relative;z-index:1}

/* ── AU PREMIER PLAN ──────────────────────────────────────────────────────
   La même toile change de parent. Elle retrouve ici sa pleine opacité, reçoit
   les clics, et couvre l'écran. Le fond sombre n'est pas décoratif : il donne
   au tracé le contraste qu'un fond clair lui refuse. */
.dc-fosse-plein{position:fixed;inset:0;z-index:80;background:#0C0F14;
  animation:dc-fondu .25s ease both}
.dc-fosse-plein .dc-fosse-toile{position:absolute;inset:0;pointer-events:auto;
  opacity:1;cursor:grab;touch-action:none}
.dc-fosse-plein .dc-fosse-toile:active{cursor:grabbing}
@keyframes dc-fondu{from{opacity:0}to{opacity:1}}

.dc-fosse-fermer{position:absolute;top:16px;right:16px;z-index:3;
  display:inline-flex;align-items:center;gap:8px;min-height:44px;
  background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.28);
  color:#ffffff;font-family:inherit;font-weight:600;font-size:14px;
  padding:10px 18px;border-radius:2px;cursor:pointer}
@media (hover:hover){.dc-fosse-fermer:hover{background:rgba(255,255,255,.20)}}

.dc-fosse-aide{position:absolute;left:0;right:0;bottom:14px;z-index:2;
  text-align:center;color:#9AA3AE;font-size:13px;padding:0 16px;
  pointer-events:none}

/* Le bouton d'ouverture reprend le bouton secondaire de la page. */
.dc-fosse-ouvrir{display:inline-flex;align-items:center;gap:9px;
  border:1px solid var(--bc-bleu);color:var(--bc-bleu);background:none;
  font-family:inherit;font-weight:600;font-size:15px;padding:10px 20px;
  border-radius:2px;cursor:pointer;min-height:44px}
@media (hover:hover){
  .dc-fosse-ouvrir:hover{background:var(--bc-bleu);color:#ffffff}
}

.dc-fosse-plein button:focus-visible,
.dc-fosse-plein input:focus-visible,
.dc-fosse-ouvrir:focus-visible{outline:2px solid var(--bc-jaune);outline-offset:2px}

/* ══ LE PANNEAU DES CALQUES ════════════════════════════════════════════════
   Chaque tracé répond à une question différente : où est le terrain, jusqu'où
   porte le dôme, où est le tir, où passe le périmètre, et ce qu'aurait donné
   un simple cercle. Les superposer tous rend le dessin illisible ; les éteindre
   un à un est la seule façon de lire une comparaison.

   Ce sont de vraies cases à cocher, non des pastilles : elles se cochent au
   clavier, s'annoncent comme telles, et disent leur état sans qu'on ait à
   deviner ce qu'une couleur veut dire. */
.dc-fosse-calques{position:absolute;left:16px;bottom:16px;z-index:3;
  background:rgba(12,15,20,.82);border:1px solid rgba(255,255,255,.16);
  border-radius:2px;padding:12px 14px;min-width:160px}
.dc-fosse-calques h3{margin:0 0 9px;font-size:11px;letter-spacing:1.4px;
  text-transform:uppercase;color:#9AA3AE;font-weight:600}
.dc-fosse-calques label{display:flex;align-items:center;gap:9px;
  min-height:30px;color:#E7EAEE;font-size:13px;cursor:pointer;white-space:nowrap}
.dc-fosse-calques input{accent-color:var(--bc-jaune);width:15px;height:15px;
  margin:0;cursor:pointer;flex:0 0 auto}
/* La pastille rappelle la couleur du tracé dans la scène. Elle DOUBLE
   l'étiquette, elle ne la remplace pas : seule, elle laisserait un lecteur
   daltonien sans moyen de savoir quelle ligne il éteint. */
.dc-fosse-pastille{width:12px;height:12px;border-radius:50%;flex:0 0 auto;
  box-sizing:border-box}

/* ══ LE CUBE DE VUE ════════════════════════════════════════════════════════
   Il tourne avec la caméra et se clique par la face. Il est bâti en trois
   dimensions CSS, non dessiné dans la toile : ses faces restent alors de vrais
   boutons, atteignables au clavier et énoncés par un lecteur d'écran, ce
   qu'un dessin dans un canevas ne peut pas offrir. */
.dc-fosse-cube-zone{position:absolute;top:16px;left:16px;z-index:3;
  width:104px;height:104px;perspective:460px}
.dc-fosse-cube{position:absolute;inset:0;transform-style:preserve-3d;
  transform:translateZ(-52px)}
.dc-fosse-cube button{position:absolute;left:50%;top:50%;width:62px;height:62px;
  margin:-31px 0 0 -31px;display:flex;align-items:center;justify-content:center;
  background:rgba(37,73,138,.62);border:1px solid rgba(255,255,255,.30);
  color:#ffffff;font-family:inherit;font-size:11px;font-weight:600;
  letter-spacing:.2px;cursor:pointer;backface-visibility:hidden}
@media (hover:hover){
  .dc-fosse-cube button:hover{background:var(--bc-jaune);color:#14171C}
}

@media (max-width:719px){
  .dc-fosse-cube-zone{width:78px;height:78px;top:12px;left:12px}
  .dc-fosse-cube{transform:translateZ(-39px)}
  .dc-fosse-cube button{width:46px;height:46px;margin:-23px 0 0 -23px;font-size:9px}
  .dc-fosse-calques{left:12px;right:12px;bottom:12px;padding:10px 12px;
    display:flex;flex-wrap:wrap;gap:2px 14px;align-items:center}
  .dc-fosse-calques h3{width:100%;margin:0 0 4px}
  .dc-fosse-aide{display:none}
}
"""


# ══ LE CHARGEUR ═══════════════════════════════════════════════════════════════
#
# ─── IL VIT DANS SA PROPRE PARENTHÈSE, ET C'EST DÉLIBÉRÉ ──────────────────────
# Il a d'abord été écrit à la fin de la grande parenthèse de design.js, à la
# suite du carrousel et du formulaire. Une faute survenant plus haut, ou une
# simple sortie anticipée dans un cas de mise en page particulier, emportait
# alors le chargeur avec elle : la fosse ne se chargeait plus, sans rien dire.
#
# Isolé, il ne dépend plus de rien. C'est la règle qui devrait valoir pour toute
# fonction indépendante partageant un fichier avec d'autres.

JS_CHARGEUR = r"""

/* ════════════════════════════════════════════════════════════════════════════
   LA FOSSE EN TROIS DIMENSIONS, CHARGÉE À LA DEMANDE.

   Le programme de rendu et la géométrie ne partent que lorsque la section
   approche de l'écran. Un visiteur qui ne descend jamais jusque-là ne les
   télécharge pas, et la page garde exactement le poids qu'elle avait avant.

   La marge de six cents pixels laisse au chargement le temps d'aboutir avant
   que la section ne paraisse : arrivée à l'écran, elle est déjà dessinée.
   ════════════════════════════════════════════════════════════════════════════ */
(function () {
  var fosse = document.querySelector('[data-fosse]');
  if (!fosse) return;

  var parti = false;
  function charger() {
    if (parti) return;
    parti = true;
    var s = document.createElement('script');
    /* Toutes les pages vivent dans /<langue>/, donc ce chemin vaut pour toutes.
       Le déduire de l'adresse du script courant serait plus savant et moins
       sûr : document.currentScript est nul dès que le code s'exécute depuis un
       rappel. */
    s.src = '../js/fosse.js';
    document.head.appendChild(s);
  }

  if (!('IntersectionObserver' in window)) { charger(); return; }

  var guetteur = new IntersectionObserver(function (entrees) {
    if (!entrees[0].isIntersecting) return;
    guetteur.disconnect();
    charger();
  }, { rootMargin: '600px' });
  guetteur.observe(fosse);

  /* ── UN SECOND DÉCLENCHEUR, POUR LE CAS OÙ LE PREMIER SE TAIT ──────────
     L'observateur dépend du cycle de rendu du navigateur. Il suffit en usage
     normal, mais il ne coûte rien de doubler la garde par un relevé direct de
     la position au défilement. Les deux passent par la même fonction, qui ne se
     laisse appeler qu'une fois. */
  function verifier() {
    if (parti) return;
    var r = fosse.getBoundingClientRect();
    if (r.top < window.innerHeight + 600 && r.bottom > -600) {
      guetteur.disconnect();
      charger();
    }
  }
  window.addEventListener('scroll', verifier, { passive: true });
  window.addEventListener('resize', verifier, { passive: true });
  verifier();
})();
"""


# ══ LE PROGRAMME DE RENDU ═════════════════════════════════════════════════════

JS_FOSSE = r"""/* ════════════════════════════════════════════════════════════════════════════
   LA FOSSE, SON DÔME ET SES PÉRIMÈTRES, EN WEBGL.

   Chargé à la demande par design.js, lorsque la section approche de l'écran.

   ─── CE QUE LE FICHIER DE GÉOMÉTRIE CONTIENT ──────────────────────────────
   Des entiers courts, non des flottants. Les positions sont quantifiées sur
   seize bits dans un cube commun à toutes les couches, et la carte graphique
   les ramène elle-même dans [0,1] : c'est le rôle du drapeau « normalisé »
   passé à vertexAttribPointer. Le nuanceur n'a plus qu'à les recentrer.

   Deux octets par coordonnée au lieu de quatre, pour un pas de 2,4 cm sur une
   emprise de 1 545 m. Aucun œil ne mesure ce décor à cette échelle.
   ════════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var hote = document.querySelector('[data-fosse]');
  if (!hote) return;

  var BASE = hote.getAttribute('data-fosse');   // « ../assets/fosse/ »
  var bouton = hote.querySelector('.dc-fosse-ouvrir');
  if (!bouton) return;

  function etiquettes(nom) {
    try { return JSON.parse(bouton.getAttribute(nom) || '[]'); }
    catch (e) { return []; }
  }
  var MOTS_COUCHES = etiquettes('data-couches');   // titre, puis un nom par couche
  var MOTS_VUES = etiquettes('data-vues');         // haut, bas, nord, sud, est, ouest

  /* ══ LES COUCHES ══════════════════════════════════════════════════════════
     L'ordre est celui du tracé : les surfaces d'abord, qui écrivent la
     profondeur, les traits ensuite, qui ne l'écrivent pas.

     « filigrane » dit si la couche paraît dans le décor de la page. Seuls le
     terrain et le dôme y figurent : le contour d'un tir et un cercle de trois
     cents mètres n'y seraient que du bruit derrière du texte. Au premier plan,
     où l'on vient comparer, tout est allumé. */
  /* ─── « TRAVERSE » : TROIS TRACÉS IGNORENT LA PROFONDEUR ────────────────
     Le tir est au fond de la fosse, à -70 m, et son contour comme les deux
     périmètres y sont posés à cette altitude. Les parois du gradin remontent
     bien au-dessus : soumis au test de profondeur, ces trois tracés
     disparaissent sous le terrain, et en vue de dessus, qui est justement la
     vue de comparaison, on ne voit plus rien du tout.

     Ce sont des annotations, non des volumes. Les logiciels miniers les
     dessinent de la même façon, par-dessus la topographie, pour qu'un plan
     d'évacuation reste lisible quel que soit le relief qu'il recouvre.

     Le dôme, lui, garde le test : c'est un volume, et le voir au travers de la
     paroi qui le masque donnerait une fausse idée de sa portée. */
  /* ─── LE PÉRIMÈTRE ET SON CERCLE PARTAGENT LA COULEUR ────────────────────
     Les deux répondent à la même question, « jusqu'où évacuer », et se lisent
     donc ensemble. Deux teintes différentes les auraient posés comme deux
     objets distincts, alors que l'un est la version plate de l'autre.

     C'est le TRAIT qui les sépare : plein pour le périmètre calculé, tireté
     pour le cercle, selon l'usage du dessin technique où un tireté marque ce
     qui est supposé plutôt que relevé. Le tireté vient de la géométrie
     elle-même, un segment sur cinq n'étant pas émis. */
  var COUCHES = {
    fosse:     { rang: 0, couleur: [0x25, 0x49, 0x8A], filigrane: true,  traverse: false },
    dome:      { rang: 1, couleur: [0xFD, 0xC3, 0x0E], filigrane: true,  traverse: false },
    contour:   { rang: 2, couleur: [0xFF, 0xFF, 0xFF], filigrane: false, traverse: true },
    perimetre: { rang: 3, couleur: [0xFF, 0x3B, 0x30], filigrane: false, traverse: true },
    cercle:    { rang: 4, couleur: [0xFF, 0x3B, 0x30], filigrane: false, traverse: true,
                 tirets: true },
  };
  var ORDRE = ['fosse', 'dome', 'contour', 'perimetre', 'cercle'];

  /* ══ ALGÈBRE ══════════════════════════════════════════════════════════════
     Les matrices sont en colonne d'abord, comme WebGL les attend, ce qui évite
     de les transposer à chaque envoi. */

  function perspective(fovy, rapport, pres, loin) {
    var f = 1 / Math.tan(fovy / 2), d = pres - loin;
    return new Float32Array([
      f / rapport, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (loin + pres) / d, -1,
      0, 0, 2 * loin * pres / d, 0,
    ]);
  }

  function regard(oeil, cible, haut) {
    var z = normer([oeil[0] - cible[0], oeil[1] - cible[1], oeil[2] - cible[2]]);
    var x = normer(produit(haut, z));
    var y = produit(z, x);
    return new Float32Array([
      x[0], y[0], z[0], 0,
      x[1], y[1], z[1], 0,
      x[2], y[2], z[2], 0,
      -(x[0] * oeil[0] + x[1] * oeil[1] + x[2] * oeil[2]),
      -(y[0] * oeil[0] + y[1] * oeil[1] + y[2] * oeil[2]),
      -(z[0] * oeil[0] + z[1] * oeil[1] + z[2] * oeil[2]), 1,
    ]);
  }

  function produit(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  }
  function normer(v) {
    var n = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / n, v[1] / n, v[2] / n];
  }
  function multiplier(a, b) {          // a * b, colonne d'abord
    var r = new Float32Array(16);
    for (var c = 0; c < 4; c++) {
      for (var l = 0; l < 4; l++) {
        r[c * 4 + l] = a[l] * b[c * 4] + a[4 + l] * b[c * 4 + 1] +
                       a[8 + l] * b[c * 4 + 2] + a[12 + l] * b[c * 4 + 3];
      }
    }
    return r;
  }

  /* ══ NUANCEURS ════════════════════════════════════════════════════════════
     Un seul programme sert à tous les maillages. u_uni bascule entre la surface
     éclairée et le trait de couleur unie : deux programmes pour cette
     différence coûteraient deux compilations et un changement d'état par image. */

  var SOMMETS = [
    'attribute vec3 a_pos;',
    'attribute vec3 a_nor;',
    'uniform mat4 u_mvp;',
    'varying vec3 v_nor;',
    'void main() {',
    /* La carte a rendu [0,1] ; le cube de la scène va de -1 à 1. */
    '  gl_Position = u_mvp * vec4(a_pos * 2.0 - 1.0, 1.0);',
    '  v_nor = a_nor;',
    '}',
  ].join('\n');

  var FRAGMENTS = [
    'precision mediump float;',
    'varying vec3 v_nor;',
    'uniform vec3 u_couleur;',
    'uniform float u_opacite;',
    'uniform float u_uni;',
    'void main() {',
    '  if (u_uni > 0.5) { gl_FragColor = vec4(u_couleur, u_opacite); return; }',
    /* Une seule source, haute et de trois quarts, comme un éclairage de maquette.
       Le terme ambiant empêche les faces opposées de tomber au noir : une
       banquette dans l'ombre doit rester lisible. */
    '  vec3 n = normalize(v_nor);',
    '  float l = 0.42 + 0.58 * max(dot(n, normalize(vec3(0.45, 0.82, 0.36))), 0.0);',
    '  gl_FragColor = vec4(u_couleur * l, u_opacite);',
    '}',
  ].join('\n');

  function compiler(gl, type, source) {
    var s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  }

  /* ══ NORMALES ═════════════════════════════════════════════════════════════
     Elles sont calculées ICI, et non transportées : trois flottants par sommet
     pèseraient plus lourd que la position quantifiée qu'ils accompagnent, pour
     une donnée que le navigateur retrouve en quelques millisecondes.

     Elles sont MOYENNÉES aux sommets partagés, et pondérées par l'aire de
     chaque face puisque le produit vectoriel n'est pas normé avant l'addition.
     Une grande facette pèse ainsi plus qu'une petite, ce qui adoucit les
     raccords sans effacer les arêtes de gradin. */
  function normales(positions, triangles) {
    var n = new Float32Array(positions.length);
    for (var i = 0; i < triangles.length; i += 3) {
      var a = triangles[i] * 3, b = triangles[i + 1] * 3, c = triangles[i + 2] * 3;
      var ux = positions[b] - positions[a], uy = positions[b + 1] - positions[a + 1],
          uz = positions[b + 2] - positions[a + 2];
      var vx = positions[c] - positions[a], vy = positions[c + 1] - positions[a + 1],
          vz = positions[c + 2] - positions[a + 2];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      n[a] += nx; n[a + 1] += ny; n[a + 2] += nz;
      n[b] += nx; n[b + 1] += ny; n[b + 2] += nz;
      n[c] += nx; n[c + 1] += ny; n[c + 2] += nz;
    }
    for (var j = 0; j < n.length; j += 3) {
      var m = Math.hypot(n[j], n[j + 1], n[j + 2]) || 1;
      n[j] /= m; n[j + 1] /= m; n[j + 2] /= m;
    }
    return n;
  }

  /* ══ CHARGEMENT ═══════════════════════════════════════════════════════════ */

  function binaire(nom) {
    return fetch(BASE + nom).then(function (r) {
      if (!r.ok) throw new Error(nom);
      return r.arrayBuffer();
    });
  }

  /* Une couche porte UNE table de positions et un ou deux jeux d'indices qui la
     partagent : la fosse est dessinée deux fois, en surface puis en fil de fer,
     sur les mêmes sommets. Les transporter deux fois doublerait le fichier. */
  fetch(BASE + 'fosse.json')
    .then(function (r) { return r.json(); })
    .then(function (manifeste) {
      var couches = manifeste.couches || manifeste.calques || {};
      var noms = Object.keys(couches).filter(function (n) { return COUCHES[n]; });
      return Promise.all(noms.map(function (nom) {
        var c = couches[nom];
        return Promise.all(
          [binaire(c.position)].concat(c.jeux.map(function (j) { return binaire(j.index); }))
        ).then(function (tampons) {
          return {
            nom: nom,
            positions: new Uint16Array(tampons[0]),
            jeux: c.jeux.map(function (j, i) {
              return { forme: j.forme, indices: new Uint16Array(tampons[i + 1]) };
            }),
          };
        });
      })).then(function (lots) {
        return { boite: manifeste.boite, lots: lots };
      });
    })
    /* Le second argument de then, et non un catch en bout de chaîne : il ne
       rattrape que les échecs du CHARGEMENT, réseau coupé ou fichier absent, où
       se taire est la bonne conduite puisque la section se tient sans son
       dessin. Un catch final avalerait aussi les fautes de demarrer, et une
       faute de programmation avalée ne se corrige jamais. */
    .then(demarrer, function () { /* la section garde son texte */ });

  /* ══ LA SCÈNE ═════════════════════════════════════════════════════════════ */

  function demarrer(scene) {
    var lots = scene.lots;
    var boite = scene.boite || { min: [-1, -1, -1], max: [1, 1, 1] };

    var toile = document.createElement('canvas');
    toile.className = 'dc-fosse-toile';
    toile.setAttribute('aria-hidden', 'true');

    var options = { alpha: true, antialias: true, depth: true,
                    premultipliedAlpha: false, powerPreference: 'low-power' };
    var gl = toile.getContext('webgl', options) || toile.getContext('experimental-webgl', options);
    if (!gl) return;                      /* pas de WebGL : rien ne s'affiche */

    var prog = gl.createProgram();
    var vs = compiler(gl, gl.VERTEX_SHADER, SOMMETS);
    var fs = compiler(gl, gl.FRAGMENT_SHADER, FRAGMENTS);
    if (!vs || !fs) return;
    gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);

    var aPos = gl.getAttribLocation(prog, 'a_pos');
    var aNor = gl.getAttribLocation(prog, 'a_nor');
    var uMvp = gl.getUniformLocation(prog, 'u_mvp');
    var uCouleur = gl.getUniformLocation(prog, 'u_couleur');
    var uOpacite = gl.getUniformLocation(prog, 'u_opacite');
    var uUni = gl.getUniformLocation(prog, 'u_uni');

    var BLEU = [0x25 / 255, 0x49 / 255, 0x8A / 255];

    var objets = [];
    var presentes = {};
    lots.forEach(function (lot) {
      presentes[lot.nom] = true;
      var position = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, position);
      gl.bufferData(gl.ARRAY_BUFFER, lot.positions, gl.STATIC_DRAW);

      var normale = null;
      var surface = lot.jeux.filter(function (j) { return j.forme === 'triangles'; })[0];
      if (surface) {
        /* Le calcul des normales se fait dans l'espace réel, donc sur les
           positions ramenées de [0,65535] à [-1,1]. */
        var reelles = new Float32Array(lot.positions.length);
        for (var i = 0; i < lot.positions.length; i++) {
          reelles[i] = lot.positions[i] / 32767.5 - 1;
        }
        normale = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, normale);
        gl.bufferData(gl.ARRAY_BUFFER, normales(reelles, surface.indices), gl.STATIC_DRAW);
      }

      lot.jeux.forEach(function (jeu) {
        var index = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, jeu.indices, gl.STATIC_DRAW);
        objets.push({
          couche: lot.nom, forme: jeu.forme, nombre: jeu.indices.length,
          position: position, normale: normale, index: index,
        });
      });
    });
    /* Les surfaces d'abord, puis les traits, chacun dans l'ordre des couches :
       un trait tracé avant la surface qui le porte serait repeint par elle. */
    objets.sort(function (a, b) {
      var sa = a.forme === 'triangles' ? 0 : 1, sb = b.forme === 'triangles' ? 0 : 1;
      return sa - sb || COUCHES[a.couche].rang - COUCHES[b.couche].rang;
    });

    /* L'état d'affichage de chaque couche présente. */
    var affichee = {};
    ORDRE.forEach(function (nom) {
      if (presentes[nom]) affichee[nom] = true;
    });

    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    /* ── LE TRAIT ET SA SURFACE SONT À LA MÊME PROFONDEUR ─────────────────
       Les arêtes de la fosse sont tracées sur les sommets mêmes de sa surface :
       elles occupent donc exactement la même profondeur, et le test de
       profondeur en retient tantôt l'une tantôt l'autre selon les arrondis du
       calcul. Le trait se met alors à clignoter par morceaux quand la scène
       tourne.

       Repousser la surface d'un cheveu, et elle seule, lève l'égalité : le
       trait passe toujours devant, sans qu'aucune géométrie ne bouge. */
    gl.enable(gl.POLYGON_OFFSET_FILL);
    gl.polygonOffset(1.2, 1.2);

    /* ══ LA CAMÉRA ════════════════════════════════════════════════════════
       L'azimut tourne, l'élévation est bornée : passer au-dessus du zénith
       retournerait la scène, ce qui désoriente sans rien montrer de plus. La
       borne s'arrête juste avant la verticale, où la caméra et son vecteur
       « haut » seraient alignés et l'orientation indéterminée.

       LE RECUL N'EST PAS UN NOMBRE FIXE. La section est large et basse, la vue
       plein écran presque carrée : un même recul y donnerait un dessin qui
       remplit l'une et se perd dans l'autre. Il est donc CALCULÉ à chaque
       image, et « zoom » n'en est qu'un facteur. */
    var FOV = 0.72;
    var LIMITE = 1.52;                 /* 87°, juste sous la verticale */
    var azimut = -0.7, elevation = 0.52, zoom = 1;
    var plein = null, image = 0, tourneSeule = true;

    /* ── LA CAMÉRA VISE LE CENTRE DE LA BOÎTE, NON L'ORIGINE ─────────────
       L'origine est le fond de la fosse, posé là par la conversion pour que le
       terrain repose sur le plan zéro. Tourner autour d'elle ferait basculer le
       modèle de haut en bas à chaque tour, comme une balançoire. */
    var CENTRE = [(boite.min[0] + boite.max[0]) / 2,
                  (boite.min[1] + boite.max[1]) / 2,
                  (boite.min[2] + boite.max[2]) / 2];
    var COINS = [];
    for (var bx = 0; bx < 2; bx++) {
      for (var by = 0; by < 2; by++) {
        for (var bz = 0; bz < 2; bz++) {
          COINS.push([(bx ? boite.max[0] : boite.min[0]) - CENTRE[0],
                      (by ? boite.max[1] : boite.min[1]) - CENTRE[1],
                      (bz ? boite.max[2] : boite.min[2]) - CENTRE[2]]);
        }
      }
    }

    function base() {
      var ce = Math.cos(elevation), se = Math.sin(elevation);
      var ca = Math.cos(azimut), sa = Math.sin(azimut);
      return {
        droite: [ca, 0, -sa],
        haut: [-se * sa, ce, -se * ca],
        avant: [ce * sa, se, ce * ca],     /* du centre vers l'œil */
      };
    }

    /* ── LE RECUL EXACT, ET NON UNE SPHÈRE ENGLOBANTE ─────────────────────
       Le modèle est un disque très aplati : sa sphère englobante déborde de
       toutes parts au-dessus et au-dessous du vide, et l'ajuster reculerait la
       caméra de moitié pour cadrer de l'air.

       On projette donc les huit coins de sa VRAIE boîte. Chaque coin impose un
       recul minimal : à la distance d, sa profondeur vue vaut d moins sa
       composante le long de l'axe de visée, et il tient dans le cadre si son
       écart latéral ne dépasse pas cette profondeur multipliée par la tangente
       du demi-angle. Le plus exigeant des huit fixe le recul. */
    function recul(rapport) {
      var tH = Math.tan(FOV / 2) * rapport, tV = Math.tan(FOV / 2);
      var b = base();
      var d = 0;
      for (var i = 0; i < COINS.length; i++) {
        var p = COINS[i];
        var x = Math.abs(p[0] * b.droite[0] + p[1] * b.droite[1] + p[2] * b.droite[2]);
        var y = Math.abs(p[0] * b.haut[0] + p[1] * b.haut[1] + p[2] * b.haut[2]);
        var z = p[0] * b.avant[0] + p[1] * b.avant[1] + p[2] * b.avant[2];
        d = Math.max(d, z + x / tH, z + y / tV);
      }
      /* ── LE FILIGRANE A LE DROIT DE DÉBORDER, PAS LA VUE PLEIN ÉCRAN ───
         Le modèle est plat : cadré en entier, il laisse au-dessus et en dessous
         deux bandes de vide qui font paraître le dessin minuscule au milieu de
         sa section. En le rapprochant d'un tiers, ce sont ces bandes qui sont
         rognées, et le filigrane occupe la place qui lui est donnée.

         Au premier plan, où le visiteur oriente le modèle lui-même, la marge
         reste franche : il y examine une géométrie, pas un décor. */
      return d * 1.10 * (plein ? 0.86 : 0.66) * zoom;
    }

    function dimensionner() {
      var r = Math.min(window.devicePixelRatio || 1, 2);
      var l = Math.max(1, Math.round(toile.clientWidth * r));
      var h = Math.max(1, Math.round(toile.clientHeight * r));
      if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
    }

    function dessiner() {
      dimensionner();
      gl.viewport(0, 0, toile.width, toile.height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      var rapport = toile.width / toile.height;
      var d = recul(rapport);
      var b = base();
      var oeil = [CENTRE[0] + d * b.avant[0],
                  CENTRE[1] + d * b.avant[1],
                  CENTRE[2] + d * b.avant[2]];
      var mvp = multiplier(perspective(FOV, rapport, 0.02, 40),
                           regard(oeil, CENTRE, [0, 1, 0]));

      /* ── EN FILIGRANE, LE DESSIN SE RANGE À DROITE ────────────────────
         Le texte occupe la gauche de la section. Centré, le dessin passerait
         dessous et gênerait la lecture sans rien gagner ; décalé, les deux
         cohabitent et la page garde son sens de lecture.

         Le décalage se fait dans l'espace de découpe, après projection : on
         ajoute au X une fraction du W, ce qui déplace l'image à l'écran sans
         déformer la perspective ni bouger la caméra. Seuls les écrans larges
         y ont droit ; sur un téléphone, le texte occupe toute la largeur. */
      var decalage = (!plein && rapport > 1.7) ? 0.34 : 0;
      if (decalage) {
        for (var c = 0; c < 4; c++) mvp[c * 4] += decalage * mvp[c * 4 + 3];
      }
      gl.uniformMatrix4fv(uMvp, false, mvp);

      objets.forEach(function (o) {
        var reglage = COUCHES[o.couche];
        if (plein ? !affichee[o.couche] : !reglage.filigrane) return;

        var triangles = o.forme === 'triangles';
        gl.bindBuffer(gl.ARRAY_BUFFER, o.position);
        gl.enableVertexAttribArray(aPos);
        /* « normalisé » : la carte ramène elle-même l'entier court dans [0,1]. */
        gl.vertexAttribPointer(aPos, 3, gl.UNSIGNED_SHORT, true, 0, 0);

        if (triangles) {
          gl.bindBuffer(gl.ARRAY_BUFFER, o.normale);
          gl.enableVertexAttribArray(aNor);
          gl.vertexAttribPointer(aNor, 3, gl.FLOAT, false, 0, 0);
        } else {
          gl.disableVertexAttribArray(aNor);
          gl.vertexAttrib3f(aNor, 0, 1, 0);
        }

        /* ── LE JAUNE NE PARAÎT QUE SUR FOND SOMBRE ─────────────────────
           En filigrane, le fond de la section est clair, et le jaune de la
           charte y tombe à 1,6:1 : le dôme s'y effacerait. Tout y est donc
           dans le bleu, distingué par la densité du tracé et non par la
           teinte. Au premier plan, sur fond anthracite, chaque couche
           retrouve sa couleur, et le contraste avec elle. */
        var couleur = plein
          ? [reglage.couleur[0] / 255, reglage.couleur[1] / 255, reglage.couleur[2] / 255]
          : BLEU;
        gl.uniform3fv(uCouleur, couleur);
        gl.uniform1f(uUni, triangles ? 0 : 1);

        /* Chaque tracé a sa raison d'être plus ou moins présent. La surface de
           la fosse ne sert qu'à masquer ce qui passe dessous : elle reste la
           plus effacée. Ses arêtes portent les gradins, donc la lecture du
           relief. Les périmètres, eux, sont le sujet. */
        var opacite;
        if (plein) {
          if (triangles) opacite = 1;
          else if (o.couche === 'fosse') opacite = 0.5;
          else opacite = 0.92;
        } else {
          opacite = triangles ? 0.30 : (o.couche === 'dome' ? 0.42 : 0.22);
          /* ── SUR ÉCRAN ÉTROIT, LE FILIGRANE S'EFFACE ENCORE ──────────
             Sur écran large, le dessin est rangé à droite et le texte occupe
             la gauche : les deux ne se rencontrent pas. Sur téléphone, le
             texte tient toute la largeur et le dessin passe forcément
             dessous. Entre un décor et un texte qui se lit, c'est le décor
             qui cède. */
          if (!decalage) opacite *= 0.62;
        }
        gl.uniform1f(uOpacite, opacite);

        /* Les fils de fer n'écrivent pas dans le tampon de profondeur : leurs
           segments lointains masqueraient les proches, et un tracé transparent
           doit se voir de part en part. */
        gl.depthMask(triangles);
        if (reglage.traverse) gl.disable(gl.DEPTH_TEST);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, o.index);
        gl.drawElements(triangles ? gl.TRIANGLES : gl.LINES, o.nombre,
                        gl.UNSIGNED_SHORT, 0);
        if (reglage.traverse) gl.enable(gl.DEPTH_TEST);
      });
      gl.depthMask(true);

      if (cube) orienterCube();
    }

    /* ══ L'ANIMATION VERS UNE VUE ═════════════════════════════════════════
       Le passage est progressif, et non instantané. Sauter d'un point de vue à
       l'autre laisse le spectateur à reconstruire seul ce qui a bougé ; un
       mouvement de quatre dixièmes de seconde lui montre le lien entre les
       deux, ce qui est tout l'intérêt d'un cube de vue. */
    var vol = null;

    function allerVers(az, el) {
      /* Le chemin le plus court en azimut : sans ce repli, passer de 175° à
         -175° ferait faire à la scène un tour complet pour dix degrés. */
      var d = (az - azimut) % (2 * Math.PI);
      if (d > Math.PI) d -= 2 * Math.PI;
      if (d < -Math.PI) d += 2 * Math.PI;
      vol = { az0: azimut, el0: elevation, daz: d, del: el - elevation,
              debut: (performance && performance.now ? performance.now() : Date.now()) };
      tourneSeule = false;
      relancer();
    }

    function avancerVol(maintenant) {
      if (!vol) return;
      var t = Math.min(1, (maintenant - vol.debut) / 420);
      var e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;   /* adouci */
      azimut = vol.az0 + vol.daz * e;
      elevation = vol.el0 + vol.del * e;
      if (t >= 1) vol = null;
    }

    var sobre = window.matchMedia &&
                window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function boucle(maintenant) {
      image = 0;
      avancerVol(maintenant || (performance && performance.now ? performance.now() : Date.now()));
      var anime = !saisie && !vol && (plein ? tourneSeule : !sobre);
      if (anime) azimut += plein ? 0.0009 : 0.0016;
      dessiner();
      if (visible || plein) image = requestAnimationFrame(boucle);
    }
    function relancer() { if (!image) image = requestAnimationFrame(boucle); }

    /* ── LE RENDU S'ARRÊTE HORS DE L'ÉCRAN ───────────────────────────────
       Une boucle d'animation qui tourne sous un contenu qu'on ne regarde pas
       consomme la batterie sans que rien ne le montre. */
    var visible = false;
    hote.appendChild(toile);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entrees) {
        visible = entrees[0].isIntersecting;
        toile.classList.toggle('dc-vue', visible);
        if (visible) relancer();
      }, { rootMargin: '120px' }).observe(hote);
    } else {
      visible = true;
      toile.classList.add('dc-vue');
      relancer();
    }
    window.addEventListener('resize', relancer, { passive: true });

    /* ══ L'ORIENTATION À LA MAIN ═══════════════════════════════════════════
       Elle n'est branchée qu'au premier plan. En filigrane, la toile ne reçoit
       aucun événement : c'est la règle qui garde la page défilable au doigt. */
    var saisie = null, pince = 0;

    function point(e) {
      return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY }
                       : { x: e.clientX, y: e.clientY };
    }
    function ecart(e) {
      var a = e.touches[0], b = e.touches[1];
      return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    }

    function prise(e) {
      tourneSeule = false;
      vol = null;
      if (e.touches && e.touches.length === 2) { pince = ecart(e); saisie = null; return; }
      saisie = point(e);
    }
    function glisse(e) {
      if (e.touches && e.touches.length === 2 && pince) {
        var d = ecart(e);
        zoom = Math.max(0.55, Math.min(2.6, zoom * pince / d));
        pince = d;
        e.preventDefault();
        relancer();
        return;
      }
      if (!saisie) return;
      var p = point(e);
      azimut -= (p.x - saisie.x) * 0.006;
      elevation = Math.max(-LIMITE, Math.min(LIMITE, elevation + (p.y - saisie.y) * 0.005));
      saisie = p;
      e.preventDefault();
      relancer();
    }
    function lache() { saisie = null; pince = 0; }
    function molette(e) {
      tourneSeule = false;
      zoom = Math.max(0.55, Math.min(2.6, zoom * (e.deltaY > 0 ? 1.1 : 0.91)));
      e.preventDefault();
      relancer();
    }

    function brancher(actif) {
      var m = actif ? 'addEventListener' : 'removeEventListener';
      toile[m]('pointerdown', prise);
      toile[m]('pointermove', glisse);
      toile[m]('touchstart', prise, { passive: false });
      toile[m]('touchmove', glisse, { passive: false });
      window[m]('pointerup', lache);
      window[m]('touchend', lache);
      toile[m]('wheel', molette, { passive: false });
    }

    /* ══ LE CUBE DE VUE ════════════════════════════════════════════════════
       Six faces, six points de vue. Il tourne avec la caméra pour dire où l'on
       se trouve, et se clique pour y aller.

       ─── LES FACES SONT DES BOUTONS, NON UN DESSIN ────────────────────────
       Bâti en trois dimensions CSS, le cube garde six éléments cliquables,
       tabulables et énonçables. Dessiné dans la toile, il aurait fallu y
       ajouter un lancer de rayon pour savoir quelle face est sous le curseur,
       et rien n'en serait resté pour qui navigue au clavier. */
    var cube = null;

    /* Le nom des faces, leur transformation dans le cube, et le point de vue
       qu'elles commandent. L'azimut nul regarde depuis le SUD : la conversion
       oriente le X de la scène vers l'est et son Z vers le sud. */
    var FACES = [
      ['haut',  'rotateX(90deg)',   null,            LIMITE],
      ['bas',   'rotateX(-90deg)',  null,           -LIMITE],
      ['nord',  'rotateY(180deg)',  Math.PI,         0],
      ['sud',   '',                 0,               0],
      ['est',   'rotateY(90deg)',   Math.PI / 2,     0],
      ['ouest', 'rotateY(-90deg)', -Math.PI / 2,     0],
    ];

    function construireCube(cote) {
      var zone = document.createElement('div');
      zone.className = 'dc-fosse-cube-zone';
      var boite3d = document.createElement('div');
      boite3d.className = 'dc-fosse-cube';
      var demi = cote / 2;

      FACES.forEach(function (f, i) {
        var b = document.createElement('button');
        b.type = 'button';
        b.textContent = MOTS_VUES[i] || f[0];
        b.style.transform = (f[1] ? f[1] + ' ' : '') + 'translateZ(' + demi + 'px)';
        b.addEventListener('click', function () {
          allerVers(f[2] === null ? azimut : f[2], f[3]);
        });
        boite3d.appendChild(b);
      });
      zone.appendChild(boite3d);
      cube = boite3d;
      return zone;
    }

    /* ── LE CUBE SUIT LA CAMÉRA PAR SA MATRICE, NON PAR DEUX ANGLES ───────
       Écrire « rotateX(-élévation) rotateY(-azimut) » paraît plus simple, mais
       l'ordre des rotations et le sens des axes CSS, dont le Y descend, y
       laissent quatre combinaisons de signes dont une seule est juste, et rien
       à l'écran ne dit laquelle.

       On pose donc la matrice de la caméra elle-même, en changeant de repère :
       le Y de la scène monte, celui de CSS descend, d'où le renversement de la
       ligne et de la colonne du milieu. C'est exact par construction. */
    function orienterCube() {
      var b = base();
      var m = [
        [ b.droite[0], -b.droite[1],  b.droite[2]],
        [-b.haut[0],    b.haut[1],   -b.haut[2]],
        [ b.avant[0],  -b.avant[1],   b.avant[2]],
      ];
      cube.style.transform =
        'translateZ(' + (-cube.parentNode.clientWidth / 2) + 'px) matrix3d(' +
        [m[0][0], m[1][0], m[2][0], 0,
         m[0][1], m[1][1], m[2][1], 0,
         m[0][2], m[1][2], m[2][2], 0,
         0, 0, 0, 1].join(',') + ')';
    }

    /* ══ LE PANNEAU DES CALQUES ════════════════════════════════════════════ */

    function construireCalques() {
      var panneau = document.createElement('div');
      panneau.className = 'dc-fosse-calques';
      var titre = document.createElement('h3');
      titre.textContent = MOTS_COUCHES[0] || 'Layers';
      panneau.appendChild(titre);

      ORDRE.forEach(function (nom, i) {
        /* Une couche absente du jeu de données n'a pas de case : proposer
           d'afficher ce qui n'existe pas laisserait croire à une panne. */
        if (!presentes[nom]) return;
        var l = document.createElement('label');
        var c = document.createElement('input');
        c.type = 'checkbox';
        c.checked = affichee[nom];
        c.addEventListener('change', function () {
          affichee[nom] = c.checked;
          relancer();
        });
        /* La pastille dit la couleur ET le trait : pleine pour un trait plein,
           en anneau tireté pour un trait tireté. Deux couches de même couleur
           seraient autrement impossibles à distinguer dans la légende, alors
           qu'elles le sont dans le dessin. */
        var pastille = document.createElement('span');
        pastille.className = 'dc-fosse-pastille';
        var teinte = 'rgb(' + COUCHES[nom].couleur.join(',') + ')';
        if (COUCHES[nom].tirets) {
          pastille.style.border = '2px dashed ' + teinte;
        } else {
          pastille.style.background = teinte;
        }
        var texte = document.createElement('span');
        texte.textContent = MOTS_COUCHES[i + 1] || nom;
        l.appendChild(c); l.appendChild(pastille); l.appendChild(texte);
        panneau.appendChild(l);
      });
      return panneau;
    }

    /* ══ OUVRIR ET REFERMER ════════════════════════════════════════════════ */

    bouton.hidden = false;

    function ouvrir() {
      plein = document.createElement('div');
      plein.className = 'dc-fosse-plein';
      plein.setAttribute('role', 'dialog');
      plein.setAttribute('aria-modal', 'true');
      plein.setAttribute('aria-label', bouton.textContent);

      var fermer = document.createElement('button');
      fermer.type = 'button';
      fermer.className = 'dc-fosse-fermer';
      fermer.textContent = bouton.getAttribute('data-fermer') || 'Close';
      fermer.addEventListener('click', refermer);

      var aide = document.createElement('p');
      aide.className = 'dc-fosse-aide';
      aide.textContent = bouton.getAttribute('data-aide') || '';

      plein.appendChild(toile);
      plein.appendChild(construireCube(window.innerWidth < 720 ? 46 : 62));
      plein.appendChild(construireCalques());
      plein.appendChild(fermer);
      plein.appendChild(aide);
      document.body.appendChild(plein);
      /* La page ne doit pas défiler derrière la vue : sur téléphone, un
         glissement qui déborde de la toile ferait remonter le contenu. */
      document.body.style.overflow = 'hidden';
      tourneSeule = true;
      brancher(true);
      document.addEventListener('keydown', clavier);
      fermer.focus();
      relancer();
    }

    function refermer() {
      if (!plein) return;
      brancher(false);
      document.removeEventListener('keydown', clavier);
      hote.appendChild(toile);
      plein.remove();
      plein = null;
      cube = null;
      vol = null;
      zoom = 1;
      document.body.style.overflow = '';
      bouton.focus();
      relancer();
    }

    function clavier(e) { if (e.key === 'Escape') refermer(); }

    bouton.addEventListener('click', ouvrir);
  }
})();
"""

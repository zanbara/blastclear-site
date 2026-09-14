/* ════════════════════════════════════════════════════════════════════════════
   ANIMATIONS DE NAVIGATION.

   Tout ce fichier est facultatif : la page est complète et lisible sans lui.
   C'est la raison pour laquelle il pose lui-même la classe dc-anime sur <html>
   avant de masquer quoi que ce soit. Si le script ne s'exécute pas, la règle de
   départ ne s'applique jamais et rien ne reste invisible.
   ════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var douceur = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var racine = document.documentElement;

  // ══ APPARITION DES SECTIONS ══════════════════════════════════════════════

  var blocs = [].slice.call(document.querySelectorAll('[data-anime]'));

  if (!douceur && blocs.length && typeof IntersectionObserver === 'function') {
    racine.classList.add('dc-anime');

    // TOUT CE QUI EST DÉJÀ À L'ÉCRAN RESTE VISIBLE.
    // Masquer puis révéler le premier écran ferait clignoter la page à
    // l'ouverture, et sur un grand moniteur c'est la moitié du contenu qui
    // serait concernée. Le test porte donc sur la position réelle, pas sur le
    // rang du bloc.
    var hauteur = window.innerHeight || 800;
    var aRevelerr = [];
    blocs.forEach(function (b) {
      if (b.getBoundingClientRect().top < hauteur * 0.9) b.classList.add('dc-vu');
      else aRevelerr.push(b);
    });

    var guetteur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('dc-vu');
        guetteur.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    aRevelerr.forEach(function (b) { guetteur.observe(b); });

    // FILET DE SÉCURITÉ. Si un bloc échappait au guetteur, pour une raison
    // quelconque, il resterait invisible pour toujours. Au bout de quatre
    // secondes, on révèle tout : une animation ratée vaut mieux qu'une section
    // manquante.
    setTimeout(function () {
      blocs.forEach(function (b) { b.classList.add('dc-vu'); });
    }, 4000);
  }

  // ══ BARRE DE NAVIGATION ══════════════════════════════════════════════════

  var barre = document.querySelector('nav');
  var jauge = document.createElement('div');
  jauge.className = 'dc-progression';
  jauge.setAttribute('aria-hidden', 'true');
  document.body.appendChild(jauge);

  var enAttente = false;
  function auDefilement() {
    if (enAttente) return;
    enAttente = true;
    requestAnimationFrame(function () {
      enAttente = false;
      var y = window.pageYOffset || racine.scrollTop;
      if (barre) barre.classList.toggle('dc-defile', y > 40);
      var total = racine.scrollHeight - window.innerHeight;
      jauge.style.width = (total > 0 ? Math.min(100, (y / total) * 100) : 0) + '%';
    });
  }
  window.addEventListener('scroll', auDefilement, { passive: true });
  window.addEventListener('resize', auDefilement, { passive: true });
  auDefilement();

  // ══ COMPTEURS ════════════════════════════════════════════════════════════
  //
  // Le texte affiché n'est PAS reconstruit à partir du nombre : il est remis
  // tel quel à la fin. Les libellés valent « + 200 h », « 6-7 mois », « ~60 USD »
  // selon la langue, et les recomposer produirait des formes fautives dans
  // plusieurs d'entre elles.

  var compteurs = [].slice.call(document.querySelectorAll('.dc-compteur'));

  if (!douceur && compteurs.length && typeof IntersectionObserver === 'function') {
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (!e.isIntersecting) return;
        observateur.unobserve(e.target);
        animerCompteur(e.target);
      });
    }, { threshold: 0.6 });
    compteurs.forEach(function (c) { observateur.observe(c); });
  }

  function animerCompteur(el) {
    var texte = el.textContent;
    var m = texte.match(/\d+/);
    if (!m) return;
    var cible = parseInt(m[0], 10);
    if (!cible || cible > 100000) return;
    var debut = null;
    var duree = 900;
    function pas(t) {
      if (debut === null) debut = t;
      var p = Math.min(1, (t - debut) / duree);
      var douce = 1 - Math.pow(1 - p, 3);
      el.textContent = texte.replace(m[0], String(Math.round(cible * douce)));
      if (p < 1) requestAnimationFrame(pas);
      else el.textContent = texte;
    }
    requestAnimationFrame(pas);
  }

  // ══ MENU DES LANGUES ═════════════════════════════════════════════════════

  var declencheur = document.querySelector('[data-bascule-langues]');
  var panneau = document.getElementById('panneau-langues');

  if (declencheur && panneau) {
    declencheur.setAttribute('aria-expanded', 'false');
    declencheur.setAttribute('aria-controls', 'panneau-langues');

    declencheur.addEventListener('click', function (e) {
      e.stopPropagation();
      var ouvert = !panneau.hidden;
      panneau.hidden = ouvert;
      declencheur.setAttribute('aria-expanded', ouvert ? 'false' : 'true');
    });

    document.addEventListener('click', function (e) {
      if (panneau.hidden) return;
      if (panneau.contains(e.target) || declencheur.contains(e.target)) return;
      panneau.hidden = true;
      declencheur.setAttribute('aria-expanded', 'false');
    });

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || panneau.hidden) return;
      panneau.hidden = true;
      declencheur.setAttribute('aria-expanded', 'false');
      declencheur.focus();
    });
  }

  // ══ FOND BALISTIQUE : LES TRAJECTOIRES SE TRACENT EN BOUCLE ══════════════
  //
  // Chaque courbe se dessine depuis le point de tir vers son point de chute,
  // les dix se succèdent, puis le cycle recommence. C'est la projection d'un
  // bloc suivant sa trajectoire, et c'est exactement ce que le logiciel calcule.
  //
  // ─── LE SENS DU TRACÉ N'EST PAS CELUI DU FICHIER ─────────────────────────
  // Rien n'oblige un dessinateur à décrire une courbe dans le sens où elle est
  // parcourue : plusieurs de ces tracés partent du point de chute et remontent
  // vers le tir. Les dessiner tels quels donnerait des blocs qui reviennent en
  // arrière. On repère donc le point de tir, là où les dix courbes se
  // rejoignent, et on inverse celles qui en partent à l'envers.

  var traits = document.getElementById('traits-balistiques');

  if (traits) {
    var courbes = [].slice.call(traits.querySelectorAll('path'));
    var parentTraits = traits.closest('.dc-zone-traits') || traits.parentElement;

    // Le point de tir : celui des vingt extrémités qui a le plus de voisines
    // proches. Une moyenne serait attirée par les points de chute, qui sont
    // dispersés ; ce comptage ne l'est pas.
    function pointDeTir() {
      var bouts = [];
      courbes.forEach(function (c) {
        var L = c.getTotalLength();
        bouts.push(c.getPointAtLength(0), c.getPointAtLength(L));
      });
      var meilleur = bouts[0], score = -1;
      bouts.forEach(function (a) {
        var n = 0;
        bouts.forEach(function (b) {
          var dx = a.x - b.x, dy = a.y - b.y;
          if (dx * dx + dy * dy < 40000) n++;   // 200 unités de rayon
        });
        if (n > score) { score = n; meilleur = a; }
      });
      return meilleur;
    }

    // ── CE QUE LE SCRIPT DÉCLARE, ET QUE LE CSS ANIME ────────────────────
    // Une longueur, un sens, un retard par courbe. Rien d'autre : la boucle,
    // le rythme et l'arrêt sur réglage système sont dans design.css.

    var CYCLE = 7.5;      // secondes, un tour complet
    var ECART = 0.19;     // secondes entre deux départs

    if (courbes.length) {
      var tir = pointDeTir();
      courbes.forEach(function (c, i) {
        var L = c.getTotalLength();
        var debut = c.getPointAtLength(0);
        var fin = c.getPointAtLength(L);
        var dDebut = Math.pow(debut.x - tir.x, 2) + Math.pow(debut.y - tir.y, 2);
        var dFin = Math.pow(fin.x - tir.x, 2) + Math.pow(fin.y - tir.y, 2);
        // Un décalage NÉGATIF fait apparaître le trait par l'autre bout : c'est
        // ce qui remet dans le sens du tir les courbes décrites à l'envers.
        var sens = dDebut <= dFin ? 1 : -1;
        c.style.setProperty('--L', L.toFixed(1));
        c.style.setProperty('--depart', (L * sens).toFixed(1));
        c.style.setProperty('--retard', (i * ECART).toFixed(2) + 's');
        c.style.setProperty('--cycle', CYCLE + 's');
      });
    }

    traits.style.opacity = '1';

    if (typeof IntersectionObserver === 'function') {
      new IntersectionObserver(function (entrees) {
        entrees.forEach(function (e) {
          traits.classList.toggle('dc-tire', e.isIntersecting);
        });
      }, { threshold: 0.12 }).observe(parentTraits);
    } else {
      traits.classList.add('dc-tire');
    }

    // La dérive lente pendant le défilement, conservée de la maquette : elle
    // donne de la profondeur sans concurrencer le tracé.
    if (!douceur) {
      var enCours = false;
      var placerTraits = function () {
        if (enCours) return;
        enCours = true;
        requestAnimationFrame(function () {
          enCours = false;
          var r = parentTraits.getBoundingClientRect();
          var vh = window.innerHeight || 800;
          var p = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
          traits.style.transform = 'translate(-50%,' + (-50 + (p - 0.5) * 10).toFixed(2) +
            '%) scale(' + (0.95 + p * 0.08).toFixed(3) + ')';
        });
      };
      window.addEventListener('scroll', placerTraits, { passive: true });
      window.addEventListener('resize', placerTraits, { passive: true });
      placerTraits();
    }
  }

  // ══ CARROUSEL ════════════════════════════════════════════════════════════
  //
  // La bande défile déjà toute seule grâce à scroll-snap. Ce bloc ne fait que
  // COMMANDER ce défilement : il ne réimplémente pas un deuxième mécanisme de
  // déplacement, ce qui évite d'avoir à tenir deux positions d'accord.

  var carrousel = document.querySelector('[data-carrousel]');

  if (carrousel) {
    var bande = carrousel.querySelector('.dc-bande');
    var vues = [].slice.call(carrousel.querySelectorAll('.dc-vue'));
    var pastilles = [].slice.call(carrousel.querySelectorAll('.dc-pastille'));
    var recule = carrousel.querySelector('[data-recule]');
    var avance = carrousel.querySelector('[data-avance]');
    var courante = 0;
    var minuteur = null;

    function allerA(i, doux) {
      if (!vues.length) return;
      courante = Math.max(0, Math.min(vues.length - 1, i));
      bande.scrollTo({ left: vues[courante].offsetLeft - bande.offsetLeft,
                       behavior: (doux === false || douceur) ? 'auto' : 'smooth' });
      marquer();
    }

    function marquer() {
      pastilles.forEach(function (p, i) {
        p.setAttribute('aria-current', i === courante ? 'true' : 'false');
      });
      // Les flèches se désactivent aux extrémités : une flèche qui ne fait rien
      // laisse croire que la page est bloquée.
      if (recule) recule.disabled = courante === 0;
      if (avance) avance.disabled = courante === vues.length - 1;
    }

    // La position vraie est celle de la barre de défilement, pas celle qu'on
    // croit avoir demandée : l'utilisateur peut faire glisser à la main.
    var enLecture = false;
    bande.addEventListener('scroll', function () {
      if (enLecture) return;
      enLecture = true;
      requestAnimationFrame(function () {
        enLecture = false;
        var centre = bande.scrollLeft + bande.clientWidth / 2;
        var meilleure = 0, ecart = Infinity;
        vues.forEach(function (v, i) {
          var d = Math.abs((v.offsetLeft - bande.offsetLeft) + v.clientWidth / 2 - centre);
          if (d < ecart) { ecart = d; meilleure = i; }
        });
        if (meilleure !== courante) { courante = meilleure; marquer(); }
      });
    }, { passive: true });

    if (recule) recule.addEventListener('click', function () { arreter(); allerA(courante - 1); });
    if (avance) avance.addEventListener('click', function () { arreter(); allerA(courante + 1); });
    pastilles.forEach(function (p) {
      p.addEventListener('click', function () {
        arreter();
        allerA(parseInt(p.getAttribute('data-va'), 10));
      });
    });

    bande.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault();
      arreter();
      allerA(courante + (e.key === 'ArrowRight' ? 1 : -1));
    });

    // ── L'AVANCE AUTOMATIQUE S'ARRÊTE DÈS QU'ON S'EN OCCUPE ────────────────
    // Un carrousel qui repart pendant qu'on lit une légende est la faute la
    // plus courante du genre. Ici il s'arrête au survol, au focus, dès la
    // première commande, et ne repart jamais de lui-même.
    function tourner() {
      if (douceur) return;
      minuteur = setInterval(function () {
        allerA(courante >= vues.length - 1 ? 0 : courante + 1);
      }, 6000);
    }
    function arreter() {
      if (minuteur) { clearInterval(minuteur); minuteur = null; }
    }

    carrousel.addEventListener('mouseenter', arreter);
    carrousel.addEventListener('focusin', arreter);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) arreter();
    });

    marquer();

    // On ne lance la rotation que lorsque le carrousel est à l'écran : animer
    // hors champ ne sert à personne et réveille le processeur pour rien.
    if (!douceur && typeof IntersectionObserver === 'function') {
      new IntersectionObserver(function (entrees, obs) {
        entrees.forEach(function (e) {
          if (!e.isIntersecting) return;
          obs.disconnect();
          tourner();
        });
      }, { threshold: 0.5 }).observe(carrousel);
    }
  }

  // ══ FORMULAIRE ═══════════════════════════════════════════════════════════
  //
  // Voir rectifier_formulaire dans outils/convertir_design.py : sans service de
  // collecte configuré, la demande part par le logiciel de messagerie du
  // visiteur plutôt que vers un tiers choisi à sa place.

  // ── AVEC UN SERVICE DE COLLECTE : ENVOI EN ARRIÈRE-PLAN ─────────────────
  //
  // On poste nous-mêmes plutôt que de laisser le navigateur soumettre le
  // formulaire : une soumission ordinaire afficherait la réponse brute du
  // service, une page blanche portant du JSON. Ici le visiteur ne voit que la
  // page de remerciement.
  //
  // Le mode « sans-échec » (no-cors) est employé à dessein : une application web
  // Google Apps Script ne renvoie pas les en-têtes qui autoriseraient la lecture
  // de sa réponse. On ne peut donc pas la lire, et on ne cherche pas à le faire.
  // En contrepartie, une erreur côté service ne peut pas être détectée ici :
  // c'est le script lui-même qui prévient par courriel s'il échoue.

  var collecte = document.querySelector('form[data-collecte]');

  if (collecte) {
    collecte.addEventListener('submit', function (e) {
      e.preventDefault();
      if (typeof collecte.reportValidity === 'function' && !collecte.reportValidity()) return;

      var bouton = collecte.querySelector('[type="submit"]');
      if (bouton) { bouton.disabled = true; bouton.style.opacity = '0.6'; }

      fetch(collecte.getAttribute('action'), {
        method: 'POST',
        mode: 'no-cors',
        body: new FormData(collecte)
      }).then(function () {
        window.location.href = 'merci.html';
      })['catch'](function () {
        // L'envoi a peut-être abouti malgré tout : on conduit quand même à la
        // page de remerciement plutôt que de laisser le visiteur sans réponse.
        window.location.href = 'merci.html';
      });
    });
  }

  var formulaire = document.querySelector('form[data-courriel]');

  if (formulaire && !formulaire.getAttribute('action')) {
    formulaire.addEventListener('submit', function (e) {
      e.preventDefault();

      // La validation native passe d'abord : sans elle, une demande partirait
      // sans adresse de réponse et serait perdue.
      if (typeof formulaire.reportValidity === 'function' && !formulaire.reportValidity()) return;

      var lignes = [];
      [].slice.call(formulaire.querySelectorAll('input,textarea,select')).forEach(function (champ) {
        if (champ.type === 'submit' || champ.type === 'button' || champ.type === 'hidden') return;
        var etiquette = champ.getAttribute('name') || champ.getAttribute('placeholder') || '';
        if (!etiquette) return;
        lignes.push(etiquette + ' : ' + (champ.value || ''));
      });

      window.location.href = 'mailto:' + formulaire.getAttribute('data-courriel') +
        '?subject=' + encodeURIComponent('BlastClear - demande de demonstration') +
        '&body=' + encodeURIComponent(lignes.join('\r\n'));

      // ── LA PAGE DE REMERCIEMENT VIENT APRÈS, ET NON AUSSITÔT ─────────────
      //
      // Le délai n'est pas cosmétique : le navigateur doit avoir le temps de
      // passer la main au logiciel de messagerie. Naviguer immédiatement
      // annulerait cette ouverture sur certains navigateurs, et la demande ne
      // partirait jamais.
      //
      // C'est une page, et non un panneau qui se dévoile : elle a sa propre
      // adresse, donc elle se partage, se met en favori, et servira de
      // destination telle quelle le jour où un service de collecte remplacera
      // l'ouverture de la messagerie.
      setTimeout(function () { window.location.href = 'merci.html'; }, 1200);
    });
  }
})();


/* ════════════════════════════════════════════════════════════════════════════
   « CETTE PAGE EXISTE DANS VOTRE LANGUE »

   Le bandeau ne redirige jamais : il propose. La page demandée reste celle qui
   s'affiche, ce qui vaut pour un lien partagé comme pour un robot d'indexation.

   IL SE TAIT DANS TROIS CAS. Si le visiteur a déjà choisi une langue, s'il a
   déjà refusé la proposition, et si sa langue est celle de la page. Un bandeau
   qui revient à chaque visite se referme sans être lu.
   ════════════════════════════════════════════════════════════════════════════ */
(function () {
  var TEXTES = {"fr":["Ce site existe en français.","Voir en français","Fermer"],"en":["This site is available in English.","View in English","Close"],"es":["Este sitio está disponible en español.","Ver en español","Cerrar"],"pt":["Este site está disponível em português.","Ver em português","Fechar"],"it":["Questo sito è disponibile in italiano.","Vedi in italiano","Chiudi"],"de":["Diese Website ist auf Deutsch verfügbar.","Auf Deutsch ansehen","Schließen"],"nl":["Deze website is beschikbaar in het Nederlands.","Bekijk in het Nederlands","Sluiten"],"sv":["Den här webbplatsen finns på svenska.","Visa på svenska","Stäng"],"no":["Dette nettstedet finnes på norsk.","Se på norsk","Lukk"],"da":["Dette websted findes på dansk.","Se på dansk","Luk"],"af":["Hierdie werf is in Afrikaans beskikbaar.","Bekyk in Afrikaans","Maak toe"],"tr":["Bu site Türkçe olarak mevcuttur.","Türkçe görüntüle","Kapat"],"zh":["本网站提供中文版。","查看中文版","关闭"]};

  /* Les codes que le navigateur emploie ne sont pas tous les nôtres : le
     norvégien se déclare « nb » ou « nn » selon la variante écrite, et le chinois
     porte sa région. On ne garde que les deux premières lettres, puis on traduit
     les variantes connues. */
  var VARIANTES = { nb: 'no', nn: 'no' };

  function memoire(cle) {
    try { return localStorage.getItem(cle); } catch (e) { return null; }
  }
  function retenir(cle, valeur) {
    try { localStorage.setItem(cle, valeur); } catch (e) { /* navigation privée */ }
  }

  var courante = (document.documentElement.lang || 'en').toLowerCase();
  var declaree = (navigator.language || '').slice(0, 2).toLowerCase();
  var cible = VARIANTES[declaree] || declaree;

  if (!TEXTES[cible] || cible === courante) return;
  if (memoire('bc-langue')) return;          // le visiteur a déjà tranché
  if (memoire('bc-banniere') === 'non') return;

  var t = TEXTES[cible];
  var fichier = location.pathname.split('/').pop() || '';

  var barre = document.createElement('div');
  barre.className = 'dc-banniere';
  barre.setAttribute('lang', cible);

  var phrase = document.createElement('span');
  phrase.textContent = t[0];

  var lien = document.createElement('a');
  lien.href = '../' + cible + '/' + fichier;
  lien.textContent = t[1];
  lien.addEventListener('click', function () { retenir('bc-langue', cible); });

  var fermer = document.createElement('button');
  fermer.type = 'button';
  fermer.className = 'dc-banniere-fermer';
  fermer.setAttribute('aria-label', t[2]);
  fermer.textContent = '\u00D7';
  fermer.addEventListener('click', function () {
    retenir('bc-banniere', 'non');
    barre.remove();
  });

  barre.appendChild(phrase);
  barre.appendChild(lien);
  barre.appendChild(fermer);

  /* Le bandeau se pose AVANT la barre de navigation, donc tout en haut du cadre.
     Posé après, il se glisserait sous une barre collante et resterait invisible. */
  var nav = document.querySelector('nav');
  if (nav && nav.parentNode) nav.parentNode.insertBefore(barre, nav);

  /* Le choix de langue fait à la main, dans le sélecteur de la barre, vaut
     décision : il évite au bandeau de reparaître à la page suivante. */
  [].slice.call(document.querySelectorAll('.dc-langues-panneau a[href^="../"]'))
    .forEach(function (a) {
      a.addEventListener('click', function () {
        var m = a.getAttribute('href').match(/^\.\.\/([a-z]{2})\//);
        if (m) retenir('bc-langue', m[1]);
      });
    });
})();

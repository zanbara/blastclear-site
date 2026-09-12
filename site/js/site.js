/* ════════════════════════════════════════════════════════════════════════════════
   BLASTCLEAR — LE PEU DE SCRIPT QUE LE SITE EMPLOIE

   Le site doit rester entièrement lisible sans JavaScript : toutes les pages sont
   du HTML servi tel quel, tous les liens sont de vrais liens. Ce fichier n'ajoute
   que deux commodités, et son absence ne casse rien.

   1. Le menu replié sur petit écran. Sans script, la barre de navigation reste
      affichée en permanence, ce qui est simplement moins joli.
   2. La mémoire de la langue choisie, pour que la racine du site n'y renvoie pas
      chaque fois au français.
   ════════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ══ MENU REPLIÉ ════════════════════════════════════════════════════════════

  var bouton = document.querySelector('.menu-bouton');
  var nav = document.getElementById('nav-principale');

  if (bouton && nav) {
    bouton.addEventListener('click', function () {
      var ouvert = nav.getAttribute('data-ouvert') === 'oui';
      nav.setAttribute('data-ouvert', ouvert ? 'non' : 'oui');
      bouton.setAttribute('aria-expanded', ouvert ? 'false' : 'true');
      bouton.setAttribute('aria-label', ouvert ? 'Ouvrir le menu' : 'Fermer le menu');
    });

    // Échap referme le menu et rend le focus au bouton : sans cela, un visiteur
    // au clavier se retrouve enfermé dans une liste qu'il ne peut plus quitter.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.getAttribute('data-ouvert') === 'oui') {
        nav.setAttribute('data-ouvert', 'non');
        bouton.setAttribute('aria-expanded', 'false');
        bouton.focus();
      }
    });
  }

  // ══ MÉMOIRE DE LA LANGUE ═══════════════════════════════════════════════════
  //
  // localStorage lève dans une fenêtre privée, et quand les données de site sont
  // bloquées. Le try/catch n'est donc pas une précaution de style : sans lui, une
  // exception ici interromprait le script et laisserait le menu inerte.

  function retenirLangue(code) {
    try { localStorage.setItem('bc-langue', code); } catch (e) { /* sans effet */ }
  }

  var langueCourante = document.documentElement.getAttribute('lang');
  if (langueCourante === 'fr' || langueCourante === 'en') {
    retenirLangue(langueCourante);
  }

  Array.prototype.forEach.call(
    document.querySelectorAll('.langue a[hreflang]'),
    function (lien) {
      lien.addEventListener('click', function () {
        retenirLangue(lien.getAttribute('hreflang'));
      });
    }
  );
})();

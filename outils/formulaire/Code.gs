/**
 * ════════════════════════════════════════════════════════════════════════════════
 *  RÉCEPTION DES DEMANDES DE DÉMONSTRATION — BLASTCLEAR
 *
 *  Ce script vit dans une feuille Google, publié en application web. Le formulaire
 *  du site lui envoie ses champs ; il écrit une ligne dans la feuille et prévient
 *  par courriel.
 *
 *  ─── POURQUOI CE MONTAGE PLUTÔT QU'UN SERVICE DE COLLECTE ────────────────────
 *  Les coordonnées d'un prospect sont une donnée commerciale. Ici elles ne quittent
 *  pas le compte Google du destinataire : pas d'intermédiaire, pas d'abonnement,
 *  pas de quota mensuel, et rien à réclamer à quiconque le jour où l'on change
 *  d'avis. La contrepartie est ce fichier, à installer une fois.
 *
 *  ─── CE QUE LE SCRIPT NE FAIT PAS ────────────────────────────────────────────
 *  Il ne stocke aucun secret et n'expose aucune donnée : doGet répond une page
 *  vide. Seul doPost écrit, et il n'écrit que dans la feuille à laquelle il est
 *  attaché.
 *
 *  INSTALLATION : voir INSTALLATION.md, dans le même dossier.
 * ════════════════════════════════════════════════════════════════════════════════
 */

// ══ RÉGLAGES ══════════════════════════════════════════════════════════════════

/** Destinataires de la notification. Le premier reçoit, les autres en copie. */
var DESTINATAIRES = [
  'contact@blastclear.com',
  'anouar.zanbara@gmail.com'
];

/** Nom de l'onglet qui reçoit les lignes. Créé s'il n'existe pas. */
var ONGLET = 'Demandes';

/**
 * Jeton partagé avec la page.
 *
 * IL NE PROTÈGE PAS UN SECRET, il filtre le bruit. Une application web Google
 * ouverte à tous reçoit tôt ou tard des envois automatisés ; sans ce jeton, ils
 * atterriraient dans la feuille et dans la boîte de réception. Le jeton voyage en
 * clair dans la page, donc il n'empêche personne de le lire : il empêche seulement
 * d'écrire sans l'avoir lu.
 *
 * À REMPLACER par une chaîne de votre choix, et à reporter à l'identique dans
 * outils/convertir_design.py, constante JETON_FORMULAIRE.
 */
var JETON = 'REMPLACER_PAR_UNE_CHAINE_A_VOUS';

// ══ COLONNES ══════════════════════════════════════════════════════════════════
//
// L'ordre fait foi : c'est lui qui fixe les colonnes de la feuille. Ajouter un
// champ se fait EN FIN DE LISTE, jamais au milieu, sous peine de décaler toutes
// les lignes déjà enregistrées.

var COLONNES = [
  ['horodatage',   'Date et heure'],
  ['langue',       'Langue de la page'],
  ['nom',          'Nom et prénom'],
  ['societe',      'Société'],
  ['poste',        'Poste'],
  ['email',        'Courriel'],
  ['indicatif',    'Indicatif'],
  ['telephone',    'Téléphone'],
  ['message',      'Message'],
  ['page',         'Page d\'origine'],
  ['navigateur',   'Navigateur'],
];

// ══ POINTS D'ENTRÉE ═══════════════════════════════════════════════════════════

function doGet() {
  // Une application web doit répondre à GET, sinon Google refuse de la publier.
  // Elle ne rend rien : il n'y a rien à consulter ici.
  return ContentService.createTextOutput('');
}

function doPost(e) {
  try {
    var champs = (e && e.parameter) ? e.parameter : {};

    if (String(champs.jeton || '') !== JETON) {
      return reponse({ ok: false, motif: 'jeton' });
    }

    // Champ-piège : invisible dans la page, donc toujours vide chez un humain.
    // Un automate remplit tout ce qu'il trouve et se signale ainsi lui-même.
    if (String(champs.site || '').length > 0) {
      return reponse({ ok: true });   // on acquiesce sans rien écrire
    }

    if (!String(champs.email || '').match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) {
      return reponse({ ok: false, motif: 'courriel' });
    }

    var ligne = ecrireLigne(champs);
    notifier(champs, ligne);
    return reponse({ ok: true });

  } catch (err) {
    // On avertit plutôt que d'échouer en silence : une demande perdue ne se
    // rattrape pas, et personne ne va relire les journaux du script.
    try {
      MailApp.sendEmail(DESTINATAIRES[0],
        'BlastClear — échec de réception d\'une demande',
        'Le script a levé une erreur :\n\n' + err + '\n\n' + (err.stack || ''));
    } catch (ignore) {}
    return reponse({ ok: false, motif: 'erreur' });
  }
}

// ══ ÉCRITURE ══════════════════════════════════════════════════════════════════

function ecrireLigne(champs) {
  var classeur = SpreadsheetApp.getActiveSpreadsheet();
  var feuille = classeur.getSheetByName(ONGLET);

  if (!feuille) {
    feuille = classeur.insertSheet(ONGLET);
    var entetes = COLONNES.map(function (c) { return c[1]; });
    feuille.appendRow(entetes);
    var tete = feuille.getRange(1, 1, 1, entetes.length);
    tete.setFontWeight('bold').setBackground('#25498A').setFontColor('#ffffff');
    feuille.setFrozenRows(1);
    feuille.setColumnWidth(1, 150);
    feuille.setColumnWidth(COLONNES.length - 2, 420);   // Message
  }

  var valeurs = COLONNES.map(function (c) {
    if (c[0] === 'horodatage') return new Date();
    return String(champs[c[0]] || '');
  });

  feuille.appendRow(valeurs);
  return feuille.getLastRow();
}

// ══ NOTIFICATION ══════════════════════════════════════════════════════════════

function notifier(champs, numeroLigne) {
  var societe = String(champs.societe || '').trim() || 'société non précisée';
  var nom = String(champs.nom || '').trim() || 'nom non précisé';

  // L'objet porte l'information : on doit pouvoir trier sa boîte sans ouvrir.
  var objet = 'Demande de démo — ' + nom + ' — ' + societe;

  var lignes = [];
  COLONNES.forEach(function (c) {
    if (c[0] === 'horodatage') return;
    var v = String(champs[c[0]] || '').trim();
    if (v) lignes.push(c[1] + ' : ' + v);
  });

  var corps =
    'Nouvelle demande de démonstration.\n\n' +
    lignes.join('\n') + '\n\n' +
    'Ligne ' + numeroLigne + ' de la feuille :\n' +
    SpreadsheetApp.getActiveSpreadsheet().getUrl() + '\n';

  // replyTo pointe le prospect : répondre depuis la notification écrit
  // directement à la bonne personne, sans recopier son adresse.
  MailApp.sendEmail({
    to: DESTINATAIRES[0],
    cc: DESTINATAIRES.slice(1).join(','),
    replyTo: String(champs.email || DESTINATAIRES[0]),
    subject: objet,
    body: corps
  });
}

// ══ RÉPONSE ═══════════════════════════════════════════════════════════════════

function reponse(objet) {
  return ContentService
    .createTextOutput(JSON.stringify(objet))
    .setMimeType(ContentService.MimeType.JSON);
}

// ══ ESSAI ═════════════════════════════════════════════════════════════════════

/**
 * À lancer une fois depuis l'éditeur, après installation : écrit une ligne d'essai
 * et envoie la notification. C'est aussi ce qui déclenche la demande
 * d'autorisations de Google, qu'il faut accorder avant que le formulaire ne
 * fonctionne.
 */
function essai() {
  var faux = {
    jeton: JETON,
    langue: 'fr',
    nom: 'Essai Essai',
    societe: 'Essai',
    poste: 'Ingénieur forage et sautage',
    email: DESTINATAIRES[DESTINATAIRES.length - 1],
    indicatif: '+226',
    telephone: '70 00 00 00',
    message: 'Ligne d\'essai produite par la fonction essai().',
    page: 'essai',
    navigateur: 'éditeur Apps Script'
  };
  var n = ecrireLigne(faux);
  notifier(faux, n);
  Logger.log('Ligne ' + n + ' écrite, notification envoyée.');
}

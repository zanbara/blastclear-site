#!/usr/bin/env python3
"""
CONVERSION DES CANEVAS CLAUDE DESIGN EN SITE STATIQUE PUBLIABLE.

─── CE QUE SONT LES FICHIERS SOURCES, ET POURQUOI ON NE LES PUBLIE PAS ─────────
Un fichier .dc.html n'est pas une page : c'est un composant pour l'éditeur Claude
Design. Il contient des marqueurs {{ }} résolus à l'exécution, des conditions
<sc-if>, des attributs style-hover, et il dépend de support.js. La variante
« hors ligne » fournie est un paquet auto-extractible de 1,5 Mo qui reconstruit
tout cela dans le navigateur : elle exige JavaScript pour afficher le moindre
texte, ne présente rien à un moteur de recherche, et fait dépendre une page
commerciale d'un moteur de rendu tiers.

Ce script produit donc, à partir des mêmes canevas, du HTML ordinaire : lisible
sans JavaScript, indexable, et qui ne dépend de rien.

─── CE QUI CHANGE PAR RAPPORT À LA MAQUETTE, ET SUR QUELLE DÉCISION ────────────
1. LA PALETTE PASSE À LA CHARTE. La maquette emploie le bleu nuit #001F4D et
   l'ambre #FFB700 du brief marketing ; la charte graphique du logo impose le
   bleu #25498A et le jaune #FDC30E. Décision prise : la charte fait foi, pour
   que le site, le logiciel, le logo et les plans disent la même chose.
2. LA POLICE PASSE À POPPINS, pour la même raison. Les libellés qu'IBM Plex Mono
   portait en capitales interlettrées deviennent du Poppins en capitales
   interlettrées, ce que la charte prévoit explicitement pour les mentions.
3. LA SECTION LICENCE N'EST PAS PUBLIÉE. C'était déjà le réglage par défaut de
   la maquette (afficherTarifs = false).
4. LA PHRASE SUR L'ABSENCE D'INCIDENT EST RETIRÉE, et le titre de la section de
   résultats devient « gains estimés ». Affirmer publiquement qu'aucun incident
   n'est survenu engage l'éditeur le jour où il en survient un.

─── CE QUE LE SCRIPT AJOUTE ────────────────────────────────────────────────────
Les animations de navigation demandées : apparition des sections au défilement,
barre de navigation qui se resserre, compteurs qui s'incrémentent, survols. Tout
est désactivé quand le système déclare préférer les animations réduites, et rien
n'est nécessaire à la lecture.

Usage :
    python outils/convertir_design.py
"""

from __future__ import annotations

import html as htmlmod
import pathlib
import re
import shutil
import unicodedata

from pourquoi import POURQUOI

RACINE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = RACINE / 'design' / 'BlastClear v2.0 flyer'
SITE = RACINE / 'site'

# ══ LES LANGUES ════════════════════════════════════════════════════════════════
# Le canevas français n'a pas de suffixe ; les autres portent le code en deux
# lettres majuscules. Le titre de la section de résultats et sa note sont
# réécrits ici, parce que la maquette y affirmait des faits qui ne seront pas
# publiés tels quels.

LANGUES: dict[str, dict[str, str]] = {
    'fr': {'suffixe': '', 'locale': 'fr_FR', 'nom': 'Français',
           'resultats': 'Gains estimés',
           'note': "Estimations établies sur une exploitation à ciel ouvert. Les gains réels dépendent du contexte du site."},
    'en': {'suffixe': ' EN', 'locale': 'en_US', 'nom': 'English',
           'resultats': 'Estimated gains',
           'note': "Estimates based on one open-pit operation. Actual gains depend on site context."},
    'es': {'suffixe': ' ES', 'locale': 'es_ES', 'nom': 'Español',
           'resultats': 'Beneficios estimados',
           'note': "Estimaciones basadas en una explotación a cielo abierto. Los beneficios reales dependen del contexto del emplazamiento."},
    'pt': {'suffixe': ' PT', 'locale': 'pt_PT', 'nom': 'Português',
           'resultats': 'Ganhos estimados',
           'note': "Estimativas baseadas numa exploração a céu aberto. Os ganhos reais dependem do contexto do local."},
    'it': {'suffixe': ' IT', 'locale': 'it_IT', 'nom': 'Italiano',
           'resultats': 'Guadagni stimati',
           'note': "Stime basate su una coltivazione a cielo aperto. I guadagni effettivi dipendono dal contesto del sito."},
    'de': {'suffixe': ' DE', 'locale': 'de_DE', 'nom': 'Deutsch',
           'resultats': 'Geschätzte Einsparungen',
           'note': "Schätzungen auf Basis eines Tagebaubetriebs. Die tatsächlichen Einsparungen hängen vom Standort ab."},
    'nl': {'suffixe': ' NL', 'locale': 'nl_NL', 'nom': 'Nederlands',
           'resultats': 'Geschatte winst',
           'note': "Schattingen op basis van één dagbouwmijn. De werkelijke winst hangt af van de situatie ter plaatse."},
    'sv': {'suffixe': ' SV', 'locale': 'sv_SE', 'nom': 'Svenska',
           'resultats': 'Uppskattade vinster',
           'note': "Uppskattningar baserade på ett dagbrott. De faktiska vinsterna beror på förhållandena på platsen."},
    'no': {'suffixe': ' NO', 'locale': 'nb_NO', 'nom': 'Norsk',
           'resultats': 'Estimerte gevinster',
           'note': "Estimater basert på ett dagbrudd. Faktiske gevinster avhenger av forholdene på stedet."},
    'da': {'suffixe': ' DA', 'locale': 'da_DK', 'nom': 'Dansk',
           'resultats': 'Estimerede gevinster',
           'note': "Estimater baseret på ét åbent brud. De faktiske gevinster afhænger af forholdene på stedet."},
    'af': {'suffixe': ' AF', 'locale': 'af_ZA', 'nom': 'Afrikaans',
           'resultats': 'Geraamde winste',
           'note': "Ramings gebaseer op een oopgroefmyn. Werklike winste hang af van die terrein se omstandighede."},
    'tr': {'suffixe': ' TR', 'locale': 'tr_TR', 'nom': 'Türkçe',
           'resultats': 'Tahmini kazanımlar',
           'note': "Tahminler tek bir açık ocak işletmesine dayanmaktadır. Gerçek kazanımlar sahaya göre değişir."},
    'zh': {'suffixe': ' ZH', 'locale': 'zh_CN', 'nom': '中文',
           'resultats': '预估收益',
           'note': "估算基于一处露天矿的运营数据。实际收益视现场情况而定。"},
}

# ══ LES MARQUEURS DU CANEVAS ══════════════════════════════════════════════════
# Valeurs reprises du renderVals() de chaque canevas, avec deux écarts assumés :
#   padSection prend la version aérée, mieux adaptée à une page consultée sur un
#     écran qu'à une vignette d'éditeur ;
#   accent prend le jaune de la charte, et non l'ambre de la maquette.

VALEURS = {
    'accent': '#FDC30E',
    'padSection': 'clamp(52px,7cqw,104px)',
    'btnFlex': '0 0 auto',
    'frameWidth': 'none',
    'frameMargin': '0',
    'frameShadow': 'none',
    'refTraits': '',
}

# Conditions <sc-if> : ce qu'on fait de chaque branche.
#   'garder'   : le contenu reste tel quel
#   'retirer'  : le bloc entier disparaît
#   'classe:X' : le contenu reste, et chaque enfant direct reçoit la classe X,
#                dont l'affichage est ensuite commandé par une requête de média.
#   'replier'  : le contenu reste mais part masqué, ouvert par le script.
CONDITIONS = {
    'afficherTarifs': 'retirer',     # décision : pas de prix public
    'lienTarifs': 'retirer',         # le lien de menu qui y conduisait
    'large': 'classe:dc-large',      # visible à partir de 720 px
    'mobile': 'classe:dc-petit',     # visible en dessous de 720 px
    'languesOuvertes': 'replier',    # le menu déroulant des langues
}

# ══ LA PALETTE ════════════════════════════════════════════════════════════════
# Ordre important : les chaînes les plus longues d'abord, sinon un remplacement
# court coupe un code plus long en deux.

COULEURS = [
    # Les voiles posés sur la photographie deviennent anthracite. La charte
    # prescrit exactement cela pour une image de fond, et un voile bleu plus
    # clair aurait dégradé la lisibilité du titre en réserve.
    (r'rgba\(0,\s*31,\s*77,', 'rgba(20,23,28,'),
    ('#001F4D', '#25498A'),   # bleu nuit de la maquette -> bleu de la charte
    ('#FFB700', '#FDC30E'),   # ambre -> jaune de la charte
    # L'orange n'appartient pas à la charte. Là où il servait à distinguer une
    # colonne, le bleu le remplace ; le magenta, lui, est conservé : c'est la
    # couleur des dômes dans le logiciel, donc une couleur de produit.
    ('#FF6B35', '#25498A'),
    # Gris : ceux de la charte graphique, qui ont été mesurés.
    ('#111111', '#1B2129'),
    ('#333333', '#39424E'),
    ('#444444', '#39424E'),
    ('#555555', '#5A6572'),
    ('#666666', '#5A6572'),
    ('#8A8A8A', '#8A93A0'),
    ('#999999', '#8A93A0'),
    ('#D8D8D8', '#E4E8EC'),
    ('#DDDDDD', '#E4E8EC'),
    ('#F1F4F9', '#EEF1F4'),
    ('#F5F5F5', '#F4F6F8'),
    ('#C9D6E8', '#C3CBD4'),
    ('#DCE5F2', '#D5DCE6'),
]

POLICES = [
    ("'IBM Plex Sans',Helvetica,sans-serif", "'Poppins','Segoe UI',system-ui,sans-serif"),
    ("'IBM Plex Sans'", "'Poppins'"),
    ("'IBM Plex Mono',monospace", "'Poppins','Segoe UI',system-ui,sans-serif"),
    ("'IBM Plex Mono'", "'Poppins'"),
]

# ══ CORRECTIONS DE TEXTE ══════════════════════════════════════════════════════
#
# LE PÉTARDAGE N'EST PAS UN TRI. La maquette écrivait « tri de blocs » en
# français, et les douze traductions avaient suivi la même erreur : sélection,
# sortering, ayıklama, 处理. Il s'agit de faire SAUTER les blocs hors gabarit,
# pas de les trier. C'est un terme de métier, et un client du domaine repère
# l'erreur immédiatement.
#
# La correction est appliquée ici, et non dans les canevas : un nouvel export
# depuis Claude Design écraserait une retouche faite dans design/.
#
# L'allemand n'y figure pas : « Knäppern » désigne déjà le pétardage de blocs.

# Le sous-titre du bandeau disait « tirs de mine », qui se lit aussi bien comme
# un tir DE mine que comme un tir DANS une mine. « Tirs à l'explosif » lève
# l'ambiguïté. Les douze autres langues emploient déjà un terme qui ne désigne
# que le tir à l'explosif (blasting, Sprengungen, voladuras, salver, atım) :
# elles n'ont donc rien à corriger sur ce point.

CORRECTIONS = {
    'fr': [("Pétardage / tri de blocs : points", "Pétardage / tir de blocs : points"),
           ("pour les tirs de mine et carrières à ciel ouvert et chantiers de génie civil",
            "pour les tirs à l'explosif de mines et carrières à ciel ouvert et chantiers de génie civil")],
    'en': [("Secondary blasting / boulder sorting: points", "Secondary blasting / boulder blasting: points"),
           # La tournure d'origine enchaînait deux « and » et se lisait mal.
           ("for open-pit mine and quarry blasting and civil engineering worksites",
            "for blasting in open-pit mines, quarries and civil engineering worksites")],
    'es': [("Voladura secundaria / selección de bolones: puntos", "Voladura secundaria / voladura de bolones: puntos")],
    'pt': [("Fogo secundário / seleção de matacões: pontos", "Fogo secundário / desmonte de matacões: pontos")],
    'it': [("Brillamento secondario / selezione blocchi: punti", "Brillamento secondario / brillamento di blocchi: punti")],
    'nl': [("Nasprengen / blokkenselectie: punten", "Nasprengen / blokken sprengen: punten")],
    'sv': [("Skutknackning / blocksortering: punkter", "Skutknackning / blocksprängning: punkter")],
    'no': [("Etterskyting / blokksortering: punkter", "Etterskyting / blokksprengning: punkter")],
    'da': [("Efterskydning / bloksortering: punkter", "Efterskydning / bloksprængning: punkter")],
    'af': [("Nasketing / bloksortering: punte", "Nasketing / bloksketing: punte")],
    'tr': [("İkincil atım / blok ayıklama: noktalar", "İkincil atım / blok patlatma: noktalar")],
    'zh': [("二次爆破／大块处理：点位", "二次爆破／大块爆破：点位")],
}


def aligner_adresse_affichee(corps: str) -> str:
    """Le pied de page affiche l'adresse du site : elle doit être celle que le
    visiteur verra dans sa barre d'adresse, donc la forme avec www.

    ─── LA SUBSTITUTION EST DÉLIBÉRÉMENT ÉTROITE ──────────────────────────────
    Elle ne porte que sur le texte d'un élément, encadré par ses balises. Une
    substitution large sur « blastclear.com » attraperait aussi
    contact@blastclear.com, et transformerait l'adresse de contact en
    contact@www.blastclear.com, qui n'existe pas et vers laquelle aucun courriel
    n'arriverait jamais."""
    return corps.replace('>blastclear.com<', '>www.blastclear.com<')


def nettoyer_typographie(corps: str) -> str:
    """Deux corrections qui valent pour les treize langues.

    ─── LE TIRET CADRATIN ─────────────────────────────────────────────────────
    Il sert de séparateur dans le pied de page et dans les légendes. L'éditeur
    ne l'emploie nulle part ailleurs dans ses documents ; le point médian tient
    le même rôle sans détoner. Entre deux chiffres, c'est un simple trait
    d'union qui convient, et il se lit dans toutes les langues.

    ─── LA VERSION ANNONCÉE ───────────────────────────────────────────────────
    Le pied de page dit « v2.0 » alors que la légende de la capture, dans le
    même document, dit « v2.2 ». La version livrée est la 2.2 : c'est elle qui
    doit être écrite, sinon la page date le produit d'un an en arrière."""
    corps = re.sub(r'\s*—+\s*', ' · ', corps)
    corps = re.sub(r'(\d)\s*–\s*(\d)', r'\1-\2', corps)
    corps = re.sub(r'\s*–\s*', ' · ', corps)
    corps = corps.replace('BlastClear v2.0', 'BlastClear v2.2')
    return corps


def completer_formulaire(corps: str, mots: dict) -> str:
    """LES CHAMPS RESTENT VIDES. SEUL LE MESSAGE GARDE SON INDICATION.

    ─── CE QUI A ÉTÉ POSÉ, PUIS RETIRÉ ────────────────────────────────────────
    La table de traduction prévoit un exemple pour chaque champ : « Jean Dupont »,
    « Nom de la mine ou du bureau d'études », et ainsi de suite. Les afficher en
    texte indicatif paraissait utile. À l'usage, cinq champs porteurs d'un texte
    gris se lisent comme un formulaire déjà rempli, et l'étiquette placée au-dessus
    de chacun dit déjà ce qu'on y attend.

    Le message fait exception et garde le sien : son étiquette, « Votre message »,
    n'indique pas ce qu'il serait utile d'écrire. Cette indication vient du canevas
    et n'a jamais eu besoin d'être posée ici.

    La fonction subsiste, sans effet, pour que le point d'insertion reste visible et
    documenté plutôt que de disparaître dans l'historique."""
    return corps


def appliquer_corrections(corps: str, code: str, source: str) -> str:
    """Applique les corrections de la langue, et se plaint si l'une ne trouve pas
    sa cible : une correction qui ne s'applique plus en silence est une
    correction perdue le jour où le texte source change."""
    for ancien, nouveau in CORRECTIONS.get(code, []):
        if ancien not in corps:
            print(f'  ATTENTION  {source} [{code}] : texte à corriger introuvable : "{ancien[:48]}…"')
            continue
        corps = corps.replace(ancien, nouveau)
    return corps


_fond_svg: str | None = None


def fond_balistique() -> str:
    """Le faisceau recoloré, prêt à être posé DANS la page.

    ─── POURQUOI IL EST INTÉGRÉ ET NON CHARGÉ COMME IMAGE ─────────────────────
    Une image chargée par <img> est une boîte noire : ni le CSS ni le script de
    la page n'atteignent ce qu'elle contient. Or l'animation demandée consiste à
    faire apparaître CHAQUE trajectoire l'une après l'autre, ce qui suppose de
    manipuler les dix tracés individuellement. Il faut donc que le SVG fasse
    partie du document.

    Le coût est un fichier de 20 ko recopié dans chaque page plutôt qu'une
    requête séparée. En contrepartie il n'y a plus de requête du tout, et le
    faisceau ne peut plus apparaître après le reste de la page."""
    global _fond_svg
    if _fond_svg is not None:
        return _fond_svg

    source = SOURCE / 'assets' / 'ballistic-bg.svg'
    svg = source.read_text(encoding='utf-8')
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<metadata>.*?</metadata>', '', svg, flags=re.S)
    for ancienne in ('#2A4B9A', '#018080', '#068C38', '#BE1542'):
        svg = re.sub(ancienne, '#25498A', svg, flags=re.I)
    svg = re.sub('#EF7E19', '#FDC30E', svg, flags=re.I)

    # L'identifiant et les attributs que la page attend, posés sur la balise
    # <svg> elle-même. aria-hidden parce qu'un décor n'a rien à annoncer.
    svg = re.sub(
        r'<svg\b[^>]*?(viewBox="[^"]*")[^>]*>',
        r'<svg \1 id="traits-balistiques" class="dc-traits" aria-hidden="true" focusable="false" '
        'style="position:absolute;left:50%;top:50%;width:170%;transform:translate(-50%,-46%);'
        'opacity:0;pointer-events:none;z-index:0">',
        svg, count=1)

    _fond_svg = svg.strip()
    return _fond_svg


def inliner_fond_balistique(corps: str) -> str:
    """Substitue le SVG intégré à la balise <img> de la maquette."""
    return re.sub(r'<img\b[^>]*ballistic-bg\.svg[^>]*/?>', lambda _: fond_balistique(), corps)


def preparer_fond_balistique() -> None:
    """Recolore et allège le faisceau de trajectoires qui sert de fond.

    ─── LES COULEURS D'ORIGINE NE SONT PAS CELLES DE LA MARQUE ────────────────
    Le fichier fourni trace ses arcs en sarcelle, cramoisi, vert, bleu et
    orange : cinq teintes dont une seule approche le bleu de la charte. Sur une
    page par ailleurs strictement bleu et jaune, le faisceau détonnait.

    Quatre arcs passent au bleu, un seul au jaune. La charte demande que le
    jaune reste minoritaire, et il porte ici ce qu'il porte partout ailleurs :
    la trajectoire que l'on surveille.

    ─── ET LE FICHIER EMPORTE 14 KO DE MÉTADONNÉES ────────────────────────────
    Un manifeste de provenance en base64 occupe la moitié du fichier et ne sert
    à rien dans une image de fond décorative."""
    source = SOURCE / 'assets' / 'ballistic-bg.svg'
    if not source.exists():
        return
    svg = source.read_text(encoding='utf-8')
    avant = len(svg)

    svg = re.sub(r'<metadata>.*?</metadata>', '', svg, flags=re.S)

    for ancienne in ('#2A4B9A', '#018080', '#068C38', '#BE1542'):
        svg = re.sub(ancienne, '#25498A', svg, flags=re.I)
    svg = re.sub('#EF7E19', '#FDC30E', svg, flags=re.I)

    cible = SITE / 'assets' / 'design' / 'ballistic-bg.svg'
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(svg, encoding='utf-8', newline='\n')
    print(f'  écrit  site/assets/design/ballistic-bg.svg  ({avant // 1024} Ko -> {len(svg) // 1024} Ko)')


def renforcer_bandeau(corps: str) -> str:
    """Le voile posé sur la photographie du bandeau.

    ─── DEUX EXIGENCES QUI S'OPPOSENT ─────────────────────────────────────────
    Le titre est en réserve blanche sur une photographie de fosse, claire par
    endroits : il lui faut un voile dense. Mais la photographie est le seul visuel
    du haut de page, et un voile uniforme assez dense pour le titre l'efface.

    Un premier essai a assombri tout le voile. Le titre est devenu net, et la fosse
    a disparu : c'est ce que montrait la capture.

    ─── LA SORTIE EST HORIZONTALE, ET NON VERTICALE ──────────────────────────
    Le texte occupe la moitié GAUCHE du bandeau ; le dôme et la fosse sont à droite.
    Un dégradé de gauche à droite peut donc être dense derrière le texte et
    quasi nul là où il n'y a rien à lire. Chacun obtient ce qu'il lui faut, au lieu
    d'un compromis qui dessert les deux.

    La règle passe en feuille de style, et non en attribut : un dégradé en ligne ne
    se change pas selon la largeur de l'écran, or sous 900 px le texte s'étale sur
    toute la largeur et le dégradé horizontal ne convient plus."""
    corps = corps.replace(
        '<div style="position:absolute;inset:0;background:linear-gradient(180deg,'
        'rgba(20,23,28,0.30) 0%,rgba(20,23,28,0.40) 25%,rgba(20,23,28,0.82) 62%,'
        'rgba(20,23,28,0.96) 100%)"></div>',
        '<div class="dc-voile" style="position:absolute;inset:0"></div>')

    # La classe permet à la feuille de style de fixer la hauteur du bandeau et le
    # cadrage de la photographie, ce qu'un style en ligne ne sait pas faire selon
    # la largeur de l'écran.
    return corps.replace(
        '<header style="position:relative;background:#25498A;overflow:hidden;',
        '<header class="dc-bandeau" style="position:relative;background:#25498A;overflow:hidden;', 1)


# Hauteurs d'affichage du logo, en pixels.
#
# LA CHARTE FIXE UN SEUIL, ET IL ÉTAIT FRANCHI. Section 4 : le logo complet ne
# descend pas sous 200 px de large à l'écran, avec ce point de vigilance : « le
# faisceau de paraboles se referme visuellement en dessous de 200 px : les
# trajectoires fusionnent en une masse bleue ». C'est exactement ce qui se voyait
# dans le bandeau.
#
# Le logo mesure 5,839 fois plus large que haut. Le seuil de 200 px de large
# correspond donc à 34,3 px de haut, et les trois emplois ci-dessous étaient en
# dessous. Les nouvelles valeurs laissent une marge plutôt que de frôler la limite.
HAUTEURS_LOGO = {
    '34': '48',   # bandeau de l'accueil : 199 px -> 282 px
    '32': '44',   # bandeau des pages de formulaire : 187 px -> 258 px
    '28': '40',   # pied de page : 163 px -> 235 px
}


MARQUE = RACINE / 'marque'

# Épaisseur de trait des variantes destinées à l'écran.
#
# ─── POURQUOI ELLE EST RELEVÉE, ET DE COMBIEN ─────────────────────────────────
# Le fichier maître porte 0,75. C'est la bonne valeur pour une impression, où le
# point est très fin ; à 40 px de haut sur un écran d'ordinateur, le maillage du
# dôme s'y délave. Rendus comparés à 0,75, 1,1, 1,5 et 2,0 : à 1,5 le maillage est
# net et régulier, à 2,0 il commence à se refermer dans sa partie dense.
#
# Ce n'est pas une recoloration ni une déformation : les proportions et les
# couleurs sont intactes. C'est l'adaptation que la charte prévoit elle-même quand
# elle impose, sous 200 px, d'employer une version allégée du symbole plutôt qu'une
# réduction du tracé complet.
EPAISSEUR_ECRAN = '1.5'


def preparer_logos() -> None:
    """Produit les variantes web du logo à partir des fichiers maîtres.

    Deux opérations, et une seule raison pour chacune.

    LE RECADRAGE. Le fichier maître est dessiné sur un plan qui déborde largement
    le tracé. Affiché tel quel, le logo apparaît petit au milieu d'une zone
    transparente, et toute hauteur demandée porte sur le vide autant que sur le
    dessin. La variante web reçoit donc l'emprise réelle du tracé pour viewBox.

    L'ÉPAISSEUR. Voir EPAISSEUR_ECRAN. Elle ne peut pas être réglée depuis la page :
    une image chargée par <img> est opaque au CSS, qui n'atteint rien de ce qu'elle
    contient. Il faut donc une variante du fichier.
    """
    fichiers = [
        ('Logo_BlastClear.svg', 'Logo_BlastClear_web.svg', 'BlastClear'),
        ('Logo_BlastClear_FondSombre.svg', 'Logo_BlastClear_FondSombre_web.svg', 'BlastClear'),
        ('Logo_BlastClear_Symbole.svg', 'Logo_BlastClear_Symbole_web.svg', 'Symbole BlastClear'),
    ]
    cible = SITE / 'assets' / 'logo'
    cible.mkdir(parents=True, exist_ok=True)

    for nom, nom_web, etiquette in fichiers:
        source = MARQUE / nom
        if not source.exists():
            print(f'  ABSENT {nom}')
            continue
        svg = source.read_text(encoding='utf-8')

        boite = emprise_svg(svg)
        if boite:
            x0, y0, x1, y1 = boite
            svg = re.sub(r'viewBox="[^"]*"',
                         f'viewBox="{x0:.2f} {y0:.2f} {x1 - x0:.2f} {y1 - y0:.2f}"',
                         svg, count=1)

        svg = re.sub(r'stroke-width:\s*\.?\d*\.?\d+', f'stroke-width:{EPAISSEUR_ECRAN}', svg)
        svg = re.sub(r'stroke-width="\.?\d*\.?\d+"', f'stroke-width="{EPAISSEUR_ECRAN}"', svg)

        svg = re.sub(r'<svg\b([^>]*?)>',
                     lambda m: f'<svg{m.group(1)} role="img" aria-label="{etiquette}">',
                     svg, count=1)

        (cible / nom_web).write_text(svg.strip(), encoding='utf-8', newline='\n')
        shutil.copy2(source, cible / nom)
    print(f'  écrit  site/assets/logo/  (variantes web, trait {EPAISSEUR_ECRAN})')


def emprise_svg(svg: str):
    """Emprise réelle des tracés, pour recadrer le plan de dessin.

    Les points de contrôle des courbes sont comptés comme des points ordinaires :
    la boîte obtenue est au pire légèrement trop grande, jamais trop petite. On ne
    risque donc pas de rogner le logo, ce qui serait la seule erreur grave ici."""
    nombres = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')
    xs, ys = [], []
    for d in re.findall(r'\sd="([^"]+)"', svg):
        x = y = 0.0
        for lettre, corps in re.findall(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)', d):
            maj, relatif = lettre.upper(), lettre.islower()
            if maj == 'Z':
                continue
            args = [float(n) for n in nombres.findall(corps)]
            arite = {'M': 2, 'L': 2, 'T': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'A': 7}[maj]
            for i in range(0, len(args) - arite + 1, arite):
                g = args[i:i + arite]
                if maj == 'H':
                    x = x + g[0] if relatif else g[0]
                elif maj == 'V':
                    y = y + g[0] if relatif else g[0]
                else:
                    couples = {'C': [(0, 1), (2, 3), (4, 5)], 'S': [(0, 1), (2, 3)],
                               'Q': [(0, 1), (2, 3)], 'A': [(5, 6)]}.get(maj, [(0, 1)])
                    for cx, cy in couples:
                        xs.append(x + g[cx] if relatif else g[cx])
                        ys.append(y + g[cy] if relatif else g[cy])
                    dx, dy = couples[-1]
                    x = x + g[dx] if relatif else g[dx]
                    y = y + g[dy] if relatif else g[dy]
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def respecter_taille_minimale_logo(corps: str) -> str:
    """Remonte les tailles d'affichage du logo au-dessus du seuil de la charte.

    La substitution ne porte QUE sur les balises du logo : la même hauteur employée
    ailleurs, sur une icône ou un pictogramme, n'a aucune raison de bouger."""
    def remplacer(m):
        balise = m.group(0)
        return re.sub(r'height:(\d+)px',
                      lambda h: 'height:' + HAUTEURS_LOGO.get(h.group(1), h.group(1)) + 'px',
                      balise)

    return re.sub(r'<img\b[^>]*Logo_BlastClear[^>]*>', remplacer, corps)


# ══ LA BARRE NE TENAIT PAS EN HAUT ════════════════════════════════════════════
#
# ─── LE SYMPTÔME ET SA CAUSE, QUI N'EST PAS DANS LA BARRE ─────────────────────
# La barre porte pourtant `position:sticky;top:0`. Elle remontait quand même avec
# la page. La règle n'est pas en cause : c'est SON ENVELOPPE qui la désarme.
#
# Le cadre de la maquette porte `overflow-x:hidden`. Or une valeur `hidden` sur un
# seul axe force l'autre axe, déclaré `visible`, à devenir `auto` : le cadre se
# transforme en conteneur de défilement. Un élément collant se cale sur le plus
# proche conteneur de défilement qui l'englobe, donc sur ce cadre, et non plus sur
# la fenêtre. Comme ce cadre ne défile jamais lui-même, la barre n'a rien à quoi se
# tenir et suit le contenu.
#
# ─── POURQUOI `clip` ET NON LA SUPPRESSION DE LA RÈGLE ────────────────────────
# Le rognage sert : plusieurs éléments de la maquette débordent volontairement en
# largeur. `overflow-x:clip` rogne exactement comme `hidden`, à une différence
# près, qui est celle qu'on cherche : il ne crée PAS de conteneur de défilement, et
# n'entraîne donc pas l'autre axe. La barre retrouve la fenêtre pour référence.

def liberer_barre_collante(corps: str) -> str:
    """Rend à la barre son point d'ancrage, en changeant le rognage du cadre."""
    return corps.replace('overflow-x:hidden', 'overflow-x:clip')


# ══ LES RÉSEAUX, DANS LE PIED DE PAGE ═════════════════════════════════════════
#
# ─── LES TRACÉS SONT CEUX DES MARQUES, NON DES APPROXIMATIONS ─────────────────
# Chaque glyphe est le tracé officiel de la marque, sur une grille de 24. Les
# redessiner « à peu près » se voit immédiatement : ces quatre symboles sont parmi
# les formes les plus reconnues qui soient, et un rayon faux les fait paraître
# contrefaits.
#
# ─── CE QUI RESTE À CONFIRMER ─────────────────────────────────────────────────
# Les adresses ci-dessous sont les formes attendues des comptes. Elles sont
# rassemblées ICI, en un seul endroit, précisément parce qu'elles devront être
# corrigées une fois les comptes ouverts : un lien de pied de page qui tombe sur
# une page absente coûte plus cher en crédibilité qu'un lien manquant.
RESEAUX = [
    ('LinkedIn', 'https://www.linkedin.com/company/blastclear',
     'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 '
     '2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 '
     '4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 '
     '2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 '
     '13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 '
     '24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'),
    ('Facebook', 'https://www.facebook.com/blastclear',
     'M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 '
     '11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 '
     '2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 '
     '23.027 24 18.062 24 12.073z'),
    ('Instagram', 'https://www.instagram.com/blastclear',
     'M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 '
     '1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 '
     '4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 '
     '1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 '
     '2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 '
     '1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 '
     '1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 '
     '2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 '
     '1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 '
     '4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 '
     '0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.166-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 '
     '0-3.196.016-3.586.061-4.861.061-1.17.254-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 '
     '1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 '
     '3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 '
     '6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 '
     '4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 '
     '0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z'),
    ('YouTube', 'https://www.youtube.com/@blastclear',
     'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 '
     '0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 '
     '0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 '
     '2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z'),
]


def poser_reseaux(corps: str) -> str:
    """Ajoute les quatre liens de réseaux à la fin du pied de page.

    ─── POURQUOI LE NOM DU RÉSEAU N'EST PAS TRADUIT ─────────────────────────
    Le lien n'a pas de texte visible : son intitulé accessible est donc le seul que
    lise un lecteur d'écran. Ce sont des noms propres, identiques dans les treize
    langues du site. Les traduire inventerait des mots qui n'existent pas.

    ─── LA CIBLE DU DOIGT FAIT 40 px, PAS 20 ────────────────────────────────
    Le symbole est dessiné à 20 px, mais la zone cliquable en fait le double par le
    rembourrage. Quatre cibles de 20 px espacées de quelques pixels, au bas d'une
    page consultée au pouce, se manquent une fois sur deux."""
    if '</footer>' not in corps or 'dc-reseaux' in corps:
        return corps

    liens = ''.join(
        f'<a class="dc-reseau" href="{url}" target="_blank" rel="noopener" '
        f'aria-label="{nom}"><svg viewBox="0 0 24 24" width="20" height="20" '
        f'fill="currentColor" aria-hidden="true" focusable="false">'
        f'<path d="{trace}"/></svg></a>'
        for nom, url, trace in RESEAUX
    )
    return corps.replace(
        '</footer>', f'    <div class="dc-reseaux">{liens}</div>\n  </footer>', 1)


# ══ LA DÉFINITION, EN TÊTE DE PAGE ════════════════════════════════════════════
#
# ─── POURQUOI ELLE MANQUAIT ────────────────────────────────────────────────────
# La page passait du bandeau directement à « AVANT / AVEC BLASTCLEAR », c'est-à-dire
# d'une accroche à une comparaison. Un visiteur qui ne connaît pas le produit devait
# deviner ce qu'il fait à partir de ce qu'il remplace. La définition comble ce saut :
# elle dit le métier avant d'en vanter le gain.
#
# ─── LA TERMINOLOGIE EST CELLE DE LA PAGE, NON UNE TRADUCTION LIBRE ───────────
# Chaque langue reprend les termes déjà employés plus bas dans ses propres listes :
# « Vorspaltsprengung » et non « Vorspalten », « förspräckning » et non
# « försprängning », « precorte » et non « pre-corte ». Deux mots différents pour la
# même opération, dans une même page, font douter de l'un et de l'autre.
#
# Ordre des trois paragraphes : le dôme et ses secteurs, l'intersection avec le
# terrain, puis les familles de tirs et les livrables.

DEFINITION = {
    'fr': ("DÉFINITION", "Ce que fait BlastClear",
           "BlastClear génère le périmètre d'évacuation d'un tir à l'explosif à partir du dôme balistique correspondant au rayon maximal retenu. La portée se module ensuite par secteur autour du tir : entière vers l'avant, où partent les projections, réduite sur les côtés, davantage réduite à l'arrière.",
           "Le dôme est intersecté avec la topographie réelle du site. Le périmètre tracé épouse donc le terrain, ses banquettes et ses ruptures de pente, et non un plan horizontal théorique.",
           "Les trois familles de tirs sont traitées dans le même projet : production sur contour fermé, pré-découpage sur polylignes, pétardage et tir de blocs sur points. Plusieurs tirs d'une même volée se fondent en un périmètre unique, sans raccord manuel. Le résultat sort en plan PDF prêt à signer, en DXF pour les plans du site, ou en image."),
    'en': ("DEFINITION", "What BlastClear does",
           "BlastClear builds the clearance perimeter of a blast from the ballistic dome matching the maximum radius you set. The reach is then graded sector by sector around the blast: full to the front, where the throw goes, reduced laterally, reduced further to the rear.",
           "The dome is intersected with the actual site topography. The perimeter therefore follows the ground, its benches and its breaks of slope, rather than a theoretical horizontal plane.",
           "All three families of blast are handled in the same project: production on a closed contour, pre-splitting on polylines, secondary and boulder blasting on points. Several blasts of the same round merge into a single perimeter, with no manual rework. The result comes out as a PDF drawing ready to sign, as DXF for the site drawings, or as an image."),
    'es': ("DEFINICIÓN", "Qué hace BlastClear",
           "BlastClear genera el perímetro de evacuación de una voladura a partir de la cúpula balística correspondiente al radio máximo establecido. El alcance se gradúa después por sectores alrededor de la voladura: completo hacia el frente, por donde salen las proyecciones, reducido en los laterales y más reducido en la parte trasera.",
           "La cúpula se interseca con la topografía real del emplazamiento. El perímetro trazado sigue por tanto el terreno, sus bancos y sus quiebres de pendiente, y no un plano horizontal teórico.",
           "Las tres familias de voladura se tratan en el mismo proyecto: producción sobre contorno cerrado, precorte sobre polilíneas, voladura secundaria y de bolones sobre puntos. Varias voladuras de una misma pega se funden en un perímetro único, sin retoque manual. El resultado sale en plano PDF listo para firmar, en DXF para los planos del emplazamiento, o en imagen."),
    'pt': ("DEFINIÇÃO", "O que faz o BlastClear",
           "O BlastClear gera o perímetro de evacuação de um fogo a partir da cúpula balística correspondente ao raio máximo definido. O alcance é depois graduado por setores em torno do fogo: total para a frente, por onde saem as projeções, reduzido lateralmente e mais reduzido atrás.",
           "A cúpula é intersetada com a topografia real do local. O perímetro traçado acompanha portanto o terreno, as suas bancadas e as suas quebras de declive, e não um plano horizontal teórico.",
           "As três famílias de fogo são tratadas no mesmo projeto: produção sobre contorno fechado, pré-corte sobre polilinhas, fogo secundário e desmonte de matacões sobre pontos. Vários fogos da mesma pega fundem-se num perímetro único, sem retrabalho manual. O resultado sai em desenho PDF pronto a assinar, em DXF para os desenhos do local, ou em imagem."),
    'it': ("DEFINIZIONE", "Che cosa fa BlastClear",
           "BlastClear genera il perimetro di evacuazione di una volata a partire dalla cupola balistica corrispondente al raggio massimo impostato. La portata viene poi graduata per settori attorno alla volata: intera verso il fronte, da cui partono le proiezioni, ridotta lateralmente e ridotta ulteriormente sul retro.",
           "La cupola viene intersecata con la topografia reale del sito. Il perimetro tracciato segue quindi il terreno, le sue gradonature e le sue rotture di pendenza, e non un piano orizzontale teorico.",
           "Le tre famiglie di volata sono trattate nello stesso progetto: produzione su contorno chiuso, pretaglio su polilinee, brillamento secondario e di blocchi su punti. Più volate della stessa serie si fondono in un perimetro unico, senza ritocchi manuali. Il risultato esce come disegno PDF pronto da firmare, come DXF per i disegni del sito, o come immagine."),
    'de': ("DEFINITION", "Was BlastClear leistet",
           "BlastClear erzeugt den Evakuierungsperimeter einer Sprengung aus der ballistischen Kuppel zum eingestellten Maximalradius. Die Reichweite wird anschließend sektorweise um die Sprengung herum abgestuft: voll nach vorn, wohin der Wurf geht, seitlich reduziert und nach hinten stärker reduziert.",
           "Die Kuppel wird mit der realen Geländeoberfläche des Standorts verschnitten. Der gezeichnete Perimeter folgt daher dem Gelände, seinen Bermen und Geländekanten, und nicht einer theoretischen Horizontalebene.",
           "Alle drei Sprengungsarten werden im selben Projekt behandelt: Produktion auf geschlossener Kontur, Vorspaltsprengung auf Polylinien, Nachsprengung und Knäppern auf Punkten. Mehrere Sprengungen desselben Abschlags verschmelzen zu einem einzigen Perimeter, ohne Nacharbeit. Das Ergebnis liegt als unterschriftsreifer PDF-Plan, als DXF für die Standortpläne oder als Bild vor."),
    'nl': ("DEFINITIE", "Wat BlastClear doet",
           "BlastClear genereert de evacuatieperimeter van een schot op basis van de ballistische koepel die hoort bij de ingestelde maximale straal. Het bereik wordt vervolgens per sector rond het schot gegradeerd: volledig naar voren, waar de worp heen gaat, zijwaarts gereduceerd en naar achteren sterker gereduceerd.",
           "De koepel wordt doorsneden met de werkelijke topografie van de locatie. De getekende perimeter volgt dus het terrein, de bermen en de hellingbreuken, en niet een theoretisch horizontaal vlak.",
           "De drie soorten schoten worden in hetzelfde project behandeld: productie op gesloten contour, voorsplijten op polylijnen, nasprengen en blokken sprengen op punten. Meerdere schoten van dezelfde ronde smelten samen tot één perimeter, zonder handwerk. Het resultaat komt eruit als een ondertekenklare PDF-tekening, als DXF voor de locatietekeningen, of als afbeelding."),
    'sv': ("DEFINITION", "Vad BlastClear gör",
           "BlastClear tar fram utrymningsperimetern för en salva utifrån den ballistiska kupol som motsvarar den inställda maximala radien. Räckvidden graderas därefter sektorvis runt salvan: full framåt, dit kastet går, reducerad i sidled och kraftigare reducerad bakåt.",
           "Kupolen skärs mot platsens verkliga topografi. Den ritade perimetern följer alltså terrängen, dess pallar och lutningsbrott, och inte ett teoretiskt horisontalplan.",
           "Alla tre typer av salvor hanteras i samma projekt: produktion på sluten kontur, förspräckning på polylinjer, skutknackning och blocksprängning på punkter. Flera salvor i samma runda slås samman till en enda perimeter, utan manuellt efterarbete. Resultatet levereras som en underskriftsklar PDF-ritning, som DXF för platsens ritningar, eller som bild."),
    'no': ("DEFINISJON", "Hva BlastClear gjør",
           "BlastClear lager evakueringsperimeteren for en salve ut fra den ballistiske kuppelen som svarer til den innstilte maksimale radien. Rekkevidden graderes deretter sektorvis rundt salven: full forover, dit kastet går, redusert sideveis og kraftigere redusert bakover.",
           "Kuppelen skjæres mot stedets virkelige topografi. Den tegnede perimeteren følger dermed terrenget, pallene og hellingsbruddene, og ikke et teoretisk horisontalplan.",
           "Alle tre salvetyper håndteres i samme prosjekt: produksjon på lukket kontur, forspalting på polylinjer, etterskyting og blokksprengning på punkter. Flere salver i samme runde slås sammen til én perimeter, uten manuelt etterarbeid. Resultatet leveres som en signeringsklar PDF-tegning, som DXF for stedets tegninger, eller som bilde."),
    'da': ("DEFINITION", "Hvad BlastClear gør",
           "BlastClear danner evakueringsperimeteren for en sprængning ud fra den ballistiske kuppel, der svarer til den valgte maksimale radius. Rækkevidden gradueres derefter sektorvis omkring sprængningen: fuld fremad, hvor kastet går hen, reduceret til siden og kraftigere reduceret bagud.",
           "Kuplen skæres mod stedets virkelige topografi. Den tegnede perimeter følger derfor terrænet, dets bænke og hældningsbrud, og ikke et teoretisk vandret plan.",
           "Alle tre sprængningstyper håndteres i samme projekt: produktion på lukket kontur, forspaltning på polylinjer, efterskydning og bloksprængning på punkter. Flere sprængninger i samme runde lægges sammen til én perimeter, uden manuelt efterarbejde. Resultatet leveres som en underskriftsklar PDF-tegning, som DXF til stedets tegninger, eller som billede."),
    'af': ("DEFINISIE", "Wat BlastClear doen",
           "BlastClear skep die ontruimingsomtrek van 'n skoot uit die ballistiese koepel wat by die ingestelde maksimum radius pas. Die bereik word daarna sektorsgewys om die skoot gegradeer: vol na voor, waarheen die werp gaan, sywaarts verminder en agter sterker verminder.",
           "Die koepel word met die terrein se werklike topografie gesny. Die omtrek wat geteken word, volg dus die terrein, sy banke en hellingbreuke, en nie 'n teoretiese horisontale vlak nie.",
           "Al drie soorte skote word in dieselfde projek hanteer: produksie op geslote kontoer, voorsplyting op pollyne, nasketing en bloksketing op punte. Verskeie skote van dieselfde ronde smelt saam tot een enkele omtrek, sonder handwerk. Die resultaat kom uit as 'n PDF-tekening gereed vir ondertekening, as DXF vir die terrein se tekeninge, of as beeld."),
    'tr': ("TANIM", "BlastClear ne yapar",
           "BlastClear, belirlenen azami yarıçapa karşılık gelen balistik kubbeden yola çıkarak bir atımın tahliye çevresini üretir. Erişim mesafesi daha sonra atımın çevresinde sektör sektör ayarlanır: savrulmanın gittiği ön tarafta tam, yanlarda azaltılmış, arkada daha da azaltılmış.",
           "Kubbe, sahanın gerçek topografyasıyla kesiştirilir. Çizilen çevre böylece araziyi, basamaklarını ve eğim kırıklıklarını izler; teorik bir yatay düzlemi değil.",
           "Üç atım ailesi de aynı projede ele alınır: kapalı kontur üzerinde üretim, polilinyalar üzerinde ön çatlatma, noktalar üzerinde ikincil atım ve blok patlatma. Aynı seriye ait birden çok atım, elle düzeltme olmadan tek bir çevrede birleşir. Sonuç, imzaya hazır PDF planı, saha planları için DXF veya görüntü olarak çıkar."),
    'zh': ("定义", "BlastClear 的作用",
           "BlastClear 依据所设定的最大半径对应的弹道穹顶，生成一次爆破的疏散警戒范围。随后按扇区调整作用距离：抛掷方向的前方取全值，侧向折减，后方折减更多。",
           "穹顶与现场真实地形求交。因此所绘的警戒范围贴合地面、台阶与坡度转折，而非一个理论水平面。",
           "三类爆破在同一项目中处理：闭合轮廓上的生产爆破、多段线上的预裂爆破、点位上的二次爆破与大块爆破。同一轮次的多次爆破自动合并为单一警戒范围，无需手工返工。成果可输出为可直接签署的 PDF 图纸、用于现场图纸的 DXF，或图像。"),
}


def b_du_logo() -> str | None:
    """Extrait du logo le tracé de son B, pour l'employer comme lettre.

    ─── EN QUOI CE B DIFFÈRE DE CELUI DE POPPINS ──────────────────────────────
    Son montant gauche n'est pas droit : il s'incurve et s'évase vers le bas, en
    balayage, à la manière d'une trajectoire. C'est la seule lettre dessinée du
    logotype ; les autres sont du Poppins.

    ─── POURQUOI ON LE PRÉLÈVE AU LIEU DE LE RECOPIER ─────────────────────────
    Le tracé est lu dans le fichier maître à chaque construction. Un nouvel export
    du logo emporte donc le titre avec lui, au lieu de le laisser diverger.

    Le tracé est repéré par sa position, non par un rang : c'est la première forme
    pleine du logotype, celle qui suit le symbole. Un rang se décalerait au premier
    réordonnancement des calques dans Illustrator.
    """
    source = MARQUE / 'Logo_BlastClear_FondSombre.svg'
    if not source.exists():
        return None
    svg = source.read_text(encoding='utf-8')

    candidats = []
    for m in re.finditer(r'<path\b([^>]*?)/?>', svg):
        attrs = m.group(1)
        if 'stroke=' in attrs and 'fill="none"' in attrs:
            continue                      # le symbole, qui est au trait
        d = re.search(r'\sd="([^"]+)"', attrs)
        if not d:
            continue
        boite = emprise_svg(f'<path d="{d.group(1)}"/>')
        if boite:
            candidats.append((boite[0], boite, d.group(1)))

    if not candidats:
        return None
    candidats.sort()
    x0, (bx0, by0, bx1, by1), trace = candidats[0]

    largeur, hauteur = bx1 - bx0, by1 - by0
    return (f'<svg class="dc-b" viewBox="{bx0:.2f} {by0:.2f} {largeur:.2f} {hauteur:.2f}" '
            f'style="aspect-ratio:{largeur:.2f}/{hauteur:.2f}" aria-hidden="true" '
            f'focusable="false"><path d="{trace}"/></svg>')


def nom_avec_b_du_logo(texte: str) -> str:
    """Remplace « BlastClear » par le nom composé à l'identique du logotype.

    Le reste des lettres demeure du texte : le nom se sélectionne, se recherche, et
    un lecteur d'écran l'énonce. Seule la lettre dessinée passe en image, et elle
    est marquée décorative, le mot complet restant lisible sans elle.

    ─── LA COUPURE EST CELLE DU LOGOTYPE, RELEVÉE DANS LE FICHIER ────────────
    Les deux exports ne portent que deux couleurs de lettres, cinq glyphes chacune :
    « Blast » dans la couleur dominante (blanc sur fond sombre, bleu sur fond clair)
    et « Clear » en #FDC30E. Le titre reprend donc exactement cette coupure, et
    « Clear » y passe en graisse normale, comme dans le logo.

    ─── LE JAUNE SUR BLANC, ICI SEULEMENT ────────────────────────────────────
    Le jaune de la charte tombe à 1,62:1 sur blanc, et la charte l'interdit pour du
    texte. L'exception vaut pour CE mot et lui seul : un nom de marque composé en
    logotype relève de l'exception de la règle 1.4.3, qui ne fixe aucun contraste au
    texte faisant partie d'un logo. La règle reste entière partout ailleurs, et rien
    d'informatif ne repose sur cette couleur : le mot est le même en noir et blanc."""
    b = b_du_logo()
    if not b or 'BlastClear' not in texte:
        return texte
    return texte.replace(
        'BlastClear',
        f'<span class="dc-nom"><span class="dc-b-lettre">B</span>{b}last'
        f'<span class="dc-clear">Clear</span></span>', 1)


def construire_pourquoi(corps_accueil: str, code: str) -> str | None:
    """La page « Pourquoi BlastClear », bâtie sur l'habillage de l'accueil.

    ─── POURQUOI ON DÉCOUPE L'ACCUEIL PLUTÔT QUE DE REFAIRE UNE PAGE ─────────
    La barre de navigation porte le logo, le menu, le sélecteur de treize langues
    et son panneau déroulant ; le pied porte la version et l'adresse. Recomposer
    tout cela à la main donnerait deux habillages qui divergeraient dès la
    première retouche de la maquette. On garde donc la tête et le pied de
    l'accueil, et on remplace ce qu'il y a entre les deux.
    """
    t = POURQUOI.get(code)
    if not t:
        return None

    fin_nav = corps_accueil.find('</nav>')
    debut_pied = corps_accueil.find('<footer')
    if fin_nav < 0 or debut_pied < 0 or debut_pied < fin_nav:
        return None

    e = htmlmod.escape
    morceaux = []

    morceaux.append(f'''
  <section style="max-width:900px;margin:0 auto;padding:{VALEURS['padSection']} 5cqw 0">
    <div class="dc-surtitre">{e(t['surtitre'])}</div>
    <h1 style="margin:0 0 22px;font-size:clamp(28px,4cqw,44px);font-weight:700;letter-spacing:-1.2px;line-height:1.1">{nom_avec_b_du_logo(e(t['titre']))}</h1>
    <p style="margin:0;font-size:clamp(17px,1.9cqw,20px);line-height:1.55;color:#1B2129">{e(t['chapo'])}</p>
  </section>
''')

    for titre, paragraphes, liste in t['sections']:
        blocs = ''.join(
            f'<p style="margin:0 0 16px;font-size:16px;line-height:1.65;color:#39424E">{p}</p>'
            for p in paragraphes
        )
        if liste:
            items = ''.join(
                f'<li style="margin:0 0 12px;padding-left:2px">{x}</li>' for x in liste
            )
            blocs += ('<ul style="margin:8px 0 0;padding-left:20px;font-size:16px;'
                      f'line-height:1.65;color:#39424E">{items}</ul>')
        morceaux.append(f'''
  <section style="max-width:900px;margin:0 auto;padding:38px 5cqw 0">
    <h2 style="margin:0 0 14px;font-size:clamp(19px,2.2cqw,25px);font-weight:700;letter-spacing:-.4px;color:#25498A">{e(titre)}</h2>
    {blocs}
  </section>
''')

    # ── DEUX ISSUES, DE POIDS DIFFÉRENT ─────────────────────────────────────
    # La demande de démonstration reste l'action première, en jaune plein. Le
    # retour à l'accueil l'accompagne en second, cerné de bleu : deux boutons
    # pleins côte à côte se disputeraient le regard sans que rien ne dise lequel
    # est l'action attendue.
    morceaux.append(f'''
  <section style="max-width:900px;margin:0 auto;padding:34px 5cqw {VALEURS['padSection']}">
    <p style="margin:0 0 24px;padding:16px 18px;border-left:3px solid #FDC30E;background:#F4F6F8;font-size:14px;line-height:1.6;color:#5A6572">{e(t['note'])}</p>
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:14px">
      <a href="demo.html" style="display:inline-flex;align-items:center;background:#FDC30E;color:#14171C;font-weight:600;font-size:15px;padding:11px 22px;border-radius:2px;text-decoration:none">{e(t['appel'])}</a>
      <a class="dc-retour" href="./" style="display:inline-flex;align-items:center;gap:8px;border:1px solid #25498A;color:#25498A;font-weight:600;font-size:15px;padding:10px 20px;border-radius:2px;text-decoration:none">{MAISON_SVG}<span>{e(mot_retour(code))}</span></a>
    </div>
  </section>
''')

    # ── LES ANCRES DE LA BARRE NE POINTAIENT NULLE PART ─────────────────────
    #
    # La barre est reprise telle quelle de l'accueil, avec ses liens « #… » vers
    # des sections qui n'existent que là-bas. Sur cette page, ils ne menaient donc
    # à rien : le visiteur cliquait « Fonctionnalités » et la page ne bougeait pas.
    #
    # Les préfixer de « ./ » les renvoie à l'accueil, sur la bonne section. C'est
    # aussi, avec le bouton du bas, ce qui rend la page à nouveau traversable.
    barre = re.sub(r'href="#(?!")', 'href="./#', corps_accueil[:fin_nav + len('</nav>')])

    # ── ET LE SÉLECTEUR DE LANGUE RENVOYAIT À L'ACCUEIL ─────────────────────
    # Il menait à « ../es/ », donc à l'accueil espagnol, alors que l'en-tête de la
    # page déclare « /es/pourquoi.html » comme sa version espagnole. Le visiteur
    # qui change de langue au milieu d'une lecture veut la même page dans l'autre
    # langue, non le retour à la case départ ; et un moteur qui suit le lien
    # trouve autre chose que ce que l'en-tête annonce.
    barre = re.sub(r'href="\.\./([a-z]{2})/"', r'href="../\1/pourquoi.html"', barre)
    barre = barre.replace('href="./"', 'href="./pourquoi.html"')

    return barre + ''.join(morceaux) + corps_accueil[debut_pied:]


def inserer_definition(corps: str, code: str) -> str:
    """Pose la définition JUSTE AVANT la section « avant / avec ».

    L'ancrage se fait sur le faisceau balistique, qui n'apparaît qu'une fois dans la
    page et toujours dans cette section. Se caler sur un rang de section aurait cédé
    au premier remaniement de la maquette."""
    t = DEFINITION.get(code)
    if not t:
        return corps
    surtitre, titre, p1, p2, p3 = t

    m = re.search(r'<section\b(?:(?!</section>).)*?id="traits-balistiques"', corps, re.S)
    if not m:
        return corps
    debut = corps.rfind('<section', 0, m.end())
    if debut < 0:
        return corps
    _, _, fin_section = bloc_equilibre(corps, debut, 'section')

    e = htmlmod.escape
    # Le bouton mène à l'argumentaire complet. Il est posé ICI, au bout de la
    # définition : c'est l'endroit où le lecteur vient d'apprendre ce que fait le
    # logiciel et où la question « pourquoi ainsi » se pose d'elle-même.
    libelle = POURQUOI.get(code, {}).get('bouton')
    savoir_plus = (
        f'<a href="pourquoi.html" style="margin-top:26px;display:inline-flex;'
        'align-items:center;gap:8px;border:1px solid #25498A;color:#25498A;'
        'font-weight:600;font-size:15px;padding:10px 20px;border-radius:2px;'
        f'text-decoration:none">{e(libelle)}'
        '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<polyline points="9 5 16 12 9 19"/></svg></a>'
    ) if libelle else ''

    bloc = f'''
  <section style="max-width:1120px;margin:0 auto;padding:{VALEURS['padSection']} 5cqw">
    <div class="dc-surtitre">{e(surtitre)}</div>
    <h2 style="margin:0 0 20px;font-size:clamp(24px,3.4cqw,40px);font-weight:700;letter-spacing:-1px">{nom_avec_b_du_logo(e(titre))}</h2>
    <p style="margin:0;font-size:clamp(17px,1.9cqw,21px);line-height:1.5;color:#1B2129;max-width:62ch">{e(p1)}</p>
    <div style="margin-top:26px;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:28px">
      <p style="margin:0;font-size:16px;line-height:1.6;color:#39424E">{e(p2)}</p>
      <p style="margin:0;font-size:16px;line-height:1.6;color:#39424E">{e(p3)}</p>
    </div>
    {savoir_plus}
  </section>
'''

    # ── LE FAISCEAU DOIT COUVRIR LES DEUX SECTIONS, PAS UNE ─────────────────
    #
    # Il vivait DANS la section « avant / avec », qui le rogne à son bord haut :
    # ses arcs s'interrompaient donc net sous la rubrique de définition, et la
    # définition paraissait les masquer. Aucun réglage de taille ou de position
    # n'y pouvait rien — le rognage tient à l'endroit où le faisceau est posé.
    #
    # On le sort de cette section et on l'installe dans une enveloppe qui contient
    # les deux. Ses arcs montent alors derrière le texte de la définition, ce qui
    # est précisément l'effet recherché.
    section = corps[debut:fin_section]
    m_svg = re.search(r'<svg\b[^>]*id="traits-balistiques"', section)
    faisceau = ''
    if m_svg:
        _, _, fin_svg = bloc_equilibre(section, m_svg.start(), 'svg')
        faisceau = section[m_svg.start():fin_svg]
        section = section[:m_svg.start()] + section[fin_svg:]

    enveloppe = (
        '\n  <div class="dc-zone-traits" style="position:relative;overflow:hidden">\n'
        + faisceau
        + bloc
        + section
        + '\n  </div>\n'
    )
    return corps[:debut] + enveloppe + corps[fin_section:]


# ══ LE CARROUSEL DE LA PAGE D'ACCUEIL ═════════════════════════════════════════
#
# La maquette montrait UNE capture, posée seule au milieu de la page. Les sites
# de référence cités (Datamine, Deswik) font défiler plusieurs vues, et c'est
# justifié ici : la valeur du logiciel tient à ce qu'il affiche, et une seule
# image ne montre ni les cadrans, ni le plan produit, ni la fusion de plusieurs
# tirs.
#
# Deux des quatre vues existent déjà dans la maquette. Les deux autres attendent
# une capture : elles s'affichent en cadre nommé plutôt qu'en rectangle vide,
# pour qu'on sache ce qui manque au lieu de croire à une panne.

# UNE VUE SANS IMAGE N'EST PAS PUBLIÉE.
#
# Les deux dernières attendent une capture. Tant qu'elles n'en ont pas, elles sont
# écartées du carrousel : un visiteur n'a pas à lire « Capture à insérer » sur une
# page commerciale, et un cadre d'attente se lit comme une page inachevée.
#
# POUR LES RÉTABLIR : déposer le fichier dans site/assets/img/ et remplacer None par
# son chemin, '../assets/img/le-fichier.png'. La légende correspondante est déjà
# traduite dans les treize langues, rien d'autre n'est à faire.
DIAPOS = [
    ('../assets/design/app-screen.jpg', 0),
    ('../assets/design/pit-dome.jpg', 1),
    (None, 2),   # plan PDF produit
    (None, 3),   # fusion de plusieurs tirs
]

# Quatre légendes par langue, plus le surtitre de la section et les commandes.
# Ordre : surtitre, légende 1 à 4, précédent, suivant, libellé de la pastille.
LEGENDES = {
    'fr': ["L'APPLICATION", "Dôme d'évacuation calculé sur la topographie réelle",
           "Fosse et contours de tir importés en DXF",
           "Plan PDF avec cartouche, cotation et nord",
           "Fusion de plusieurs tirs en un périmètre unique",
           "Vue précédente", "Vue suivante", "Aller à la vue"],
    'en': ["THE SOFTWARE", "Exclusion dome computed on the real topography",
           "Pit and blast outlines imported from DXF",
           "PDF drawing with title block, dimensions and north",
           "Several blasts merged into a single perimeter",
           "Previous view", "Next view", "Go to view"],
    'es': ["LA APLICACIÓN", "Cúpula de evacuación calculada sobre la topografía real",
           "Rajo y contornos de voladura importados en DXF",
           "Plano PDF con cajetín, acotación y norte",
           "Varias voladuras fusionadas en un único perímetro",
           "Vista anterior", "Vista siguiente", "Ir a la vista"],
    'pt': ["A APLICAÇÃO", "Cúpula de evacuação calculada sobre a topografia real",
           "Cava e contornos de desmonte importados em DXF",
           "Desenho PDF com legenda, cotagem e norte",
           "Vários desmontes fundidos num único perímetro",
           "Vista anterior", "Vista seguinte", "Ir para a vista"],
    'it': ["L'APPLICAZIONE", "Cupola di evacuazione calcolata sulla topografia reale",
           "Cava e contorni di volata importati in DXF",
           "Disegno PDF con cartiglio, quotatura e nord",
           "Più volate fuse in un unico perimetro",
           "Vista precedente", "Vista successiva", "Vai alla vista"],
    'de': ["DIE ANWENDUNG", "Sicherheitskuppel auf der realen Topografie berechnet",
           "Tagebau und Sprengkonturen aus DXF importiert",
           "PDF-Plan mit Schriftfeld, Bemaßung und Nordpfeil",
           "Mehrere Sprengungen zu einem Perimeter verschmolzen",
           "Vorherige Ansicht", "Nächste Ansicht", "Zur Ansicht"],
    'nl': ["DE TOEPASSING", "Veiligheidskoepel berekend op de werkelijke topografie",
           "Dagbouw en schietcontouren geïmporteerd uit DXF",
           "PDF-tekening met titelblok, bemating en noorden",
           "Meerdere schoten samengevoegd tot één perimeter",
           "Vorige weergave", "Volgende weergave", "Ga naar weergave"],
    'sv': ["PROGRAMMET", "Säkerhetskupol beräknad på den verkliga topografin",
           "Dagbrott och salvkonturer importerade från DXF",
           "PDF-ritning med ritningshuvud, måttsättning och norr",
           "Flera salvor sammanslagna till en enda perimeter",
           "Föregående vy", "Nästa vy", "Gå till vy"],
    'no': ["PROGRAMMET", "Sikkerhetskuppel beregnet på den virkelige topografien",
           "Dagbrudd og salvekonturer importert fra DXF",
           "PDF-tegning med tittelfelt, målsetting og nord",
           "Flere salver slått sammen til én perimeter",
           "Forrige visning", "Neste visning", "Gå til visning"],
    'da': ["PROGRAMMET", "Sikkerhedskuppel beregnet på den virkelige topografi",
           "Brud og sprængningskonturer importeret fra DXF",
           "PDF-tegning med tegningshoved, målsætning og nord",
           "Flere sprængninger samlet til én perimeter",
           "Forrige visning", "Næste visning", "Gå til visning"],
    'af': ["DIE PROGRAM", "Veiligheidskoepel bereken op die werklike topografie",
           "Oopgroef en skietkontoere ingevoer uit DXF",
           "PDF-tekening met titelblok, afmetings en noord",
           "Verskeie skote saamgevoeg tot een omtrek",
           "Vorige aansig", "Volgende aansig", "Gaan na aansig"],
    'tr': ["UYGULAMA", "Gerçek topoğrafya üzerinde hesaplanan güvenlik kubbesi",
           "DXF'ten alınan ocak ve atım konturları",
           "Antet, ölçülendirme ve kuzey içeren PDF planı",
           "Birden çok atımın tek bir çevrede birleştirilmesi",
           "Önceki görünüm", "Sonraki görünüm", "Görünüme git"],
    'zh': ["软件界面", "基于真实地形计算的疏散穹顶",
           "从 DXF 导入的采坑与爆破轮廓",
           "带图签、标注和指北针的 PDF 图纸",
           "多次爆破合并为单一警戒范围",
           "上一张", "下一张", "转到第"],
}

# ══ ANALYSE DES BALISES ═══════════════════════════════════════════════════════


def bloc_equilibre(texte: str, debut: int, balise: str) -> tuple[int, int, int]:
    """Trouve la fin d'une balise ouvrante et la fin de son bloc, en comptant les
    imbrications. Un simple `.*?` s'arrêterait à la première fermeture venue, ce
    qui découperait au mauvais endroit dès qu'une condition en contient une autre."""
    ouvrante = re.compile(r'<' + balise + r'\b', re.I)
    fermante = re.compile(r'</' + balise + r'\s*>', re.I)
    fin_ouvrante = texte.index('>', debut) + 1
    profondeur = 1
    i = fin_ouvrante
    while profondeur:
        o = ouvrante.search(texte, i)
        f = fermante.search(texte, i)
        if not f:
            raise ValueError(f'<{balise}> non refermée à {debut}')
        if o and o.start() < f.start():
            profondeur += 1
            i = o.end()
        else:
            profondeur -= 1
            i = f.end()
    return fin_ouvrante, i - len(f.group(0)), i


def ajouter_classe(fragment: str, classe: str) -> str:
    """Pose une classe sur chaque élément de premier niveau du fragment."""
    sortie, i = [], 0
    while i < len(fragment):
        j = fragment.find('<', i)
        if j < 0:
            sortie.append(fragment[i:])
            break
        sortie.append(fragment[i:j])
        if fragment.startswith('</', j) or fragment.startswith('<!', j):
            k = fragment.index('>', j) + 1
            sortie.append(fragment[j:k])
            i = k
            continue
        nom = re.match(r'<([a-zA-Z][\w-]*)', fragment[j:])
        if not nom:
            sortie.append(fragment[j])
            i = j + 1
            continue
        try:
            _, _, fin = bloc_equilibre(fragment, j, nom.group(1))
        except ValueError:
            fin = fragment.index('>', j) + 1
        element = fragment[j:fin]
        m = re.match(r'(<[a-zA-Z][\w-]*)', element)
        element = m.group(1) + f' class="{classe}"' + element[m.end():]
        sortie.append(element)
        i = fin
    return ''.join(sortie)


def resoudre_conditions(texte: str) -> str:
    """Remplace chaque <sc-if> par le traitement décidé pour sa variable."""
    while True:
        m = re.search(r'<sc-if\b[^>]*value="\{\{\s*(\w+)\s*\}\}"', texte)
        if not m:
            return texte
        variable = m.group(1)
        debut_contenu, fin_contenu, fin_bloc = bloc_equilibre(texte, m.start(), 'sc-if')
        contenu = texte[debut_contenu:fin_contenu]
        action = CONDITIONS.get(variable, 'garder')
        if action == 'retirer':
            remplacement = ''
        elif action.startswith('classe:'):
            remplacement = ajouter_classe(contenu, action.split(':', 1)[1])
        elif action == 'replier':
            remplacement = ajouter_classe(contenu, 'dc-langues-panneau').replace(
                '<div class="dc-langues-panneau"', '<div class="dc-langues-panneau" id="panneau-langues" hidden', 1)
        else:
            remplacement = contenu
        texte = texte[:m.start()] + remplacement + texte[fin_bloc:]


def convertir_survols(texte: str) -> tuple[str, str]:
    """`style-hover` n'existe que dans l'éditeur. On en fait de vraies règles CSS,
    une par occurrence, attachées à une classe numérotée."""
    regles, compteur = [], 0

    def remplacer(m):
        nonlocal compteur
        compteur += 1
        classe = f'dc-h{compteur}'
        declarations = htmlmod.unescape(m.group(1)).rstrip(';')
        regles.append(f'.{classe}:hover,.{classe}:focus-visible{{{declarations}}}')
        return f' data-survol="{classe}"'

    texte = re.sub(r'\sstyle-hover="([^"]*)"', remplacer, texte)

    # La classe est posée sur l'élément qui portait l'attribut, en fusionnant
    # avec une classe déjà présente plutôt qu'en la remplaçant.
    def poser(m):
        balise = m.group(0)
        classe = m.group(1)
        balise = balise.replace(f' data-survol="{classe}"', '')
        if 'class="' in balise:
            return re.sub(r'class="([^"]*)"', lambda c: f'class="{c.group(1)} {classe}"', balise, count=1)
        return re.sub(r'^<([a-zA-Z][\w-]*)', rf'<\1 class="{classe}"', balise)

    texte = re.sub(r'<[a-zA-Z][\w-]*[^>]*\sdata-survol="(dc-h\d+)"[^>]*>', poser, texte)
    return texte, '\n'.join(regles)


# ══ TEXTE ET MÉTADONNÉES ══════════════════════════════════════════════════════


def texte_nu(fragment: str) -> str:
    return re.sub(r'\s+', ' ', htmlmod.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def extraire_metadonnees(corps: str) -> tuple[str, str]:
    """Le titre et la description viennent du bandeau de la page elle-même : c'est
    ce qui les rend justes dans les treize langues sans table de traduction."""
    h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', corps, re.S)
    titre = texte_nu(h1.group(1)) if h1 else 'BlastClear'
    titre = re.sub(r'\s*\|\s*', ' ', titre)
    if len(titre) > 62:
        titre = titre[:59].rsplit(' ', 1)[0] + '…'
    p = re.search(r'</h1>\s*<p\b[^>]*>(.*?)</p>', corps, re.S)
    description = texte_nu(p.group(1)) if p else ''
    return f'BlastClear | {titre}', description[:180]


# ══ RÉÉCRITURES DE CONTENU ════════════════════════════════════════════════════


def rectifier_resultats(corps: str, langue: dict) -> str:
    """Deux corrections dans la section des résultats.

    Le titre annonçait des résultats « mesurés » alors que les chiffres sont des
    estimations, et le paragraphe de conclusion affirmait qu'aucun incident
    n'était survenu. Une page web est un document opposable : cette phrase
    engagerait l'éditeur au premier incident, et personne ne pourrait produire la
    mesure qui la fonde."""
    m = re.search(r'<section id="preuves".*?</section>', corps, re.S)
    if not m:
        return corps
    section = m.group(0)

    section = re.sub(r'(<h2\b[^>]*>)(.*?)(</h2>)',
                     lambda h: h.group(1) + htmlmod.escape(langue['resultats']) + h.group(3),
                     section, count=1, flags=re.S)

    # Le dernier paragraphe de la section est celui du déploiement.
    paragraphes = list(re.finditer(r'<p\b[^>]*>.*?</p>', section, re.S))
    if paragraphes:
        dernier = paragraphes[-1]
        note = ('<p style="margin:0;font-size:14px;line-height:1.5;color:#C3CBD4;max-width:760px">'
                + htmlmod.escape(langue['note']) + '</p>')
        section = section[:dernier.start()] + note + section[dernier.end():]

    return corps[:m.start()] + section + corps[m.end():]


def rectifier_liens(corps: str, langue_courante: str) -> str:
    """Les canevas se pointent entre eux par leur nom de fichier. Le site publié
    range chaque langue dans son dossier : les liens doivent suivre."""
    for code, langue in LANGUES.items():
        nom = f"Canvas BlastClear.com{langue['suffixe']}.dc.html"
        cible = './' if code == langue_courante else f'../{code}/'
        for variante in (nom, nom.replace(' ', '%20')):
            corps = corps.replace(f'href="{variante}"', f'href="{cible}"')

    # Le canevas de demande porte les treize langues dans un seul fichier ; on en
    # tire une page par dossier, donc chaque langue reste chez elle.
    #
    # LA SUBSTITUTION DOIT ABSORBER LE PARAMÈTRE D'URL. Les douze canevas traduits
    # écrivent « …dc.html?lang=EN » là où le français écrit « …dc.html ». Une
    # comparaison sur la chaîne exacte ne reconnaissait donc que le français, et les
    # douze autres pages conservaient un lien vers un fichier qui n'existe pas : le
    # bouton « Demander une démo » n'y menait nulle part, sans le moindre message.
    #
    # Le paramètre lui-même n'a plus d'objet : il servait à dire au canevas unique
    # quelle langue afficher, alors qu'il y a désormais une page par langue.
    corps = re.sub(
        r'href="Demande(?:%20| )de(?:%20| )d(?:%C3%A9|é)mo\.dc\.html(?:\?[^"]*)?"',
        'href="demo.html"', corps)
    return corps


MAISON_SVG = (
    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" '
    'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
    'style="flex:none"><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20h13V9.5"/>'
    '<path d="M9.75 20v-5.5h4.5V20"/></svg>'
)


def retour_accueil(mots: dict) -> str:
    """Le bouton qui clôt la page de remerciement.

    Une page de remerciement sans issue laisse le visiteur sur une impasse : il n'a
    plus qu'à employer le bouton Précédent, qui le ramènerait au formulaire qu'il
    vient d'envoyer. Ce bouton lui rend l'accueil."""
    texte = str(mots.get('retour', '')).lstrip('←⟵<- ').strip() or 'Home'
    return (
        '<a class="dc-retour" href="./" style="margin-top:28px;display:inline-flex;'
        'align-items:center;gap:8px;background:#FDC30E;color:#14171C;font-weight:600;'
        'font-size:15px;padding:11px 22px;border-radius:2px;text-decoration:none">'
        + MAISON_SVG + '<span>' + htmlmod.escape(texte) + '</span></a>'
    )


_TABLE_DEMO: dict = {}


def mot_retour(code: str) -> str:
    """Le libellé « retour à l'accueil » dans la langue demandée.

    ─── IL EST PRIS À SA SOURCE, NON RECOPIÉ ────────────────────────────────
    Les treize traductions existent déjà dans le canevas de demande, qui porte sa
    table de langues. En écrire une seconde série ici donnerait deux jeux de mots
    pour la même idée, qui divergeraient à la première correction de l'un des deux.
    La table est lue une fois puis gardée, la conversion visitant treize langues.

    La flèche est retirée du libellé : elle est remplacée par la maison, et « ← »
    se confondrait avec le bouton Précédent du navigateur."""
    global _TABLE_DEMO
    if not _TABLE_DEMO:
        demo = SOURCE / 'Demande de démo.dc.html'
        _TABLE_DEMO = (lire_table(demo.read_text(encoding='utf-8'), 'L')
                       if demo.exists() else {'EN': {}})
    mots = _TABLE_DEMO.get(code.upper()) or _TABLE_DEMO.get('EN') or {}
    return str(mots.get('retour', '')).lstrip('←⟵<- ').strip() or 'Home'


def poser_lien_accueil(corps: str, mots: dict) -> str:
    """Remplace la flèche du lien de retour par une maison.

    ─── POURQUOI UNE MAISON PLUTÔT QU'UNE FLÈCHE ──────────────────────────────
    « ← » dit « en arrière », ce qui se confond avec le bouton Précédent du
    navigateur. Or ce lien ne revient pas d'un pas : il ramène à l'accueil, quel
    que soit le chemin emprunté pour arriver là. La maison dit exactement cela,
    dans les treize langues, sans dépendre du texte.

    Le libellé reste, amputé de sa flèche : une icône seule oblige à deviner, et
    les treize traductions du texte existent déjà.
    """
    texte = str(mots.get('retour', '')).lstrip('←⟵<- ').strip()
    if not texte:
        return corps

    # La substitution vise le lien du bandeau, reconnu à son libellé de retour.
    # On le reconstruit en ligne flexible, pour que l'icône et le texte restent
    # alignés sur leur ligne médiane quelle que soit la taille de police.
    motif = re.compile(
        r'(<a\b[^>]*href="\./"[^>]*style=")([^"]*)("[^>]*>)\s*'
        + re.escape(htmlmod.escape(str(mots.get('retour', ''))))
        + r'\s*(</a>)')

    def remplacer(m):
        style = m.group(2).rstrip(';')
        style += ';display:inline-flex;align-items:center;gap:7px'
        return (m.group(1) + style + m.group(3)
                + MAISON_SVG + '<span>' + htmlmod.escape(texte) + '</span>' + m.group(4))

    return motif.sub(remplacer, corps, count=1)


def verifier_liens(corps: str, source: str, code: str) -> None:
    """AUCUN LIEN NE DOIT ENCORE DÉSIGNER UN CANEVAS.

    ─── LE DÉFAUT QUE CE CONTRÔLE AURAIT ÉVITÉ ────────────────────────────────
    Le contrôle des marqueurs ne voit que les {{ }}. Un lien vers un fichier
    .dc.html, lui, est du HTML parfaitement valide : il passait sans rien
    déclencher, et la page publiée portait un bouton qui ne menait nulle part.

    C'est ce qui est arrivé aux douze pages traduites. Leur lien de demande de
    démonstration comportait un paramètre, « ?lang=EN », que la substitution ne
    reconnaissait pas : elle ne traitait que la forme exacte, sans paramètre, celle
    du seul canevas français. Douze pages sur treize ont donc été mises en ligne
    avec un appel à l'action inerte, et rien ne l'a signalé.

    À appeler EN FIN de conversion, une fois les liens réécrits.
    """
    canevas = sorted(set(re.findall(r'href="([^"]*\.dc\.html[^"]*)"', corps)))
    if canevas:
        raise SystemExit(
            f'{source} [{code}] : lien(s) vers un canevas non réécrit(s) :\n  '
            + '\n  '.join(canevas)
            + '\nCompléter rectifier_liens.'
        )


def rectifier_ressources(corps: str) -> str:
    corps = corps.replace('src="assets/logo-dark.svg"', 'src="../assets/logo/Logo_BlastClear_FondSombre_web.svg"')
    corps = corps.replace('src="assets/logo-light.svg"', 'src="../assets/logo/Logo_BlastClear_web.svg"')
    corps = corps.replace('src="assets/', 'src="../assets/design/')
    return corps


def construire_carrousel(code: str) -> str:
    """Le carrousel qui remplace la capture unique de la maquette.

    ─── IL FONCTIONNE SANS JAVASCRIPT ─────────────────────────────────────────
    Les quatre vues sont dans le HTML, dans une bande qui défile horizontalement
    avec scroll-snap. Sans script, on fait glisser à la main ou au clavier et
    tout reste atteignable. Le script n'ajoute que l'avance automatique et les
    pastilles actives.

    ─── ET IL NE PIÈGE PAS LE CLAVIER ─────────────────────────────────────────
    Les commandes sont de vrais boutons, la bande est une région annoncée, et
    l'avance automatique s'arrête au survol comme au focus. Un carrousel qui
    repart pendant qu'on lit est la faute la plus courante du genre."""
    t = LEGENDES.get(code, LEGENDES['en'])
    surtitre, precedent, suivant, aller = t[0], t[5], t[6], t[7]

    # Seules les vues pourvues d'une image sont publiées, cf. DIAPOS.
    disponibles = [(image, rang) for image, rang in DIAPOS if image]
    if not disponibles:
        return ''

    vues = []
    for i, (image, rang) in enumerate(disponibles):
        legende = htmlmod.escape(t[1 + rang])
        # La première vue se charge sans délai : elle est vue tout de suite après le
        # bandeau, et un chargement paresseux y laisse un cadre gris le temps que le
        # navigateur se décide. Les suivantes ne doivent pas peser sur l'affichage
        # initial.
        chargement = ('loading="eager" fetchpriority="high"' if i == 0
                      else 'loading="lazy" fetchpriority="low"')
        visuel = (f'<img src="{image}" alt="{legende}" {chargement} decoding="async" '
                  f'style="width:100%;height:100%;object-fit:cover;display:block">')
        vues.append(
            f'<li class="dc-vue" id="vue-{code}-{i}" aria-label="{i + 1} / {len(disponibles)}">'
            f'<div class="dc-vue-cadre">{visuel}</div>'
            f'<p class="dc-vue-legende">{legende}</p></li>'
        )

    # Une seule vue n'est pas un carrousel : ni flèches, ni pastilles, ni rotation.
    commandes = len(disponibles) > 1
    pastilles = ''.join(
        f'<button type="button" class="dc-pastille" data-va="{i}" '
        f'aria-label="{htmlmod.escape(aller)} {i + 1}"></button>'
        for i in range(len(disponibles))
    ) if commandes else ''

    fleches = f'''        <button type="button" class="dc-fleche dc-fleche--avant" data-recule aria-label="{htmlmod.escape(precedent)}">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 5 8 12 15 19"/></svg>
        </button>
        <button type="button" class="dc-fleche dc-fleche--apres" data-avance aria-label="{htmlmod.escape(suivant)}">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 5 16 12 9 19"/></svg>
        </button>
''' if commandes else ''

    return f'''
  <section class="dc-carrousel" data-carrousel style="background:#F4F6F8;padding:{VALEURS['padSection']} 5cqw">
    <div style="max-width:1120px;margin:0 auto">
      <div class="dc-surtitre">{htmlmod.escape(surtitre)}</div>
      <div class="dc-carrousel-corps">
        <ul class="dc-bande" tabindex="0" role="group" aria-roledescription="carrousel" aria-label="{htmlmod.escape(surtitre)}">
{''.join('          ' + v + chr(10) for v in vues)}        </ul>
{fleches}      </div>
      <div class="dc-pastilles">{pastilles}</div>
    </div>
  </section>
'''


def remplacer_section_application(corps: str, code: str) -> str:
    """Substitue le carrousel à la section qui ne portait qu'une capture."""
    for m in re.finditer(r'<section\b(?![^>]*\bid=)[^>]*>.*?</section>', corps, re.S):
        if 'app-screen.jpg' in m.group(0):
            return corps[:m.start()] + construire_carrousel(code) + corps[m.end():]
    return corps


def poser_animations(corps: str) -> str:
    """Marque les blocs que le script fera apparaître au défilement.

    Le marquage se fait ICI et non dans le script, pour que le repère soit dans
    le HTML : une section ajoutée plus tard sans la classe reste simplement
    visible, au lieu de disparaître parce qu'un sélecteur ne l'a pas prévue."""
    corps = re.sub(r'<(section|header|footer)\b', r'<\1 data-anime', corps, flags=re.I)
    # Les compteurs de la section des résultats.
    corps = re.sub(
        r'(<div style="font-size:30px;font-weight:700;line-height:1">)([^<]+)(</div>)',
        r'\1<span class="dc-compteur">\2</span>\3', corps)
    return corps


# ══ LE FORMULAIRE ═════════════════════════════════════════════════════════════


# ══ OÙ PARTENT LES DEMANDES DE DÉMONSTRATION ══════════════════════════════════
#
# Tant que COLLECTE_URL est vide, le formulaire ouvre le logiciel de messagerie du
# visiteur : rien ne transite par un tiers, et il n'y a rien à installer. Dès qu'une
# adresse y figure, le formulaire l'appelle et le visiteur n'a plus qu'un clic à
# faire.
#
# L'adresse attendue est celle d'une application web Google Apps Script, déployée
# depuis la feuille de calcul. Le script et sa procédure d'installation sont dans
# outils/formulaire/.
#
# LE JETON DOIT ÊTRE LE MÊME DES DEUX CÔTÉS. Il ne protège aucun secret : il filtre
# les envois automatisés, qui arrivent tôt ou tard sur une application web ouverte.

COLLECTE_URL = ''
JETON_FORMULAIRE = 'REMPLACER_PAR_UNE_CHAINE_A_VOUS'


def rectifier_formulaire(corps: str, code: str = 'fr') -> str:
    """Branche le formulaire sur sa destination.

    ─── DEUX MODES, ET UN SEUL INTERRUPTEUR ───────────────────────────────────
    Sans service de collecte configuré, le formulaire compose un courriel dans la
    messagerie du visiteur : aucune donnée ne passe par un intermédiaire, et il n'y
    a rien à configurer. Le script de la page reconnaît ce mode à l'absence
    d'attribut action.

    Avec un service configuré, le même script poste vers lui et conduit ensuite à la
    page de remerciement.

    ─── LES TROIS CHAMPS CACHÉS ───────────────────────────────────────────────
    jeton  : filtre les envois automatisés.
    langue : dit depuis quelle version le prospect a écrit, ce qui indique en quelle
             langue lui répondre. L'information n'existe nulle part ailleurs.
    site   : champ-piège. Invisible, donc toujours vide chez un humain ; un automate
             remplit tout ce qu'il trouve et se signale ainsi lui-même.
    """
    caches = (
        f'<input type="hidden" name="jeton" value="{htmlmod.escape(JETON_FORMULAIRE, quote=True)}">'
        f'<input type="hidden" name="langue" value="{code}">'
        '<input type="text" name="site" tabindex="-1" autocomplete="off" '
        'aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px">'
    )

    if COLLECTE_URL:
        ouverture = (f'<form action="{htmlmod.escape(COLLECTE_URL, quote=True)}" method="POST" '
                     'data-collecte="oui"')
    else:
        ouverture = '<form data-courriel="contact@blastclear.com"'

    corps = corps.replace('<form', ouverture, 1)
    return re.sub(r'(<form\b[^>]*>)', r'\1' + caches, corps, count=1)


# ══ FEUILLE ET SCRIPT COMMUNS ═════════════════════════════════════════════════

CSS_COMMUN = """/* ════════════════════════════════════════════════════════════════════════════
   HABILLAGE COMMUN DES PAGES ISSUES DE LA MAQUETTE.

   Les canevas portent leur mise en forme en style en ligne, élément par
   élément. Ce fichier ne contient donc que ce qu'un style en ligne ne sait pas
   exprimer : les polices, les survols, les seuils d'écran, et les animations.
   ════════════════════════════════════════════════════════════════════════ */

@font-face{font-family:'Poppins';font-style:normal;font-weight:300;font-display:swap;
  src:url('../assets/fonts/poppins-300.woff2') format('woff2')}
@font-face{font-family:'Poppins';font-style:normal;font-weight:400;font-display:swap;
  src:url('../assets/fonts/poppins-400.woff2') format('woff2')}
@font-face{font-family:'Poppins';font-style:normal;font-weight:600;font-display:swap;
  src:url('../assets/fonts/poppins-600.woff2') format('woff2')}
@font-face{font-family:'Poppins';font-style:normal;font-weight:700;font-display:swap;
  src:url('../assets/fonts/poppins-700.woff2') format('woff2')}

:root{
  --bc-bleu:#25498A; --bc-jaune:#FDC30E; --bc-anthracite:#14171C;
  --bc-ocre:#8A6200; --bc-magenta:#FF1493;
}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#ffffff;font-family:'Poppins','Segoe UI',system-ui,sans-serif}
img,svg{max-width:100%}
a{color:var(--bc-bleu);text-decoration:none;transition:color .18s ease}

/* Le contour de focus doit se voir sur le bleu comme sur le blanc. */
:focus-visible{outline:3px solid var(--bc-jaune);outline-offset:3px;border-radius:2px}

.saut-au-contenu{position:absolute;left:-9999px;top:0;z-index:100;background:var(--bc-jaune);
  color:var(--bc-anthracite);padding:.7rem 1.2rem;font-weight:600}
.saut-au-contenu:focus{left:0}

/* ══ SEUIL D'ÉCRAN ═════════════════════════════════════════════════════════
   La maquette basculait entre deux rendus par une mesure de largeur faite en
   JavaScript. Ici c'est une requête de média : le bon rendu est déjà en place
   au premier affichage, sans attendre l'exécution d'un script. */
.dc-petit{display:none !important}
@media (max-width:719px){
  .dc-large{display:none !important}
  .dc-petit{display:flex !important}
}

/* ══ LE MENU DES LANGUES ═══════════════════════════════════════════════════
   Le !important n'est pas une facilité : le panneau porte un display:grid EN
   STYLE EN LIGNE, hérité de la maquette, et un style en ligne l'emporte sur
   toute règle de feuille. Sans lui, le menu des langues s'affiche déplié au
   chargement de chaque page. */
.dc-langues-panneau[hidden]{display:none !important}
.dc-langues-panneau{animation:dc-deplier .18s ease both}

/* ── LE PANNEAU SORTAIT DE L'ÉCRAN SUR TÉLÉPHONE ──────────────────────────
   La maquette l'ancre par la DROITE du bouton, ce qui convient sur un écran
   large où le sélecteur est à droite de la barre. Sur téléphone la barre passe
   à la ligne, le sélecteur se retrouve à gauche, et un panneau de 360 px ancré
   par sa droite déborde alors HORS DE L'ÉCRAN par la gauche : sept langues sur
   treize devenaient illisibles, coupées au bord.

   On l'ancre donc par la gauche et on borne sa largeur à celle de l'écran. Le
   !important est requis : le positionnement vient d'un style en ligne. */
@media (max-width:719px){
  .dc-langues-panneau{
    left:0 !important; right:auto !important;
    width:min(360px,calc(100vw - 32px)) !important;
    grid-template-columns:1fr 1fr !important;
    max-height:60vh !important;
  }
}
/* Sous 380 px, deux colonnes rogneraient les noms les plus longs. */
@media (max-width:379px){
  .dc-langues-panneau{grid-template-columns:1fr !important}
}
@keyframes dc-deplier{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}

/* ══ APPARITION AU DÉFILEMENT ══════════════════════════════════════════════
   Le repère est posé dans le HTML (data-anime) et l'état visible est ajouté par
   le script. Conséquence voulue : sans JavaScript, RIEN n'est masqué, parce que
   la règle de départ n'est appliquée que lorsque le script a marqué la page. */
html.dc-anime [data-anime]{opacity:0;transform:translateY(26px);
  transition:opacity .7s cubic-bezier(.22,.61,.36,1),transform .7s cubic-bezier(.22,.61,.36,1)}
html.dc-anime [data-anime].dc-vu{opacity:1;transform:none}

/* ══ BARRE DE NAVIGATION ═══════════════════════════════════════════════════ */
nav[style*="sticky"]{transition:padding .25s ease,box-shadow .25s ease,background-color .25s ease}
nav[style*="sticky"].dc-defile{padding-top:8px !important;padding-bottom:8px !important;
  box-shadow:0 6px 22px rgba(20,23,28,.28)}
nav[style*="sticky"] img{transition:height .25s ease}
nav[style*="sticky"].dc-defile img{height:38px !important}

/* Le trait jaune qui se remplit sous la barre à mesure qu'on descend. */
.dc-progression{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:var(--bc-jaune);transition:width .1s linear}

/* ── LA BARRE RESTE EN HAUT, QUOI QU'IL ARRIVE AU CADRE ───────────────────
   Le cadre de la maquette est corrigé à la conversion, où `overflow-x:hidden`
   devient `overflow-x:clip` : `hidden` sur un seul axe entraîne l'autre en
   `auto`, ce qui fait du cadre un conteneur de défilement et prive la barre de
   son ancrage à la fenêtre.

   Cette règle est le filet : si une future retouche de la maquette réintroduit
   un rognage sur un ancêtre de la barre, elle la remet hors du flux plutôt que
   de la laisser repartir avec la page. Le rembourrage compense alors la hauteur
   qu'elle n'occupe plus. */
@supports not (overflow-x:clip){
  nav[style*="sticky"]{position:fixed !important;left:0;right:0;top:0}
  nav[style*="sticky"]+*{padding-top:78px}
}

/* ══ LES RÉSEAUX DU PIED DE PAGE ═══════════════════════════════════════════
   Les symboles sont en blanc sur le bleu de la charte, à 9,1:1. Le survol les
   passe en jaune : sur CE fond, le jaune tient 8,2:1, alors qu'il tomberait à
   1,62:1 sur blanc. C'est la seule raison pour laquelle il est employé ici.

   La zone cliquable fait 40 px pour un symbole de 20. */
.dc-reseaux{display:flex;align-items:center;gap:4px}
.dc-reseau{display:inline-flex;align-items:center;justify-content:center;
  width:40px;height:40px;color:#ffffff;opacity:.88;border-radius:2px;
  text-decoration:none;transition:color .18s ease,opacity .18s ease,background-color .18s ease}
@media (hover:hover){
  .dc-reseau:hover{color:var(--bc-jaune);opacity:1;background:rgba(255,255,255,.10)}
}
.dc-reseau:focus-visible{outline:2px solid var(--bc-jaune);outline-offset:2px;opacity:1}

/* ══ SURVOLS AJOUTÉS ═══════════════════════════════════════════════════════
   La maquette n'animait pas les colonnes de fonctionnalités. Le mouvement reste
   discret : trois pixels et une ombre, rien qui déplace le texte sous le
   curseur au point de le rendre difficile à viser. */
section#fonctionnalites>div>div{transition:transform .22s ease,box-shadow .22s ease}
@media (hover:hover){
  section#fonctionnalites>div>div:hover{transform:translateY(-3px);
    box-shadow:0 12px 30px rgba(20,23,28,.10)}
}
section#preuves>div>div>div{transition:transform .22s ease}
@media (hover:hover){section#preuves>div>div>div:hover{transform:translateX(3px)}}

a[style*="border-radius:2px"]{transition:background-color .18s ease,color .18s ease,
  opacity .18s ease,transform .18s ease}
a[style*="border-radius:2px"]:active{transform:translateY(1px)}

/* ══ FAISCEAU BALISTIQUE : LA PROJECTION DES BLOCS ═════════════════════════
   Chaque trajectoire se trace depuis le point de tir vers son point de chute,
   les dix se succèdent, le faisceau s'efface et le cycle reprend.

   ─── C'EST LE CSS QUI ANIME, ET NON LE SCRIPT ────────────────────────────
   Une première version pilotait les dix décalages image par image en
   JavaScript. Le script ne fait plus que MESURER chaque courbe et déclarer sa
   longueur, son sens et son retard ; l'animation, sa boucle et son rythme sont
   décrits ici. Trois raisons : le navigateur peut alors la confier au
   compositeur, elle continue de tourner quand le fil principal est occupé, et
   elle s'interrompt d'elle-même sur un réglage système d'animations réduites.

   ─── LE SENS DU TRACÉ VIENT DU SCRIPT ────────────────────────────────────
   --depart vaut la longueur de la courbe, positive ou NÉGATIVE. Le signe fait
   apparaître le trait par l'un ou l'autre bout, ce qui permet de partir du
   point de tir même quand le fichier décrit la courbe à l'envers. */

/* ══ LE BANDEAU : MONTRER LE DÔME EN ENTIER ════════════════════════════════

   ─── POURQUOI IL ÉTAIT TRONQUÉ, ET POURQUOI CE N'EST PAS UN RÉGLAGE ───────
   La photographie mesure 1600 × 893, et le dôme y occupe 61 % de la hauteur.
   L'image est affichée en « cover », qui remplit le cadre en rognant : la part
   verticale visible vaut le rapport de l'image divisé par celui du cadre. Sur un
   bandeau de 1900 × 450, cela fait 42 %. Le dôme ne peut donc PAS y tenir, quel
   que soit le cadrage choisi : il manque de la hauteur, pas du réglage.

   Le bandeau est donc rendu plus haut. À 1900 × 700, la part visible passe à
   66 %, et le dôme tient. Les bornes évitent les deux excès : jamais moins de
   420 px sur un portable, jamais plus de 720 px sur un grand écran, où un
   bandeau pleine hauteur repousserait tout le contenu hors de vue. */
header[style*="pit-dome"], .dc-bandeau{min-height:clamp(420px,62vh,720px)}
.dc-bandeau{display:flex;align-items:center}
.dc-bandeau>img{object-position:center 45% !important}

/* ══ LE VOILE ══════════════════════════════════════════════════════════════
   Il ne reste que ce qu'il faut pour lire le titre, et rien de plus.

   ─── POURQUOI ON NE PEUT PAS LE SUPPRIMER TOUT À FAIT ─────────────────────
   Le titre est en réserve blanche, et la photographie porte un ciel clair et des
   gradins ocre. Sans voile, le blanc sur ces zones descend sous le seuil de
   lisibilité : le titre ne disparaîtrait pas, il deviendrait pénible, ce qui est
   pire parce que personne ne le signale.

   Le voile est donc réduit au minimum ET complété par une ombre portée sur le
   seul texte. L'ombre ne touche pas la photographie : elle rend le titre lisible
   là où le voile ne l'est plus, ce qui permet d'alléger le voile d'autant.
   Elle ne s'applique évidemment pas au logo, que la charte en dispense. */
.dc-voile{
  background:
    linear-gradient(90deg,
      rgba(20,23,28,.62) 0%,
      rgba(20,23,28,.44) 28%,
      rgba(20,23,28,.10) 54%,
      rgba(20,23,28,0) 72%),
    linear-gradient(180deg,
      rgba(20,23,28,.10) 0%,
      rgba(20,23,28,0) 40%,
      rgba(20,23,28,.34) 100%);
}
.dc-bandeau h1,
.dc-bandeau p{text-shadow:0 2px 16px rgba(20,23,28,.8),0 1px 3px rgba(20,23,28,.75)}

/* Sous 900 px le texte prend toute la largeur : un dégradé horizontal laisserait
   sa fin sur la partie claire de la photographie. On revient au voile vertical. */
@media (max-width:899px){
  .dc-voile{
    background:linear-gradient(180deg,
      rgba(20,23,28,.50) 0%,
      rgba(20,23,28,.58) 30%,
      rgba(20,23,28,.76) 70%,
      rgba(20,23,28,.90) 100%);
  }
}

/* ══ LE LOGO ═══════════════════════════════════════════════════════════════
   Le faisceau du symbole est fait de fuseaux PLEINS, très fins, et non de traits :
   il n'y a aucune épaisseur de trait à augmenter. À petite taille, ces fuseaux
   tombent sous le pixel et le lissage les rend inégaux, ce que la charte annonce
   au paragraphe des tailles minimales.

   geometricPrecision demande au navigateur de privilégier la fidélité du tracé
   plutôt que la vitesse. Combiné à la taille d'affichage relevée, le faisceau
   redevient régulier. */
img[src*="Logo_BlastClear"]{shape-rendering:geometricPrecision}

/* ══ LE B DU LOGO, EMPLOYÉ COMME LETTRE ════════════════════════════════════
   Son montant gauche s'incurve et s'évase, à la manière d'une trajectoire, là
   où le B de Poppins a un montant droit. C'est la seule lettre dessinée du
   logotype.

   ─── LA LETTRE RESTE DANS LE TEXTE, SOUS LE DESSIN ────────────────────────
   Le B textuel n'est pas supprimé mais masqué visuellement : il reste dans le
   flux, donc « BlastClear » se copie, se recherche dans la page et s'énonce
   entier par un lecteur d'écran. Le dessin, lui, est marqué décoratif. Un mot
   dont une lettre serait une image sans texte dessous se copierait « lastClear ».

   La hauteur est donnée en em, sur la hauteur de capitale de Poppins : la lettre
   suit alors la taille du titre, qui varie avec la largeur de l'écran. */
.dc-nom{white-space:nowrap}
.dc-b-lettre{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
.dc-b{height:.705em;width:auto;vertical-align:baseline;fill:currentColor;
      margin-right:.012em;shape-rendering:geometricPrecision}

/* ── « CLEAR », COMME DANS LE LOGOTYPE ────────────────────────────────────
   Le logo compose « Blast » dans sa couleur dominante et « Clear » en jaune, en
   graisse normale. Le titre reprend les deux.

   Le crénage du titre est ANNULÉ sur ces cinq lettres. Un titre serré à -1,2 px
   convient à du 700, où les pleins sont larges ; appliqué à du 400, il colle les
   fûts du l et du e. Remettre la valeur normale sur le seul mot concerné garde le
   resserrement du reste du titre. */
.dc-clear{font-weight:400;color:var(--bc-jaune);letter-spacing:normal}

/* ══ LE FAISCEAU TENAIT MAL DANS SA SECTION ════════════════════════════════
   La maquette l'étale sur 170 % de la largeur. Le dessin ayant un rapport de
   1,77, cela le rend plus HAUT que large de beaucoup : sur une section de
   1400 px de large, il mesurait 2380 sur 1344, pour une section qui n'en fait
   que 430 de haut. Un tiers du faisceau y entrait, et ce tiers était sa partie
   basse : on voyait des jambes d'arcs sans sommet ni point de départ, coupées
   net au bord supérieur.

   Deux corrections, et la section respire : le faisceau est ramené à une
   largeur qui le fait tenir, et la section reçoit une hauteur minimale. */
.dc-traits{opacity:1;width:118% !important}

/* L'enveloppe couvre la définition ET la comparaison ; le faisceau y monte donc
   derrière le texte au lieu de s'arrêter à la frontière entre les deux. */
.dc-zone-traits>section{position:relative;z-index:1}
.dc-zone-traits>.dc-traits{z-index:0}

.dc-traits path{
  stroke-linecap:round;
  stroke-dasharray:var(--L) var(--L);
  stroke-dashoffset:var(--depart);
  opacity:0;
  animation:dc-projection var(--cycle,7.5s) linear var(--retard,0s) infinite both;
  animation-play-state:paused;
}
/* On ne fait tourner le faisceau que lorsqu'il est à l'écran. */
.dc-traits.dc-tire path{animation-play-state:running}

@keyframes dc-projection{
  /* Le vol : rapide au départ, ralenti à l'approche du point de chute. */
  0%   {stroke-dashoffset:var(--depart);opacity:0;   animation-timing-function:cubic-bezier(.16,.62,.28,1)}
  3%   {opacity:.45;                                 animation-timing-function:cubic-bezier(.16,.62,.28,1)}
  40%  {stroke-dashoffset:0;opacity:.45;             animation-timing-function:linear}
  /* La retombée reste affichée : c'est l'enveloppe que le logiciel calcule. */
  80%  {stroke-dashoffset:0;opacity:.45}
  94%  {stroke-dashoffset:0;opacity:0}
  /* Le retour au départ se fait hors de vue, sinon la courbe s'effacerait
     à rebours et donnerait un bloc qui revient au trou de mine. */
  100% {stroke-dashoffset:var(--depart);opacity:0}
}

@media (prefers-reduced-motion:reduce){
  .dc-traits path{animation:none;stroke-dashoffset:0;opacity:.38}
}

/* ══ CARROUSEL ═════════════════════════════════════════════════════════════
   La bande défile par scroll-snap, ce qui lui donne son glissement natif au
   doigt et à la molette sans une ligne de script. Le script ne fait que
   commander ce même défilement depuis les flèches et les pastilles : il n'y a
   donc qu'un seul mécanisme de déplacement, et pas deux à tenir d'accord. */

.dc-surtitre{font-size:12px;letter-spacing:2px;font-weight:600;color:var(--bc-bleu);
  text-transform:uppercase;margin-bottom:16px}

.dc-carrousel-corps{position:relative}

.dc-bande{display:flex;gap:18px;list-style:none;margin:0;padding:0 0 4px;
  overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;
  scrollbar-width:thin;scrollbar-color:var(--bc-bleu) #E4E8EC}
.dc-bande::-webkit-scrollbar{height:6px}
.dc-bande::-webkit-scrollbar-thumb{background:var(--bc-bleu);border-radius:3px}
.dc-bande::-webkit-scrollbar-track{background:#E4E8EC}

.dc-vue{flex:0 0 100%;scroll-snap-align:center;min-width:0}
.dc-vue-cadre{aspect-ratio:16/10;border:2px solid var(--bc-bleu);background:#14171C;
  overflow:hidden}
.dc-vue-cadre img{transition:transform 6s ease-out}
.dc-carrousel:hover .dc-vue-cadre img{transform:scale(1.03)}
.dc-vue-legende{margin:12px 0 0;font-size:13px;color:#5A6572;letter-spacing:.2px}

/* Ce qui tient la place d'une capture encore absente. Un cadre vide passerait
   pour une image qui n'a pas chargé ; celui-ci dit ce qu'il attend. */
.dc-vue-attendue{width:100%;height:100%;display:grid;place-content:center;gap:8px;
  text-align:center;padding:24px;color:#C3CBD4;
  background:repeating-linear-gradient(45deg,rgba(255,255,255,.03) 0 14px,transparent 14px 28px),#14171C}
.dc-vue-attendue span{font-size:15px;font-weight:600;color:#EDF0F4;max-width:30ch}
.dc-vue-attendue em{font-style:normal;font-size:12px;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--bc-jaune)}

.dc-fleche{position:absolute;top:calc(50% - 34px);transform:translateY(-50%);
  width:44px;height:44px;display:grid;place-content:center;cursor:pointer;
  border:none;border-radius:50%;background:var(--bc-bleu);color:#ffffff;
  box-shadow:0 6px 20px rgba(20,23,28,.28);
  transition:background-color .18s ease,color .18s ease,transform .18s ease,opacity .18s ease}
.dc-fleche--avant{left:-10px}
.dc-fleche--apres{right:-10px}
@media (hover:hover){
  .dc-fleche:hover{background:var(--bc-jaune);color:var(--bc-anthracite);transform:translateY(-50%) scale(1.07)}
}
.dc-fleche[disabled]{opacity:.35;cursor:default}
@media (max-width:719px){.dc-fleche{display:none}}

.dc-pastilles{display:flex;justify-content:center;gap:9px;margin-top:18px}
.dc-pastille{width:9px;height:9px;padding:0;border:none;border-radius:50%;cursor:pointer;
  background:#C3CBD4;transition:background-color .2s ease,width .2s ease}
.dc-pastille[aria-current="true"]{background:var(--bc-jaune);width:26px;border-radius:5px}

/* ══ PAGE DE DEMANDE ═══════════════════════════════════════════════════════ */
.dc-merci[hidden]{display:none}
.dc-merci{animation:dc-deplier .25s ease both}
form select:focus,form input:focus,form textarea:focus{border-color:var(--bc-bleu);outline-offset:1px}
form input,form textarea,form select{font-family:'Poppins','Segoe UI',system-ui,sans-serif}

/* ══ RESPECT DU RÉGLAGE SYSTÈME ════════════════════════════════════════════
   Ce n'est pas une politesse : le mouvement déclenche des malaises chez les
   personnes sujettes aux troubles vestibulaires, et le système le signale. */
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  html.dc-anime [data-anime]{opacity:1 !important;transform:none !important;transition:none}
  .dc-bande{scroll-behavior:auto}
  .dc-vue-cadre img,.dc-carrousel:hover .dc-vue-cadre img{transition:none;transform:none}
  *,*::before,*::after{animation-duration:.01ms !important;transition-duration:.01ms !important}
}
"""

JS_COMMUN = """/* ════════════════════════════════════════════════════════════════════════════
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
    var m = texte.match(/\\d+/);
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
        '&body=' + encodeURIComponent(lignes.join('\\r\\n'));

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
"""


# ══ ASSEMBLAGE D'UNE PAGE ═════════════════════════════════════════════════════

GABARIT = """<!doctype html>
<!-- PAGE ASSEMBLÉE PAR outils/convertir_design.py À PARTIR DE :
       design/BlastClear v2.0 flyer/{source}
     Ne pas corriger ce fichier : la prochaine conversion écraserait la
     correction. Modifier le canevas, ou le script. -->
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://www.blastclear.com/{lang}/{fichier}">
{alternats}
<meta property="og:type" content="website">
<meta property="og:locale" content="{locale}">
<meta property="og:site_name" content="BlastClear">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://www.blastclear.com/{lang}/{fichier}">
<meta property="og:image" content="https://www.blastclear.com/assets/design/app-screen.jpg">
<meta property="og:image:width" content="1500">
<meta property="og:image:height" content="900">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:alt" content="{titre}">
<meta name="twitter:card" content="summary_large_image">
{DONNEES_STRUCTUREES}
<meta name="theme-color" content="#25498A">
<link rel="icon" href="../assets/logo/favicon.ico" sizes="any">
<link rel="icon" href="../assets/logo/BlastClear_B_bleu_256.png" type="image/png">
<link rel="apple-touch-icon" href="../assets/logo/BlastClear_B_bleu_512.png">
<link rel="preload" href="../assets/fonts/poppins-600.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="../assets/fonts/poppins-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../css/design.css">
<style>
{survols}
</style>
</head>
<body>
<a class="saut-au-contenu" href="#contenu">{saut}</a>
<div id="contenu">
{corps}
</div>
<script src="../js/design.js" defer></script>
</body>
</html>
"""

def donnees_structurees(code: str, titre: str, description: str, fichier: str) -> str:
    """Les données structurées, à destination des moteurs de recherche.

    ─── CE QU'ELLES CHANGENT, ET CE QU'ELLES NE CHANGENT PAS ──────────────────
    Elles ne font pas monter un site dans les résultats. Elles disent ce qu'EST la
    page, dans un vocabulaire que les moteurs comprennent : un logiciel, son
    éditeur, la plateforme qu'il exige. C'est ce qui permet à une recherche
    « logiciel périmètre évacuation tir minier » de reconnaître un logiciel plutôt
    qu'un article qui en parle.

    ─── POURQUOI SEULEMENT SUR LA PAGE D'ACCUEIL ──────────────────────────────
    Déclarer le même logiciel sur cinquante pages n'apporte rien et brouille la
    lecture. Une page, une déclaration.

    Aucun prix n'y figure : la grille n'est pas publiée, et annoncer un prix dans
    les données structurées le rendrait visible dans les résultats de recherche,
    ce qui reviendrait à le publier par une autre porte.
    """
    if fichier:          # seules les pages d'accueil portent la déclaration
        return ''

    import json
    bloc = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "BlastClear",
        "url": f"https://www.blastclear.com/{code}/",
        "inLanguage": code,
        "description": description,
        "applicationCategory": "EngineeringApplication",
        "applicationSubCategory": "Mining and blasting engineering",
        "operatingSystem": "Windows 10, Windows 11",
        "softwareVersion": "2.2",
        "image": "https://www.blastclear.com/assets/design/app-screen.jpg",
        "author": {"@type": "Person", "name": "Anouar Zanbara"},
        "publisher": {"@type": "Person", "name": "Anouar Zanbara"},
        "offers": {"@type": "Offer", "availability": "https://schema.org/InStock"},
    }
    return ('<script type="application/ld+json">'
            + json.dumps(bloc, ensure_ascii=False, separators=(',', ':'))
            + '</script>')


SAUT = {
    'fr': 'Aller au contenu', 'en': 'Skip to content', 'es': 'Ir al contenido',
    'pt': 'Ir para o conteúdo', 'it': 'Vai al contenuto', 'de': 'Zum Inhalt springen',
    'nl': 'Naar de inhoud', 'sv': 'Till innehållet', 'no': 'Til innholdet',
    'da': 'Til indholdet', 'af': 'Gaan na inhoud', 'tr': 'İçeriğe geç', 'zh': '跳至内容',
}


def extraire_canevas(chemin: pathlib.Path) -> str:
    texte = chemin.read_text(encoding='utf-8')
    m = re.search(r'<x-dc>(.*?)</x-dc>', texte, re.S)
    if not m:
        raise SystemExit(f'{chemin.name} : pas de bloc <x-dc>. Fichier inattendu.')
    corps = m.group(1)
    # Le bloc <helmet> porte les polices distantes et un reset ; on fournit les
    # deux nous-mêmes, en local.
    return re.sub(r'<helmet>.*?</helmet>', '', corps, flags=re.S).strip()


def convertir(chemin: pathlib.Path, code: str, fichier: str) -> str:
    langue = LANGUES[code]
    corps = extraire_canevas(chemin)

    corps = resoudre_conditions(corps)

    for cle, valeur in VALEURS.items():
        corps = corps.replace('{{ ' + cle + ' }}', valeur)

    corps = corps.replace('onClick="{{ basculerLangues }}"', 'data-bascule-langues')
    corps = corps.replace('ref=""', 'id="traits-balistiques"')
    corps = re.sub(r'\sref="\{\{[^}]*\}\}"', ' id="traits-balistiques"', corps)
    corps = re.sub(r'\shint-placeholder-val="[^"]*"', '', corps)
    corps = re.sub(r'sc-camel-view-box=', 'viewBox=', corps)

    restants = sorted(set(re.findall(r'\{\{\s*(\w+)\s*\}\}', corps)))
    if restants:
        raise SystemExit(
            f'{chemin.name} : marqueur(s) non résolu(s) : {", ".join(restants)}.\n'
            "Ajouter la valeur dans VALEURS, ou le traitement dans CONDITIONS."
        )


    corps, survols = convertir_survols(corps)

    for motif, valeur in COULEURS:
        corps = re.sub(motif, valeur, corps) if motif.startswith('rgba') else corps.replace(motif, valeur)
        survols = re.sub(motif, valeur, survols) if motif.startswith('rgba') else survols.replace(motif, valeur)
    for ancienne, nouvelle in POLICES:
        corps = corps.replace(ancienne, nouvelle)

    corps = appliquer_corrections(corps, code, chemin.name)
    corps = aligner_adresse_affichee(corps)
    corps = nettoyer_typographie(corps)
    corps = renforcer_bandeau(corps)
    corps = rectifier_resultats(corps, langue)
    corps = rectifier_liens(corps, code)
    corps = rectifier_ressources(corps)
    corps = respecter_taille_minimale_logo(corps)
    corps = inliner_fond_balistique(corps)
    if fichier == 'index.html':
        corps = inserer_definition(corps, code)
        corps = remplacer_section_application(corps, code)
    corps = rectifier_formulaire(corps, code)
    corps = poser_animations(corps)
    corps = liberer_barre_collante(corps)
    corps = poser_reseaux(corps)
    verifier_liens(corps, chemin.name, code)

    titre, description = extraire_metadonnees(corps)

    alternats = '\n'.join(
        f'<link rel="alternate" hreflang="{c}" href="https://www.blastclear.com/{c}/">'
        for c in LANGUES
    # x-default désigne la page servie à qui ne correspond à aucune des langues
    # listées. C'est l'anglais, comme la racine du site : les deux doivent dire la
    # même chose, sans quoi un moteur annoncerait une destination et le visiteur en
    # trouverait une autre.
    ) + '\n<link rel="alternate" hreflang="x-default" href="https://www.blastclear.com/en/">'

    return GABARIT.format(
        source=chemin.name, lang=code, locale=langue['locale'],
        titre=htmlmod.escape(titre, quote=True),
        description=htmlmod.escape(description, quote=True),
        fichier='' if fichier == 'index.html' else fichier,
        alternats=alternats, survols=survols,
        DONNEES_STRUCTUREES=donnees_structurees(code, titre, description, '' if fichier == 'index.html' else fichier),
        saut=htmlmod.escape(SAUT.get(code, 'Skip to content')),
        corps=corps,
    )


# ══ LA PAGE DE DEMANDE DE DÉMONSTRATION ══════════════════════════════════════
#
# Ce canevas n'est pas une page traduite treize fois : c'est UNE page qui porte
# sa table de traduction et change de langue dans le navigateur. Le site publié
# a besoin de l'inverse, une page par langue, pour être indexable et pour que le
# lien /es/demo.html ouvre bien l'espagnol.

PAYS_PAR_DEFAUT = {
    'fr': 'FR', 'en': 'GB', 'es': 'ES', 'pt': 'PT', 'it': 'IT', 'de': 'DE',
    'nl': 'NL', 'sv': 'SE', 'no': 'NO', 'da': 'DK', 'af': 'ZA', 'tr': 'TR', 'zh': 'CN',
}


def objet_js_vers_json(texte: str) -> str:
    """Met des guillemets autour des clés nues d'un littéral d'objet JavaScript.

    La substitution ne peut pas se faire par une simple expression régulière :
    elle transformerait aussi ce qui ressemble à une clé À L'INTÉRIEUR d'une
    chaîne, par exemple le `https:` d'une adresse. Ce petit parcours suit donc
    l'état du texte et ne touche à rien tant qu'il est dans une chaîne."""
    sortie, i, n = [], 0, len(texte)
    dans_chaine = None
    while i < n:
        c = texte[i]
        if dans_chaine:
            sortie.append(c)
            if c == '\\':
                if i + 1 < n:
                    sortie.append(texte[i + 1])
                    i += 2
                    continue
            elif c == dans_chaine:
                dans_chaine = None
            i += 1
            continue
        if c in '"\'':
            dans_chaine = c
            sortie.append('"' if c == "'" else c)
            i += 1
            continue
        m = re.match(r'([A-Za-z_$][\w$]*)\s*:', texte[i:])
        if m:
            sortie.append(f'"{m.group(1)}":')
            i += m.end()
            continue
        sortie.append(c)
        i += 1
    # Les virgules finales sont licites en JavaScript, pas en JSON.
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(sortie))


def lire_table(script: str, nom: str) -> object:
    """Isole `const NOM = ...;` en comptant les accolades et crochets."""
    import json
    m = re.search(rf'\b(?:const|let|var)\s+{nom}\s*=\s*', script)
    if not m:
        raise SystemExit(f"Table {nom} introuvable dans le canevas de démonstration.")
    debut = m.end()
    ouvrants, fermants = {'{': '}', '[': ']'}, {'}': '{', ']': '['}
    pile, i, dans_chaine = [], debut, None
    while i < len(script):
        c = script[i]
        if dans_chaine:
            if c == '\\':
                i += 2
                continue
            if c == dans_chaine:
                dans_chaine = None
        elif c in '"\'':
            dans_chaine = c
        elif c in ouvrants:
            pile.append(c)
        elif c in fermants:
            pile.pop()
            if not pile:
                return json.loads(objet_js_vers_json(script[debut:i + 1]))
        i += 1
    raise SystemExit(f"Table {nom} non refermée.")


def selecteur_pays(dial: list, defaut: str, libelle: str) -> str:
    """Une liste déroulante native remplace le sélecteur d'indicatif de la maquette.

    ─── POURQUOI PAS LE SÉLECTEUR D'ORIGINE ───────────────────────────────────
    Il affichait un drapeau par pays, chargé depuis flagcdn.com : plus de deux
    cents requêtes vers un tiers, et l'adresse IP du visiteur qui part avec.
    Pour un champ facultatif, c'est cher payé.

    ─── ET POURQUOI UNE LISTE NATIVE ──────────────────────────────────────────
    Elle se navigue au clavier, se cherche en tapant les premières lettres,
    s'ouvre en roue sur téléphone, et ne coûte pas une ligne de script. Le
    composant sur mesure faisait moins bien les trois."""
    options = []
    for iso, nom, indicatif in dial:
        selection = ' selected' if iso == defaut else ''
        options.append(
            f'<option value="{htmlmod.escape(indicatif, quote=True)}"{selection}>'
            f'{htmlmod.escape(nom)} {htmlmod.escape(indicatif)}</option>'
        )
    return (
        f'<select name="indicatif" aria-label="{htmlmod.escape(libelle, quote=True)}" '
        'style="border:1px solid #C3CBD4;background:#ffffff;font-family:inherit;font-size:14px;'
        'color:#1B2129;padding:0 9px;border-radius:2px;height:38px;box-sizing:border-box;'
        'flex:0 0 150px;min-width:0;cursor:pointer">' + ''.join(options) + '</select>'
    )


def convertir_demo(chemin: pathlib.Path, code: str) -> tuple[str, str]:
    """Rend deux pages : la demande de démonstration, et le remerciement."""
    # Déclaré ici, avant toute lecture : Python refuse un `global` placé après
    # le premier usage du nom dans la fonction.
    global CONDITIONS

    script = chemin.read_text(encoding='utf-8')
    tables_l = lire_table(script, 'L')
    dial = lire_table(script, 'DIAL')

    mots = tables_l.get(code.upper()) or tables_l.get('EN') or tables_l['FR']
    langue = LANGUES[code]

    corps = extraire_canevas(chemin)

    # Le sélecteur d'indicatif : on retire le composant sur mesure en entier,
    # puis on pose la liste native à sa place.
    m = re.search(r'<button type="button" onClick="\{\{ basculerIndicatif \}\}"', corps)
    if m:
        _, _, fin = bloc_equilibre(corps, m.start(), 'button')
        corps = corps[:m.start()] + selecteur_pays(dial, PAYS_PAR_DEFAUT.get(code, 'FR'),
                                                   mots.get('lTel', 'Country code')) + corps[fin:]
    corps = re.sub(r'<input name="indicatif" type="hidden"[^>]*/?>', '', corps)

    # Les conditions propres à cette page.
    conditions_demo = dict(CONDITIONS)
    conditions_demo.update({'indicatifOuvert': 'retirer', 'formulaire': 'garder', 'envoye': 'replier'})
    anciennes, CONDITIONS = CONDITIONS, conditions_demo
    try:
        corps = resoudre_conditions(corps)
    finally:
        CONDITIONS = anciennes

    # Le panneau de remerciement part masqué et s'affiche après envoi.
    corps = corps.replace('class="dc-langues-panneau" id="panneau-langues" hidden',
                          'class="dc-merci" id="panneau-merci" hidden', 1)
    corps = corps.replace('class="dc-langues-panneau"', 'class="dc-merci"')

    # Les textes de la langue, puis les marqueurs de mise en page communs.
    for cle, valeur in mots.items():
        corps = corps.replace('{{ ' + cle + ' }}', htmlmod.escape(str(valeur)))
    corps = corps.replace('{{ mentionObligatoire }}', htmlmod.escape(str(mots.get('mention', ''))))
    corps = corps.replace('href="{{ accueilUrl }}"', 'href="./"')
    corps = corps.replace('{{ accueilUrl }}', './')
    corps = re.sub(r'\sonSubmit="\{\{ envoyer \}\}"', '', corps)
    corps = re.sub(r'\sonClick="\{\{[^}]*\}\}"', '', corps)

    for cle, valeur in VALEURS.items():
        corps = corps.replace('{{ ' + cle + ' }}', valeur)
    corps = re.sub(r'\shint-placeholder-val="[^"]*"', '', corps)
    corps = re.sub(r'\shint-placeholder-count="[^"]*"', '', corps)

    restants = sorted(set(re.findall(r'\{\{\s*([\w.]+)\s*\}\}', corps)))
    if restants:
        raise SystemExit(f'{chemin.name} [{code}] : marqueur(s) non résolu(s) : {", ".join(restants)}')

    corps, survols = convertir_survols(corps)
    for motif, valeur in COULEURS:
        corps = re.sub(motif, valeur, corps) if motif.startswith('rgba') else corps.replace(motif, valeur)
        survols = re.sub(motif, valeur, survols) if motif.startswith('rgba') else survols.replace(motif, valeur)
    for ancienne, nouvelle in POLICES:
        corps = corps.replace(ancienne, nouvelle)

    corps = completer_formulaire(corps, mots)
    corps = poser_lien_accueil(corps, mots)
    corps = aligner_adresse_affichee(corps)
    corps = nettoyer_typographie(corps)
    corps = rectifier_ressources(corps)
    corps = respecter_taille_minimale_logo(corps)
    corps = rectifier_formulaire(corps, code)
    corps = poser_animations(corps)
    corps = liberer_barre_collante(corps)
    corps = poser_reseaux(corps)
    verifier_liens(corps, chemin.name, code)

    # ── DEUX PAGES SONT TIRÉES DU MÊME CORPS ────────────────────────────────
    #
    # La page de demande porte le formulaire ; la page de remerciement porte le
    # message de confirmation. Toutes deux sont produites en RETIRANT un bloc du
    # même corps converti, plutôt qu'en composant une seconde page à la main.
    #
    # C'est ce qui garantit qu'elles partagent exactement le même habillage :
    # barre, logo, lien de retour, pied de page, styles de survol. Une page de
    # remerciement écrite séparément aurait divergé à la première retouche.
    bloc_merci = ''
    m = re.search(r'<div class="dc-merci" id="panneau-merci" hidden', corps)
    if m:
        _, _, fin = bloc_equilibre(corps, m.start(), 'div')
        bloc_merci = corps[m.start():fin].replace(' hidden', '', 1)
        corps_demande = corps[:m.start()] + corps[fin:]
    else:
        corps_demande = corps

    # ── LA PAGE DE REMERCIEMENT PARLE DE REMERCIEMENT, PAS DE DEMANDE ───────
    #
    # Retirer le formulaire ne suffisait pas : la page gardait le titre « Demander
    # une démo » et son texte d'introduction, suivis du pavé « Demande envoyée ».
    # Elle demandait et confirmait à la fois.
    #
    # Le titre et l'introduction prennent donc les textes de remerciement, et le
    # pavé disparaît : son contenu vient de remonter à sa place.
    corps_merci = corps_demande
    f = re.search(r'<form\b', corps_merci)
    if f:
        _, _, fin_f = bloc_equilibre(corps_merci, f.start(), 'form')
        corps_merci = corps_merci[:f.start()] + retour_accueil(mots) + corps_merci[fin_f:]

    corps_merci = re.sub(
        r'(<h1\b[^>]*>).*?(</h1>)',
        lambda m: m.group(1) + htmlmod.escape(str(mots.get('merciTitre', ''))) + m.group(2),
        corps_merci, count=1, flags=re.S)
    corps_merci = re.sub(
        r'(</h1>\s*<p\b[^>]*>).*?(</p>)',
        lambda m: m.group(1) + htmlmod.escape(str(mots.get('merciTexte', ''))) + m.group(2),
        corps_merci, count=1, flags=re.S)

    def page(fichier: str, titre_page: str, description_page: str, corps_page: str) -> str:
        alternats = '\n'.join(
            f'<link rel="alternate" hreflang="{c}" href="https://www.blastclear.com/{c}/{fichier}"/>'
            for c in LANGUES
        ) + f'\n<link rel="alternate" hreflang="x-default" href="https://www.blastclear.com/en/{fichier}"/>'

        # Ni le formulaire ni le remerciement n'ont leur place dans un index de
        # moteur de recherche : ils n'apportent aucun contenu et diluent les pages
        # qui comptent. Une page de remerciement indexée se retrouve même parfois
        # en résultat de recherche, où elle n'a aucun sens.
        entete_sup = '<meta name="robots" content="noindex,follow">'

        return GABARIT.format(
            source=chemin.name, lang=code, locale=langue['locale'],
            titre=htmlmod.escape(titre_page, quote=True),
            description=htmlmod.escape(description_page, quote=True),
            fichier=fichier, alternats=alternats + '\n' + entete_sup,
            DONNEES_STRUCTUREES='',
            survols=survols, saut=htmlmod.escape(SAUT.get(code, 'Skip to content')),
            corps=corps_page,
        )

    return (
        page('demo.html',
             f"BlastClear | {mots.get('titre', 'Demo')}",
             str(mots.get('intro', ''))[:180],
             corps_demande),
        page('merci.html',
             f"BlastClear | {mots.get('merciTitre', 'Thank you')}",
             str(mots.get('merciTexte', ''))[:180],
             corps_merci),
    )


def main() -> int:
    if not SOURCE.is_dir():
        raise SystemExit(f'Dossier des canevas introuvable : {SOURCE}')

    (SITE / 'css').mkdir(parents=True, exist_ok=True)
    (SITE / 'js').mkdir(parents=True, exist_ok=True)
    (SITE / 'css' / 'design.css').write_text(CSS_COMMUN, encoding='utf-8', newline='\n')
    (SITE / 'js' / 'design.js').write_text(JS_COMMUN, encoding='utf-8', newline='\n')
    print('  écrit  site/css/design.css')
    print('  écrit  site/js/design.js')

    total = 0
    for code, langue in LANGUES.items():
        canevas = SOURCE / f"Canvas BlastClear.com{langue['suffixe']}.dc.html"
        if not canevas.exists():
            print(f'  ABSENT {canevas.name}')
            continue
        page = convertir(canevas, code, 'index.html')
        cible = SITE / code / 'index.html'
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(page, encoding='utf-8', newline='\n')
        total += 1
        print(f'  écrit  site/{code}/index.html   ({len(page) // 1024} Ko)')

        # ── LA PAGE « POURQUOI », BÂTIE SUR L'HABILLAGE DE CELLE-CI ─────────
        # On repart de la page qu'on vient d'écrire plutôt que de recomposer une
        # barre et un pied : les deux resteront identiques quoi qu'il advienne de
        # la maquette.
        m_corps = re.search(r'<div id="contenu">\n(.*)\n</div>\n<script', page, re.S)
        t = POURQUOI.get(code)
        if m_corps and t:
            corps_pq = construire_pourquoi(m_corps.group(1), code)
            if corps_pq:
                survols = re.search(r'<style>\n(.*?)\n</style>', page, re.S)
                alternats = '\n'.join(
                    f'<link rel="alternate" hreflang="{c}" href="https://www.blastclear.com/{c}/pourquoi.html"/>'
                    for c in LANGUES
                ) + '\n<link rel="alternate" hreflang="x-default" href="https://www.blastclear.com/en/pourquoi.html"/>'
                page_pq = GABARIT.format(
                    source=canevas.name + ' + outils/pourquoi.py',
                    lang=code, locale=langue['locale'],
                    titre=htmlmod.escape(f"{t['titre']} | BlastClear", quote=True),
                    description=htmlmod.escape(t['chapo'][:180], quote=True),
                    fichier='pourquoi.html', alternats=alternats,
                    DONNEES_STRUCTUREES='',
                    survols=survols.group(1) if survols else '',
                    saut=htmlmod.escape(SAUT.get(code, 'Skip to content')),
                    corps=corps_pq,
                )
                (SITE / code / 'pourquoi.html').write_text(page_pq, encoding='utf-8', newline='\n')
                total += 1

    # La page de demande existe en un seul canevas qui porte les treize langues ;
    # on en tire treize pages, une par dossier, pour qu'elles soient indexables
    # et que chaque lien ouvre bien la bonne langue.
    demo = SOURCE / 'Demande de démo.dc.html'
    if demo.exists():
        for code in LANGUES:
            page_demande, page_merci = convertir_demo(demo, code)
            dossier = SITE / code
            dossier.mkdir(parents=True, exist_ok=True)
            (dossier / 'demo.html').write_text(page_demande, encoding='utf-8', newline='\n')
            (dossier / 'merci.html').write_text(page_merci, encoding='utf-8', newline='\n')
            total += 2
        print(f'  écrit  site/<langue>/demo.html et merci.html  ({len(LANGUES) * 2} pages)')
    else:
        print('  ABSENT Demande de démo.dc.html')

    # Les photographies se copient telles quelles ; le faisceau balistique, lui,
    # passe par preparer_fond_balistique, qui le recolore et l'allège.
    for nom in ('app-screen.jpg', 'pit-dome.jpg'):
        src = SOURCE / 'assets' / nom
        if src.exists():
            dest = SITE / 'assets' / 'design' / nom
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    preparer_fond_balistique()
    preparer_logos()

    print(f'{total} page(s) produite(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

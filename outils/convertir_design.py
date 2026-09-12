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
    """Pose les textes indicatifs que la maquette avait prévus sans les poser.

    La table de traduction définit pNom, pSociete, pPoste et pEmail pour les
    treize langues, mais aucun de ces textes n'est branché sur son champ : les
    quatre premiers champs du formulaire sont vides et rien n'indique ce qu'on
    y attend. Seul le message en avait un."""
    correspondances = {
        'nom': 'pNom', 'societe': 'pSociete', 'poste': 'pPoste',
        'email': 'pEmail', 'telephone': 'pTel',
    }
    for champ, cle in correspondances.items():
        texte = mots.get(cle)
        if not texte:
            continue
        corps = re.sub(
            rf'(<input name="{champ}"(?![^>]*placeholder))',
            rf'\1 placeholder="{htmlmod.escape(str(texte), quote=True)}"',
            corps, count=1)
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
    """Assombrit le voile posé sur la photographie du bandeau.

    La maquette montait de 0,30 à 0,40 d'opacité sur le premier quart de la
    hauteur. Le titre en réserve blanche tombe précisément là, et la photo y est
    claire : le contraste devenait incertain. La charte demande un voile d'au
    moins 60 % sous un élément posé sur une photographie."""
    return (corps
            .replace('rgba(20,23,28,0.30) 0%', 'rgba(20,23,28,0.52) 0%')
            .replace('rgba(20,23,28,0.40) 25%', 'rgba(20,23,28,0.66) 25%'))


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

    # Le canevas de demande porte les treize langues dans un seul fichier ; on
    # en tire une page par dossier, donc chaque langue reste chez elle.
    for variante in ('Demande de démo.dc.html', 'Demande%20de%20d%C3%A9mo.dc.html',
                     'Demande de d%C3%A9mo.dc.html'):
        corps = corps.replace(f'href="{variante}"', 'href="demo.html"')
    return corps


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


def rectifier_formulaire(corps: str) -> str:
    """Un hébergement statique ne traite aucun envoi de formulaire.

    Plutôt que d'expédier les coordonnées d'un prospect vers un service tiers
    choisi à sa place, le formulaire compose un courriel dans le logiciel de
    messagerie du visiteur. Aucune donnée ne transite par un intermédiaire, et
    il n'y a rien à configurer. Le jour où un service de collecte est retenu, il
    suffit de renseigner action= et method= sur la balise <form>."""
    return corps.replace('<form', '<form data-courriel="contact@blastclear.com"', 1)


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
nav[style*="sticky"].dc-defile img{height:26px !important}

/* Le trait jaune qui se remplit sous la barre à mesure qu'on descend. */
.dc-progression{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:var(--bc-jaune);transition:width .1s linear}

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

.dc-traits{opacity:1}

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
    var parentTraits = traits.parentElement;

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
          traits.style.transform = 'translate(-50%,' + (-46 + (p - 0.5) * 12).toFixed(2) +
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

      // Le panneau de remerciement s'affiche, mais un instant plus tard : le
      // temps que le logiciel de messagerie s'ouvre. Remplacer le formulaire
      // immédiatement donnerait l'impression que l'envoi est parti alors qu'il
      // reste à confirmer dans le client de messagerie.
      var merci = document.getElementById('panneau-merci');
      if (!merci) return;
      setTimeout(function () {
        merci.hidden = false;
        formulaire.hidden = true;
        merci.setAttribute('tabindex', '-1');
        merci.focus();
      }, 900);
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
<link rel="canonical" href="https://blastclear.com/{lang}/{fichier}">
{alternats}
<meta property="og:type" content="website">
<meta property="og:locale" content="{locale}">
<meta property="og:site_name" content="BlastClear">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://blastclear.com/{lang}/{fichier}">
<meta property="og:image" content="https://blastclear.com/assets/design/app-screen.jpg">
<meta name="twitter:card" content="summary_large_image">
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
    corps = nettoyer_typographie(corps)
    corps = renforcer_bandeau(corps)
    corps = rectifier_resultats(corps, langue)
    corps = rectifier_liens(corps, code)
    corps = rectifier_ressources(corps)
    corps = inliner_fond_balistique(corps)
    if fichier == 'index.html':
        corps = remplacer_section_application(corps, code)
    corps = rectifier_formulaire(corps)
    corps = poser_animations(corps)

    titre, description = extraire_metadonnees(corps)

    alternats = '\n'.join(
        f'<link rel="alternate" hreflang="{c}" href="https://blastclear.com/{c}/">'
        for c in LANGUES
    ) + '\n<link rel="alternate" hreflang="x-default" href="https://blastclear.com/fr/">'

    return GABARIT.format(
        source=chemin.name, lang=code, locale=langue['locale'],
        titre=htmlmod.escape(titre, quote=True),
        description=htmlmod.escape(description, quote=True),
        fichier='' if fichier == 'index.html' else fichier,
        alternats=alternats, survols=survols,
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


def convertir_demo(chemin: pathlib.Path, code: str) -> str:
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
    corps = nettoyer_typographie(corps)
    corps = rectifier_ressources(corps)
    corps = rectifier_formulaire(corps)
    corps = poser_animations(corps)

    titre = f"BlastClear | {mots.get('titre', 'Demo')}"
    description = str(mots.get('intro', ''))[:180]

    alternats = '\n'.join(
        f'<link rel="alternate" hreflang="{c}" href="https://blastclear.com/{c}/demo.html"/>'
        for c in LANGUES
    ) + '\n<link rel="alternate" hreflang="x-default" href="https://blastclear.com/fr/demo.html"/>'

    # Une page de formulaire n'a rien à faire dans un index de moteur de
    # recherche : elle n'apporte aucun contenu et dilue les pages qui comptent.
    entete_sup = '<meta name="robots" content="noindex,follow">'

    return GABARIT.format(
        source=chemin.name, lang=code, locale=langue['locale'],
        titre=htmlmod.escape(titre, quote=True),
        description=htmlmod.escape(description, quote=True),
        fichier='demo.html', alternats=alternats + '\n' + entete_sup,
        survols=survols, saut=htmlmod.escape(SAUT.get(code, 'Skip to content')),
        corps=corps,
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

    # La page de demande existe en un seul canevas qui porte les treize langues ;
    # on en tire treize pages, une par dossier, pour qu'elles soient indexables
    # et que chaque lien ouvre bien la bonne langue.
    demo = SOURCE / 'Demande de démo.dc.html'
    if demo.exists():
        for code in LANGUES:
            page = convertir_demo(demo, code)
            cible = SITE / code / 'demo.html'
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(page, encoding='utf-8', newline='\n')
            total += 1
        print(f'  écrit  site/<langue>/demo.html  ({len(LANGUES)} pages)')
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

    print(f'{total} page(s) produite(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

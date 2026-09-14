#!/usr/bin/env python3
"""
LA FOSSE, SON DÔME, LE TIR ET SES PÉRIMÈTRES, DU DXF VERS LE NAVIGATEUR.

─── POURQUOI UNE CONVERSION, ET NON LES DXF TELS QUELS ─────────────────────────
Le relevé de fosse pèse 10,5 Mo de texte : chaque coordonnée y est écrite en
toutes lettres, et chaque sommet répété autant de fois qu'il appartient à des
faces. Le lire dans un navigateur demanderait d'y télécharger 10 Mo, puis d'écrire
un analyseur DXF en JavaScript pour retrouver ce qu'on sait déjà ici.

─── TROIS RÉDUCTIONS, ET CE QU'ELLES COÛTENT ───────────────────────────────────
1. DÉDUPLICATION. Le DXF réécrit chaque sommet pour chaque face qui le touche.
   Les réunir au millimètre divise leur nombre par plus de deux, sans rien perdre.

2. REGROUPEMENT PAR CELLULES. L'espace est quadrillé, et tous les sommets d'une
   même cellule fusionnent en leur barycentre. C'est la seule des trois qui perde
   du détail, et c'est délibéré : à la taille où ce décor s'affiche, les banquettes
   se distinguent encore mais leurs irrégularités centimétriques ne se voient pas.
   Elle ne s'applique QU'AUX SURFACES : une polyligne de quelques dizaines de
   points n'a rien à y gagner et son tracé en souffrirait.

3. QUANTIFICATION SUR 16 BITS. Les coordonnées sont ramenées dans l'emprise
   commune puis écrites en entiers courts, deux octets au lieu de quatre. Sur une
   emprise de 1 545 m, le pas vaut 2,4 cm. Un relevé de fosse n'est pas levé plus
   finement.

─── L'EMPRISE EST COMMUNE À TOUT ───────────────────────────────────────────────
Une emprise par fichier décalerait les objets les uns par rapport aux autres, et le
dôme ne serait plus au-dessus de son tir. Tout est donc mesuré d'abord, quantifié
ensuite.

Usage :
    python outils/convertir_fosse.py
"""

from __future__ import annotations

import json
import math
import pathlib
import struct
import sys
from collections import defaultdict

RACINE = pathlib.Path(__file__).resolve().parent.parent
SORTIE = RACINE / 'site' / 'assets' / 'fosse'
SOURCES = pathlib.Path(r'D:\Claude Code\Projet Blast Perimeter')

# ══ CE QUI EST LU, ET CE QUE ÇA DEVIENT ═══════════════════════════════════════
#
# Chaque entrée : le fichier, le calque DXF (None = tout le fichier), le nom de la
# couche à l'écran, sa forme de tracé, et la finesse du regroupement.
#
# La fosse est la plus fine des surfaces : ses banquettes sont ce qui la rend
# reconnaissable, et une grille trop lâche les efface en un cône lisse. Le dôme
# est une calotte régulière, que peu de facettes suffisent à décrire.
#
# La fosse sort en surface ET en fil de fer. Une surface de relevé minier est
# presque plate à l'échelle de son emprise, 334 m de dénivelé pour 1 545 m de côté,
# et son ombrage seul ne dit rien de ses gradins : ce sont les arêtes qui les
# révèlent. La surface reste néanmoins émise, sans quoi le fil de fer du dôme se
# verrait au travers du terrain.

SURFACES = [
    ('DE_EMZ_PH07F_V16dxf(Wireframes)2.dxf', 'DE_EMZ_PH07F_V16_Surf',
     'fosse', ('triangles', 'aretes'), 104),
    ('DE_EMZ_PH07F_V16dxf(Wireframes)2.dxf', '5-70-014_Contour_R_500_m',
     'dome', ('aretes',), 54),
]

# ─── LES TRACÉS SONT CHERCHÉS EN PLUSIEURS ENDROITS ───────────────────────────
# Un même export existe souvent en deux exemplaires, l'un périmé. On retient le
# PLUS RÉCENT qui porte effectivement de la géométrie sur le calque demandé : un
# fichier vide, resté d'un export manqué, ne doit pas l'emporter sur le bon parce
# qu'il se trouve plus haut dans une liste.
#
# Le calque est filtré. Le fichier du périmètre porte aussi une polyligne de trois
# points sur le calque « 0 », laissée par l'export : la prendre ajouterait au
# dessin un segment que rien n'explique.
TRACES = [
    # noms à l'écran, chemins candidats, calque à retenir, fermer la boucle ?
    ('contour',
     [r'D:\Claude Code\Projet Blast Perimeter\5-70-014_Contour.dxf'],
     {'Geometry_Line'}, True),
    ('perimetre',
     [r'D:\Claude Code\Blast Perimeter WPF\Travail\EMZ\Test_Boena\Intersection_300.dxf',
      r'D:\Claude Code\Projet Blast Perimeter\Intersection_300.dxf'],
     {'5-70-014_Contour_R_500_m'}, True),
]

# ─── LE CERCLE DE COMPARAISON ─────────────────────────────────────────────────
# Son rayon est celui du dôme, pour que la comparaison porte sur la FORME et non
# sur la portée : les deux partent de la même distance maximale, et ce qu'on lit
# est ce que le terrain y change.
#
# Il est TIRETÉ, comme une règle empirique doit l'être à côté d'un calcul. Le
# tireté n'est pas un style de trait envoyé à la carte graphique, qui n'en connaît
# aucun : ce sont les segments eux-mêmes qui sont émis en alternance. Deux cent
# quarante segments donnent une corde de 13 m, et le motif trois pleins pour deux
# vides un tiret de 39 m suivi d'un blanc de 26 m, lisible sur tout le pourtour.
RAYON_CERCLE = 500.0
SEGMENTS_CERCLE = 240
TIRET_PLEIN, TIRET_VIDE = 3, 2

# Un 3DFACE porte ses quatre sommets dans ces codes. Le quatrième répète souvent le
# troisième : la face est alors un triangle, et le quadrilatère dégénéré.
CODES = {10: (0, 0), 20: (0, 1), 30: (0, 2),
         11: (1, 0), 21: (1, 1), 31: (1, 2),
         12: (2, 0), 22: (2, 1), 32: (2, 2),
         13: (3, 0), 23: (3, 1), 33: (3, 2)}


# ══ LECTURE ═══════════════════════════════════════════════════════════════════

def lignes_dxf(chemin: pathlib.Path) -> list[str]:
    return chemin.read_text(encoding='utf-8', errors='replace').split('\n')


def lire_faces(chemin: pathlib.Path, calques: set[str]) -> dict[str, list]:
    """Rend, par calque, la liste des faces sous forme de quadruplets de sommets."""
    L = lignes_dxf(chemin)
    faces = defaultdict(list)
    i, n = 0, len(L)

    while i < n - 1:
        if L[i].strip() == '0' and L[i + 1].strip() == '3DFACE':
            i += 2
            calque = ''
            coins = [[None] * 3 for _ in range(4)]
            while i < n - 1 and L[i].strip() != '0':
                try:
                    code = int(L[i].strip())
                except ValueError:
                    i += 2
                    continue
                valeur = L[i + 1].strip()
                if code == 8:
                    calque = valeur
                elif code in CODES:
                    s, c = CODES[code]
                    try:
                        coins[s][c] = float(valeur)
                    except ValueError:
                        pass
                i += 2
            if calque in calques and all(None not in c for c in coins):
                faces[calque].append([tuple(c) for c in coins])
        else:
            i += 1
    return faces


def lire_polylignes(chemin: pathlib.Path,
                    calques: set[str] | None = None) -> list[list[tuple]]:
    """Rend les polylignes du fichier, sous les deux écritures que le DXF connaît.

    ─── DEUX ÉCRITURES POUR LA MÊME CHOSE ────────────────────────────────────
    POLYLINE écrit ses points comme des entités VERTEX séparées, jusqu'à SEQEND.
    LWPOLYLINE les écrit dans l'entité elle-même, avec une altitude unique en
    groupe 38. Les exports miniers emploient l'une ou l'autre selon le logiciel ;
    n'en lire qu'une donnerait un fichier « vide » sans que rien ne le dise.

    ─── LE CALQUE EST FILTRÉ, ET CE N'EST PAS DU ZÈLE ────────────────────────
    Un export minier emporte souvent des tracés de service sur le calque « 0 » :
    repères de construction, restes d'une sélection. Le fichier du périmètre en
    porte un de trois points. Tout lire ajouterait au dessin un segment que rien
    n'explique, et que personne ne penserait à chercher dans le DXF.

    `calques` à None prend tout, ce qui reste juste pour un fichier qui n'en a
    qu'un.
    """
    L = lignes_dxf(chemin)
    traces: list[list[tuple]] = []
    i, n = 0, len(L)
    courante = None
    calque = ''

    def retenir(points, cal):
        if len(points) >= 2 and (calques is None or cal in calques):
            traces.append(points)

    while i < n - 1:
        if L[i].strip() != '0':
            i += 1
            continue
        type_ = L[i + 1].strip()

        if type_ == 'POLYLINE':
            courante, calque = [], ''
            i += 2
            # L'en-tête de la polyligne porte son calque, avant ses sommets.
            while i < n - 1 and L[i].strip() != '0':
                if L[i].strip() == '8':
                    calque = L[i + 1].strip()
                i += 2
            continue

        if type_ == 'VERTEX' and courante is not None:
            i += 2
            p = [None] * 3
            while i < n - 1 and L[i].strip() != '0':
                try:
                    code = int(L[i].strip())
                except ValueError:
                    i += 2
                    continue
                if code in (10, 20, 30):
                    try:
                        p[(code - 10) // 10] = float(L[i + 1].strip())
                    except ValueError:
                        pass
                i += 2
            # Un sommet sans altitude est un sommet plan : le DXF omet alors le
            # groupe 30, et le prendre pour absent perdrait la polyligne entière.
            if p[0] is not None and p[1] is not None:
                courante.append((p[0], p[1], p[2] if p[2] is not None else 0.0))
            continue

        if type_ == 'SEQEND':
            if courante:
                retenir(courante, calque)
            courante = None
            i += 2
            continue

        if type_ == 'LWPOLYLINE':
            i += 2
            xs, ys, altitude, cal = [], [], 0.0, ''
            while i < n - 1 and L[i].strip() != '0':
                try:
                    code = int(L[i].strip())
                except ValueError:
                    i += 2
                    continue
                val = L[i + 1].strip()
                if code == 8:
                    cal = val
                else:
                    try:
                        if code == 10:
                            xs.append(float(val))
                        elif code == 20:
                            ys.append(float(val))
                        elif code == 38:
                            altitude = float(val)
                    except ValueError:
                        pass
                i += 2
            if len(xs) == len(ys):
                retenir([(x, y, altitude) for x, y in zip(xs, ys)], cal)
            continue

        i += 2

    return traces


# ══ TRAITEMENT DES SURFACES ═══════════════════════════════════════════════════

def indexer(faces: list) -> tuple[list[tuple], list[int]]:
    """Déduplique les sommets au millimètre et triangule les quadrilatères."""
    rangs: dict[tuple, int] = {}
    sommets: list[tuple] = []
    triangles: list[int] = []

    def rang(p):
        cle = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
        r = rangs.get(cle)
        if r is None:
            r = len(sommets)
            rangs[cle] = r
            sommets.append(cle)
        return r

    for a, b, c, d in faces:
        ia, ib, ic, idd = rang(a), rang(b), rang(c), rang(d)
        if ia == ib or ib == ic or ic == ia:
            continue                       # face dégénérée, rien à dessiner
        triangles.extend((ia, ib, ic))
        if idd not in (ia, ib, ic):        # quadrilatère : un second triangle
            triangles.extend((ia, ic, idd))

    return sommets, triangles


def boucles_de_bord(triangles: list[int]) -> list[list[int]]:
    """Les boucles de bord libre du maillage.

    Une arête intérieure appartient à deux triangles ; une arête de bord, à un
    seul. Les chaîner bout à bout donne les contours des trous et le pourtour."""
    compte = defaultdict(int)
    for i in range(0, len(triangles), 3):
        t = triangles[i:i + 3]
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            compte[(a, b) if a < b else (b, a)] += 1

    voisins = defaultdict(list)
    for (a, b), n in compte.items():
        if n == 1:
            voisins[a].append(b)
            voisins[b].append(a)

    vus, boucles = set(), []
    for depart in list(voisins):
        if depart in vus:
            continue
        boucle, courant, precedent = [depart], depart, None
        vus.add(depart)
        while True:
            suite = [v for v in voisins[courant] if v != precedent and v not in vus]
            if not suite:
                break
            precedent, courant = courant, suite[0]
            vus.add(courant)
            boucle.append(courant)
        if len(boucle) >= 3:
            boucles.append(boucle)
    return boucles


def fermer_le_fond(sommets: list[tuple], triangles: list[int]) -> int:
    """Bouche les trous du FOND de la fosse, et eux seuls.

    ─── POURQUOI LE FOND ÉTAIT OUVERT ────────────────────────────────────────
    Le relevé est une surface, non un volume : il décrit le terrain vu du dessus
    et s'arrête là où le levé s'arrête. Le carreau du fond, souvent couvert d'eau
    ou d'engins le jour du levé, y laisse un trou. À l'écran, on voyait au travers
    de la fosse jusqu'à sa paroi opposée, ce qui n'a aucun sens pour un terrain.

    ─── ET POURQUOI PAS LE POURTOUR ──────────────────────────────────────────
    Le relevé a DEUX bords libres : ce trou du fond, et le pourtour de la zone
    levée, tout en haut, qui n'est pas un trou mais la limite du document. Le
    boucher tendrait une membrane par-dessus le paysage entier.

    Ils se distinguent par leur altitude, sans ambiguïté sur ce relevé : le trou
    du fond culmine à -70 m quand le pourtour descend au plus bas à 0 m. Le seuil
    est pris au sixième de la hauteur totale, loin de l'un comme de l'autre.

    ─── LE REMPLISSAGE EST UN ÉVENTAIL DEPUIS LE BARYCENTRE ──────────────────
    Le carreau d'une fosse est plat à quelques mètres près : 4,4 m de dénivelé sur
    ce trou-ci. Un éventail depuis le barycentre y suffit et ne peut pas échouer,
    là où une triangulation par oreilles demanderait de traiter les cas dégénérés
    d'un contour relevé au terrain.
    """
    if not sommets:
        return 0
    zs = [p[2] for p in sommets]
    seuil = min(zs) + (max(zs) - min(zs)) / 6
    ajoutes = 0

    for boucle in boucles_de_bord(triangles):
        if max(sommets[i][2] for i in boucle) > seuil:
            continue                       # le pourtour du levé, pas un trou

        cx = sum(sommets[i][0] for i in boucle) / len(boucle)
        cy = sum(sommets[i][1] for i in boucle) / len(boucle)
        cz = sum(sommets[i][2] for i in boucle) / len(boucle)
        centre = len(sommets)
        sommets.append((cx, cy, cz))

        # L'aire signée du contour dit son sens de parcours. L'imposer rend la
        # normale du bouchon dirigée vers le haut, comme le reste du terrain :
        # sans quoi le carreau s'afficherait dans l'ombre, au milieu d'une fosse
        # éclairée.
        aire = 0.0
        for k in range(len(boucle)):
            a, b = sommets[boucle[k]], sommets[boucle[(k + 1) % len(boucle)]]
            aire += a[0] * b[1] - b[0] * a[1]
        ordre = boucle if aire > 0 else boucle[::-1]

        for k in range(len(ordre)):
            triangles.extend((centre, ordre[k], ordre[(k + 1) % len(ordre)]))
            ajoutes += 1

    return ajoutes


def regrouper(sommets: list[tuple], triangles: list[int],
              emprise: tuple, cellules: int) -> tuple[list[tuple], list[int]]:
    """Fusionne les sommets d'une même cellule d'un quadrillage régulier.

    ─── LE REPRÉSENTANT EST LE BARYCENTRE, NON LE CENTRE DE LA CELLULE ───────
    Prendre le centre de la cellule ferait osciller la surface autour de sa vraie
    position, d'un demi-pas de part et d'autre, ce qui se voit sur un talus en
    escalier comme une ondulation qui n'existe pas. Le barycentre des sommets
    fusionnés reste sur la surface d'origine.
    """
    (x0, y0, z0), (x1, y1, z1) = emprise
    pas = max(x1 - x0, y1 - y0, z1 - z0) / cellules

    cumuls: dict[tuple, list] = {}
    nouveau_rang: list[int] = []
    for x, y, z in sommets:
        cle = (math.floor((x - x0) / pas), math.floor((y - y0) / pas),
               math.floor((z - z0) / pas))
        e = cumuls.get(cle)
        if e is None:
            e = [len(cumuls), 0.0, 0.0, 0.0, 0]
            cumuls[cle] = e
        e[1] += x; e[2] += y; e[3] += z; e[4] += 1
        nouveau_rang.append(e[0])

    fusionnes: list = [None] * len(cumuls)
    for e in cumuls.values():
        fusionnes[e[0]] = (e[1] / e[4], e[2] / e[4], e[3] / e[4])

    sortie = []
    for i in range(0, len(triangles), 3):
        a = nouveau_rang[triangles[i]]
        b = nouveau_rang[triangles[i + 1]]
        c = nouveau_rang[triangles[i + 2]]
        if a == b or b == c or c == a:     # triangle aplati par la fusion
            continue
        sortie.extend((a, b, c))

    return fusionnes, sortie


def aretes_uniques(triangles: list[int]) -> list[int]:
    """Les arêtes du maillage, sans doublon, pour un tracé en fil de fer."""
    vues, sortie = set(), []
    for i in range(0, len(triangles), 3):
        t = triangles[i:i + 3]
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            cle = (a, b) if a < b else (b, a)
            if cle in vues:
                continue
            vues.add(cle)
            sortie.extend(cle)
    return sortie


# ══ TRAITEMENT DES TRACÉS ═════════════════════════════════════════════════════

def chaine(points: list[tuple], fermer: bool) -> tuple[list[tuple], list[int]]:
    """Un tracé continu, en sommets et en paires d'indices."""
    pts = list(points)
    # Un contour exporté répète souvent son premier point en dernier. Le garder
    # ajouterait un segment de longueur nulle, que rien ne dessine mais que tout
    # transporte.
    if len(pts) > 2 and pts[0] == pts[-1]:
        pts.pop()
    indices = []
    for k in range(len(pts) - 1):
        indices.extend((k, k + 1))
    if fermer and len(pts) > 2:
        indices.extend((len(pts) - 1, 0))
    return pts, indices


def barycentre(points: list[tuple]) -> tuple[float, float, float]:
    """Le barycentre de la SURFACE délimitée, non la moyenne des sommets.

    Les deux diffèrent dès que les points sont inégalement espacés, ce qui est la
    règle sur un contour relevé au terrain : un côté finement découpé y tirerait
    la moyenne des sommets vers lui, alors qu'il ne pèse pas davantage dans la
    forme. Le tir, lui, a bien un centre de gravité, et c'est celui-là."""
    n = len(points)
    aire = cx = cy = 0.0
    for k in range(n):
        x0, y0, _ = points[k]
        x1, y1, _ = points[(k + 1) % n]
        croix = x0 * y1 - x1 * y0
        aire += croix
        cx += (x0 + x1) * croix
        cy += (y0 + y1) * croix
    z = sum(p[2] for p in points) / n
    if abs(aire) < 1e-9:                   # contour dégénéré : la moyenne suffit
        return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n, z)
    return (cx / (3 * aire), cy / (3 * aire), z)


def cercle_tirete(centre: tuple, rayon: float, segments: int,
                  plein: int, vide: int) -> tuple[list[tuple], list[int]]:
    """Le cercle de comparaison, à l'altitude du tir, en trait tireté.

    ─── LE TIRETÉ EST DANS LA GÉOMÉTRIE, NON DANS LE STYLE ───────────────────
    WebGL ne connaît aucun style de trait : une ligne est pleine, et rien dans
    l'interface ne permet de la pointiller. L'obtenir autrement demanderait de
    porter la distance parcourue le long du tracé jusqu'au nuanceur, et d'y
    écarter les fragments, soit un attribut de plus et une passe de calcul pour
    un cercle de deux cent quarante segments.

    Émettre un segment sur cinq coûte moins cher que de les émettre tous : le
    tireté allège le tracé au lieu de l'alourdir.
    """
    points = [(centre[0] + rayon * math.cos(2 * math.pi * k / segments),
               centre[1] + rayon * math.sin(2 * math.pi * k / segments),
               centre[2])
              for k in range(segments)]
    periode = plein + vide
    indices = []
    for k in range(segments):
        if k % periode < plein:
            indices.extend((k, (k + 1) % segments))
    return points, indices


# ══ ASSEMBLAGE ════════════════════════════════════════════════════════════════

def main() -> int:
    couches: dict[str, dict] = {}          # nom -> {sommets, jeux:{forme:indices}}
    absents: list[str] = []

    # ── Les surfaces ──────────────────────────────────────────────────────────
    besoins: dict[str, set[str]] = defaultdict(set)
    for fichier, calque, _, _, _ in SURFACES:
        besoins[fichier].add(calque)

    lues: dict[str, dict] = {}
    for fichier, calques in besoins.items():
        chemin = SOURCES / fichier
        if not chemin.exists():
            absents.append(f'{fichier} (introuvable)')
            continue
        print(f'Lecture de {fichier} ({chemin.stat().st_size / 1024 / 1024:.1f} Mo)…')
        lues[fichier] = lire_faces(chemin, calques)

    for fichier, calque, nom, formes, grille in SURFACES:
        lot = lues.get(fichier, {}).get(calque)
        if not lot:
            absents.append(f'{fichier} → calque {calque}')
            continue
        sommets, triangles = indexer(lot)
        brut = len(sommets)
        bouches = fermer_le_fond(sommets, triangles) if nom == 'fosse' else 0
        couches[nom] = {'sommets': sommets, 'triangles': triangles,
                        'formes': formes, 'grille': grille, 'brut': brut,
                        'bouches': bouches}

    # ── Les tracés ────────────────────────────────────────────────────────────
    points_contour = None
    for nom, candidats, calques, fermer in TRACES:
        # Le plus récent des fichiers présents QUI PORTE de la géométrie. Un
        # export manqué laisse un fichier valide mais vide, qui ne doit pas
        # l'emporter sur le bon.
        existants = sorted((pathlib.Path(c) for c in candidats if pathlib.Path(c).exists()),
                           key=lambda p: p.stat().st_mtime, reverse=True)
        if not existants:
            absents.append(f'{nom} (aucun fichier trouvé)')
            continue

        traces, retenu = [], None
        for chemin in existants:
            traces = lire_polylignes(chemin, calques)
            if traces:
                retenu = chemin
                break
        if not retenu:
            noms = ', '.join(p.name for p in existants)
            absents.append(f"{nom} ({noms} : aucune polyligne sur "
                           f"{'/'.join(sorted(calques))})")
            continue

        # Plusieurs tracés dans un même fichier se concatènent en une seule couche,
        # chacun gardant sa propre chaîne d'indices.
        sommets, indices = [], []
        for t in traces:
            pts, idx = chaine(t, fermer)
            decalage = len(sommets)
            sommets.extend(pts)
            indices.extend(i + decalage for i in idx)
        couches[nom] = {'sommets': sommets, 'indices': indices,
                        'formes': ('aretes',), 'grille': None,
                        'brut': len(sommets), 'traces': len(traces)}
        print(f'  {nom:<9} lu dans {retenu.name} ({len(traces)} tracé(s))')
        if nom == 'contour':
            points_contour = traces[0]

    # ── Le cercle de comparaison ──────────────────────────────────────────────
    #
    # Il n'est dans aucun fichier : c'est la règle empirique qu'il sert à mettre en
    # regard du périmètre calculé. Le produire ici plutôt que de le dessiner dans
    # un logiciel de CAO garantit qu'il est bien centré sur le barycentre du tir et
    # posé à son altitude, et non à peu près.
    if points_contour:
        c = barycentre(points_contour)
        pts, idx = cercle_tirete(c, RAYON_CERCLE, SEGMENTS_CERCLE,
                                 TIRET_PLEIN, TIRET_VIDE)
        couches['cercle'] = {'sommets': pts, 'indices': idx,
                             'formes': ('aretes',), 'grille': None,
                             'brut': len(pts)}
        print(f'  cercle    R={RAYON_CERCLE:.0f} m centré sur '
              f'({c[0]:.1f}, {c[1]:.1f}) à Z={c[2]:.1f}, '
              f'{len(idx) // 2} tirets')
    else:
        absents.append('cercle de comparaison (il dépend du contour)')

    if not couches:
        raise SystemExit('Aucune géométrie lue. Rien à écrire.')

    # ── L'EMPRISE COMMUNE, MESURÉE SUR TOUT ───────────────────────────────────
    bas, haut = [1e30] * 3, [-1e30] * 3
    for c in couches.values():
        for p in c['sommets']:
            for k in range(3):
                bas[k] = min(bas[k], p[k])
                haut[k] = max(haut[k], p[k])
    emprise = (tuple(bas), tuple(haut))

    cx = (bas[0] + haut[0]) / 2
    cy = (bas[1] + haut[1]) / 2
    demi = max(haut[0] - bas[0], haut[1] - bas[1], haut[2] - bas[2]) / 2

    SORTIE.mkdir(parents=True, exist_ok=True)
    for vieux in SORTIE.glob('*.bin'):
        vieux.unlink()

    manifeste = {'demiCoteMetres': round(demi, 1), 'couches': {}}
    extremes = [[1e30] * 3, [-1e30] * 3]
    total = 0

    for nom, c in couches.items():
        if 'triangles' in c:
            sommets, triangles = regrouper(c['sommets'], c['triangles'],
                                           emprise, c['grille'])
            jeux = {}
            if 'triangles' in c['formes']:
                jeux['triangles'] = triangles
            if 'aretes' in c['formes']:
                jeux['aretes'] = aretes_uniques(triangles)
        else:
            sommets = c['sommets']
            jeux = {'aretes': c['indices']}

        if len(sommets) > 65535:
            raise SystemExit(f"{nom} : {len(sommets)} sommets, au-delà de ce qu'un "
                             'indice de 16 bits adresse. Réduire sa grille.')

        # ── QUANTIFICATION, ET PASSAGE EN REPÈRE ÉCRAN ──────────────────────
        # Le repère minier a le Z vertical ; un moteur 3D attend le Y vertical.
        # L'échange se fait ici, une fois, plutôt que dans le nuanceur à chaque
        # image. L'axe des X garde l'est ; le Z de la scène pointe donc le sud.
        brut = []
        for x, y, z in sommets:
            for v, k in (((x - cx) / demi, 0), ((z - (bas[2] + demi)) / demi, 1),
                         ((cy - y) / demi, 2)):
                q = max(0, min(65535, round((v + 1) * 32767.5)))
                brut.append(q)
                reel = q / 32767.5 - 1
                extremes[0][k] = min(extremes[0][k], reel)
                extremes[1][k] = max(extremes[1][k], reel)

        f_pos = SORTIE / f'{nom}.pos.bin'
        f_pos.write_bytes(struct.pack(f'<{len(brut)}H', *brut))
        poids = f_pos.stat().st_size

        entree = {'sommets': len(sommets), 'position': f_pos.name, 'jeux': []}
        detail = []
        for forme, indices in jeux.items():
            f_idx = SORTIE / f'{nom}.{forme}.bin'
            f_idx.write_bytes(struct.pack(f'<{len(indices)}H', *indices))
            poids += f_idx.stat().st_size
            entree['jeux'].append({'forme': forme, 'index': f_idx.name,
                                   'indices': len(indices)})
            detail.append(f'{len(indices) // (3 if forme == "triangles" else 2):,} {forme}')
        total += poids

        manifeste['couches'][nom] = entree
        bouche = f"  (+{c['bouches']} au fond)" if c.get('bouches') else ''
        print(f"  {nom:<9} {c['brut']:>6,} -> {len(sommets):>6,} sommets  "
              f"{', '.join(detail):<28} {poids / 1024:>6,.0f} ko{bouche}")

    # La boîte, en coordonnées de scène : le navigateur s'en sert pour CALCULER le
    # recul de la caméra. Le modèle est un disque très aplati, 334 m de dénivelé
    # pour 1 545 m de côté : un ajustement sur sa sphère englobante le reculerait
    # de moitié pour cadrer de l'air.
    manifeste['boite'] = {'min': [round(v, 4) for v in extremes[0]],
                          'max': [round(v, 4) for v in extremes[1]]}

    (SORTIE / 'fosse.json').write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f'Total : {total / 1024:.0f} ko dans site/assets/fosse/')
    if absents:
        print('\nNON INTÉGRÉ :')
        for a in absents:
            print(f'  - {a}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

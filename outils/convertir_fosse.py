#!/usr/bin/env python3
"""
LA FOSSE ET SON DÔME, DU DXF VERS LE NAVIGATEUR.

─── POURQUOI UNE CONVERSION, ET NON LE DXF TEL QUEL ────────────────────────────
Le DXF pèse 10,5 Mo de texte : chaque coordonnée y est écrite en toutes lettres, et
chaque sommet répété autant de fois qu'il appartient à des faces. Le lire dans un
navigateur demanderait d'y télécharger 10 Mo, puis d'écrire un analyseur DXF en
JavaScript pour retrouver ce qu'on sait déjà ici.

─── TROIS RÉDUCTIONS, ET CE QU'ELLES COÛTENT ───────────────────────────────────
Le maillage indexé brut pèse encore 0,93 Mo, ce qui reste hors de proportion pour
un décor. Trois opérations le ramènent sous les 200 ko, dans cet ordre.

1. DÉDUPLICATION. Le DXF réécrit chaque sommet pour chaque face qui le touche.
   Les réunir au millimètre divise leur nombre par plus de deux, sans rien perdre.

2. REGROUPEMENT PAR CELLULES. L'espace est quadrillé, et tous les sommets d'une
   même cellule fusionnent en leur barycentre. C'est la seule des trois qui perde
   du détail, et c'est délibéré : à la taille où ce décor s'affiche, derrière du
   texte, les banquettes se distinguent encore mais leurs irrégularités
   centimétriques ne se voient pas. La finesse de la grille se règle par calque.

3. QUANTIFICATION SUR 16 BITS. Les coordonnées sont ramenées dans l'emprise
   commune puis écrites en entiers courts, deux octets au lieu de quatre. Sur une
   emprise de 1 545 m, le pas vaut 2,4 cm. Un relevé de fosse n'est pas levé plus
   finement, et ce décor n'est mesuré par personne.

Les indices passent eux aussi sur 16 bits, ce que le nombre de sommets autorise
après regroupement. C'est le format que la carte graphique accepte tel quel.

─── CE QUI EST ÉMIS, ET POURQUOI PAS L'INVERSE ─────────────────────────────────
La fosse sort en TRIANGLES : c'est une surface, elle se lit à l'ombrage. Le dôme
sort en ARÊTES : c'est un volume transparent posé par-dessus, et le remplir
cacherait la fosse qu'il surplombe. C'est aussi ainsi que le logiciel les montre.

N'émettre que ce qui sert évite de transporter des indices que rien ne dessine.

Usage :
    python outils/convertir_fosse.py <fichier.dxf>
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

# Les deux calques retenus, le rôle qu'ils jouent, et la finesse de la grille de
# regroupement. Plus le nombre est grand, plus le maillage garde de détail.
#
# La fosse est la plus fine des deux : ses banquettes sont ce qui la rend
# reconnaissable, et une grille trop lâche les efface en un cône lisse. Le dôme
# est une calotte régulière, que peu de facettes suffisent à décrire.
#
# La troisième valeur dit ce qui est émis. La fosse sort en surface ET en fil de
# fer : une surface de relevé minier est presque plate à l'échelle de son emprise,
# 334 m de dénivelé pour 1 545 m de côté, et son ombrage seul ne dit rien de ses
# banquettes. Ce sont les arêtes qui les révèlent. La surface reste néanmoins
# émise : sans elle, le fil de fer du dôme se verrait au travers du terrain.
CALQUES = {
    'DE_EMZ_PH07F_V16_Surf': ('fosse', 104, ('triangles', 'aretes')),
    '5-70-014_Contour_R_500_m': ('dome', 54, ('aretes',)),
}

# Un 3DFACE porte ses quatre sommets dans ces codes. Le quatrième répète souvent le
# troisième : la face est alors un triangle, et le quadrilatère dégénéré.
CODES = {10: (0, 0), 20: (0, 1), 30: (0, 2),
         11: (1, 0), 21: (1, 1), 31: (1, 2),
         12: (2, 0), 22: (2, 1), 32: (2, 2),
         13: (3, 0), 23: (3, 1), 33: (3, 2)}


def lire_faces(chemin: pathlib.Path) -> dict[str, list]:
    """Rend, par calque, la liste des faces sous forme de quadruplets de sommets."""
    lignes = chemin.read_text(encoding='utf-8', errors='replace').split('\n')
    faces = defaultdict(list)
    i, n = 0, len(lignes)

    while i < n - 1:
        if lignes[i].strip() == '0' and lignes[i + 1].strip() == '3DFACE':
            i += 2
            calque = ''
            coins = [[None] * 3 for _ in range(4)]
            while i < n - 1 and lignes[i].strip() != '0':
                try:
                    code = int(lignes[i].strip())
                except ValueError:
                    i += 2
                    continue
                valeur = lignes[i + 1].strip()
                if code == 8:
                    calque = valeur
                elif code in CODES:
                    s, c = CODES[code]
                    try:
                        coins[s][c] = float(valeur)
                    except ValueError:
                        pass
                i += 2
            if calque in CALQUES and all(None not in c for c in coins):
                faces[CALQUES[calque][0]].append([tuple(c) for c in coins])
        else:
            i += 1
    return faces


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


def regrouper(sommets: list[tuple], triangles: list[int],
              emprise: tuple, cellules: int) -> tuple[list[tuple], list[int]]:
    """Fusionne les sommets d'une même cellule d'un quadrillage régulier.

    ─── LE REPRÉSENTANT EST LE BARYCENTRE, NON LE CENTRE DE LA CELLULE ───────
    Prendre le centre de la cellule ferait osciller la surface autour de sa vraie
    position, d'un demi-pas de part et d'autre, ce qui se voit sur un talus en
    escalier comme une ondulation qui n'existe pas. Le barycentre des sommets
    fusionnés reste sur la surface d'origine.

    ─── LA GRILLE EST COMMUNE AUX DEUX CALQUES ───────────────────────────────
    Elle se fonde sur l'emprise de l'ensemble, non sur celle du calque. Deux
    quadrillages distincts décaleraient le dôme par rapport à la fosse qu'il
    surplombe, d'une fraction de cellule, et le tir ne serait plus sous son dôme.
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

    fusionnes = [None] * len(cumuls)
    for e in cumuls.values():
        fusionnes[e[0]] = (e[1] / e[4], e[2] / e[4], e[3] / e[4])

    sortie = []
    for i in range(0, len(triangles), 3):
        a = nouveau_rang[triangles[i]]
        b = nouveau_rang[triangles[i + 1]]
        c = nouveau_rang[triangles[i + 2]]
        # Deux sommets tombés dans la même cellule aplatissent le triangle : il
        # n'a plus de surface, et la carte graphique ne dessinerait rien.
        if a == b or b == c or c == a:
            continue
        sortie.extend((a, b, c))

    return fusionnes, sortie


def aretes_uniques(triangles: list[int]) -> list[int]:
    """Les arêtes du maillage, sans doublon, pour un tracé en fil de fer.

    Chaque arête intérieure appartient à deux triangles : la lister deux fois
    doublerait le travail de la carte graphique pour un résultat identique."""
    vues = set()
    sortie = []
    for i in range(0, len(triangles), 3):
        t = triangles[i:i + 3]
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            cle = (a, b) if a < b else (b, a)
            if cle in vues:
                continue
            vues.add(cle)
            sortie.extend(cle)
    return sortie


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit('Usage : python outils/convertir_fosse.py <fichier.dxf>')
    source = pathlib.Path(sys.argv[1])
    if not source.exists():
        raise SystemExit(f'Introuvable : {source}')

    print(f'Lecture de {source.name} ({source.stat().st_size / 1024 / 1024:.1f} Mo)…')
    faces = lire_faces(source)
    if not faces:
        raise SystemExit('Aucune face trouvée sur les calques attendus.')

    SORTIE.mkdir(parents=True, exist_ok=True)

    # ── L'EMPRISE EST COMMUNE AUX DEUX CALQUES ────────────────────────────────
    # Les mesurer séparément les décalerait l'un par rapport à l'autre, et le dôme
    # ne serait plus au-dessus de son tir.
    bas = [1e30] * 3
    haut = [-1e30] * 3
    for lot in faces.values():
        for f in lot:
            for p in f:
                for k in range(3):
                    bas[k] = min(bas[k], p[k])
                    haut[k] = max(haut[k], p[k])
    emprise = (tuple(bas), tuple(haut))
    etendue = max(haut[0] - bas[0], haut[1] - bas[1])

    reglages = {nom: (grille, forme) for nom, grille, forme in CALQUES.values()}
    manifeste = {'etendueMetres': round(etendue, 1), 'calques': {}}
    total = 0
    extremes = [[1e30] * 3, [-1e30] * 3]        # la boîte, en coordonnées de scène

    for nom, lot in faces.items():
        grille, formes = reglages[nom]
        sommets, triangles = indexer(lot)
        avant = len(sommets)
        sommets, triangles = regrouper(sommets, triangles, emprise, grille)
        if len(sommets) > 65535:
            raise SystemExit(f'{nom} : {len(sommets)} sommets, au-delà de ce qu\'un '
                             'indice de 16 bits adresse. Réduire sa grille.')

        jeux = {'triangles': triangles} if 'triangles' in formes else {}
        if 'aretes' in formes:
            jeux['aretes'] = aretes_uniques(triangles)

        # ── QUANTIFICATION, DANS UN CUBE CENTRÉ SUR L'EMPRISE COMMUNE ────────
        # Le repère minier a le Z vertical ; un moteur 3D attend le Y vertical.
        # L'échange se fait ici, une fois, plutôt que dans le nuanceur à chaque
        # image.
        cx = (bas[0] + haut[0]) / 2
        cy = (bas[1] + haut[1]) / 2
        demi = max(haut[0] - bas[0], haut[1] - bas[1], haut[2] - bas[2]) / 2
        brut = []
        for x, y, z in sommets:
            # Ramené dans [0,1] sur chaque axe, puis sur toute l'échelle d'un
            # entier court. L'écrêtage ne sert qu'à parer un arrondi en bordure.
            for v, c in (((x - cx) / demi, 0), ((z - (bas[2] + demi)) / demi, 1),
                         ((cy - y) / demi, 2)):
                q = max(0, min(65535, round((v + 1) * 32767.5)))
                brut.append(q)
                # Relevé sur la valeur quantifiée, donc sur ce qui sera dessiné.
                reel = q / 32767.5 - 1
                extremes[0][c] = min(extremes[0][c], reel)
                extremes[1][c] = max(extremes[1][c], reel)

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

        manifeste['calques'][nom] = entree
        print(f'  {nom:<6} {avant:>6,} -> {len(sommets):>6,} sommets  '
              f'{", ".join(detail):<28} {poids / 1024:>6,.0f} ko')

    # Le demi-côté du cube sert au navigateur à revenir en mètres, pour placer la
    # caméra à une distance qui a un sens plutôt qu'à un nombre choisi à l'œil.
    manifeste['demiCoteMetres'] = round(
        max(haut[0] - bas[0], haut[1] - bas[1], haut[2] - bas[2]) / 2, 1)

    # ── LA BOÎTE, DANS LES COORDONNÉES DE LA SCÈNE ────────────────────────────
    #
    # Le navigateur s'en sert pour CALCULER le recul de la caméra plutôt que de
    # le deviner. Le modèle est un disque très aplati, 334 m de dénivelé pour
    # 1 545 m de côté : un ajustement sur sa sphère englobante le reculerait de
    # moitié pour rien, et un nombre écrit à la main cesserait d'être juste au
    # premier changement de fichier source.
    #
    # Elle est relevée sur les valeurs QUANTIFIÉES, donc sur ce qui est
    # réellement dessiné, et non sur ce qui a été lu du DXF.
    manifeste['boite'] = {'min': [round(v, 4) for v in extremes[0]],
                          'max': [round(v, 4) for v in extremes[1]]}

    (SORTIE / 'fosse.json').write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f'Total : {total / 1024:.0f} ko dans site/assets/fosse/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

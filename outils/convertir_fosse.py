#!/usr/bin/env python3
"""
LA FOSSE ET SON DÔME, DU DXF VERS LE NAVIGATEUR.

─── POURQUOI UNE CONVERSION, ET NON LE DXF TEL QUEL ────────────────────────────
Le DXF pèse 10,5 Mo de texte : chaque coordonnée y est écrite en toutes lettres, et
chaque sommet répété autant de fois qu'il appartient à des faces. Le lire dans un
navigateur demanderait d'y télécharger 10 Mo, puis d'écrire un analyseur DXF en
JavaScript pour retrouver ce qu'on sait déjà ici.

La conversion déduplique les sommets, triangule les faces et écrit des tableaux
binaires que le navigateur passe directement à la carte graphique, sans analyse.
Mesuré sur ce fichier : 10,5 Mo de DXF deviennent moins de 0,9 Mo, et environ 0,5 Mo
une fois compressés par le serveur.

─── CE QUI EST CONSERVÉ, ET CE QUI NE L'EST PAS ────────────────────────────────
Les deux calques qui portent la géométrie : la surface de la fosse, et le dôme. Les
coordonnées sont RECENTRÉES sur l'origine et mises à l'échelle : un relevé minier
porte des coordonnées projetées à sept chiffres, que la simple précision d'un
flottant 32 bits ne représente pas sans perdre le centimètre. Recentrer ramène tout
autour de zéro, où cette précision est largement suffisante.

Usage :
    python outils/convertir_fosse.py <fichier.dxf>
"""

from __future__ import annotations

import json
import pathlib
import struct
import sys
from collections import defaultdict

RACINE = pathlib.Path(__file__).resolve().parent.parent
SORTIE = RACINE / 'site' / 'assets' / 'fosse'

# Les deux calques retenus, et le rôle qu'ils jouent à l'écran.
CALQUES = {
    'DE_EMZ_PH07F_V16_Surf': 'fosse',
    '5-70-014_Contour_R_500_m': 'dome',
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
                faces[CALQUES[calque]].append([tuple(c) for c in coins])
        else:
            i += 1
    return faces


def indexer(faces: list) -> tuple[list[float], list[int]]:
    """Déduplique les sommets et triangule.

    LA DÉDUPLICATION SE FAIT AU MILLIMÈTRE. Deux faces voisines partagent un sommet
    que le DXF réécrit de son côté, parfois au bit près, parfois non. Arrondir au
    millimètre les réunit, ce qui divise le nombre de sommets par plus de deux sur
    ce fichier, et surtout permet plus tard de calculer des normales lissées."""
    index_par_point: dict[tuple, int] = {}
    positions: list[float] = []
    triangles: list[int] = []

    def rang(p):
        cle = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
        r = index_par_point.get(cle)
        if r is None:
            r = len(index_par_point)
            index_par_point[cle] = r
            positions.extend(cle)
        return r

    for a, b, c, d in faces:
        ia, ib, ic, idd = rang(a), rang(b), rang(c), rang(d)
        if ia == ib or ib == ic or ic == ia:
            continue                       # triangle dégénéré, rien à dessiner
        triangles.extend((ia, ib, ic))
        # Quatrième sommet distinct : la face est un quadrilatère, d'où un second
        # triangle. Quand il répète le troisième, on s'arrête là.
        if idd not in (ia, ib, ic):
            triangles.extend((ia, ic, idd))

    return positions, triangles


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

    # ── LE RECENTRAGE EST COMMUN AUX DEUX CALQUES ─────────────────────────────
    # Les recentrer séparément les décalerait l'un par rapport à l'autre : le dôme
    # ne serait plus au-dessus de son tir.
    xs, ys, zs = [], [], []
    for lot in faces.values():
        for f in lot:
            for p in f:
                xs.append(p[0]); ys.append(p[1]); zs.append(p[2])
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cz = min(zs)                      # l'origine se pose au fond de la fosse
    etendue = max(max(xs) - min(xs), max(ys) - min(ys))
    echelle = 2.0 / etendue           # le tout tient dans un cube de deux unités

    manifeste = {'echelle': round(etendue, 1), 'calques': {}}

    for nom, lot in faces.items():
        positions, triangles = indexer(lot)
        aretes = aretes_uniques(triangles)

        # Recentrage, mise à l'échelle, et passage en repère écran : le Z minier
        # est vertical, alors qu'un moteur 3D attend le Y vertical.
        plat = []
        for i in range(0, len(positions), 3):
            x = (positions[i] - cx) * echelle
            y = (positions[i + 1] - cy) * echelle
            z = (positions[i + 2] - cz) * echelle
            plat.extend((x, z, -y))

        f_pos = SORTIE / f'{nom}.pos.bin'
        f_tri = SORTIE / f'{nom}.tri.bin'
        f_are = SORTIE / f'{nom}.lin.bin'
        f_pos.write_bytes(struct.pack(f'<{len(plat)}f', *plat))
        f_tri.write_bytes(struct.pack(f'<{len(triangles)}I', *triangles))
        f_are.write_bytes(struct.pack(f'<{len(aretes)}I', *aretes))

        manifeste['calques'][nom] = {
            'sommets': len(plat) // 3,
            'triangles': len(triangles) // 3,
            'aretes': len(aretes) // 2,
        }
        print(f'  {nom:<6} {len(plat)//3:>7,} sommets  {len(triangles)//3:>7,} triangles  '
              f'{len(aretes)//2:>7,} aretes  '
              f'{(f_pos.stat().st_size + f_tri.stat().st_size + f_are.stat().st_size)/1024:>7,.0f} ko')

    (SORTIE / 'fosse.json').write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=1), encoding='utf-8')

    total = sum(f.stat().st_size for f in SORTIE.iterdir())
    print(f'Total : {total/1024/1024:.2f} Mo dans site/assets/fosse/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

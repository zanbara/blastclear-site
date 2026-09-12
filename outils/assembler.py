#!/usr/bin/env python3
"""
ASSEMBLAGE DES PAGES DU SITE BLASTCLEAR.

─── POURQUOI UN ASSEMBLEUR ALORS QUE LE SITE EST STATIQUE ──────────────────────
Le site sera bilingue et compte une dizaine de pages, soit une vingtaine de
fichiers portant le même en-tête et le même pied. Corrigés à la main, ils
divergent : une entrée de menu ajoutée sur douze pages et oubliée sur la
treizième ne se voit pas à la relecture, elle se découvre en production.

Ce que produit ce script est du HTML ordinaire, versionné dans site/ et servi
tel quel par GitHub Pages. La publication ne dépend donc d'aucun outil : le
script ne tourne que sur le poste, et seulement quand l'ossature change.

─── CE QUI EST GÉNÉRÉ, ET CE QUI NE L'EST PAS ──────────────────────────────────
Généré       : tout site/fr/*.html et site/en/*.html.
Écrit à la main : site/index.html (aiguillage de langue), site/css, site/js,
                  site/assets, et les fichiers de service (CNAME, robots.txt).

Un fichier généré porte un avertissement en tête. Ne jamais corriger une page de
site/ directement : la prochaine génération écraserait la correction.

Usage :
    python outils/assembler.py            assemble tout
    python outils/assembler.py --verifier  ne réécrit rien, signale ce qui a dérivé
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
GABARIT = RACINE / 'gabarit'
CONTENU = RACINE / 'contenu'
SORTIE = RACINE / 'site'

AVERTISSEMENT = (
    '<!-- FICHIER ASSEMBLÉ, NE PAS MODIFIER ICI.\n'
    '     Le corps de cette page vient de contenu/{lang}/{slug}.html ;\n'
    "     l'en-tête, le menu et le pied viennent de gabarit/.\n"
    '     Toute correction faite dans ce fichier sera perdue à la prochaine\n'
    '     exécution de outils/assembler.py. -->\n'
)

# L'entête de fragment : trois lignes de métadonnées, puis une ligne vide, puis le corps.
#   titre: ...
#   description: ...
#   slug: ...
ENTETE = re.compile(r'^(?:([a-z_]+)\s*:\s*(.*))$')


def lire_fragment(chemin: pathlib.Path) -> tuple[dict[str, str], str]:
    """Sépare les métadonnées du corps. Les métadonnées sont les premières lignes
    de la forme `cle: valeur`, jusqu'à la première ligne vide."""
    lignes = chemin.read_text(encoding='utf-8').splitlines()
    meta: dict[str, str] = {}
    i = 0
    while i < len(lignes):
        ligne = lignes[i].strip()
        if not ligne:
            i += 1
            break
        m = ENTETE.match(ligne)
        if not m:
            break
        meta[m.group(1)] = m.group(2).strip()
        i += 1
    manquantes = {'titre', 'description'} - meta.keys()
    if manquantes:
        raise SystemExit(
            f'{chemin} : métadonnée(s) manquante(s) : {", ".join(sorted(manquantes))}.\n'
            "Le fragment doit commencer par `titre:` et `description:`, puis une ligne vide."
        )
    return meta, '\n'.join(lignes[i:]).strip('\n')


def bloc_nav(config: dict, slug_courant: str) -> str:
    lignes = []
    for slug, href, libelle in config['nav']:
        courant = ' aria-current="page"' if slug == slug_courant else ''
        lignes.append(
            f'        <li><a class="nav__lien" href="{href}"{courant}>{html.escape(libelle)}</a></li>'
        )
    return '\n'.join(lignes)


def bloc_langues(lang: str, fichier: str) -> str:
    """Le sélecteur pointe sur LA MÊME page dans l'autre langue, pas sur son accueil.
    Renvoyer systématiquement à l'accueil fait perdre sa place au visiteur."""
    lignes = []
    for code, libelle in (('fr', 'FR'), ('en', 'EN')):
        cible = f'./{fichier}' if code == lang else f'../{code}/{fichier}'
        if fichier == 'index.html':
            cible = './' if code == lang else f'../{code}/'
        courant = ' aria-current="true"' if code == lang else ''
        lignes.append(f'        <a href="{cible}"{courant} hreflang="{code}">{libelle}</a>')
    return '\n'.join(lignes)


def bloc_pied(config: dict) -> str:
    blocs = []
    for titre, liens in config['pied_colonnes']:
        items = '\n'.join(
            f'          <li><a href="{href}">{html.escape(libelle)}</a></li>'
            for href, libelle in liens
        )
        blocs.append(
            f'      <div>\n'
            f'        <h4>{html.escape(titre)}</h4>\n'
            f'        <ul>\n{items}\n        </ul>\n'
            f'      </div>'
        )
    return '\n'.join(blocs)


def assembler(lang: str, config: dict, gabarit: str) -> list[tuple[pathlib.Path, str]]:
    dossier = CONTENU / lang
    if not dossier.is_dir():
        return []
    pages = []
    for fragment in sorted(dossier.glob('*.html')):
        meta, corps = lire_fragment(fragment)
        slug = meta.get('slug', fragment.stem)
        fichier = f'{fragment.stem}.html'
        page = gabarit
        remplacements = {
            'LANG': lang,
            'OG_LOCALE': config['og_locale'],
            'TITRE': html.escape(meta['titre'], quote=True),
            'DESCRIPTION': html.escape(meta['description'], quote=True),
            'FICHIER_CANONIQUE': '' if fichier == 'index.html' else fichier,
            'SAUT_CONTENU': html.escape(config['saut_contenu']),
            'LOGO_ALT': html.escape(config['logo_alt'], quote=True),
            'MENU_LABEL': html.escape(config['menu_label'], quote=True),
            'NAV_LABEL': html.escape(config['nav_label'], quote=True),
            'LANGUE_LABEL': html.escape(config['langue_label'], quote=True),
            'NAV': bloc_nav(config, slug),
            'LANGUES': bloc_langues(lang, fichier),
            'CORPS': corps,
            'PIED_BARATIN': html.escape(config['pied_baratin']),
            'PIED_COLONNES': bloc_pied(config),
            'PIED_DROITS': html.escape(config['pied_droits']),
            'PIED_AVERTISSEMENT': html.escape(config['pied_avertissement']),
        }
        for cle, valeur in remplacements.items():
            page = page.replace('{{' + cle + '}}', valeur)

        restants = re.findall(r'\{\{([A-Z_]+)\}\}', page)
        if restants:
            raise SystemExit(f'{fragment} : marqueur non remplacé : {", ".join(set(restants))}')

        # L'avertissement se glisse après la déclaration de type, pas avant :
        # un commentaire précédant <!doctype html> bascule les navigateurs en
        # mode de compatibilité et casse la mise en page.
        page = page.replace('<!doctype html>\n', '<!doctype html>\n' + AVERTISSEMENT.format(lang=lang, slug=fragment.stem), 1)

        pages.append((SORTIE / lang / fichier, page))
    return pages


def main() -> int:
    verifier = '--verifier' in sys.argv
    gabarit = (GABARIT / 'page.html').read_text(encoding='utf-8')
    config = json.loads((GABARIT / 'site.json').read_text(encoding='utf-8'))

    total, ecrits, derives = 0, 0, []
    for lang in ('fr', 'en'):
        if lang not in config:
            continue
        for chemin, contenu in assembler(lang, config[lang], gabarit):
            total += 1
            ancien = chemin.read_text(encoding='utf-8') if chemin.exists() else None
            if ancien == contenu:
                continue
            if verifier:
                derives.append(chemin.relative_to(RACINE))
                continue
            chemin.parent.mkdir(parents=True, exist_ok=True)
            chemin.write_text(contenu, encoding='utf-8', newline='\n')
            ecrits += 1
            print(f'  écrit  {chemin.relative_to(RACINE)}')

    if verifier:
        if derives:
            print(f'{len(derives)} page(s) ne correspondent plus à leur source :')
            for d in derives:
                print(f'  {d}')
            print('Relancer : python outils/assembler.py')
            return 1
        print(f'{total} page(s) à jour.')
        return 0

    print(f'{ecrits} page(s) réécrite(s) sur {total}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

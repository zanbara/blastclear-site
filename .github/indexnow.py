#!/usr/bin/env python3
"""
ANNONCE AUX MOTEURS DE RECHERCHE DES PAGES QUI VIENNENT DE CHANGER.

Appelé par .github/workflows/publier.yml, APRÈS le déploiement. Le commentaire de
cette étape explique pourquoi après, et pourquoi seulement les pages modifiées.

─── CE QUE CE SCRIPT REFUSE DE FAIRE ───────────────────────────────────────────
Il n'annonce JAMAIS une adresse au hasard. Trois garde-fous :

  1. La liste de départ est le plan du site, et lui seul. Une page hors du plan
     est une page que l'on ne veut pas indexée ; l'annoncer irait contre.
  2. Une adresse n'est retenue que si le fichier correspondant a changé dans cet
     envoi. C'est la règle du protocole, et ce qui lui garde sa valeur.
  3. Si la comparaison échoue, il n'annonce RIEN. Ne pas prévenir coûte quelques
     jours ; tout réannoncer à chaque exécution fait perdre la confiance du
     domaine, ce qui coûte beaucoup plus longtemps.

─── LA CLÉ N'EST PAS UN SECRET ─────────────────────────────────────────────────
Elle est publiée en clair à la racine du site, comme le protocole l'exige : c'est
ainsi que le moteur vérifie que celui qui l'annonce possède bien le domaine. Elle
n'ouvre aucun accès et ne se dérobe pas. Elle vit donc dans le dépôt, et non dans
un secret de dépôt, où elle serait invisible et intrigante.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

RACINE = pathlib.Path(__file__).resolve().parent.parent
DOMAINE = 'www.blastclear.com'
CLE = '887411f5597148abb2d565e405f86a1e'
POINT_D_ENTREE = 'https://api.indexnow.org/IndexNow'

# Un envoi vide, un envoi qui se trompe de domaine, une clé absente : le service
# répond par un code d'erreur explicite, qu'on rapporte tel quel.
CODES = {
    200: 'reçu',
    202: 'reçu, clé en cours de vérification',
    400: 'requête mal formée',
    403: 'clé refusée : le fichier de clé est introuvable ou ne correspond pas',
    422: 'adresses refusées : elles n\'appartiennent pas au domaine déclaré',
    429: 'trop d\'annonces : le domaine est momentanément limité',
}


def adresses_du_plan() -> dict[str, str]:
    """Les adresses publiques, et le fichier de chacune. Le plan du site fait foi."""
    plan = (RACINE / 'site' / 'sitemap.xml').read_text(encoding='utf-8')
    table = {}
    for adresse in re.findall(r'<loc>([^<]+)</loc>', plan):
        chemin = adresse.split(DOMAINE, 1)[-1].lstrip('/')
        if not chemin or chemin.endswith('/'):
            chemin += 'index.html'
        table[f'site/{chemin}'] = adresse
    return table


def fichiers_modifies(avant: str, apres: str) -> set[str] | None:
    """Les fichiers touchés par cet envoi, ou None si la comparaison n'est pas
    possible — premier envoi, réécriture d'historique, dépôt tronqué."""
    # Quarante zéros : ce que GitHub met dans « before » quand la branche vient
    # d'être créée. Il n'y a alors aucun état antérieur à comparer.
    if not avant or set(avant) == {'0'} or not apres:
        return None
    for reference in (avant, apres):
        verif = subprocess.run(['git', 'cat-file', '-e', reference + '^{commit}'],
                               cwd=RACINE, capture_output=True)
        if verif.returncode != 0:
            return None
    diff = subprocess.run(['git', 'diff', '--name-only', avant, apres],
                          cwd=RACINE, capture_output=True, text=True)
    if diff.returncode != 0:
        return None
    return {ligne.strip() for ligne in diff.stdout.splitlines() if ligne.strip()}


def annoncer(adresses: list[str]) -> int:
    corps = json.dumps({
        'host': DOMAINE,
        'key': CLE,
        'keyLocation': f'https://{DOMAINE}/{CLE}.txt',
        'urlList': adresses,
    }).encode('utf-8')
    requete = urllib.request.Request(
        POINT_D_ENTREE, data=corps, method='POST',
        headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            code = reponse.status
    except urllib.error.HTTPError as erreur:
        code = erreur.code
    except urllib.error.URLError as erreur:
        print(f'IndexNow injoignable : {erreur.reason}')
        return 1
    print(f'IndexNow a répondu {code} : {CODES.get(code, "réponse inattendue")}')
    return 0 if code in (200, 202) else 1


def main() -> int:
    table = adresses_du_plan()

    if os.environ.get('MANUEL') == 'true':
        # Republication demandée à la main : on annonce tout, puisque c'est
        # précisément ce que l'on vient de demander.
        retenues = sorted(table.values())
        print(f'Republication manuelle : {len(retenues)} adresse(s) annoncée(s).')
    else:
        modifies = fichiers_modifies(os.environ.get('AVANT', ''),
                                     os.environ.get('APRES', ''))
        if modifies is None:
            print('Comparaison impossible : aucune annonce. '
                  'Une republication manuelle les annoncera toutes.')
            return 0
        retenues = sorted(a for f, a in table.items() if f in modifies)
        if not retenues:
            print('Aucune page publique modifiée : rien à annoncer.')
            return 0
        print(f'{len(retenues)} page(s) modifiée(s) :')
        for a in retenues:
            print(f'  {a}')

    return annoncer(retenues)


if __name__ == '__main__':
    sys.exit(main())

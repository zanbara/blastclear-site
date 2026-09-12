# Site web BlastClear

Le site de `blastclear.com`. Treize langues, pages statiques, aucune dépendance à
l'exécution.

---

## Comment le dossier est organisé

| Dossier | Contenu | Publié ? |
|---|---|---|
| `site/` | **Ce qui est mis en ligne.** Rien d'autre. | oui |
| `design/` | Les canevas exportés de Claude Design, source de la conversion | non |
| `gabarit/` | En-tête, menu et pied communs, pour les pages écrites à la main | non |
| `contenu/` | Textes source, et brouillons en attente de reprise | non |
| `marque/` | Charte graphique et logos maîtres | non |
| `outils/` | Les deux scripts de génération | non |
| `docs/` | Procédures : DNS, messagerie, mise en ligne | non |

---

## Les deux scripts, et quand les lancer

### `outils/convertir_design.py`

Transforme les canevas de `design/` en pages publiables dans `site/`.

```
python outils/convertir_design.py
```

**À relancer après toute modification des canevas**, ou du script lui-même. Il
réécrit `site/<langue>/index.html`, `site/<langue>/demo.html`, `site/css/design.css`,
`site/js/design.js` et les images de `site/assets/design/`.

Ce qu'il fait, et qui n'est pas qu'une recopie :

- résout les marqueurs de l'éditeur, les conditions et les survols, absents du HTML ;
- **transpose la palette de la maquette vers celle de la charte** : bleu `#25498A`,
  jaune `#FDC30E`, police Poppins ;
- applique les corrections de vocabulaire métier dans les treize langues, et se
  plaint si l'une ne trouve plus sa cible ;
- remplace la capture unique par un carrousel de quatre vues ;
- intègre le faisceau balistique dans la page pour pouvoir l'animer.

### `outils/assembler.py`

Assemble les pages écrites à la main, à partir de `contenu/<langue>/*.html` et de
`gabarit/`. Il n'a aucune page à traiter pour l'instant : les quatre brouillons
attendent dans `contenu/_brouillons-fr/`.

```
python outils/assembler.py             assemble
python outils/assembler.py --verifier  signale ce qui a dérivé, sans rien réécrire
```

---

## Voir le site avant publication

```
cd site
python -m http.server 8765
```

Puis `http://127.0.0.1:8765/`.

**Passer par un serveur, et non par un double-clic sur le fichier.** En `file://`,
les chemins absolus de la page d'accueil ne résolvent pas, et la redirection de
langue ne fonctionne pas.

---

## Règles de la charte que le code applique

Elles viennent de `marque/BlastClear_Charte_Graphique.html`.

| Règle | Où elle est tenue |
|---|---|
| Bleu `#25498A`, jaune `#FDC30E`, anthracite `#14171C` | table `COULEURS` du convertisseur |
| Poppins, servie par le site | `@font-face` de `site/css/design.css` |
| **Jamais de texte jaune sur fond blanc** (1,62:1) | le jaune ne sert qu'en aplat ou sur fond sombre |
| Voile d'au moins 60 % sous un élément posé sur une photographie | `renforcer_bandeau` |
| Le logo ne se recolore pas | les SVG maîtres sont repris tels quels, seulement recadrés |

---

## Ce qu'il reste à faire

- **Fournir deux captures d'écran** pour le carrousel : le plan PDF produit, et la
  fusion de plusieurs tirs. Les emplacements sont nommés dans la page ; le chemin se
  renseigne dans la table `DIAPOS` du convertisseur.
- **Reprendre les pages Vibrations et Mentions légales.** Elles sont rédigées, dans
  `contenu/_brouillons-fr/`, mais sur un habillage antérieur à la maquette.
- **Trancher trois points ouverts** : les chiffres de la section Résultats, qui
  demandent une source ; la visibilité du dépôt ; le service de collecte du
  formulaire de démonstration.

---

## Deux avertissements

**Ne jamais corriger un fichier de `site/` à la main.** Il est généré. La prochaine
exécution du convertisseur écraserait la correction sans le dire. Chaque page porte
d'ailleurs cet avertissement en tête.

**La stratégie de monétisation ne doit pas entrer dans le dépôt.** Elle contient les
commissions partenaires et le partage de revenus nominatif. Elle est exclue par
`.gitignore`, et cette exclusion vaut même si le dépôt est privé : un dépôt privé peut
devenir public, et l'historique git, lui, garde tout.

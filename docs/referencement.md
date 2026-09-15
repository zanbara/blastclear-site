# Être trouvé par les moteurs de recherche

Ce que le site fait tout seul, ce qui reste à faire une fois pour toutes, et ce qu'il
ne faut pas espérer.

---

## Ce qu'un moteur regarde, dans l'ordre

Un moteur de recherche fait trois choses, et dans cet ordre. **Il découvre** une
adresse, par un lien ou par le plan du site. **Il l'explore**, s'il en a le droit.
**Il l'indexe**, s'il juge la page digne de figurer dans ses résultats.

Un défaut à la première étape rend les deux autres sans objet. C'est pourquoi le plan
du site et le fichier `robots.txt` comptent davantage que n'importe quel réglage de
mots-clés : ils décident de ce qui sera vu, quand tout le reste ne décide que du rang.

---

## Ce qui est automatique

Tout ce qui suit est produit par `python outils/convertir_design.py`. **Aucun de ces
fichiers ne se modifie à la main** : la conversion suivante écraserait la retouche.

| Fichier | Rôle |
|---|---|
| `site/sitemap.xml` | Les 26 adresses publiques, avec la date réelle du dernier changement de chacune et ses treize traductions déclarées |
| `site/robots.txt` | Ouvre l'exploration, et indique le plan du site |
| `site/404.html` | La page des adresses introuvables, servie par GitHub Pages à toute profondeur |
| `site/<clé>.txt` | La clé IndexNow, publiée en clair comme le protocole l'exige |

Dans chaque page : le titre, la description, l'adresse canonique, les treize
`hreflang` plus `x-default`, les balises de partage, et sur les accueils une
déclaration de données structurées.

### Les dates du plan du site ne mentent pas

Elles ne sont ni la date du jour, ni la date du fichier, mais celle du dernier
enregistrement git ayant touché la page — et le jour même si la page est modifiée mais
pas encore enregistrée.

Cela a l'air d'un détail, et c'en est un jusqu'au jour où ce n'en est plus un. Google
a publié la règle : un plan dont les dates suivent le jour de génération est considéré
comme non fiable, et **ses dates cessent alors d'être lues**. On perd l'outil au
moment exact où l'on voudrait signaler qu'une page vient d'être refaite.

### Les pages de demande et de remerciement

Elles portent `noindex`, et l'exploration leur est **ouverte**. Ce n'est pas une
contradiction, c'est la seule façon que cela fonctionne : `Disallow` interdit de LIRE
la page, donc d'y lire le `noindex`. Un moteur qui connaît l'adresse par les liens de
l'accueil sans pouvoir en voir le contenu publie alors un lien nu, sans titre ni
description. C'est exactement ce que l'on voulait éviter, obtenu par le moyen censé
l'empêcher.

---

## Ce qui reste à faire, une fois

### 1. Google Search Console

Sans elle, on publie à l'aveugle : aucun moyen de savoir si Google a vu le site, ce
qu'il en a indexé, ni sur quelles recherches il l'affiche.

1. Ouvrir <https://search.google.com/search-console> et ajouter une propriété.
2. Choisir **Domaine** (`blastclear.com`), et non « Préfixe d'URL ». La propriété de
   domaine couvre `www`, la racine, `http`, `https` et tout sous-domaine à venir, d'un
   seul enregistrement. Le préfixe d'URL en demanderait un par variante.
3. Google donne un enregistrement **TXT** à poser chez Namecheap, onglet *Advanced
   DNS* : hôte `@`, valeur `google-site-verification=…`.

   > **Ne toucher à aucun autre enregistrement TXT.** Ils portent SPF, DKIM et DMARC,
   > et la messagerie tombe sans avertissement si l'un d'eux disparaît. Voir
   > `docs/dns-et-messagerie.md`.

4. La vérification prend de quelques minutes à quelques heures, le temps de la
   propagation.
5. Une fois vérifiée : menu **Sitemaps**, déclarer `https://www.blastclear.com/sitemap.xml`.
   Une seule fois, définitivement.

### 2. Bing Webmaster Tools

Bing alimente Bing, Yahoo, DuckDuckGo et la recherche intégrée à Windows. Ce n'est pas
un marché à négliger : c'est celui des postes d'entreprise, et les ingénieurs
d'exploitation cherchent depuis un poste d'entreprise.

1. Ouvrir <https://www.bing.com/webmasters>.
2. **Importer depuis Google Search Console.** C'est proposé à la première ouverture et
   cela reprend la propriété et le plan du site sans rien vérifier à nouveau. Faire
   donc la Search Console d'abord.
3. Sinon, vérification par DNS de la même façon qu'au-dessus.

### 3. Rien d'autre

Il n'y a pas d'autre moteur à prévenir. Yahoo, DuckDuckGo et Ecosia se servent de
Bing ou de Google ; Yandex et Seznam sont prévenus par IndexNow, ci-dessous, sans
inscription.

---

## IndexNow, et ce qu'il ne fait pas

À chaque publication, le workflow annonce aux moteurs les adresses qui viennent de
changer. Un moteur passe alors dans l'heure, au lieu de repasser quand il le décide,
ce qui sur un site neuf peut prendre des semaines.

Une seule annonce atteint **Bing, Yandex, Seznam, Naver et Yep**, qui partagent le même
point d'entrée.

**Google n'en fait pas partie.** Il a essayé le protocole, puis s'en est tenu à
l'écart. Pour lui, il n'y a que le plan du site et la Search Console — d'où le point 1
ci-dessus, qui n'a pas de substitut.

Le mécanisme n'annonce **que les pages modifiées**. Réannoncer les vingt-six adresses
à chaque envoi, y compris pour une correction de feuille de style, ferait perdre au
signal ce qui en fait la valeur, et les moteurs limitent les domaines qui en abusent.
Si la comparaison échoue, rien n'est annoncé : ne pas prévenir coûte quelques jours,
tout réannoncer coûte la confiance du domaine.

Une republication lancée à la main depuis l'onglet *Actions* annonce, elle, les
vingt-six adresses : c'est précisément ce que l'on demande en la lançant.

La clé vit dans `.github/indexnow.py` et dans `site/<clé>.txt`. **Ce n'est pas un
secret** : le protocole exige qu'elle soit publiée en clair, c'est ainsi que le moteur
vérifie que celui qui annonce possède bien le domaine. Elle n'ouvre aucun accès.

---

## Vérifier

**Le lendemain de la publication**, et sans attendre d'être indexé :

```
https://www.blastclear.com/robots.txt      s'ouvre, et cite le plan du site
https://www.blastclear.com/sitemap.xml     s'ouvre, 26 adresses
https://www.blastclear.com/zz/             affiche la page des introuvables
```

Dans l'onglet *Actions* du dépôt, l'étape « Prévenir les moteurs » doit afficher
`IndexNow a répondu 200 : reçu`. Un `403` signifie que le fichier de clé n'est pas
encore en ligne : republier suffit.

**Une semaine après**, dans la Search Console : *Indexation des pages* doit montrer
des pages indexées, et *Inspection d'URL* sur `https://www.blastclear.com/fr/` doit
répondre « URL sur Google ».

**Le test de résultats enrichis** de Google, sur l'adresse d'un accueil, doit
reconnaître un `SoftwareApplication` et un `WebSite` sans erreur.

---

## Ce qu'il ne faut pas espérer

**Un site neuf n'arrive pas en tête.** Le domaine n'a aucun historique, aucun lien
entrant, aucune mesure d'usage. Les premières semaines, il ne sortira que sur son
propre nom. C'est normal et cela ne se corrige par aucun réglage.

**Ce qui fait vraiment monter un site de cette nature**, dans l'ordre :

1. **Des liens depuis des sites du métier.** Un article, un annuaire de fournisseurs
   miniers, une association professionnelle, une publication. Un seul lien depuis un
   site reconnu du secteur pèse plus que toutes les balises de ce document réunies.
2. **Du contenu qui répond à une question qu'on se pose.** La page « pourquoi » en est
   un début : elle compare le cercle au dôme, ce qui est une vraie question de métier.
   Une page par question ferait mieux qu'une page qui les aborde toutes.
3. **Le temps.** Six mois est un ordre de grandeur honnête pour un domaine neuf.

**Les comptes des réseaux sociaux ne sont pas déclarés** dans les données structurées,
bien que les adresses figurent dans le pied de page. Tant que les comptes ne sont pas
ouverts, les déclarer reviendrait à donner pour vraies des pages qui n'existent pas.
Les ouvrir, puis me le dire : la déclaration est alors une ligne à ajouter.

**L'adresse des pages « pourquoi » reste en français dans les treize langues**
(`/en/pourquoi.html`). Le gain d'une traduction des adresses serait faible, et le coût
réel : le site est en ligne, et changer une adresse publiée demande d'en maintenir
l'ancienne indéfiniment. Si vous préférez malgré tout, c'est faisable, dites-le avant
que les liens ne se répandent.

# Publier le site

Hébergement **GitHub Pages**, dépôt **public**, DNS conservé chez **Namecheap**.

---

## Pourquoi ce montage

**Le dépôt est public** parce que GitHub Pages ne publie depuis un dépôt privé qu'avec
un abonnement payant. Les documents de travail commerciaux et les canevas de la
maquette en sont donc exclus par `.gitignore`. Cette exclusion n'est pas réversible
dans l'autre sens : ce qui entre une fois dans l'historique git y reste, même
supprimé ensuite.

**Le DNS reste chez Namecheap** parce que la messagerie y est configurée. Déplacer les
serveurs de noms obligerait à recréer les enregistrements MX, SPF, DKIM et DMARC
ailleurs, et la moindre omission ferait tomber le courrier sans avertissement.

---

## 1. Le dépôt

```
cd "D:\Claude Code\BlastClear Site"
git init
git add .
git commit -m "Site BlastClear : 13 langues, converties depuis les canevas Claude Design"
```

**Avant le premier envoi, vérifier ce qui part.** Deux contrôles, et ils valent la
peine.

Le premier liste les dossiers versionnés. Seuls `site`, `marque`, `contenu`,
`gabarit`, `outils` et `docs` doivent apparaître :

```
git ls-files | ForEach-Object { ($_ -replace '^"','' -split '/')[0] } | Sort-Object -Unique
```

Le second cherche, dans le contenu des fichiers versionnés, ce qui n'a pas à être
publié : les montants de la grille de licence et les noms de partenaires
commerciaux. Compléter la première ligne avec les noms à surveiller.

```
$aProscrire = '8[ ,]500|7[ ,]500|7[ ,]000|NomDuPartenaire'
git ls-files | ForEach-Object {
  $p = $_ -replace '^"|"$',''
  if (Test-Path -LiteralPath $p) {
    $c = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $p))
    if ($c -match $aProscrire) { "  $p" }
  }
}
```

Il ne doit **rien** renvoyer. Si l'un des deux contrôles signale quelque chose, ne pas
pousser : compléter `.gitignore`, vider l'index avec `git read-tree --empty`, refaire
`git add -A`, puis recontrôler.

> **Une valeur en dollars n'est pas forcément une fuite.** La section des résultats
> publie sciemment une estimation de coût par tir. Le contrôle porte sur la grille de
> licence, qui, elle, n'est pas publiée.

Puis :

```
gh repo create blastclear-site --public --source=. --remote=origin --push
```

---

## 2. Activer Pages

Dans les réglages du dépôt, rubrique Pages :

- Source : branche `main`
- Dossier : **`/site`**, et non la racine

Le fichier `site/CNAME` contient déjà `blastclear.com` : GitHub y lit le domaine
personnalisé tout seul.

---

## 3. Le DNS, chez Namecheap

Onglet **Advanced DNS** du domaine.

**À supprimer :**

| Type | Hôte | Valeur |
|---|---|---|
| A | `@` | `192.64.119.108` (parking) |
| CNAME | `www` | `parkingpage.namecheap.com` |

**À ajouter :**

| Type | Hôte | Valeur |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `zanbara.github.io` |

**Ne toucher à aucun enregistrement MX ni TXT.** Ils portent la messagerie.

Faire ce changement **dans le même passage** que celui de `docs/dns-et-messagerie.md` :
chacun demande quelques heures de propagation, et les enchaîner évite d'attendre deux
fois.

---

## 4. Le certificat

Une fois les enregistrements A propagés, GitHub émet un certificat automatiquement.
Cocher alors **Enforce HTTPS** dans les réglages Pages. La case reste grisée tant que
le certificat n'est pas délivré : c'est normal, il faut parfois une heure.

---

## 5. Publier une modification

```
python outils/convertir_design.py     si les canevas ou le script ont changé
git add -A
git commit -m "…"
git push
```

La mise en ligne suit d'une à deux minutes. **Ne jamais modifier un fichier de `site/`
à la main** : il est généré, et la prochaine conversion écraserait la retouche.

---

## 6. Vérification

1. `https://blastclear.com` et `https://www.blastclear.com` répondent tous les deux.
2. Le certificat est valide, `http` redirige vers `https`.
3. La racine oriente vers la bonne langue, et le sélecteur bascule d'une page à
   l'autre sans revenir à l'accueil.
4. Les quatre vues du carrousel défilent, et les trajectoires balistiques se tracent.
5. La page se lit à 400 px de large sans défilement horizontal.
6. **La messagerie fonctionne toujours** : envoyer un message à
   `contact@blastclear.com` après la bascule. C'est le contrôle qui prouve qu'on n'a
   pas abîmé les MX en modifiant les A.

---

## Le formulaire de démonstration

Il ouvre le logiciel de messagerie du visiteur, à destination de
`contact@blastclear.com`. Aucun service tiers, donc aucune donnée personnelle
transmise à qui que ce soit, et rien à configurer.

GitHub Pages ne traite aucun envoi de formulaire : il ne sert que des fichiers. Pour
recevoir les demandes sans que le visiteur ait à confirmer dans sa messagerie, il
faudrait un service de collecte. La marche à suivre est décrite à la fin de
`docs/dns-et-messagerie.md`.

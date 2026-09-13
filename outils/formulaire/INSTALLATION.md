# Recevoir les demandes de démonstration dans une feuille Google

Les demandes arrivent dans une feuille Google et déclenchent un courriel vers
`contact@blastclear.com` et `anouar.zanbara@gmail.com`.

Compter vingt minutes. Aucune ligne de code à écrire.

---

## Pourquoi ce montage

Les coordonnées d'un prospect sont une donnée commerciale. Ici elles ne quittent pas
votre compte Google : pas d'intermédiaire, pas d'abonnement, pas de quota mensuel, et
rien à réclamer à personne le jour où vous changez d'avis.

La contrepartie est ce fichier, à installer une fois.

---

## 1. La feuille

1. Créer une feuille Google, la nommer par exemple **BlastClear — Demandes de démo**.
2. La laisser **privée**. Elle contiendra des coordonnées professionnelles
   nominatives : nom, société, poste, courriel, téléphone.

**Ne pas créer les colonnes à la main.** Le script crée l'onglet `Demandes` et ses
en-têtes au premier envoi, dans le bon ordre.

| Colonne | Contenu |
|---|---|
| Date et heure | horodatage de réception |
| Langue de la page | `fr`, `en`, `es`… La langue dans laquelle répondre |
| Nom et prénom | |
| Société | |
| Poste | |
| Courriel | |
| Indicatif | `+226`, `+27`… |
| Téléphone | |
| Message | |
| Page d'origine | l'adresse d'où la demande a été envoyée |
| Navigateur | utile seulement pour comprendre un envoi anormal |

> **Ajouter un champ plus tard se fait en FIN de liste**, dans `COLONNES` du script,
> jamais au milieu : insérer une colonne décalerait toutes les lignes déjà
> enregistrées.

---

## 2. Le script

1. Dans la feuille : menu **Extensions**, puis **Apps Script**.
2. Effacer le contenu de `Code.gs` et y coller **tout** le fichier
   `outils/formulaire/Code.gs`.
3. Modifier **une seule ligne**, la valeur de `JETON` :

   ```js
   var JETON = 'une-chaine-a-vous-choisir';
   ```

   N'importe quelle chaîne convient. Elle ne protège aucun secret : elle filtre les
   envois automatisés, qui finissent toujours par trouver une application web
   ouverte. Sans elle, ils atterriraient dans la feuille et dans votre boîte.

4. Enregistrer.

---

## 3. Autoriser, et vérifier

1. Dans la liste des fonctions, choisir **`essai`**, puis **Exécuter**.
2. Google demande les autorisations : écrire dans la feuille, envoyer un courriel en
   votre nom. Les accorder.

   > L'écran « Google n'a pas validé cette application » est attendu : l'application,
   > c'est votre propre script. Cliquer sur **Paramètres avancés**, puis sur
   > **Accéder à …**.

3. Vérifier les deux résultats : une ligne d'essai dans la feuille, et un courriel
   reçu. Si les deux sont là, le montage fonctionne. Supprimer la ligne d'essai.

**Ne pas passer à l'étape suivante avant que ces deux vérifications aboutissent.**
Une fois le site branché, un échec ne se verrait plus : les demandes disparaîtraient
sans laisser de trace.

---

## 4. Publier l'application web

1. Bouton **Déployer**, puis **Nouveau déploiement**.
2. Type : **Application web**.
3. Deux réglages, et ils comptent :

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Exécuter en tant que | **Moi** | Le script écrit dans VOTRE feuille et envoie depuis VOTRE compte. Un visiteur n'a aucun accès à l'une ni à l'autre. |
| Qui a accès | **Tout le monde** | Le visiteur du site n'est pas connecté à Google. Sans cela, personne ne pourrait envoyer. |

4. Copier l'adresse produite. Elle ressemble à :

   ```
   https://script.google.com/macros/s/AKfycb…/exec
   ```

---

## 5. Brancher le site

Dans `outils/convertir_design.py`, en tête de fichier :

```python
COLLECTE_URL = 'https://script.google.com/macros/s/AKfycb…/exec'
JETON_FORMULAIRE = 'une-chaine-a-vous-choisir'     # LE MÊME que dans Code.gs
```

Puis :

```
python outils/convertir_design.py
git add -A
git commit -m "Branche le formulaire sur la feuille de collecte"
git push
```

Les treize pages basculent ensemble. **Le jeton doit être identique des deux côtés**,
sinon le script refuse tout, sans message visible pour le visiteur.

---

## 6. Vérifier depuis le site

Envoyer une vraie demande depuis `https://www.blastclear.com/fr/demo.html`.

Trois choses doivent se produire :

1. La page de remerciement s'affiche.
2. Une ligne apparaît dans la feuille, avec `fr` en langue.
3. Le courriel arrive aux deux adresses.

Recommencer depuis `https://www.blastclear.com/en/demo.html` et vérifier que la
langue enregistrée est bien `en`.

---

## Ce qu'il faut savoir avant de basculer

**Une mention devient nécessaire sur la page.** Tant que le formulaire ouvre la
messagerie du visiteur, rien n'est collecté et il n'y a rien à déclarer. Dès que les
données sont enregistrées, il faut dire sur la page qui les reçoit, pourquoi, combien
de temps elles sont conservées, et comment en demander la suppression. Une ligne sous
le bouton d'envoi suffit ; elle reste à rédiger.

**Le courriel de notification part de votre compte Google.** Il porte donc votre
adresse Gmail comme expéditeur, et non `contact@blastclear.com`, tant que la
messagerie professionnelle n'est pas en service. C'est sans conséquence : cette
notification ne va qu'à vous.

**Répondre au prospect se fait depuis la notification.** Le champ de réponse y
désigne déjà son adresse : répondre écrit directement à la bonne personne, sans avoir
à la recopier.

**Le script prévient s'il échoue.** En cas d'erreur, il vous envoie un courriel
plutôt que de perdre la demande en silence. Une demande perdue ne se rattrape pas, et
personne ne va relire les journaux d'un script.

---

## Revenir en arrière

Remettre `COLLECTE_URL = ''`, relancer la conversion, pousser. Le formulaire
retrouve l'ouverture de la messagerie. La feuille et le script restent en place, sans
rien recevoir.

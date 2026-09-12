# DNS et messagerie de blastclear.com

Procédure complète, de l'état constaté à l'état visé. Tout se fait chez **Namecheap**,
dans l'onglet **Advanced DNS** du domaine. **Les serveurs de noms ne changent pas.**

---

## 1. État constaté le 11 septembre 2026

Relevé par interrogation DNS depuis le poste, avant toute modification.

| Enregistrement | Valeur constatée |
|---|---|
| Serveurs de noms | `dns1.registrar-servers.com`, `dns2.registrar-servers.com` (Namecheap BasicDNS) |
| A sur `@` | `192.64.119.108` (page de parking Namecheap) |
| CNAME sur `www` | `parkingpage.namecheap.com` |
| MX | `eforward1` à `eforward5.registrar-servers.com` (redirection gratuite Namecheap) |
| TXT SPF | `v=spf1 include:spf.efwd.registrar-servers.com ~all` |
| TXT `_dmarc` | absent |
| TXT `google._domainkey` | absent |

Deux conséquences immédiates :

- **La plomberie de messagerie existe déjà**, mais aucun alias n'est créé : un courrier
  envoyé à `contact@blastclear.com` n'arrive nulle part.
- **Un courrier partant de ce domaine est mal authentifié.** Sans DKIM ni DMARC, il finit
  en indésirable chez une bonne partie des destinataires professionnels.

Pour relever à nouveau cet état à tout moment :

```powershell
Resolve-DnsName blastclear.com -Type A
Resolve-DnsName www.blastclear.com -Type CNAME
Resolve-DnsName blastclear.com -Type MX
Resolve-DnsName blastclear.com -Type TXT
Resolve-DnsName google._domainkey.blastclear.com -Type TXT
Resolve-DnsName _dmarc.blastclear.com -Type TXT
```

---

## 2. État visé

| Enregistrement | Valeur visée | Rôle |
|---|---|---|
| A sur `@` | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` | Le site, sur GitHub Pages |
| CNAME sur `www` | `zanbara.github.io` | Le site, en `www` |
| MX | `smtp.google.com`, priorité 1 | Google Workspace |
| TXT SPF | `v=spf1 include:_spf.google.com ~all` | Qui a le droit d'envoyer |
| TXT `google._domainkey` | la clé fournie par la console Google | Signature des messages |
| TXT `_dmarc` | `v=DMARC1; p=none; rua=mailto:contact@blastclear.com` | Surveillance, puis mise en quarantaine |

---

## 3. Ordre des opérations

**Faire les deux séries de modifications DNS dans le même passage.** Chacune demande une
propagation de quelques heures ; les enchaîner évite d'attendre deux fois.

### 3.1 Souscrire Google Workspace

1. Google Workspace Business Starter, utilisateur principal `contact@blastclear.com`.
2. Google fournit un enregistrement TXT de vérification. L'ajouter chez Namecheap,
   type `TXT`, hôte `@`, puis valider dans la console Google.

### 3.2 Basculer la messagerie

3. **Supprimer les cinq enregistrements MX `eforward*.registrar-servers.com`.**
   La redirection gratuite Namecheap cesse alors de fonctionner : c'est voulu, les deux
   systèmes ne peuvent pas coexister sur les mêmes MX.
4. Ajouter un MX : hôte `@`, valeur `smtp.google.com`, priorité `1`.
5. **Remplacer** l'enregistrement SPF existant par `v=spf1 include:_spf.google.com ~all`.

   > Il ne doit rester **qu'un seul** enregistrement SPF sur le domaine. Deux
   > enregistrements SPF font échouer la vérification pour tout le monde, y compris pour
   > les messages parfaitement légitimes. Modifier celui qui existe, ne pas en ajouter un.

6. Dans la console d'administration Google, générer la clé **DKIM en 2048 bits**, publier
   le TXT sur l'hôte `google._domainkey`, puis **activer la signature** dans la console.
   La génération de la clé ne suffit pas : tant que l'activation n'est pas faite, rien
   n'est signé.
7. Ajouter le TXT `_dmarc` : `v=DMARC1; p=none; rua=mailto:contact@blastclear.com`.

   > **Commencer en `p=none`, pas en `p=reject`.** Le mode `none` observe sans rien
   > bloquer. Passer directement au rejet ferait disparaître, sans trace visible, les
   > messages légitimes envoyés par un service qui n'aurait pas été déclaré. Rester en
   > observation deux à trois semaines, lire les rapports reçus sur `contact@`, puis
   > passer à `p=quarantine`.

### 3.3 Créer support@

8. Dans la console Google, ajouter `support@blastclear.com` **en alias** de l'utilisateur
   `contact@blastclear.com`. Un alias est gratuit ; un second utilisateur serait un second
   abonnement. Le jour où une autre personne traite le support, l'alias devient un groupe
   Google, sans aucun changement DNS.
9. Dans Gmail, réglages, comptes : ajouter `support@blastclear.com` en adresse d'envoi,
   pour pouvoir répondre depuis cette adresse.

### 3.4 Basculer le site

10. **Supprimer** l'enregistrement A vers `192.64.119.108` et le CNAME `www` vers
    `parkingpage.namecheap.com`.
11. Ajouter les **quatre** A sur `@` : `185.199.108.153`, `185.199.109.153`,
    `185.199.110.153`, `185.199.111.153`.
12. Ajouter le CNAME `www` vers `zanbara.github.io`.

---

## 4. Vérification

À faire après propagation, quelques heures plus tard.

1. Relancer les six commandes du paragraphe 1 et comparer à l'état visé.
2. Envoyer un message **depuis** `contact@blastclear.com` vers une adresse extérieure,
   puis passer le test de `mail-tester.com`.
   Attendu : **SPF, DKIM et DMARC en réussite tous les trois**, note d'au moins 9 sur 10.
3. Envoyer un message **vers** `support@blastclear.com` et vérifier qu'il arrive dans la
   boîte de `contact@`.
4. Ouvrir `https://blastclear.com` et `https://www.blastclear.com` : les deux répondent,
   le certificat est valide, `http` redirige vers `https`.

---

## 5. Le formulaire de demande de démonstration

Les pages `*/demo.html` portent un vrai formulaire. **GitHub Pages ne traite aucun envoi**,
puisqu'il ne sert que des fichiers.

En l'état, le formulaire compose un message dans le logiciel de messagerie du visiteur, à
destination de `contact@blastclear.com`. Rien ne transite par un tiers, et il n'y a rien à
configurer. En contrepartie, le visiteur doit avoir un client de messagerie configuré, et
il doit confirmer l'envoi.

Pour recevoir les demandes sans cette étape, il faut un service de collecte (Formspree,
Web3Forms et leurs équivalents). Le branchement se fait sur la balise `<form>` :

```html
<form action="https://formspree.io/f/VOTRE_IDENTIFIANT" method="POST" ...>
```

Dès qu'un `action` est présent, le script de la page cesse d'intercepter l'envoi et laisse
le navigateur poster normalement. La modification se fait dans `outils/convertir_design.py`,
fonction `rectifier_formulaire`, pour qu'elle survive à une nouvelle conversion.

> **À décider avant de brancher un tel service** : les coordonnées d'un prospect passeront
> alors par un tiers. Cela demande une mention dans la page et, selon les destinataires, un
> traitement au titre du RGPD.

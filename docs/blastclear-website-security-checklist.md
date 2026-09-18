# 🔒 Checklist Sécurisation Site BlastClear.com

**Statut** : www.blastclear.com est actuellement publié  
**Priorité** : CRITIQUE (données minières sensibles en jeu)  
**Dernière mise à jour** : Septembre 2026  

---

## 📋 Table des matières

1. [Infrastructure & Hosting](#1--infrastructure--hosting)
2. [Sécurité des données](#2--sécurité-des-données)
3. [Conformité & Audit](#3--conformité--audit)
4. [Monitoring & Incidents](#4--monitoring--incidents)
5. [Développement sécurisé](#5--développement-sécurisé)
6. [Gestion des secrets](#6--gestion-des-secrets)
7. [Calendrier d'implémentation](#7--calendrier-dimplémentation)

---

## 1️⃣ INFRASTRUCTURE & HOSTING

### 1.1 : SSL/TLS — Certificat HTTPS

**Statut** : ✅ DOIT ÊTRE ACTIF (www.blastclear.com doit être en HTTPS)

| Élément | Action | Priorité | Outil |
|---------|--------|----------|-------|
| **Certificat SSL** | Vérifier : `curl -I https://www.blastclear.com \| grep "SSL"` | 🔴 CRITIQUE | Let's Encrypt / Namecheap |
| **Validity date** | Certificat valide jusqu'à... ? | 🔴 CRITIQUE | Namecheap dashboard |
| **Auto-renewal** | Renouvellement auto activé ? | 🔴 CRITIQUE | Let's Encrypt ou Namecheap |
| **Certificate chain** | Certificat intermédiaire inclus ? | 🟠 HAUTE | SSL Labs (test-ssl.com) |
| **TLS version** | Minimum TLS 1.2 (idéal: TLS 1.3) | 🟠 HAUTE | Vérifier via SSL Labs |
| **Wildcard cert** | Certificat pour *.blastclear.com ? | 🟡 MOYEN | Namecheap |
| **HSTS header** | `Strict-Transport-Security: max-age=31536000` | 🟠 HAUTE | Configuration serveur |

**Action immédiate** :
```bash
# Vérifier l'état SSL
curl -I https://www.blastclear.com | grep -i "ssl\|tls"

# Vérifier validité + expiration
echo | openssl s_client -servername www.blastclear.com -connect www.blastclear.com:443 2>/dev/null | openssl x509 -noout -dates

# Audit complet SSL/TLS
# → Aller sur https://www.ssllabs.com/ssltest/ et scanner www.blastclear.com
```

---

### 1.2 : DNS — Configuration & Sécurité

**Statut** : À vérifier sur Namecheap

| Élément | Action | Priorité | Outil |
|---------|--------|----------|-------|
| **DNS records** | A, AAAA, CNAME correctement pointés ? | 🔴 CRITIQUE | Namecheap DNS |
| **MX records** | Mail routing pour contact@blastclear.com | 🟠 HAUTE | Namecheap ou Zoho |
| **SPF record** | `v=spf1 include:... -all` | 🟠 HAUTE | MXToolBox |
| **DKIM** | Clé DKIM configurée ? | 🟠 HAUTE | Zoho Mail ou Gmail |
| **DMARC** | `v=DMARC1; p=reject; ...` | 🟠 HAUTE | MXToolBox |
| **DNSSEC** | DNSSEC activé ? (protection contre spoofing) | 🟡 MOYEN | Namecheap |
| **CAA record** | `0 issue "letsencrypt.org"` | 🟠 HAUTE | Namecheap DNS |
| **Domain privacy** | WhoisGuard activé ? | 🟡 MOYEN | Namecheap |

**Action immédiate** :
```bash
# Vérifier DNS records
nslookup www.blastclear.com
nslookup -type=MX blastclear.com
nslookup -type=TXT blastclear.com (pour SPF, DKIM, DMARC)

# Vérifier CAA records
nslookup -type=CAA blastclear.com

# Audit SPF/DKIM/DMARC
# → Utiliser https://mxtoolbox.com pour validation complète
```

---

### 1.3 : Web Server Hardening

**Statut** : À vérifier (dépend du hosting actuel)

| Élément | Action | Priorité | Détail |
|---------|--------|----------|--------|
| **Server type** | Quel serveur ? (Nginx, Apache, IIS, Node.js, Next.js?) | 🔴 CRITIQUE | Déterminer d'abord |
| **Version masquée** | Header "Server" caché ? | 🟠 HAUTE | Retirer "Server: Apache/2.4..." |
| **X-Frame-Options** | `X-Frame-Options: DENY` | 🟠 HAUTE | Empêcher clickjacking |
| **X-Content-Type-Options** | `X-Content-Type-Options: nosniff` | 🟠 HAUTE | Empêcher MIME sniffing |
| **X-XSS-Protection** | `X-XSS-Protection: 1; mode=block` | 🟡 MOYEN | Protéger XSS (navigateurs) |
| **CSP header** | Content-Security-Policy stricte | 🔴 CRITIQUE | Voir section CSP ci-dessous |
| **Referrer-Policy** | `Referrer-Policy: strict-origin-when-cross-origin` | 🟡 MOYEN | Limiter info referer |

**Action** : Tester via https://securityheaders.com

```bash
# Vérifier les headers de sécurité
curl -I https://www.blastclear.com | grep -i "x-frame\|x-content\|csp\|hsts"
```

---

### 1.4 : Content Security Policy (CSP)

**Critère** : 🔴 CRITIQUE

Le CSP doit être **très stricte** pour un site SaaS minière (données sensibles).

```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.blastclear.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  upgrade-insecure-requests;
  block-all-mixed-content;
```

**Action** : 
- Configurer dans les headers serveur (Nginx `.conf`, Apache `.htaccess`, ou Next.js `next.config.js`)
- Tester via https://csp-evaluator.withgoogle.com

---

### 1.5 : DDoS Protection & WAF

**Statut** : À évaluer

| Élément | Action | Priorité | Outil |
|---------|--------|----------|-------|
| **Rate limiting** | Limiter requêtes par IP ? | 🟠 HAUTE | Nginx, Cloudflare, ou HAProxy |
| **Bot protection** | Distinguer bots légitimes / malveillants ? | 🟠 HAUTE | Cloudflare, hCaptcha sur formulaires |
| **WAF rules** | OWASP Top 10 activé ? | 🟠 HAUTE | Cloudflare WAF ou AWS WAF |
| **DDoS protection** | Planification prise DDoS ? | 🟡 MOYEN | Cloudflare, AWS Shield, ou Akamai |
| **Backup DNS** | Serveurs DNS secondaires ? | 🟡 MOYEN | Cloudflare ou DNSimple |

**Recommandation** : Utiliser **Cloudflare** en proxy (gratuit) :
- Active WAF OWASP
- Rate limiting natif
- DDoS protection
- Cache automatique
- Analytics trafic

---

### 1.6 : Backup & Disaster Recovery

**Statut** : À mettre en place

| Élément | Action | Fréquence | Rétention |
|---------|--------|-----------|-----------|
| **Backup complet site** | Base de données + fichiers statiques | Quotidien | 30 jours |
| **Backup géographique** | Stockage hors-site (autre région) | Quotidien | 30 jours |
| **Test de restoration** | Vérifier restauration fonctionnelle | Mensuel | N/A |
| **RTO (Recovery Time)** | Objectif : < 4 heures | N/A | Documentation |
| **RPO (Recovery Point)** | Objectif : < 1 heure de perte données | N/A | Documentation |

**Outil recommandé** :
- **AWS Backup** (si hébergé AWS)
- **Azure Backup** (si Azure)
- **Backblaze B2** (cloud généraliste, moins cher)
- **Vercel snapshots** (si Next.js sur Vercel)

---

## 2️⃣ SÉCURITÉ DES DONNÉES

### 2.1 : Formulaires Web — Protection CSRF/XSS

**Statut** : À vérifier sur la page actuelle

| Élément | Action | Priorité | Implémentation |
|---------|--------|----------|-----------------|
| **CSRF tokens** | Token unique par formulaire ? | 🔴 CRITIQUE | `<input type="hidden" name="_csrf" value="TOKEN">` |
| **Input validation** | Valider côté client + serveur ? | 🔴 CRITIQUE | Regex, longueur max, caractères autorisés |
| **XSS escaping** | Échapper sorties HTML ? | 🔴 CRITIQUE | `.textContent`, `.innerText` (pas `.innerHTML`) |
| **Rate limiting** | Limiter soumissions formulaire ? | 🟠 HAUTE | Max 5 soumissions/min/IP |
| **CAPTCHA** | hCaptcha sur formulaire contact ? | 🟠 HAUTE | https://www.hcaptcha.com |
| **Email validation** | Vérifier format email ? | 🟡 MOYEN | Regex + envoi confirmation |

**Action immédiate** :
```html
<!-- Ajouter au formulaire de contact -->
<input type="hidden" name="_csrf" value="GENERATED_TOKEN">
<div class="h-captcha" data-sitekey="YOUR_SITEKEY"></div>
```

---

### 2.2 : Chiffrement des données (en repos)

**Statut** : À évaluer

| Élément | Action | Priorité | Standard |
|---------|--------|----------|----------|
| **Base de données** | Chiffrage AES-256 ? | 🟠 HAUTE | TDE (Transparent Data Encryption) |
| **Fichiers uploadés** | Chiffrer DXF, PDF uploadés ? | 🟠 HAUTE | Chiffrage côté serveur |
| **Backups** | Chiffrer backups stockés ? | 🟠 HAUTE | Clé de chiffrage en HSM |
| **Clés de chiffrage** | Où stocker les clés ? | 🔴 CRITIQUE | AWS KMS, Azure Key Vault, Vault |
| **Rotation clés** | Rotation clés tous les 90 jours ? | 🟠 HAUTE | Automatisée |

**Recommandation** :
- **AWS RDS** : Activer RDS Encryption (AES-256 natif)
- **PostgreSQL** : pgcrypto extension, chiffrer colonnes sensibles
- **Azure** : SQL Database Encryption, Always Encrypted

---

### 2.3 : Chiffrement en transit (HTTPS)

**Statut** : ✅ Couvert par SSL/TLS (section 1.1)

**Mais aussi vérifier** :
- ✅ Pas de requêtes HTTP (tout en HTTPS)
- ✅ Pas d'images/CSS/JS en HTTP dans la page HTTPS (mixed content)
- ✅ Tokens JWT signés (HS256 minimum, RS256 mieux)

```bash
# Vérifier mixed content
curl -s https://www.blastclear.com | grep -i "http://" | grep -v "https://"
```

---

### 2.4 : Gestion des sessions & tokens

**Statut** : À définir

| Élément | Action | Priorité | Détail |
|---------|--------|----------|--------|
| **Session timeout** | Durée max session : 15-30 min inactivité ? | 🟠 HAUTE | Redirigé vers login après timeout |
| **JWT expiration** | Token expire après 15 min ? | 🟠 HAUTE | Refresh token valid 7 jours |
| **Secure cookies** | `HttpOnly`, `Secure`, `SameSite=Strict` ? | 🟠 HAUTE | Empêcher accès JS + CSRF |
| **Token storage** | Tokens en mémoire (pas localStorage) ? | 🔴 CRITIQUE | XSS risk si localStorage |
| **Logout** | Vraiment supprimer session/token ? | 🟠 HAUTE | Blacklist token côté serveur |

**Exemple secure cookie** :
```javascript
// Node.js / Express
res.cookie('authToken', token, {
  httpOnly: true,      // Interdit accès JavaScript
  secure: true,        // HTTPS uniquement
  sameSite: 'Strict',  // CSRF protection
  maxAge: 15 * 60 * 1000  // 15 minutes
});
```

---

## 3️⃣ CONFORMITÉ & AUDIT

### 3.1 : RGPD (GDPR)

**Statut** : ⚠️ OBLIGATOIRE si clients EU

| Élément | Action | Priorité | Détail |
|---------|--------|----------|--------|
| **Privacy Policy** | Page `/privacy` avec mentions RGPD ? | 🔴 CRITIQUE | [Télécharger template](#) |
| **Consent management** | Cookie banner demandant consentement ? | 🔴 CRITIQUE | Outils : OneTrust, Termly, Cookiebot |
| **Data processing agreement (DPA)** | Contrat entre BlastClear et client ? | 🟠 HAUTE | Article 28 RGPD |
| **DPIA (Impact Assessment)** | Analyse impact traitement données ? | 🟠 HAUTE | Pour données minières sensibles |
| **Right to be forgotten** | Permettre suppression données ? | 🟠 HAUTE | API endpoint `/api/users/{id}/delete` |
| **Data portability** | Permettre export données (JSON) ? | 🟠 HAUTE | API endpoint `/api/users/{id}/export` |
| **Breach notification** | Procédure si fuite données ? | 🟠 HAUTE | Notifier CNIL sous 72h |

**Action immédiate** :
- ✅ Créer page Privacy Policy complète
- ✅ Ajouter cookie banner (Cookiebot gratuit)
- ✅ Documenter DPA avec clients

---

### 3.2 : Terms of Service (ToS)

**Statut** : REQUIS

| Élément | Action | Priorité |
|---------|--------|----------|
| **ToS page** | Page `/terms` avec conditions d'utilisation | 🔴 CRITIQUE |
| **Liability disclaimer** | "BlastClear n'est pas responsable si..." | 🔴 CRITIQUE |
| **IP rights** | Droits d'auteur sur le logiciel | 🔴 CRITIQUE |
| **Acceptable use** | Interdire utilisation malveillante | 🟠 HAUTE |
| **Indemnification** | Clause d'indemnisation client | 🟠 HAUTE |

---

### 3.3 : Conformité minière (NI 43-101, JORC, ICOLD)

**Statut** : À clarifier sur site

| Élément | Action | Priorité | Note |
|---------|--------|----------|------|
| **Disclaimer NI 43-101** | BlastClear est un **outil**, pas une source de réserves ? | 🔴 CRITIQUE | Page FAQ ou conditions |
| **Limitation responsabilité** | Responsabilité limitée aux bugs logiciel | 🟠 HAUTE | Contrat licence |
| **Validation méthodologie** | Publication scientifique avant production ? | 🟠 HAUTE | ABEPS methodology |

---

## 4️⃣ MONITORING & INCIDENTS

### 4.1 : Monitoring uptime & performance

**Statut** : À mettre en place

| Élément | Action | Fréquence | Outil |
|---------|--------|-----------|-------|
| **Uptime monitoring** | Vérifier site accessible 24/7 ? | Continu | Pingdom, UptimeRobot, Statuspage.io |
| **Response time** | Page charge en < 3s ? | Continu | Google Lighthouse, GTmetrix |
| **SSL expiration alert** | Alerte 30 jours avant expiration ? | Quotidien | LetEncrypt auto-renew ou Namecheap |
| **Domain expiration alert** | Alerte 60 jours avant renouvellement ? | Quotidien | Namecheap notifications |
| **404 errors** | Tracker pages mortes ? | Quotidien | Google Search Console |
| **Broken links** | Vérifier liens internes ? | Hebdo | Broken Link Checker |

**Outil recommandé** : Créer un **Statuspage** public pour transparence
- https://www.statuspage.io (Atlassian)
- Voir : https://status.blastclear.com (futur)

---

### 4.2 : Error Logging & Alertes

**Statut** : À implémenter

| Élément | Action | Priorité | Outil |
|---------|--------|----------|-------|
| **Error tracking** | Capturer erreurs app (500, 404, etc) ? | 🔴 CRITIQUE | Sentry, Rollbar, New Relic |
| **Log centralization** | Tous logs serveur au même endroit ? | 🟠 HAUTE | ELK (Elasticsearch), Datadog, Splunk |
| **Real-time alerts** | Notifier équipe si erreur critique ? | 🟠 HAUTE | Slack, email, SMS |
| **Audit logs** | Tracer tous changements (admin panel) ? | 🟠 HAUTE | Database audit trail |
| **Access logs** | Qui a accédé à quoi et quand ? | 🟠 HAUTE | Serverware logs |

**Recommendation** : **Sentry** (gratuit jusqu'à 5K erreurs/mois)
```javascript
// Next.js + Sentry
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://YOUR_KEY@sentry.io/PROJECT_ID",
  tracesSampleRate: 1.0,
});
```

---

### 4.3 : Incident Response Plan

**Statut** : À documenter

| Scénario | Étapes | Temps |
|----------|--------|-------|
| **Fuite de données** | 1. Détecter 2. Contenir 3. Notifier CNIL 4. Clients | < 72h |
| **Site down** | 1. Alerte 2. Diagnostic 3. Restauration 4. Postmortem | < 4h |
| **Attaque XSS/SQL injection** | 1. Patch 2. Deploy 3. Audit logs 4. Notifier clients | < 2h |
| **Certificat SSL expiré** | 1. Renouvellement auto (doit pas arriver) 2. Manual renew | < 1h |
| **Attaque brute-force login** | 1. Rate limiting active 2. IP blocée 3. Alert | < 15min |

**Action** : Créer document **Incident Response Plan** (IRP)
- Lister contacts clés (CTO, security, ops)
- Procédures par type incident
- Escalade (qui appeler en cas d'urgence)
- Communication clients (template email)

---

## 5️⃣ DÉVELOPPEMENT SÉCURISÉ

### 5.1 : Code Review & Security Testing

**Statut** : À instaurer

| Élément | Action | Priorité | Fréquence |
|---------|--------|----------|-----------|
| **Code review** | Toute PR revue avant merge ? | 🔴 CRITIQUE | 100% des PRs |
| **SAST** | Scan code source pour vulnérabilités ? | 🟠 HAUTE | À chaque commit |
| **Dependency scan** | Checker npm/pip packages pour vulnérabilités ? | 🟠 HAUTE | À chaque commit |
| **DAST** | Tester app en exécution (pentest) ? | 🟠 HAUTE | Mensuel |
| **Security training** | Équipe formée aux vulnérabilités courantes ? | 🟡 MOYEN | Annuel |

**Outils SAST recommandés** :
- **SonarQube** (gratuit pour open-source)
- **Snyk** (npm, docker, terraform scanning)
- **GitHub Advanced Security** (si GitHub)

---

### 5.2 : Dependency Management

**Statut** : À mettre en place

```bash
# npm
npm audit              # Trouver vulnérabilités
npm audit fix          # Fixer automatiquement

# Configurer auto-updates
# → Ajouter Dependabot (GitHub) ou Snyk
```

---

### 5.3 : Secrets Management

**Statut** : À implémenter (voir section 6)

---

## 6️⃣ GESTION DES SECRETS

### 6.1 : Stockage des secrets

**DANGER CRITIQUE** : Ne JAMAIS committer secrets en Git !

| Secret | Stockage | Accès |
|--------|----------|-------|
| Database password | AWS Secrets Manager / Azure Key Vault | Application seulement |
| API keys (Stripe, etc) | Environment variables (`.env`, secrets GitHub) | Env var, jamais code |
| JWT signing key | HSM ou Key Vault | Serveur seulement |
| OAuth client secret | Secrets Manager | Backend API seulement |
| Private keys (SSL, signing) | HSM ou secure server | Restricted access |

### 6.2 : Environnements

**Stricte séparation** :
- **Development** : Secrets de test (clés Stripe test, etc)
- **Staging** : Secrets vrais mais données de test
- **Production** : Secrets vrais + data réelle (accès strict)

```bash
# ❌ MAUVAIS
export DB_PASSWORD="super-secret-123"  # Ne jamais faire ça

# ✅ BON
# Utiliser AWS Secrets Manager, Azure Key Vault, ou Vault
# Secrets injected at runtime via environment variables
# Jamais stockés en .env commité
```

---

## 7️⃣ CALENDRIER D'IMPLÉMENTATION

### Phase 1 : URGENT (Semaine 1-2)

| # | Tâche | Responsable | Délai |
|---|-------|-------------|-------|
| 1 | Vérifier SSL/TLS valide + auto-renew | DevOps | J+2 |
| 2 | Ajouter security headers (HSTS, CSP, X-Frame-Options) | Dev | J+3 |
| 3 | Vérifier CSRF tokens sur formulaire contact | Dev | J+3 |
| 4 | Ajouter hCaptcha formulaire contact | Dev | J+5 |
| 5 | Créer Privacy Policy + Cookie banner | Legal/PM | J+7 |
| 6 | Créer Terms of Service | Legal/PM | J+7 |

### Phase 2 : HAUTE PRIORITÉ (Semaine 2-4)

| # | Tâche | Responsable | Délai |
|---|-------|-------------|-------|
| 7 | Mettre en place Sentry (error tracking) | Dev | J+10 |
| 8 | Configurer backups quotidiens (AWS Backup ou Backblaze) | DevOps | J+10 |
| 9 | Activer Cloudflare WAF en proxy | DevOps | J+12 |
| 10 | Mettre en place monitoring uptime (UptimeRobot) | DevOps | J+14 |
| 11 | Ajouter DMARC/SPF/DKIM pour email | DevOps | J+14 |
| 12 | Configurer Snyk pour dependency scanning | Dev | J+14 |

### Phase 3 : MOYEN TERME (Mois 1-2)

| # | Tâche | Responsable | Délai |
|---|-------|-------------|-------|
| 13 | Rédiger Incident Response Plan (IRP) | Security/PM | M+30 |
| 14 | Faire audit de sécurité complet (pentest) | Externe | M+45 |
| 15 | Implémenter logging centralisé (ELK ou Datadog) | DevOps | M+30 |
| 16 | Mettre en place RBAC (contrôle accès) | Dev | M+45 |
| 17 | Former équipe aux pratiques sécurité | PM | M+60 |

---

## 📊 DASHBOARD DE SUIVI

### Checklist d'auto-évaluation

Imprimer & remplir chaque mois :

```
[ ] SSL/TLS valide et auto-renew activé
[ ] Tous headers de sécurité présents (via securityheaders.com)
[ ] CSP configuré et sans violations
[ ] CSRF tokens sur tous formulaires
[ ] CAPTCHA actif sur formulaire contact
[ ] Privacy Policy publiée et à jour
[ ] Terms of Service publiés
[ ] Backups quotidiens en place et testés
[ ] Sentry/error tracking actif
[ ] Uptime monitoring < 1h indisponibilité/mois
[ ] Snyk scanning des dépendances
[ ] Pas de vulnérabilités critiques (npm audit)
[ ] Rate limiting actif
[ ] Logs centralisés et consultables
[ ] IRP documenté et connu de l'équipe
[ ] Pentest annuel complété
```

---

## 📞 CONTACTS URGENCE

| Situation | Contact | Temps réponse |
|-----------|---------|---------------|
| **Site down** | DevOps lead + Namecheap support | < 30 min |
| **SSL expiré** | DevOps + Namecheap | < 15 min |
| **Fuite sécurité** | CTO + Sentry + Legal | < 1h |
| **Attaque DDOS** | Cloudflare support + DevOps | < 5 min |
| **Donnée client exposée** | Legal + CNIL | < 2h |

---

## 📚 RESSOURCES UTILES

### Guides & Standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Les 10 vulnérabilités les plus critiques
- [Mozilla Web Security Guide](https://infosec.mozilla.org/guidelines/web_security) — Bonnes pratiques Mozilla
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) — Framework US standard

### Outils
- **SSL/TLS** : [SSL Labs](https://www.ssllabs.com/ssltest/)
- **Security Headers** : [securityheaders.com](https://securityheaders.com)
- **DNS** : [MXToolBox](https://mxtoolbox.com)
- **Uptime** : [UptimeRobot](https://uptimerobot.com)
- **Error Tracking** : [Sentry](https://sentry.io)
- **Dependency Scan** : [Snyk](https://snyk.io)
- **WAF** : [Cloudflare](https://www.cloudflare.com)

### Conformité
- **RGPD** : [Commission Nationale Informatique et Libertés](https://www.cnil.fr/)
- **NI 43-101** : [Canadian Securities Administrators](https://www.osc.ca/)
- **ICOLD** : [International Commission on Large Dams](https://www.icold-cigb.org/)

---

## ✅ SIGN-OFF

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| **CTO/Dev Lead** | ___________ | ___/___/___ | |
| **DevOps/Infrastructure** | ___________ | ___/___/___ | |
| **Product Manager** | ___________ | ___/___/___ | |
| **Legal** | ___________ | ___/___/___ | |

---

**BlastClear v2.2** — Checklist Sécurité Site Web — Septembre 2026

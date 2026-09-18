# Lexique métier du site, treize langues

Ce fichier fixe les deux notions qui portent le titre de la page d'accueil. Il existe
parce qu'elles étaient jusqu'ici dispersées dans trois tables Python — `TITRE_BANDEAU`,
`DEFINITION` et `LEGENDES` de `outils/convertir_design.py` — sans qu'un seul endroit dise
pourquoi tel mot plutôt que tel autre. Un terme qu'on ne peut pas justifier se retraduit
au premier doute.

**Règle d'ensemble, déjà écrite dans le script :** la terminologie est celle du métier
dans chaque langue, jamais une traduction mot à mot du français. C'est ce qui a donné
`Vorspaltsprengung` et non `Vorspalten`, `förspräckning` et non `försprängning`.

---

## 1. La zone bouclée autour du tir

Ce que l'on évacue et interdit avant de faire feu.

| Langue | Terme retenu | Écarté, et pourquoi |
|---|---|---|
| fr | **périmètre d'évacuation** | C'est le terme du logiciel et celui de l'exploitant. Conservé tel quel. |
| en | **safety exclusion zone** | « clearance perimeter » se comprend mais ne se cherche pas : les autorités minières écrivent *blast exclusion zone* ou *safety exclusion zone*. |
| es | **zona de exclusión** | « perímetro de evacuación » décrit l'évacuation, non l'interdiction qui subsiste. |
| pt | **zona de exclusão** | idem. |
| it | **zona di esclusione** | idem. |
| de | **Sperrbereich** | La réglementation SprengTR 310 parle de l'*abzusperrender Sprengbereich*. « Evakuierungsperimeter » est un calque du français. |
| nl | **veiligheidszone** | « evacuatieperimeter » est un calque. |
| sv | **skyddsområde** | « utrymningsperimeter » est un calque. |
| no | **sikringssone** | idem. |
| da | **sikkerhedszone** | idem. |
| af | **veiligheidsone** | idem. |
| tr | **emniyet bölgesi** | « tahliye çevresi » dit l'évacuation seule. |
| zh | **安全警戒范围** | 疏散警戒范围 dit l'évacuation ; 安全 porte la sécurité. |

## 2. La projection de roches

Le fragment qui part au-delà du tir. C'est le phénomène que le dôme balistique modélise,
et c'est le mot qu'un acheteur du domaine reconnaît immédiatement.

| Langue | Terme retenu | Note |
|---|---|---|
| fr | **projections** | Terme des documents d'exploitation. |
| en | **flyrock** | Le mot du métier, universel dans la littérature anglophone. |
| es | **proyección de rocas** | |
| pt | **ultralançamento** | Terme consacré au Brésil et au Portugal. |
| it | **proiezioni** | |
| de | **Steinflug** | Le mot des règles DGUV 113-016 « Sprengarbeiten ». |
| nl | **steenworp** | |
| sv | **stenkast** | |
| no | **steinsprut** | **Ne pas écrire `stenkast`**, qui est le suédois. Les deux textes disent « dit … går » : un remplacement global de l'un atteint l'autre. Le défaut a été commis, puis corrigé. |
| da | **stenkast** | |
| af | **flyrock** | **Emprunt assumé.** La filière sud-africaine travaille en anglais, les normes SANS sont en anglais, et aucun terme afrikaans n'est attesté dans la littérature du métier. En forger un ferait dire au site un mot que personne n'emploie sur le terrain. |
| tr | **taş savrulması** | Terme de la réglementation minière turque et des guides d'étude d'impact. |
| zh | **飞石** | |

---

## Où ces termes vivent dans le code

| Table | Fichier | Ce qu'elle porte |
|---|---|---|
| `TITRE_BANDEAU` | `outils/convertir_design.py` | les trois lignes du grand titre, versées dans `CORRECTIONS` |
| `CORRECTIONS` | idem | les arbitrages de vocabulaire, appliqués au corps de page |
| `DEFINITION` | idem | le bloc « Ce que fait BlastClear » |
| `LEGENDES` | idem | les légendes des illustrations |
| `POURQUOI` | `outils/pourquoi.py` | la page « Pourquoi BlastClear » |

**Rien ne s'édite dans `site/`** : `convertir_design.py` réécrit les 52 pages à chaque
exécution. Et rien ne s'édite dans `design/` non plus pour ces termes-là : un nouvel
export depuis Claude Design écraserait la retouche. Les corrections vivent dans le script,
qui imprime une `ATTENTION` dès qu'une cible ne se trouve plus.

## Sources

- Blast-exclusion zones, Resources Safety & Health Queensland —
  <https://www.rshq.qld.gov.au/safety-and-health-alerts/mines/blast-exclusion-zones>
- Flyrock, définition et accidentologie —
  <https://en.wikipedia.org/wiki/Flyrock>
- DGUV Regel 113-016 « Sprengarbeiten », pour `Steinflug` et `Sprengbereich` —
  <https://www.uv-bund-bahn.de/fileadmin/user_upload/113-016.pdf>
- Patlatma tasarımları ve patlatma kaynaklı çevresel etkiler kılavuzu, ministère turc de
  l'Environnement, pour `taş savrulması` —
  <https://webdosya.csb.gov.tr/db/ced/icerikler/patlatma-tasarimlari-ve-patlatma-kaynakli-cevresel-etkiler-kilavuzu-20180319120154.pdf>

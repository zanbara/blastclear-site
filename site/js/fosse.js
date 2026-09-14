/* ════════════════════════════════════════════════════════════════════════════
   LA FOSSE ET SON DÔME, EN WEBGL.

   Chargé à la demande par design.js, lorsque la section approche de l'écran.

   ─── CE QUE LE FICHIER DE GÉOMÉTRIE CONTIENT ──────────────────────────────
   Des entiers courts, non des flottants. Les positions sont quantifiées sur
   seize bits dans un cube commun aux deux calques, et la carte graphique les
   ramène elle-même dans [0,1] : c'est le rôle du drapeau « normalisé » passé à
   vertexAttribPointer. Le nuanceur n'a plus qu'à les recentrer.

   Deux octets par coordonnée au lieu de quatre, pour un pas de 2,4 cm sur une
   emprise de 1 545 m. Aucun œil ne mesure ce décor à cette échelle.
   ════════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var hote = document.querySelector('[data-fosse]');
  if (!hote) return;

  var BASE = hote.getAttribute('data-fosse');   // « ../assets/fosse/ »

  /* ══ ALGÈBRE ══════════════════════════════════════════════════════════════
     Quatre fonctions suffisent. Les matrices sont en colonne d'abord, comme
     WebGL les attend, ce qui évite de les transposer à chaque envoi. */

  function perspective(fovy, rapport, pres, loin) {
    var f = 1 / Math.tan(fovy / 2), d = pres - loin;
    return new Float32Array([
      f / rapport, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (loin + pres) / d, -1,
      0, 0, 2 * loin * pres / d, 0,
    ]);
  }

  function regard(oeil, cible, haut) {
    var z = normer([oeil[0] - cible[0], oeil[1] - cible[1], oeil[2] - cible[2]]);
    var x = normer(produit(haut, z));
    var y = produit(z, x);
    return new Float32Array([
      x[0], y[0], z[0], 0,
      x[1], y[1], z[1], 0,
      x[2], y[2], z[2], 0,
      -(x[0] * oeil[0] + x[1] * oeil[1] + x[2] * oeil[2]),
      -(y[0] * oeil[0] + y[1] * oeil[1] + y[2] * oeil[2]),
      -(z[0] * oeil[0] + z[1] * oeil[1] + z[2] * oeil[2]), 1,
    ]);
  }

  function produit(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  }
  function normer(v) {
    var n = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / n, v[1] / n, v[2] / n];
  }
  function multiplier(a, b) {          // a * b, colonne d'abord
    var r = new Float32Array(16);
    for (var c = 0; c < 4; c++) {
      for (var l = 0; l < 4; l++) {
        r[c * 4 + l] = a[l] * b[c * 4] + a[4 + l] * b[c * 4 + 1] +
                       a[8 + l] * b[c * 4 + 2] + a[12 + l] * b[c * 4 + 3];
      }
    }
    return r;
  }

  /* ══ NUANCEURS ════════════════════════════════════════════════════════════
     Un seul programme sert aux deux maillages. u_uni bascule entre la surface
     éclairée et le trait de couleur unie : deux programmes pour cette
     différence coûteraient deux compilations et un changement d'état par image. */

  var SOMMETS = [
    'attribute vec3 a_pos;',
    'attribute vec3 a_nor;',
    'uniform mat4 u_mvp;',
    'varying vec3 v_nor;',
    'void main() {',
    /* La carte a rendu [0,1] ; le cube de la scène va de -1 à 1. */
    '  gl_Position = u_mvp * vec4(a_pos * 2.0 - 1.0, 1.0);',
    '  v_nor = a_nor;',
    '}',
  ].join('\n');

  var FRAGMENTS = [
    'precision mediump float;',
    'varying vec3 v_nor;',
    'uniform vec3 u_couleur;',
    'uniform float u_opacite;',
    'uniform float u_uni;',
    'void main() {',
    '  if (u_uni > 0.5) { gl_FragColor = vec4(u_couleur, u_opacite); return; }',
    /* Une seule source, haute et de trois quarts, comme un éclairage de maquette.
       Le terme ambiant empêche les faces opposées de tomber au noir : une
       banquette dans l'ombre doit rester lisible. */
    '  vec3 n = normalize(v_nor);',
    '  float l = 0.42 + 0.58 * max(dot(n, normalize(vec3(0.45, 0.82, 0.36))), 0.0);',
    '  gl_FragColor = vec4(u_couleur * l, u_opacite);',
    '}',
  ].join('\n');

  function compiler(gl, type, source) {
    var s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  }

  /* ══ NORMALES ═════════════════════════════════════════════════════════════
     Elles sont calculées ICI, et non transportées : trois flottants par sommet
     pèseraient plus lourd que la position quantifiée qu'ils accompagnent, pour
     une donnée que le navigateur retrouve en quelques millisecondes.

     Elles sont MOYENNÉES aux sommets partagés, et pondérées par l'aire de
     chaque face puisque le produit vectoriel n'est pas normé avant l'addition.
     Une grande facette pèse ainsi plus qu'une petite, ce qui adoucit les
     raccords sans effacer les arêtes de banquette. */
  function normales(positions, triangles) {
    var n = new Float32Array(positions.length);
    for (var i = 0; i < triangles.length; i += 3) {
      var a = triangles[i] * 3, b = triangles[i + 1] * 3, c = triangles[i + 2] * 3;
      var ux = positions[b] - positions[a], uy = positions[b + 1] - positions[a + 1],
          uz = positions[b + 2] - positions[a + 2];
      var vx = positions[c] - positions[a], vy = positions[c + 1] - positions[a + 1],
          vz = positions[c + 2] - positions[a + 2];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      n[a] += nx; n[a + 1] += ny; n[a + 2] += nz;
      n[b] += nx; n[b + 1] += ny; n[b + 2] += nz;
      n[c] += nx; n[c + 1] += ny; n[c + 2] += nz;
    }
    for (var j = 0; j < n.length; j += 3) {
      var m = Math.hypot(n[j], n[j + 1], n[j + 2]) || 1;
      n[j] /= m; n[j + 1] /= m; n[j + 2] /= m;
    }
    return n;
  }

  /* ══ CHARGEMENT ═══════════════════════════════════════════════════════════ */

  function binaire(nom) {
    return fetch(BASE + nom).then(function (r) {
      if (!r.ok) throw new Error(nom);
      return r.arrayBuffer();
    });
  }

  /* Un calque porte UNE table de positions et un ou deux jeux d'indices qui la
     partagent : la fosse est dessinée deux fois, en surface puis en fil de fer,
     sur les mêmes sommets. Les transporter deux fois doublerait le fichier pour
     rien. */
  fetch(BASE + 'fosse.json')
    .then(function (r) { return r.json(); })
    .then(function (manifeste) {
      var calques = manifeste.calques;
      return Promise.all(Object.keys(calques).map(function (nom) {
        var c = calques[nom];
        return Promise.all(
          [binaire(c.position)].concat(c.jeux.map(function (j) { return binaire(j.index); }))
        ).then(function (tampons) {
          return {
            nom: nom,
            positions: new Uint16Array(tampons[0]),
            jeux: c.jeux.map(function (j, i) {
              return { forme: j.forme, indices: new Uint16Array(tampons[i + 1]) };
            }),
          };
        });
      })).then(function (lots) {
        return { boite: manifeste.boite, lots: lots };
      });
    })
    /* Le second argument de then, et non un catch en bout de chaîne : il ne
       rattrape que les échecs du CHARGEMENT, réseau coupé ou fichier absent, où
       se taire est la bonne conduite puisque la section se tient sans son
       dessin. Un catch final avalerait aussi les fautes de demarrer, et une
       faute de programmation avalée ne se corrige jamais. */
    .then(demarrer, function () { /* la section garde son texte */ });

  /* ══ LA SCÈNE ═════════════════════════════════════════════════════════════ */

  function demarrer(scene) {
    var lots = scene.lots;
    var boite = scene.boite || { min: [-1, -1, -1], max: [1, 1, 1] };

    var toile = document.createElement('canvas');
    toile.className = 'dc-fosse-toile';
    toile.setAttribute('aria-hidden', 'true');

    var options = { alpha: true, antialias: true, depth: true,
                    premultipliedAlpha: false, powerPreference: 'low-power' };
    var gl = toile.getContext('webgl', options) || toile.getContext('experimental-webgl', options);
    if (!gl) return;                      /* pas de WebGL : rien ne s'affiche */

    var prog = gl.createProgram();
    var vs = compiler(gl, gl.VERTEX_SHADER, SOMMETS);
    var fs = compiler(gl, gl.FRAGMENT_SHADER, FRAGMENTS);
    if (!vs || !fs) return;
    gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);

    var aPos = gl.getAttribLocation(prog, 'a_pos');
    var aNor = gl.getAttribLocation(prog, 'a_nor');
    var uMvp = gl.getUniformLocation(prog, 'u_mvp');
    var uCouleur = gl.getUniformLocation(prog, 'u_couleur');
    var uOpacite = gl.getUniformLocation(prog, 'u_opacite');
    var uUni = gl.getUniformLocation(prog, 'u_uni');

    /* Les couleurs de la charte, en composantes de 0 à 1. */
    var BLEU = [0x25 / 255, 0x49 / 255, 0x8A / 255];
    var JAUNE = [0xFD / 255, 0xC3 / 255, 0x0E / 255];

    /* ── L'ORDRE DE TRACÉ EST CELUI DE CETTE LISTE ────────────────────────
       Les surfaces d'abord, qui écrivent la profondeur ; les fils de fer
       ensuite, qui ne l'écrivent pas. L'inverse laisserait le trait de la
       fosse repeint par sa propre surface. */
    var objets = [];
    lots.forEach(function (lot) {
      var position = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, position);
      gl.bufferData(gl.ARRAY_BUFFER, lot.positions, gl.STATIC_DRAW);

      var normale = null;
      var surface = lot.jeux.filter(function (j) { return j.forme === 'triangles'; })[0];
      if (surface) {
        /* Le calcul des normales se fait dans l'espace réel, donc sur les
           positions ramenées de [0,65535] à [-1,1]. */
        var reelles = new Float32Array(lot.positions.length);
        for (var i = 0; i < lot.positions.length; i++) {
          reelles[i] = lot.positions[i] / 32767.5 - 1;
        }
        normale = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, normale);
        gl.bufferData(gl.ARRAY_BUFFER, normales(reelles, surface.indices), gl.STATIC_DRAW);
      }

      lot.jeux.forEach(function (jeu) {
        var index = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, jeu.indices, gl.STATIC_DRAW);
        objets.push({
          calque: lot.nom, forme: jeu.forme, nombre: jeu.indices.length,
          position: position, normale: normale, index: index,
        });
      });
    });
    objets.sort(function (a, b) {
      return (a.forme === 'triangles' ? 0 : 1) - (b.forme === 'triangles' ? 0 : 1);
    });

    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    /* ── LE TRAIT ET SA SURFACE SONT À LA MÊME PROFONDEUR ─────────────────
       Les arêtes de la fosse sont tracées sur les sommets mêmes de sa surface :
       elles occupent donc exactement la même profondeur, et le test de
       profondeur en retient tantôt l'une tantôt l'autre selon les arrondis du
       calcul. Le trait se met alors à clignoter par morceaux quand la scène
       tourne.

       Repousser la surface d'un cheveu, et elle seule, lève l'égalité : le
       trait passe toujours devant, sans qu'aucune géométrie ne bouge. */
    gl.enable(gl.POLYGON_OFFSET_FILL);
    gl.polygonOffset(1.2, 1.2);

    /* ── ÉTAT DE LA CAMÉRA ────────────────────────────────────────────────
       L'azimut tourne, l'élévation est bornée : passer au-dessus du zénith
       retournerait la scène, ce qui désoriente sans rien montrer de plus.

       LE RECUL N'EST PAS UN NOMBRE FIXE. La section est large et basse, la vue
       plein écran presque carrée : un même recul y donnerait un dessin qui
       remplit l'une et se perd dans l'autre. Il est donc CALCULÉ à chaque image
       pour que le modèle tienne dans le cadre, et « zoom » n'en est qu'un
       facteur, celui que la molette fait varier. */
    var FOV = 0.72;
    var azimut = -0.7, elevation = 0.52, zoom = 1;
    var plein = null, image = 0;

    /* ── LA CAMÉRA VISE LE CENTRE DE LA BOÎTE, NON L'ORIGINE ─────────────
       L'origine est le fond de la fosse, posé là par la conversion pour que le
       terrain repose sur le plan zéro. Tourner autour d'elle ferait basculer le
       modèle de haut en bas à chaque tour, comme une balançoire.

       Les coins sont donc exprimés RELATIVEMENT à ce centre : c'est ce qui rend
       le calcul du recul exact, puisque la caméra y regarde. */
    var CENTRE = [(boite.min[0] + boite.max[0]) / 2,
                  (boite.min[1] + boite.max[1]) / 2,
                  (boite.min[2] + boite.max[2]) / 2];
    var COINS = [];
    for (var bx = 0; bx < 2; bx++) {
      for (var by = 0; by < 2; by++) {
        for (var bz = 0; bz < 2; bz++) {
          COINS.push([(bx ? boite.max[0] : boite.min[0]) - CENTRE[0],
                      (by ? boite.max[1] : boite.min[1]) - CENTRE[1],
                      (bz ? boite.max[2] : boite.min[2]) - CENTRE[2]]);
        }
      }
    }

    /* ── LE RECUL EXACT, ET NON UNE SPHÈRE ENGLOBANTE ─────────────────────
       Le modèle est un disque très aplati : sa sphère englobante déborde de
       toutes parts au-dessus et au-dessous du vide, et l'ajuster reculerait la
       caméra de moitié pour cadrer de l'air.

       On projette donc les huit coins de sa VRAIE boîte. Chaque coin impose un
       recul minimal : à la distance d, sa profondeur vue vaut d moins sa
       composante le long de l'axe de visée, et il tient dans le cadre si son
       écart latéral ne dépasse pas cette profondeur multipliée par la tangente
       du demi-angle. Le plus exigeant des huit fixe le recul. */
    function recul(rapport) {
      var tH = Math.tan(FOV / 2) * rapport, tV = Math.tan(FOV / 2);
      var ce = Math.cos(elevation), se = Math.sin(elevation);
      var ca = Math.cos(azimut), sa = Math.sin(azimut);
      /* Les trois axes de la caméra, pour un œil placé en coordonnées
         sphériques et visant l'origine. */
      var droite = [ca, 0, -sa];
      var haut = [-se * sa, ce, -se * ca];
      var avant = [ce * sa, se, ce * ca];   /* de l'origine vers l'œil */

      var d = 0;
      for (var i = 0; i < COINS.length; i++) {
        var p = COINS[i];
        var x = Math.abs(p[0] * droite[0] + p[1] * droite[1] + p[2] * droite[2]);
        var y = Math.abs(p[0] * haut[0] + p[1] * haut[1] + p[2] * haut[2]);
        var z = p[0] * avant[0] + p[1] * avant[1] + p[2] * avant[2];
        d = Math.max(d, z + x / tH, z + y / tV);
      }
      /* ── LE FILIGRANE A LE DROIT DE DÉBORDER, PAS LA VUE PLEIN ÉCRAN ───
         Le modèle est plat : cadré en entier, il laisse au-dessus et en dessous
         deux bandes de vide qui font paraître le dessin minuscule au milieu de
         sa section. En le rapprochant d'un tiers, ce sont ces bandes qui sont
         rognées, et le filigrane occupe enfin la place qui lui est donnée.

         Au premier plan, où le visiteur oriente le modèle lui-même, la marge
         reste franche : il y examine une géométrie, et rien ne doit sortir du
         cadre sous ses doigts. */
      return d * 1.10 * (plein ? 0.86 : 0.66) * zoom;
    }

    var sobre = window.matchMedia &&
                window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function dimensionner() {
      var r = Math.min(window.devicePixelRatio || 1, 2);
      var l = Math.max(1, Math.round(toile.clientWidth * r));
      var h = Math.max(1, Math.round(toile.clientHeight * r));
      if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
    }

    function dessiner() {
      dimensionner();
      gl.viewport(0, 0, toile.width, toile.height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      var rapport = toile.width / toile.height;
      var d = recul(rapport);
      var oeil = [
        CENTRE[0] + d * Math.cos(elevation) * Math.sin(azimut),
        CENTRE[1] + d * Math.sin(elevation),
        CENTRE[2] + d * Math.cos(elevation) * Math.cos(azimut),
      ];
      var mvp = multiplier(perspective(FOV, rapport, 0.02, 40),
                           regard(oeil, CENTRE, [0, 1, 0]));

      /* ── EN FILIGRANE, LE DESSIN SE RANGE À DROITE ────────────────────
         Le texte occupe la gauche de la section. Centré, le dessin passerait
         dessous et gênerait la lecture sans rien gagner ; décalé, les deux
         cohabitent et la page garde son sens de lecture.

         Le décalage se fait dans l'espace de découpe, après projection : on
         ajoute au X une fraction du W, ce qui déplace l'image à l'écran sans
         déformer la perspective ni bouger la caméra. Seuls les écrans larges
         y ont droit ; sur un téléphone, le texte occupe toute la largeur. */
      var decalage = (!plein && rapport > 1.7) ? 0.34 : 0;
      if (decalage) {
        for (var c = 0; c < 4; c++) mvp[c * 4] += decalage * mvp[c * 4 + 3];
      }
      gl.uniformMatrix4fv(uMvp, false, mvp);

      objets.forEach(function (o) {
        var triangles = o.forme === 'triangles';
        gl.bindBuffer(gl.ARRAY_BUFFER, o.position);
        gl.enableVertexAttribArray(aPos);
        /* « normalisé » : la carte ramène elle-même l'entier court dans [0,1]. */
        gl.vertexAttribPointer(aPos, 3, gl.UNSIGNED_SHORT, true, 0, 0);

        if (triangles) {
          gl.bindBuffer(gl.ARRAY_BUFFER, o.normale);
          gl.enableVertexAttribArray(aNor);
          gl.vertexAttribPointer(aNor, 3, gl.FLOAT, false, 0, 0);
        } else {
          gl.disableVertexAttribArray(aNor);
          gl.vertexAttrib3f(aNor, 0, 1, 0);
        }

        /* ── LE JAUNE NE PARAÎT QUE SUR FOND SOMBRE ─────────────────────
           En filigrane, le fond de la section est clair, et le jaune de la
           charte y tombe à 1,6:1 : le dôme s'y effacerait entièrement. Tout y
           est donc dans le bleu, distingué par la densité du tracé et non par
           la teinte. Au premier plan, sur fond anthracite, le jaune retrouve
           le contraste qui lui manquait, et avec lui la lecture qu'en donne
           le logiciel : le terrain en bleu, le dôme en jaune. */
        var dome = o.calque === 'dome';
        gl.uniform3fv(uCouleur, plein && dome ? JAUNE : BLEU);
        gl.uniform1f(uUni, triangles ? 0 : 1);

        /* Quatre tracés se superposent, et chacun a sa raison d'être plus ou
           moins présent. La surface de la fosse ne sert qu'à masquer ce qui
           passe dessous : elle reste la plus effacée. Ses arêtes portent les
           banquettes, donc la lecture du relief. Le dôme, lui, est le sujet. */
        var opacite;
        if (plein) opacite = triangles ? 1 : (dome ? 0.85 : 0.5);
        else opacite = triangles ? 0.30 : (dome ? 0.42 : 0.22);

        /* ── SUR ÉCRAN ÉTROIT, LE FILIGRANE S'EFFACE ENCORE ─────────────
           Sur écran large, le dessin est rangé à droite et le texte occupe la
           gauche : les deux ne se rencontrent pas. Sur téléphone, le texte
           tient toute la largeur et le dessin passe forcément dessous. Il
           s'atténue donc d'un tiers, parce qu'entre un décor et un texte qui
           se lit, c'est le décor qui cède. */
        if (!plein && !decalage) opacite *= 0.62;
        gl.uniform1f(uOpacite, opacite);

        /* Le dôme n'écrit pas dans le tampon de profondeur : ses arêtes
           lointaines masqueraient les proches, et un fil de fer transparent
           doit se voir de part en part. */
        gl.depthMask(triangles);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, o.index);
        gl.drawElements(triangles ? gl.TRIANGLES : gl.LINES, o.nombre,
                        gl.UNSIGNED_SHORT, 0);
      });
      gl.depthMask(true);
    }

    function boucle() {
      image = 0;
      if (!saisie && !(sobre && !plein)) azimut += plein ? 0.0009 : 0.0016;
      dessiner();
      if (visible || plein) image = requestAnimationFrame(boucle);
    }
    function relancer() { if (!image) image = requestAnimationFrame(boucle); }

    /* ── LE RENDU S'ARRÊTE HORS DE L'ÉCRAN ───────────────────────────────
       Une boucle d'animation qui tourne sous un contenu qu'on ne regarde pas
       consomme la batterie sans que rien ne le montre. */
    var visible = false;
    hote.appendChild(toile);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entrees) {
        visible = entrees[0].isIntersecting;
        toile.classList.toggle('dc-vue', visible);
        if (visible) relancer();
      }, { rootMargin: '120px' }).observe(hote);
    } else {
      visible = true;
      toile.classList.add('dc-vue');
      relancer();
    }
    window.addEventListener('resize', relancer, { passive: true });

    /* ══ L'ORIENTATION À LA MAIN ═══════════════════════════════════════════
       Elle n'est branchée qu'au premier plan. En filigrane, la toile ne reçoit
       aucun événement : c'est la règle qui garde la page défilable au doigt. */
    var saisie = null, pince = 0;

    function point(e) {
      return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY }
                       : { x: e.clientX, y: e.clientY };
    }
    function ecart(e) {
      var a = e.touches[0], b = e.touches[1];
      return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    }

    function prise(e) {
      if (e.touches && e.touches.length === 2) { pince = ecart(e); saisie = null; return; }
      saisie = point(e);
    }
    function glisse(e) {
      if (e.touches && e.touches.length === 2 && pince) {
        var d = ecart(e);
        zoom = Math.max(0.55, Math.min(2.6, zoom * pince / d));
        pince = d;
        e.preventDefault();
        relancer();
        return;
      }
      if (!saisie) return;
      var p = point(e);
      azimut -= (p.x - saisie.x) * 0.006;
      elevation = Math.max(-0.25, Math.min(1.35, elevation + (p.y - saisie.y) * 0.005));
      saisie = p;
      e.preventDefault();
      relancer();
    }
    function lache() { saisie = null; pince = 0; }

    function brancher(actif) {
      var m = actif ? 'addEventListener' : 'removeEventListener';
      toile[m]('pointerdown', prise);
      toile[m]('pointermove', glisse);
      toile[m]('touchstart', prise, { passive: false });
      toile[m]('touchmove', glisse, { passive: false });
      window[m]('pointerup', lache);
      window[m]('touchend', lache);
      toile[m]('wheel', molette, { passive: false });
    }
    function molette(e) {
      zoom = Math.max(0.55, Math.min(2.6, zoom * (e.deltaY > 0 ? 1.1 : 0.91)));
      e.preventDefault();
      relancer();
    }

    /* ══ OUVRIR ET REFERMER ════════════════════════════════════════════════ */

    var bouton = hote.querySelector('.dc-fosse-ouvrir');
    if (!bouton) return;
    bouton.hidden = false;

    function ouvrir() {
      plein = document.createElement('div');
      plein.className = 'dc-fosse-plein';
      plein.setAttribute('role', 'dialog');
      plein.setAttribute('aria-modal', 'true');
      plein.setAttribute('aria-label', bouton.textContent);

      var fermer = document.createElement('button');
      fermer.type = 'button';
      fermer.className = 'dc-fosse-fermer';
      fermer.textContent = bouton.getAttribute('data-fermer') || 'Close';
      fermer.addEventListener('click', refermer);

      var aide = document.createElement('p');
      aide.className = 'dc-fosse-aide';
      aide.textContent = bouton.getAttribute('data-aide') || '';

      plein.appendChild(toile);
      plein.appendChild(fermer);
      plein.appendChild(aide);
      document.body.appendChild(plein);
      /* La page ne doit pas défiler derrière la vue : sur téléphone, un
         glissement qui déborde de la toile ferait remonter le contenu. */
      document.body.style.overflow = 'hidden';
      brancher(true);
      document.addEventListener('keydown', clavier);
      fermer.focus();
      relancer();
    }

    function refermer() {
      if (!plein) return;
      brancher(false);
      document.removeEventListener('keydown', clavier);
      hote.appendChild(toile);
      plein.remove();
      plein = null;
      document.body.style.overflow = '';
      bouton.focus();
      relancer();
    }

    function clavier(e) { if (e.key === 'Escape') refermer(); }

    bouton.addEventListener('click', ouvrir);
  }
})();

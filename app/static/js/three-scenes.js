(function () {
  "use strict";

  var PRICE_MODEL  = "/static/models/price_building.glb";
  var ENERGY_MODEL = "/static/models/energy_building.glb";

  // Helpers

  // Center + scale model
  function fitModel(gltfScene, targetSize) {
    gltfScene.updateMatrixWorld(true);
    var box  = new THREE.Box3().setFromObject(gltfScene);
    var size = box.getSize(new THREE.Vector3()).length();
    if (size > 0) gltfScene.scale.setScalar(targetSize / size);

    gltfScene.updateMatrixWorld(true);
    var center = new THREE.Box3().setFromObject(gltfScene).getCenter(new THREE.Vector3());
    gltfScene.position.sub(center);
  }

  // Fix transparent materials
  function fixMaterials(gltfScene) {
    gltfScene.traverse(function (child) {
      if (!child.isMesh) return;
      var mats = Array.isArray(child.material) ? child.material : [child.material];
      mats.forEach(function (mat) {
        mat.transparent = false;
        mat.opacity = 1.0;
        mat.depthWrite = true;
      });
    });
  }

  // Mouse/touch controls
  function addModelControls(canvas, group, camera, autoRot) {
    var dragging = false;
    var prevX = 0, prevY = 0;

    canvas.style.cursor = "grab";

    function start(x, y) {
      dragging = true;
      prevX = x; prevY = y;
      canvas.style.cursor = "grabbing";
      autoRot.active = false;
    }
    function move(x, y) {
      if (!dragging) return;
      group.rotation.y += (x - prevX) * 0.012;
      group.rotation.x += (y - prevY) * 0.012;
      prevX = x; prevY = y;
    }
    function end() {
      dragging = false;
      canvas.style.cursor = "grab";
      autoRot.active = true;
    }

    canvas.addEventListener("mousedown",  function (e) { start(e.clientX, e.clientY); });
    window.addEventListener("mousemove",  function (e) { move(e.clientX, e.clientY); });
    window.addEventListener("mouseup",    end);

    canvas.addEventListener("touchstart", function (e) {
      e.preventDefault();
      start(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: false });
    canvas.addEventListener("touchmove",  function (e) {
      e.preventDefault();
      move(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: false });
    canvas.addEventListener("touchend", end);

    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      camera.position.multiplyScalar(1 + e.deltaY * 0.001);
      var d = camera.position.length();
      if (d < 1.0) camera.position.setLength(1.0);
      if (d > 20)  camera.position.setLength(20);
    }, { passive: false });
  }

  // Hero particles

  var _heroRenderer = null;
  var _heroRAF      = null;

  function initHeroScene(canvasId) {
    if (typeof THREE === "undefined") return;
    if (_heroRenderer) { _heroRenderer.dispose(); cancelAnimationFrame(_heroRAF); }

    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var hero = canvas.parentElement;
    var W = hero ? hero.offsetWidth  : window.innerWidth;
    var H = hero ? hero.offsetHeight : 120;
    if (!W || !H) return;

    _heroRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: false });
    _heroRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    _heroRenderer.setSize(W, H, false);

    var scene  = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 100);
    camera.position.z = 4;

    var COUNT = 75;
    var pos   = new Float32Array(COUNT * 3);
    var vel   = new Float32Array(COUNT * 2);

    for (var i = 0; i < COUNT; i++) {
      pos[i * 3]     = (Math.random() - 0.5) * 14;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 4.5;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 1.5;
      vel[i * 2]     = (Math.random() - 0.5) * 0.006;
      vel[i * 2 + 1] = (Math.random() - 0.5) * 0.005;
    }

    var ptGeom = new THREE.BufferGeometry();
    ptGeom.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    scene.add(new THREE.Points(
      ptGeom,
      new THREE.PointsMaterial({ color: 0x5a9cd4, size: 0.07, transparent: true, opacity: 0.9 })
    ));

    var THRESH    = 1.9;
    var lineArr   = new Float32Array(COUNT * COUNT * 6);
    var lineGeom  = new THREE.BufferGeometry();
    lineGeom.setAttribute("position", new THREE.BufferAttribute(lineArr, 3));
    scene.add(new THREE.LineSegments(
      lineGeom,
      new THREE.LineBasicMaterial({ color: 0x6aaad0, transparent: true, opacity: 0.22 })
    ));

    function tick() {
      _heroRAF = requestAnimationFrame(tick);
      for (var k = 0; k < COUNT; k++) {
        pos[k * 3]     += vel[k * 2];
        pos[k * 3 + 1] += vel[k * 2 + 1];
        if (Math.abs(pos[k * 3])     > 7.2) vel[k * 2]     *= -1;
        if (Math.abs(pos[k * 3 + 1]) > 2.4) vel[k * 2 + 1] *= -1;
      }
      ptGeom.attributes.position.needsUpdate = true;

      var li = 0;
      for (var a = 0; a < COUNT; a++) {
        for (var b = a + 1; b < COUNT; b++) {
          var dx = pos[a * 3] - pos[b * 3];
          var dy = pos[a * 3 + 1] - pos[b * 3 + 1];
          if (dx * dx + dy * dy < THRESH * THRESH) {
            lineArr[li++] = pos[a*3];     lineArr[li++] = pos[a*3+1]; lineArr[li++] = pos[a*3+2];
            lineArr[li++] = pos[b*3];     lineArr[li++] = pos[b*3+1]; lineArr[li++] = pos[b*3+2];
          }
        }
      }
      lineGeom.setDrawRange(0, li / 3);
      lineGeom.attributes.position.needsUpdate = true;
      _heroRenderer.render(scene, camera);
    }

    window.addEventListener("resize", function () {
      var w = hero ? hero.offsetWidth  : window.innerWidth;
      var h = hero ? hero.offsetHeight : 120;
      if (!w || !h) return;
      _heroRenderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    });

    tick();
  }

  // Price model

  var _priceRenderer = null;
  var _priceRAF      = null;

  function initPriceScene(canvasId) {
    if (typeof THREE === "undefined") return;
    if (_priceRenderer) { _priceRenderer.dispose(); cancelAnimationFrame(_priceRAF); }

    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var SIZE = canvas.offsetWidth || 120;
    _priceRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    _priceRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    _priceRenderer.setSize(SIZE, SIZE, false);
    _priceRenderer.outputColorSpace = THREE.SRGBColorSpace;
    _priceRenderer.toneMapping      = THREE.ACESFilmicToneMapping;
    _priceRenderer.toneMappingExposure = 1.0;   

    var scene  = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(2.4, 1.9, 3.2);
    camera.lookAt(0, 0.25, 0);

    // Lights
    scene.add(new THREE.HemisphereLight(0xddeeff, 0x442200, 0.6)); 
    var sun = new THREE.DirectionalLight(0xfff5e0, 2.0);  
    sun.position.set(3, 5, 4);
    scene.add(sun);
    var fill = new THREE.DirectionalLight(0xffffff, 0.15); 
    fill.position.set(-3, 1, -4);
    scene.add(fill);

    var group   = new THREE.Group();
    var autoRot = { active: true };
    scene.add(group);
    addModelControls(canvas, group, camera, autoRot);

    // Fallback shape
    function addFallback() {
      var mMain = new THREE.LineBasicMaterial({ color: 0x000080, transparent: true, opacity: 0.90 });
      var mAcc  = new THREE.LineBasicMaterial({ color: 0x1b6ac9, transparent: true, opacity: 0.75 });
      var body  = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1.55, 1)), mMain);
      body.position.y = 0.275;
      group.add(body);
      var roof  = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.ConeGeometry(0.82, 0.55, 4)), mAcc);
      roof.position.y = 1.35;
      roof.rotation.y = Math.PI / 4;
      group.add(roof);
      var chim  = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.13, 0.27, 0.13)), mAcc);
      chim.position.set(0.24, 1.76, 0.18);
      group.add(chim);
    }

    addFallback();

    // Load GLB
    if (typeof THREE.GLTFLoader !== "undefined") {
      new THREE.GLTFLoader().load(
        PRICE_MODEL,
        function (gltf) {
          fixMaterials(gltf.scene);
          fitModel(gltf.scene, 2.5);
          while (group.children.length) group.remove(group.children[0]);
          group.add(gltf.scene);
        },
        undefined,
        function () { /* Keep fallback */ }
      );
    }

    function tick() {
      _priceRAF = requestAnimationFrame(tick);
      if (autoRot.active) group.rotation.y += 0.011;
      _priceRenderer.render(scene, camera);
    }
    tick();
  }

  // Energy model

  var _energyRenderer = null;
  var _energyRAF      = null;

  function initEnergyScene(canvasId, totalLoad) {
    if (typeof THREE === "undefined") return;
    if (_energyRenderer) { _energyRenderer.dispose(); cancelAnimationFrame(_energyRAF); }

    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var SIZE = canvas.offsetWidth || 120;
    _energyRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    _energyRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    _energyRenderer.setSize(SIZE, SIZE, false);
    _energyRenderer.outputColorSpace = THREE.SRGBColorSpace;
    _energyRenderer.toneMapping      = THREE.ACESFilmicToneMapping;
    _energyRenderer.toneMappingExposure = 1.2;

    var scene  = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.z = 5.2;

    scene.add(new THREE.AmbientLight(0xffffff, 1.0));
    var dirFront = new THREE.DirectionalLight(0xffffff, 1.0);
    dirFront.position.set(2, 4, 3);
    scene.add(dirFront);
    var dirBack = new THREE.DirectionalLight(0xffffff, 0.4);
    dirBack.position.set(-2, 2, -3);
    scene.add(dirBack);

    var t   = Math.min(1, Math.max(0, (totalLoad - 10) / 50));
    var col = new THREE.Color(0x1a2a5e).lerp(new THREE.Color(0x8b1a1a), t);

    var group   = new THREE.Group();
    var autoRot = { active: true };
    var rings   = [];
    scene.add(group);
    addModelControls(canvas, group, camera, autoRot);

    function addFallback() {
      for (var i = 0; i < 3; i++) {
        var torus = new THREE.Mesh(
          new THREE.TorusGeometry(0.58 + i * 0.44, 0.032, 8, 64),
          new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.90 - i * 0.22 })
        );
        torus.rotation.x = Math.PI / 5;
        group.add(torus);
        rings.push({ mesh: torus, phase: (i / 3) * Math.PI * 2, dir: i % 2 === 0 ? 1 : -1 });
      }
    }

    addFallback();

    if (typeof THREE.GLTFLoader !== "undefined") {
      new THREE.GLTFLoader().load(
        ENERGY_MODEL,
        function (gltf) {
          fixMaterials(gltf.scene);
          fitModel(gltf.scene, 3.2);  
          while (group.children.length) group.remove(group.children[0]);
          rings = [];
          group.add(gltf.scene);
        },
        undefined,
        function () { /* Keep fallback */ }
      );
    }

    var clock = 0;
    function tick() {
      _energyRAF = requestAnimationFrame(tick);
      clock += 0.025;
      if (rings.length > 0) {
        for (var j = 0; j < rings.length; j++) {
          var r = rings[j];
          if (autoRot.active) {
            r.mesh.scale.setScalar(1 + 0.09 * Math.sin(clock + r.phase));
            r.mesh.rotation.z += 0.006 * r.dir;
          }
        }
      } else if (autoRot.active) {
        group.rotation.y += 0.008;
      }
      _energyRenderer.render(scene, camera);
    }
    tick();
  }

  window.SpiThree = {
    initHeroScene:   initHeroScene,
    initPriceScene:  initPriceScene,
    initEnergyScene: initEnergyScene,
  };
}());

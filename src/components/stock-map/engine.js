// TEE LOUNGE 재고 지도 엔진: 3D 사무실 모형, 재고 검색, 재고 등록 화면을 root 안에 그려요.
// store 가 null 이면 예시 데이터만 보여줘요. 반환값은 화면을 정리하는 함수예요.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const TEMPLATE = `<div id="app">
  <div id="stage" aria-label="TEE LOUNGE 사무실 3D 모형. 드래그해서 돌리고, 선반을 누르면 안에 든 재고가 보여요."></div>
  <div class="ui">
    <aside class="panel" id="panel">
      <div class="panel-top" id="panel-top">
        <div class="title-row">
          <div>
            <div class="eyebrow">TEE LOUNGE</div>
            <h1>재고 지도</h1>
          </div>
          <span class="pill">초안</span>
        </div>
        <label class="search" for="q">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input id="q" type="search" placeholder="품목, 컬러, 사이즈, 선반 코드" autocomplete="off" enterkeyhint="search">
          <button class="btn btn-ghost" id="clear" type="button" hidden>지우기</button>
        </label>
        <div class="tools">
          <button class="btn" id="btn-zones" type="button">구역 목록</button>
          <button class="btn" id="btn-all" type="button">전체 보기</button>
          <button class="btn" id="btn-top" type="button">위에서 보기</button>
          <button class="btn" id="btn-labels" type="button">이름표: 구역</button>
        </div>
        <div class="actions" id="actions" hidden>
          <button class="btn btn-primary" id="btn-add" type="button">재고 추가</button>
          <button class="btn" id="btn-paste" type="button">엑셀 붙여넣기</button>
          <button class="btn" id="btn-export" type="button">내보내기</button>
        </div>
      </div>
      <div class="list" id="list"></div>
      <p class="note" id="note">재고를 불러오는 중이에요.</p>
    </aside>

    <section class="sheet" id="sheet" hidden aria-live="polite">
      <div class="sheet-head">
        <div>
          <span class="code-big" id="sheet-code"></span>
          <span class="sheet-sub" id="sheet-sub"></span>
        </div>
        <button class="btn" id="sheet-close" type="button">닫기</button>
      </div>
      <ol class="levels" id="levels"></ol>
    </section>
  </div>
  <div class="toast" id="toast" role="status" hidden></div>
</div>

<dialog id="dlg-item" aria-labelledby="dlg-item-title">
  <form class="dlg" id="form-item">
    <h2 id="dlg-item-title">재고 추가</h2>
    <div class="field"><label for="f-name">품목명</label><input id="f-name" required maxlength="80" autocomplete="off" placeholder="예: 베이직 반팔 티"></div>
    <div class="grid3">
      <div class="field"><label for="f-color">컬러</label><input id="f-color" maxlength="40" autocomplete="off"></div>
      <div class="field"><label for="f-size">사이즈</label><input id="f-size" maxlength="20" autocomplete="off"></div>
      <div class="field"><label for="f-qty">수량</label><input id="f-qty" type="number" inputmode="numeric" min="0" step="1" value="0"></div>
    </div>
    <div class="grid2">
      <div class="field"><label for="f-unit">선반</label><select id="f-unit"></select></div>
      <div class="field"><label for="f-level">단</label><select id="f-level"></select></div>
    </div>
    <div class="field"><label for="f-note">메모</label><input id="f-note" maxlength="120" autocomplete="off" placeholder="예: 반품 검수 후 입고"></div>
    <p class="hint" id="f-meta" hidden></p>
    <div class="dlg-foot">
      <button class="btn btn-danger" id="f-delete" type="button" hidden>삭제</button>
      <div class="right">
        <button class="btn" id="f-cancel" type="button">취소</button>
        <button class="btn btn-primary" id="f-save" type="submit">저장</button>
      </div>
    </div>
  </form>
</dialog>

<dialog id="dlg-paste" aria-labelledby="dlg-paste-title">
  <form class="dlg" id="form-paste">
    <h2 id="dlg-paste-title">엑셀에서 붙여넣기</h2>
    <p class="hint">엑셀이나 구글 시트에서 표를 복사해 붙여넣으세요. 열 순서는 <code>품목 · 컬러 · 사이즈 · 수량 · 선반 · 단 · 메모</code>예요. 첫 줄에 열 제목이 있으면 제목을 보고 맞춰요. 선반은 지도에 보이는 코드(예: 3-B)로 적어주세요.</p>
    <div class="field"><label for="p-text">붙여넣을 표</label><textarea id="p-text" spellcheck="false" placeholder="베이직 반팔 티&#9;화이트&#9;M&#9;24&#9;2-A&#9;2"></textarea></div>
    <div class="preview" id="p-preview">붙여넣으면 여기에서 미리 확인할 수 있어요.</div>
    <div class="dlg-foot">
      <div class="right">
        <button class="btn" id="p-cancel" type="button">취소</button>
        <button class="btn btn-primary" id="p-save" type="submit" disabled>추가하기</button>
      </div>
    </div>
  </form>
</dialog>

<dialog id="dlg-export" aria-labelledby="dlg-export-title">
  <div class="dlg">
    <h2 id="dlg-export-title">재고 내보내기</h2>
    <p class="hint" id="x-count"></p>
    <div class="field"><label for="x-text">엑셀에 붙여넣을 수 있는 표</label><textarea id="x-text" readonly spellcheck="false"></textarea></div>
    <div class="dlg-foot">
      <button class="btn" id="x-close" type="button">닫기</button>
      <div class="right">
        <button class="btn" id="x-copy" type="button">표 복사</button>
        <button class="btn btn-primary" id="x-save" type="button" hidden>CSV 파일 저장</button>
      </div>
    </div>
  </div>
</dialog>`;

export function mountStockMap(root, store) {
  root.innerHTML = TEMPLATE;
  let disposed = false;
  let rafId = 0;
  const cleanups = [];
  const on = (target, type, fn) => { target.addEventListener(type, fn); cleanups.push(() => target.removeEventListener(type, fn)); };

  // ───────── 배치 데이터 (단위 m · x는 출입구에서 창가 쪽, z는 북쪽 벽에서 남쪽) ─────────
  const ROOM_W = 13, ROOM_D = 10, WALL_H = 2.5;

  const ZONES = {
    '1': { name: '입구 수납장' },
    '2': { name: '큐브 선반' },
    '3': { name: '원목 선반' },
    '4': { name: '포장실 벽 선반' },
    '5': { name: '포장실 크롬 선반' },
    '6': { name: '일자 창고' },
  };

  // front: 물건을 꺼내는 쪽 (S 남 · N 북 · E 동 · W 서 · both 양면)
  const UNITS = [
    { code: '1-A', zone: '1', x: [0.25, 1.4], z: [0.15, 0.55], h: 1.45, levels: 5, style: 'cube', front: 'S', shoes: 'mixed' },
    { code: '1-B', zone: '1', x: [1.45, 2.85], z: [0.15, 0.95], h: 2.3, levels: 4, style: 'boxes', front: 'S', sheets: true },
    { code: '1-C', zone: '1', x: [2.9, 4.2], z: [0.15, 0.55], h: 1.65, levels: 4, style: 'organizer', front: 'S' },
    { code: '2-A', zone: '2', x: [4.35, 6.05], z: [0.15, 0.6], h: 1.25, levels: 4, style: 'cube', front: 'S' },
    { code: '2-B', zone: '2', x: [6.05, 7.75], z: [0.15, 0.6], h: 1.25, levels: 4, style: 'cube', front: 'S' },
    { code: '3-A', zone: '3', x: [3.4, 5.0], z: [5.4, 6.0], h: 2.1, levels: 4, style: 'wood', front: 'N' },
    { code: '3-B', zone: '3', x: [5.0, 6.6], z: [5.4, 6.0], h: 2.1, levels: 4, style: 'wood', front: 'N' },
    { code: '3-C', zone: '3', x: [6.6, 8.2], z: [5.4, 6.0], h: 2.1, levels: 4, style: 'wood', front: 'N' },
    { code: '3-D', zone: '3', x: [8.2, 9.6], z: [5.4, 6.0], h: 2.1, levels: 4, style: 'wood', front: 'N' },
    { code: '3-E', zone: '3', x: [9.7, 10.3], z: [5.5, 6.05], h: 1.6, levels: 4, style: 'chrome', front: 'N' },
    { code: '4-A', zone: '4', x: [0.1, 0.45], z: [6.5, 8.0], h: 1.9, levels: 4, style: 'white', front: 'E', shoes: true },
    { code: '4-B', zone: '4', x: [0.15, 0.6], z: [8.1, 9.3], h: 1.8, levels: 5, style: 'white', front: 'E' },
    { code: '5-A', zone: '5', x: [0.3, 1.85], z: [9.45, 9.95], h: 1.8, levels: 4, style: 'chrome', front: 'N', topBins: true },
    { code: '5-B', zone: '5', x: [1.85, 3.4], z: [9.45, 9.95], h: 1.8, levels: 4, style: 'chrome', front: 'N', topBins: true },
  ];
  // 일자 창고: 원목 선반 뒤 크롬 줄 · 가운데 흰색 줄 · 남쪽 벽 크롬 줄. 동쪽 끝은 칸막이, 그 너머가 대표님 자리
  [
    ['ABC', [6.4, 6.9], 'chrome', 'S', 4, [[3.8, 5.9], [5.9, 8.0], [8.0, 10.0]]],
    ['DEF', [7.8, 8.3], 'white', 'both', 5, [[4.2, 5.9], [5.9, 7.6], [7.6, 9.2]]],
    ['GHI', [9.45, 9.95], 'chrome', 'N', 4, [[3.8, 5.9], [5.9, 8.0], [8.0, 10.0]]],
  ].forEach(([letters, z, style, front, levels, xs]) => {
    xs.forEach((x, i) => UNITS.push({ code: '6-' + letters[i], zone: '6', x, z, h: style === 'white' ? 1.9 : 1.8, levels, style, front }));
  });
  // 창고 데스크: 대표님 자리와 일자 창고를 나누는 낮은 데스크. 창고 쪽에서 꺼내고 윗판에도 올려요
  UNITS.push({ code: '6-J', zone: '6', x: [10.0, 10.6], z: [6.25, 9.9], h: 1.0, levels: 3, style: 'desk', front: 'W' });
  UNITS.sort((a, b) => a.code.localeCompare(b.code));
  const UNIT_SPEC = new Map(UNITS.map((u) => [u.code, u]));

  // 예시 재고: 저장된 재고가 없을 때 '예시로 둘러보기'에서만 보여요. [품목, 컬러, 사이즈, 수량, 선반, 단(1 = 맨 아래)]
  const EXAMPLES = [
    ['택배 박스 (소)', '부자재', '', 120, '1-B', 1],
    ['택배 박스 (중)', '부자재', '', 80, '1-B', 2],
    ['OPP 폴리백', '부자재', '', 500, '1-C', 2],
    ['스니커즈', '화이트', '250', 6, '2-A', 4],
    ['스니커즈', '화이트', '260', 4, '2-B', 4],
    ['스니커즈', '블랙', '270', 3, '2-B', 4],
    ['베이직 반팔 티', '화이트', 'S', 18, '2-A', 3],
    ['베이직 반팔 티', '화이트', 'M', 24, '2-A', 2],
    ['베이직 반팔 티', '화이트', 'L', 20, '2-B', 2],
    ['베이직 반팔 티', '블랙', 'M', 22, '2-B', 3],
    ['베이직 반팔 티', '블랙', 'L', 16, '1-A', 2],
    ['오버핏 반팔 티', '그레이', 'FREE', 30, '3-A', 3],
    ['맨투맨', '네이비', 'M', 14, '3-A', 2],
    ['맨투맨', '멜란지', 'L', 12, '3-B', 2],
    ['후드티', '블랙', 'L', 10, '3-B', 4],
    ['후드티', '오트밀', 'M', 9, '3-C', 3],
    ['후드집업', '차콜', 'XL', 7, '3-D', 1],
    ['린넨 셔츠', '아이보리', 'M', 11, '6-A', 3],
    ['옥스포드 셔츠', '스카이블루', 'L', 8, '6-B', 2],
    ['와이드 슬랙스', '블랙', '30', 13, '6-E', 4],
    ['와이드 슬랙스', '베이지', '28', 6, '6-F', 1],
    ['니트 가디건', '베이지', 'FREE', 15, '6-C', 3],
    ['꽈배기 니트', '크림', 'FREE', 9, '6-C', 2],
    ['데님 팬츠', '연청', '30', 10, '6-G', 4],
    ['패딩 조끼', '블랙', 'L', 5, '6-D', 4],
    ['롱패딩', '블랙', 'XL', 4, '6-F', 3],
    ['울 코트', '카멜', 'M', 3, '6-H', 4],
    ['반품 검수 대기', '', '', 6, '6-I', 1],
    ['스니커즈', '그레이', '250', 5, '4-A', 4],
    ['슬리퍼', '블랙', '260', 12, '4-B', 2],
    ['에코백', '내추럴', 'FREE', 25, '5-A', 3],
    ['포장 테이프', '부자재', '', 36, '5-A', 1],
    ['양말 3팩', '화이트', 'FREE', 40, '5-B', 2],
    ['볼캡', '네이비', 'FREE', 18, '5-B', 4],
  ];

  function indexItem(it) {
    const zone = it.unit.split('-')[0];
    const hay = [it.name, it.color, it.size, it.note, it.unit, `${it.unit} ${it.level}단`, ZONES[zone]?.name || ''].join(' ').toLowerCase();
    return { ...it, zone, hay: hay + ' ' + hay.replace(/\s+/g, '') };
  }
  const EXAMPLE_ITEMS = EXAMPLES.map(([name, color, size, qty, unit, level], i) => indexItem({ id: 'ex' + i, name, color, size, qty, unit, level, note: '' }));
  let ITEMS = [];

  // ───────── 3D 기본 ─────────
  const $ = (s) => root.querySelector(s);
  const cssVar = (n) => getComputedStyle(root).getPropertyValue(n).trim();
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const X = (x) => x - ROOM_W / 2;
  const Z = (z) => z - ROOM_D / 2;

  const stage = $('#stage');
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  // 성능: 해상도 배율은 1.5배까지, 그림자는 장면이 바뀔 때만 다시 계산해요
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  stage.appendChild(renderer.domElement);

  const labelRenderer = new CSS2DRenderer();
  labelRenderer.domElement.className = 'label-layer';
  stage.appendChild(labelRenderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 200);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.screenSpacePanning = false;
  controls.maxPolarAngle = Math.PI * 0.46;
  controls.minDistance = 2.5;
  controls.maxDistance = 60;
  let dirty = true;
  const invalidate = () => { dirty = true; };
  controls.addEventListener('change', invalidate);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xb9b2a6, 1.9));
  const sun = new THREE.DirectionalLight(0xffffff, 2.1);
  sun.position.set(-7, 16, 9);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 50 });
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.02;
  scene.add(sun);

  const BOX = new THREE.BoxGeometry(1, 1, 1);
  const CYL = new THREE.CylinderGeometry(1, 1, 1, 24);
  const BALL = new THREE.SphereGeometry(1, 20, 14);
  const matCache = new Map();
  function mat(color, extra) {
    const key = color + (extra ? JSON.stringify(extra) : '');
    if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0, ...extra }));
    return matCache.get(key);
  }
  const GLASS = new THREE.MeshStandardMaterial({ color: '#bcd6e8', transparent: true, opacity: 0.32, roughness: 0.15, depthWrite: false });

  function shape(geo, parent, sx, sy, sz, x, y, z, material, shadow = true) {
    const m = new THREE.Mesh(geo, typeof material === 'string' ? mat(material) : material);
    m.scale.set(sx, sy, sz);
    m.position.set(x, y, z);
    m.castShadow = shadow;
    m.receiveShadow = true;
    parent.add(m);
    return m;
  }
  // y는 바닥면 기준
  const block = (p, w, h, d, x, y, z, c, s) => shape(BOX, p, w, h, d, x, y + h / 2, z, c, s);
  // 방 좌표(x0~x1, z0~z1)로 상자 놓기
  const rblock = (x0, x1, z0, z1, y, h, c, p = scene, s) => block(p, x1 - x0, h, z1 - z0, X((x0 + x1) / 2), y, Z((z0 + z1) / 2), c, s);

  function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hash(s) { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; }

  // ───────── 바닥 · 벽 ─────────
  block(scene, ROOM_W + 0.7, 0.2, ROOM_D + 0.7, 0, -0.2, 0, '#f1f0eb', false);
  rblock(0, 16, 0, 10, 0, 0.006, '#e2dccf', scene, false);

  const WALL = '#f6f6f3';
  const walls = [];
  function wallGroup(n, p, lowH) {
    const g = new THREE.Group();
    scene.add(g);
    const w = { g, n: new THREE.Vector3(...n), p: new THREE.Vector3(...p), low: lowH / WALL_H, cur: 1, decor: [] };
    walls.push(w);
    return w;
  }
  const E = ROOM_W; // 동쪽 창가 x
  // 북쪽 벽 (TEE LOUNGE 글씨 · 큐브 선반 쪽)
  const north = wallGroup([0, 0, -1], [0, 0, Z(0)], 0.3);
  rblock(-0.07, E + 0.07, -0.07, 0.07, 0, WALL_H, WALL, north.g);
  // 남쪽 벽 (일자 창고 뒤)
  const south = wallGroup([0, 0, 1], [0, 0, Z(10)], 0.3);
  rblock(-0.07, E + 0.07, 9.93, 10.07, 0, WALL_H, WALL, south.g);
  // 서쪽: 1번 수납장 바로 옆 모서리의 유리 양여닫이 출입문
  const west = wallGroup([-1, 0, 0], [X(0), 0, 0], 0.3);
  rblock(-0.07, 0.07, -0.07, 0.3, 0, WALL_H, WALL, west.g);
  rblock(-0.07, 0.07, 2.3, 10.07, 0, WALL_H, WALL, west.g);
  rblock(-0.07, 0.07, 0.3, 2.3, 2.2, 0.3, WALL, west.g);
  rblock(-0.02, 0.02, 0.3, 2.3, 0, 2.2, GLASS, west.g, false);
  for (const z of [0.3, 0.55, 1.3, 2.05, 2.3]) rblock(-0.04, 0.04, z - 0.02, z + 0.02, 0, 2.2, '#b9bec2', west.g);
  for (const z of [1.18, 1.42]) rblock(0.03, 0.07, z - 0.012, z + 0.012, 0.75, 0.6, '#9aa1a7', west.g);
  // 동쪽: 라운지 · 대표님 자리 쪽 통창
  const east = wallGroup([1, 0, 0], [X(E), 0, 0], 0.3);
  rblock(E - 0.07, E + 0.07, -0.07, 10.07, 0, 0.3, WALL, east.g);
  rblock(E - 0.07, E + 0.07, -0.07, 10.07, 2.3, 0.2, WALL, east.g);
  rblock(E - 0.02, E + 0.02, 0, 10, 0.3, 2.0, GLASS, east.g, false);
  for (let k = 0; k <= 8; k++) { const z = k * 10 / 8; rblock(E - 0.05, E + 0.05, z - 0.03, z + 0.03, 0.3, 2.0, WALL, east.g); }
  // 대표님 자리 뒤 초록 벽 (남쪽 벽 안쪽 면)
  rblock(10.14, E - 0.07, 9.85, 9.93, 0, WALL_H, '#2f5a48', south.g);

  function textPlane(text, w, h, color) {
    const c = document.createElement('canvas');
    c.width = 1024; c.height = Math.round(1024 * h / w);
    const ctx = c.getContext('2d');
    ctx.fillStyle = color; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `600 ${Math.round(c.height * 0.72)}px ${cssVar('--font-ui') || 'sans-serif'}`;
    if ('letterSpacing' in ctx) ctx.letterSpacing = `${Math.round(c.height * 0.12)}px`;
    ctx.fillText(text, c.width / 2, c.height / 2);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  }
  function addSigns() {
    const a = textPlane('TEE LOUNGE', 2.6, 0.34, '#9a7854');
    a.position.set(X(6.05), 1.8, Z(0) + 0.076);
    north.g.add(a); north.decor.push(a);
    const b = textPlane('TEE LOUNGE', 1.5, 0.22, '#ffffff');
    b.rotation.y = Math.PI;
    b.position.set(X(11.75), 1.75, Z(9.85) - 0.006);
    south.g.add(b); south.decor.push(b);
    invalidate();
  }
  const signs = () => { if (!disposed) addSigns(); };
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(signs, signs);

  // ───────── 가구 (재고 아님) ─────────
  const DARK = '#2a2d30';
  function desk(x0, x1, z0, z1, h = 0.74, color = '#fafaf8') {
    rblock(x0, x1, z0, z1, h - 0.03, 0.03, color);
    for (const [x, z] of [[x0 + 0.04, z0 + 0.04], [x1 - 0.04, z0 + 0.04], [x0 + 0.04, z1 - 0.04], [x1 - 0.04, z1 - 0.04]]) rblock(x - 0.02, x + 0.02, z - 0.02, z + 0.02, 0, h - 0.03, '#c9cdd0');
  }
  function monitor(x, z, alongZ, facing) {
    const w = 0.58;
    const [x0, x1, z0, z1] = alongZ ? [x - 0.015, x + 0.015, z - w / 2, z + w / 2] : [x - w / 2, x + w / 2, z - 0.015, z + 0.015];
    rblock(x0, x1, z0, z1, 0.86, 0.35, DARK);
    rblock(x - 0.02, x + 0.02, z - 0.02, z + 0.02, 0.74, 0.14, DARK);
  }
  function chair(x, z) {
    shape(CYL, scene, 0.26, 0.03, 0.26, X(x), 0.02, Z(z), '#c3c9ce');
    shape(CYL, scene, 0.03, 0.42, 0.03, X(x), 0.24, Z(z), '#9aa1a7');
    shape(CYL, scene, 0.24, 0.07, 0.24, X(x), 0.48, Z(z), '#dfe3e6');
  }
  function plant(x, z, s = 1) {
    shape(CYL, scene, 0.17 * s, 0.36 * s, 0.17 * s, X(x), 0.18 * s, Z(z), '#f3f2ee');
    shape(BALL, scene, 0.36 * s, 0.42 * s, 0.36 * s, X(x), 0.78 * s, Z(z), '#86ad78');
    shape(BALL, scene, 0.24 * s, 0.3 * s, 0.24 * s, X(x + 0.12 * s), 1.12 * s, Z(z - 0.05 * s), '#94b986');
  }
  function sofa(x0, x1, z0, z1, back, color) {
    rblock(x0, x1, z0, z1, 0, 0.42, color);
    const t = 0.2;
    const b = { N: [x0, x1, z0, z0 + t], S: [x0, x1, z1 - t, z1], E: [x1 - t, x1, z0, z1], W: [x0, x0 + t, z0, z1] }[back];
    rblock(b[0], b[1], b[2], b[3], 0.42, 0.36, color);
  }
  function garmentRackZ(x, z0, z1, rnd) {
    rblock(x - 0.02, x + 0.02, z0, z0 + 0.04, 0, 1.6, '#e9e9e6');
    rblock(x - 0.02, x + 0.02, z1 - 0.04, z1, 0, 1.6, '#e9e9e6');
    rblock(x - 0.015, x + 0.015, z0, z1, 1.56, 0.03, '#e9e9e6');
    for (let z = z0 + 0.12; z < z1 - 0.1; z += 0.11) rblock(x - 0.22, x + 0.22, z - 0.02, z + 0.02, 0.85 + rnd() * 0.12, 0.6, ['#efe6d6', '#d9dde3', '#f5f2ea'][Math.floor(rnd() * 3)]);
  }
  function blueBin(x, z, rot = false) {
    const [w, d] = rot ? [0.4, 0.55] : [0.55, 0.4];
    rblock(x - w / 2, x + w / 2, z - d / 2, z + d / 2, 0, 0.3, '#2d4ea6');
  }
  {
    const r = rng(7);
    // 업무 데스크 2줄 (가운데 타공판 칸막이)
    for (let i = 0; i < 4; i++) {
      const x0 = 2 + i * 1.5;
      desk(x0 + 0.02, x0 + 1.48, 2.3, 3.03);
      desk(x0 + 0.02, x0 + 1.48, 3.07, 3.8);
      monitor(x0 + 0.75, 2.88, false);
      monitor(x0 + 0.75, 3.22, false);
      chair(x0 + 0.75, 1.9);
      chair(x0 + 0.75, 4.2);
    }
    rblock(2.0, 8.0, 3.03, 3.07, 0.74, 0.4, '#f2f2ef');
    // 커피 자리 · 냉장고 · 큰 화분 (라운지 왼쪽 벽)
    rblock(8.9, 9.85, 0.15, 0.6, 0, 0.9, '#f1efea');
    rblock(9.1, 9.5, 0.2, 0.5, 0.9, 0.3, '#2b2b2b');
    rblock(9.9, 10.5, 0.15, 0.75, 0, 1.35, '#2b2b2b');
    plant(10.95, 0.5, 1.2);
    // 대표님 자리: 동남쪽 구석, 초록 벽을 등지고 앉아 라운지 쪽(북쪽)을 봐요
    desk(10.9, 12.6, 8.3, 8.9, 0.74, '#fafaf8');
    monitor(11.75, 8.42, false);
    chair(11.75, 9.3);
    plant(12.65, 9.5, 0.85);
    // 라운지: 업무 데스크 동쪽 끝 바로 앞. 통창을 등진 갈색 가죽 소파, 마주 보는 가죽 의자 두 개, 유리 테이블
    rblock(9.8, 12.9, 1.4, 4.3, 0, 0.012, '#3d3935', scene, false);
    sofa(12.05, 12.85, 1.7, 3.9, 'E', '#8a4f35');
    sofa(9.95, 10.6, 1.95, 2.6, 'W', '#6b3f2a');
    sofa(9.95, 10.6, 3.0, 3.65, 'W', '#6b3f2a');
    rblock(10.95, 11.65, 2.2, 3.4, 0, 0.42, GLASS);
    // 오른쪽 크림 소파와 프린터 협탁
    sofa(10.9, 12.5, 4.45, 5.15, 'S', '#eee5d3');
    rblock(12.25, 12.85, 4.0, 4.4, 0, 0.55, '#3b2b21');
    rblock(12.35, 12.8, 4.05, 4.35, 0.55, 0.2, '#f4f4f2');
    // 창가 화분과 아크 스탠드
    plant(11.8, 0.7, 1.0);
    plant(12.45, 0.8, 0.9);
    plant(12.7, 5.5, 1.1);
    rblock(12.55, 12.61, 1.25, 1.31, 0, 1.9, '#2a2d30');
    rblock(11.95, 12.6, 1.25, 1.31, 1.88, 0.03, '#2a2d30');
    shape(CYL, scene, 0.22, 0.25, 0.22, X(11.95), 1.7, Z(1.28), '#222426');
    // 원목 선반 앞 택배 박스 (파란 테이프, 1~2단)
    [[3.7, 0.42, 1], [4.25, 0.4, 2], [4.8, 0.44, 1], [5.6, 0.4, 2], [6.15, 0.42, 1], [7.0, 0.4, 2], [7.55, 0.44, 2], [8.4, 0.4, 1], [8.95, 0.42, 2]].forEach(([x, h, n]) => {
      for (let k = 0; k < n; k++) { const y = k * h; rblock(x - 0.24, x + 0.24, 4.95, 5.37, y, h - 0.01, '#c9a473'); rblock(x - 0.03, x + 0.03, 4.95, 5.37, y + h - 0.01, 0.004, '#3c6fd6', scene, false); }
    });
    // 포장실
    desk(1.0, 3.0, 7.9, 8.6, 0.9);
    desk(2.4, 3.0, 7.0, 7.9, 0.9);
    rblock(1.6, 2.5, 8.0, 8.5, 0.9, 0.02, '#c9a473');
    rblock(0.8, 1.2, 7.2, 7.6, 0, 0.8, '#222426');
    desk(1.0, 2.0, 6.4, 6.95, 0.72);
    rblock(1.08, 1.92, 6.45, 6.9, 0.72, 0.05, '#c9a473');
    rblock(3.22, 3.26, 7.0, 8.2, 0.8, 0.95, '#fbfbfa');
    rblock(3.2, 3.28, 7.05, 7.09, 0, 0.8, '#c9cdd0');
    rblock(3.2, 3.28, 8.11, 8.15, 0, 0.8, '#c9cdd0');
    garmentRackZ(3.5, 7.2, 8.6, r);
    blueBin(1.4, 9.1); blueBin(4.6, 7.35); blueBin(7.6, 9.0); blueBin(9.55, 8.9);
    // 출입구 옆 핸드카트, 바닥의 투명 리빙박스와 비닐 포장 물건
    rblock(0.35, 0.75, 1.0, 1.05, 0, 1.05, '#e0662b');
    rblock(0.35, 0.75, 1.05, 1.35, 0, 0.04, '#333');
    rblock(1.0, 1.55, 1.0, 1.4, 0, 0.32, GLASS);
    rblock(1.1, 1.75, 1.45, 1.95, 0, 0.22, '#3a3f45');
  }

  // ───────── 재고 선반 ─────────
  const YAW = { S: 0, N: Math.PI, E: Math.PI / 2, W: -Math.PI / 2, both: 0 };
  const PAL = ['#ecebe7', '#d5d9dc', '#a7aeb6', '#45536a', '#2f3540', '#dacfbe', '#8b96a5', '#c6c0b3'];
  const SHOE = '#ec6a2c';
  const SHOE_MIX = ['#c9a473', '#d3b285', '#2f5fb3', '#e9c22c', '#ec6a2c', '#bf9a69', '#8a3b3b'];
  const KHAKI = ['#6d7550', '#646b48', '#777e59'];
  const BUBBLE = new THREE.MeshStandardMaterial({ color: '#f4f6f7', transparent: true, opacity: 0.85, roughness: 0.3 });

  function levelFloors(u) {
    const n = u.levels;
    if (u.style === 'cube') return Array.from({ length: n }, (_, i) => i === 0 ? 0.03 : i * u.h / (n - 1));
    if (u.style === 'boxes') return Array.from({ length: n }, (_, i) => i * u.h / n);
    if (u.style === 'desk') return [0.08, 0.5, u.h].slice(0, n);
    if (u.style === 'organizer') return Array.from({ length: n }, (_, i) => 0.03 + i * (u.h - 0.03) / n);
    const base = 0.1, step = (u.h - base) / n;
    return Array.from({ length: n }, (_, i) => base + i * step);
  }

  function shoes(stock, rnd, L, D, y, maxH, colors = [SHOE]) {
    const bw = 0.34, bh = 0.12, bd = Math.min(0.24, D * 0.8);
    for (let x = -L / 2 + 0.04; x + bw < L / 2 - 0.02; x += bw + 0.02) {
      const tiers = Math.max(1, Math.min(Math.floor(maxH / bh), (colors.length > 1 ? 2 : 1) + Math.floor(rnd() * 3)));
      for (let t = 0; t < tiers; t++) stock.push([x + bw / 2, y + t * bh, 0, bw, bh - 0.006, bd, colors[Math.floor(rnd() * colors.length)]]);
    }
  }
  function fillLevel(stock, rnd, u, L, D, y, maxH, li) {
    if (u.style === 'chrome' && li === 0) {
      for (let x = -L / 2 + 0.06; x + 0.5 < L / 2; x += 0.56) stock.push([x + 0.25, y, 0, 0.5, Math.min(0.3, maxH * 0.9), D * 0.85, '#2d4ea6']);
      return;
    }
    if (u.shoes && li === u.levels - 1) return shoes(stock, rnd, L, D, y, maxH);
    let x = -L / 2 + 0.05;
    while (x < L / 2 - 0.2) {
      const w = 0.26 + rnd() * 0.18;
      if (x + w > L / 2 - 0.04) break;
      if (rnd() > 0.14) stock.push([x + w / 2, y, (rnd() - 0.5) * 0.04, w, maxH * (0.3 + rnd() * 0.5), D * (0.62 + rnd() * 0.2), PAL[Math.floor(rnd() * PAL.length)]]);
      x += w + 0.035;
    }
  }

  const LOOK = {
    wood: { post: '#7b5233', board: '#cfa77b', pt: 0.05, bt: 0.03 },
    white: { post: '#efefec', board: '#f7f7f5', pt: 0.035, bt: 0.022 },
    chrome: { post: '#a9b1b9', board: '#c8cdd2', pt: 0.025, bt: 0.014 },
  };
  const STYLE = {
    open(g, u, L, D, floors, rnd, stock) {
      const k = LOOK[u.style];
      const nx = Math.max(2, Math.round(L / 1.1) + 1);
      for (let i = 0; i < nx; i++) {
        const x = -L / 2 + k.pt / 2 + (L - k.pt) * i / (nx - 1);
        for (const z of [-D / 2 + k.pt / 2, D / 2 - k.pt / 2]) block(g, k.pt, u.h, k.pt, x, 0, z, k.post);
      }
      for (const y of [...floors, u.h - k.bt]) block(g, L, k.bt, D, 0, y, 0, k.board);
      const gap = floors[1] - floors[0];
      floors.forEach((y, li) => fillLevel(stock, rnd, u, L, D, y + k.bt, gap - k.bt - 0.05, li));
      if (u.topBins) for (let x = -L / 2 + 0.06; x + 0.5 < L / 2; x += 0.56) stock.push([x + 0.25, u.h, 0, 0.5, 0.28, D * 0.85, '#2d4ea6']);
    },
    cube(g, u, L, D, floors, rnd, stock) {
      const c = '#f5f5f2', t = 0.025, rowH = u.h / (u.levels - 1);
      block(g, L, u.h, t, 0, 0, -D / 2 + t / 2, c);
      for (const x of [-L / 2 + t / 2, L / 2 - t / 2]) block(g, t, u.h, D, x, 0, 0, c);
      for (let i = 0; i < u.levels; i++) block(g, L, t, D, 0, i === 0 ? 0 : floors[i] - t, 0, c);
      const cells = Math.max(2, Math.round(L / 0.45)), cw = L / cells;
      for (let k = 1; k < cells; k++) block(g, t, u.h, D, -L / 2 + k * cw, 0, 0, c);
      for (let r = 0; r < u.levels - 1; r++) for (let k = 0; k < cells; k++) {
        if (rnd() < 0.12) continue;
        stock.push([-L / 2 + (k + 0.5) * cw, floors[r], 0.01, cw * 0.76, rowH * (0.35 + rnd() * 0.42), D * 0.78, PAL[Math.floor(rnd() * PAL.length)]]);
      }
      if (u.shoes === 'mixed') shoes(stock, rnd, L, D, u.h, 0.55, SHOE_MIX);
      else if (u.shoes !== false) shoes(stock, rnd, L, D, u.h, 0.42);
    },
    // 진한 갈색 큐브 수납장: 칸마다 카키색 박스를 쌓고, 위에 큰 택배 박스
    organizer(g, u, L, D, floors, rnd, stock) {
      const c = '#3b2b21', t = 0.03;
      block(g, L, u.h, t, 0, 0, -D / 2 + t / 2, c);
      for (const x of [-L / 2 + t / 2, L / 2 - t / 2]) block(g, t, u.h, D, x, 0, 0, c);
      for (let i = 0; i <= u.levels; i++) block(g, L, t, D, 0, i === u.levels ? u.h - t : floors[i] - t, 0, c);
      const cols = Math.max(2, Math.round(L / 0.43)), cw = L / cols;
      for (let k = 1; k < cols; k++) block(g, t, u.h, D, -L / 2 + k * cw, 0, 0, c);
      for (let r = 0; r < u.levels; r++) for (let k = 0; k < cols; k++) {
        const n = 2 + Math.floor(rnd() * 2);
        for (let j = 0; j < n; j++) stock.push([-L / 2 + (k + 0.5) * cw, floors[r] + j * 0.115, 0.01, cw * 0.82, 0.11, D * 0.8, KHAKI[Math.floor(rnd() * KHAKI.length)]]);
      }
      stock.push([-L / 4, u.h, 0, L * 0.48, 0.38, D * 1.3, '#c9a473'], [L / 4, u.h, 0, L * 0.46, 0.32, D * 1.2, '#bf9a69']);
    },
    desk(g, u, L, D, floors, rnd, stock) {
      const c = '#f3f2ee', t = 0.03;
      block(g, L, u.h, t, 0, 0, -D / 2 + t / 2, c);
      for (const x of [-L / 2 + t / 2, L / 2 - t / 2]) block(g, t, u.h, D, x, 0, 0, c);
      const bays = Math.max(2, Math.round(L / 1.2));
      for (let k = 1; k < bays; k++) block(g, t, u.h - 0.04, D, -L / 2 + k * L / bays, 0, 0, c);
      block(g, L, t, D, 0, floors[0] - t, 0, c);
      block(g, L, t, D, 0, floors[1] - t, 0, c);
      block(g, L + 0.04, 0.04, D + 0.04, 0, u.h - 0.04, 0, '#e9e6df');
      fillLevel(stock, rnd, u, L, D, floors[0], floors[1] - floors[0] - 0.08, 0);
      fillLevel(stock, rnd, u, L, D, floors[1], u.h - floors[1] - 0.1, 1);
      for (let x = -L / 2 + 0.2; x < L / 2 - 0.5; x += 0.7 + rnd() * 0.5) stock.push([x + 0.2, u.h, 0, 0.42, 0.18 + rnd() * 0.2, D * 0.7, rnd() > 0.5 ? '#c9a473' : '#bf9a69']);
    },
    boxes(g, u, L, D, floors, rnd, stock) {
      const tierH = u.h / u.levels;
      const right = L / 2 - (u.sheets ? 0.55 : 0);
      for (let t = 0; t < u.levels; t++) {
        let x = -L / 2;
        while (x < right - 0.25) {
          const w = Math.min(0.38 + rnd() * 0.22, right - x);
          const h = tierH * (0.86 + rnd() * 0.1);
          block(g, w - 0.02, h, D * (0.8 + rnd() * 0.15), x + w / 2, t * tierH, (rnd() - 0.5) * 0.05, ['#c9a473', '#bf9a69', '#d3b285'][Math.floor(rnd() * 3)]);
          if (rnd() > 0.5) block(g, 0.06, 0.004, D * 0.8, x + w / 2, t * tierH + h, 0, '#3c6fd6', false);
          x += w;
        }
      }
      if (u.sheets) {
        // 접어 둔 박스판 더미와 에어캡 뭉치
        const cx = right + 0.275;
        for (let i = 0; i < 26; i++) stock.push([cx + (rnd() - 0.5) * 0.04, i * 0.058, (rnd() - 0.5) * 0.04, 0.51, 0.052, D * 0.95, i % 2 ? '#c9a473' : '#b8935f']);
        shape(BALL, g, 0.32, 0.26, 0.24, cx - 0.35, 1.25, D / 2 + 0.05, BUBBLE);
      }
    },
  };

  const accentMats = [];
  const accentMat = (m) => (accentMats.push(m), m);
  const EDGE_MAT = accentMat(new THREE.LineBasicMaterial({ color: '#d9561f' }));
  const MARK_MAT = accentMat(new THREE.MeshBasicMaterial({ color: '#d9561f', transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false }));
  const HIT_MAT = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
  const hitboxes = [];
  const dummy = new THREE.Object3D();

  function makeLabel(className, html, onClick) {
    const el = document.createElement('div');
    el.className = 'lbl ' + className;
    el.innerHTML = html;
    if (onClick) {
      el.setAttribute('role', 'button');
      el.tabIndex = 0;
      el.addEventListener('click', (e) => { e.stopPropagation(); onClick(); });
      el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } });
    }
    return new CSS2DObject(el);
  }

  function buildUnit(u) {
    const alongZ = u.front === 'E' || u.front === 'W';
    const L = alongZ ? u.z[1] - u.z[0] : u.x[1] - u.x[0];
    const D = alongZ ? u.x[1] - u.x[0] : u.z[1] - u.z[0];
    const g = new THREE.Group();
    g.position.set(X((u.x[0] + u.x[1]) / 2), 0, Z((u.z[0] + u.z[1]) / 2));
    g.rotation.y = YAW[u.front];
    scene.add(g);

    const rnd = rng(hash(u.code));
    const floors = levelFloors(u);
    const stock = [];
    const build = STYLE[u.style] || STYLE.open;
    build(g, u, L, D, floors, rnd, stock);
    if (stock.length) {
      const inst = new THREE.InstancedMesh(BOX, mat('#ffffff'), stock.length);
      const col = new THREE.Color();
      stock.forEach(([x, y, z, w, h, d, c], i) => {
        dummy.position.set(x, y + h / 2, z);
        dummy.scale.set(w, h, d);
        dummy.updateMatrix();
        inst.setMatrixAt(i, dummy.matrix);
        inst.setColorAt(i, col.set(c));
      });
      inst.castShadow = inst.receiveShadow = true;
      g.add(inst);
    }

    const hit = new THREE.Mesh(BOX, HIT_MAT);
    hit.scale.set(L + 0.06, u.h + 0.05, D + 0.06);
    hit.position.y = (u.h + 0.05) / 2;
    hit.userData.code = u.code;
    g.add(hit);
    hitboxes.push(hit);

    const glow = new THREE.Mesh(BOX, accentMat(new THREE.MeshBasicMaterial({ color: '#d9561f', transparent: true, opacity: 0.14, depthWrite: false })));
    glow.scale.set(L + 0.1, u.h + 0.08, D + 0.1);
    glow.position.y = (u.h + 0.08) / 2;
    glow.visible = false;
    g.add(glow);

    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(L + 0.1, u.h + 0.08, D + 0.1)), EDGE_MAT);
    edges.position.y = (u.h + 0.08) / 2;
    edges.visible = false;
    g.add(edges);

    const marker = new THREE.Mesh(new THREE.PlaneGeometry(L + 0.14, D + 0.14), MARK_MAT);
    marker.rotation.x = -Math.PI / 2;
    marker.visible = false;
    g.add(marker);

    const label = makeLabel('lbl-unit', u.code, () => selectUnit(u.code));
    label.position.set(0, u.h + 0.22, 0);
    g.add(label);

    return { u, g, L, D, floors, glow, edges, marker, label };
  }

  const units = UNITS.map(buildUnit);
  const unitMap = new Map(units.map((R) => [R.u.code, R]));

  // 성능: 움직이지 않는 선반 · 가구 조각 수천 개를 재질별로 하나씩 묶어서 그리기 횟수를 줄여요
  function mergeStatic() {
    scene.updateMatrixWorld(true);
    const wallGroups = new Set(walls.map((w) => w.g));
    const keep = new Set([HIT_MAT, GLASS, ...accentMats]);
    const buckets = new Map();
    scene.traverse((o) => {
      if (!o.isMesh || o.isInstancedMesh || Array.isArray(o.material) || keep.has(o.material) || o.material.map || o.material.transparent) return;
      for (let p = o.parent; p; p = p.parent) if (wallGroups.has(p)) return;
      const key = o.material.uuid + (o.castShadow ? '|cast' : '');
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(o);
    });
    for (const meshes of buckets.values()) {
      if (meshes.length < 2) continue;
      const parts = meshes.map((m) => {
        const g = m.geometry.clone();
        g.clearGroups();
        return g.applyMatrix4(m.matrixWorld);
      });
      const merged = mergeGeometries(parts, false);
      parts.forEach((g) => g.dispose());
      if (!merged) continue;
      const mesh = new THREE.Mesh(merged, meshes[0].material);
      mesh.castShadow = meshes[0].castShadow;
      mesh.receiveShadow = true;
      meshes.forEach((m) => m.removeFromParent());
      scene.add(mesh);
    }
    renderer.shadowMap.needsUpdate = true;
  }
  mergeStatic();
  const unitsOfZone = (id) => units.filter((R) => R.u.zone === id);

  // 구역 · 공간 이름표
  const zoneLabels = Object.entries(ZONES).map(([id, z]) => {
    const list = unitsOfZone(id);
    const c = new THREE.Vector3();
    list.forEach((R) => c.add(R.g.position));
    c.divideScalar(list.length);
    c.y = Math.max(...list.map((R) => R.u.h)) + 0.6;
    const o = makeLabel('lbl-zone', `<span class="badge">${id}</span>${z.name}`, () => focusZone(id));
    o.position.copy(c);
    scene.add(o);
    return { id, o };
  });
  const areaLabels = [
    ['업무 데스크', 5.0, 1.25, 3.05], ['대표님 자리', 11.75, 1.5, 9.1], ['라운지', 11.3, 1.2, 2.8],
    ['포장실', 2.0, 1.4, 8.2], ['출입구', 0.55, 1.0, 1.3],
  ].map(([t, x, y, z]) => { const o = makeLabel('lbl-area', t); o.position.set(X(x), y, Z(z)); scene.add(o); return o; });

  // ───────── 상태 · 화면 ─────────
  const state = { query: '', results: [], hits: new Set(), zone: null, selected: null, level: null, labelMode: 'zone', showZones: false, collapsed: false };
  const LABEL_MODES = ['zone', 'unit', 'off'];
  const LABEL_TEXT = { zone: '이름표: 구역', unit: '이름표: 선반 코드', off: '이름표: 끔' };
  const panel = $('#panel'), list = $('#list'), sheet = $('#sheet'), input = $('#q');
  const isPhone = () => root.clientWidth < 720;

  function search(q) {
    const toks = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!toks.length) return [];
    return ITEMS.filter((it) => toks.every((t) => it.hay.includes(t)))
      .sort((a, b) => a.unit.localeCompare(b.unit) || b.level - a.level);
  }

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  // ───────── 저장된 재고 (db) ─────────
  // mode: loading(불러오는 중) · live(Supabase 연결) · offline(연결 설정이나 테이블이 없어 예시만)
  const data = { mode: 'loading', live: [], loaded: false, demo: false, canWrite: false, readOnly: false, meId: null };
  const editable = () => data.mode === 'live' && !data.demo && data.canWrite && !data.readOnly;
  const pendingQty = new Map();
  const qtyOf = (it) => (pendingQty.has(it.id) ? pendingQty.get(it.id) : it.qty);
  const str = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : typeof v === 'number' ? String(v) : '');

  function fromDoc(id, d) {
    if (!d || typeof d.name !== 'string' || !d.name.trim()) return null;
    const code = str(d.unit, 10).toUpperCase();
    const spec = UNIT_SPEC.get(code);
    return indexItem({
      id,
      name: str(d.name, 80),
      color: str(d.color, 40),
      size: str(d.size, 20),
      qty: Math.max(0, Math.round(Number(d.qty) || 0)),
      unit: spec ? code : '?',
      level: spec ? Math.min(Math.max(1, Math.round(Number(d.level) || 1)), spec.levels) : 1,
      note: str(d.note, 120),
      updatedAt: Number(d.updatedAt) || 0,
      updatedBy: typeof d.updatedBy === 'string' ? d.updatedBy : null,
    });
  }

  function applyItems() {
    ITEMS = data.mode === 'offline' || data.demo ? EXAMPLE_ITEMS : data.mode === 'live' ? data.live : [];
    if (state.query.trim()) {
      state.results = search(state.query);
      state.hits = new Set(state.results.map((it) => it.unit));
    }
    refresh();
  }

  async function initData() {
    if (!store) { data.mode = 'offline'; applyItems(); return; }
    data.canWrite = store.canWrite !== false;
    data.mode = 'live';
    applyItems();
    cleanups.push(store.subscribe((rows) => {
      if (disposed) return;
      data.live = rows.map((r) => fromDoc(r.id, r)).filter(Boolean);
      data.loaded = true;
      if (data.live.length) data.demo = false;
      applyItems();
    }, (code) => {
      if (disposed) return;
      if (code === 'missing_table') { data.mode = 'offline'; data.setup = true; applyItems(); return; }
      data.loaded = true;
      applyItems();
      toast('재고를 불러오지 못했어요. 잠시 후 새로 고쳐 주세요.');
    }));
  }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const stamp = () => ({ updatedAt: Date.now(), updatedBy: data.meId });
  function failed(e) {
    const code = e && e.code;
    if ((code === 'forbidden' || code === 'invalid_argument') && !data.readOnly) {
      data.readOnly = true;
      applyItems();
      toast('지금은 재고를 고칠 수 없게 설정돼 있어요. 관리자에게 문의해 주세요.');
    } else if (code === 'quota_exceeded') toast('저장 공간이 가득 찼어요. 쓰지 않는 재고를 지운 뒤 다시 시도해 주세요.');
    else if (code === 'resource_exhausted') toast('요청이 많아 잠시 멈췄어요. 조금 뒤 다시 시도해 주세요.');
    else toast('저장하지 못했어요. 잠시 후 다시 시도해 주세요.');
    return false;
  }
  async function write(fn) {
    try { await fn(); return true; } catch (e) {
      if (!e || e.code !== 'unavailable') return failed(e);
      await sleep(400 + Math.random() * 600);
      try { await fn(); return true; } catch (e2) { return failed(e2); }
    }
  }

  // 수량 +/−: 빠르게 여러 번 눌러도 멈춘 뒤 한 번만 저장해요
  const qtyTimers = new Map(), qtyWriting = new Set();
  function bumpQty(it, delta) {
    const next = Math.max(0, qtyOf(it) + delta);
    pendingQty.set(it.id, next);
    root.querySelectorAll(`[data-qty="${CSS.escape(it.id)}"]`).forEach((o) => { o.textContent = String(next); });
    clearTimeout(qtyTimers.get(it.id));
    qtyTimers.set(it.id, setTimeout(() => flushQty(it.id), 700));
  }
  async function flushQty(id) {
    if (qtyWriting.has(id)) { qtyTimers.set(id, setTimeout(() => flushQty(id), 300)); return; }
    const q = pendingQty.get(id);
    if (q == null) return;
    qtyWriting.add(id);
    const ok = await write(() => store.update(id, { qty: q, ...stamp() }));
    qtyWriting.delete(id);
    if (!ok || pendingQty.get(id) === q) pendingQty.delete(id);
    refresh();
  }

  let toastTimer = 0;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 3400);
  }

  function renderChrome() {
    const live = data.mode === 'live' && !data.demo;
    $('#actions').hidden = !live;
    $('#btn-add').hidden = $('#btn-paste').hidden = !editable();
    $('#btn-export').disabled = !ITEMS.length;
    const note = $('#note');
    note.replaceChildren();
    let msg;
    if (data.mode === 'loading' || (data.mode === 'live' && !data.loaded)) msg = '재고를 불러오는 중이에요.';
    else if (data.mode === 'offline') msg = data.setup
      ? '재고 테이블(stock_items)이 아직 준비되지 않아 예시를 보여드려요. 관리자가 Supabase에 테이블을 만들면 실제 재고가 저장돼요.'
      : 'Supabase 연결 설정이 없어 예시를 보여드려요.';
    else if (data.demo) msg = '예시 데이터를 보는 중이에요. 저장된 재고가 아니에요.';
    else msg = `재고 ${ITEMS.length}건 · 팀원과 실시간으로 공유돼요${editable() ? '' : ' · 보기 전용'}.`;
    note.append(msg + (isPhone() ? '' : ' 키보드 숫자 1~6을 누르면 그 구역으로 이동하고, 0은 전체 보기예요.') + ' 배치는 영상을 보고 그린 초안이에요.');
    if (data.demo) {
      const off = el('button', 'link', '예시 끄기');
      off.type = 'button';
      off.addEventListener('click', () => { data.demo = false; applyItems(); });
      note.append(' ', off);
    }
  }

  function emptyCard() {
    const card = el('div', 'card');
    card.append(el('strong', null, '아직 등록된 재고가 없어요'));
    card.append(el('p', null, editable()
      ? '재고를 등록하면 지도에서 어느 선반 몇 단에 있는지 바로 찾을 수 있어요. 엑셀 표를 그대로 붙여넣거나 하나씩 추가하세요.'
      : '편집 권한이 있는 사람이 재고를 등록하면 여기에 보여요.'));
    const row = el('div', 'actions');
    const btn = (text, cls, fn) => { const b = el('button', 'btn' + (cls ? ' ' + cls : ''), text); b.type = 'button'; b.addEventListener('click', fn); row.append(b); };
    if (editable()) {
      btn('엑셀 붙여넣기', 'btn-primary', openPaste);
      btn('하나씩 추가', '', () => openItemDialog(null));
    }
    btn('예시로 둘러보기', '', () => { data.demo = true; applyItems(); });
    card.append(row);
    return card;
  }

  function renderList() {
    list.replaceChildren();
    const q = state.query.trim();
    const empty = data.mode === 'live' && data.loaded && !data.demo && !data.live.length;
    if (q) {
      const res = state.results;
      list.append(el('div', 'list-head', `검색 결과 ${res.length}건`));
      if (!res.length) list.append(el('p', 'empty', `‘${q}’에 맞는 재고가 없어요. 품목명, 컬러, 사이즈나 선반 코드(예: 3-B)로 찾아보세요.`));
      for (const it of res) {
        const b = el('button', 'row');
        b.type = 'button';
        if (state.selected === it.unit && state.level === it.level) b.classList.add('is-on');
        const mid = el('span');
        mid.append(el('span', 'row-title', it.name), el('span', 'row-meta', [it.color, it.size, it.note].filter(Boolean).join(' · ') || ZONES[it.zone]?.name || ''));
        const placed = unitMap.has(it.unit);
        b.append(el('span', 'loc', placed ? `${it.unit} · ${it.level}단` : '위치 없음'), mid, el('span', 'qty', `${qtyOf(it)}개`));
        b.addEventListener('click', () => {
          if (!placed) { openItemDialog(it); return; }
          if (isPhone()) state.collapsed = true;
          selectUnit(it.unit, it.level);
        });
        list.append(b);
      }
    } else {
      if (empty) list.append(emptyCard());
      list.append(el('div', 'list-head', '구역'));
      for (const [id, z] of Object.entries(ZONES)) {
        const us = unitsOfZone(id);
        const n = ITEMS.filter((it) => it.zone === id).length;
        const b = el('button', 'row');
        b.type = 'button';
        if (state.zone === id) b.classList.add('is-on');
        const mid = el('span');
        mid.append(el('span', 'row-title', z.name), el('span', 'row-meta', `${us[0].u.code} ~ ${us.at(-1).u.code} · 선반 ${us.length}개`));
        b.append(el('span', 'badge', id), mid, el('span', 'qty', `품목 ${n}`));
        b.addEventListener('click', () => { if (isPhone()) state.showZones = false; focusZone(id); });
        list.append(b);
      }
    }
    panel.classList.toggle('list-open', (!!q && !state.collapsed) || state.showZones);
    $('#clear').hidden = !q;
  }

  function renderSheet() {
    const R = unitMap.get(state.selected);
    if (!R) { sheet.hidden = true; return; }
    sheet.hidden = false;
    const canEdit = editable();
    const inUnit = ITEMS.filter((it) => it.unit === R.u.code);
    $('#sheet-code').textContent = R.u.code;
    $('#sheet-sub').textContent = `${R.u.zone} · ${ZONES[R.u.zone].name} · 품목 ${inUnit.length}개`;
    const ol = $('#levels');
    ol.replaceChildren();
    for (let lv = R.u.levels; lv >= 1; lv--) {
      const li = el('li', 'level');
      li.tabIndex = 0;
      if (state.level === lv) li.classList.add('is-active');
      const here = inUnit.filter((it) => it.level === lv);
      const where = lv === R.u.levels ? ' · 맨 위' : lv === 1 ? ' · 맨 아래' : '';
      const head = el('div', 'lv');
      head.append(el('span', null, `${lv}단${where}`), el('span', null, here.length ? `${here.reduce((s, it) => s + qtyOf(it), 0)}개` : ''));
      li.append(head);
      if (here.length) {
        const ul = el('ul', 'items');
        for (const it of here) {
          const row = el('li', 'item');
          const name = el('span', 'item-main', it.name + ' ');
          const meta = [it.color, it.size, it.note].filter(Boolean).join(' · ');
          if (meta) name.append(el('small', null, meta));
          row.append(name);
          if (canEdit) {
            const step = el('span', 'stepper');
            const minus = el('button', null, '−');
            const plus = el('button', null, '+');
            const out = el('output', null, String(qtyOf(it)));
            out.dataset.qty = it.id;
            minus.type = plus.type = 'button';
            minus.setAttribute('aria-label', `${it.name} 1개 빼기`);
            plus.setAttribute('aria-label', `${it.name} 1개 더하기`);
            minus.addEventListener('click', () => bumpQty(it, -1));
            plus.addEventListener('click', () => bumpQty(it, 1));
            step.append(minus, out, plus);
            const edit = el('button', 'icon-btn', '수정');
            edit.type = 'button';
            edit.addEventListener('click', () => openItemDialog(it));
            row.append(step, edit);
          } else row.append(el('span', 'qty', `${qtyOf(it)}개`));
          ul.append(row);
        }
        li.append(ul);
      } else li.append(el('div', 'lv-empty', '등록된 재고 없음'));
      if (canEdit) {
        const add = el('button', 'icon-btn add-here', '+ 이 단에 추가');
        add.type = 'button';
        add.addEventListener('click', () => openItemDialog(null, { unit: R.u.code, level: lv }));
        li.append(add);
      }
      const pick = () => { state.level = state.level === lv ? null : lv; refresh(); };
      li.addEventListener('click', (e) => { if (!e.target.closest('button')) pick(); });
      li.addEventListener('keydown', (e) => { if (e.target === li && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); pick(); } });
      ol.append(li);
    }
  }

  function refresh3D() {
    const hits = state.hits;
    const counts = new Map();
    for (const it of ITEMS) counts.set(it.unit, (counts.get(it.unit) || 0) + 1);
    for (const R of units) {
      const hit = hits.has(R.u.code), sel = state.selected === R.u.code;
      const n = counts.get(R.u.code) || 0;
      R.glow.visible = R.edges.visible = hit || sel;
      R.glow.material.opacity = sel ? 0.24 : 0.13;
      R.label.element.textContent = n ? `${R.u.code} · ${n}` : R.u.code;
      R.label.visible = state.labelMode === 'unit' || hit || sel;
      R.label.element.classList.toggle('is-hit', hit || sel);
      R.marker.visible = sel && state.level != null;
      if (R.marker.visible) R.marker.position.y = R.floors[state.level - 1] + 0.035;
    }
    for (const { id, o } of zoneLabels) {
      o.visible = state.labelMode === 'zone';
      o.element.classList.toggle('is-hit', state.zone === id || unitsOfZone(id).some((R) => hits.has(R.u.code) || state.selected === R.u.code));
    }
    for (const o of areaLabels) o.visible = state.labelMode !== 'off';
    invalidate();
  }

  function refresh() { renderChrome(); renderList(); renderSheet(); refresh3D(); layoutView(); }

  // ───────── 재고 추가 · 수정 ─────────
  const dlgItem = $('#dlg-item'), formItem = $('#form-item');
  const f = (id) => $('#f-' + id);
  let editing = null;
  let deleteArmed = 0;
  const fmtTime = (ts) => new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(ts));

  function fillUnitSelect(value) {
    const sel = f('unit');
    sel.replaceChildren();
    for (const [id, z] of Object.entries(ZONES)) {
      const g = document.createElement('optgroup');
      g.label = `${id} · ${z.name}`;
      unitsOfZone(id).forEach((R) => g.append(new Option(R.u.code, R.u.code)));
      sel.append(g);
    }
    sel.value = UNIT_SPEC.has(value) ? value : UNITS[0].code;
  }
  function fillLevelSelect(value) {
    const n = UNIT_SPEC.get(f('unit').value)?.levels || 1;
    const sel = f('level');
    sel.replaceChildren();
    for (let lv = n; lv >= 1; lv--) sel.append(new Option(`${lv}단${lv === n ? ' (맨 위)' : lv === 1 ? ' (맨 아래)' : ''}`, String(lv)));
    sel.value = String(Math.min(Math.max(1, Number(value) || 1), n));
  }
  f('unit').addEventListener('change', () => fillLevelSelect(f('level').value));

  function openItemDialog(it, preset = {}) {
    if (!editable()) return;
    editing = it;
    deleteArmed = 0;
    $('#dlg-item-title').textContent = it ? '재고 수정' : '재고 추가';
    f('name').value = it ? it.name : '';
    f('color').value = it ? it.color : '';
    f('size').value = it ? it.size : '';
    f('qty').value = String(it ? qtyOf(it) : 0);
    f('note').value = it ? it.note : '';
    fillUnitSelect(it && it.unit !== '?' ? it.unit : preset.unit || state.selected);
    fillLevelSelect(it ? it.level : preset.level || state.level || 1);
    const del = f('delete');
    del.hidden = !it;
    del.textContent = '삭제';
    const meta = f('meta');
    meta.hidden = !(it && it.updatedAt);
    if (it && it.updatedAt) {
      meta.textContent = `마지막 수정 · ${fmtTime(it.updatedAt)}`;
    }
    dlgItem.showModal();
    f('name').focus();
  }
  f('cancel').addEventListener('click', () => dlgItem.close());
  formItem.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = f('name').value.trim();
    if (!name) { f('name').focus(); return; }
    const body = {
      name: name.slice(0, 80),
      color: f('color').value.trim().slice(0, 40),
      size: f('size').value.trim().slice(0, 20),
      qty: Math.max(0, Math.round(Number(f('qty').value) || 0)),
      unit: f('unit').value,
      level: Number(f('level').value) || 1,
      note: f('note').value.trim().slice(0, 120),
      ...stamp(),
    };
    const save = f('save');
    save.disabled = true;
    const was = editing;
    if (was) { pendingQty.delete(was.id); clearTimeout(qtyTimers.get(was.id)); }
    const ok = await write(() => (was
      ? store.update(was.id, body)
      : store.add(body)));
    save.disabled = false;
    if (!ok) return;
    dlgItem.close();
    toast(was ? '저장했어요' : `${body.unit} ${body.level}단에 추가했어요`);
    selectUnit(body.unit, body.level);
  });
  f('delete').addEventListener('click', async () => {
    const it = editing;
    if (!it) return;
    if (Date.now() - deleteArmed > 4000) {
      deleteArmed = Date.now();
      f('delete').textContent = '한 번 더 누르면 삭제';
      return;
    }
    f('delete').disabled = true;
    const ok = await write(() => store.remove(it.id));
    f('delete').disabled = false;
    if (!ok) return;
    dlgItem.close();
    toast(`‘${it.name}’을(를) 지웠어요`);
  });

  // ───────── 엑셀 붙여넣기 ─────────
  const dlgPaste = $('#dlg-paste');
  const HEADS = {
    name: ['품목', '품목명', '상품명', '제품명', '이름', 'name', 'item'],
    color: ['컬러', '색상', '색', 'color'],
    size: ['사이즈', '크기', 'size'],
    qty: ['수량', '재고', '개수', '재고수량', 'qty', 'quantity'],
    unit: ['선반', '위치', '선반코드', '코드', 'location', 'shelf'],
    level: ['단', '층', '칸', 'level'],
    note: ['메모', '비고', 'note'],
  };
  function splitRow(line) {
    if (line.includes('\t')) return line.split('\t');
    const out = [];
    let cur = '', quoted = false;
    for (const ch of line) {
      if (ch === '"') quoted = !quoted;
      else if (ch === ',' && !quoted) { out.push(cur); cur = ''; }
      else cur += ch;
    }
    out.push(cur);
    return out;
  }
  function parsePaste(text) {
    const lines = text.replace(/\r/g, '').split('\n').filter((l) => l.trim());
    const rows = [], bad = [];
    if (!lines.length) return { rows, bad };
    let cols = ['name', 'color', 'size', 'qty', 'unit', 'level', 'note'];
    let start = 0;
    const mapped = splitRow(lines[0]).map((c) => {
      const key = c.trim().toLowerCase().replace(/\s+/g, '');
      return Object.keys(HEADS).find((k) => HEADS[k].includes(key)) || null;
    });
    if (mapped.filter(Boolean).length >= 2) { cols = mapped; start = 1; }
    lines.slice(start).forEach((line, i) => {
      const cells = splitRow(line).map((c) => c.trim());
      const r = {};
      cols.forEach((k, j) => { if (k && r[k] == null && cells[j] != null) r[k] = cells[j]; });
      const at = `${start + i + 1}번째 줄`;
      const name = (r.name || '').trim();
      const m = String(r.unit || '').toUpperCase().match(/([1-9])\s*-\s*([A-Z])(?:\s*[-·\s]\s*(\d+))?/);
      const unit = m ? `${m[1]}-${m[2]}` : '';
      let level = m && m[3] ? Number(m[3]) : 0;
      if (r.level) level = parseInt(String(r.level).replace(/[^\d]/g, ''), 10) || level;
      const spec = UNIT_SPEC.get(unit);
      if (!name) { bad.push(`${at}: 품목명이 비어 있어요`); return; }
      if (!spec) { bad.push(`${at}: 선반 코드 ‘${r.unit || ''}’를 지도에서 못 찾았어요`); return; }
      rows.push({
        name: name.slice(0, 80),
        color: (r.color || '').slice(0, 40),
        size: (r.size || '').slice(0, 20),
        qty: Math.max(0, parseInt(String(r.qty || '0').replace(/[^\d]/g, ''), 10) || 0),
        unit,
        level: Math.min(Math.max(1, level || 1), spec.levels),
        note: (r.note || '').slice(0, 120),
      });
    });
    return { rows, bad };
  }
  function renderPastePreview() {
    const { rows, bad } = parsePaste($('#p-text').value);
    const box = $('#p-preview');
    box.replaceChildren();
    if (!rows.length && !bad.length) { box.append('붙여넣으면 여기에서 미리 확인할 수 있어요.'); $('#p-save').disabled = true; return; }
    box.append(el('div', null, `추가할 재고 ${rows.length}건${bad.length ? ` · 확인 필요 ${bad.length}건` : ''}`));
    rows.slice(0, 4).forEach((r) => box.append(el('div', null, `· ${[r.name, r.color, r.size].filter(Boolean).join(' / ')} ${r.qty}개 → ${r.unit} ${r.level}단`)));
    if (rows.length > 4) box.append(el('div', null, `· 외 ${rows.length - 4}건`));
    bad.slice(0, 5).forEach((b) => box.append(el('div', 'bad', b)));
    if (bad.length > 5) box.append(el('div', 'bad', `외 ${bad.length - 5}줄`));
    $('#p-save').disabled = !rows.length;
    $('#p-save').textContent = rows.length ? `${rows.length}건 추가하기` : '추가하기';
  }
  function openPaste() {
    if (!editable()) return;
    renderPastePreview();
    dlgPaste.showModal();
    $('#p-text').focus();
  }
  $('#p-text').addEventListener('input', renderPastePreview);
  $('#p-cancel').addEventListener('click', () => dlgPaste.close());
  $('#form-paste').addEventListener('submit', async (e) => {
    e.preventDefault();
    const { rows } = parsePaste($('#p-text').value);
    if (!rows.length) return;
    const btn = $('#p-save');
    btn.disabled = true;
    let done = 0;
    for (const r of rows) {
      btn.textContent = `저장 중 ${done}/${rows.length}`;
      const now = Date.now();
      const ok = await write(() => store.add({ ...r, updatedAt: now }));
      if (!ok) break;
      done++;
    }
    if (done === rows.length) {
      $('#p-text').value = '';
      dlgPaste.close();
      toast(`재고 ${done}건을 추가했어요`);
    } else {
      // 저장된 줄은 빼고 남은 줄만 남겨서, 다시 눌러도 중복되지 않게 해요
      $('#p-text').value = toTsv(rows.slice(done).map((r) => [r.name, r.color, r.size, r.qty, r.unit, r.level, r.note]));
      if (done) toast(`${done}건까지 추가했어요. 남은 줄은 다시 시도해 주세요.`);
    }
    renderPastePreview();
  });

  // ───────── 내보내기 ─────────
  const dlgExport = $('#dlg-export');
  const toTsv = (rows) => rows.map((r) => r.map((c) => String(c ?? '').replace(/[\t\r\n]+/g, ' ')).join('\t')).join('\n');
  const csvCell = (c) => { const s = String(c ?? ''); return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  function exportRows() {
    const sorted = ITEMS.slice().sort((a, b) => a.unit.localeCompare(b.unit) || a.level - b.level || a.name.localeCompare(b.name, 'ko'));
    return [['품목', '컬러', '사이즈', '수량', '선반', '단', '메모'], ...sorted.map((it) => [it.name, it.color, it.size, qtyOf(it), it.unit, it.level, it.note])];
  }
  $('#btn-export').addEventListener('click', () => {
    const rows = exportRows();
    $('#x-count').textContent = `재고 ${rows.length - 1}건이에요. 표 전체를 복사해 엑셀이나 구글 시트에 붙여넣으면 돼요.`;
    $('#x-text').value = toTsv(rows);
    $('#x-save').hidden = false;
    dlgExport.showModal();
  });
  $('#x-close').addEventListener('click', () => dlgExport.close());
  $('#x-copy').addEventListener('click', () => {
    const text = $('#x-text').value;
    const fallback = () => { $('#x-text').focus(); $('#x-text').select(); toast('표를 선택했어요. Ctrl+C(⌘+C)로 복사해 주세요.'); };
    try {
      navigator.clipboard.writeText(text).then(() => toast('표를 복사했어요'), fallback);
    } catch { fallback(); }
  });
  $('#x-save').addEventListener('click', () => {
    const d = new Date();
    const day = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const csv = '\uFEFF' + exportRows().map((r) => r.map(csvCell).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `TEE LOUNGE 재고 ${day}.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $('#btn-add').addEventListener('click', () => openItemDialog(null));
  $('#btn-paste').addEventListener('click', openPaste);

  // ───────── 카메라 ─────────
  let tween = null;
  let vis = { x0: -1, x1: 1, y0: -1, y1: 1 }; // 패널에 가려지지 않은 화면 영역 (NDC)
  const DEFAULT_DIR = new THREE.Vector3(-0.42, 0.95, 0.85).normalize();
  const PHONE_DIR = new THREE.Vector3(-1.0, 1.15, 0.22).normalize(); // 휴대폰: 출입구 쪽에서 창가를 바라봐요
  const ROOM_BOX = new THREE.Box3(new THREE.Vector3(-ROOM_W / 2, 0, -ROOM_D / 2), new THREE.Vector3(ROOM_W / 2, 1.2, ROOM_D / 2));
  const portrait = () => stage.clientWidth / Math.max(1, stage.clientHeight) < 0.9;

  // box 전체가 보이는 영역에 들어오는 가장 가까운 거리
  function fitDistance(box, dir, target) {
    const cam = camera.clone();
    const pts = [];
    for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) pts.push(new THREE.Vector3(x, y, z));
    const v = new THREE.Vector3();
    let lo = 1, hi = controls.maxDistance;
    for (let i = 0; i < 20; i++) {
      const mid = (lo + hi) / 2;
      cam.position.copy(target).addScaledVector(dir, mid);
      cam.lookAt(target);
      cam.updateMatrixWorld();
      const fits = pts.every((p) => { v.copy(p).project(cam); return v.z < 1 && v.x > vis.x0 && v.x < vis.x1 && v.y > vis.y0 && v.y < vis.y1; });
      if (fits) hi = mid; else lo = mid;
    }
    return hi;
  }

  function moveCamera(pos, target, instant) {
    if (instant || reduceMotion) { tween = null; camera.position.copy(pos); controls.target.copy(target); controls.update(); return; }
    tween = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: target, start: performance.now(), ms: 750 };
  }
  // 지금 보는 방향은 유지하고, 너무 눕거나 너무 세운 각도만 조정해요
  function viewDir() {
    const dir = camera.position.clone().sub(controls.target).normalize();
    const fallback = portrait() ? PHONE_DIR : DEFAULT_DIR;
    let hx = dir.x, hz = dir.z;
    if (Math.hypot(hx, hz) < 1e-3) { hx = fallback.x; hz = fallback.z; }
    const hl = Math.hypot(hx, hz);
    const phi = THREE.MathUtils.clamp(Math.asin(THREE.MathUtils.clamp(dir.y, -1, 1)), 0.75, 1.2);
    return new THREE.Vector3((hx / hl) * Math.cos(phi), Math.sin(phi), (hz / hl) * Math.cos(phi));
  }
  function frameBox(box) {
    const c = box.getCenter(new THREE.Vector3());
    c.y = Math.min(c.y, 0.9);
    const d = viewDir();
    const padded = box.clone().expandByVector(new THREE.Vector3(0.7, 0.1, 0.7));
    const dist = THREE.MathUtils.clamp(fitDistance(padded, d, c), 4.5, controls.maxDistance);
    moveCamera(c.clone().addScaledVector(d, dist), c);
  }
  function unitBox(R) {
    return new THREE.Box3(new THREE.Vector3(X(R.u.x[0]), 0, Z(R.u.z[0])), new THREE.Vector3(X(R.u.x[1]), R.u.h, Z(R.u.z[1])));
  }
  function frameUnits(codes) {
    const box = new THREE.Box3();
    codes.forEach((c) => box.union(unitBox(unitMap.get(c))));
    if (!box.isEmpty()) frameBox(box);
  }
  function overview(instant) {
    const t = new THREE.Vector3(0, 0, 0);
    const d = portrait() ? PHONE_DIR : DEFAULT_DIR;
    moveCamera(t.clone().addScaledVector(d, fitDistance(ROOM_BOX, d, t)), t, instant);
  }
  // 휴대폰에서는 긴 쪽이 세로로 오게 돌려서 내려다봐요
  function topView() {
    const t = new THREE.Vector3(0, 0, 0);
    const d = (portrait() ? new THREE.Vector3(-0.02, 1, 0) : new THREE.Vector3(0, 1, 0.02)).normalize();
    moveCamera(t.clone().addScaledVector(d, fitDistance(ROOM_BOX, d, t)), t);
  }

  // 패널에 가려지는 만큼 모형을 보이는 영역 가운데로 옮겨요
  function layoutView() {
    const st = stage.getBoundingClientRect();
    const W = Math.max(1, st.width), H = Math.max(1, st.height);
    let left = 0, right = 0, top = 0, bottom = 0;
    if (isPhone()) {
      top = $('#panel-top').getBoundingClientRect().bottom - st.top;
      if (!sheet.hidden) bottom = st.bottom - sheet.getBoundingClientRect().top;
    } else {
      left = panel.getBoundingClientRect().right - st.left;
      if (!sheet.hidden) right = st.right - sheet.getBoundingClientRect().left;
    }
    left = THREE.MathUtils.clamp(left, 0, W * 0.6); right = THREE.MathUtils.clamp(right, 0, W * 0.6);
    top = THREE.MathUtils.clamp(top, 0, H * 0.5); bottom = THREE.MathUtils.clamp(bottom, 0, H * 0.6);
    const FW = W + left + right, FH = H + top + bottom;
    camera.aspect = FW / FH;
    camera.fov = W / H < 0.9 ? 46 : 34;
    if (left || right || top || bottom) camera.setViewOffset(FW, FH, right, bottom, W, H);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
    const m = 0.04;
    vis = { x0: (left / W) * 2 - 1 + m, x1: ((W - right) / W) * 2 - 1 - m, y0: 1 - ((H - bottom) / H) * 2 + m, y1: 1 - (top / H) * 2 - m };
    invalidate();
  }

  function resize() {
    const W = stage.clientWidth, H = stage.clientHeight;
    renderer.setSize(W, H);
    labelRenderer.setSize(W, H);
    layoutView();
    invalidate();
  }

  // ───────── 동작 ─────────
  function selectUnit(code, level = null) {
    state.selected = code;
    state.level = level;
    state.zone = null;
    if (!state.query.trim()) state.hits = new Set();
    refresh();
    frameBox(unitBox(unitMap.get(code)));
  }
  function closeSheet() {
    state.selected = null;
    state.level = null;
    refresh();
  }
  function focusZone(id) {
    state.zone = id;
    state.selected = null;
    state.level = null;
    state.query = '';
    input.value = '';
    state.results = [];
    state.hits = new Set(unitsOfZone(id).map((R) => R.u.code));
    refresh();
    frameUnits([...state.hits]);
  }

  let frameTimer = 0;
  input.addEventListener('input', () => {
    state.query = input.value;
    state.results = search(state.query);
    state.hits = new Set(state.results.map((it) => it.unit));
    state.zone = null;
    state.collapsed = false;
    refresh();
    clearTimeout(frameTimer);
    if (state.hits.size && !state.selected) frameTimer = setTimeout(() => frameUnits([...state.hits]), 500);
  });
  input.addEventListener('focus', () => { if (state.collapsed) { state.collapsed = false; renderList(); } });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && state.results.length) { const it = state.results[0]; if (isPhone()) { state.collapsed = true; input.blur(); } selectUnit(it.unit, it.level); }
    if (e.key === 'Escape') clearSearch();
  });
  function clearSearch() {
    input.value = '';
    state.query = '';
    state.results = [];
    state.hits = new Set();
    refresh();
  }
  $('#clear').addEventListener('click', () => { clearSearch(); input.focus(); });
  $('#sheet-close').addEventListener('click', closeSheet);
  $('#btn-all').addEventListener('click', () => { state.zone = null; if (!state.query.trim()) state.hits = new Set(); refresh(); overview(); });
  $('#btn-top').addEventListener('click', topView);
  $('#btn-zones').addEventListener('click', () => { state.showZones = !state.showZones; if (state.showZones) { clearSearch(); } renderList(); layoutView(); });
  $('#btn-labels').addEventListener('click', (e) => {
    state.labelMode = LABEL_MODES[(LABEL_MODES.indexOf(state.labelMode) + 1) % LABEL_MODES.length];
    e.currentTarget.textContent = LABEL_TEXT[state.labelMode];
    refresh3D();
  });
  on(document, 'keydown', (e) => { if (e.key === 'Escape' && state.selected && (root.getRootNode().activeElement || document.activeElement) !== input && !root.querySelector('dialog[open]')) closeSheet(); });
  // 숫자 키 1~6: 그 구역으로 카메라 이동 · 0: 전체 보기 (글자 입력 중에는 무시)
  on(document, 'keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || e.isComposing) return;
    if ((e.composedPath()[0] || e.target).closest?.('input, textarea, select, [contenteditable="true"]') || root.querySelector('dialog[open]')) return;
    if (ZONES[e.key]) { e.preventDefault(); focusZone(e.key); }
    else if (e.key === '0') { e.preventDefault(); state.zone = null; if (!state.query.trim()) state.hits = new Set(); refresh(); overview(); }
  });

  // 선반 누르기 (드래그와 구분)
  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  function pickAt(cx, cy) {
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((cx - r.left) / r.width) * 2 - 1, -((cy - r.top) / r.height) * 2 + 1);
    raycaster.setFromCamera(ndc, camera);
    return raycaster.intersectObjects(hitboxes, false)[0];
  }
  let down = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down) return;
    const moved = Math.hypot(e.clientX - down[0], e.clientY - down[1]);
    down = null;
    if (moved > 6) return;
    const hit = pickAt(e.clientX, e.clientY);
    if (hit) selectUnit(hit.object.userData.code);
    else if (state.selected) closeSheet();
  });
  renderer.domElement.addEventListener('pointermove', (e) => {
    if (e.pointerType !== 'mouse' || e.buttons) return;
    renderer.domElement.style.cursor = pickAt(e.clientX, e.clientY) ? 'pointer' : '';
  });
  controls.addEventListener('start', () => { tween = null; });

  // 테마
  function applyTheme() {
    scene.background = new THREE.Color(cssVar('--scene') || '#e3e7e4');
    const a = cssVar('--accent') || '#d9561f';
    accentMats.forEach((m) => m.color.set(a));
    invalidate();
  }
  on(matchMedia('(prefers-color-scheme: dark)'), 'change', applyTheme);

  // 카메라 쪽 벽은 낮춰서 안이 보이게
  const tmp = new THREE.Vector3();
  function updateWalls() {
    let moved = false;
    for (const w of walls) {
      const outside = tmp.copy(camera.position).sub(w.p).dot(w.n) > 0;
      const target = outside ? w.low : 1;
      const next = reduceMotion || Math.abs(target - w.cur) < 0.003 ? target : w.cur + (target - w.cur) * 0.18;
      if (next === w.cur) continue;
      w.cur = next;
      w.g.scale.y = next;
      for (const d of w.decor) d.visible = next > 0.95;
      moved = true;
    }
    if (moved) renderer.shadowMap.needsUpdate = true;
    return moved;
  }

  const easeInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
  // 성능: 카메라 · 벽 · 선택이 바뀐 프레임만 다시 그려요 (가만히 있을 때는 GPU를 쓰지 않아요)
  function frame(now) {
    rafId = requestAnimationFrame(frame);
    if (tween) {
      const k = Math.min(1, (now - tween.start) / tween.ms);
      const e = easeInOut(k);
      camera.position.lerpVectors(tween.p0, tween.p1, e);
      controls.target.lerpVectors(tween.t0, tween.t1, e);
      if (k === 1) tween = null;
      dirty = true;
    }
    controls.update();
    if (updateWalls()) dirty = true;
    if (!dirty) return;
    dirty = false;
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
  }

  const ro = new ResizeObserver(resize);
  ro.observe(stage);
  cleanups.push(() => ro.disconnect());
  applyTheme();
  refresh();
  resize();
  overview(true);
  rafId = requestAnimationFrame(frame);
  initData();

  return () => {
    disposed = true;
    cancelAnimationFrame(rafId);
    for (const fn of cleanups) fn();
    controls.dispose();
    renderer.dispose();
    root.replaceChildren();
  };
}

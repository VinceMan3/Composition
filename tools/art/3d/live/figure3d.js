// The muscle map figure in 3D, drawn live in graphite.
//
//   const fig = await createFigure(canvas, { modelUrl, info, colors })
//   fig.setView({ yaw, pitch, zoom, panX, panY, lift })   (radians, 1 = whole figure)
//   fig.pick(x, y)          -> part id at a point in the canvas (css pixels), or ''
//   fig.select(partId)      red with a sheen; '' clears it
//   fig.setColors(colors)   { ink, shade, tone, light, red } from the look's colors
//   fig.partRect(partId)    -> where a part is on screen now (css pixels), or null
//   fig.render()            draws (the figure also redraws itself when anything changes)
//   fig.snapshot(partId, w, h) -> a canvas with a close-up of a part from its best side
//   fig.dispose()
//
// How it draws: the model is first drawn into hidden buffers that keep, for
// every pixel, how dark the graphite should be (the light comes from the
// viewer's upper left, so the look holds at any angle), how deep in a crease
// it is, which way the muscle's fibers run, which part and which piece it is.
// A second pass reads those buffers and draws in pencil: outlines where
// pieces meet (dark in shadow, lost in the light, with a slight wobble),
// hatching along each muscle, cross-hatching in the darkest places, paper
// tooth, and the red with its sheen on a picked muscle.

import * as THREE from './three.module.js';
import { makeSkeleton } from './skeleton.js';

// ---------- reading the model file ----------
// figure.bin is written by tools/art/3d/export.py: plain arrays, one after another.
// It can also come as base64 text in one or more parts, for hosts that only serve text.
async function readModel(url) {
  let buf;
  if (Array.isArray(url) || url.endsWith('.txt')) {
    const parts = await Promise.all([].concat(url).map(async u => {
      const res = await fetch(u);
      if (!res.ok) throw new Error('model ' + res.status);
      return (await res.text()).trim();
    }));
    const bin = atob(parts.join(''));
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    buf = bytes.buffer;
  } else {
    const res = await fetch(url);
    if (!res.ok) throw new Error('model ' + res.status);
    buf = await res.arrayBuffer();
  }
  const dv = new DataView(buf);
  const magic = dv.getUint32(0, true);
  if (magic !== 0x34504d43) throw new Error('not a figure model');
  const n = dv.getUint32(4, true), m = dv.getUint32(8, true);
  let off = 12;
  const take = (Arr, count) => { const a = new Arr(buf, off, count); off += a.byteLength; return a; };
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(take(Float32Array, n * 3), 3));
  geo.setIndex(new THREE.BufferAttribute(take(Uint32Array, m), 1));
  geo.setAttribute('a_piece', new THREE.BufferAttribute(take(Uint16Array, n), 1));
  geo.setAttribute('normal', new THREE.BufferAttribute(take(Int8Array, n * 4), 4, true));
  geo.setAttribute('a_fiber', new THREE.BufferAttribute(take(Int8Array, n * 4), 4, true));
  geo.setAttribute('a_part', new THREE.BufferAttribute(take(Uint8Array, n), 1));
  geo.setAttribute('a_aoa', new THREE.BufferAttribute(take(Uint8Array, n), 1, true));
  geo.setAttribute('a_aob', new THREE.BufferAttribute(take(Uint8Array, n), 1, true));
  // the skeleton's hold on each point, and each muscle's squeeze
  geo.setAttribute('a_joints', new THREE.BufferAttribute(take(Uint8Array, n * 4), 4));
  geo.setAttribute('a_weights', new THREE.BufferAttribute(take(Uint8Array, n * 4), 4, true));
  geo.setAttribute('a_flex', new THREE.BufferAttribute(take(Int8Array, n * 4), 4));
  geo.setAttribute('a_flexn', new THREE.BufferAttribute(take(Int8Array, n * 4), 4, true));
  geo.setAttribute('a_vac', new THREE.BufferAttribute(take(Int8Array, n * 4), 4));
  geo.computeBoundingBox();
  geo.computeBoundingSphere();
  return geo;
}

// ---------- the first pass: the model into buffers ----------
const GRAIN_K = 260;   // grain across the fibers, per meter, at the starting size

const GBUF_VERT = /* glsl */`
precision highp float;
precision highp sampler2D;
in vec3 position; in vec4 normal;
in float a_part; in float a_piece; in vec4 a_fiber; in float a_aoa; in float a_aob;
in vec4 a_joints; in vec4 a_weights; in vec4 a_flex; in vec4 a_flexn; in vec4 a_vac;
uniform mat4 modelViewMatrix; uniform mat4 projectionMatrix; uniform mat3 normalMatrix;
uniform sampler2D uBones;            // one bone's matrix per row, four texels across
uniform float uFlex[48];              // how hard each part is squeezing (by part number)
uniform float uFlexScale; uniform float uVac; uniform float uVacScale;
out vec3 vN; out vec3 vView; out vec3 vWorld; out vec3 vFib; out vec3 vNo; out vec3 vFo;
flat out float vPart; flat out float vPiece; out float vAoa; out float vAob;
// dual quaternion skinning: each bone is a turn (r) and a move (d)
void boneDQ(float i, out vec4 r, out vec4 d) {
  int k = int(i + 0.5);
  r = texelFetch(uBones, ivec2(0, k), 0);
  d = texelFetch(uBones, ivec2(1, k), 0);
}
void main() {
  // the squeeze and the vacuum change the standing shape first
  float fl = uFlex[int(a_part + 0.5)];
  vec3 p = position + a_flex.xyz * (uFlexScale * fl) + a_vac.xyz * (uVacScale * uVac);
  vec3 nr = normalize(mix(normal.xyz, a_flexn.xyz, clamp(fl, 0.0, 1.0)));
  // then the skeleton carries it into the pose
  vec4 r0, d0, r1, d1, r2, d2, r3, d3;
  boneDQ(a_joints.x, r0, d0); boneDQ(a_joints.y, r1, d1); boneDQ(a_joints.z, r2, d2); boneDQ(a_joints.w, r3, d3);
  float s1 = dot(r0, r1) < 0.0 ? -1.0 : 1.0, s2 = dot(r0, r2) < 0.0 ? -1.0 : 1.0, s3 = dot(r0, r3) < 0.0 ? -1.0 : 1.0;
  vec4 r = r0 * a_weights.x + r1 * (a_weights.y * s1) + r2 * (a_weights.z * s2) + r3 * (a_weights.w * s3);
  vec4 d = d0 * a_weights.x + d1 * (a_weights.y * s1) + d2 * (a_weights.z * s2) + d3 * (a_weights.w * s3);
  float len = length(r);
  r /= len; d /= len;
  vec3 pp = p + 2.0 * cross(r.xyz, cross(r.xyz, p) + r.w * p) + 2.0 * (r.w * d.xyz - d.w * r.xyz + cross(r.xyz, d.xyz));
  vec4 mv = modelViewMatrix * vec4(pp, 1.0);
  vView = mv.xyz;
  // the grain and the head's lines stay fixed to the body, so they use the standing shape
  vWorld = position;
  vec3 rn = nr + 2.0 * cross(r.xyz, cross(r.xyz, nr) + r.w * nr);
  vec3 rf = a_fiber.xyz + 2.0 * cross(r.xyz, cross(r.xyz, a_fiber.xyz) + r.w * a_fiber.xyz);
  vN = normalize(normalMatrix * rn);
  vFib = normalize(normalMatrix * rf);
  vNo = nr; vFo = a_fiber.xyz;
  vPart = a_part; vPiece = a_piece; vAoa = a_aoa; vAob = a_aob;
  gl_Position = projectionMatrix * mv;
}`;

const GBUF_FRAG = /* glsl */`
precision highp float;
in vec3 vN; in vec3 vView; in vec3 vWorld; in vec3 vFib; in vec3 vNo; in vec3 vFo;
flat in float vPart; flat in float vPiece; in float vAoa; in float vAob;
uniform vec3 uHeadC; uniform vec3 uHeadS; uniform float uHeadPiece; uniform float uFar;
uniform float uGrainK; uniform float uGrainMix;
uniform vec3 uKey; uniform float uFill; uniform float uAmb; uniform float uShut; uniform float uLo; uniform float uHi; uniform float uGamma; uniform float uCore; uniform float uCrease;
layout(location = 0) out vec4 g0;   // darkness, light, fiber angle, head lines
layout(location = 1) out vec4 g1;   // part, piece (two bytes), covered
layout(location = 2) out vec4 g2;   // depth (two bytes), graphite grain
// graphite grain fixed to the body's surface, streaked along the muscle fibers,
// so it turns with the figure instead of sitting on the screen
float h3(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float n3(vec3 x) {
  vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(h3(i), h3(i + vec3(1, 0, 0)), f.x), mix(h3(i + vec3(0, 1, 0)), h3(i + vec3(1, 1, 0)), f.x), f.y),
             mix(mix(h3(i + vec3(0, 0, 1)), h3(i + vec3(1, 0, 1)), f.x), mix(h3(i + vec3(0, 1, 1)), h3(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
float grainAt(vec3 q, float K) {
  float a = n3(q * vec3(K, K, K / 7.0));
  float b = n3(q * vec3(K * 2.1, K * 2.1, K / 3.0) + 31.7);
  return a * 0.65 + b * 0.35;
}
void main() {
  vec3 N = normalize(vN);
  if (!gl_FrontFacing) N = -N;
  // light fixed to the viewer: a key from the upper left, a weak fill from the right
  vec3 Lk = normalize(vec3(uKey.x, uKey.y, uKey.z));
  vec3 Lf = normalize(vec3(0.75, -0.05, 0.45));
  float k = max(dot(N, Lk), 0.0);
  float f = max(dot(N, Lf), 0.0);
  float shut = mix(1.0, vAob, uShut);
  float lit = (uAmb + (1.0 - uAmb) * k + uFill * f) * shut;
  // to graphite: 0 lit paper, 1 deepest shadow
  float T = 1.0 - clamp((lit - uLo) / (uHi - uLo), 0.0, 1.0);
  T = pow(T, uGamma);
  float crease = clamp((1.0 - vAoa) * 1.25, 0.0, 1.0);
  float core = exp(-pow((T - 0.58) / 0.16, 2.0)) * uCore;   // the core shadow band
  T = clamp(T + crease * uCrease + core, 0.0, 1.0);
  // which way the fibers run on screen
  vec2 fd = vFib.xy;
  float ang = (length(fd) > 1e-4) ? mod(atan(fd.y, fd.x), 3.14159265) / 3.14159265 : 0.0;
  // the head's construction lines: center, brow and nose, light like a first lay-in
  float head = 0.0;
  if (abs(vPiece - uHeadPiece) < 0.5) {
    vec3 p = (vWorld - uHeadC) / uHeadS;   // -0.5 .. 0.5 across the head
    float w = 0.006;
    float center = 1.0 - smoothstep(w * 0.5, w * 1.6, abs(p.x));
    float front = smoothstep(-0.05, 0.08, p.z);
    float brow = (1.0 - smoothstep(w * 0.5, w * 1.6, abs(p.y - 0.03))) * front * 0.9;
    float nose = (1.0 - smoothstep(w * 0.5, w * 1.6, abs(p.y + 0.23))) * front * 0.7;
    head = max(center * 0.6, max(brow, nose));
  }
  g0 = vec4(T, k, ang, head);
  float pc = floor(vPiece + 0.5);
  g1 = vec4(floor(vPart + 0.5) / 255.0, floor(pc / 256.0) / 255.0, mod(pc, 256.0) / 255.0, 1.0);
  float d = clamp(-vView.z / uFar, 0.0, 1.0) * 255.0;
  // the fiber's frame: two directions across it, one along it
  vec3 F = normalize(vFo);
  vec3 A = normalize(abs(F.y) < 0.9 ? cross(F, vec3(0, 1, 0)) : cross(F, vec3(1, 0, 0)));
  vec3 B = cross(F, A);
  vec3 q = vec3(dot(vWorld, A), dot(vWorld, B), dot(vWorld, F));
  // two sizes of grain, blended as the view zooms, so it keeps the same look up close
  float g = mix(grainAt(q, uGrainK), grainAt(q, uGrainK * 2.0), uGrainMix);
  // fade the grain where it gets finer than the screen can show (edges seen side on)
  float fw = length(fwidth(q.xy)) * uGrainK;
  g = mix(g, 0.5, smoothstep(0.35, 0.8, fw));
  g2 = vec4(floor(d) / 255.0, fract(d), g, 1.0);
}`;

// ---------- the second pass: pencil ----------
const PENCIL_VERT = /* glsl */`
in vec3 position; out vec2 vUv;
void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const PENCIL_FRAG = /* glsl */`
precision highp float;
in vec2 vUv;
uniform sampler2D tG0; uniform sampler2D tG1; uniform sampler2D tG2;
uniform vec2 uRes;          // buffer size in pixels
uniform float uS;           // pencil scale: pixels per unit of the drawing's tuning
uniform float uSel;         // the picked part (0 none)
uniform vec4 uInk; uniform vec4 uShade; uniform vec4 uLight; uniform vec4 uRed; uniform float uTone; uniform float uSoft; uniform float uGrain; uniform float uStroke; uniform float uMaxT;
out vec4 outColor;

float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
vec4 g0At(vec2 px) { return texture(tG0, px / uRes); }
// part, piece, depth, covered
vec4 g1At(vec2 px) {
  vec4 a = texture(tG1, px / uRes), d = texture(tG2, px / uRes);
  return vec4(floor(a.x * 255.0 + 0.5), floor(a.y * 255.0 + 0.5) * 256.0 + floor(a.z * 255.0 + 0.5), (floor(d.x * 255.0 + 0.5) + d.y) / 255.0, a.w);
}
vec4 over(vec4 top, vec4 under) { return top + under * (1.0 - top.a); }

void main() {
  vec2 px = vUv * uRes;
  vec4 a = g0At(px), b = g1At(px);
  float cov = b.w;
  // a slow wander, like a hand, for the lines
  vec2 wob = (vec2(vnoise(px / (40.0 * uS)), vnoise(px / (40.0 * uS) + 17.0)) - 0.5) * 1.2 * uS;
  // ----- lines: where pieces meet, and the outline -----
  float r = max(1.0, uS * 0.9);
  float edge = 0.0, out_ = 0.0, fold = 0.0;
  vec2 q = px + wob;
  vec4 c0 = g1At(q);
  for (int i = 0; i < 8; i++) {
    float t = float(i) * 0.785398;
    vec2 o = vec2(cos(t), sin(t)) * r;
    vec4 c = g1At(q + o);
    if (c.w < 0.5 && c0.w > 0.5 || c.w > 0.5 && c0.w < 0.5) out_ = 1.0;
    else if (c.w > 0.5 && c0.w > 0.5) {
      if (abs(c.y - c0.y) > 0.5) edge = 1.0;
      if (abs(c.z - c0.z) * 400.0 > 1.0) fold = 1.0;   // a fold in front of a far surface
    }
  }
  // the outline is firmer on the side turned away from the light (lower right)
  float Tq = g0At(q).x;
  float Ts = 0.0;
  for (int i = 0; i < 4; i++) { float t = float(i) * 1.5708 + 0.4; Ts += g0At(px + vec2(cos(t), sin(t)) * 3.0 * uS).x; }
  Ts = Ts * 0.25;
  float weight = 0.12 + 0.6 * smoothstep(0.1, 0.75, Ts);
  float inner = max(edge, fold * 0.8) * weight;
  float outline = out_ * (0.62 + 0.38 * smoothstep(0.2, 0.8, Ts)) * 0.72;
  float lines = max(inner, outline);
  // head construction lines
  lines = max(lines, a.w * 0.8);

  // ----- graphite: a soft tone, broken up by grain that is fixed to the body -----
  float T = a.x * cov;
  // a softened tone, so the model's fine surface bumps do not show as noise
  float Tb = T * 2.0;
  for (int i = 0; i < 8; i++) {
    float t = float(i) * 0.785398 + 0.2;
    vec2 o = vec2(cos(t), sin(t)) * 4.5 * uS;
    vec4 bb = g1At(px + o);
    Tb += (bb.w > 0.5 && abs(bb.y - b.y) < 0.5) ? g0At(px + o).x : T;
  }
  Tb /= 10.0;
  float gr = texture(tG2, vUv).z;                 // 0..1, about 0.5 on average
  float gs = (gr - 0.5) * 2.0;
  // in shadow the grain gathers into strokes; in the light it is a faint tooth
  // strokes gather in the half tones; the deepest shadow stays a calm, even tone
  float stroke = smoothstep(0.62 - Tb * 0.35, 0.95 - Tb * 0.35, gr) * smoothstep(0.25, 0.7, Tb) * (1.0 - 0.55 * smoothstep(0.6, 0.95, Tb));
  float hatchInk = stroke * uStroke * cov;
  float ink = clamp(max(lines, hatchInk), 0.0, 1.0);
  float tone = mix(T, Tb, uSoft) * 0.9;
  tone = min(tone, uMaxT);
  tone = clamp(tone * (1.0 + uGrain * gs * (1.0 - 0.5 * smoothstep(0.45, 0.9, Tb))), 0.0, 1.0) * cov;

  // ----- paper tooth: graphite shows the grain in light and middle tones -----
  float grain = (vnoise(px / (1.1 * uS)) - 0.5) * 2.0;
  tone = clamp(tone * (1.0 + 0.13 * (1.0 - smoothstep(0.55, 0.9, tone)) * grain), 0.0, 1.0);
  ink = clamp(ink * (1.0 + 0.1 * grain), 0.0, 1.0);

  // ----- the layers, like the app's: light, red, shading, lines, sheen -----
  bool picked = uSel > 0.5 && abs(b.x - uSel) < 0.5 && cov > 0.5;
  float sel = picked ? 1.0 : 0.0;
  vec4 col = vec4(0.0);
  float litAmt = pow(clamp(1.0 - T * 1.15, 0.0, 1.0), 1.3) * cov;
  col = over(vec4(uLight.rgb * uLight.a * litAmt, uLight.a * litAmt), col);
  if (picked) {
    float Ln = clamp(a.y, 0.0, 1.0);
    vec3 red = uRed.rgb * (0.46 + 0.6 * Ln);
    col = over(vec4(red, 1.0), col);
  }
  float sa = tone * uTone * (1.0 - 0.45 * sel);
  col = over(vec4(uShade.rgb * sa, sa), col);
  float ia = ink * uInk.a * (1.0 - 0.3 * sel);
  col = over(vec4(uInk.rgb * ia, ia), col);
  if (picked) {
    float sheen = smoothstep(0.72, 1.0, a.y) * 0.34;
    col.rgb += sheen * (1.0 - col.rgb) * col.a;
  }
  outColor = col;
}`;

export async function createFigure(canvas, { modelUrl, info, colors = {} } = {}) {
  const geo = await readModel(modelUrl);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: true });
  renderer.setClearColor(0x000000, 0);
  const dpr = Math.min(window.devicePixelRatio || 1, 2.6);
  renderer.setPixelRatio(dpr);

  const box = geo.boundingBox;
  const height = box.max.y - box.min.y;
  // ----- the skeleton: bone matrices go to the shader as a small float picture -----
  const rig = makeSkeleton(info.bones);
  const boneTex = new THREE.DataTexture(rig.mats, 2, rig.n, THREE.RGBAFormat, THREE.FloatType);
  boneTex.needsUpdate = true;
  const flex = new Float32Array(48);
  // the framing follows the pose: the standing box, stretched as far as the bones moved
  const frame = new THREE.Box3().copy(box), boneBox = new THREE.Box3();
  const center = new THREE.Vector3();
  function reframe() {
    rig.box(boneBox);
    frame.min.copy(box.min).add(boneBox.min).sub(rig.restBox.min);
    frame.max.copy(box.max).add(boneBox.max).sub(rig.restBox.max);
    frame.getCenter(center);
  }
  reframe();
  const fitW = () => Math.max(frame.max.x - frame.min.x, frame.max.z - frame.min.z);
  // half the picture's height at zoom 1: the whole figure fits, arms and all
  const half = () => Math.max((frame.max.y - frame.min.y) * 0.56, (fitW() * 0.54) / camera.aspect);
  const camera = new THREE.PerspectiveCamera(16, 1, 0.5, 40);
  const FAR = 40;
  const scene = new THREE.Scene();
  const head = info.head;
  const gmat = new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3,
    vertexShader: GBUF_VERT,
    fragmentShader: GBUF_FRAG,
    side: THREE.DoubleSide,
    uniforms: {
      uHeadC: { value: new THREE.Vector3(...head.center) },
      uHeadS: { value: new THREE.Vector3(...head.size) },
      uHeadPiece: { value: head.piece },
      uGrainK: { value: 300 }, uGrainMix: { value: 0 },
      uFar: { value: FAR },
      uBones: { value: boneTex }, uFlex: { value: flex }, uFlexScale: { value: info.flexScale || 0 },
      uVac: { value: 0 }, uVacScale: { value: info.vacScale || 0 },
      // the light and how it turns into graphite, tuned against the drawn figure
      uKey: { value: new THREE.Vector3(-0.45, 0.52, 0.72) },
      uFill: { value: 0.32 }, uAmb: { value: 0.32 }, uShut: { value: 0.45 }, uLo: { value: 0.36 }, uHi: { value: 0.98 },
      uGamma: { value: 1.1 }, uCore: { value: 0.2 }, uCrease: { value: 0.45 },
    },
  });
  const mesh = new THREE.Mesh(geo, gmat);
  mesh.frustumCulled = false;
  scene.add(mesh);

  let target = null;
  function makeTarget(w, h) {
    if (target) target.dispose();
    target = new THREE.WebGLRenderTarget(w, h, { count: 3, type: THREE.UnsignedByteType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: true });
  }

  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3,
    vertexShader: PENCIL_VERT,
    fragmentShader: PENCIL_FRAG,
    depthTest: false,
    depthWrite: false,
    transparent: false,
    uniforms: {
      tG0: { value: null }, tG1: { value: null }, tG2: { value: null },
      uRes: { value: new THREE.Vector2() }, uS: { value: 1 }, uSel: { value: 0 },
      uInk: { value: new THREE.Vector4() }, uShade: { value: new THREE.Vector4() }, uLight: { value: new THREE.Vector4() },
      uRed: { value: new THREE.Vector4() }, uTone: { value: 1 }, uSoft: { value: 0.6 }, uGrain: { value: 0.52 }, uStroke: { value: 0.48 }, uMaxT: { value: 0.75 },
    },
  }));
  quad.frustumCulled = false;
  const post = new THREE.Scene();
  post.add(quad);
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const view = { yaw: 0, pitch: 0, zoom: 1, panX: 0, panY: 0, lift: 0 };
  let size = { w: 1, h: 1 };
  let selected = 0;
  let queued = false;

  function color(c, fallback) {
    const v = new THREE.Color(c || fallback);
    return v;
  }
  function parseRgba(s, fallback) {
    if (!s) return fallback;
    s = s.trim();
    if (s === 'transparent') return [0, 0, 0, 0];
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (m) {
      const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
      return [p[0] / 255, p[1] / 255, p[2] / 255, p.length > 3 ? p[3] : 1];
    }
    const c = new THREE.Color(s);
    return [c.r, c.g, c.b, 1];
  }
  function setColors(c) {
    const u = quad.material.uniforms;
    const set = (vec, val, fb) => { const [r, g, b, a] = parseRgba(val, fb); vec.set(r, g, b, a); };
    set(u.uInk.value, c.ink, [0.165, 0.165, 0.18, 1]);
    set(u.uShade.value, c.shade, [0.11, 0.11, 0.12, 1]);
    set(u.uLight.value, c.light, [0, 0, 0, 0]);
    set(u.uRed.value, c.red, [0.79, 0.19, 0.17, 1]);
    if (c.tune) for (const [k, v] of Object.entries(c.tune)) {
      const m = gmat.uniforms[k] || u[k];
      if (m) m.value = Array.isArray(v) ? new THREE.Vector3(...v) : v;
    }
    u.uTone.value = c.tone === undefined ? 1 : Number(c.tone);
    // colors are blended in the screen's own color space, like the CSS layers
    queue();
  }

  function placeCamera() {
    const dist = half() / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / view.zoom;
    const t = new THREE.Vector3(center.x + view.panX, center.y + view.panY, center.z);
    const dir = new THREE.Vector3(Math.sin(view.yaw) * Math.cos(view.pitch), Math.sin(view.pitch), Math.cos(view.yaw) * Math.cos(view.pitch));
    camera.position.copy(t).addScaledVector(dir, dist);
    camera.up.set(0, 1, 0);
    camera.lookAt(t);
    // slide the picture up for the card without moving the figure in space
    camera.setViewOffset(size.w, size.h, 0, -view.lift, size.w, size.h);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
  }

  function resize() {
    const w = Math.max(1, canvas.clientWidth), h = Math.max(1, canvas.clientHeight);
    if (w === size.w && h === size.h && target) return;
    size = { w, h };
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    makeTarget(Math.round(w * dpr), Math.round(h * dpr));
  }

  function render() {
    queued = false;
    resize();
    placeCamera();
    renderer.setRenderTarget(target);
    renderer.setClearColor(0x000000, 0);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.setRenderTarget(null);
    const u = quad.material.uniforms;
    u.tG0.value = target.textures[0];
    u.tG1.value = target.textures[1];
    u.tG2.value = target.textures[2];
    u.uRes.value.set(target.width, target.height);
    // the pencil was tuned on a figure 1750 pixels tall; keep its marks in proportion
    const figPx = ((target.height * height) / (2 * half())) * view.zoom;
    u.uS.value = Math.min(Math.max(figPx / 2300, dpr * 0.45), dpr * 1.5);
    // grain size on the body: about the same on screen at any zoom (steps of two, blended)
    const pxPerM = figPx / height;
    const L = Math.log2(Math.max(pxPerM / 1150, 1e-3));
    gmat.uniforms.uGrainK.value = GRAIN_K * Math.pow(2, Math.floor(L));
    gmat.uniforms.uGrainMix.value = L - Math.floor(L);
    u.uSel.value = selected;
    renderer.clear();
    renderer.render(post, postCam);
  }
  // after turning bones or changing squeezes: send them to the shader and redraw
  function posed({ vac = 0, shut = 1 } = {}) {
    rig.update();
    boneTex.needsUpdate = true;
    gmat.uniforms.uVac.value = vac;
    gmat.uniforms.uShut.value = 0.45 * shut;
    reframe();
    queue();
  }
  function queue() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(render);
  }

  const px = new Uint8Array(4);
  function pick(x, y) {
    if (!target) return '';
    const tx = Math.round(x * dpr), ty = Math.round(target.height - 1 - y * dpr);
    renderer.readRenderTargetPixels(target, tx, ty, 1, 1, px, undefined, 1);
    return px[0] > 0 && px[3] > 127 ? info.parts[px[0] - 1] : '';
  }

  // which model piece is at a point (for checking the model; 0 = none)
  function pickPiece(x, y) {
    if (!target) return 0;
    const tx = Math.round(x * dpr), ty = Math.round(target.height - 1 - y * dpr);
    renderer.readRenderTargetPixels(target, tx, ty, 1, 1, px, undefined, 1);
    return px[3] > 127 ? px[1] * 256 + px[2] : 0;
  }

  // where a part sits on screen now: read its pixels from the buffer
  function partRect(partId) {
    if (!target || !partId) return null;
    const id = info.parts.indexOf(partId) + 1;
    const w = target.width, h = target.height;
    const step = 4;
    const sw = Math.ceil(w / step), sh = Math.ceil(h / step);
    const all = new Uint8Array(w * h * 4);
    renderer.readRenderTargetPixels(target, 0, 0, w, h, all, undefined, 1);
    let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let j = 0; j < sh; j++) for (let i = 0; i < sw; i++) {
      const k = ((j * step) * w + i * step) * 4;
      if (all[k + 3] > 127 && all[k] === id) {
        const X = i * step, Y = h - j * step;
        if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y;
      }
    }
    if (x1 < 0) return null;
    return { left: x0 / dpr, top: y0 / dpr, right: x1 / dpr, bottom: y1 / dpr };
  }

  setColors(colors);
  return {
    THREE, renderer, camera, info, view,
    setView(v) { Object.assign(view, v); queue(); },
    getView() { return { ...view }; },
    select(partId) { selected = partId ? info.parts.indexOf(partId) + 1 : 0; queue(); },
    rig, flex, posed, center: () => center.clone(), pick, pickPiece, partRect, setColors, render, queue, resize: () => { resize(); queue(); },
    dispose() { target && target.dispose(); geo.dispose(); renderer.dispose(); },
  };
}

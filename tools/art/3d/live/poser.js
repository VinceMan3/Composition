// Poses: turns plain joint angles (degrees) into bone turns, and moves the
// figure between poses with a squeeze at the end.
//
// A pose (see poses.js):
//   body: { pelvis, spine, neck, head: { bend, side, twist } }
//        bend = forward, side = toward its own left, twist = chest turned to its own left
//   arm:  { l, r, '*': { abd, raise, swing, rot, elbow, pron, wrist, dev, shrug, reach, fist, thumb } }
//        abd = up to the side (degrees from hanging, 90 = level), raise = forward from hanging,
//        swing = a raised arm brought forward, rot = turned outward (thumb back), elbow = bent,
//        pron = forearm turned palm down, wrist = bent toward the palm, dev = toward the thumb,
//        shrug = shoulder up, reach = shoulder forward, fist = 0 open .. 1 tight
//   leg:  { l, r, '*': { flex, abd, rot, knee, ankle, toes } }
//        flex = thigh forward, abd = out to the side, rot = toes out, knee = bent,
//        ankle = toes pointed down, toes = toes bent up
//   flex: { group or part: amount }, vac: 0..1, face: degrees the viewer moves round to
import * as THREE from './three.module.js';

const D = Math.PI / 180;
const X = new THREE.Vector3(1, 0, 0), Y = new THREE.Vector3(0, 1, 0), Z = new THREE.Vector3(0, 0, 1);
const qa = (axis, deg) => new THREE.Quaternion().setFromAxisAngle(axis, deg * D);

export function makePoser(fig, { groups, parts }) {
  const rig = fig.rig;
  const I = name => rig.index(name);
  const restArmDown = {};
  for (const s of ['l', 'r']) {
    const d = rig.dir[I(`upperarm.${s}`)];
    restArmDown[s] = Math.atan2(Math.abs(d.x), -d.y) / D;   // how far out the arm already is standing
  }
  const hinge = (bone, toward) => new THREE.Vector3().crossVectors(rig.dir[bone], toward).normalize();
  const along = bone => rig.dir[bone].clone();

  function quats(spec) {
    const q = rig.q.map(() => new THREE.Quaternion());
    const set = (name, quat) => { const i = I(name); if (i >= 0) q[i].copy(quat); };
    const body = spec.body || {};
    const trunk = (o = {}, k = 1) => qa(Y, (o.twist || 0) * k).multiply(qa(Z, -(o.side || 0) * k)).multiply(qa(X, (o.bend || 0) * k));
    set('pelvis', trunk(body.pelvis));
    // the spine's bend is shared out down its three bones
    const sp = body.spine || {};
    set('spine1', trunk(sp, 0.3)); set('spine2', trunk(sp, 0.35)); set('spine3', trunk(sp, 0.35));
    set('neck', trunk(body.neck)); set('head', trunk(body.head));
    const arms = spec.arm || {}, legs = spec.leg || {};
    for (const s of ['l', 'r']) {
      const m = s === 'l' ? 1 : -1;
      const a = { ...(arms['*'] || {}), ...(arms[s] || {}) };
      // the shoulder girdle
      // the shoulder blade rolls up as the arm rises (about a quarter of the lift), as in a real shoulder
      const lift = (a.abd === undefined ? restArmDown[s] : a.abd) - restArmDown[s];
      const roll = 0.25 * Math.max(0, lift) + 0.12 * Math.max(0, a.raise || 0);
      set(`clavicle.${s}`, qa(Y, -m * (a.reach || 0)).multiply(qa(Z, m * ((a.shrug || 0) + roll))));
      // the upper arm: turned on its own axis, lifted out to the side, forward, then swung forward
      const ua = I(`upperarm.${s}`);
      const abd = lift - roll;
      set(`upperarm.${s}`, qa(Y, -m * (a.swing || 0)).multiply(qa(X, -(a.raise || 0))).multiply(qa(Z, m * abd)).multiply(qa(along(ua), -m * (a.rot || 0))));
      // the elbow bends toward the palm side (forward when standing)
      const fa = I(`forearm.${s}`);
      const pron = a.pron || 0;
      set(`forearm.${s}`, qa(hinge(fa, Z), a.elbow || 0).multiply(qa(along(fa), m * pron * 0.4)));
      set(`twist.${s}`, qa(along(I(`twist.${s}`)), m * pron * 0.6));
      const hb = I(`hand.${s}`);
      set(`hand.${s}`, qa(Z, m * (a.dev || 0)).multiply(qa(hinge(hb, Z), a.wrist || 0)));
      // fingers: curled toward the palm
      const f = a.fist === undefined ? 0.15 : a.fist;
      for (const [name, k] of [['index', 1], ['middle', 1.05], ['ring', 1.1], ['pinky', 1.15]]) {
        const amt = [82, 96, 62];
        for (let j = 1; j <= 3; j++) {
          const b = I(`${name}${j}.${s}`);
          set(`${name}${j}.${s}`, qa(hinge(b, Z), amt[j - 1] * f * k));
        }
      }
      const t = a.thumb === undefined ? f : a.thumb;
      const toward = rig.head[I(`middle2.${s}`)].clone().sub(rig.head[I(`thumb1.${s}`)]).normalize();
      set(`thumb1.${s}`, qa(hinge(I(`thumb1.${s}`), toward), 25 * t));
      set(`thumb2.${s}`, qa(hinge(I(`thumb2.${s}`), toward), 35 * t));
      set(`thumb3.${s}`, qa(hinge(I(`thumb3.${s}`), toward), 45 * t));
      // the leg
      const l = { ...(legs['*'] || {}), ...(legs[s] || {}) };
      set(`thigh.${s}`, qa(Y, m * (l.rot || 0)).multiply(qa(X, -(l.flex || 0))).multiply(qa(Z, m * (l.abd || 0))));
      set(`shin.${s}`, qa(X, l.knee || 0));
      set(`foot.${s}`, qa(X, l.ankle || 0));
      set(`toes.${s}`, qa(X, -(l.toes || 0)));
    }
    return q;
  }

  // how hard each part squeezes: names can be groups or parts
  function flexOf(spec) {
    const out = new Float32Array(48);
    for (const [name, amt] of Object.entries(spec.flex || {})) {
      const list = groups[name] || [name];
      for (const p of list) {
        const i = parts.indexOf(p);
        if (i >= 0) out[i + 1] = Math.max(out[i + 1], amt);
      }
    }
    return out;
  }

  // ----- moving -----
  const cur = { q: rig.q.map(x => x.clone()), flex: new Float32Array(48), vac: 0 };
  let anim = 0, job = null;
  const ease = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  function go(spec, { dur = 900, squeeze = true, onFrame, after } = {}) {
    cancelAnimationFrame(anim);
    const from = { q: cur.q.map(x => x.clone()), flex: cur.flex.slice(), vac: cur.vac };
    const to = { q: quats(spec), flex: flexOf(spec), vac: spec.vac || 0 };
    const t0 = performance.now();
    const shakeBones = ['spine2', 'spine3', 'upperarm.l', 'upperarm.r', 'neck'].map(I);
    const tmp = new THREE.Quaternion();
    job = { spec };
    const step = now => {
      const t = Math.min(1, (now - t0) / dur);
      const e = ease(t);
      for (let i = 0; i < rig.n; i++) cur.q[i].slerpQuaternions(from.q[i], to.q[i], e);
      // the squeeze: hits as the pose lands, with a little shake, then settles a touch softer
      const after_ = Math.max(0, (now - t0 - dur * 0.7) / 1000);
      let hard = 0, shake = 0;
      if (squeeze && to.flex.some(v => v > 0)) {
        hard = after_ <= 0 ? 0 : Math.min(1, after_ / 0.18) * (1 - 0.15 * Math.min(1, Math.max(0, after_ - 0.9) / 0.6));
        shake = after_ > 0 ? Math.exp(-after_ * 2.2) * Math.min(1, after_ / 0.1) : 0;
      }
      for (let i = 0; i < 48; i++) cur.flex[i] = from.flex[i] + (to.flex[i] - from.flex[i]) * e;
      cur.vac = from.vac + (to.vac - from.vac) * e;
      for (let i = 0; i < 48; i++) fig.flex[i] = cur.flex[i] * (0.55 + 0.45 * hard);
      for (let i = 0; i < rig.n; i++) rig.q[i].copy(cur.q[i]);
      if (shake > 0.001) {
        const w = Math.sin(now / 1000 * 2 * Math.PI * 10.5) * shake * 0.7;
        for (const b of shakeBones) rig.q[b].multiply(tmp.setFromAxisAngle(X, w * D * 0.6)).multiply(tmp.setFromAxisAngle(Z, w * D * 0.4));
      }
      fig.posed({ vac: cur.vac, shut: 1 - 0.5 * Math.min(1, poseAmount()) });
      if (onFrame) onFrame(e);
      if (t < 1 || (squeeze && (shake > 0.001 || after_ < 1.6))) anim = requestAnimationFrame(step);
      else if (after) after();
    };
    anim = requestAnimationFrame(step);
  }
  // how far from standing the figure is (0 standing, 1 well posed)
  function poseAmount() {
    let s = 0;
    for (let i = 0; i < rig.n; i++) s += 1 - Math.abs(cur.q[i].w);
    return Math.min(1, s * 4);
  }
  const stand = { body: {}, arm: {}, leg: {} };
  // straight into a pose, fully squeezed (for pictures and checks)
  function snap(spec) {
    cancelAnimationFrame(anim);
    const q = quats(spec), f = flexOf(spec);
    for (let i = 0; i < rig.n; i++) { cur.q[i].copy(q[i]); rig.q[i].copy(q[i]); }
    cur.flex = f; cur.vac = spec.vac || 0;
    for (let i = 0; i < 48; i++) fig.flex[i] = f[i];
    job = { spec };
    fig.posed({ vac: cur.vac, shut: 1 - 0.5 * poseAmount() });
  }
  return { quats, go, snap, stand, relax: (o = {}) => go(stand, { squeeze: false, dur: 700, ...o }), current: () => job && job.spec };
}

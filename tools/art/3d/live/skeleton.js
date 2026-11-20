// The figure's skeleton: bones from figure.json, turned by a pose, giving one
// matrix per bone for the model's points to follow.
//
// Each bone turns about its own start (its joint), in its parent's frame, with
// the standing figure as the starting point (no turn = standing). Angles are
// about the figure's own axes when standing: x to its left, y up, z forward.
import * as THREE from './three.module.js';

const v1 = new THREE.Vector3(), m1 = new THREE.Matrix4(), m2 = new THREE.Matrix4();
const qr = new THREE.Quaternion(), tv = new THREE.Vector3(), sv = new THREE.Vector3();

export function makeSkeleton(bones) {
  const n = bones.length;
  const names = bones.map(b => b.name);
  const head = bones.map(b => new THREE.Vector3(...b.head));
  const tail = bones.map(b => new THREE.Vector3(...b.tail));
  const dir = bones.map((b, i) => tail[i].clone().sub(head[i]).normalize());
  const parent = bones.map(b => b.parent);
  const q = bones.map(() => new THREE.Quaternion());
  const root = new THREE.Vector3();
  const G = bones.map(() => new THREE.Matrix4());
  // per bone, two rows of texels: a dual quaternion (turn, then move) for each bone
  const mats = new Float32Array(n * 8);
  const posHead = bones.map(() => new THREE.Vector3());
  const posTail = bones.map(() => new THREE.Vector3());
  const index = name => names.indexOf(name);

  // the floor, and what can touch it: soles, toes, knees
  const floorY = Math.min(...tail.map(t => t.y), ...head.map(h => h.y)) - 0.012;
  const contacts = [];
  for (const s of ['l', 'r']) {
    const foot = index(`foot.${s}`), toes = index(`toes.${s}`), shin = index(`shin.${s}`);
    contacts.push({ bone: foot, at: 'head', lift: head[foot].y - floorY });   // the heel under the ankle
    contacts.push({ bone: toes, at: 'tail', lift: tail[toes].y - floorY });   // the toe tips
    contacts.push({ bone: toes, at: 'head', lift: head[toes].y - floorY });   // the ball of the foot
    contacts.push({ bone: shin, at: 'head', lift: 0.055 });                   // the front of the knee
  }

  function update({ ground = true } = {}) {
    for (let i = 0; i < n; i++) {
      const p = parent[i];
      if (p < 0) G[i].makeTranslation(head[i].x + root.x, head[i].y + root.y, head[i].z + root.z);
      else G[i].copy(G[p]).multiply(m1.makeTranslation(head[i].x - head[p].x, head[i].y - head[p].y, head[i].z - head[p].z));
      G[i].multiply(m1.makeRotationFromQuaternion(q[i]));
    }
    if (ground) {
      // keep the lowest thing that can touch the floor on the floor
      let low = Infinity;
      for (const c of contacts) {
        v1.set(0, 0, 0);
        if (c.at === 'tail') v1.copy(tail[c.bone]).sub(head[c.bone]);
        v1.applyMatrix4(G[c.bone]);
        low = Math.min(low, v1.y - c.lift);
      }
      const drop = low - floorY;
      if (Math.abs(drop) > 1e-5) {
        m2.makeTranslation(0, -drop, 0);
        for (let i = 0; i < n; i++) G[i].premultiply(m2);
        root.y -= drop;
      }
    }
    for (let i = 0; i < n; i++) {
      m1.copy(G[i]).multiply(m2.makeTranslation(-head[i].x, -head[i].y, -head[i].z));
      m1.decompose(tv, qr, sv);
      // dual quaternion: blends turns without the arm thinning where it twists
      const o = i * 8;
      mats[o] = qr.x; mats[o + 1] = qr.y; mats[o + 2] = qr.z; mats[o + 3] = qr.w;
      mats[o + 4] = 0.5 * (tv.x * qr.w + tv.y * qr.z - tv.z * qr.y);
      mats[o + 5] = 0.5 * (-tv.x * qr.z + tv.y * qr.w + tv.z * qr.x);
      mats[o + 6] = 0.5 * (tv.x * qr.y - tv.y * qr.x + tv.z * qr.w);
      mats[o + 7] = -0.5 * (tv.x * qr.x + tv.y * qr.y + tv.z * qr.z);
      posHead[i].setFromMatrixPosition(G[i]);
      posTail[i].copy(tail[i]).sub(head[i]).applyMatrix4(G[i]);
    }
    return mats;
  }

  // the space the posed bones take up, next to the standing one
  const restBox = new THREE.Box3().setFromPoints([...head, ...tail]);
  function box(out = new THREE.Box3()) {
    out.makeEmpty();
    for (let i = 0; i < n; i++) { out.expandByPoint(posHead[i]); out.expandByPoint(posTail[i]); }
    return out;
  }

  update();
  return { n, names, index, head, tail, dir, parent, q, root, mats, update, box, restBox, posHead, posTail, floorY };
}

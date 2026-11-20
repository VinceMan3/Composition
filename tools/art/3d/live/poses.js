// The poses. Angles in degrees; see poser.js for what each one means.
// '*' sets both sides; l and r (the figure's own left and right) override it.

export const GROUPS = {"chest":["chest-upper","chest-middle","chest-lower"],"front-delts":["front-delts"],"side-delts":["side-delts"],"rear-delts":["rear-delts"],"biceps":["biceps-long","biceps-short","brachialis"],"triceps":["triceps-long","triceps-lateral","triceps-medial"],"forearms":["brachioradialis","wrist-flexors","wrist-extensors"],"traps":["traps-upper","traps-middle","traps-lower"],"upper-back":["rhomboids","infraspinatus","teres-minor","teres-major"],"lats":["lats"],"lower-back":["lower-back"],"abs":["abs"],"obliques":["external-oblique","serratus"],"glutes":["glute-max","glute-med"],"quads":["rectus-femoris","vastus-lateralis","vastus-medialis","sartorius","tfl","hip-flexors"],"hamstrings":["biceps-femoris","semitendinosus","semimembranosus"],"adductors":["adductor-longus","adductor-magnus","gracilis","pectineus"],"calves":["gastroc-medial","gastroc-lateral","soleus"],"shins":["tibialis-anterior"]};

const LEGS_TIGHT = { quads: 0.9, adductors: 0.6, calves: 0.6 };
// arms flexed up, as in a double biceps
const DB_ARM = { abd: 95, rot: 88, elbow: 90, pron: -30, wrist: 15, fist: 0.9, shrug: 6 };
// hands behind the head, elbows up and out
const HEAD_ARM = { abd: 122, swing: 22, rot: 85, elbow: 152, pron: 10, wrist: 10, fist: 0.35 };
// fists on the waist, elbows flared: the lat spread
const LAT_ARM = { abd: 44, swing: 24, rot: -70, elbow: 95, pron: 60, wrist: 25, fist: 0.9, reach: 14 };
// one heel up behind, as in the back poses
const HEEL_UP = { flex: -8, knee: 14, ankle: 38, toes: 45, abd: 2, rot: 6 };

export const POSES = [
  {
    id: 'front-double-biceps', name: 'Front double biceps', set: 'Classic', face: 0,
    body: { spine: { bend: -4 }, head: { bend: -3 } },
    arm: { '*': { ...DB_ARM, swing: 8 } },
    leg: { l: { abd: 7, rot: 14 }, r: { abd: 6, rot: 10, flex: 4, knee: 6 } },
    flex: { biceps: 1, 'front-delts': 0.8, 'side-delts': 0.9, forearms: 0.8, abs: 0.7, lats: 0.5, chest: 0.4, ...LEGS_TIGHT },
  },
  {
    id: 'front-lat-spread', name: 'Front lat spread', set: 'Classic', face: 0,
    body: { spine: { bend: -3 } },
    arm: { '*': LAT_ARM },
    leg: { l: { abd: 7, rot: 14 }, r: { abd: 6, rot: 10, flex: 4, knee: 6 } },
    flex: { lats: 1, 'upper-back': 0.6, chest: 0.6, 'front-delts': 0.6, 'side-delts': 0.6, abs: 0.6, obliques: 0.5, ...LEGS_TIGHT },
  },
  {
    id: 'side-chest', name: 'Side chest', set: 'Classic', face: 70,
    body: { pelvis: { twist: 10 }, spine: { twist: 22, bend: -4 }, head: { twist: 20 } },
    arm: {
      l: { abd: 16, raise: 8, rot: -55, elbow: 96, pron: 20, wrist: 10, fist: 0.9, reach: 8 },
      r: { abd: 6, raise: 26, rot: -55, elbow: 72, pron: 30, wrist: 5, fist: 0.75, reach: 12 },
    },
    leg: { l: { flex: 14, knee: 28, ankle: 32, toes: 40, rot: -12, abd: -2 }, r: { rot: 10, abd: 3 } },
    flex: { chest: 1, biceps: 0.8, 'front-delts': 0.8, 'side-delts': 0.6, forearms: 0.6, abs: 0.5, obliques: 0.5, quads: 0.9, hamstrings: 0.7, calves: 1 },
  },
  {
    id: 'back-double-biceps', name: 'Back double biceps', set: 'Classic', face: 180,
    body: { spine: { bend: -6 }, head: { bend: -6, twist: 15 } },
    arm: { '*': { ...DB_ARM, swing: -6, elbow: 92, reach: -6, shrug: 4 } },
    leg: { l: { abd: 4, rot: 8 }, r: HEEL_UP },
    flex: { biceps: 1, 'rear-delts': 0.9, 'side-delts': 0.8, traps: 0.9, 'upper-back': 1, lats: 0.8, 'lower-back': 0.8, triceps: 0.5,
            hamstrings: 0.9, glutes: 0.9, calves: 1, forearms: 0.7 },
  },
  {
    id: 'back-lat-spread', name: 'Back lat spread', set: 'Classic', face: 180,
    body: { spine: { bend: -2 }, head: { bend: -2 } },
    arm: { '*': { ...LAT_ARM, reach: 18 } },
    leg: { l: { abd: 4, rot: 8 }, r: HEEL_UP },
    flex: { lats: 1, 'upper-back': 0.9, 'rear-delts': 0.6, traps: 0.6, 'lower-back': 0.6, hamstrings: 0.9, glutes: 0.9, calves: 1 },
  },
  {
    id: 'side-triceps', name: 'Side triceps', set: 'Classic', face: 75,
    body: { pelvis: { twist: 8 }, spine: { twist: 18, bend: -3 }, head: { twist: 20 } },
    arm: {
      l: { abd: 4, raise: -6, rot: -10, elbow: 2, pron: 40, wrist: -10, fist: 0.5, reach: -6 },
      r: { abd: 20, raise: -40, rot: -60, elbow: 95, pron: 10, wrist: 10, fist: 0.5, reach: -10 },
    },
    leg: { l: { flex: 14, knee: 28, ankle: 32, toes: 40, rot: -12 }, r: { rot: 10, abd: 3 } },
    flex: { triceps: 1, 'side-delts': 0.7, 'rear-delts': 0.6, chest: 0.6, obliques: 0.6, abs: 0.5, quads: 0.9, hamstrings: 0.7, calves: 1 },
  },
  {
    id: 'vacuum', name: 'Vacuum', set: 'Classic', face: 0, vac: 1,
    body: { spine: { bend: -9 }, head: { bend: -4 } },
    arm: { '*': HEAD_ARM },
    leg: { l: { abd: 5, rot: 10 }, r: { abd: 5, rot: 12, flex: 5, knee: 8 } },
    flex: { lats: 0.8, serratus: 0.9, chest: 0.5, triceps: 0.5, quads: 1, adductors: 0.7, calves: 0.6 },
  },
  {
    id: 'abs-and-thighs', name: 'Abs and thighs', set: 'Classic', face: 0,
    body: { spine: { bend: 9, side: -2 }, head: { bend: 6 } },
    arm: { '*': HEAD_ARM },
    leg: { l: { abd: 5, rot: 8, knee: 4 }, r: { flex: 14, abd: 6, rot: 8, ankle: 16 } },
    flex: { abs: 1, obliques: 1, serratus: 1, quads: 1, adductors: 0.8, calves: 0.6, triceps: 0.4 },
  },
  {
    id: 'arnold-back-double-biceps', name: 'Three-quarter back double biceps', set: 'Golden Era', face: 145,
    body: { pelvis: { twist: -10 }, spine: { twist: -16, bend: -5 }, head: { twist: -45, bend: 4 } },
    arm: { '*': { ...DB_ARM, elbow: 95 }, l: { swing: -12 }, r: { swing: 4 } },
    leg: { l: { flex: 16, knee: 22, rot: 12, ankle: -4 }, r: { flex: -12, knee: 10, ankle: 34, toes: 45, rot: 4 } },
    flex: { biceps: 1, 'rear-delts': 0.9, traps: 0.9, 'upper-back': 1, lats: 0.8, 'lower-back': 0.8, triceps: 0.6, glutes: 0.8, hamstrings: 1, calves: 1, quads: 0.7 },
  },
  {
    id: 'archer', name: 'Archer', set: 'Golden Era', face: 20,
    body: { pelvis: { twist: 10 }, spine: { twist: 14, side: -4, bend: -3 }, head: { twist: 32, bend: -12 } },
    arm: {
      l: { abd: 118, swing: 28, rot: 10, elbow: 2, pron: 80, wrist: -14, fist: 0.05, thumb: 0.1 },
      r: { ...DB_ARM, swing: -4, elbow: 100 },
    },
    leg: { l: { abd: 16, rot: 26, knee: 12 }, r: { abd: 14, rot: 8, flex: -6 } },
    flex: { biceps: 0.9, triceps: 0.7, 'side-delts': 0.9, 'front-delts': 0.8, chest: 0.6, lats: 0.7, abs: 0.7, obliques: 0.6, ...LEGS_TIGHT },
  },
  {
    id: 'mantis', name: 'Mantis', set: 'Golden Era', face: -20,
    body: { pelvis: { twist: -6 }, spine: { twist: -16, bend: 4 }, head: { twist: -20 } },
    arm: {
      r: { abd: 52, swing: 40, rot: 10, elbow: 96, pron: 30, wrist: 10, fist: 0.95, reach: 10 },
      l: { abd: 62, swing: 18, rot: 10, elbow: 92, pron: 30, wrist: 10, fist: 0.95 },
    },
    leg: { l: { abd: 6, rot: 10 }, r: { abd: 8, rot: 16, knee: 8 } },
    flex: { chest: 1, biceps: 0.9, 'front-delts': 1, 'side-delts': 0.8, forearms: 0.9, abs: 0.7, obliques: 0.6, ...LEGS_TIGHT },
  },
  {
    id: 'victory', name: 'Victory', set: 'Golden Era', face: 0,
    body: { spine: { bend: -6 }, head: { bend: -16 } },
    arm: { '*': { abd: 152, swing: 8, rot: 85, elbow: 35, pron: -20, wrist: 15, fist: 0.9 } },
    leg: { '*': { abd: 2, rot: 6 } },
    flex: { lats: 1, 'side-delts': 0.9, biceps: 0.8, triceps: 0.6, abs: 1, obliques: 0.7, serratus: 0.8, chest: 0.6, ...LEGS_TIGHT },
  },
  {
    id: 'atlas', name: 'Atlas', set: 'Golden Era', face: 0,
    body: { pelvis: { bend: 12 }, spine: { bend: 26 }, head: { bend: 14 } },
    arm: { '*': { abd: 78, swing: 18, rot: -10, elbow: 28, pron: 40, wrist: 15, fist: 0.95, reach: 12 } },
    leg: { l: { abd: 62, rot: 35, knee: 2, ankle: 10 }, r: { flex: 62, abd: 32, rot: 32, knee: 105, ankle: -20 } },
    flex: { lats: 1, traps: 1, 'side-delts': 0.9, 'rear-delts': 0.8, biceps: 0.6, forearms: 0.8, quads: 1, adductors: 0.9, calves: 0.8 },
  },
  {
    id: 'abs-and-biceps', name: 'Abs and biceps', set: 'Golden Era', face: 10,
    body: { spine: { bend: 6, side: 4, twist: 6 }, head: { twist: -15 } },
    arm: { l: HEAD_ARM, r: { ...DB_ARM, swing: 10 } },
    leg: { l: { abd: 5, rot: 8 }, r: { abd: 6, rot: 10, flex: 6, knee: 6 } },
    flex: { abs: 1, obliques: 0.9, serratus: 0.9, biceps: 1, 'side-delts': 0.7, chest: 0.6, ...LEGS_TIGHT },
  },
  {
    id: 'kneeling-classic', name: 'Kneeling classic', set: 'Golden Era', face: 200,
    body: { pelvis: { twist: 10 }, spine: { twist: 32, bend: 18, side: 6 }, head: { bend: 20, twist: 10 } },
    arm: {
      r: { abd: 165, swing: 10, rot: 70, elbow: 120, pron: 0, wrist: 10, fist: 0.9 },
      l: { abd: 70, raise: 40, rot: 80, elbow: 110, pron: -20, wrist: 15, fist: 0.95 },
    },
    leg: { l: { flex: 88, knee: 92, abd: 8, rot: 6 }, r: { flex: -12, knee: 100, ankle: -30, toes: 40, abd: 6 } },
    flex: { biceps: 1, 'rear-delts': 0.9, 'upper-back': 0.9, lats: 0.9, traps: 0.8, triceps: 0.7, glutes: 0.8, hamstrings: 0.8, quads: 0.8, calves: 0.7 },
  },
];

// "Flex it": a small move that works each group, held with a squeeze, then back to standing.
// Each one shows the muscle from where it is easiest to see (face).
export const FLEX_MOVES = {
  chest: { face: 0, arm: { '*': { abd: 30, raise: 30, rot: -45, elbow: 85, pron: 30, fist: 0.9, reach: 16 } } },
  'front-delts': { face: 30, arm: { '*': { raise: 80, rot: -10, elbow: 5, pron: 60, fist: 0.8 } } },
  'side-delts': { face: 0, arm: { '*': { abd: 88, rot: -10, elbow: 8, pron: 60, fist: 0.8 } } },
  'rear-delts': { face: 180, arm: { '*': { abd: 80, swing: -28, rot: -20, elbow: 12, pron: 60, fist: 0.8, reach: -10 } } },
  biceps: { face: 0, arm: { '*': { abd: 22, rot: 10, elbow: 125, pron: -70, wrist: 20, fist: 1 } } },
  triceps: { face: 70, arm: { '*': { abd: 10, raise: -18, elbow: 0, pron: 50, wrist: -15, fist: 0.4 } } },
  forearms: { face: 20, arm: { '*': { abd: 20, raise: 20, elbow: 90, pron: -60, wrist: 55, fist: 1 } } },
  traps: { face: 180, arm: { '*': { shrug: 22, abd: 18, fist: 0.8 } } },
  'upper-back': { face: 180, arm: { '*': { abd: 42, swing: -30, rot: -10, elbow: 95, pron: 0, fist: 0.9, reach: -16 } } },
  lats: { face: 180, arm: { '*': { abd: 44, swing: 24, rot: -70, elbow: 95, pron: 60, wrist: 25, fist: 0.9, reach: 14 } } },
  'lower-back': { face: 120, body: { spine: { bend: -16 }, head: { bend: -8 } }, arm: { '*': { abd: 20, raise: -10, fist: 0.5 } } },
  abs: { face: 0, body: { spine: { bend: 22 }, head: { bend: 10 } }, arm: { '*': { abd: 122, swing: 22, rot: 85, elbow: 152, fist: 0.35 } } },
  obliques: { face: 20, body: { spine: { side: 14, twist: 18, bend: 6 } }, arm: { '*': { abd: 122, swing: 22, rot: 85, elbow: 152, fist: 0.35 } } },
  glutes: { face: 160, leg: { r: { flex: -24, knee: 10, rot: 10 } }, body: { pelvis: { bend: 4 } } },
  quads: { face: 20, leg: { r: { flex: 22, knee: 0, rot: 12, ankle: 16 }, l: { knee: 6 } } },
  hamstrings: { face: 150, leg: { r: { flex: -6, knee: 95, ankle: 20 } } },
  adductors: { face: 0, leg: { '*': { abd: -4, rot: 6 } } },
  calves: { face: 160, leg: { '*': { ankle: 32, toes: 40 } } },
  shins: { face: 30, leg: { '*': { ankle: -24 } }, body: { pelvis: { bend: -3 } } },
};

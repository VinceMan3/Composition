/*
  STRENGTH STANDARDS
  Safe to edit. These set where the levels start for the Big Three.

  Each number is a multiple of bodyweight for a lifter at the reference
  bodyweight (men 80 kg / 176 lb, women 60 kg / 132 lb). For other
  bodyweights the app scales them along the DOTS curve, so heavier lifters
  need a smaller multiple and lighter lifters a bigger one, the way meet
  results run.

  The five numbers are where each level begins:
    Novice, Intermediate, Advanced, Elite, World class
  Anything below the first number is Beginner.
*/
export const LEVELS = ['Beginner', 'Novice', 'Intermediate', 'Advanced', 'Elite', 'World class'];

export const STANDARDS = {
  men: {
    referenceKg: 80,
    squat: [1.0, 1.5, 2.0, 2.5, 3.1],
    'bench-press': [0.75, 1.0, 1.4, 1.8, 2.25],
    deadlift: [1.25, 1.75, 2.25, 2.8, 3.4],
  },
  women: {
    referenceKg: 60,
    squat: [0.75, 1.1, 1.5, 2.0, 2.6],
    'bench-press': [0.45, 0.65, 0.9, 1.2, 1.55],
    deadlift: [1.0, 1.35, 1.8, 2.3, 2.9],
  },
};

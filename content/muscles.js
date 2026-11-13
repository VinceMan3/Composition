/*
  MUSCLES
  Safe to edit. Everything the muscle map says about each muscle.

  GROUPS are the 19 muscle groups. PARTS are the 46 pieces you can tap on the
  map; every part belongs to one group.

  For each part:
  id     matches the shape in the drawings (art/muscle-front.svg and
         art/muscle-back.svg). Never change it.
  group  the id of the group it belongs to
  name   what the card calls it
  view   which drawing it shows on: 'front', 'back' or 'both'
  names  the muscle names from the lift list (content/lifts.js, the works
         and helps words) that count toward this part, split by commas.
         One name can count toward several parts: "chest" counts toward all
         three chest parts. A check makes sure every name in the lift list
         lands somewhere.
  does   what it does, in plain words, and a movement that uses it
  fact   a fun fact

  The does and fact lines use double quotes, so apostrophes are fine. If you
  want a quote mark inside one, use curly quotes like “these”.

  PICK is the list of muscles you can choose from when you write in a lift of
  your own, in the order they show.
*/

export const GROUPS = [
  { id: 'chest', name: 'Chest' },
  { id: 'front-delts', name: 'Front delts' },
  { id: 'side-delts', name: 'Side delts' },
  { id: 'rear-delts', name: 'Rear delts' },
  { id: 'biceps', name: 'Biceps' },
  { id: 'triceps', name: 'Triceps' },
  { id: 'forearms', name: 'Forearms' },
  { id: 'traps', name: 'Traps' },
  { id: 'upper-back', name: 'Upper back' },
  { id: 'lats', name: 'Lats' },
  { id: 'lower-back', name: 'Lower back' },
  { id: 'abs', name: 'Abs' },
  { id: 'obliques', name: 'Obliques' },
  { id: 'glutes', name: 'Glutes' },
  { id: 'quads', name: 'Quads' },
  { id: 'hamstrings', name: 'Hamstrings' },
  { id: 'adductors', name: 'Adductors' },
  { id: 'calves', name: 'Calves' },
  { id: 'shins', name: 'Shins' },
];

export const PARTS = [
  // ----- Chest -----
  { id: 'chest-upper', group: 'chest', name: 'Upper chest', view: 'front',
    names: 'chest, upper chest',
    does: "Raises your arm forward and up, the angle you hit on an incline bench or a front raise.",
    fact: "It starts on your collarbone, which is why anatomy books call it the clavicular head." },
  { id: 'chest-middle', group: 'chest', name: 'Middle chest', view: 'front',
    names: 'chest',
    does: "Squeezes your arm across your body, the main mover when you press a bar off your chest or give someone a bear hug.",
    fact: "Monday is International Chest Day, which is why every bench in the gym is taken." },
  { id: 'chest-lower', group: 'chest', name: 'Lower chest', view: 'front',
    names: 'chest, lower chest',
    does: "Pulls your arm down and in from above, like the bottom of a dip, a decline press or a high-to-low cable fly.",
    fact: "Its lowest fibers start on the sheath over your abs, and that bottom edge is the line bodybuilders try to sharpen before a show." },

  // ----- Delts -----
  { id: 'front-delts', group: 'front-delts', name: 'Front delts', view: 'front',
    names: 'front delts',
    does: "Lift your arm forward in front of you, so they work in every press, from bench to overhead.",
    fact: "Pressing hits them so hard that plenty of coaches say most lifters never need to train them on their own." },
  { id: 'side-delts', group: 'side-delts', name: 'Side delts', view: 'both',
    names: 'side delts',
    does: "Lift your arm out to the side, like a lateral raise or reaching for something on a high shelf beside you.",
    fact: "Wide side delts make your shoulders look broad and your waist look small, the heart of the Classic Physique X-frame." },
  { id: 'rear-delts', group: 'rear-delts', name: 'Rear delts', view: 'back',
    names: 'rear delts',
    does: "Pull your arm back and out to the side, like a face pull, a rear delt fly or yanking a lawnmower cord.",
    fact: "They're the delt head everybody skips, which is why “rear delts every day” is a running joke in the gym." },

  // ----- Biceps -----
  { id: 'biceps-long', group: 'biceps', name: 'Long head', view: 'front',
    names: 'biceps',
    does: "Bends your elbow and turns your palm up, and since it crosses the shoulder it also helps raise your arm forward. Incline curls stretch it the most.",
    fact: "It builds the peak of your biceps, the part that pops when you flex for a picture." },
  { id: 'biceps-short', group: 'biceps', name: 'Short head', view: 'front',
    names: 'biceps',
    does: "Bends your elbow and turns your palm up, working hardest with your arm out in front of you, like a preacher curl.",
    fact: "It runs along the inside of your arm and adds the thickness that shows in a front double biceps." },
  { id: 'brachialis', group: 'biceps', name: 'Brachialis', view: 'front',
    names: 'brachialis',
    does: "Bends your elbow whichever way your palm faces, so it does most of the work in hammer and reverse curls.",
    fact: "It sits under your biceps and pushes it up, so building it makes your arm look bigger even when it's relaxed." },

  // ----- Triceps -----
  { id: 'triceps-long', group: 'triceps', name: 'Long head', view: 'both',
    names: 'triceps',
    does: "Straightens your elbow and, because it crosses the shoulder, helps pull your arm down and back. Overhead extensions stretch it the most.",
    fact: "It's the biggest of the three heads, and your triceps make up about two thirds of your upper arm, so if you want big arms, train triceps." },
  { id: 'triceps-lateral', group: 'triceps', name: 'Lateral head', view: 'back',
    names: 'triceps',
    does: "Straightens your elbow, and it works hard in pushdowns and close-grip presses.",
    fact: "It's the horseshoe on the outside of your arm that shows up in a side triceps pose." },
  { id: 'triceps-medial', group: 'triceps', name: 'Medial head', view: 'both',
    names: 'triceps',
    does: "Straightens your elbow in every press and pushdown, and it's on the job even when the weight is light.",
    fact: "Most of it hides under the other two heads, with only a small strip showing just above your elbow." },

  // ----- Forearms -----
  { id: 'brachioradialis', group: 'forearms', name: 'Brachioradialis', view: 'both',
    names: 'forearms',
    does: "Bends your elbow when your thumb points up, like a hammer curl or lifting a mug to your mouth.",
    fact: "It's the thick muscle on top of your forearm, and it starts way up on your upper arm, above the elbow." },
  { id: 'wrist-flexors', group: 'forearms', name: 'Wrist flexors', view: 'both',
    names: 'forearms',
    does: "Curl your wrist and fingers toward your palm, so they hang onto the bar in a deadlift and work in wrist curls.",
    fact: "Grip strength is one of the simplest health checks doctors have, and a strong grip is linked to a longer life." },
  { id: 'wrist-extensors', group: 'forearms', name: 'Wrist extensors', view: 'back',
    names: 'forearms',
    does: "Lift the back of your hand and keep your wrist straight while you grip, like a reverse curl or swinging a hammer.",
    fact: "Tennis elbow is these tendons worn out where they attach at the outside of your elbow, and you don't have to play tennis to get it." },

  // ----- Traps -----
  { id: 'traps-upper', group: 'traps', name: 'Upper traps', view: 'both',
    names: 'traps',
    does: "Shrug your shoulders up and help tip your shoulder blades so you can reach overhead, like a shrug or carrying heavy bags.",
    fact: "Heavy deadlifts and farmer's carries build them as well as shrugs, which is why so many strongmen look like they have no neck." },
  { id: 'traps-middle', group: 'traps', name: 'Middle traps', view: 'back',
    names: 'traps',
    does: "Pull your shoulder blades together, like the squeeze at the top of a row.",
    fact: "The trapezius is named for its shape: both sides together make a big trapezoid, or a kite, across your back." },
  { id: 'traps-lower', group: 'traps', name: 'Lower traps', view: 'back',
    names: 'traps',
    does: "Pull your shoulder blades down and help turn them upward so your arms can go overhead, like a Y-raise or the top of an overhead press.",
    fact: "Weak lower traps are a common reason shoulders feel cranky overhead, which is why physical therapists love handing out Y-raises." },

  // ----- Upper back -----
  { id: 'rhomboids', group: 'upper-back', name: 'Rhomboids', view: 'back',
    names: 'rhomboids, upper back',
    does: "Pull your shoulder blades in toward your spine, the squeeze at the end of a row or when you sit up tall.",
    fact: "They sit under your traps, so you never see them, but they help carve that thick groove down the middle of a big back." },
  { id: 'infraspinatus', group: 'upper-back', name: 'Infraspinatus', view: 'back',
    names: 'rear delts, upper back',
    does: "Turns your arm outward and helps hold the ball of your shoulder in its socket, like a face pull or a backhand swing.",
    fact: "It's one of the four rotator cuff muscles, and in a lean back double biceps you can see it bulge across the shoulder blade." },
  { id: 'teres-minor', group: 'upper-back', name: 'Teres minor', view: 'back',
    names: 'rear delts, upper back',
    does: "Turns your arm outward with the infraspinatus and keeps your shoulder steady when you press or throw.",
    fact: "Its name is Latin for “the smaller round one,” and it's another of the four rotator cuff muscles." },
  { id: 'teres-major', group: 'upper-back', name: 'Teres major', view: 'back',
    names: 'lats, upper back',
    does: "Pulls your arm down and back and turns it inward, the same job as your lats, so it works in pull-ups and rows.",
    fact: "It's nicknamed the lat's little helper, and even though its name sounds like one, it's not part of the rotator cuff." },

  // ----- Lats -----
  { id: 'lats', group: 'lats', name: 'Lats', view: 'both',
    names: 'lats',
    does: "Pull your arm down and back toward your hip, the way you do in a pull-up, a row or climbing a rope.",
    fact: "They're the broadest muscle in your body, running from your upper arm down to your lower back and hips." },

  // ----- Lower back -----
  { id: 'lower-back', group: 'lower-back', name: 'Spinal erectors', view: 'back',
    names: 'lower back',
    does: "Keep your spine straight and stand you up tall, holding your back flat in a squat or deadlift and pulling you up out of a bend.",
    fact: "The “Christmas tree” at the bottom of a bodybuilder's back is mostly these, and heavy deadlifts are what grow it." },

  // ----- Abs -----
  { id: 'abs', group: 'abs', name: 'Abs', view: 'front',
    names: 'abs',
    does: "Curl your ribs toward your hips and brace your trunk, which protects your spine when you squat, deadlift or take a body shot.",
    fact: "A six-pack is one long muscle crossed by bands of tendon, and how many boxes you get is set by your genes, not your training." },

  // ----- Obliques -----
  { id: 'external-oblique', group: 'obliques', name: 'External oblique', view: 'both',
    names: 'obliques',
    does: "Twists your trunk and bends it to the side, like throwing a hook, swinging a bat or holding a side plank.",
    fact: "Its fibers run the same way your fingers point when you slide your hands into your front pockets." },
  { id: 'serratus', group: 'obliques', name: 'Serratus', view: 'front',
    names: 'serratus',
    does: "Pulls your shoulder blade forward around your ribs, like the end of a punch or the top of a push-up.",
    fact: "It's called the boxer's muscle because it drives a punch through, and when you're lean it shows as finger-like ridges along your ribs." },

  // ----- Glutes -----
  { id: 'glute-max', group: 'glutes', name: 'Glute max', view: 'back',
    names: 'glutes',
    does: "Drives your hips forward and straightens you up, the power behind standing out of a squat, locking out a deadlift or sprinting uphill.",
    fact: "It's the biggest muscle in your body." },
  { id: 'glute-med', group: 'glutes', name: 'Glute med', view: 'back',
    names: 'glutes',
    does: "Lifts your leg out to the side and keeps your hips level whenever you stand on one leg, which happens with every step you walk or run.",
    fact: "When it's weak, the opposite hip drops as you walk, a pattern doctors call a Trendelenburg gait." },

  // ----- Quads -----
  { id: 'rectus-femoris', group: 'quads', name: 'Rectus femoris', view: 'front',
    names: 'quads',
    does: "Straightens your knee and lifts your thigh, since it's the one quad that crosses your hip too. It works in squats, leg extensions and kicking a ball.",
    fact: "Its fibers run in a feather pattern, which packs in more muscle and more force for its size." },
  { id: 'vastus-lateralis', group: 'quads', name: 'Vastus lateralis', view: 'both',
    names: 'quads',
    does: "Straightens your knee, and as the biggest quad it does a lot of the work in squats, leg presses and climbing stairs.",
    fact: "It builds the outer sweep of your thigh, the curve physique judges look for from the front." },
  { id: 'vastus-medialis', group: 'quads', name: 'Vastus medialis', view: 'front',
    names: 'quads',
    does: "Straightens your knee and helps keep your kneecap tracking straight, so it works in every squat, lunge and leg extension.",
    fact: "Lifters call it the teardrop, after the shape it makes just above the inside of your knee." },
  { id: 'sartorius', group: 'quads', name: 'Sartorius', view: 'front',
    names: 'hip flexors',
    does: "Helps bend your hip and knee and turn your thigh out, the move you make to sit cross-legged.",
    fact: "It's the longest muscle in your body, and its name comes from the Latin for tailor, since tailors used to sit cross-legged to sew." },
  { id: 'tfl', group: 'quads', name: 'TFL', view: 'front',
    names: 'hip flexors',
    does: "Helps lift your thigh forward and out to the side, and steadies your hip and knee through the IT band when you walk or run.",
    fact: "Its full name is tensor fasciae latae, which roughly means “the tightener of the thigh's wrapping.”" },
  { id: 'hip-flexors', group: 'quads', name: 'Hip flexors', view: 'front',
    names: 'hip flexors',
    does: "Lift your knee toward your chest, like a hanging leg raise, a sprint or climbing stairs.",
    fact: "In a cow, the psoas is the tenderloin, the cut that filet mignon comes from." },

  // ----- Hamstrings -----
  { id: 'biceps-femoris', group: 'hamstrings', name: 'Biceps femoris', view: 'back',
    names: 'hamstrings',
    does: "Bends your knee and pulls your thigh back from the outside of the back of your leg, like a leg curl, an RDL or a sprint.",
    fact: "It's the hamstring sprinters pull most often, usually right at top speed." },
  { id: 'semitendinosus', group: 'hamstrings', name: 'Semitendinosus', view: 'back',
    names: 'hamstrings',
    does: "Bends your knee, pulls your thigh back and turns your shin in, working in leg curls, RDLs and good mornings.",
    fact: "Its long tendon is a favorite of surgeons rebuilding a torn ACL." },
  { id: 'semimembranosus', group: 'hamstrings', name: 'Semimembranosus', view: 'back',
    names: 'hamstrings',
    does: "Bends your knee, pulls your thigh back and turns your shin in, from underneath the semitendinosus on the inside of your thigh.",
    fact: "It's named for the flat, membrane-like tendon at its top end." },

  // ----- Adductors -----
  { id: 'adductor-longus', group: 'adductors', name: 'Adductor longus', view: 'front',
    names: 'adductors',
    does: "Pulls your thigh in toward the middle, like squeezing a ball between your knees or pushing off in a side shuffle.",
    fact: "It's the classic groin pull in hockey and soccer." },
  { id: 'adductor-magnus', group: 'adductors', name: 'Adductor magnus', view: 'back',
    names: 'adductors',
    does: "Pulls your thigh in and, with a part that works like a hamstring, drives your hips up out of the bottom of a squat.",
    fact: "It's one of the biggest muscles in your body, bigger than any one of your hamstrings." },
  { id: 'gracilis', group: 'adductors', name: 'Gracilis', view: 'both',
    names: 'adductors',
    does: "Pulls your thigh in and helps bend your knee, running in a thin strap down the inside of your thigh.",
    fact: "Its name is Latin for slender, and surgeons sometimes borrow it to rebuild other muscles because you can spare it." },
  { id: 'pectineus', group: 'adductors', name: 'Pectineus', view: 'front',
    names: 'adductors',
    does: "Pulls your thigh in and forward, helping lift your knee and squeeze your legs together.",
    fact: "Its name comes from the Latin for comb, after the ridge on your pubic bone it starts from." },

  // ----- Calves -----
  { id: 'gastroc-medial', group: 'calves', name: 'Inner calf', view: 'both',
    names: 'calves',
    does: "Points your toes and lifts your heel, like a standing calf raise, a jump or pushing off in a sprint. It works best with your knee straight.",
    fact: "The inner head is the bigger one and hangs lower, which gives a big calf its diamond shape from behind." },
  { id: 'gastroc-lateral', group: 'calves', name: 'Outer calf', view: 'both',
    names: 'calves',
    does: "Lifts your heel with the inner head and helps bend your knee, so it works in calf raises, jumping and running.",
    fact: "Calves are famously stubborn, and lifters love to joke that you're either born with them or you're not." },
  { id: 'soleus', group: 'calves', name: 'Soleus', view: 'both',
    names: 'calves',
    does: "Raises your heel when your knee is bent, which is why seated calf raises hit it hardest, and it keeps you from tipping forward while you stand.",
    fact: "It's called your “second heart” because squeezing it pushes blood from your legs back up toward your heart." },

  // ----- Shins -----
  { id: 'tibialis-anterior', group: 'shins', name: 'Tibialis anterior', view: 'front',
    names: 'shins',
    does: "Pulls your toes up toward your shin, so your foot clears the ground on every step and your heel lands softly when you run.",
    fact: "If it stops working, the foot slaps the ground with each step, a problem called foot drop." },
];

export const PICK = [
  'Chest', 'Upper chest', 'Front delts', 'Side delts', 'Rear delts',
  'Biceps', 'Brachialis', 'Triceps', 'Forearms',
  'Traps', 'Upper back', 'Lats', 'Lower back',
  'Abs', 'Obliques', 'Serratus',
  'Glutes', 'Quads', 'Hip flexors', 'Hamstrings', 'Adductors', 'Calves', 'Shins',
];

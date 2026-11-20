"""Which model muscles make up each of the app's 46 parts. Shared by build.py and export.py."""

# Model muscle names (without .l / .r) for each of our parts.
PART = {
    'chest-upper': ['Clavicular head of pectoralis major muscle'],
    'chest-middle': ['Sternocostal head of pectoralis major muscle'],
    'chest-lower': ['(Abdominal part of pectoralis major muscle)'],
    'front-delts': ['Clavicular part of deltoid muscle'],
    'side-delts': ['Acromial part of deltoid muscle'],
    'rear-delts': ['Scapular spinal part of deltoid muscle'],
    'biceps-long': ['Long head of biceps brachii'],
    'biceps-short': ['Short head of biceps brachii'],
    'brachialis': ['Brachialis muscle'],
    'triceps-long': ['Long head of triceps brachii'],
    'triceps-lateral': ['Lateral head of triceps brachii'],
    'triceps-medial': ['Medial head of triceps brachii', 'Anconeus muscle'],
    'brachioradialis': ['Brachioradialis muscle'],
    'wrist-flexors': ['Flexor carpi radialis', 'Palmaris longus muscle', 'Humeral head of flexor carpi ulnaris',
                      'Ulnar head of flexor carpi ulnaris', 'Superficial head of pronator teres', 'Deep head of pronator teres',
                      'Humero-ulnar head of flexor digitorum superficialis', 'Radial head of flexor digitorum superficialis',
                      'Flexor digitorum profundus', 'Flexor pollicis longus'],
    'wrist-extensors': ['Extensor carpi radialis longus', 'Extensor carpi radialis brevis', 'Extensor digitorum',
                        'Extensor digiti minimi', 'Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris',
                        'Abductor pollicis longus', 'Extensor pollicis brevis', 'Extensor pollicis longus', 'Extensor indicis'],
    # The model's names for the top and bottom of the trapezius come out
    # swapped (its "descending" piece sits low on the back), so these follow
    # where each piece really is.
    'traps-upper': ['Ascending part of trapezius muscle'],
    'traps-middle': ['Transverse part of trapezius muscle'],
    'traps-lower': ['Descending part of trapezius muscle'],
    'rhomboids': ['Rhomboid major muscle', 'Rhomboid minor muscle'],
    'infraspinatus': ['Infraspinatus muscle'],
    'teres-minor': ['Teres minor muscle'],
    'teres-major': ['Teres major muscle'],
    'lats': ['Latissimus dorsi muscle'],
    'lower-back': ['Iliocostalis lumborum muscle', 'Iliocostalis thoracis muscle', 'Longissimus thoracis muscle',
                   'Spinalis thoracis muscle', 'Multifidus lumborum muscle', 'Multifidus thoracis muscle'],
    'abs': ['Rectus abdominis muscle', 'Linea alba', 'Pyramidalis muscle'],
    'external-oblique': ['External abdominal oblique muscle'],
    'serratus': ['Serratus anterior muscle'],
    'glute-max': ['Gluteus maximus muscle'],
    'glute-med': ['Gluteus medius muscle'],
    'rectus-femoris': ['Rectus femoris muscle'],
    'vastus-lateralis': ['Vastus lateralis muscle'],
    'vastus-medialis': ['Vastus medialis muscle'],
    'sartorius': ['Sartorius muscle'],
    'tfl': ['Tensor fasciae latae'],
    'hip-flexors': ['Iliacus muscle', 'Psoas major'],
    'biceps-femoris': ['Long head of biceps femoris', 'Short head of biceps femoris'],
    'semitendinosus': ['Semitendinosus muscle'],
    'semimembranosus': ['Semimembranosus muscle'],
    'adductor-longus': ['Adductor longus', 'Adductor brevis'],
    'adductor-magnus': ['Adductor magnus', '(Adductor minimus)'],
    'gracilis': ['Gracilis muscle'],
    'pectineus': ['Pectineus muscle'],
    'gastroc-medial': ['Medial head of gastrocnemius'],
    'gastroc-lateral': ['Lateral head of gastrocnemius'],
    'soleus': ['Soleus muscle'],
    'tibialis-anterior': ['Tibialis anterior muscle'],
}
ORDER = list(PART)
BY_NAME = {n: p for p, ns in PART.items() for n in ns}


def base(n):
    """A model name without its .l / .r side."""
    return n.rsplit('.', 1)[0] if n.rsplit('.', 1)[-1] in ('l', 'r') else n

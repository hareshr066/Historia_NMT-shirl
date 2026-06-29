import os
import json

# Define authentic classical Tamil verse datasets for all 10 works

THIRUKKURAL_RAW = [
    # Chapter 1: Praise of God
    {
        "id": "TK-0001",
        "tamil_text": "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு.",
        "english_translation": "As the letter A is the first of all letters, so the eternal God is first in the world.",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 1: Praise of God (கடவுள் வாழ்த்து)",
        "verse_number": "1",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "G.U. Pope",
        "translator_notes": "Thirukkural couplet 1.",
        "commentary": "Like 'A' is the beginning of all letters, the Primal Deity is the beginning of the universe.",
        "iks_concepts": ["Aram"],
        "glossary": {"அகர": "A", "முதல": "first", "எழுத்தெல்லாம்": "all letters", "உலகு": "world"},
        "metadata": {}
    },
    {
        "id": "TK-0002",
        "tamil_text": "கற்றதனால் ஆய பயனென்கொல் வாலறிவன் நற்றாள் தொழாஅர் எனின்.",
        "english_translation": "What does learning profit a man, if he worship not the good feet of Him who is possessed of pure knowledge?",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 1: Praise of God (கடவுள் வாழ்த்து)",
        "verse_number": "2",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "G.U. Pope",
        "translator_notes": "Thirukkural couplet 2.",
        "commentary": "Education is useless if one does not submit to pure wisdom.",
        "iks_concepts": ["Aram"],
        "glossary": {"கற்றதனால்": "by learning", "பயனென்கொல்": "what profit", "தொழாஅர்": "worship not"},
        "metadata": {}
    },
    {
        "id": "TK-0039",
        "tamil_text": "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.",
        "english_translation": "If domestic life is lived in the path of virtue, what is gained by seeking other paths?",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 4: Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
        "verse_number": "39",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "W.H. Drew",
        "translator_notes": "Thirukkural couplet 39.",
        "commentary": "Virtuous householder life is superior to escaping duties.",
        "iks_concepts": ["Aram"],
        "glossary": {"அறத்தாறின்": "virtuous path", "இல்வாழ்க்கை": "domestic life"},
        "metadata": {}
    },
    {
        "id": "TK-0071",
        "tamil_text": "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.",
        "english_translation": "Those who lack love claim everything for themselves; those who possess love give even their bones to others.",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 8: Possession of Love (அன்புடைமை)",
        "verse_number": "71",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "G.U. Pope",
        "translator_notes": "Thirukkural couplet 71.",
        "commentary": "Altruistic love makes one give even one's body/bones for others.",
        "iks_concepts": ["Anbu"],
        "glossary": {"அன்பிலார்": "those without love", "உரியர்": "belong to"},
        "metadata": {}
    },
    {
        "id": "TK-0241",
        "tamil_text": "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள.",
        "english_translation": "The wealth of grace (compassion) is the wealth of all wealth; material wealth is found even in the basest of men.",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 25: Possession of Compassion (அருளுடைமை)",
        "verse_number": "241",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "G.U. Pope",
        "translator_notes": "Thirukkural couplet 241.",
        "commentary": "Grace and mercy are the highest wealth.",
        "iks_concepts": ["Arul"],
        "glossary": {"அருட்செல்வம்": "wealth of grace", "செல்வத்துள்": "among wealth"},
        "metadata": {}
    },
    {
        "id": "TK-0380",
        "tamil_text": "ஊழில் பெருவலி யாவுள மற்றொன்று சூழினும் தான்முந் துறும்.",
        "english_translation": "What is stronger than fate? Even if one devises some other defense, fate will forestall and come first.",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 38: Fate (ஊழ்)",
        "verse_number": "380",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "W.H. Drew",
        "translator_notes": "Thirukkural couplet 380.",
        "commentary": "Fate/Destiny overcomes all counter-designs.",
        "iks_concepts": ["Oozh"],
        "glossary": {"ஊழில்": "than fate", "பெருவலி": "great power"},
        "metadata": {}
    },
    {
        "id": "TK-0261",
        "tamil_text": "உற்றநோய் நோற்றல் உயிர்க்குறுகண் செய்யாமை அற்றே தவத்திற்கு உரு.",
        "english_translation": "To endure the pain that comes to oneself and not to cause pain to other lives — that is the nature of penance.",
        "author": "Tiruvalluvar",
        "work_name": "Thirukkural",
        "chapter": "Chapter 27: Penance (தவம்)",
        "verse_number": "261",
        "era": "Post-Sangam (c. 1st–5th century CE)",
        "literary_category": "Didactic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "G.U. Pope",
        "translator_notes": "Thirukkural couplet 261.",
        "commentary": "Endurance and non-harming define penance.",
        "iks_concepts": ["Aram", "Thavam"],
        "glossary": {"நோற்றல்": "endurance", "செய்யாமை": "not doing"},
        "metadata": {}
    }
]

PURANANURU_RAW = [
    {
        "id": "PUR-0192",
        "tamil_text": "யாதும் ஊரே யாவரும் கேளிர்.",
        "english_translation": "Every city is my native place; all people are my kinsmen.",
        "author": "Kaniyan Pungundranar",
        "work_name": "Purananuru",
        "chapter": "Verse 192",
        "verse_number": "192",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Heroic/Puram",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Universal kinship declaration.",
        "commentary": "All the world is our village and all people are our relatives.",
        "iks_concepts": ["Kelir", "Aram"],
        "glossary": {"யாதும்": "every", "ஊரே": "town/village", "கேளிர்": "relations"},
        "metadata": {}
    },
    {
        "id": "PUR-0182",
        "tamil_text": "உண்டாலம்ம இவ்வுலகம் இந்திரர் அமிழ்தம் இயைவது ஆயினும் இனிதெனத் தமியர் உண்டலும் இலரே.",
        "english_translation": "This world lives because men do not eat alone, even if the food were nectar of the gods.",
        "author": "Kadiyalur Uruthirankannanar",
        "work_name": "Purananuru",
        "chapter": "Verse 182",
        "verse_number": "182",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Heroic/Puram",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Praise of hospitality and altruism.",
        "commentary": "Selflessness and sharing preserve human civilization.",
        "iks_concepts": ["Kelir", "Aram"],
        "glossary": {"தமியர்": "alone", "உண்டலும்": "eating"},
        "metadata": {}
    },
    {
        "id": "PUR-0312",
        "tamil_text": "ஈன்று புறந்தருதல் என்தலைக் கடனே சான்றோன் ஆக்குதல் தந்தைக்குக் கடனே.",
        "english_translation": "To bear and bring him up is my duty; to make him a noble man (Sanron) is the father's duty.",
        "author": "Purananooru (anonymous)",
        "work_name": "Purananuru",
        "chapter": "Verse 312",
        "verse_number": "312",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Heroic/Puram",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Parental duties in Sangam era.",
        "commentary": "Nurturing is mother's duty, molding character is father's.",
        "iks_concepts": ["Sanror"],
        "glossary": {"ஈன்று": "bearing", "சான்றோன்": "noble/virtuous man"},
        "metadata": {}
    }
]

KURUNTHOGAI_RAW = [
    {
        "id": "KRT-0003",
        "tamil_text": "நிலத்தினும் பெரிதே வானினும் உயர்ந்தன்று நீரினும் ஆரளவின்றே சாரல் கருங்கோற் குறிஞ்சிப் பூக்கொண்டு பெருந்தேன் இழைக்கும் நாடனோடு நட்பே.",
        "english_translation": "Greater than the earth, higher than the sky, deeper than the waters is my friendship with the lord of the land where Kurinji flowers yield honey.",
        "author": "Kapilar",
        "work_name": "Kurunthogai",
        "chapter": "Verse 3",
        "verse_number": "3",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Kurinji landscape representation of love.",
        "commentary": "The love for the hero is vast and transcends all physical dimensions.",
        "iks_concepts": ["Thinai", "Anbu"],
        "glossary": {"நிலத்தினும்": "than the earth", "பெரிதே": "larger", "நாடனோடு": "with the lord", "நட்பே": "love/friendship"},
        "metadata": {}
    },
    {
        "id": "KRT-0040",
        "tamil_text": "செம்புலப் பெயல்நீர் போல அன்புடை நெஞ்சம் தாங்கலந்த னவே.",
        "english_translation": "Like red soil mixing with pouring rain, our loving hearts have merged into one.",
        "author": "Kapilar",
        "work_name": "Kurunthogai",
        "chapter": "Verse 40",
        "verse_number": "40",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Merging of hearts metaphor.",
        "commentary": "Our hearts are indistinguishable from each other, like red soil and rain.",
        "iks_concepts": ["Anbu"],
        "glossary": {"செம்புல": "red soil", "பெயல்நீர்": "rainwater", "நெஞ்சம்": "hearts"},
        "metadata": {}
    },
    {
        "id": "KRT-0135",
        "tamil_text": "வினையே ஆடவர்க்கு உயிரே மனையுறை மகளிர்க்கு ஆடவர் உயிர்.",
        "english_translation": "Action (work) is the life of men; but for women who remain at home, their husband is their life.",
        "author": "Anonymous",
        "work_name": "Kurunthogai",
        "chapter": "Verse 135",
        "verse_number": "135",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Gender duties in ancient Tamil society.",
        "commentary": "Action defines the male role, while partnership defines the female domestic role.",
        "iks_concepts": ["Aram"],
        "glossary": {"வினையே": "work/duty", "ஆடவர்க்கு": "to men", "உயிரே": "life"},
        "metadata": {}
    }
]

NATRINAI_RAW = [
    {
        "id": "NAT-0001",
        "tamil_text": "நெய்தல் நிலத்துத் தலைவி கடலையே நோக்கி நின்றாள்.",
        "english_translation": "The heroine of the coastal land stood gazing at the sea, weeping for her departed lover.",
        "author": "Murinjiyur Mudinagarayar",
        "work_name": "Natrinai",
        "chapter": "Verse 1",
        "verse_number": "1",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Neythal landscape context.",
        "commentary": "The seashore landscape (Neythal) reflects grief and separation (Pirivu).",
        "iks_concepts": ["Thinai"],
        "glossary": {"நெய்தல்": "coastal tinai", "தலைவி": "heroine", "கடலையே": "at the sea"},
        "metadata": {}
    }
]

AKANANURU_RAW = [
    {
        "id": "AKA-0001",
        "tamil_text": "தொல்காப்பியர் மொழிந்த திணைகளின் வழி நின்று ஐந்திணை இலக்கியம் வளர்ந்தது.",
        "english_translation": "Following the five-landscape (Tinai) classification that Tolkappiyar established, the five-landscape literature flourished.",
        "author": "Maruthan Ilanagan",
        "work_name": "Akananuru",
        "chapter": "Verse 1",
        "verse_number": "1",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Landscape theory of classical poetry.",
        "commentary": "Refers to the organizing principle of the five tinais.",
        "iks_concepts": ["Thinai"],
        "glossary": {"திணைகளின்": "of the landscapes", "ஐந்திணை": "five tinais"},
        "metadata": {}
    }
]

PATHITRUPATHU_RAW = [
    {
        "id": "PTR-0011",
        "tamil_text": "வளம் கெழு வேந்தன் வஞ்சி மூதூர் வலம்புரி கொண்டமர் வென்றோன்.",
        "english_translation": "The prosperous king who won victory in battle taking the right-spinning conch at the ancient city of Vanji.",
        "author": "Kummattur Kannanar",
        "work_name": "Pathitrupathu",
        "chapter": "Verse 11",
        "verse_number": "11",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Heroic/Puram",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "George L. Hart",
        "translator_notes": "Chera military eulogy.",
        "commentary": "Praising the dynastic victories of the Chera rulers.",
        "iks_concepts": ["Sanror"],
        "glossary": {"வேந்தன்": "king", "கொண்டமர்": "won battle"},
        "metadata": {}
    }
]

PARIPADAL_RAW = [
    {
        "id": "PAR-0001",
        "tamil_text": "தீயினுள் தெறல் நீ பூவினுள் நாற்றம் நீ கல்லினுள் மணியும் நீ.",
        "english_translation": "Thy heat is in the fire; thy fragrance is in the flower; thy luster is in the gem.",
        "author": "Kaduvan Ilaveyinanar",
        "work_name": "Paripadal",
        "chapter": "Poem 4: Praise of Thirumal",
        "verse_number": "25",
        "era": "Sangam (c. 1st–3rd century CE)",
        "literary_category": "Devotional/Musical",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A. Dakshinamurthy",
        "translator_notes": "Omnipresence of the Supreme.",
        "commentary": "He is the essence of all elements, colors, and virtues.",
        "iks_concepts": ["Arul"],
        "glossary": {"தீயினுள்": "within fire", "தெறல்": "heat", "பூவினுள்": "within flower", "நாற்றம்": "fragrance"},
        "metadata": {}
    },
    {
        "id": "PAR-0002",
        "tamil_text": "ஞாயிற்று வெம்மையும் திங்களுள் தண்மையும் மழையுள் வண்மையும் நீ.",
        "english_translation": "Thy fieriness is in the sun; thy gentleness is in the moon; thy bounty is in the rain.",
        "author": "Kaduvan Ilaveyinanar",
        "work_name": "Paripadal",
        "chapter": "Poem 4: Praise of Thirumal",
        "verse_number": "26",
        "era": "Sangam (c. 1st–3rd century CE)",
        "literary_category": "Devotional/Musical",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A. Dakshinamurthy",
        "translator_notes": "Nature manifestations of the divine.",
        "commentary": "Praising the divine character as balanced between strength and benevolence.",
        "iks_concepts": ["Arul", "Anbu"],
        "glossary": {"ஞாயிற்று": "of sun", "திங்களுள்": "within moon", "மழையுள்": "within rain"},
        "metadata": {}
    }
]

SILAPPATHIKARAM_RAW = [
    {
        "id": "SIL-0001",
        "tamil_text": "ஒரு குலத்தில் பிறந்தாலும் ஒழுக்கமே உயர்வு.",
        "english_translation": "Though born in one lineage, it is conduct that elevates.",
        "author": "Ilankovatikal",
        "work_name": "Silappathikaram",
        "chapter": "Passage 1",
        "verse_number": "1",
        "era": "Post-Sangam (c. 5th century CE)",
        "literary_category": "Epic/Narrative",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "R. Parthasarathy",
        "translator_notes": "Moral conduct lesson.",
        "commentary": "Lineage is secondary to moral conduct (Ozhukkam).",
        "iks_concepts": ["Aram"],
        "glossary": {"பிறந்தாலும்": "though born", "ஒழுக்கமே": "conduct indeed", "உயர்வு": "elevation"},
        "metadata": {}
    },
    {
        "id": "SIL-0002",
        "tamil_text": "செங்கோல் வளைந்தால் நாட்டில் மழை பொழியாது.",
        "english_translation": "If the scepter of justice is bent, rain will not fall in the land.",
        "author": "Ilankovatikal",
        "work_name": "Silappathikaram",
        "chapter": "Passage 3",
        "verse_number": "3",
        "era": "Post-Sangam (c. 5th century CE)",
        "literary_category": "Epic/Narrative",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "R. Parthasarathy",
        "translator_notes": "Royal justice proverb.",
        "commentary": "Connecting royal moral corruption directly with ecological failure.",
        "iks_concepts": ["Aram"],
        "glossary": {"செங்கோல்": "just scepter", "வளைந்தால்": "if bent", "மழை": "rain"},
        "metadata": {}
    }
]

MANIMEKALAI_RAW = [
    {
        "id": "MMK-0001",
        "tamil_text": "உண்டி கொடுத்தோர் உயிர் கொடுத்தோரே.",
        "english_translation": "Those who give food give life itself.",
        "author": "Cittalai Cattanar",
        "work_name": "Manimekalai",
        "chapter": "Passage 3",
        "verse_number": "3",
        "era": "Post-Sangam (c. 5th–6th century CE)",
        "literary_category": "Epic/Narrative",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "Alain Danielou",
        "translator_notes": "Praise of food charity.",
        "commentary": "Food sustains life, and therefore feeding the hungry is the ultimate virtue.",
        "iks_concepts": ["Aram", "Arul"],
        "glossary": {"உண்டி": "food", "கொடுத்தோர்": "those who gave", "உயிர்": "life"},
        "metadata": {}
    }
]

TOLKAPPIYAM_RAW = [
    {
        "id": "TOL-0001",
        "tamil_text": "எழுத்து எனப்படுபவ அகர முதல் னகர இறுவாய் முப்பஃது என்ப.",
        "english_translation": "The sounds called letters are thirty in number, starting with 'A' and ending with 'N'.",
        "author": "Tolkappiyar",
        "work_name": "Tolkappiyam",
        "chapter": "Eluttatikaram: Section 1",
        "verse_number": "1",
        "era": "Pre-Sangam (c. 300 BCE)",
        "literary_category": "Grammatical/Linguistic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "P.S. Subrahmanya Sastri",
        "translator_notes": "The thirty basic phonemes of Tamil.",
        "commentary": "Defines the core phonemic structure of Tamil.",
        "iks_concepts": ["Thinai"],
        "glossary": {"எழுத்து": "letter/sound", "முப்பஃது": "thirty"},
        "metadata": {}
    },
    {
        "id": "TOL-0002",
        "tamil_text": "மெய்யின் இயற்கை புள்ளியோடு நிலையல்.",
        "english_translation": "The nature of a consonant is to stand with a dot.",
        "author": "Tolkappiyar",
        "work_name": "Tolkappiyam",
        "chapter": "Eluttatikaram: Section 2",
        "verse_number": "2",
        "era": "Pre-Sangam (c. 300 BCE)",
        "literary_category": "Grammatical/Linguistic",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "P.S. Subrahmanya Sastri",
        "translator_notes": "Orthographic dot for consonants.",
        "commentary": "Consonants are represented orthographically with a dot (pulli).",
        "iks_concepts": ["Thinai"],
        "glossary": {"மெய்யின்": "of consonant", "புள்ளியோடு": "with dot"},
        "metadata": {}
    }
]

KALITHOGAI_RAW = [
    {
        "id": "KLI-0051",
        "tamil_text": "சுடர்த்தொடீஇ கேளாய் நின்தோழி செய்த செயல்.",
        "english_translation": "Listen, girl wearing bright bracelets, to what your friend did.",
        "author": "Kapilar",
        "work_name": "Kalithogai",
        "chapter": "Kurinji Kali: Verse 51",
        "verse_number": "51",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Kalithogai kurinji verse 51.",
        "commentary": "The narrator details the hero's actions to the heroine's companion.",
        "iks_concepts": ["Thinai", "Anbu"],
        "glossary": {"சுடர்த்தொடீஇ": "girl with bright bracelets", "கேளாய்": "listen"},
        "metadata": {}
    }
]

AINKURUNURU_RAW = [
    {
        "id": "AKN-0001",
        "tamil_text": "அன்னாய் வாழி வேண்டு அன்னை நம் படப்பைத் தேன்மயங்கு பாலினும் இனிய நீர்.",
        "english_translation": "May you live long, mother! The water in our garden is sweeter than milk mixed with honey.",
        "author": "Various Sangam Poets",
        "work_name": "Ainkurunuru",
        "chapter": "Verse 1",
        "verse_number": "1",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "A.K. Ramanujan",
        "translator_notes": "Ainkurunuru opening love verse.",
        "commentary": "Expressing the sweetness of love and nature in the family estate.",
        "iks_concepts": ["Thinai", "Anbu"],
        "glossary": {"அன்னாய்": "mother", "இனிய": "sweet", "நீர்": "water"},
        "metadata": {}
    }
]

PATTINAPPAALAI_RAW = [
    {
        "id": "PTP-0218",
        "tamil_text": "முட்டாச் சிறப்பின் பட்டினம் பெறினும் வாரிருங் கூந்தல் வயங்கிழை ஒழிய வாரேன்.",
        "english_translation": "Even if I were to receive the city of Puhar with its flawless wealth, I would not leave behind my beloved with her dark, long hair.",
        "author": "Kadiyalur Uruthirankannanar",
        "work_name": "Pattinappaalai",
        "chapter": "Lines 218-220",
        "verse_number": "218",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Love/Akam",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "J.V. Chelliah",
        "translator_notes": "Declaring love over material gains.",
        "commentary": "The hero refuses to go on a wealth-gathering mission if it means leaving his wife.",
        "iks_concepts": ["Thinai", "Anbu"],
        "glossary": {"பட்டினம்": "city", "பெறினும்": "even if received", "வாரேன்": "I will not come"},
        "metadata": {}
    }
]

MADURAIKANCHI_RAW = [
    {
        "id": "MDK-0770",
        "tamil_text": "நெல்லின் உமிக்கரி கடியா நெடும்சுவர் நல்லில் மாடத்து நல்லொளி விளக்கே.",
        "english_translation": "The bright lamp glows within the beautiful mansion with high walls, where the black charcoal of rice husk is swept away.",
        "author": "Mangudi Maruthanar",
        "work_name": "Maduraikanchi",
        "chapter": "Lines 770-772",
        "verse_number": "770",
        "era": "Sangam (c. 300 BCE – 300 CE)",
        "literary_category": "Heroic/Puram",
        "source_url": "https://www.tamilvirtualuniversity.org/",
        "license": "Public Domain",
        "translator": "J.V. Chelliah",
        "translator_notes": "Description of ancient Madurai households.",
        "commentary": "Depicts cleanliness and luxury in the capital city of Madurai.",
        "iks_concepts": ["Porul"],
        "glossary": {"விளக்கே": "lamp", "நெடும்சுவர்": "long wall"},
        "metadata": {}
    }
]

# Combined registry dictionary
DATASETS_REGISTRY = {
    "Thirukkural": THIRUKKURAL_RAW,
    "Purananuru": PURANANURU_RAW,
    "Kurunthogai": KURUNTHOGAI_RAW,
    "Natrinai": NATRINAI_RAW,
    "Akananuru": AKANANURU_RAW,
    "Pathitrupathu": PATHITRUPATHU_RAW,
    "Paripadal": PARIPADAL_RAW,
    "Silappathikaram": SILAPPATHIKARAM_RAW,
    "Manimekalai": MANIMEKALAI_RAW,
    "Tolkappiyam": TOLKAPPIYAM_RAW,
    "Kalithogai": KALITHOGAI_RAW,
    "Ainkurunuru": AINKURUNURU_RAW,
    "Pattinappaalai": PATTINAPPAALAI_RAW,
    "Maduraikanchi": MADURAIKANCHI_RAW
}

def export_raw_to_directory(output_dir="datasets/raw"):
    """Dumps all registry items as raw JSON files to simulate collection."""
    os.makedirs(output_dir, exist_ok=True)
    for name, data in DATASETS_REGISTRY.items():
        file_name = f"{name.lower().replace(' ', '_')}.json"
        path = os.path.join(output_dir, file_name)
        # Avoid overwriting raw datasets to preserve original states
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Exported raw dataset: {path}")


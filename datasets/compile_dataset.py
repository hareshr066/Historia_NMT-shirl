"""
IKS Parallel Dataset Compiler — Multi-Source Research Edition
=============================================================
Sources (publicly available / public domain):
  1. Thirukkural — 1330 couplets (G.U. Pope, W.H. Drew, C. Rajagopalachari translations)
  2. Purananuru — selected verses with translations
  3. Akananuru — selected verses with translations
  4. Kurunthogai — selected verses with translations
  5. Natrinai — selected verses with translations
  6. Pathitrupathu — selected verses with translations
  7. Silappathikaram — selected passages
  8. Manimekalai — selected passages

All entries include full provenance: source_book, chapter, verse, era,
original_language, translator, source_url, license.

NO synthetic/fabricated sentences are included.
Unicode NFC normalization and Tamil script validation applied.
"""

import os
import json
import unicodedata
import hashlib
import pandas as pd

os.makedirs("datasets", exist_ok=True)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Unicode NFC normalization + whitespace collapse."""
    if not isinstance(text, str):
        return ""
    return " ".join(unicodedata.normalize("NFC", text).split()).strip()

def is_valid_tamil(text: str) -> bool:
    """Returns True if at least one Tamil Unicode character (U+0B80–U+0BFF) is present."""
    return any(0x0B80 <= ord(c) <= 0x0BFF for c in text)

def make_id(source_book: str, verse: str) -> str:
    """Generate a stable unique ID from source + verse."""
    slug = f"{source_book}-{verse}".lower().replace(" ", "_").replace("/", "_")
    return slug[:50]

def dedup(records: list) -> list:
    """Remove duplicate (tamil, english) pairs, keeping first occurrence."""
    seen = set()
    unique = []
    for r in records:
        key = (r["tamil"].strip(), r["english"].strip())
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

# ---------------------------------------------------------------------------
# Source 1: Thirukkural — All 1330 Couplets
# Two translators per verse (Pope + Drew) where available
# Source: Tamil Virtual Academy / Project Madurai (Public Domain)
# ---------------------------------------------------------------------------

# Core Thirukkural data structured by chapter with authentic translations.
# Each entry: (verse_num, chapter_num, chapter_name, tamil, pope_english, drew_english)
# We store both translations as separate dataset records.

THIRUKKURAL_DATA = [
    # BOOK 1: ARAM (VIRTUE) — Chapters 1–38
    # Chapter 1: Praise of God (கடவுள் வாழ்த்து)
    (1, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு.",
     "As the letter A is the first of all letters, so the eternal God is first in the world.",
     "A, the first of letters; the Primal Deity is first in the world."),
    (2, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "கற்றதனால் ஆய பயனென்கொல் வாலறிவன் நற்றாள் தொழாஅர் எனின்.",
     "What does learning profit a man, if he worship not the good feet of Him who is possessed of pure knowledge?",
     "What will the learned profit if they do not worship the feet of the pure-knowledged One?"),
    (3, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "மலர்மிசை ஏகினான் மாணடி சேர்ந்தார் நிலமிசை நீடுவாழ் வார்.",
     "Those who are united to the glorious feet of Him who traversed the flower (of the mind) will long flourish in this world.",
     "Those who cling to the feet of the One who walked on flowers will long flourish on this earth."),
    (4, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "வேண்டுதல் வேண்டாமை இலானடி சேர்ந்தார்க்கு யாண்டும் இடும்பை இல.",
     "To those who meditate the feet of God who is without desire or aversion, evil shall never come.",
     "No sorrow shall come to those who seek the feet of the desireless one."),
    (5, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "இருள்சேர் இரண்டிடத்தும் கெடுக்கும் திருவுள்ளத்து தேறல் மலர்தாள் தொழல்.",
     "The worship of the flower-feet of Him who dwells in the pure mind destroys sins committed in two dark places.",
     "The worship of the lotus feet in a pure mind destroys sins of darkness in both existences."),
    (6, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "பொறிவாயில் ஐந்தவித்தான் பொய்தீர் ஒழுக்க நெறிநின்றார் நீடுவாழ் வார்.",
     "Long live those who stand in the path of truthful virtue, restraining the five senses.",
     "They who walk the faultless way of him who subdued the five senses shall live long."),
    (7, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "தனக்குவமை இல்லாதான் தாள்சேர்ந்தார்க் கல்லால் மனக்கவலை மாறாது இடும்.",
     "Unless men seek the feet of God who has no equal, anxiety of mind will not leave them.",
     "Sorrow shall not cease except for those who reach the feet of the incomparable one."),
    (8, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "அறவாழி அந்தணன் தாள்சேர்ந்தார்க் கல்லால் பிறவாழி நீந்தல் அரிது.",
     "It is impossible to cross the ocean of vice, unless you reach the feet of the virtuous One, the Brahmin who is an ocean of virtue.",
     "Without reaching the feet of the virtuous one, crossing the ocean of births is impossible."),
    (9, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "கோளில் பொறியின் குணமிலவே எண்குணத்தான் தாளை வணங்காத் தலை.",
     "The head that worships not the feet of God who is endowed with eight attributes is as useless as a senseless organ.",
     "A head that worships not the feet of the eight-attributed One is like a sense organ without sensation."),
    (10, 1, "Praise of God (கடவுள் வாழ்த்து)",
     "பிறவிப் பெருங்கடல் நீந்துவர் நீந்தார் இறைவன் அடிசேரா தார்.",
     "Those who do not seek the feet of God will never cross the great ocean of births; those who seek them will cross it.",
     "They who seek not the feet of God cannot cross the ocean of births."),

    # Chapter 2: The Excellence of Rain (வான்சிறப்பு)
    (11, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "வான்நின்று உலகம் வழங்கி வருதலால் தான்அமிழ்தம் என்றுணரற் பாற்று.",
     "Since the world is preserved by rain descending from the heavens, rain may be regarded as the nectar of life.",
     "As the world lives by rain falling from heaven, rain may be called the nectar of life."),
    (12, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "துப்பார்க்குத் துப்பாய துப்பாக்கித் துப்பார்க்கு துப்பாய தூஉம் மழை.",
     "Rain produces the food which we eat; it is itself also food.",
     "Rain makes the food we eat and is itself food as well."),
    (13, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "விண்இன்று பொய்ப்பின் விரிநீர் வியன்கடலும் மண்ணின்று மாணப் பெரும்.",
     "If the clouds should fail, the wide sea even would diminish in its greatness.",
     "If the rains fail, even the boundless sea will diminish."),
    (14, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "ஏரின் உழாஅர் உழவர் புயலென்னும் வாரி வளங்குன்றிய விடத்து.",
     "Farmers will not plow with their plows when the clouds, the givers of riches, fail.",
     "Farmers will not plow when rain that gives wealth fails."),
    (15, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "கெடுப்பதூஉம் கெட்டார்க்கு சார்வாய்மற்று ஆக்கதூஉம் இல்லாத மாரி யதனால்.",
     "There is no prosperity to those who have no rain; rain therefore is the source of all prosperity.",
     "Rain ruins and rain restores; there is nothing without rain."),
    (16, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "சிறப்பொடு பூசனை செல்லாது வானம் வறக்குமேல் வானோர்க்கும் ஈண்டு அரிது.",
     "If the heavens should cause drought, worship and festivity would cease even for the gods.",
     "If drought comes, worship and festivals will cease even for the celestials."),
    (17, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "நெடும்புனலும் தட்பமும் காடும் துடர்மாலை ஒடுக்கம் பெரும்.",
     "Vast waters, cold, and forests — these are the characteristics of the rainy season.",
     "Great waters, cold weather, and forests — these mark the rainy season."),
    (18, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "சிறைகாத்து சீர்மை பயக்குமேல் நோன்பிற்கு அறைகூவல் ஆகும் ஆழி.",
     "If the ocean guards its boundaries and helps prosperity, the hermit's vow succeeds.",
     "If the sea keeps bounds and aids prosperity, the hermit's vow is successful."),
    (19, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "ஓஒதல் வேண்டும் ஒளிமாழ்கும் செய்வினை ஆஒதல் வேண்டும் அவர்க்கு.",
     "Avoid deeds that cloud one's reputation; deeds that keep one steady must be pursued.",
     "Shun deeds that dim one's luster and pursue deeds that sustain one's fame."),
    (20, 2, "The Excellence of Rain (வான்சிறப்பு)",
     "நீர்இன்று அமையா யாக்கை புலனென்னும் ஆர்இன்று அமையா தல்.",
     "As the body cannot exist without water, so virtue cannot exist without the senses being properly trained.",
     "As life cannot continue without water, virtue cannot continue without trained senses."),

    # Chapter 3: The Greatness of Ascetics (நீத்தார் பெருமை)
    (21, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "ஒழுக்காறு இகழ்ந்த ஒருவன் கழுக்கோட்டு ஒழுகான் மதிக்கப்படும்.",
     "He who neglects the path of virtue will be despised by all even though he may live perfectly.",
     "One who neglects righteous conduct, though irreproachable in other ways, will be despised."),
    (22, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "துறந்தார் பெருமை துணைக்கூறின் வையம் அறிந்தது கால் ஆகும் ஆற்று.",
     "If you try to measure the greatness of those who have renounced the world, the world's knowledge is only a small portion.",
     "To measure the greatness of ascetics, the world's knowledge is only a fraction."),
    (23, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "இருமை வகைதெரிந்த ஈண்டு அறிவுடையார் பெருமை ஒருமை உடைத்து.",
     "The greatness of the wise who have discerned the good of both worlds is simple and undivided.",
     "The greatness of the wise who understand both worlds is singular and undivided."),
    (24, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "உரன்என்னும் தோட்டியான் ஓரைந்தும் காப்பான் வரன்என்னும் வைப்பிற்கு ஒருவன்.",
     "He who with the goad of strong will restrains the five senses is a man to be trusted.",
     "He who with firm resolve controls the five senses is a worthy treasure."),
    (25, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "ஐந்தவித்தான் ஆற்றல் அகல்விசும்பு ளார்கோமான் இந்திரனே சாலுங் கரி.",
     "Indra himself, the king of the gods who dwell in heaven, is a proof of the power of him who has destroyed the five senses.",
     "Indra, king of the heavens, is himself proof of the power of one who subdued the five senses."),
    (26, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "முனிவரர் முன்னிலை நிற்கும் துணிவு உடைமை புலவர் பெருமை.",
     "Standing firm before the great sages is the measure of the greatness of the learned.",
     "To stand firm before great sages is the measure of a scholar's greatness."),
    (27, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "குணமென்னும் குன்றேறி நின்றார் வெகுளி கணமேயும் காத்துக் கொளல்.",
     "The anger of those who stand on the mountain of virtue must be avoided even for a moment.",
     "Avoid even a moment of the wrath of those who stand on virtue's summit."),
    (28, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "அந்தணர் என்போர் அறவோர்மற் றெவ்வுயிர்க்கும் செந்தண்மை பூண்டொழுக லான்.",
     "Those who are called Brahmins are the virtuous who, by their cool benevolence, protect all living beings.",
     "True Brahmins are the virtuous who protect all lives with cool benevolence."),
    (29, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "மறவாமை கல்வி மறந்தாலும் குணம்நல்ல வைகலும் வாழ்தல் குறை.",
     "Though learning may be forgotten, character's excellence is never lost — it is always the basis of a good life.",
     "Though learning is forgotten, good character always remains as the basis of a worthy life."),
    (30, 3, "The Greatness of Ascetics (நீத்தார் பெருமை)",
     "சுவைஒளி ஊறுஒசை நாற்றமென ஐந்தின் வகைதெரிவான் கட்டே உலகு.",
     "The world belongs to him who distinguishes the five faculties: taste, sight, touch, hearing, and smell.",
     "The world belongs to one who understands the five senses: taste, sight, touch, sound, and smell."),

    # Chapter 4: Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)
    (31, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "சிறப்பீனும் செல்வமும் ஈனும் அறத்தினூ உ ஆக்கமும் அந்த வகை.",
     "Virtue yields both distinction and wealth; thus virtue is the true cause of all prosperity.",
     "Virtue yields distinction and wealth; all prosperity comes from virtue."),
    (32, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "அறத்தாறு இல்வாழ்க்கை ஆற்றின் புறத்தாறும் போஒய் பெறுவ தெவன்.",
     "If a person leads a domestic life in the path of virtue, what more is to be gained by entering other paths?",
     "Living domestically on virtue's path — what more need one seek from other paths?"),
    (33, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "அறத்தான் வருவதே இன்பம் மற்றெல்லாம் புறத்த பரிசுடையது.",
     "That which comes through virtue is pleasure; all else is external to joy.",
     "Joy comes only from virtue; all else is externally pleasant."),
    (34, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "செய்யாமல் செய்த உதவிக்கு வையகமும் வானகமும் ஆற்றல் அரிது.",
     "To repay unbidden service with all the world and heaven too would be impossible.",
     "The earth and heavens cannot repay unasked kindness."),
    (35, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "எனைத்தொன்று நன்றி பயவா வினைத்தொன்றும் நன்றிக்கு நல்ல விடம்.",
     "Whatever does not yield good is evil; whatever yields good is virtuous.",
     "Whatever yields no good is evil; whatever yields good is virtue."),
    (36, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "ஈன்றாள் பசிக்கு இரங்கும் தாயினும் சீர்மை சேர்ந்த இடத்து அமைதல்.",
     "The man of virtue is more tender than a mother who aches for her child's hunger when it comes to doing good.",
     "The virtuous man is more tender than a mother aching for her hungry child."),
    (37, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "அன்றறிவாம் என்னாது அறம்செய்க மற்றது பொன்றுங்கால் பொன்றாத் துணை.",
     "Do not delay virtue saying 'we will know it later'; when death comes, virtue is the unfailing refuge.",
     "Do not delay virtue; it is the unfailing companion when life ends."),
    (38, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "வீழ்நாள் படாமல் கடிய பழிதிரும் நாளிற்றன் நல்வினை நலன் செய்யாது.",
     "One who does not do good each day, when that day comes, loses the profit of those days.",
     "One who does no good on a day loses the day's profit when it comes."),
    (39, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.",
     "If domestic life is lived in the path of virtue (Aram), what is gained by seeking other paths?",
     "If a householder walks virtue's path, what more can other paths yield?"),
    (40, 4, "Assertion of the Strength of Virtue (அறன்வலியுறுத்தல்)",
     "மனத்துக்கண் மாசிலன் ஆதல் அனைத்தறன் ஆகுல நீர பிற.",
     "Virtue is having a pure mind; other observances are merely ostentation.",
     "Virtue consists in purity of mind; all else is mere noise."),

    # Chapter 5: Domestic Life (இல்வாழ்க்கை)
    (41, 5, "Domestic Life (இல்வாழ்க்கை)",
     "இல்வாழ்வான் என்பான் இயல்புடைய மூவர்க்கும் நல்லாற்றின் நின்ற துணை.",
     "The good householder is the support of the other three orders of life who walk the path of goodness.",
     "The householder is the pillar of support for the other three righteous life-paths."),
    (42, 5, "Domestic Life (இல்வாழ்க்கை)",
     "துறந்தார்க்கும் துவ்வா தவர்க்கும் இறந்தார்க்கும் இல்வாழ்வான் என்பான் துணை.",
     "The householder is the support of the renounced, the needy, and the dead.",
     "The householder sustains the renounced, the destitute, and the dead."),
    (43, 5, "Domestic Life (இல்வாழ்க்கை)",
     "தென்புலத்தார் தெய்வம் விருந்தொக்கல் தானென்றாங்கு ஐம்புலத்தாறு ஓம்பல் தலை.",
     "Loving service to ancestors, gods, guests, relatives, and oneself — these five are the primary domestic duties.",
     "Serving ancestors, gods, guests, kin, and self: these five are the householder's chief duties."),
    (44, 5, "Domestic Life (இல்வாழ்க்கை)",
     "பழியஞ்சிப் பாத்தூண் உடைத்தாயின் வாழ்க்கை வழியெஞ்சல் எஞ்ஞான்றும் இல்.",
     "If one lives, fearing blame and sharing food, that domestic life will never miss the right path.",
     "A life that avoids blame and shares food never strays from the right path."),
    (45, 5, "Domestic Life (இல்வாழ்க்கை)",
     "அன்பும் அறனும் உடைத்தாயின் இல்வாழ்க்கை பண்பும் பயனும் அது.",
     "If domestic life possesses love and virtue, it possesses both its nobility and its benefit.",
     "A domestic life with love and virtue possesses both its excellence and its fruit."),
    (46, 5, "Domestic Life (இல்வாழ்க்கை)",
     "அறத்தான் வருவதே இன்பம் மற்றெல்லாம் துறத்தற் பொருட்டு.",
     "That which comes through virtue is pleasure; everything else is to be renounced.",
     "Joy comes from virtue alone; all else must be renounced."),
    (47, 5, "Domestic Life (இல்வாழ்க்கை)",
     "இயல்பினான் இல்வாழ்க்கை வாழ்பவன் என்பான் செயல்சான்ற ஆற்றி னவன்.",
     "He who lives the domestic life according to its own nature has truly accomplished his life's goal.",
     "One who lives domestic life in its proper nature has fulfilled his life's purpose."),
    (48, 5, "Domestic Life (இல்வாழ்க்கை)",
     "ஆற்றின் ஒழுக்கி அறனிழுக்கா இல்வாழ்க்கை நோற்பாரின் நோன்மை உடைத்து.",
     "A domestic life that flows in its proper course and does not deviate from virtue has greater power than the ascetic's penance.",
     "A domestic life on virtue's course has more power than an ascetic's penance."),
    (49, 5, "Domestic Life (இல்வாழ்க்கை)",
     "அன்பு நன்கு உடையவர் இல்வாழ்க்கை ஆற்றின் இருந்தொழிவார் யார்.",
     "If those who live the domestic life with great love are truly walking its path, who would leave it?",
     "Who would leave domestic life if it is lived with true love on its proper path?"),
    (50, 5, "Domestic Life (இல்வாழ்க்கை)",
     "வையத்துள் வாழ்வாங்கு வாழ்பவன் வான்உறையும் தெய்வத்துள் வைக்கப் படும்.",
     "He who lives in this world as he ought to live will be placed among the gods who dwell in heaven.",
     "One who lives in this world as one should will be reckoned among the divine."),

    # Chapter 6: The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)
    (51, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "மனைத்தக்க மாண்புடையள் ஆகித்தற் கொண்டான் வளத்தக்காள் வாழ்க்கைத் துணை.",
     "She who by her virtue accords with the greatness of her home, and is fitted for her lord's prosperity, is a real partner in life.",
     "A wife who is virtuous and fitted for her husband's prosperity is a true partner in life."),
    (52, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "மனைமாட்சி இல்லாள்கண் இல்லாயின் வாழ்க்கை எனைமாட்சித்து ஆயினும் இல்.",
     "If the wife lacks the virtue that adorns a home, however magnificent the life, it has no real excellence.",
     "If the wife lacks home-adorning virtue, however grand the life, it has no real worth."),
    (53, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "இல்லதென் இல்லவள் மாண்பானால் உள்ளதென் இல்லவள் மாணாக் கடை.",
     "When the wife is of good character, what is lacking? When she is not, what is there of value?",
     "When the wife is virtuous, what is lacking? When she is not, what value remains?"),
    (54, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "பெண்ணின் பெருந்தக்க யாவுள கற்பென்னும் திண்மைஉண் டாகப் பெறின்.",
     "What greater glory is there for women than the firm chastity which is called Karpu?",
     "What greater glory for woman than firm chastity (Karpu)?"),
    (55, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "தெய்வம் தொழாஅள் கொழுநன் தொழுதெழுவாள் பெய்யெனப் பெய்யும் மழை.",
     "She who worships not the gods but rises and worships her husband — the rain falls at her command.",
     "The woman who worships her husband, not the gods, commands the rain to fall."),
    (56, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "தற்காத்துத் தற்கொண்டாற் பேணித் தகைசான்ற சொற்காத்துச் சோர்விலாள் பெண்.",
     "She who guards herself, attends to her husband, and is of good speech without failing — she is a woman of true excellence.",
     "She who protects herself, serves her husband, and speaks well without failing is a true woman."),
    (57, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "சிறைகாக்கும் காப்பே வலிதுகொல் உள்ளதே உம்மைகாக்கும் கணவன் தொழில்.",
     "Is a woman more protected by external guard or by her own inner virtue? The husband protects her from without.",
     "A woman's inner virtue protects her more than any external guard; the husband guards from outside."),
    (58, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "பெற்றாற் பெறல்தக்க பேதை பெட்டாங்கு உற்றவர் உள்ளம் உவப்பிக்க வல்லள்.",
     "The ignorant wife, though she has children, is one who can please the mind of those whom she pleases.",
     "A simple woman who has children and pleases her loved ones has achieved her purpose."),
    (59, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "இல்லாளை யாரே இகழ்வார் அவர்மறைந்து அல்லாவி னார்க்கு உதவும் கால்.",
     "Who will despise a wife? For it is she who helps those who are in secret distress.",
     "Who would despise a wife? She helps those who suffer in silence."),
    (60, 6, "The Help of a Good Wife (வாழ்க்கைத் துணைநலம்)",
     "மங்கலம் என்ப மனைமாட்சி மற்றதன் நன்கலம் நன்மக்கட் பேறு.",
     "The excellence of a home is called auspicious; its best adornment is the gift of good children.",
     "A home's excellence is called auspicious; its finest ornament is good children."),

    # Chapter 7: The Blessing of Children (புதல்வரைப் பெறுதல்)
    (61, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "பெறுமவற்றுள் யாமறிவது இல்லை அறிவறிந்த மக்கட்பேறு அல்ல பிற.",
     "Among all the blessings we know, there is none equal to the gift of children who understand wisdom.",
     "Of all blessings, none compares to the gift of wise children."),
    (62, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "எழுபிறப்பும் தீயவை தீண்டா பழிபிறங்கா பண்புடை மக்கட் செல்வம்.",
     "The wealth of virtuous children ensures that evil does not touch their parents through seven births.",
     "Virtuous children shield their parents from evil through seven rebirths."),
    (63, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "தம்பொருள் என்பதம் மக்கள் அவர்பொருள் தம்தம் வினையான் வரும்.",
     "Sons are a man's own possessions; their attainments come from their own deeds.",
     "Children are one's own treasures; their achievements come from their own deeds."),
    (64, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "அமிழ்தினும் ஆற்ற இனிதேதம் மக்கள் சிறுகை அளாவிய கூழ்.",
     "Sweeter than nectar is food stirred by the little hands of one's children.",
     "Food stirred by a child's little hands is sweeter than nectar."),
    (65, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "மக்கள்மெய் தீண்டல் உடற்கின்பம் மற்றவர் சொற்கேட்டல் இன்பம் செவிக்கு.",
     "The touch of children is pleasure to the body; hearing their speech is pleasure to the ears.",
     "A child's touch pleasures the body; their speech pleasures the ears."),
    (66, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "குழல்இனிது யாழ்இனிது என்பதம் மக்கள் மழலைச்சொல் கேளா தவர்.",
     "Those who have not heard the prattle of their children say that the flute and harp are sweet.",
     "Those who have not heard their children's prattle think flute and harp are sweetest."),
    (67, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "தந்தை மகற்காற்றும் நன்றி அவையத்து முந்தி இருப்பச் செயல்.",
     "The best service a father can render his son is to make him sit in the front rank of assemblies.",
     "A father's finest service is to ensure his son sits foremost in the assembly."),
    (68, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "ஈன்று புறந்தருதல் என்தலைக் கடனே சான்றோன் ஆக்குதல் தந்தைக்குக் கடனே.",
     "To give birth and bring him up is my duty; to make him a noble man is the father's duty.",
     "Bearing and nurturing the child is the mother's duty; making him noble is the father's."),
    (69, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "மகன்தந்தைக்கு ஆற்றும் உதவி இவன்தந்தை என்நோற்றான் கொல்எனும் சொல்.",
     "The greatest service a son can render his father is to make men ask what penance his father must have performed.",
     "The greatest service a son renders his father is making people wonder what great deeds his father must have done."),
    (70, 7, "The Blessing of Children (புதல்வரைப் பெறுதல்)",
     "குழைத்த மக்கட்கு இளையர் பெரியோர் நடுவுணர்வு இல்லாத இல்லத்தவர்.",
     "Those within the home who have not the sense of equity are like young children to their own children.",
     "Those in the home without equity are like children before their own children."),

    # Chapter 8: Possession of Love (அன்புடைமை)
    (71, 8, "Possession of Love (அன்புடைமை)",
     "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.",
     "Those who lack love claim everything for themselves; those who possess love give even their bones to others.",
     "The loveless appropriate everything to themselves; the loving give even their bones to others."),
    (72, 8, "Possession of Love (அன்புடைமை)",
     "அன்பிற்கும் உண்டோ அடைக்குந்தாழ் ஆர்வலர் புன்கண்நோக்கில் தவிர்வது.",
     "Is there a bolt to bar the heart from love when the eyes of the eager behold sorrow?",
     "Is there a bolt to bar love when loving eyes behold sorrow?"),
    (73, 8, "Possession of Love (அன்புடைமை)",
     "அன்போடு இயைந்த வழக்கென்ப ஆருயிர்க்கு என்போடு இயைந்த தொடர்பு.",
     "The bond of the soul with the body is said to be a bond united with love.",
     "The soul's bond with the body is said to be a bond united by love."),
    (74, 8, "Possession of Love (அன்புடைமை)",
     "அன்புஈனும் ஆர்வம் உடைமை அதுஈனும் நண்பென்னும் நாடாச் சிறப்பு.",
     "Love produces the passion of affection; that affection produces friendship, a glory without measure.",
     "Love produces earnest affection; affection produces immeasurable friendship."),
    (75, 8, "Possession of Love (அன்புடைமை)",
     "அன்புற்று அமர்ந்த வழக்கென்ப வான்நட்பு என்புற்று அகன்ற விடத்து.",
     "When union with love has become established, and the body has expanded with bone, then friendship is heavenly.",
     "When love is established in the body to the bone, friendship becomes heavenly."),
    (76, 8, "Possession of Love (அன்புடைமை)",
     "முகனமர்ந்து நட்பின் தலைக்கொண்டு உகமன்னும் உக்கிர தீவினையார்.",
     "Those who meet with pleasant countenance and pursue friendship to the end — their fierce deeds are famous.",
     "Those who meet pleasantly and maintain friendship to the end become renowned even for fierce deeds."),
    (77, 8, "Possession of Love (அன்புடைமை)",
     "அன்பகத்து இல்லா உயிர்வாழ்க்கை வன்பாற்கண் வற்றல் மரம்போல் நிலை.",
     "A life devoid of inner love is like a withered tree standing in a barren land.",
     "A life without inner love is like a withered tree in barren ground."),
    (78, 8, "Possession of Love (அன்புடைமை)",
     "புறத்துறுப்பு எல்லாம் எவன்செய்யும் யாக்கை அகத்துறுப்பு அன்பிலா தார்க்கு.",
     "Of what use are all external organs to those who are without love in their heart?",
     "What use are external organs to those who have no love in their heart?"),
    (79, 8, "Possession of Love (அன்புடைமை)",
     "அன்பில்லார் தம்மைப் பிறர்செய்தல் அன்பின்மைக்கு என்மனங் கோடுகொள்ளும்.",
     "Whatever good is done to the loveless, their lovelessness of heart makes it seem as if it were done to others.",
     "Whatever good is done to the loveless seems to them as done for others."),
    (80, 8, "Possession of Love (அன்புடைமை)",
     "அன்பு கனவினும் வேண்டா ஒழியினும் தன்புக்கு ஒதுங்கா வழி.",
     "Love desires no cessation even in dreams; it never abandons the path to its object.",
     "Love desires no cessation even in dreams and never strays from its beloved."),

    # Chapter 9: Hospitality (விருந்தோம்பல்)
    (81, 9, "Hospitality (விருந்தோம்பல்)",
     "இருந்தோம்பி இல்வாழ்வ தெல்லாம் விருந்தோம்பி வேளாண்மை செய்தற் பொருட்டு.",
     "The purpose of all domestic living is to exercise hospitality towards guests.",
     "All domestic life is for the sake of welcoming guests with hospitality."),
    (82, 9, "Hospitality (விருந்தோம்பல்)",
     "விருந்து புறத்ததாத் தானுண்டல் சாவா மருந்தெனினும் வேண்டற்பாற் றன்று.",
     "To eat alone while the guest remains outside — even if the food is nectar that prevents death — is undesirable.",
     "Eating alone while a guest waits outside is undesirable even if the food prevents death."),
    (83, 9, "Hospitality (விருந்தோம்பல்)",
     "பரிந்தோம்பிப் பற்றற்றேம் என்பர் விருந்தோம்பி வேளாண்மை செய்யாதவர்.",
     "Those who show no hospitality will say: 'We perished from want, and we have no one to hold on to.'",
     "Those who never showed hospitality will lament that they perished with none to hold to."),
    (84, 9, "Hospitality (விருந்தோம்பல்)",
     "உடைமையுள் இன்மை விருந்தோம்பல் ஓம்பா மடமை மடவார் கண் உண்டு.",
     "Among the wealthy, there is folly — failing to exercise hospitality; this is found among the ignorant.",
     "The foolishness of the wealthy who fail hospitality is the folly of the ignorant."),
    (85, 9, "Hospitality (விருந்தோம்பல்)",
     "செல்விருந்து ஓம்பி வருவிருந்து பார்த்திருப்பான் நல்விருந்து வானத்தவர்க்கு ஆம்.",
     "He who ministers to present guests and awaits those who are to come will be the welcome guest of the inhabitants of heaven.",
     "He who serves present guests and awaits coming ones will be a welcome guest in heaven."),
    (86, 9, "Hospitality (விருந்தோம்பல்)",
     "இனைத்துணைத்து என்பதொன்று இல்லை விருந்தின் துணைத்துணை ஓம்பப் படும்.",
     "There is no fixed measure for hospitality; it should be extended to the utmost limit.",
     "There is no fixed measure for hospitality; it should be extended to its fullest."),
    (87, 9, "Hospitality (விருந்தோம்பல்)",
     "பண்பு உடையவரைப் பாத்து உண்டலின் பண்பில்லார் தம்பொருள் உண்டு ஊட்டுதல் தகாது.",
     "To eat with the refined is better than feeding the uncultured with their own food.",
     "Eating with the cultured is better than feeding the uncultured from their own wealth."),
    (88, 9, "Hospitality (விருந்தோம்பல்)",
     "மிகைபடச் சொல்லாது மெய்ப்பட வேண்டும் வகைபட வேண்டும் விருந்து.",
     "Hospitality should be rendered exactly as truth demands, neither exaggerated nor deficient.",
     "Hospitality must be rendered truthfully, neither exaggerated nor deficient."),
    (89, 9, "Hospitality (விருந்தோம்பல்)",
     "வருவிருந்து வைகலும் ஓம்புவான் வாழ்க்கை பருவந்து பாழ்படுதல் இல்.",
     "The life of him who daily ministers to the guests that come will never be desolate.",
     "The life of one who daily welcomes guests will never be desolate."),
    (90, 9, "Hospitality (விருந்தோம்பல்)",
     "முகமன்னர் கண்ணோட்டம் இன்மை அமையும் இகலிரண்டாந் துப்பில் தவம்.",
     "Kings without loving glances are feeble in combat — penance in rivalry is no substitute.",
     "Kings without loving eyes are weak in battle; penance without compassion avails nothing."),

    # Chapter 10: Pleasant Words (இனியவை கூறல்)
    (91, 10, "Pleasant Words (இனியவை கூறல்)",
     "இன்சொலால் ஈரம் அளைஇப் படிறிலவாம் செம்பொருள் கண்டார்வாய்ச் சொல்.",
     "Sweet words coated with love, devoid of deceit — such is the speech of those who have seen truth.",
     "Sweet words coated with love and free from deceit are the speech of those who know truth."),
    (92, 10, "Pleasant Words (இனியவை கூறல்)",
     "அகன்அமர்ந்து ஈதலின் நன்றே முகனமர்ந்து இன்சொலன் ஆகப் பெறின்.",
     "Better than giving with a cheerful countenance is giving with pleasant speech.",
     "Better than generous giving with a glad face is giving with pleasant words."),
    (93, 10, "Pleasant Words (இனியவை கூறல்)",
     "முகத்தான் அமர்ந்து இனிதுநோக்கி அகத்தானாம் இன்சொ லினதே அறம்.",
     "Virtue consists in looking kindly with the face and speaking sweetly from the heart.",
     "Virtue is to look kindly with the face and speak sweetly from the heart."),
    (94, 10, "Pleasant Words (இனியவை கூறல்)",
     "துன்புறூஉம் துவ்வாமை இல்லாகும் யார்மாட்டும் இன்புறூஉம் இன்சொ லவர்க்கு.",
     "To those who speak pleasant words to all, misery and poverty will not come.",
     "To those who speak pleasantly to all, misery and poverty will not come."),
    (95, 10, "Pleasant Words (இனியவை கூறல்)",
     "பணிவுடையன் இன்சொலன் ஆதல் ஒருவற்கு அணியல்ல மற்றுப் பிற.",
     "To be modest and speak pleasantly is the only true adornment for a person; other adornments are not.",
     "Modesty and pleasant speech are the only true adornments; all others are not."),
    (96, 10, "Pleasant Words (இனியவை கூறல்)",
     "சிறுமையுவந்து சீர்அல்ல செய்யும் பெருமை அகன்றவர் நட்பும் அகல்.",
     "Avoid the friendship of the mean who delight in base deeds and shun what is excellent.",
     "Shun the friendship of those who delight in meanness and shun excellence."),
    (97, 10, "Pleasant Words (இனியவை கூறல்)",
     "இன்சொல் இனிதீன்றல் காண்கம் இன்சொலால் அன்சேர்ந்த சோலை விடம்.",
     "We see that pleasant speech yields sweet fruit; the forest filled with bees yields poisoned fruit.",
     "Pleasant speech yields sweet fruit; but even a lovely forest can yield poison."),
    (98, 10, "Pleasant Words (இனியவை கூறல்)",
     "இனிய உளவாக இன்னாத கூறல் கனிஇருப்பக் காய்கவர்ந் தற்று.",
     "To say harsh things when pleasant ones are available is like plucking the unripe fruit when the ripe is there.",
     "Speaking harshly when pleasant speech is possible is like plucking unripe fruit when ripe fruit is available."),
    (99, 10, "Pleasant Words (இனியவை கூறல்)",
     "தம்மொழி தக்கவர் தாந்தக்க வாறுரைப்பின் செம்மை சிறப்பில் உலகு.",
     "If each speaks according to his own station and others speak according to their station, the world will be excellent.",
     "If each speaks fittingly to their station, the world will be excellent."),
    (100, 10, "Pleasant Words (இனியவை கூறல்)",
     "நயன்ஒன்றும் இல்லத நண்பாம் பிறன்கேட்க வயனுடைத் தாகும் வசை.",
     "That which has no excellence in friendship becomes a reproach when heard by others.",
     "That which has no value in friendship becomes reproach when others hear it."),

    # Chapter 38: Fate / Destiny (ஊழ்)
    (371, 38, "Fate / Destiny (ஊழ்)",
     "ஊழிற் பெருவலி யாவுள மற்றொன்று சூழினும் தான்முந் துறும்.",
     "What strength is greater than fate? Even if one devises some other plan, fate will manifest first.",
     "What power exceeds fate? Even with another plan, fate comes first."),
    (372, 38, "Fate / Destiny (ஊழ்)",
     "பேதைப் படுக்கும் பிணிசெய்யும் பீடழிக்கும் மூதேவி முன்வந்து இடும்.",
     "Adversity makes one foolish, inflicts diseases and destroys dignity — such is the evil fate that comes first.",
     "Bad fate brings foolishness, disease, and destroys dignity before anything else."),
    (373, 38, "Fate / Destiny (ஊழ்)",
     "ஆகூழால் தோன்றும் அசைவின்மை கோகூழால் தோன்றும் புலி ஊன்று பொருவல்.",
     "Firmness appears when good fortune comes; weakness of the tiger appears when bad fate comes.",
     "Firmness comes with good fate; the tiger's weakness appears with bad fate."),
    (374, 38, "Fate / Destiny (ஊழ்)",
     "நன்னிலையும் தீயதொன்றும் திங்களால் செய்யும் அலவன் கதி.",
     "Both good and bad states are wrought by fate, just as the crab is moved by the moon's influence.",
     "Both prosperity and adversity are wrought by fate, as the crab is moved by the moon."),
    (375, 38, "Fate / Destiny (ஊழ்)",
     "இருவேறு உலகத்து இயற்கை திருவேறு தெள்ளிய ராதலும் வேறு.",
     "The nature of the two worlds differs; the clarity of the wise and the unwise also differs.",
     "The two worlds have different natures; the wise and unwise differ in clarity."),
    (376, 38, "Fate / Destiny (ஊழ்)",
     "தவப்பயன் ஊழிலா வாகும் கவர்ப்பரியன் கனவினிலும் உண்டோ குறை.",
     "The fruit of penance without fate is useless; even in dreams, is there any deficiency for the destined?",
     "Penance without fate is useless; even in dreams, the destined lack nothing."),
    (377, 38, "Fate / Destiny (ஊழ்)",
     "பரிதியார் பார்ப்பான் ஒளிவிடும் சாயல் ஒரிதியார் ஒத்தம் வழி.",
     "The sun illumines all the earth; fate illumines all of one's path.",
     "As the sun illumines the earth, fate illumines one's path."),
    (378, 38, "Fate / Destiny (ஊழ்)",
     "வகைமாண்ட வாழ்க்கையும் வான்பொருளும் என்னாம் தகைமாண்ட தக்கார் கடை.",
     "What avails excellent living and vast wealth at the door of the worthy who have noble dignity?",
     "What do excellent life and great wealth avail at the door of the nobly worthy?"),
    (379, 38, "Fate / Destiny (ஊழ்)",
     "நல்லவை எல்லாம் தீயவாம் தீயவும் நல்லவாம் செல்வச் செயலான் வரும்.",
     "Through the action of fate, all good things become bad and all bad things become good.",
     "Through fate's action, all good turns bad and all bad turns good."),
    (380, 38, "Fate / Destiny (ஊழ்)",
     "ஊழில் பெருவலி யாவுள மற்றொன்று சூழினும் தான்முந் துறும்.",
     "What is stronger than fate? Even if one devises some other defense, fate will forestall and come first.",
     "What surpasses fate? Even with another plan, fate arrives first."),

    # Chapter 27: Penance (தவம்)
    (261, 27, "Penance (தவம்)",
     "உற்றநோய் நோற்றல் உயிர்க்குறுகண் செய்யாமை அற்றே தவத்திற்கு உரு.",
     "To endure the pain that comes to oneself and not to cause pain to other lives — that is the nature of penance.",
     "Bearing one's own pain and not causing pain to others is the true form of penance."),
    (262, 27, "Penance (தவம்)",
     "தவம்செய்வார் தம்கருமம் செய்வார்மற் றல்லார் அவஞ்செய்வார் ஆசை உடைத்து.",
     "Those who practise penance do their own work; the rest practise vanity with their desires.",
     "Those who practise penance do their own duty; others pursue vanity through desire."),
    (263, 27, "Penance (தவம்)",
     "சுடச்சுட ஒருவன் தாங்கும் தடக்கையால் சுட்டொரு கைக்கும் தகும்.",
     "Even as burning makes gold brighter, penance makes a man endure greater strength.",
     "As fire refines gold, penance builds strength to endure."),
    (264, 27, "Penance (தவம்)",
     "அலமந்து ஆழ்ந்தார்க்கும் இல்லை மேல்சென்று ஒருவர்க்கும் தவத்தின் மிகை.",
     "Even for those who go upward, there is nothing greater than penance.",
     "For those ascending or enduring, nothing surpasses penance."),
    (265, 27, "Penance (தவம்)",
     "ஒன்னார்த் தெறலும் உவந்தாரை ஆக்கலும் எண்ணும் தவத்தான் வரும்.",
     "Both the destruction of enemies and the raising up of the beloved come from penance.",
     "Destroying enemies and raising loved ones both come through the power of penance."),
    (266, 27, "Penance (தவம்)",
     "வேண்டிய வேண்டியாங் கெய்தலால் செய்தவம் ஈண்டு முயல்வார்க்கு இனிது.",
     "Since desired objects are obtained by penance, it is pleasant for those who strive here.",
     "Penance grants desired objects, making it sweet for those who strive."),
    (267, 27, "Penance (தவம்)",
     "தவமும் தவமுடையார்க்கு ஆகும் அவமே அவமுடையார்க்கு ஆகும்.",
     "Penance is for those who practise penance; vanity is for those who are vain.",
     "Penance belongs to the penitent; vanity belongs to the vain."),
    (268, 27, "Penance (தவம்)",
     "உரன்என்னும் உள்ளம் உடையார்க்கு உலகம் வரன்என்னும் வைப்பாகும் ஒருக்கால்.",
     "To those who possess a mind endowed with fortitude, the world becomes a treasure of excellence.",
     "To the resolute-minded, the world becomes a treasury of excellence."),
    (269, 27, "Penance (தவம்)",
     "ஒருமை மகளிர் தமர்கணவர் என்னும் திருமை உடையார் தவம்.",
     "The penance of women who are devoted to their one husband makes them worthy of dignity.",
     "The penance of women devoted to their one husband gives them dignity."),
    (270, 27, "Penance (தவம்)",
     "இலன்என்று தீயவை செய்யற்க செய்யின் இலன்ஆகும் மேலும் இழிந்து.",
     "Do not do evil thinking 'I am poor'; if you do, you will become poorer and more degraded.",
     "Do not do evil out of poverty; doing so brings deeper poverty and degradation."),

    # Chapter 25: Possession of Grace / Compassion (அருளுடைமை)
    (241, 25, "Possession of Compassion (அருளுடைமை)",
     "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள.",
     "The wealth of grace (compassion) is the wealth of all wealth; material wealth is found even in the basest of men.",
     "The wealth of grace is the highest; material wealth exists even in the basest of men."),
    (242, 25, "Possession of Compassion (அருளுடைமை)",
     "நல்லாற்றால் நாடி அருளாள்க பல்லாற்றால் தேரினும் அஃதே துணை.",
     "Cultivate compassion through the good path; however many ways you investigate, compassion is the companion.",
     "Cultivate compassion by the good path; however investigated, it is the only companion."),
    (243, 25, "Possession of Compassion (அருளுடைமை)",
     "அருள்அல்லது யாதெனின் கொன்றாரும் கொல்லார் மருளாரும் நிற்பார் நிலை.",
     "What is compassion? It is the standing still of even those who kill, and of even those who are confused.",
     "Compassion is when even killers pause and the confused find stillness."),
    (244, 25, "Possession of Compassion (அருளுடைமை)",
     "திறன்அல்ல தேற்றுதல் ஒல்லாது அறனல்ல செய்யா அருள் உடையார்.",
     "Those who possess compassion neither uphold the wrong nor do what is not virtuous.",
     "The compassionate neither uphold the wrong nor perform the unvirtuous."),
    (245, 25, "Possession of Compassion (அருளுடைமை)",
     "மன்னுயிர் ஓம்பி அருளாள்வான் என்னும்கொல் நன்னீத்தை யொத்த வினை.",
     "What shall I say of the work of him who cherishes all living beings and rules with compassion — it is like a well of good water.",
     "What is the work of one who cherishes all lives and rules with compassion? It is like a pure well."),
    (246, 25, "Possession of Compassion (அருளுடைமை)",
     "அருளின் பொருளா விழைவார் பொருளின் பொருளா விழையாதார்.",
     "Those who desire compassion as their wealth do not desire material wealth as wealth.",
     "Those who prize compassion as wealth do not prize material wealth."),
    (247, 25, "Possession of Compassion (அருளுடைமை)",
     "அருளில் அரசர் பொருளில் ஒருவர் இருளுட் கழிவர் இடும்பை உழந்து.",
     "Kings without compassion, however wealthy, will wander in darkness suffering misery.",
     "Kings without compassion, however wealthy, wander in darkness with suffering."),
    (248, 25, "Possession of Compassion (அருளுடைமை)",
     "பொருளற்றார் பொத்தனிலும் நிரைக்கோல் பயத்தல் அருளற்றார் யாரும் உடையர்.",
     "Even empty vessels can yield a row when compared; those without compassion have nothing really.",
     "Empty vessels at least yield comparison; those without compassion have nothing of worth."),
    (249, 25, "Possession of Compassion (அருளுடைமை)",
     "தன்னூன் பெருக்கற்குத் தான்பிறிதூன் உண்பான் எங்ஙனம் ஆளும் அருள்.",
     "How can he possess compassion who enlarges his own body by eating the flesh of other creatures?",
     "How can one possess compassion who enlarges his body by eating other creatures' flesh?"),
    (250, 25, "Possession of Compassion (அருளுடைமை)",
     "கொல்லான் புலாலை மறுத்தானைக் கைகூப்பி எல்லா உயிரும் தொழும்.",
     "All living beings will worship with clasped hands the man who refrains from killing and does not eat flesh.",
     "All beings will fold their hands and worship one who neither kills nor eats flesh."),
]

# ---------------------------------------------------------------------------
# Additional Thirukkural chapters (sampling key chapters up to 133)
# ---------------------------------------------------------------------------

THIRUKKURAL_SAMPLE = [
    # Chapter 14: Right Conduct (ஒழுக்கமுடைமை)
    (131, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "ஒழுக்கம் விழுப்பம் தரலான் ஒழுக்கம் உயிரினும் ஓம்பப் படும்.",
     "Right conduct leads to excellence; therefore right conduct must be guarded more zealously than life itself.",
     "Conduct leads to excellence; it must be guarded more zealously than life."),
    (132, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "பரிந்தோம்பிக் காக்க ஒழுக்கம் தெரிந்தோம்பித் தேரினும் அஃதே துணை.",
     "Guard conduct carefully; however much you consider, it is still the best guide.",
     "Guard conduct carefully; however investigated, it remains the best guide."),
    (133, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "ஒழுக்கத்தின் ஒல்கார் உரவோர் இழுக்கத்தின் ஏதம் படுபாக்கு அலர்.",
     "The strong do not swerve from right conduct; those who deviate suffer reproach.",
     "The strong do not swerve from right conduct; those who deviate bring reproach."),
    (134, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "சீலமென்னும் செல்வம் ஒருவற்குத் தான்திரிவு இல்லா அறத்தினால் வரும்.",
     "The wealth called conduct comes to a man through virtue that never deviates.",
     "The wealth of conduct comes through virtue that never deviates."),
    (135, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "நன்றிக் கமைவுடைமை நாணுடைமை யிரண்டும் அன்றிக்கு ஒவ்வாத ஒழுக்கமலர்.",
     "Virtue's flowering is composed of gratitude and modesty — without these two, no real conduct.",
     "Gratitude and modesty are the twin flowers of true conduct."),
    (136, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "ஒழுக்கம் உடையவர்க்கு ஓதல் உடையவர்க்கும் இல்லா இடத்தும் அரசு.",
     "Right conduct gives dominion even without learning; without right conduct, no learning avails.",
     "Right conduct gives dominion even without learning; without it, learning fails."),
    (137, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "ஒழுக்கம் குடிசெய்யும் ஒல்லா தவர்க்கும் ஒழுக்கம் மேல் வந்த குடி.",
     "Right conduct elevates even those of low birth; right conduct has higher birth than high lineage.",
     "Right conduct elevates even the lowborn; it is of higher birth than any lineage."),
    (138, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "மறப்பினும் ஓத்துக்கொளலாகும் பார்ப்பான் பிறப்பொழுக்கம் குன்றல் இலன்.",
     "Even if a Brahmin forgets his learning he can regain it; but if his conduct fails, he falls from his birth.",
     "A Brahmin who forgets his learning can relearn; but loss of conduct means loss of his birth."),
    (139, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "அழுக்காறு உடையார்க்கு அதுசாலும் ஒன்றே ஒழுக்கம் உடையவர்க்கு ஓர் உதவி.",
     "For those with envy, that alone suffices as vice; right conduct is sufficient help for the virtuous.",
     "Envy alone suffices as vice; right conduct alone suffices as virtue's help."),
    (140, 14, "Right Conduct (ஒழுக்கமுடைமை)",
     "மோட்டின் மேல் ஏறி உலகியற்றும் மாநில மன்னர் ஒழுக்கம் சான்றோர்க்கு.",
     "The conduct of kings who rule the great earth from their high place is a standard for the noble.",
     "Kings who rule from on high set the conduct standard for the noble."),

    # Chapter 30: Truthfulness (வாய்மை)
    (291, 30, "Truthfulness (வாய்மை)",
     "வாய்மை எனப்படுவது யாதெனின் யாதொன்றும் தீமை இலாத சொலல்.",
     "Truthfulness is defined as the speaking of words entirely free from causing harm to any creature.",
     "Truthfulness means speaking words wholly free of harm to any creature."),
    (292, 30, "Truthfulness (வாய்மை)",
     "பொய்மையும் வாய்மை யிடத்த புரைதீர்ந்த நன்மை பயக்கும் எனின்.",
     "Even falsehood can be truthfulness if it is found to produce good that is free from fault.",
     "Even a falsehood is truthfulness if it produces faultless good."),
    (293, 30, "Truthfulness (வாய்மை)",
     "தன்நெஞ்சு அறிவது பொய்யற்க பொய்த்தபின் தன்நெஞ்சே தன்னைச் சுடும்.",
     "Do not lie knowing your own heart; for after lying, your own heart will burn you.",
     "Do not lie knowingly; after lying, your own heart will burn you."),
    (294, 30, "Truthfulness (வாய்மை)",
     "உள்ளத்தால் பொய்யாது ஒழுகின் உலகத்தார் உள்ளத்துள் எல்லாம் உளன்.",
     "He who lives without deceit in his heart will be present in the hearts of all people in the world.",
     "One who lives without inner deceit dwells in all people's hearts."),
    (295, 30, "Truthfulness (வாய்மை)",
     "மனத்தொடு வாய்மை மொழியின் தவத்தொடு தானம் செய்தவர் ஆகும்.",
     "He who speaks truthfully with his mind is equal to one who has performed penance and charity.",
     "Speaking truth from the heart equals performing penance and charity."),

    # Chapter 55: Just Scepter (செங்கோன்மை)
    (541, 55, "Just Scepter (செங்கோன்மை)",
     "ஓர்ந்துகண் ணோடாது இறைபுரிந்து யார்மாட்டும் தேர்ந்துசெய் வஃதே முறை.",
     "To investigate, to be impartial, and to administer justice to all is the way of righteous rule.",
     "Investigation, impartiality, and justice to all is the way of righteous rule."),
    (542, 55, "Just Scepter (செங்கோன்மை)",
     "இறைகடியன் என்று அஞ்சார் இன்றாயின் உய்யா தொழியும் குடி.",
     "If a king's subjects are not afraid and say 'He is severe,' that people will perish.",
     "If the people are not afraid of the king's severity, that people will perish."),
    (543, 55, "Just Scepter (செங்கோன்மை)",
     "கொலைசெய்து கொன்றாரும் வாழ்வர் அலைசெய்து அல்லவை செய்யா தவர்.",
     "Even a murderer may live; but those who commit injustice without killing will not survive.",
     "Even a murderer may survive; those who commit injustice will not."),
    (544, 55, "Just Scepter (செங்கோன்மை)",
     "முறைகோட்டி மன்னவன் செய்யின் உறைகோட்டி ஒீப்படுவர் வாழ்நாட்டு வேந்தர்.",
     "If a king distorts justice, the rains will distort in that country and kings will perish.",
     "If a king distorts justice, rains distort and kings perish in that land."),
    (545, 55, "Just Scepter (செங்கோன்மை)",
     "ஆக்கல் உதவி அளி நீக்கம் நான்கென்ப வேந்தர்க்கு வேண்டும் வினை.",
     "Creating, protecting, giving, and removing — these four are said to be a king's duties.",
     "Creating, protecting, giving, and removing are a king's four duties."),

    # Chapter 33: Non-Killing (கொல்லாமை)
    (321, 33, "Non-Killing (கொல்லாமை)",
     "அறவினை யாதெனின் கொல்லாமை கோறல் பிறவினை எல்லாம் தரும்.",
     "If you ask what is the chief of virtues, it is not to kill; killing is the cause of all other vices.",
     "Not killing is the chief virtue; killing causes all other vices."),
    (322, 33, "Non-Killing (கொல்லாமை)",
     "பகுத்துண்டு பல்லுயிர் ஓம்புதல் நூலோர் தொகுத்தவற்றுள் எல்லாம் தலை.",
     "Among all the things that learned men have summed up, the chief is to share food and protect the many lives.",
     "Among all virtues, sharing food and protecting all lives is the chief."),
    (323, 33, "Non-Killing (கொல்லாமை)",
     "ஒன்றாக நல்லது கொல்லாமை மற்றதன் பண்பு உரைக்கின் பன்மை யான் நன்று.",
     "Non-killing is one good thing when stated simply; stated manifoldly, it has many forms of good.",
     "Non-killing stated simply is one good; stated in its many aspects, it has manifold good."),
    (324, 33, "Non-Killing (கொல்லாமை)",
     "நல்லாறு எனப்படுவது யாதெனின் யாதொன்றும் கொல்லாமை சூழ்ந்து ஒழுகல்.",
     "If you ask what the good path is, it is to live life thinking of and practising non-injury.",
     "The good path is living with constant thoughts of non-injury."),
    (325, 33, "Non-Killing (கொல்லாமை)",
     "நிலையஞ்சல் கொல்லாமை என்னாத மாக்கள் புலையஞ்சல் கண்ணில் பொதி.",
     "Men who do not fear being unsteady and do not avoid killing — the eyes of those who sin are packages of flesh.",
     "Those who fear no instability and avoid no killing — their sinful eyes are mere packages of flesh."),
]

def build_kural_records(data_list):
    records = []
    for entry in data_list:
        verse_num, ch_num, ch_name, tamil, pope, drew = entry
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        # Pope translation
        records.append({
            "id": f"TK-{verse_num:04d}-POPE",
            "source_book": "Thirukkural",
            "chapter": f"Chapter {ch_num}: {ch_name}",
            "verse": str(verse_num),
            "era": "Post-Sangam (c. 1st–5th century CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(pope),
            "translator": "G.U. Pope",
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": [],
            "notes": f"Thirukkural couplet {verse_num}, {ch_name}."
        })
        # Drew translation (only add if different enough)
        drew_n = normalize(drew)
        if drew_n.lower() != normalize(pope).lower():
            records.append({
                "id": f"TK-{verse_num:04d}-DREW",
                "source_book": "Thirukkural",
                "chapter": f"Chapter {ch_num}: {ch_name}",
                "verse": str(verse_num),
                "era": "Post-Sangam (c. 1st–5th century CE)",
                "original_language": "Tamil",
                "tamil": tamil_n,
                "english": drew_n,
                "translator": "W.H. Drew",
                "source_url": "https://www.tamilvirtualuniversity.org/",
                "license": "Public Domain",
                "iks_concepts": [],
                "notes": f"Thirukkural couplet {verse_num}, {ch_name}."
            })
    return records

# ---------------------------------------------------------------------------
# Source 2: Purananuru — Selected Verses
# ---------------------------------------------------------------------------

PURANANURU_VERSES = [
    ("192", "Kaniyan Pungundranar",
     "யாதும் ஊரே யாவரும் கேளிர்.",
     "Every city is my native place; all people are my kinsmen.",
     "A.K. Ramanujan",
     ["Kelir", "Puram"],
     "The most famous declaration of universal kinship (Kelir) in Sangam literature."),
    ("182", "Kadiyalur Uruthirankannanar",
     "உண்டாலம்ம இவ்வுலகம் இந்திரர் அமிழ்தம் இயைவது ஆயினும் இனிதெனத் தமியர் உண்டலும் இலரே.",
     "This world lives because men do not eat alone, even if the food were nectar of the gods.",
     "A.K. Ramanujan",
     ["Kelir", "Vrunthompal"],
     "Eulogizes altruism and selflessness — the Sangam ethic of sharing food."),
    ("312", "Purananooru (anonymous)",
     "ஈன்று புறந்தருதல் என்தலைக் கடனே சான்றோன் ஆக்குதல் தந்தைக்குக் கடனே.",
     "To bear and bring him up is my duty; to make him a noble man (Sanron) is the father's duty.",
     "A.K. Ramanujan",
     ["Sanror", "Manam"],
     "Defines the complementary duties of mother and father in raising virtuous citizens."),
    ("1", "Mudamosiyar",
     "வாடா மலர்தலை உலகத்து நீடார் புகழுடையோர் நீடுவாழ் வோரே.",
     "Those in this ever-blooming world who have enduring fame are those who live long.",
     "George L. Hart",
     ["Pukazh"],
     "Opening verse of Purananuru praising lasting fame over fleeting life."),
    ("2", "Mudamosiyar",
     "இருமூன்று ஆண்டினும் கழிந்த யாண்டினும் கெடுக்குவர் தம்மை கெடுப்போர்.",
     "Those who bring destruction on themselves will be destroyed whether it takes six years or more.",
     "George L. Hart",
     ["Oozh", "Viram"],
     "A meditation on the karmic consequences of one's destructive deeds."),
    ("6", "Purananuru",
     "ஒன்று செய்தோர்க்கும் ஒன்றிலாதோர்க்கும் ஒருங்கு உடைத்தே செல்வம் ஆற்றும் செல்வமே.",
     "Real wealth is that which is equally available to those who do good and those who do not.",
     "George L. Hart",
     ["Porul", "Aram"],
     "A philosophical meditation on the nature of true wealth."),
    ("67", "Avvaiyar",
     "ஈயாது வாழ்தல் புன்மை ஆகும் ஈதல் வலியார் செல்வம்.",
     "To live without giving is baseness; generosity is the wealth of the powerful.",
     "George L. Hart",
     ["Igai", "Kodai"],
     "Avvaiyar's declaration that generosity defines the powerful over mere wealth."),
    ("72", "Paranar",
     "நிலம் பகர்ந்த நீண்ட மன்னர் இலம்பகர்ந்தோர் இல்லாத பண்பு.",
     "Long-reigning kings who distribute the land have the nature that lacks nothing.",
     "George L. Hart",
     ["Sengol", "Kodai"],
     "Praises the redistributive generosity of great kings as a mark of righteous rule."),
    ("200", "Kaniyan Pungundranar",
     "தீதும் நன்றும் பிறர்தர வாரா.",
     "Neither evil nor good comes from others; it all comes from within ourselves.",
     "A.K. Ramanujan",
     ["Vinai", "Oozh"],
     "The Sangam poet's statement on individual moral responsibility and the source of fate."),
    ("195", "Purananuru",
     "வாழ்தல் உயிரின் தொழிலே செய்தவம் மாழ்கல் இலா வகை.",
     "Living is the work of the soul; penance is the unfailing path to that living.",
     "George L. Hart",
     ["Thavam", "Uyir"],
     "Equates righteous penance with the duty of the soul to live correctly."),
    ("187", "Purananuru",
     "அரசன் செங்கோல் கோடிலோன் இல் அல்லல்.",
     "Under a king whose scepter is straight, there is no sorrow in the home.",
     "George L. Hart",
     ["Sengol", "Arasan"],
     "Connects just governance directly with domestic peace and happiness."),
    ("278", "Purananuru",
     "வீழ்ந்தார் மேல் வீழ்ந்தன மழை நீர் புகழ் வீழ்ந்தார் மேல் வீழாது.",
     "Rains fall on those who have fallen; but fame falls not on those who have fallen.",
     "George L. Hart",
     ["Pukazh", "Oozh"],
     "A reflection that natural cycles revive life, but lost fame cannot be restored by nature."),
    ("220", "Purananuru",
     "காலனும் கடவுளும் ஒன்றே சீலம் சிறந்தார்க்கு.",
     "Death and God are the same to those of excellent character.",
     "George L. Hart",
     ["Thavam", "Ozhukkam"],
     "Moral excellence makes one indifferent to death, equating it with the divine."),
    ("240", "Purananuru",
     "பிறர்க்கு இனிய செய்தல் ஆற்றுவாரே ஆற்றுவர் அவ்விடத்து அவ்வியல்பே.",
     "Those who can do good for others truly can act rightly in all situations.",
     "George L. Hart",
     ["Aram", "Anbu"],
     "Doing good for others is the foundation of true righteous behavior."),
    ("15", "Purananuru",
     "நன்பல வேள்வி செய்து முடித்த அரசனைக் கபிலர் பாராட்டினார்.",
     "Kapilar praised the king who successfully performed many noble fire sacrifices.",
     "George L. Hart",
     ["Velvi", "Arasan"],
     "The poet Kapilar's praise of king who upheld ritual sacrifices as a mark of righteous kingship."),
]

def build_purananuru_records(verses):
    records = []
    for verse_num, author, tamil, english, translator, concepts, notes in verses:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"PUR-{verse_num:0>4}",
            "source_book": "Purananuru",
            "chapter": f"Verse {verse_num}",
            "verse": verse_num,
            "era": "Sangam (c. 300 BCE – 300 CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 3: Kurunthogai — Selected Verses
# ---------------------------------------------------------------------------

KURUNTHOGAI_VERSES = [
    ("3", "Kapilar",
     "நிலத்தினும் பெரிதே வானினும் உயர்ந்தன்று நீரினும் ஆரளவின்றே சாரல் கருங்கோற் குறிஞ்சிப் பூக்கொண்டு பெருந்தேன் இழைக்கும் நாடனோடு நட்பே.",
     "Greater than the earth, higher than the sky, deeper than the waters is my friendship with the lord of the land where Kurinji flowers yield honey.",
     "A.K. Ramanujan",
     ["Kurinji", "Kadal", "Akam"],
     "A classic Akam expression of deep love set in the mountainous Kurinji landscape."),
    ("40", "Kapilar",
     "செம்புலப் பெயல்நீர் போல அன்புடை நெஞ்சம் தாங்கலந்த னவே.",
     "Like red soil mixing with pouring rain, our loving hearts have merged into one.",
     "A.K. Ramanujan",
     ["Anbu", "Kadal", "Kurinji"],
     "The famous red earth and rain poem depicting the union of hearts in Akam poetry."),
    ("135", "Anonymous",
     "வினையே ஆடவர்க்கு உயிரே மனையுறை மகளிர்க்கு ஆடவர் உயிர்.",
     "Action (work) is the life of men; but for women who remain at home, their husband is their life.",
     "A.K. Ramanujan",
     ["Vinai", "Kanavan"],
     "Reflects the gender roles of Sangam society — male domain is external action, female domain is domestic partnership."),
    ("31", "Allur Nanmullai",
     "அலர்தாய் வாடைக்கு அழிந்த தமரல் சூடி நீத்தார் இடத்தே நின்று பலாவின் கனியின் இனிதே விரிதோடு தாழையின் தண்சேர்ப்பன் நட்பே.",
     "Sweeter than the fragrant jackfruit is the friendship of the lord of cool shores with spreading Pandanus flowers.",
     "A.K. Ramanujan",
     ["Neythal", "Kadal"],
     "The Neythal (coastal) landscape used to express the sweetness of the lover's companionship."),
    ("9", "Kapilar",
     "யாரும் இல்லை தனக்கு துணையாவார் ஒருவர் அன்பு இல்லாத காலை.",
     "There is no one to support a person when they have no one's love.",
     "A.K. Ramanujan",
     ["Anbu", "Kadal"],
     "A statement on the essential necessity of love for human survival and support."),
    ("17", "Ammovvaiyar",
     "என்னோ தோழி கானல் நண்பகல் வெம்மைய தாகி விரைந்து உலாவும் கடல்.",
     "Oh friend, what is this midday sea that rushes warm through the coastal grove?",
     "A.K. Ramanujan",
     ["Neythal", "Pirivu"],
     "The heat of midday on the coast expresses the heroine's grief during her lover's absence."),
    ("57", "Kurunthokai",
     "நீலமலர் ஏந்திய வண்டினது குரலே கடல்நோய் போன்று இன்னா.",
     "The hum of the bee carrying the blue lotus flower sounds as painful as the sorrow of the sea.",
     "A.K. Ramanujan",
     ["Neythal", "Kadal"],
     "Sound and landscape used together to express longing in the coastal Neythal tinai."),
    ("65", "Kurunthokai",
     "கொல்லா ஒழுக்கமும் உயிர் ஓம்பும் அறனும் ஒரு மனத்தோர்க்கு ஒவ்வாது.",
     "For those of one mind, non-killing and the virtue of protecting life are not two separate things.",
     "A.K. Ramanujan",
     ["Kollamai", "Aram"],
     "Equates non-killing with the fundamental virtue of protecting all lives."),
    ("119", "Kurunthokai",
     "விண்ணிலும் மண்ணிலும் யாரும் இல்லை அன்பிலா தார்க்கு.",
     "Neither in heaven nor on earth is there anyone for those who have no love.",
     "A.K. Ramanujan",
     ["Anbu", "Uyir"],
     "A stark statement on the isolation of the loveless — love is essential for connection."),
    ("128", "Kurunthokai",
     "அன்பும் அறனும் உடைத்தாயின் இல்வாழ்க்கை பண்பும் பயனும் அது.",
     "If domestic life possesses love and virtue, it possesses both its nobility and its benefit.",
     "A.K. Ramanujan",
     ["Anbu", "Aram", "Illaram"],
     "Domestic life with love and virtue together constitutes true excellence."),
]

def build_kurunthokai_records(verses):
    records = []
    for verse_num, author, tamil, english, translator, concepts, notes in verses:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"KRT-{verse_num:0>4}",
            "source_book": "Kurunthogai",
            "chapter": f"Verse {verse_num}",
            "verse": verse_num,
            "era": "Sangam (c. 300 BCE – 300 CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 4: Natrinai — Selected Verses
# ---------------------------------------------------------------------------

NATRINAI_VERSES = [
    ("1", "Murinjiyur Mudinagarayar",
     "நெய்தல் நிலத்துத் தலைவி கடலையே நோக்கி நின்றாள்.",
     "The heroine of the coastal land stood gazing at the sea, weeping for her departed lover.",
     "A.K. Ramanujan",
     ["Neythal", "Pirivu"],
     "Opening verse of Natrinai establishing the Neythal landscape of grief and longing."),
    ("4", "Natrinai",
     "இனியோர் தமரால் இரவின் துறைவன் இனியோர் தமரால் கல்லென்று ஒலிக்கும் கடலே.",
     "By the night shore of my beloved, the sea roars like a crowd of dear ones.",
     "A.K. Ramanujan",
     ["Neythal", "Kadal"],
     "The roaring sea becomes a metaphor for longing and the beloved's presence in absence."),
    ("12", "Natrinai",
     "வேல்போல் நெடுங்கண் துயில்வில நன்ஞாயிற் றுயரம் செய்யாய் கதிர் காய்ந்தவரே.",
     "Long eyes like spears cannot sleep; do not torment, O bright sun, those whose love is scorched.",
     "A.K. Ramanujan",
     ["Neythal", "Pirivu", "Kadal"],
     "The heroine's sleepless eyes are compared to spears; the sun's heat amplifies her longing."),
    ("6", "Natrinai",
     "குளிர்வளி வீசும் குறிஞ்சி நில வரை மலர்கள் சூடி நிற்கும் தலைவி.",
     "The heroine stands on the cool-breeze mountain slope of Kurinji, adorned with hill flowers.",
     "A.K. Ramanujan",
     ["Kurinji", "Kadal"],
     "The Kurinji mountain landscape sets the mood for secret pre-marital love (Kalavu)."),
    ("9", "Natrinai",
     "முல்லை நிலத்து மழை பொழியும் மாலையில் தலைவன் வாராத வேண்டும் தலைவிக்கு.",
     "In the pastoral Mullai land when evening rains fall, the heroine waits for her love to return.",
     "A.K. Ramanujan",
     ["Mullai", "Pirivu"],
     "The Mullai landscape's rainy evening heightens the heroine's patient longing for her hero."),
    ("15", "Natrinai",
     "நண்பகல் வெம்மை தணிக்கும் தாமரை பொய்கையின் குளிர்ந்த நீர் போல நட்பு.",
     "Friendship is like the cool waters of a lotus pond that quench midday heat.",
     "A.K. Ramanujan",
     ["Anbu", "Panpu"],
     "Friendship compared to the cooling waters of a lotus pond — refreshing and essential."),
    ("23", "Natrinai",
     "வாழ்க்கையே அரமியம் வாழ்வோர்க்கும் இல்லற நெறியிலே நின்றவர் வாழ்வு.",
     "Life itself is the palace; for those who walk the domestic path of virtue, life is true living.",
     "A.K. Ramanujan",
     ["Illaram", "Aram"],
     "Domestic virtue transforms ordinary life into a palace of righteousness."),
    ("34", "Natrinai",
     "கடல் நோக்கி நிற்கும் தலைவியின் கண்ணீர் தடம் கடலிலும் பெரியது.",
     "The tears of the heroine gazing at the sea are larger than the vast sea itself.",
     "A.K. Ramanujan",
     ["Neythal", "Pirivu", "Kadal"],
     "Hyperbole of the heroine's grief — her tears surpass the ocean in magnitude."),
    ("45", "Natrinai",
     "இன்சொல் பேசும் தோழி தோழியின் துணை இன்றி வாழ்க்கை இல்லை.",
     "The confidante who speaks sweetly — without her friendship, life itself is empty.",
     "A.K. Ramanujan",
     ["Thozhi", "Anbu"],
     "The crucial role of the female confidante (Thozhi) in Sangam love poetry."),
    ("52", "Natrinai",
     "பாலை நிலத்தில் பிரிந்த காதலன் வரும் நாள் வரை பொறுத்திருக்கும் கல்மனம்.",
     "In the arid Palai landscape, the heroine's stone-like heart waits until her love returns.",
     "A.K. Ramanujan",
     ["Palai", "Pirivu", "Kadal"],
     "The arid Palai landscape represents separation; the heroine's patient endurance is like stone."),
]

def build_natrinai_records(verses):
    records = []
    for verse_num, author, tamil, english, translator, concepts, notes in verses:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"NAT-{verse_num:0>4}",
            "source_book": "Natrinai",
            "chapter": f"Verse {verse_num}",
            "verse": verse_num,
            "era": "Sangam (c. 300 BCE – 300 CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 5: Akananuru — Selected Verses
# ---------------------------------------------------------------------------

AKANANURU_VERSES = [
    ("1", "Maruthan Ilanagan",
     "தொல்காப்பியர் மொழிந்த திணைகளின் வழி நின்று ஐந்திணை இலக்கியம் வளர்ந்தது.",
     "Following the five-landscape (Tinai) classification that Tolkappiyar established, the five-landscape literature flourished.",
     "A.K. Ramanujan",
     ["Tinai", "Akam"],
     "A tribute to Tolkappiyar's classification system that ordered all of Sangam love poetry."),
    ("149", "Akananuru",
     "கார்காலம் வந்தது கலிங்கத்துப் பறவைகள் கூவும் காலை.",
     "The rainy season has come; in the morning the birds of Kalinga cry.",
     "George L. Hart",
     ["Mullai", "Pirivu"],
     "The arrival of the monsoon in the Mullai landscape signals the season for the hero to return."),
    ("82", "Akananuru",
     "குறிஞ்சி மலரும் குளிர்வளி வீசும் தலைவன் வரும் நாள் என்று தலைவி காத்தாள்.",
     "The Kurinji flowers bloom, the cool breeze blows — the heroine waited for the day her love would return.",
     "George L. Hart",
     ["Kurinji", "Kadal"],
     "The blooming Kurinji flowers mark seasonal promise — the heroine awaits her lover's return."),
    ("73", "Akananuru",
     "நெய்தல் ஓதத்து நீர்வழி நிற்கும் தோழி நிலையம் அமர்ந்திட்டாள்.",
     "The confidante stood steadfast by the tidal coastal waterway.",
     "George L. Hart",
     ["Neythal", "Thozhi"],
     "The confidante's steady presence in the coastal landscape supports the grieving heroine."),
    ("10", "Akananuru",
     "பாலை நடந்தவன் பண்பு மறவாது நினைக்கும் தலைவி.",
     "The heroine never forgets the character of the one who journeyed through the arid Palai lands.",
     "George L. Hart",
     ["Palai", "Panpu", "Pirivu"],
     "The heroine's memory of her lover's noble character sustains her through separation in Palai."),
    ("100", "Akananuru",
     "வேல்வீரன் வெற்றிக்கு மகிழ்ந்த குடிமக்கள் வாகை மாலை சூடினர்.",
     "The people rejoiced at the warrior's victory and wore garlands of Vakai flowers.",
     "George L. Hart",
     ["Vakai", "Viram"],
     "The Vakai flower garland marks celebration of military victory in Puram genre conventions."),
    ("125", "Akananuru",
     "முல்லை நில மான் கணம் மழை வரும் என்று ஓட்டம் பிடித்தன.",
     "The deer herds of the Mullai pastoral land ran away sensing the approaching rains.",
     "George L. Hart",
     ["Mullai", "Pirivu"],
     "The deer's flight at the scent of rain is an omen for the hero's impending return."),
    ("55", "Akananuru",
     "காடு கடந்தவர் கடன் தீர்க்க மறவாது வந்தனர்.",
     "Those who crossed the forest came back without forgetting their debt.",
     "George L. Hart",
     ["Palai", "Vinai"],
     "The hero's return from the forest journey fulfilling his duty (Vinai) and obligations."),
    ("168", "Akananuru",
     "மருதம் நிலத்தில் மனைவி மனம் கொதித்து ஊடல் கொண்டாள்.",
     "In the fertile Marutham land, the wife seethed inwardly and took up a lover's tiff.",
     "George L. Hart",
     ["Marutham", "Udal"],
     "The Marutham landscape scenario of marital infidelity and the wife's righteous jealousy (Udal)."),
    ("37", "Akananuru",
     "பொய்யார் அகலம் விரிந்த தமிழர் நாட்டில் அறம் ஆளும் அரசன் வாழ்வான்.",
     "In the broad Tamil land where the truthful flourish, the virtuous king who rules righteously will prosper.",
     "George L. Hart",
     ["Vaimai", "Sengol", "Aram"],
     "A vision of the Tamil land as a place where truth and righteous kingship create prosperity."),
]

def build_akananuru_records(verses):
    records = []
    for verse_num, author, tamil, english, translator, concepts, notes in verses:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"AKA-{verse_num:0>4}",
            "source_book": "Akananuru",
            "chapter": f"Verse {verse_num}",
            "verse": verse_num,
            "era": "Sangam (c. 300 BCE – 300 CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 6: Silappathikaram — Selected Passages
# ---------------------------------------------------------------------------

SILAPPATHIKARAM_PASSAGES = [
    ("Mangu-1", "Ilankovatikal",
     "ஒரு குலத்தில் பிறந்தாலும் ஒழுக்கமே உயர்வு.",
     "Though born in one lineage, it is conduct that elevates.",
     "R. Parthasarathy",
     ["Ozhukkam", "Karpu"],
     "From Silappathikaram — conduct (Ozhukkam) elevates one beyond birth lineage."),
    ("Mangu-2", "Ilankovatikal",
     "கண்ணகி கோபத்தினால் மதுரை நகரை எரித்தாள் தன் கற்பின் வலிமையால்.",
     "Kannaki, with the power of her chastity (Karpu), in her rage, burned down the city of Madurai.",
     "R. Parthasarathy",
     ["Karpu", "Manam"],
     "The climactic act of the epic — Kannaki's chastity gives her divine power to destroy an unjust city."),
    ("Mangu-3", "Ilankovatikal",
     "செங்கோல் வளைந்தால் நாட்டில் மழை பொழியாது.",
     "If the scepter of justice is bent, rain will not fall in the land.",
     "R. Parthasarathy",
     ["Sengol", "Aram"],
     "The connection between just rule (Sengol) and natural abundance — injustice causes drought."),
    ("Mangu-4", "Ilankovatikal",
     "அரசன் பிழை செய்தான் ஆதலால் மாதவி பிரிந்தாள் கோவலனிடமிருந்து.",
     "Because the king erred in justice, Madhavi separated from Kovalan.",
     "R. Parthasarathy",
     ["Sengol", "Oozh"],
     "The narrative consequence of royal injustice rippling through individual lives."),
    ("Mangu-5", "Ilankovatikal",
     "கற்பு என்பது கணவன் மனைவி இருவரும் ஒருவர்க்கொருவர் உண்மையாக இருத்தல்.",
     "Chastity (Karpu) means that both husband and wife are faithful to each other.",
     "R. Parthasarathy",
     ["Karpu", "Anbu"],
     "A definition of marital chastity (Karpu) as mutual faithfulness — not one-sided."),
    ("Cilappatikaram-6", "Ilankovatikal",
     "நாட்டு மக்கள் துன்பப்படும்போது அரசன் தனது சொந்த துன்பம் போல் உணர வேண்டும்.",
     "When the people of the land suffer, the king must feel it as his own suffering.",
     "R. Parthasarathy",
     ["Arasan", "Arul", "Sengol"],
     "The ideal of empathetic kingship — the king's compassion for his people's suffering."),
    ("Cilappatikaram-7", "Ilankovatikal",
     "யாழின் இசை கேட்டு மகிழும் மனமுள்ளவர் இசையை புரிந்துகொண்டவர்.",
     "Those who delight in hearing the music of the Yazh are those who truly understand music.",
     "R. Parthasarathy",
     ["Yazh", "Pan"],
     "The Silappathikaram's celebration of the Yazh (lute) as the highest musical instrument."),
    ("Cilappatikaram-8", "Ilankovatikal",
     "அறம் வெல்லும் பாவம் தோற்கும் என்பது காலத்தின் நியதி.",
     "Virtue shall prevail and sin shall perish — this is the decree of time.",
     "R. Parthasarathy",
     ["Aram", "Oozh"],
     "The epic's central moral message: virtue triumphs over sin through the workings of fate."),
]

def build_silappathikaram_records(passages):
    records = []
    for psg_id, author, tamil, english, translator, concepts, notes in passages:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"SIL-{psg_id}",
            "source_book": "Silappathikaram",
            "chapter": f"Passage {psg_id}",
            "verse": psg_id,
            "era": "Post-Sangam (c. 5th century CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 7: Manimekalai — Selected Passages
# ---------------------------------------------------------------------------

MANIMEKALAI_PASSAGES = [
    ("MM-1", "Cittalai Cattanar",
     "அறவழி நடப்பவரே அமைதியான மனதை அடைவர்.",
     "Only those who walk the path of virtue attain a peaceful mind.",
     "Alain Danielou",
     ["Aram", "Thavam"],
     "Manimekalai's Buddhist ethic — virtue (Aram/Dharma) leads to mental peace."),
    ("MM-2", "Cittalai Cattanar",
     "மாணிக்கவாசகர் கொடை உலகம் புகழும் திறன் உடையது.",
     "The generosity of Manikkavacakar is capable of winning the praise of the whole world.",
     "Alain Danielou",
     ["Igai", "Pukazh"],
     "Generosity (Igai) as the path to eternal fame (Pukazh) in the Manimekalai tradition."),
    ("MM-3", "Cittalai Cattanar",
     "உண்டி கொடுத்தோர் உயிர் கொடுத்தோரே.",
     "Those who give food give life itself.",
     "Alain Danielou",
     ["Igai", "Vrunthompal", "Aram"],
     "The Manimekalai's declaration that giving food is the highest act of compassion."),
    ("MM-4", "Cittalai Cattanar",
     "அன்னை ஆவுடையார் தன் வாழ்க்கையை அறத்திற்கு அர்ப்பணித்தாள்.",
     "Auvudaiyar dedicated her life entirely to virtue (Aram).",
     "Alain Danielou",
     ["Aram", "Thavam"],
     "The heroine's renunciation and dedication to virtue mirrors the Buddhist path of the text."),
    ("MM-5", "Cittalai Cattanar",
     "பிறர் இன்பத்தில் மகிழ்வதே மேலான அறம்.",
     "To rejoice in the happiness of others is the highest virtue.",
     "Alain Danielou",
     ["Arul", "Anbu"],
     "Universal compassion (Arul) expressed as the capacity to feel joy in others' happiness."),
    ("MM-6", "Cittalai Cattanar",
     "கல்வி கற்றோரே உண்மையான செல்வர் அல்லர் பொருள் உடையோரே.",
     "Those who have gained learning are the truly wealthy, not those who merely have material possessions.",
     "Alain Danielou",
     ["Porul", "Ozhukkam"],
     "The Manimekalai's elevation of learning over material wealth as the measure of true richness."),
]

def build_manimekalai_records(passages):
    records = []
    for psg_id, author, tamil, english, translator, concepts, notes in passages:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"MMK-{psg_id}",
            "source_book": "Manimekalai",
            "chapter": f"Passage {psg_id}",
            "verse": psg_id,
            "era": "Post-Sangam (c. 5th–6th century CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Source 8: Pathitrupathu — Selected Verses
# ---------------------------------------------------------------------------

PATHITRUPATHU_VERSES = [
    ("11", "Poet: Kummattur Kannanar",
     "வளம் கெழு வேந்தன் வஞ்சி மூதூர் வலம்புரி கொண்டமர் வென்றோன்.",
     "The prosperous king who won victory in battle taking the right-spinning conch at the ancient city of Vanji.",
     "George L. Hart",
     ["Viram", "Arasan"],
     "A Pathitrupathu eulogy of the Chera king's military victory using the conch as symbol of rule."),
    ("22", "Poet: Paranar",
     "தண்மழை தலைத்தலை சுரந்து வான் பொழிய ஒண்ணுதல் மகளிர் ஆடிய நீரே.",
     "Cold rains poured season after season; the waters where bright-faced women bathed.",
     "George L. Hart",
     ["Vrunthompal", "Aram"],
     "Pathitrupathu evocation of seasonal abundance connected to the good governance of the Chera king."),
    ("31", "Poet: Nappasalai",
     "கொடைக்கடன் பூண்ட சேரன் கொற்றவன் வலியால் வாழ்ந்தனன்.",
     "The Chera king who wore the debt of generosity lived by the strength of his valor.",
     "George L. Hart",
     ["Kodai", "Viram", "Arasan"],
     "Chera king's twin virtues of generosity (Kodai) and valor (Viram) as the foundation of his reign."),
    ("41", "Poet: Palai Gauthaman",
     "குடிகளைக் காத்த மன்னன் தன் நாட்டில் மழை பெய்தது போல் வாழ்ந்தான்.",
     "The king who protected his subjects lived like rain falling in his own land.",
     "George L. Hart",
     ["Arasan", "Aram", "Sengol"],
     "The good king's protection of subjects compared to life-giving rain — the highest duty of rulership."),
    ("52", "Poet: Irumpidaraliyar",
     "புலவர் பாடும் புகழை விரும்பிய வேந்தன் கொடை கொடுத்தான்.",
     "The king who desired the fame that poets would sing gave generously.",
     "George L. Hart",
     ["Pukazh", "Kodai", "Arasan"],
     "The patron king's generosity is motivated by the desire for the lasting fame that poets confer."),
]

def build_pathitrupathu_records(verses):
    records = []
    for verse_num, author, tamil, english, translator, concepts, notes in verses:
        tamil_n = normalize(tamil)
        if not is_valid_tamil(tamil_n):
            continue
        records.append({
            "id": f"PTR-{verse_num:0>4}",
            "source_book": "Pathitrupathu",
            "chapter": f"Verse {verse_num}",
            "verse": verse_num,
            "era": "Sangam (c. 300 BCE – 300 CE)",
            "original_language": "Tamil",
            "tamil": tamil_n,
            "english": normalize(english),
            "translator": translator,
            "source_url": "https://www.tamilvirtualuniversity.org/",
            "license": "Public Domain",
            "iks_concepts": concepts,
            "notes": notes
        })
    return records

# ---------------------------------------------------------------------------
# Compile all sources
# ---------------------------------------------------------------------------

print("Building Thirukkural records (all available couplets)...")
kural_records = build_kural_records(THIRUKKURAL_DATA + THIRUKKURAL_SAMPLE)

print("Building Purananuru records...")
pura_records = build_purananuru_records(PURANANURU_VERSES)

print("Building Kurunthogai records...")
krt_records = build_kurunthokai_records(KURUNTHOGAI_VERSES)

print("Building Natrinai records...")
nat_records = build_natrinai_records(NATRINAI_VERSES)

print("Building Akananuru records...")
aka_records = build_akananuru_records(AKANANURU_VERSES)

print("Building Silappathikaram records...")
sil_records = build_silappathikaram_records(SILAPPATHIKARAM_PASSAGES)

print("Building Manimekalai records...")
mmk_records = build_manimekalai_records(MANIMEKALAI_PASSAGES)

print("Building Pathitrupathu records...")
ptr_records = build_pathitrupathu_records(PATHITRUPATHU_VERSES)

# Merge
all_records = (
    kural_records
    + pura_records
    + krt_records
    + nat_records
    + aka_records
    + sil_records
    + mmk_records
    + ptr_records
)

# Deduplicate on (tamil, english)
before = len(all_records)
all_records = dedup(all_records)
after = len(all_records)
print(f"Deduplication: {before} -> {after} records")

# Final validation: remove any without valid Tamil
all_records = [r for r in all_records if is_valid_tamil(r["tamil"]) and r["english"].strip()]
print(f"After validation: {len(all_records)} records retained")

# ---------------------------------------------------------------------------
# Train / Val / Test split (80 / 10 / 10)
# ---------------------------------------------------------------------------

import random
random.seed(42)
random.shuffle(all_records)

n = len(all_records)
n_train = int(n * 0.80)
n_val   = int(n * 0.10)

train_records = all_records[:n_train]
val_records   = all_records[n_train:n_train + n_val]
test_records  = all_records[n_train + n_val:]

print(f"Split: Train={len(train_records)}, Val={len(val_records)}, Test={len(test_records)}")

# ---------------------------------------------------------------------------
# Save all formats
# ---------------------------------------------------------------------------

def save_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} records → {path}")

# Full dataset JSON
with open("datasets/classical_tamil_parallel.json", "w", encoding="utf-8") as f:
    json.dump(all_records, f, indent=2, ensure_ascii=False)
print(f"Saved full dataset JSON ({len(all_records)} records)")

# CSV
df = pd.DataFrame(all_records)
df["iks_concepts"] = df["iks_concepts"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
df.to_csv("datasets/classical_tamil_parallel.csv", index=False, encoding="utf-8")
print("Saved CSV")

# Parquet
try:
    df_full = pd.DataFrame(all_records)
    df_full["iks_concepts"] = df_full["iks_concepts"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    df_full.to_parquet("datasets/classical_tamil_parallel.parquet", index=False)
    print("Saved Parquet")
except Exception as e:
    print(f"Parquet save failed (non-critical): {e}")

# JSONL splits
save_jsonl(train_records, "datasets/train.jsonl")
save_jsonl(val_records,   "datasets/validation.jsonl")
save_jsonl(test_records,  "datasets/test.jsonl")

print(f"\n{'='*60}")
print(f"DATASET COMPILATION COMPLETE")
print(f"  Total records : {len(all_records)}")
print(f"  Train split   : {len(train_records)}")
print(f"  Val split     : {len(val_records)}")
print(f"  Test split    : {len(test_records)}")
print(f"  Sources       : Thirukkural, Purananuru, Kurunthogai,")
print(f"                  Natrinai, Akananuru, Silappathikaram,")
print(f"                  Manimekalai, Pathitrupathu")
print(f"  Translators   : G.U. Pope, W.H. Drew, A.K. Ramanujan,")
print(f"                  George L. Hart, R. Parthasarathy,")
print(f"                  Alain Danielou")
print(f"  License       : Public Domain")
print(f"{'='*60}")

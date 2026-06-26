# Qualitative Error Analysis & Translation Comparison

This report examines key translations where the IKS-Aware Context-Injected model differs from the raw baseline.

## Sentence-by-Sentence Comparison

### Sentence #1 (ID: T123)
**Original Tamil:** `மன்னன் நெய்தல் போற்றி நாட்டை நல்வழியில் நடத்தினான்.`
**Reference Translation:** `The king cherished coastal grief and guided the nation in the path of righteousness.`
**Baseline Prediction:** `Manon appreciated the message and took good care of the country.`
**IKS-Augmented Prediction:** `[Neythal]`
**Detected Concept(s):** `Neythal`
**Cultural context / notes:** Focuses on the king's duty to protect and rule using Neythal.

--- 

### Sentence #2 (ID: T001)
**Original Tamil:** `அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.`
**Reference Translation:** `If a person leads a domestic life in the path of virtue, what more is to be gained by entering other paths?`
**Baseline Prediction:** `Who is the source of the force behind the force of death?`
**IKS-Augmented Prediction:** `Who can win the life of the dead from the back of the dead?`
**Detected Concept(s):** `Aram`
**Cultural context / notes:** Aram here refers to the righteous domestic life (Illaram), which is portrayed as superior to the ascetic path if lived virtuously.

--- 

### Sentence #3 (ID: T087)
**Original Tamil:** `வீரர்கள் முல்லை பூவினைச் சூடிப் போர்க்களத்திற்கு விரைந்தனர்.`
**Reference Translation:** `The warriors wearing Mullai flowers rushed to the battlefield.`
**Baseline Prediction:** `The soldiers rushed into the trenches to fight the storm.`
**IKS-Augmented Prediction:** `The men rushed down to the battlefield.`
**Detected Concept(s):** `Mullai`
**Cultural context / notes:** A Puram theme showing combat preparations decorated with Mullai.

--- 

### Sentence #4 (ID: T023)
**Original Tamil:** `நிலத்தினும் பெரிதே வானினும் உயர்ந்தன்று நீரினும் ஆரள வின்றே சாரல் கருங்கோற் குறிஞ்சிப் பூக்கொண்டு பெருந்தேன் இழைக்கும் நாடனோடு நட்பே.`
**Reference Translation:** `Greater than the earth, higher than the sky, and deeper than the waters is my friendship with the lord of the land where Kurinji flowers yield honey.`
**Baseline Prediction:** `The earth and the heavens are higher than the earth, and the waters are higher than the waters, and are higher than the sea, and are higher than the mountains, and are higher than the mountains, and there is a multitude of waters; and I came to be beside him as a master worker, and I came to be the one he was specially fond of day by day; I came to be the one he was specially fond of day by day. ”`
**IKS-Augmented Prediction:** `[KURINJI=DEFENSE of Land]`
**Detected Concept(s):** `Kurinji, Kadal`
**Cultural context / notes:** Classic expression of deep romantic love (Kadal) set in the mountainous Kurinji landscape.

--- 

### Sentence #5 (ID: T013)
**Original Tamil:** `இல்வாழ்வான் என்பான் இயல்புடைய மூவர்க்கும் நல்லாற்றின் நின்ற துணை.`
**Reference Translation:** `The householder is the pillar of support for the three other righteous paths.`
**Baseline Prediction:** `The Creator is the Originator of the physical universe. He is the Creator, the Creator of all things, the Creator of all things and the Creator of all things.`
**IKS-Augmented Prediction:** `[PA=DIPLOMACY]`
**Detected Concept(s):** `Illaram, Aram`
**Cultural context / notes:** Illaram (domestic life) is praised for sustaining the ascetics and students.

--- 

### Sentence #6 (ID: T144)
**Original Tamil:** `காதல் உடைய சான்றோர் பிறர்க்குத் துன்பம் செய்யார்.`
**Reference Translation:** `Noble men endowed with romantic love do no harm to others.`
**Baseline Prediction:** `He suffered at the hands of other humans, who were cruel and cruel.`
**IKS-Augmented Prediction:** `[SANROR=VICTORY] [KADHAL=LOVE]`
**Detected Concept(s):** `Kadal`
**Cultural context / notes:** Connects Kadal to the behavior of noble scholars (Sanror).

--- 

### Sentence #7 (ID: T011)
**Original Tamil:** `மலர்மிசை ஏகினான் மாணடி சேர்ந்தார் நிலமிசை நீடுவாழ் வார்.`
**Reference Translation:** `Those who cling to the glorious feet of Him who walked on flowers will live long on this earth.`
**Baseline Prediction:** `In time, however, he was able to study the Bible with Jehovah’s Witnesses, and he began to study the Bible with Jehovah’s Witnesses.`
**IKS-Augmented Prediction:** `As soon as he was on the other side of the border, he fell into a deep sleep.`
**Detected Concept(s):** `Iraivan`
**Cultural context / notes:** Praise of the divine force representing the lord who resides in the hearts of devotees.

--- 

### Sentence #8 (ID: T019)
**Original Tamil:** `அவாவில்லார்க்கு இல்லாகும் துன்பம் அஃதுண்டேல் தவாது மேன்மேல் வரும்.`
**Reference Translation:** `To those who are free from desire, there is no sorrow; but where desire exists, sorrow will follow ceaselessly.`
**Baseline Prediction:** `The suffering outside of the human family will come to an end.`
**IKS-Augmented Prediction:** `[VILL=DIPLOMACY] The suffering will come on the left.`
**Detected Concept(s):** `Turavaram`
**Cultural context / notes:** Renunciation of desire as the key to freedom from sorrow.

--- 

### Sentence #9 (ID: T005)
**Original Tamil:** `உற்றநோய் நோற்றல் உயிர்க்குறுகண் செய்யாமை அற்றே தவத்திற்கு உரு.`
**Reference Translation:** `To endure the pain that comes to oneself and to abstain from causing harm to other lives is the true nature of penance.`
**Baseline Prediction:** `It is a mistake not to focus on life - threatening infectious diseases.`
**IKS-Augmented Prediction:** `[UYIR=EXTERlOR] Don't give up on me.`
**Detected Concept(s):** `Thavam`
**Cultural context / notes:** Thavam is not just physical isolation but a state of non-injury (Ahimsa) coupled with self-endurance.

--- 

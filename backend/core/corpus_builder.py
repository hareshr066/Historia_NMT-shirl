import os
# Prevent duplicate OpenMP library initialization deadlock
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import csv
import logging
import hashlib
import unicodedata
import re
import subprocess
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from backend.core.corpus_sources import DATASETS_REGISTRY, export_raw_to_directory

# Setup logging
os.makedirs("results", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("results/dataset_build.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("CorpusBuilder")

# Concept definitions mapping for annotation
CONCEPT_MEANINGS = {
    "aram": "Virtue, righteousness, or moral ethics in classical Tamil thought",
    "anbu": "Love, affection, or emotional/familial bonding",
    "arul": "Grace, benevolence, or divine compassion",
    "oozh": "Fate, destiny, or cosmic cause-and-effect",
    "kelir": "Kinsmen, universal brotherhood, or social relations",
    "sanror": "Noble scholars, people of exemplary character, or wise elders",
    "thinai": "Poetic landscapes, ecological/climatic zones, or behavior genres",
    "karpu": "Chastity, faithfulness, or marital virtue",
    "ozhukkam": "Moral conduct, discipline, or personal integrity",
    "thavam": "Penance, ascetic practice, or self-discipline",
    "uyir": "Soul, life, or living being",
    "porul": "Wealth, material goods, or meaning/substance",
    "pukazh": "Fame, honor, or reputation",
    "arasan": "King, ruler, or sovereign leader",
    "velvi": "Ritual sacrifice or sacred offerings",
    "kodai": "Generosity, charity, or patronage",
    "viram": "Valor, bravery, or heroism",
    "udal": "Marital tiff, feigned anger, or lovers' quarrel",
    "mullai": "Pastoral/forest landscape (associated with waiting)",
    "kurinji": "Mountainous landscape (associated with union)",
    "neythal": "Coastal/seashore landscape (associated with separation/grief)",
    "palai": "Arid/desert landscape (associated with journey/separation)",
    "marutham": "Agricultural/fertile landscape (associated with infidelity/quarrel)",
    "thozhi": "Female confidante, helper, or companion"
}

# Related concepts dictionary to enhance IKS annotation
RELATED_CONCEPTS_MAP = {
    "aram": ["IKS-ARUL", "IKS-OZHUKKAM", "IKS-PORUL"],
    "anbu": ["IKS-ARUL", "IKS-KARPU", "IKS-UDAL"],
    "arul": ["IKS-ARAM", "IKS-ANBU", "IKS-THAVAM"],
    "oozh": ["IKS-UYIR", "IKS-THAVAM"],
    "kelir": ["IKS-ANBU", "IKS-SANROR"],
    "sanror": ["IKS-ARAM", "IKS-OZHUKKAM", "IKS-KELIR"],
    "thinai": ["IKS-MULLAI", "IKS-KURINJI", "IKS-NEYTHAL", "IKS-PALAI", "IKS-MARUTHAM"],
    "karpu": ["IKS-ANBU", "IKS-OZHUKKAM"],
    "ozhukkam": ["IKS-ARAM", "IKS-SANROR"],
    "thavam": ["IKS-ARAM", "IKS-ARUL"],
    "uyir": ["IKS-OOZH", "IKS-THAVAM"],
    "porul": ["IKS-ARAM", "IKS-ARASAN"],
    "pukazh": ["IKS-VIRAM", "IKS-KODAI"],
    "arasan": ["IKS-PORUL", "IKS-VIRAM"],
    "velvi": ["IKS-ARASAN", "IKS-KODAI"],
    "kodai": ["IKS-ARAM", "IKS-PORUL"],
    "viram": ["IKS-ARASAN", "IKS-PUKAZH"],
    "udal": ["IKS-ANBU", "IKS-MARUTHAM"]
}

def get_concept_details(concept_name, era_context="Classical"):
    """Resolves a concept name to its standard meaning, ID, era, and related concepts."""
    name_clean = concept_name.strip().lower()
    meaning = CONCEPT_MEANINGS.get(name_clean, f"Classical Tamil IKS concept of {concept_name}")
    concept_id = f"IKS-{concept_name.upper().replace(' ', '_')}"
    related = RELATED_CONCEPTS_MAP.get(name_clean, [])
    return concept_id, concept_name, meaning, era_context, related

class CorpusBuilder:
    def __init__(self, config_path="configs/config.yaml"):
        self.config_path = config_path
        self.load_config()
        self.init_directories()
        self.duplicates_removed_count = 0

    def load_config(self):
        import yaml
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        # Paths config
        self.raw_dir = "datasets/raw"
        self.processed_dir = "datasets/processed"
        self.clean_dir = "datasets/clean"
        self.augmented_dir = "datasets/augmented"
        self.metadata_dir = "datasets/metadata"
        self.train_path = "datasets/train/train.jsonl"
        self.val_path = "datasets/validation/validation.jsonl"
        self.test_path = "datasets/test/test.jsonl"
        self.exports_dir = "datasets/exports"

    def init_directories(self):
        """Creates the v2 dataset directory structure."""
        dirs = [
            self.raw_dir,
            self.processed_dir,
            self.clean_dir,
            self.augmented_dir,
            self.metadata_dir,
            os.path.dirname(self.train_path),
            os.path.dirname(self.val_path),
            os.path.dirname(self.test_path),
            self.exports_dir,
            "results"
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def collect_raw_data(self):
        """Collects raw data from python registry and compiles old JSON data if available."""
        logger.info("Collecting raw datasets...")
        
        # 1. Export the core registry files (now 14 works)
        export_raw_to_directory(self.raw_dir)

        # 2. Check for legacy compilation files to merge
        old_json_path = "datasets/classical_tamil_parallel.json"
        if os.path.exists(old_json_path):
            logger.info(f"Found legacy compilation dataset at {old_json_path}. Merging into raw/ files...")
            try:
                with open(old_json_path, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                
                # Group legacy records by work/book
                grouped_records = {}
                for record in legacy_data:
                    work = record.get("source_book", "Thirukkural").strip()
                    grouped_records.setdefault(work, []).append(record)
                
                # Merge grouped records into raw/ files
                for work_name, records in grouped_records.items():
                    file_name = f"{work_name.lower().replace(' ', '_')}.json"
                    path = os.path.join(self.raw_dir, file_name)
                    
                    # Read existing raw file if it exists
                    existing_records = []
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            existing_records = json.load(f)
                    
                    # Keep track of existing Tamil texts to prevent duplicates
                    existing_texts = {r.get("tamil_text", r.get("tamil", "")).strip() for r in existing_records}
                    
                    merged_count = 0
                    for r in records:
                        tamil = r.get("tamil", r.get("tamil_text", "")).strip()
                        if not tamil:
                            continue
                        if tamil not in existing_texts:
                            # Map record to raw schema
                            mapped = {
                                "id": r.get("id", f"LEG-{hashlib.md5(tamil.encode()).hexdigest()[:6].upper()}"),
                                "tamil_text": tamil,
                                "english_translation": r.get("english", r.get("english_translation", "")),
                                "author": r.get("author", self._infer_author(work_name)),
                                "work_name": work_name,
                                "chapter": r.get("chapter", ""),
                                "verse_number": str(r.get("verse", r.get("verse_number", ""))),
                                "era": r.get("era", self._infer_era(work_name)),
                                "literary_category": r.get("literary_category", self._infer_category(work_name)),
                                "source_url": r.get("source_url", "https://www.tamilvirtualuniversity.org/"),
                                "license": r.get("license", "Public Domain"),
                                "translator": r.get("translator", "Unknown"),
                                "translator_notes": r.get("notes", r.get("translator_notes", "")),
                                "commentary": r.get("commentary", ""),
                                "iks_concepts": r.get("iks_concepts", []),
                                "glossary": r.get("glossary", {}),
                                "metadata": r.get("metadata", {})
                            }
                            existing_records.append(mapped)
                            existing_texts.add(tamil)
                            merged_count += 1
                    
                    if merged_count > 0:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(existing_records, f, indent=2, ensure_ascii=False)
                        logger.info(f"Merged {merged_count} legacy records into {path}")
            except Exception as e:
                logger.error(f"Failed to merge legacy dataset: {e}", exc_info=True)

    def _infer_author(self, work):
        work_lower = work.lower()
        if "thirukkural" in work_lower: return "Tiruvalluvar"
        if "tolkappiyam" in work_lower: return "Tolkappiyar"
        if "silappathikaram" in work_lower: return "Ilankovatikal"
        if "manimekalai" in work_lower: return "Cittalai Cattanar"
        if "purananuru" in work_lower: return "Various Sangam Poets"
        if "kurunthogai" in work_lower: return "Various Sangam Poets"
        if "natrinai" in work_lower: return "Various Sangam Poets"
        if "akananuru" in work_lower: return "Various Sangam Poets"
        if "pathitrupathu" in work_lower: return "Various Sangam Poets"
        if "paripadal" in work_lower: return "Various Sangam Poets"
        if "kalithogai" in work_lower: return "Kapilar / Various"
        if "ainkurunuru" in work_lower: return "Various Sangam Poets"
        if "pattinappaalai" in work_lower: return "Kadiyalur Uruthirankannanar"
        if "maduraikanchi" in work_lower: return "Mangudi Maruthanar"
        return "Unknown"

    def _infer_era(self, work):
        work_lower = work.lower()
        if "tolkappiyam" in work_lower: return "Pre-Sangam (c. 300 BCE)"
        if "thirukkural" in work_lower: return "Post-Sangam (c. 1st–5th century CE)"
        if "silappathikaram" in work_lower: return "Post-Sangam (c. 5th century CE)"
        if "manimekalai" in work_lower: return "Post-Sangam (c. 5th–6th century CE)"
        return "Sangam (c. 300 BCE – 300 CE)"

    def _infer_category(self, work):
        work_lower = work.lower()
        if "thirukkural" in work_lower: return "Didactic"
        if "tolkappiyam" in work_lower: return "Grammatical/Linguistic"
        if "silappathikaram" in work_lower or "manimekalai" in work_lower: return "Epic/Narrative"
        if "purananuru" in work_lower or "pathitrupathu" in work_lower or "maduraikanchi" in work_lower: return "Heroic/Puram"
        if "paripadal" in work_lower: return "Devotional/Musical"
        return "Love/Akam"

    def preprocess_record(self, item):
        """Cleans, normalizes, validates, and rates the record quality."""
        # Get raw fields
        tamil_raw = item.get("tamil_text", item.get("tamil", ""))
        english_raw = item.get("english_translation", item.get("english", ""))
        
        # 1. Unicode NFC Normalization
        tamil_norm = unicodedata.normalize("NFC", str(tamil_raw))
        english_norm = unicodedata.normalize("NFC", str(english_raw))
        
        # Whitespace cleanup
        tamil_clean = " ".join(tamil_norm.split()).strip()
        english_clean = " ".join(english_norm.split()).strip()
        
        validation_errors = []
        
        # 2. Script & Language validation
        has_tamil = bool(re.search(r"[\u0b80-\u0bff]", tamil_clean))
        has_english = bool(re.search(r"[a-zA-Z]", english_clean))
        
        if not has_tamil:
            validation_errors.append("Missing Tamil script")
        if not has_english:
            validation_errors.append("Missing English script")
            
        # 3. Missing translation / empty field detection
        if not tamil_clean:
            validation_errors.append("Empty Tamil text")
        if not english_clean:
            validation_errors.append("Empty English translation")
            
        # 4. Length validation
        if len(tamil_clean) < 3:
            validation_errors.append("Tamil text too short")
        elif len(tamil_clean) > 1000:
            validation_errors.append("Tamil text too long")
            
        if len(english_clean) < 3:
            validation_errors.append("English translation too short")
        elif len(english_clean) > 1000:
            validation_errors.append("English translation too long")
            
        is_valid = len(validation_errors) == 0
        
        # 5. Metadata Completeness Evaluation
        optional_fields = [
            "author", "translator", "era", "chapter", 
            "verse_number", "commentary", "glossary", "source_reference"
        ]
        populated_metadata_count = 0
        for fld in optional_fields:
            val = item.get(fld, "")
            if val and str(val).strip() and val != "Unknown":
                populated_metadata_count += 1
        
        # 6. Quality Score Calculation (range 0.0 - 1.0)
        score = 0.0
        if is_valid:
            score += 0.3  # Basic validations pass
            
            # Ideal character length check (30 - 400 chars)
            if 30 <= len(tamil_clean) <= 400:
                score += 0.15
            if 30 <= len(english_clean) <= 400:
                score += 0.15
                
            # Density checks
            tamil_density = len(re.findall(r"[\u0b80-\u0bff\s.,!?;'\"-]", tamil_clean)) / len(tamil_clean) if tamil_clean else 0
            english_density = len(re.findall(r"[a-zA-Z\s.,!?;'\"-]", english_clean)) / len(english_clean) if english_clean else 0
            if tamil_density > 0.8:
                score += 0.1
            if english_density > 0.8:
                score += 0.1
                
            # Metadata completeness contribution (up to 0.2)
            score += (populated_metadata_count / len(optional_fields)) * 0.2
        else:
            score = 0.1  # Low score for invalid/corrupt records
            
        score = round(min(max(score, 0.0), 1.0), 2)
        
        # Extract alternate translations
        alt_trans = item.get("alternate_translations", [])
        if isinstance(alt_trans, str):
            alt_trans = [alt_trans] if alt_trans.strip() else []
            
        # Map record fields standardly to v2 schema
        processed = {
            "id": item.get("id", f"VER-{hashlib.md5(tamil_clean.encode()).hexdigest()[:6].upper()}"),
            "work_name": item.get("work_name", "Unknown"),
            "author": item.get("author", "Unknown"),
            "translator": item.get("translator", "Unknown"),
            "era": item.get("era", "Unknown"),
            "literary_type": item.get("literary_type", item.get("literary_category", "Unknown")),
            "chapter": item.get("chapter", ""),
            "verse_number": str(item.get("verse_number", item.get("verse", ""))),
            "tamil_text": tamil_clean,
            "english_translation": english_clean,
            "alternate_translations": alt_trans,
            "commentary": item.get("commentary", ""),
            "glossary": item.get("glossary", {}),
            "iks_concepts": item.get("iks_concepts", []),
            "concept_ids": [], # Filled during annotation
            "semantic_tags": [], # Filled during annotation
            "source_reference": item.get("source_reference", item.get("source_url", "https://www.tamilvirtualuniversity.org/")),
            "license": item.get("license", "Public Domain"),
            "quality_score": score,
            "is_valid": is_valid,
            "validation_errors": validation_errors
        }
        return processed

    def annotate_iks_concepts(self, record):
        """Scans the record, detects IKS concepts, and attaches annotations."""
        tamil_text = record["tamil_text"]
        english_text = record["english_translation"]
        commentary = record["commentary"]
        
        detected_concepts = []
        seen_concept_ids = set()
        
        # Match existing annotations if any
        raw_concepts = record.get("iks_concepts", [])
        for c in raw_concepts:
            if isinstance(c, dict):
                c_name = c.get("name", "")
            else:
                c_name = str(c)
                
            c_id, name, meaning, era, related = get_concept_details(c_name, record["era"])
            if c_id not in seen_concept_ids:
                detected_concepts.append({
                    "concept_id": c_id,
                    "name": name.capitalize(),
                    "meaning": meaning,
                    "historical_era": era,
                    "related_concepts": related,
                    "confidence": 1.0
                })
                seen_concept_ids.add(c_id)
                
        # Scrape and search keywords
        text_to_search = f"{tamil_text} {english_text} {commentary}".lower()
        for concept, meaning in CONCEPT_MEANINGS.items():
            concept_id = f"IKS-{concept.upper()}"
            if concept_id in seen_concept_ids:
                continue
                
            matches_tamil = concept in tamil_text.lower()
            matches_english = concept in english_text.lower()
            
            confidence = 0.0
            if matches_tamil:
                confidence = 0.9
            elif matches_english:
                confidence = 0.7
                
            if confidence > 0.0:
                c_id, name, meaning, era, related = get_concept_details(concept, record["era"])
                detected_concepts.append({
                    "concept_id": c_id,
                    "name": name.capitalize(),
                    "meaning": meaning,
                    "historical_era": era,
                    "related_concepts": related,
                    "confidence": confidence
                })
                seen_concept_ids.add(c_id)
                
        record["iks_concepts"] = detected_concepts
        record["concept_ids"] = list(seen_concept_ids)
        record["semantic_tags"] = [c["name"].lower() for c in detected_concepts]
        return record

    def build_corpus(self):
        """Runs the entire end-to-end ChronoIKS Corpus v2 pipeline."""
        logger.info("=== ChronoIKS Corpus v2 Dataset Generation Pipeline ===")
        
        # 1. Collect raw datasets
        self.collect_raw_data()
        
        # Read raw JSON files
        raw_files = [f for f in os.listdir(self.raw_dir) if f.endswith(".json")]
        if not raw_files:
            logger.error("No raw dataset files found in datasets/raw/.")
            return False
            
        all_records = []
        for rf in raw_files:
            path = os.path.join(self.raw_dir, rf)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_records.extend(data)
                logger.info(f"Loaded {len(data)} records from raw file: {path}")
            except Exception as e:
                logger.error(f"Failed to read raw file {path}: {e}")
                
        # 2. Preprocess, validate, and deduplicate
        processed_records = []
        seen_texts = set()
        self.duplicates_removed_count = 0
        invalid_records = []
        
        for item in all_records:
            proc = self.preprocess_record(item)
            if not proc["is_valid"]:
                invalid_records.append(proc)
                continue
                
            # Deduplicate by Tamil text
            text_key = proc["tamil_text"]
            if text_key in seen_texts:
                self.duplicates_removed_count += 1
                continue
            seen_texts.add(text_key)
            processed_records.append(proc)
            
        logger.info(f"Loaded: {len(all_records)} | Unique Valid: {len(processed_records)} | Duplicates Removed: {self.duplicates_removed_count} | Invalid: {len(invalid_records)}")
        
        # Save invalid/corrupt records log (for research tracing)
        if invalid_records:
            invalid_log_path = os.path.join(self.processed_dir, "invalid_records.json")
            with open(invalid_log_path, "w", encoding="utf-8") as f:
                json.dump(invalid_records, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(invalid_records)} invalid records to {invalid_log_path} for review.")
            
        # 3. Annotate IKS Concepts
        annotated_records = []
        for r in processed_records:
            annotated_records.append(self.annotate_iks_concepts(r))
            
        # Write to processed/ directory
        processed_path = os.path.join(self.processed_dir, "processed_corpus.json")
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump(annotated_records, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved processed corpus to {processed_path}")
        
        # Save clean dataset (without metadata fields or system verification structures) to clean/
        clean_path = os.path.join(self.clean_dir, "clean_corpus.json")
        clean_records = []
        for r in annotated_records:
            clean_rec = dict(r)
            clean_rec.pop("is_valid", None)
            clean_rec.pop("validation_errors", None)
            clean_records.append(clean_rec)
            
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_records, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved clean corpus to {clean_path}")
        
        # 4. Augment with IKS tag prefixes
        logger.info("Initializing IKS concept-aware tagging augmentation...")
        augmented_records = []
        
        # Import augmenter lazily
        try:
            import sys
            scripts_dir = os.path.abspath("scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            from scripts.augment import IKSInputAugmenter
            augmenter = IKSInputAugmenter(self.config_path)
        except Exception as e:
            logger.warning(f"Could not initialize scripts.augment.IKSInputAugmenter: {e}. Using rule-based fallback augmenter.")
            augmenter = None
            
        for r in clean_records:
            tamil_text = r["tamil_text"]
            if augmenter:
                try:
                    res = augmenter.augment_sentence(tamil_text)
                    augmented_tamil = res["augmented"]
                    aug_details = res["details"]
                except Exception:
                    augmented_tamil = tamil_text
                    aug_details = []
            else:
                # Rule-based fallback prefix builder
                tags = []
                for c in r["iks_concepts"]:
                    c_name = c["name"].upper()
                    meaning_word = c["meaning"].split(",")[0].split(";")[0].split("/")[0].strip().upper()
                    tags.append(f"[{c_name}={meaning_word}]")
                prefix = "".join(tags)
                augmented_tamil = f"{prefix} {tamil_text}" if prefix else tamil_text
                aug_details = r["iks_concepts"]
                
            aug_record = dict(r)
            aug_record["augmented_tamil"] = augmented_tamil
            aug_record["augmentation_details"] = aug_details
            
            # Backwards compatibility fields
            aug_record["tamil"] = r["tamil_text"]
            aug_record["english"] = r["english_translation"]
            aug_record["source_book"] = r["work_name"]
            aug_record["verse"] = r["verse_number"]
            aug_record["notes"] = r["translator_notes"] if "translator_notes" in r else ""
            
            augmented_records.append(aug_record)
            
        # Write augmented corpus
        augmented_path = os.path.join(self.augmented_dir, "augmented_corpus.json")
        with open(augmented_path, "w", encoding="utf-8") as f:
            json.dump(augmented_records, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved augmented corpus to {augmented_path}")
        
        # 5. Split train/validation/test (80 / 10 / 10)
        df = pd.DataFrame(augmented_records)
        split_ratios = self.config.get("data", {}).get("split_ratios", {"train": 0.8, "val": 0.1, "test": 0.1})
        
        test_ratio = split_ratios["test"]
        val_ratio = split_ratios["val"]
        val_adjusted_ratio = val_ratio / (1.0 - test_ratio)
        
        train_val_df, test_df = train_test_split(df, test_size=test_ratio, random_state=42)
        train_df, val_df = train_test_split(train_val_df, test_size=val_adjusted_ratio, random_state=42)
        
        logger.info(f"Splits generated: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")
        
        # Save JSONL splits
        self.save_jsonl(train_df, self.train_path)
        self.save_jsonl(val_df, self.val_path)
        self.save_jsonl(test_df, self.test_path)
        
        # 6. Versioning & Hashes
        self.generate_dataset_version(augmented_records)
        
        # 7. Quality Reports & Statistics
        self.generate_reports(augmented_records, train_df, val_df, test_df)
        
        logger.info("ChronoIKS Corpus v2 build completed successfully.")
        return True

    def save_jsonl(self, df, path):
        records = df.to_dict(orient="records")
        # Ensure target folder exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                # Convert list/dict columns to strings to ensure JSON serialization
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(df)} records to {path}")

    def generate_dataset_version(self, records):
        """Generates v2 version details and SHA-256 hash."""
        # Calculate SHA-256 hash of the complete dataset structure
        hasher = hashlib.sha256()
        hasher.update(json.dumps(records, sort_keys=True).encode("utf-8"))
        ds_hash = hasher.hexdigest()
        
        # Collect distinct counts
        unique_concepts = set()
        unique_authors = set()
        unique_works = set()
        
        for r in records:
            unique_authors.add(r["author"])
            unique_works.add(r["work_name"])
            for c in r["iks_concepts"]:
                unique_concepts.add(c["concept_id"])
                
        # Vocabulary Size
        vocab = set()
        for r in records:
            for w in re.findall(r"[\u0b80-\u0bff]+", r["tamil_text"]):
                vocab.add(w.lower())
            for w in re.findall(r"[a-zA-Z]+", r["english_translation"]):
                vocab.add(w.lower())
        vocab_size = len(vocab)
        
        # Average Sentence Length (word count)
        total_words = 0
        for r in records:
            tamil_words = len(re.findall(r"[\u0b80-\u0bff]+", r["tamil_text"]))
            english_words = len(re.findall(r"[a-zA-Z]+", r["english_translation"]))
            total_words += (tamil_words + english_words)
        avg_sent_len = round(total_words / (2 * len(records)), 2) if records else 0
        
        # Get Git Hash
        try:
            git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        except Exception:
            git_hash = "unknown"
            
        version_data = {
            "Dataset Version": "v2.0.0",
            "Creation Date": datetime.utcnow().isoformat() + "Z",
            "Git Hash": git_hash,
            "Sample Count": len(records),
            "Unique Concepts": len(unique_concepts),
            "Unique Authors": len(unique_authors),
            "Unique Literary Works": len(unique_works),
            "Vocabulary Size": vocab_size,
            "Average Sentence Length": avg_sent_len,
            "Dataset Hash": ds_hash
        }
        
        # Save to metadata folder and project root
        paths = [
            os.path.join(self.metadata_dir, "dataset_version.json"),
            "dataset_version.json"
        ]
        for p in paths:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(version_data, f, indent=2)
                
        logger.info(f"Generated dataset version v2.0.0 with hash {ds_hash[:10]}")

    def generate_reports(self, records, train_df, val_df, test_df):
        """Generates v2 statistics, quality csv, and reports."""
        logger.info("Generating dataset reports...")
        
        # 1. Quality CSV
        quality_csv_path = "results/dataset_quality.csv"
        with open(quality_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["verse_id", "work_name", "tamil_length", "english_length", "quality_score", "detected_concepts", "validation_errors"])
            for r in records:
                concept_names = "|".join([c["name"] for c in r["iks_concepts"]])
                val_errs = "|".join(r.get("validation_errors", []))
                writer.writerow([
                    r["id"],
                    r["work_name"],
                    len(r["tamil_text"]),
                    len(r["english_translation"]),
                    r["quality_score"],
                    concept_names,
                    val_errs
                ])
                
        # 2. Statistics JSON
        total_samples = len(records)
        avg_tamil_len = sum(len(r["tamil_text"]) for r in records) / total_samples if total_samples > 0 else 0
        avg_eng_len = sum(len(r["english_translation"]) for r in records) / total_samples if total_samples > 0 else 0
        
        work_counts = {}
        concept_counts = {}
        author_counts = {}
        quality_bins = {"0.0-0.4": 0, "0.4-0.7": 0, "0.7-1.0": 0}
        
        vocab = set()
        for r in records:
            # works
            work_counts[r["work_name"]] = work_counts.get(r["work_name"], 0) + 1
            # authors
            author_counts[r["author"]] = author_counts.get(r["author"], 0) + 1
            # concepts
            for c in r["iks_concepts"]:
                concept_counts[c["name"]] = concept_counts.get(c["name"], 0) + 1
            # quality distribution
            qs = r["quality_score"]
            if qs < 0.4:
                quality_bins["0.0-0.4"] += 1
            elif qs < 0.7:
                quality_bins["0.4-0.7"] += 1
            else:
                quality_bins["0.7-1.0"] += 1
            # vocab
            for w in re.findall(r"[\u0b80-\u0bff]+", r["tamil_text"]):
                vocab.add(w.lower())
            for w in re.findall(r"[a-zA-Z]+", r["english_translation"]):
                vocab.add(w.lower())
                
        stats = {
            "total_samples": total_samples,
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "average_tamil_length": round(avg_tamil_len, 2),
            "average_english_length": round(avg_eng_len, 2),
            "unique_concepts_count": len(concept_counts),
            "unique_authors_count": len(author_counts),
            "duplicates_removed": self.duplicates_removed_count,
            "concept_annotation_coverage_pct": round(len([r for r in records if r["iks_concepts"]]) / total_samples * 100, 2) if total_samples > 0 else 0,
            "quality_distribution": quality_bins,
            "vocabulary_statistics": {
                "total_vocabulary_words": len(vocab),
            },
            "work_distribution": work_counts,
            "concept_distribution": concept_counts,
            "build_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        with open("results/dataset_statistics.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
            
        # 3. Markdown Report
        report_path = "results/dataset_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# ChronoIKS Corpus v2 Research Grade Dataset Report\n\n")
            f.write(f"**Build Timestamp:** {stats['build_timestamp']}\n")
            f.write(f"**Dataset Version:** v2.0.0\n\n")
            
            f.write("## 1. Summary Statistics\n")
            f.write(f"- **Total Samples:** {total_samples}\n")
            f.write(f"- **Duplicates Removed:** {stats['duplicates_removed']}\n")
            f.write(f"- **Total Distinct Authors:** {stats['unique_authors_count']}\n")
            f.write(f"- **Total Unique IKS Concepts:** {stats['unique_concepts_count']}\n")
            f.write(f"- **IKS Concept Annotation Coverage:** {stats['concept_annotation_coverage_pct']}%\n")
            f.write(f"- **Total Vocabulary Size:** {stats['vocabulary_statistics']['total_vocabulary_words']} words\n")
            f.write(f"- **Average Tamil Verse Length:** {stats['average_tamil_length']} chars\n")
            f.write(f"- **Average English Verse Length:** {stats['average_english_length']} chars\n\n")
            
            f.write("## 2. Dataset Split Distributions\n")
            f.write("| Split | Samples | Percentage |\n")
            f.write("|---|---|---|\n")
            f.write(f"| Train | {stats['train_samples']} | {round(stats['train_samples']/total_samples*100, 1)}% |\n")
            f.write(f"| Validation | {stats['val_samples']} | {round(stats['val_samples']/total_samples*100, 1)}% |\n")
            f.write(f"| Test | {stats['test_samples']} | {round(stats['test_samples']/total_samples*100, 1)}% |\n")
            f.write(f"| **Total** | **{total_samples}** | **100%** |\n\n")
            
            f.write("## 3. Literary Source Distributions\n")
            f.write("| Work Name | Verses Count | Percentage |\n")
            f.write("|---|---|---|\n")
            for w, c in sorted(work_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {w} | {c} | {round(c/total_samples*100, 1)}% |\n")
            f.write("\n")
            
            f.write("## 4. Quality Distribution\n")
            f.write("| Quality Range | Count | Percentage |\n")
            f.write("|---|---|---|\n")
            for q_bin, q_count in quality_bins.items():
                f.write(f"| {q_bin} | {q_count} | {round(q_count/total_samples*100, 1)}% |\n")
            f.write("\n")
            
            f.write("## 5. Top Annotated Concepts\n")
            f.write("| Concept | Occurrences |\n")
            f.write("|---|---|\n")
            for cp, oc in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
                f.write(f"| {cp} | {oc} |\n")
            f.write("\n")
            
        logger.info(f"Generated quality report: {report_path}")

    def validate_corpus(self):
        """Performs validation checks on splits and schemas."""
        logger.info("Executing ChronoIKS Corpus validation checks...")
        
        splits = {"train": self.train_path, "val": self.val_path, "test": self.test_path}
        records = {}
        
        for name, path in splits.items():
            if not os.path.exists(path):
                logger.error(f"Validation failed: split file {path} does not exist. Run 'build' first.")
                return False
                
            records[name] = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records[name].append(json.loads(line))
            logger.info(f"Loaded {len(records[name])} records from {name} split.")
            
        # 1. No overlap check (zero duplicates across splits)
        train_texts = {r["tamil_text"] for r in records["train"]}
        val_texts = {r["tamil_text"] for r in records["val"]}
        test_texts = {r["tamil_text"] for r in records["test"]}
        
        train_val_overlap = train_texts.intersection(val_texts)
        train_test_overlap = train_texts.intersection(test_texts)
        val_test_overlap = val_texts.intersection(test_texts)
        
        overlap_error = False
        if train_val_overlap:
            logger.error(f"Overlap found between Train and Validation: {len(train_val_overlap)} items.")
            overlap_error = True
        if train_test_overlap:
            logger.error(f"Overlap found between Train and Test: {len(train_test_overlap)} items.")
            overlap_error = True
        if val_test_overlap:
            logger.error(f"Overlap found between Validation and Test: {len(val_test_overlap)} items.")
            overlap_error = True
            
        if not overlap_error:
            logger.info("Validation PASSED: Zero duplicate verses across splits.")
            
        # 2. Schema compliance check
        required_fields = [
            "id", "work_name", "author", "translator", "era", "literary_type", 
            "chapter", "verse_number", "tamil_text", "english_translation", 
            "alternate_translations", "commentary", "glossary", "iks_concepts", 
            "concept_ids", "semantic_tags", "source_reference", "license", "quality_score"
        ]
        schema_error = False
        
        for name, split_recs in records.items():
            for r in split_recs:
                for fld in required_fields:
                    if fld not in r:
                        logger.error(f"Schema error in {name} split, item {r.get('id')}: missing field '{fld}'")
                        schema_error = True
                
                # Check concept structure
                if not isinstance(r.get("iks_concepts"), list):
                    logger.error(f"Schema error in {name} split, item {r.get('id')}: 'iks_concepts' is not a list")
                    schema_error = True
                else:
                    for c in r["iks_concepts"]:
                        if not all(k in c for k in ["concept_id", "name", "meaning", "historical_era", "related_concepts", "confidence"]):
                            logger.error(f"Schema error in {name} split, item {r.get('id')}: malformed concept object {c}")
                            schema_error = True
                            
        if not schema_error:
            logger.info("Validation PASSED: Schema is compliant with research corpus standards.")
            
        return (not overlap_error) and (not schema_error)

    def get_stats(self):
        """Calculates and returns corpus stats for CLI print."""
        stats_path = "results/dataset_statistics.json"
        if os.path.exists(stats_path):
            with open(stats_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def export_corpus(self, format_type):
        """Exports dataset to exports/ directory in target formats (CSV, JSONL, Parquet, HF)."""
        logger.info(f"Exporting dataset to format: {format_type}...")
        processed_path = os.path.join(self.processed_dir, "processed_corpus.json")
        if not os.path.exists(processed_path):
            logger.error("Processed corpus does not exist. Please run 'build' first.")
            return False
            
        with open(processed_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            
        df = pd.DataFrame(records)
        os.makedirs(self.exports_dir, exist_ok=True)
        
        if format_type.lower() == "csv":
            csv_out = os.path.join(self.exports_dir, "chronoiks_corpus.csv")
            df.to_csv(csv_out, index=False, encoding="utf-8")
            logger.info(f"Successfully exported CSV corpus to {csv_out}")
            
        elif format_type.lower() == "jsonl":
            jsonl_out = os.path.join(self.exports_dir, "chronoiks_corpus.jsonl")
            with open(jsonl_out, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            logger.info(f"Successfully exported JSONL corpus to {jsonl_out}")
            
        elif format_type.lower() == "parquet":
            try:
                df_pq = df.copy()
                # Serialize list/dict columns to strings for parquet support
                df_pq["iks_concepts"] = df_pq["iks_concepts"].apply(json.dumps)
                df_pq["concept_ids"] = df_pq["concept_ids"].apply(json.dumps)
                df_pq["semantic_tags"] = df_pq["semantic_tags"].apply(json.dumps)
                df_pq["alternate_translations"] = df_pq["alternate_translations"].apply(json.dumps)
                df_pq["glossary"] = df_pq["glossary"].apply(json.dumps)
                if "validation_errors" in df_pq.columns:
                    df_pq = df_pq.drop(columns=["validation_errors"])

                
                pq_out = os.path.join(self.exports_dir, "chronoiks_corpus.parquet")
                df_pq.to_parquet(pq_out, index=False)
                logger.info(f"Successfully exported Parquet corpus to {pq_out}")
            except Exception as e:
                logger.error(f"Failed to export Parquet: {e}")
                return False
                
        elif format_type.lower() == "hf":
            try:
                import sys
                saved_path = list(sys.path)
                cwd = os.path.abspath(os.getcwd())
                sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd(), cwd)]
                
                from datasets import Dataset
                sys.path = saved_path
                
                hf_dir = os.path.join(self.exports_dir, "chronoiks_hf_dataset")
                dataset = Dataset.from_pandas(df)
                dataset.save_to_disk(hf_dir)
                logger.info(f"Successfully saved Hugging Face Dataset to directory {hf_dir}")
            except Exception as e:
                if 'saved_path' in locals():
                    sys.path = saved_path
                logger.error(f"Failed to save HF Dataset: {e}")
                return False
        else:
            logger.error(f"Unknown format type: {format_type}. Supported: csv, jsonl, parquet, hf.")
            return False
            
        return True

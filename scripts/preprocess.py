import os
import json
import yaml
import unicodedata
import pandas as pd
from sklearn.model_selection import train_test_split
from augment import IKSInputAugmenter

class IKSPreprocessor:
    def __init__(self, config_path="configs/config.yaml"):
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.raw_json_path = self.config["data"]["json_path"]
        self.train_path = self.config["data"]["train_path"]
        self.val_path = self.config["data"]["val_path"]
        self.test_path = self.config["data"]["test_path"]
        
        self.unicode_norm = self.config["preprocessing"]["unicode_norm"]
        self.remove_duplicates = self.config["preprocessing"]["remove_duplicates"]
        self.split_ratios = self.config["data"]["split_ratios"]
        
        # Initialize augmenter
        self.augmenter = IKSInputAugmenter(config_path)

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        # Unicode normalization (NFC)
        normalized = unicodedata.normalize(self.unicode_norm, text)
        # Normalize whitespace (split and join)
        cleaned = " ".join(normalized.split()).strip()
        return cleaned

    def process_and_split(self):
        print(f"Loading raw dataset from {self.raw_json_path}...")
        if not os.path.exists(self.raw_json_path):
            raise FileNotFoundError(f"Raw dataset file not found at {self.raw_json_path}. Run datasets/compile_dataset.py first.")
            
        with open(self.raw_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        processed_data = []
        seen_pairs = set()
        
        print("Cleaning text and augmenting sentences with IKS tags...")
        for idx, item in enumerate(data):
            if idx % 10 == 0:
                print(f" -> Processing sentence {idx+1}/{len(data)}...", flush=True)
            tamil_cleaned = self.clean_text(item["tamil"])
            english_cleaned = self.clean_text(item["english"])
            
            # De-duplication check
            pair_key = (tamil_cleaned, english_cleaned)
            if self.remove_duplicates and pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            
            # Apply input augmentation
            aug_result = self.augmenter.augment_sentence(tamil_cleaned)
            augmented_tamil = aug_result["augmented"]
            
            processed_data.append({
                "id": item["id"],
                "source_book": item["source_book"],
                "chapter": item["chapter"],
                "verse": item["verse"],
                "era": item["era"],
                "tamil": tamil_cleaned,
                "augmented_tamil": augmented_tamil,
                "english": english_cleaned,
                "iks_concepts": item["iks_concepts"],
                "augmentation_details": aug_result["details"],
                "notes": item["notes"]
            })
            
        print("Completed tag augmentation for all sentences.", flush=True)
        # Convert to DataFrame for splitting
        df = pd.DataFrame(processed_data)
        
        # Calculate split sizes
        test_ratio = self.split_ratios["test"]
        val_ratio = self.split_ratios["val"]
        # Adjusted validation ratio for the second split
        val_adjusted_ratio = val_ratio / (1.0 - test_ratio)
        
        # Perform split: Train (80%), Val (10%), Test (10%)
        # Stratification is not strictly possible on small datasets with random selections,
        # but we split randomly with a seed for reproducibility.
        train_val_df, test_df = train_test_split(df, test_size=test_ratio, random_state=42)
        train_df, val_df = train_test_split(train_val_df, test_size=val_adjusted_ratio, random_state=42)
        
        print(f"Dataset split results:")
        print(f" - Train:      {len(train_df)} rows")
        print(f" - Validation: {len(val_df)} rows")
        print(f" - Test:       {len(test_df)} rows")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.train_path), exist_ok=True)
        
        # Save to JSONL
        self.save_jsonl(train_df, self.train_path)
        self.save_jsonl(val_df, self.val_path)
        self.save_jsonl(test_df, self.test_path)
        print("Dataset preprocessing and splits saved successfully.")

    def save_jsonl(self, df, path):
        records = df.to_dict(orient="records")
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Saved {len(df)} records to {path}")

if __name__ == "__main__":
    preprocessor = IKSPreprocessor()
    preprocessor.process_and_split()

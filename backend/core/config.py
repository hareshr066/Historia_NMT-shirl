import os
import yaml

# Safe loading of dotenv variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "configs", "config.yaml")

# Load YAML configs
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
else:
    settings = {}

# PostgreSQL credentials defaulting to env variables or standard local defaults
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/chronoiks_ai"
)

# JWT Secret Key config
SECRET_KEY = os.getenv("SECRET_KEY", "chronoiks_super_secret_key")

# Extract config paths
KB_JSON_PATH = os.path.join(BASE_DIR, settings.get("kb", {}).get("json_path", "knowledge_base/iks_kb.json"))
KB_INDEX_PATH = os.path.join(BASE_DIR, settings.get("kb", {}).get("faiss_index_path", "knowledge_base/iks_faiss.index"))

NLL_MODEL_PATH = os.path.join(BASE_DIR, settings.get("models", {}).get("nllb", "models/opus-mt-mul-en"))
SENTENCE_TRANSFORMER_MODEL = settings.get("models", {}).get("sentence_transformer", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

SOURCE_LANG = settings.get("models", {}).get("source_lang", "tam_Taml")
TARGET_LANG = settings.get("models", {}).get("target_lang", "eng_Latn")

# Active Translation model configuration
TRANSLATION_MODEL_TYPE = settings.get("translation_model", {}).get("type", "indictrans2")
TRANSLATION_MODEL_NAME = settings.get("translation_model", {}).get("model_name", "ai4bharat/indictrans2-indic-en-dist-200M")
TRANSLATION_SOURCE_LANG = settings.get("translation_model", {}).get("language", {}).get("source", "tam_Taml")
TRANSLATION_TARGET_LANG = settings.get("translation_model", {}).get("language", {}).get("target", "eng_Latn")
TRANSLATION_BEAM_SIZE = settings.get("translation_model", {}).get("beam_size", 5)
TRANSLATION_MAX_LENGTH = settings.get("translation_model", {}).get("max_length", 256)

LORA_ADAPTER_PATH = os.path.join(
    BASE_DIR, 
    settings.get("training", {}).get("output_dir", "models/checkpoint"), 
    "best_lora_adapter"
)


from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Concept(Base):
    __tablename__ = "concepts"
    
    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String(255), nullable=False, index=True)
    tamil = Column(String(255), nullable=False, index=True)
    romanization = Column(String(255), nullable=True)
    language = Column(String(100), default="Tamil")
    english_meaning = Column(Text, nullable=False)
    era = Column(String(100), nullable=True)
    definition = Column(Text, nullable=True)
    historical_meaning = Column(Text, nullable=True)
    modern_meaning = Column(Text, nullable=True)
    commentary = Column(Text, nullable=True)
    source_reference = Column(String(255), nullable=True)
    confidence = Column(Float, default=1.0)
    verified_by = Column(String(255), default="Tamil Scholar / IKS Researcher")
    revision_history = Column(Text, default="[]")  # Stores JSON array log of updates
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    raw_baseline_translation = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    latency = Column(Float, nullable=True)  # in ms
    confidence = Column(Float, nullable=True)  # matching confidence percentage
    explanation_report = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    license = Column(String(100), default="Public Domain")
    language = Column(String(100), default="Tamil")
    url = Column(String(512), nullable=True)
    era = Column(String(100), nullable=True)
    author = Column(String(255), nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

class Verse(Base):
    __tablename__ = "verses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    verse_number = Column(String(100), nullable=True)
    chapter_name = Column(String(255), nullable=True)
    book_name = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    translation = Column(Text, nullable=True)

class Meaning(Base):
    __tablename__ = "meanings"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    era = Column(String(100), nullable=False)
    meaning = Column(Text, nullable=False)
    historical_notes = Column(Text, nullable=True)

class Reference(Base):
    __tablename__ = "references"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    verse_id = Column(Integer, ForeignKey("verses.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, nullable=True)

class Commentary(Base):
    __tablename__ = "commentaries"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=True)
    verse_id = Column(Integer, ForeignKey("verses.id", ondelete="CASCADE"), nullable=True)
    author = Column(String(255), nullable=False)
    commentary_text = Column(Text, nullable=False)
    era = Column(String(100), nullable=True)

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    version = Column(String(50), default="1.0")
    license = Column(String(100), default="Creative Commons")
    size_records = Column(Integer, default=0)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmbeddingRecord(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    text_content = Column(Text, nullable=False)
    vector_metadata = Column(Text, nullable=True)  # Stores JSON mapping or index coordinates
    source_table = Column(String(100), nullable=False)  # "concepts" or "verses"
    source_id = Column(Integer, nullable=False)

class TrainingRun(Base):
    __tablename__ = "training_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(255), nullable=False)
    epochs = Column(Integer, default=3)
    learning_rate = Column(Float, default=2e-5)
    loss = Column(Float, nullable=True)
    bleu = Column(Float, nullable=True)
    bert_score = Column(Float, nullable=True)
    duration_sec = Column(Float, nullable=True)
    model_version = Column(String(100), default="1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False)
    dataset_name = Column(String(255), nullable=False)
    hyperparameters = Column(Text, nullable=True)  # JSON dump of parameters
    bleu = Column(Float, nullable=True)
    bert_score = Column(Float, nullable=True)
    training_time_sec = Column(Float, nullable=True)
    metrics_log = Column(Text, nullable=True)  # JSON dump of final BLEU, ROUGE, BERTScore
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    path = Column(String(512), nullable=False)
    version = Column(String(50), default="1.0")
    is_active = Column(Integer, default=0)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())

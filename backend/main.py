import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import translate
from backend.core.database import Base, engine

# Initialize database schema tables on startup
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
    
    # Auto-seed database from JSON file if empty
    from backend.core.database import SessionLocal
    from backend.core.models import Concept
    from backend.core.config import KB_JSON_PATH
    import json
    import os
    
    db = SessionLocal()
    try:
        if db.query(Concept).count() == 0:
            print("Database concepts table is empty. Seeding from JSON Knowledge Base...")
            if os.path.exists(KB_JSON_PATH):
                with open(KB_JSON_PATH, "r", encoding="utf-8") as f:
                    concepts_data = json.load(f)
                for c in concepts_data:
                    tamil_text = c.get('tamil', '')
                    lang = "Tamil"
                    for char in tamil_text:
                        if 0x0900 <= ord(char) <= 0x097F:
                            lang = "Sanskrit"
                            break
                    
                    db_concept = Concept(
                        concept=c.get('concept', ''),
                        tamil=tamil_text,
                        romanization=c.get('romanization') or c.get('concept', ''),
                        language=c.get('language') or lang,
                        english_meaning=c.get('english') or c.get('english_meaning') or '',
                        era=c.get('era') or 'Classical',
                        definition=c.get('definition') or '',
                        historical_meaning=c.get('historical_meaning') or '',
                        modern_meaning=c.get('modern_meaning') or '',
                        commentary=c.get('commentary') or c.get('historical_meaning') or '',
                        source_reference=c.get('source_reference') or 'Tolkappiyam & Literature',
                        confidence=float(c.get('confidence', 1.0)),
                        verified_by=c.get('verified_by') or 'Tamil Scholar / IKS Researcher',
                        revision_history=c.get('revision_history') or '[]',
                        version=int(c.get('version', 1))
                    )
                    db.add(db_concept)
                db.commit()
                print(f"Successfully seeded {len(concepts_data)} concepts into SQL database.")
            else:
                print(f"Warning: JSON Knowledge Base path not found at {KB_JSON_PATH}")
        else:
            print("Database concepts table already contains entries. Skipping seeding.")
    except Exception as db_err:
        print(f"Database seeding failed: {db_err}")
    finally:
        db.close()

except Exception as e:
    print(f"Warning: Database initialization skipped/failed: {e}")

# Instantiate FastAPI
app = FastAPI(
    title="ChronoIKS AI Gateway",
    description="An Explainable Semantic Intelligence Platform for Indian Knowledge Systems",
    version="1.0.0"
)

# Wire CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL (e.g. http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire APIRouter endpoints
app.include_router(translate.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ChronoIKS AI Engine Gateway",
        "endpoints": {
            "translate": "/api/translate [POST]",
            "compare": "/api/compare [POST]",
            "search": "/api/search [GET]"
        }
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

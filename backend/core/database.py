import os
import operator
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, UnaryExpression
from sqlalchemy.orm.attributes import InstrumentedAttribute
from backend.core.config import DATABASE_URL, BASE_DIR

# Configure dnspython to use Google and Cloudflare DNS to bypass network/VPN DNS refusals
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']
    print("Database DNS: Overrode default resolver to Google/Cloudflare DNS.")
except Exception as dns_err:
    print(f"Database DNS Warning: Could not override default resolver: {dns_err}")

# MongoDB Configuration
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://wshirlypriscilla_db_user:ItXlljBkEeTBpym6@cluster0.hnr1fr0.mongodb.net/?appName=Cluster0"
)

db_mode = "sql"  # default
mongo_client = None
mongo_db = None

# Base class for DB models
Base = declarative_base()

# Test MongoDB connection on startup
try:
    print("Database: Connecting to MongoDB...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    mongo_db = mongo_client["chronoiks_ai"]
    db_mode = "mongodb"
    print("Database: Connected to MongoDB successfully. Using MongoDB as main database.")
except Exception as e:
    print(f"Database Warning: MongoDB connection failed ({e}).")
    print("IMPORTANT: If using MongoDB Atlas, please verify that your IP is whitelisted (e.g., set to 'Allow access from anywhere' / 0.0.0.0/0) in Atlas network settings.")
    print("Database: Falling back to SQL (PostgreSQL/SQLite)...")
    db_mode = "sql"

# Setup SQL Engine (for PostgreSQL or local SQLite fallback)
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
    print("Database: Connected to PostgreSQL successfully.")
except Exception as e:
    sqlite_path = os.path.join(BASE_DIR, "chronoiks_ai.db")
    print(f"Database Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite at {sqlite_path}.")
    sqlite_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False}
    )

# SQL Session Factory
SQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB Sequence Generator for auto-increment keys
def get_next_sequence_value(db, sequence_name):
    try:
        ret = db["counters"].find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=True
        )
        return ret["sequence_value"]
    except Exception:
        # Fallback to count + 1
        return db[sequence_name].count_documents({}) + 1

# SQL Expression to MongoDB Query Compiler
def compile_expression(expr):
    if expr is None:
        return {}
    if isinstance(expr, BinaryExpression):
        left = expr.left
        right = expr.right
        op = expr.operator
        key = getattr(left, 'key', None) or getattr(left, 'name', None)
        if not key:
            key = str(left).split('.')[-1]
        value = getattr(right, 'value', right)
        
        op_name = getattr(op, '__name__', '')
        if op == operator.eq or op_name == 'eq':
            return {key: value}
        elif op == operator.ne or op_name == 'ne':
            return {key: {"$ne": value}}
        elif op == operator.lt or op_name == 'lt':
            return {key: {"$lt": value}}
        elif op == operator.le or op_name == 'le':
            return {key: {"$lte": value}}
        elif op == operator.gt or op_name == 'gt':
            return {key: {"$gt": value}}
        elif op == operator.ge or op_name == 'ge':
            return {key: {"$gte": value}}
        else:
            return {key: value}
    elif isinstance(expr, BooleanClauseList):
        op = expr.operator
        op_name = getattr(op, '__name__', '')
        sub_queries = [compile_expression(c) for c in expr.clauses]
        if op == operator.or_ or op_name == 'or_':
            return {"$or": sub_queries}
        else:
            return {"$and": sub_queries}
    elif isinstance(expr, dict):
        return expr
    return {}

# MongoDB Query Class mimicking SQLAlchemy Query
class MongoQuery:
    def __init__(self, session, entity):
        self.session = session
        self.db = session.db
        
        if isinstance(entity, InstrumentedAttribute):
            self.model_class = entity.class_
            self.select_keys = [entity.key]
        elif hasattr(entity, 'class_'):
            self.model_class = entity.class_
            self.select_keys = [entity.key]
        else:
            self.model_class = entity
            self.select_keys = None
            
        self.collection_name = self.model_class.__tablename__
        self.filter_query = {}
        self.sort_fields = None
        self.limit_val = None

    def filter(self, *args):
        for arg in args:
            q = compile_expression(arg)
            if q:
                self.filter_query.update(q)
        return self

    def order_by(self, *args):
        self.sort_fields = []
        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2:
                self.sort_fields.append(arg)
            elif isinstance(arg, str):
                self.sort_fields.append((arg, 1))
            elif isinstance(arg, UnaryExpression):
                key = getattr(arg.element, 'key', None) or getattr(arg.element, 'name', None)
                mod_name = getattr(arg.modifier, '__name__', '')
                direction = -1 if 'desc' in mod_name else 1
                self.sort_fields.append((key, direction))
            elif hasattr(arg, 'element') and hasattr(arg, 'modifier'):
                key = getattr(arg.element, 'key', None) or getattr(arg.element, 'name', None)
                mod_name = getattr(arg.modifier, '__name__', '')
                direction = -1 if 'desc' in mod_name else 1
                self.sort_fields.append((key, direction))
        return self

    def limit(self, value):
        self.limit_val = value
        return self

    def count(self):
        return self.db[self.collection_name].count_documents(self.filter_query)

    def _doc_to_instance(self, doc):
        instance = self.model_class()
        for k, v in doc.items():
            if k != "_id":
                setattr(instance, k, v)
        self.session.register_loaded(instance)
        return instance

    def first(self):
        if self.select_keys:
            cursor = self.db[self.collection_name].find(self.filter_query, {k: 1 for k in self.select_keys})
            if self.sort_fields:
                cursor = cursor.sort(self.sort_fields)
            doc = next(cursor, None)
            if doc:
                return (doc.get(self.select_keys[0]),)
            return None
        else:
            cursor = self.db[self.collection_name].find(self.filter_query)
            if self.sort_fields:
                cursor = cursor.sort(self.sort_fields)
            doc = next(cursor, None)
            if doc:
                return self._doc_to_instance(doc)
            return None

    def all(self):
        cursor = self.db[self.collection_name].find(self.filter_query)
        if self.sort_fields:
            cursor = cursor.sort(self.sort_fields)
        if self.limit_val is not None:
            cursor = cursor.limit(self.limit_val)
            
        if self.select_keys:
            return [(doc.get(self.select_keys[0]),) for doc in cursor]
        else:
            return [self._doc_to_instance(doc) for doc in cursor]

# MongoDB Session Class mimicking SQLAlchemy Session
class MongoSession:
    def __init__(self, db):
        self.db = db
        self.to_add = []
        self.loaded_instances = {}  # maps (model_class, id) -> (instance, original_dict)

    def query(self, entity):
        return MongoQuery(self, entity)

    def add(self, instance):
        if instance not in self.to_add:
            self.to_add.append(instance)

    def register_loaded(self, instance):
        if instance and getattr(instance, "id", None):
            key = (instance.__class__, instance.id)
            if key not in self.loaded_instances:
                self.loaded_instances[key] = (instance, self._get_dict(instance))

    def _get_dict(self, instance):
        d = {}
        for k, v in list(instance.__dict__.items()):
            if not k.startswith('_') and not callable(v) and k != 'registry' and k != 'metadata':
                d[k] = v
        return d

    def commit(self):
        # 1. Insert/upsert new documents
        for instance in self.to_add:
            collection_name = instance.__tablename__
            if not getattr(instance, "id", None):
                instance.id = get_next_sequence_value(self.db, collection_name)
            doc = self._get_dict(instance)
            self.db[collection_name].replace_one({"id": instance.id}, doc, upsert=True)
            self.register_loaded(instance)
        self.to_add.clear()

        # 2. Update existing modified documents
        for key, (instance, original_dict) in list(self.loaded_instances.items()):
            current_dict = self._get_dict(instance)
            if current_dict != original_dict:
                collection_name = instance.__tablename__
                self.db[collection_name].replace_one({"id": instance.id}, current_dict)
                self.loaded_instances[key] = (instance, current_dict)

    def refresh(self, instance):
        if getattr(instance, "id", None):
            collection_name = instance.__tablename__
            doc = self.db[collection_name].find_one({"id": instance.id})
            if doc:
                for k, v in doc.items():
                    if k != "_id":
                        setattr(instance, k, v)
                key = (instance.__class__, instance.id)
                self.loaded_instances[key] = (instance, self._get_dict(instance))

    def close(self):
        pass

# Session Factory
class SessionLocalFactory:
    def __call__(self):
        if db_mode == "mongodb":
            return MongoSession(mongo_db)
        else:
            return SQLSessionLocal()

SessionLocal = SessionLocalFactory()

def get_db():
    """Dependency injector for database sessions (MongoDB or SQL fallback)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

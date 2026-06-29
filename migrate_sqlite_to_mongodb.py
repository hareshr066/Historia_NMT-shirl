import sqlite3
from pymongo import MongoClient

# Configure dnspython to use Google and Cloudflare DNS to bypass network/VPN DNS refusals
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']
    print("DNS: Overrode default resolver to Google/Cloudflare DNS.")
except Exception as dns_err:
    print(f"DNS Warning: Could not override default resolver: {dns_err}")

mongo_uri = "mongodb+srv://wshirlypriscilla_db_user:ItXlljBkEeTBpym6@cluster0.hnr1fr0.mongodb.net/?appName=Cluster0"
sqlite_db_path = "chronoiks_ai.db"

def migrate():
    print("Connecting to local SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    print("Connecting to MongoDB...")
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client["chronoiks_ai"]
    
    # Get all tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    for table in tables:
        if table.startswith("sqlite_"):
            continue
            
        sqlite_cursor.execute(f'SELECT * FROM "{table}";')
        rows = sqlite_cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in sqlite_cursor.description]
        
        print(f"Table '{table}': Found {len(rows)} records in SQLite.")
        
        # Clear existing collection in MongoDB
        mongo_db[table].delete_many({})
        
        documents = []
        max_id = 0
        for row in rows:
            doc = dict(zip(column_names, row))
            if "id" in doc and doc["id"] is not None:
                try:
                    val = int(doc["id"])
                    if val > max_id:
                        max_id = val
                except ValueError:
                    pass
            documents.append(doc)
            
        if documents:
            mongo_db[table].insert_many(documents)
            print(f" -> Migrated {len(documents)} records to MongoDB collection '{table}'.")
            
        # Initialize counter for this table
        if max_id > 0:
            mongo_db["counters"].replace_one(
                {"_id": table},
                {"_id": table, "sequence_value": max_id},
                upsert=True
            )
            print(f" -> Set counter for '{table}' to {max_id}.")
            
    sqlite_conn.close()
    print("Data migration completed successfully!")

if __name__ == "__main__":
    migrate()

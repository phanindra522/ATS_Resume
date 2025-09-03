import chromadb
from chromadb.config import Settings as ChromaSettings
import os
import json
from app.core.config import settings
from typing import Dict, List, Any
import uuid
from datetime import datetime

# Data storage files
DATA_DIR = "./data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
RESUMES_FILE = os.path.join(DATA_DIR, "resumes.json")
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")
SCORING_FILE = os.path.join(DATA_DIR, "scoring_results.json")

# In-Memory Storage with persistence
in_memory_db: Dict[str, List[Dict[str, Any]]] = {
    "users": [],
    "resumes": [],
    "jobs": [],
    "scoring_results": []
}

# ChromaDB (keeping this for embeddings)
chroma_client = None
chroma_collection = None

def ensure_data_directory():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_data_from_files():
    """Load data from JSON files into memory"""
    global in_memory_db
    
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                in_memory_db["users"] = json.load(f)
        
        if os.path.exists(RESUMES_FILE):
            with open(RESUMES_FILE, 'r', encoding='utf-8') as f:
                in_memory_db["resumes"] = json.load(f)
        
        if os.path.exists(JOBS_FILE):
            with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                in_memory_db["jobs"] = json.load(f)
        
        if os.path.exists(SCORING_FILE):
            with open(SCORING_FILE, 'r', encoding='utf-8') as f:
                in_memory_db["scoring_results"] = json.load(f)
                
        print(f"✅ Loaded {sum(len(data) for data in in_memory_db.values())} records from persistent storage")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not load existing data: {e}")
        print("Starting with fresh in-memory database")

def save_data_to_files():
    """Save data from memory to JSON files"""
    try:
        ensure_data_directory()
        
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(in_memory_db["users"], f, indent=2, default=str)
        
        with open(RESUMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(in_memory_db["resumes"], f, indent=2, default=str)
        
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(in_memory_db["jobs"], f, indent=2, default=str)
        
        with open(SCORING_FILE, 'w', encoding='utf-8') as f:
            json.dump(in_memory_db["scoring_results"], f, indent=2, default=str)
            
        print(f"💾 Saved {sum(len(data) for data in in_memory_db.values())} records to persistent storage")
        
    except Exception as e:
        print(f"❌ Error saving data: {e}")

async def init_db():
    global chroma_client, chroma_collection

    # Ensure data directory exists
    ensure_data_directory()
    
    # Load existing data from files
    load_data_from_files()

    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIRECTORY,
        settings=ChromaSettings(
            anonymized_telemetry=False
        )
    )

    # Get or create collection for resume embeddings
    try:
        chroma_collection = chroma_client.get_collection("resume_embeddings")
    except:
        chroma_collection = chroma_client.create_collection("resume_embeddings")

    print("✅ In-memory database initialized with persistence")
    print(f" Collections: {list(in_memory_db.keys())}")
    print(f"👥 Users: {len(in_memory_db['users'])}")
    print(f" Resumes: {len(in_memory_db['resumes'])}")
    print(f"💼 Jobs: {len(in_memory_db['jobs'])}")
    print(f" Scoring Results: {len(in_memory_db['scoring_results'])}")

async def create_indexes():
    # No need for indexes in in-memory storage
    pass

async def close_db():
    if chroma_client:
        chroma_client.close()
    
    # Save data before shutting down
    save_data_to_files()
    print("💾 Data saved before shutdown")

def get_database():
    """Return in-memory database interface"""
    return InMemoryDB()

def get_chroma_collection():
    return chroma_collection

class InMemoryDB:
    """In-memory database interface that mimics MongoDB operations with persistence"""

    def __getattr__(self, name):
        """Return collection-like object for any attribute access"""
        return InMemoryCollection(name)

class InMemoryCollection:
    """In-memory collection that mimics MongoDB collection operations with persistence"""

    def __init__(self, name: str):
        self.name = name
        self.data = in_memory_db.get(name, [])

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single document"""
        doc_id = str(uuid.uuid4())
        document["_id"] = doc_id
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()

        self.data.append(document)
        
        # Save to file after each insert
        save_data_to_files()
        
        return {"inserted_id": doc_id}

    async def find_one(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Find a single document matching the filter"""
        for doc in self.data:
            if self._matches_filter(doc, filter_dict):
                return doc
        return None

    async def find(self, filter_dict: Dict[str, Any] = None) -> 'InMemoryCursor':
        """Find documents matching the filter - returns a cursor-like object"""
        if not filter_dict:
            matching_data = self.data.copy()
        else:
            matching_data = []
            for doc in self.data:
                if self._matches_filter(doc, filter_dict):
                    matching_data.append(doc)
        
        return InMemoryCursor(matching_data)

    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update a single document"""
        for i, doc in enumerate(self.data):
            if self._matches_filter(doc, filter_dict):
                # Handle $set operations
                if "$set" in update_dict:
                    for key, value in update_dict["$set"].items():
                        doc[key] = value
                else:
                    # Direct update
                    doc.update(update_dict)

                doc["updated_at"] = datetime.utcnow()
                
                # Save to file after each update
                save_data_to_files()
                
                return {"matched_count": 1, "modified_count": 1}

        return {"matched_count": 0, "modified_count": 0}

    async def delete_one(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a single document"""
        for i, doc in enumerate(self.data):
            if self._matches_filter(doc, filter_dict):
                del self.data[i]
                
                # Save to file after each delete
                save_data_to_files()
                
                return {"deleted_count": 1}
        return {"deleted_count": 0}

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple aggregation pipeline support"""
        # For now, just return the data (can be enhanced later)
        return self.data.copy()

    def _matches_filter(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if document matches the filter"""
        for key, value in filter_dict.items():
            if key == "_id" and isinstance(value, str):
                # Handle string ID comparison
                if doc.get("_id") != value:
                    return False
            elif key not in doc or doc[key] != value:
                return False
        return True

    def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Convert to list (for compatibility with MongoDB cursor)"""
        if length:
            return self.data[:length]
        return self.data.copy()

class InMemoryCursor:
    """Cursor-like object that mimics MongoDB cursor behavior"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Convert to list (for compatibility with MongoDB cursor)"""
        if length:
            return self.data[:length]
        return self.data.copy()
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
# Multi-Agent Scoring System - Performance Optimization Guide

## 🚀 Overview

This guide provides optimization strategies for the multi-agent scoring system to handle large-scale usage efficiently.

## 📊 Current Performance Characteristics

### **Baseline Metrics:**
- **Processing Time:** ~2-5 seconds per resume (depending on complexity)
- **Memory Usage:** ~50-100MB per scoring session
- **Concurrent Capacity:** 10-20 simultaneous scoring requests
- **Agent Execution:** All agents run in parallel (async/await)

### **Bottlenecks Identified:**
1. **LLM API Calls** - Embedding generation (semantic agent)
2. **ChromaDB Operations** - Vector similarity calculations
3. **Text Processing** - Regex operations and skill extraction
4. **Memory Allocation** - Large text processing and embeddings

---

## ⚡ Optimization Strategies

### **1. Caching Layer**

#### **Embedding Cache**
```python
# Add to semantic_agent.py
import redis
from functools import lru_cache

class SemanticSimilarityAgent(BaseAgent):
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SEMANTIC_SIMILARITY, weight)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 86400  # 24 hours
    
    async def _get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embedding from Redis"""
        cached = self.redis_client.get(f"embedding:{text_hash}")
        if cached:
            return json.loads(cached)
        return None
    
    async def _cache_embedding(self, text_hash: str, embedding: List[float]):
        """Cache embedding in Redis"""
        self.redis_client.setex(
            f"embedding:{text_hash}", 
            self.cache_ttl, 
            json.dumps(embedding)
        )
```

#### **Scoring Results Cache**
```python
# Add to scoring_coordinator.py
class MultiAgentScoringCoordinator:
    def __init__(self):
        # ... existing code ...
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        self.scoring_cache_ttl = 3600  # 1 hour
    
    async def _get_cached_score(self, resume_id: str, job_id: str) -> Optional[ScoringBreakdown]:
        """Get cached scoring result"""
        cache_key = f"score:{resume_id}:{job_id}"
        cached = self.redis_client.get(cache_key)
        if cached:
            return ScoringBreakdown.from_dict(json.loads(cached))
        return None
    
    async def _cache_score(self, resume_id: str, job_id: str, breakdown: ScoringBreakdown):
        """Cache scoring result"""
        cache_key = f"score:{resume_id}:{job_id}"
        self.redis_client.setex(
            cache_key, 
            self.scoring_cache_ttl, 
            json.dumps(breakdown.to_dict())
        )
```

### **2. Database Optimizations**

#### **ChromaDB Connection Pooling**
```python
# Add to database.py
import chromadb
from chromadb.config import Settings

class ChromaDBManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self.connection_pool_size = 10
    
    def get_client(self):
        if self.client is None:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db",
                anonymized_telemetry=False
            ))
        return self.client
    
    def get_collection(self, name: str = "resumes"):
        if self.collection is None:
            client = self.get_client()
            self.collection = client.get_or_create_collection(name)
        return self.collection
```

#### **MongoDB Indexing**
```python
# Add to main.py startup
async def create_indexes():
    """Create database indexes for better performance"""
    db = get_database()
    
    # Resume indexes
    await db.resumes.create_index("user_id")
    await db.resumes.create_index("created_at")
    await db.resumes.create_index([("user_id", 1), ("created_at", -1)])
    
    # Job indexes
    await db.jobs.create_index("user_id")
    await db.jobs.create_index("created_at")
    
    # Scoring results indexes
    await db.scoring_results.create_index("user_id")
    await db.scoring_results.create_index("job_id")
    await db.scoring_results.create_index([("user_id", 1), ("created_at", -1)])
```

### **3. Agent Optimizations**

#### **Parallel Processing Enhancement**
```python
# Enhanced coordinator with batch processing
class MultiAgentScoringCoordinator:
    async def score_resumes_batch(self, resumes: List[Dict], job: Dict) -> List[ScoringBreakdown]:
        """Score multiple resumes in parallel batches"""
        batch_size = 5  # Process 5 resumes at a time
        results = []
        
        for i in range(0, len(resumes), batch_size):
            batch = resumes[i:i + batch_size]
            batch_tasks = [self.score_resume(resume, job) for resume in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
```

#### **Text Processing Optimization**
```python
# Optimized skill extraction with compiled regex
import re
from functools import lru_cache

class SkillMatchingAgent(BaseAgent):
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SKILL_MATCHING, weight)
        # Pre-compile regex patterns
        self.skills_patterns = self._compile_patterns()
    
    @lru_cache(maxsize=128)
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        return {
            'skills_section': re.compile(r'skills?[:\s]*([^.\n]+?)(?:\n|\.|$)', re.IGNORECASE),
            'experience': re.compile(r'(?:developed|built|created|implemented)\s+(?:using\s+)?([^.\n]+?)(?:\s|,|\.|$)', re.IGNORECASE),
            # ... more patterns
        }
```

### **4. Memory Management**

#### **Streaming Processing**
```python
# Process large datasets in chunks
async def process_large_resume_batch(resumes: List[Dict], job: Dict, chunk_size: int = 100):
    """Process resumes in chunks to manage memory"""
    results = []
    
    for i in range(0, len(resumes), chunk_size):
        chunk = resumes[i:i + chunk_size]
        chunk_results = await coordinator.score_resumes_batch(chunk, job)
        results.extend(chunk_results)
        
        # Force garbage collection
        import gc
        gc.collect()
    
    return results
```

#### **Embedding Memory Optimization**
```python
# Use numpy arrays for better memory efficiency
import numpy as np

class SemanticSimilarityAgent(BaseAgent):
    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Optimized cosine similarity with numpy"""
        # Convert to numpy arrays for vectorized operations
        vec1 = np.array(embedding1, dtype=np.float32)  # Use float32 to save memory
        vec2 = np.array(embedding2, dtype=np.float32)
        
        # Vectorized operations
        dot_product = np.dot(vec1, vec2)
        norms = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        
        return dot_product / norms if norms > 0 else 0.0
```

### **5. API Rate Limiting & Queuing**

#### **Request Queuing**
```python
# Add to scoring router
import asyncio
from asyncio import Queue

class ScoringQueue:
    def __init__(self, max_concurrent: int = 10):
        self.queue = Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.workers = []
    
    async def process_scoring_request(self, resume: Dict, job: Dict):
        """Process scoring request with concurrency control"""
        async with self.semaphore:
            return await coordinator.score_resume(resume, job)

# Global queue instance
scoring_queue = ScoringQueue(max_concurrent=10)

@router.post("/score/{job_id}")
async def score_resumes_with_queue(job_id: str, current_user = Depends(get_current_user)):
    """Score resumes with queuing for better performance"""
    # ... existing code ...
    
    # Process with queue
    scored_resumes = []
    for resume in resumes:
        result = await scoring_queue.process_scoring_request(resume, job)
        scored_resumes.append(result)
    
    return {"scored_resumes": scored_resumes}
```

---

## 📈 Performance Monitoring

### **Metrics Collection**
```python
# Add to scoring_coordinator.py
import time
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    total_time: float
    agent_times: Dict[str, float]
    memory_usage: float
    cache_hits: int
    cache_misses: int

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
    
    def record_scoring_session(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.metrics.append(metrics)
        
        # Keep only last 1000 records
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def get_average_performance(self) -> Dict[str, float]:
        """Get average performance metrics"""
        if not self.metrics:
            return {}
        
        return {
            "avg_total_time": sum(m.total_time for m in self.metrics) / len(self.metrics),
            "avg_memory_usage": sum(m.memory_usage for m in self.metrics) / len(self.metrics),
            "cache_hit_rate": sum(m.cache_hits for m in self.metrics) / 
                            sum(m.cache_hits + m.cache_misses for m in self.metrics)
        }
```

### **Health Check Endpoint**
```python
# Add to scoring router
@router.get("/health")
async def health_check():
    """Health check endpoint with performance metrics"""
    try:
        # Test each agent
        test_resume = {"title": "Test", "text_content": "Test content"}
        test_job = {"title": "Test Job", "skills": ["test"], "requirements": ["test"]}
        
        start_time = time.time()
        result = await coordinator.score_resume(test_resume, test_job)
        end_time = time.time()
        
        return {
            "status": "healthy",
            "processing_time": end_time - start_time,
            "agents_working": len(result.agent_results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

---

## 🚀 Deployment Optimizations

### **Docker Configuration**
```dockerfile
# Optimized Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with optimized settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### **Environment Variables**
```bash
# .env for production
# Database
MONGODB_URL=mongodb://localhost:27017/ats_resume
CHROMA_PERSIST_DIRECTORY=/app/chroma_db

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Performance
MAX_CONCURRENT_REQUESTS=20
BATCH_SIZE=10
CACHE_TTL=3600

# LLM
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```

---

## 📊 Expected Performance Improvements

### **With Caching:**
- **50-70% reduction** in processing time for repeated requests
- **80% reduction** in LLM API calls
- **60% reduction** in ChromaDB queries

### **With Database Optimization:**
- **30-40% faster** database queries
- **Better concurrent** request handling
- **Reduced memory** usage

### **With Batch Processing:**
- **3-5x faster** for large resume batches
- **Better resource** utilization
- **Improved scalability**

---

## 🔧 Implementation Priority

1. **High Priority:**
   - Redis caching layer
   - Database indexing
   - Request queuing

2. **Medium Priority:**
   - Batch processing
   - Memory optimization
   - Performance monitoring

3. **Low Priority:**
   - Advanced optimizations
   - Custom deployment configs
   - Detailed analytics

---

## 📝 Monitoring Checklist

- [ ] Redis cache hit rate > 70%
- [ ] Average processing time < 3 seconds
- [ ] Memory usage < 200MB per request
- [ ] Database query time < 100ms
- [ ] Error rate < 1%
- [ ] Concurrent requests handled > 20

This optimization guide provides a comprehensive approach to scaling the multi-agent scoring system for production use.

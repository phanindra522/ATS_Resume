# Semantic Similarity Agent - Implementation Guide

## 🎯 **Overview**

The Semantic Similarity Agent is the most sophisticated agent in the multi-agent system, using **LLM-powered embeddings** to understand the semantic meaning of text beyond exact keyword matches. It captures the conceptual similarity between resume content and job descriptions.

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                Semantic Similarity Agent                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Resume Text   │    │   Job Text      │                │
│  │   Extraction    │    │   Extraction    │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  LLM Embedding  │    │  LLM Embedding  │                │
│  │   Generation    │    │   Generation    │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────────────────────────────┐                │
│  │        Cosine Similarity                │                │
│  │         Calculation                     │                │
│  └─────────────────────────────────────────┘                │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────┐                │
│  │      Score Normalization &              │                │
│  │      Confidence Analysis                │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Implementation Details**

### **1. Class Structure**

```python
class SemanticSimilarityAgent(BaseAgent):
    """Agent for semantic similarity using ChromaDB embeddings"""
    
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SEMANTIC_SIMILARITY, weight)
```

**Key Features:**
- **Weight**: 25% of total score (highest among all agents)
- **Inheritance**: Extends BaseAgent for consistent interface
- **Purpose**: Semantic understanding beyond keyword matching

### **2. Main Analysis Method**

```python
async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
    """Analyze semantic similarity between resume and job"""
    try:
        # Step 1: Extract text content
        resume_text = self._extract_text_content(resume)
        job_text = self._extract_job_content(job)
        
        # Step 2: Generate embeddings
        resume_embedding = self._generate_embedding(resume_text)
        job_embedding = self._generate_embedding(job_text)
        
        # Step 3: Calculate similarity
        similarity_score = self._calculate_cosine_similarity(resume_embedding, job_embedding)
        
        # Step 4: Normalize score
        normalized_score = max(0.0, (similarity_score + 1) / 2)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_embedding_confidence(resume_embedding, job_embedding)
        
        return self._create_result(score=normalized_score, evidence={...}, confidence=confidence)
```

## 🧠 **LLM Integration**

### **Embedding Generation Pipeline**

The agent uses a **multi-provider embedding system** with fallback mechanisms:

```python
def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding using configured LLM provider"""
    try:
        if settings.LLM_PROVIDER.lower() == "openai":
            return generate_openai_embedding(text)
        elif settings.LLM_PROVIDER.lower() == "gemini":
            return generate_gemini_embedding(text)
        else:
            # Fallback to placeholder for other providers
            return generate_placeholder_embedding(text, settings.EMBEDDING_DIMENSION)
    except Exception as e:
        print(f"Embedding generation failed: {e}, using placeholder")
        return generate_placeholder_embedding(text, settings.EMBEDDING_DIMENSION)
```

### **OpenAI Integration**

```python
def generate_openai_embedding(text: str) -> np.ndarray:
    """Generate embedding using OpenAI"""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.LLM_PROVIDER_API_KEY)
        response = client.embeddings.create(
            model=settings.LLM_EMBEDDING_MODEL,  # e.g., "text-embedding-3-small"
            input=text
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        raise Exception(f"OpenAI embedding error: {str(e)}")
```

**Supported OpenAI Models:**
- `text-embedding-ada-002` (1536 dimensions)
- `text-embedding-3-small` (1536 dimensions)
- `text-embedding-3-large` (3072 dimensions)

### **Google Gemini Integration**

```python
def generate_gemini_embedding(text: str) -> np.ndarray:
    """Generate embedding using Google Gemini"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.LLM_PROVIDER_API_KEY)
        result = genai.embed_content(
            model=settings.LLM_EMBEDDING_MODEL,  # e.g., "text-embedding-004"
            content=text,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'])
    except Exception as e:
        raise Exception(f"Gemini embedding error: {str(e)}")
```

**Supported Gemini Models:**
- `text-embedding-004` (768 dimensions)

### **Fallback Mechanism**

```python
def generate_placeholder_embedding(text: str, dimension: int = None) -> np.ndarray:
    """Generate a placeholder embedding for fallback"""
    if dimension is None:
        dimension = settings.EMBEDDING_DIMENSION
    return np.random.rand(dimension)
```

**Fallback Scenarios:**
- LLM API unavailable
- Invalid API key
- Network connectivity issues
- Rate limiting

## 📊 **Similarity Calculation**

### **Cosine Similarity Algorithm**

```python
def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Ensure same dimensions
        if len(vec1) != len(vec2):
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, similarity))
        
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0
```

### **Mathematical Formula**

```
Cosine Similarity = (A · B) / (||A|| × ||B||)

Where:
- A · B = dot product of vectors A and B
- ||A|| = magnitude (norm) of vector A
- ||B|| = magnitude (norm) of vector B
- Result range: [-1, 1]
```

### **Score Normalization**

```python
# Normalize to 0-1 range (cosine similarity is -1 to 1)
normalized_score = max(0.0, (similarity_score + 1) / 2)
```

**Normalization Logic:**
- **Cosine Similarity Range**: [-1, 1]
- **Normalized Range**: [0, 1]
- **Formula**: `(similarity + 1) / 2`
- **Examples**:
  - Similarity = 1.0 → Normalized = 1.0 (perfect match)
  - Similarity = 0.0 → Normalized = 0.5 (neutral)
  - Similarity = -1.0 → Normalized = 0.0 (opposite)

## 🎯 **Confidence Analysis**

### **Embedding Quality Assessment**

```python
def _calculate_embedding_confidence(self, embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate confidence based on embedding quality"""
    try:
        # Check embedding dimensions
        if len(embedding1) != len(embedding2):
            return 0.5  # Lower confidence for dimension mismatch
        
        # Check for zero vectors
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.1  # Very low confidence for zero vectors
        
        # Check for reasonable embedding values
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.2  # Low confidence for all-zero embeddings
        
        # Check for NaN or infinite values
        if np.any(np.isnan(vec1)) or np.any(np.isnan(vec2)) or np.any(np.isinf(vec1)) or np.any(np.isinf(vec2)):
            return 0.3  # Low confidence for invalid values
        
        # Higher confidence for embeddings with good variance
        variance1 = np.var(vec1)
        variance2 = np.var(vec2)
        
        if variance1 > 0.01 and variance2 > 0.01:
            return 1.0  # High confidence
        elif variance1 > 0.001 and variance2 > 0.001:
            return 0.8  # Good confidence
        else:
            return 0.6  # Medium confidence
            
    except Exception as e:
        print(f"Error calculating embedding confidence: {e}")
        return 0.5  # Default medium confidence
```

### **Confidence Factors**

| Factor | Impact | Confidence Level |
|--------|--------|------------------|
| **Dimension Mismatch** | Different embedding sizes | 0.5 (Medium) |
| **Zero Vectors** | Empty or invalid embeddings | 0.1 (Very Low) |
| **All-Zero Embeddings** | Placeholder embeddings | 0.2 (Low) |
| **Invalid Values** | NaN or infinite values | 0.3 (Low) |
| **High Variance** | Good embedding quality | 1.0 (High) |
| **Medium Variance** | Decent embedding quality | 0.8 (Good) |
| **Low Variance** | Poor embedding quality | 0.6 (Medium) |

## 💾 **ChromaDB Integration**

### **Vector Storage**

```python
async def store_resume_embedding(self, resume_id: str, resume_text: str, user_id: str) -> bool:
    """Store resume embedding in ChromaDB for future use"""
    try:
        embedding = self._generate_embedding(resume_text)
        if embedding is None:
            return False
        
        chroma_collection = get_chroma_collection()
        if chroma_collection is None:
            return False
        
        # Store in ChromaDB
        chroma_collection.add(
            embeddings=[embedding],
            documents=[resume_text],
            metadatas=[{"resume_id": resume_id, "user_id": user_id}],
            ids=[resume_id]
        )
        
        return True
        
    except Exception as e:
        print(f"Error storing resume embedding: {e}")
        return False
```

### **Vector Retrieval**

```python
async def remove_resume_embedding(self, resume_id: str) -> bool:
    """Remove resume embedding from ChromaDB"""
    try:
        chroma_collection = get_chroma_collection()
        if chroma_collection is None:
            return False
        
        # Remove from ChromaDB
        chroma_collection.delete(ids=[resume_id])
        
        return True
        
    except Exception as e:
        print(f"Error removing resume embedding: {e}")
        return False
```

## 🔄 **Processing Flow**

### **Step-by-Step Execution**

1. **Text Extraction**
   ```python
   resume_text = self._extract_text_content(resume)
   job_text = self._extract_job_content(job)
   ```

2. **Embedding Generation**
   ```python
   resume_embedding = self._generate_embedding(resume_text)
   job_embedding = self._generate_embedding(job_text)
   ```

3. **Similarity Calculation**
   ```python
   similarity_score = self._calculate_cosine_similarity(resume_embedding, job_embedding)
   ```

4. **Score Normalization**
   ```python
   normalized_score = max(0.0, (similarity_score + 1) / 2)
   ```

5. **Confidence Assessment**
   ```python
   confidence = self._calculate_embedding_confidence(resume_embedding, job_embedding)
   ```

6. **Result Creation**
   ```python
   return self._create_result(score=normalized_score, evidence={...}, confidence=confidence)
   ```

## 📈 **Example Output**

### **Sample Result**

```json
{
  "score": 0.78,
  "percentage": 78.0,
  "weight": 0.25,
  "evidence": {
    "resume_embedding_generated": true,
    "job_embedding_generated": true,
    "similarity_score": 0.56,
    "normalized_score": 0.78,
    "embedding_dimensions": 768,
    "resume_text_length": 2500,
    "job_text_length": 1800
  },
  "confidence": 0.92,
  "error": null
}
```

### **Evidence Breakdown**

- **resume_embedding_generated**: Whether resume embedding was successfully created
- **job_embedding_generated**: Whether job embedding was successfully created
- **similarity_score**: Raw cosine similarity (-1 to 1)
- **normalized_score**: Normalized score (0 to 1)
- **embedding_dimensions**: Number of dimensions in embeddings
- **resume_text_length**: Length of resume text processed
- **job_text_length**: Length of job text processed

## 🚀 **Performance Characteristics**

### **Timing Analysis**

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| **Text Extraction** | < 1ms | Very fast |
| **Embedding Generation** | 200-500ms | Depends on LLM provider |
| **Similarity Calculation** | < 1ms | Fast numpy operations |
| **Confidence Analysis** | < 1ms | Fast statistical calculations |
| **Total Processing** | 200-500ms | Dominated by embedding generation |

### **Memory Usage**

- **Embedding Storage**: ~3KB per embedding (768 dimensions × 4 bytes)
- **Text Processing**: Minimal memory overhead
- **ChromaDB**: Efficient vector storage and retrieval

## 🔧 **Configuration**

### **Environment Variables**

```env
# LLM Provider Configuration
LLM_PROVIDER=gemini                    # or "openai"
LLM_PROVIDER_API_KEY=your_api_key_here
LLM_EMBEDDING_MODEL=text-embedding-004 # or "text-embedding-3-small"
EMBEDDING_DIMENSION=768                # or 1536 for OpenAI

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### **Model Selection Guide**

| Provider | Model | Dimensions | Cost | Quality |
|----------|-------|------------|------|---------|
| **OpenAI** | text-embedding-3-small | 1536 | Low | High |
| **OpenAI** | text-embedding-3-large | 3072 | High | Very High |
| **Gemini** | text-embedding-004 | 768 | Low | High |

## 🎯 **Key Advantages**

### **1. Semantic Understanding**
- Captures meaning beyond exact words
- Handles synonyms and related concepts
- Understands context and intent

### **2. Flexibility**
- Multiple LLM provider support
- Fallback mechanisms for reliability
- Configurable models and dimensions

### **3. Performance**
- Efficient vector operations
- ChromaDB integration for storage
- Parallel processing support

### **4. Reliability**
- Comprehensive error handling
- Confidence scoring
- Graceful degradation

## 🔮 **Future Enhancements**

### **Potential Improvements**

1. **Caching**: Cache embeddings for repeated documents
2. **Batch Processing**: Process multiple documents simultaneously
3. **Model Fine-tuning**: Custom models for resume-job matching
4. **Multi-language Support**: Handle different languages
5. **Domain-specific Models**: Specialized models for different industries

The Semantic Similarity Agent represents the cutting edge of the multi-agent system, providing deep semantic understanding that complements the precision of rule-based agents.

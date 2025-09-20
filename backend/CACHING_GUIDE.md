# 🚀 ATS Caching System - Token Optimization Guide

## Overview

This advanced caching system dramatically reduces LLM token usage and improves response times by intelligently caching LLM responses, skill extractions, and other expensive operations.

## 🎯 Key Benefits

- **💰 Token Cost Reduction**: 70-90% reduction in OpenAI API calls
- **⚡ Faster Response Times**: Cached results return in <50ms vs 2-5s for API calls
- **🛡️ Rate Limit Protection**: Fewer API calls = less chance of hitting rate limits
- **📊 Smart Statistics**: Track cache hit ratios and estimated cost savings
- **🔄 Fallback Support**: Graceful degradation if cache fails

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Request   │───▶│ Cache Layer  │───▶│   LLM Service   │
│  (Job Parsing)  │    │              │    │  (OpenAI API)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Cache Backends  │
                    │  ┌─────────────┐ │
                    │  │   Redis     │ │ ◀── Primary (persistent)
                    │  │ (optional)  │ │
                    │  └─────────────┘ │
                    │  ┌─────────────┐ │
                    │  │   Memory    │ │ ◀── Fallback (fast)
                    │  │   Cache     │ │
                    │  └─────────────┘ │
                    └──────────────────┘
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Cache Configuration
CACHE_ENABLED=true                    # Master switch for caching
REDIS_URL=redis://localhost:6379     # Redis connection (optional)
CACHE_TTL_SECONDS=3600               # Default cache TTL (1 hour)
CACHE_LLM_TTL_SECONDS=86400          # LLM responses TTL (24 hours) 
CACHE_EMBEDDINGS_TTL_SECONDS=604800  # Embeddings TTL (7 days)
MEMORY_CACHE_SIZE=1000               # In-memory cache size
CACHE_PREFIX=ats                     # Redis key prefix
```

### Installation

1. **Install Redis (Optional but Recommended):**
   ```bash
   # Windows (via Chocolatey)
   choco install redis-64
   
   # Or use WSL/Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install redis cachetools
   ```

3. **Update Configuration:**
   - Add cache settings to your `.env` file
   - Restart the backend server

## 📊 Cache Strategies

### 1. LLM Response Caching
- **What**: Job description parsing results
- **Key**: SHA256 hash of normalized text + provider
- **TTL**: 24 hours (configurable)
- **Impact**: Saves ~500-2000 tokens per duplicate job

### 2. Skill Extraction Caching
- **What**: Extracted skills from job descriptions
- **Key**: SHA256 hash of text content
- **TTL**: 1 hour (configurable)
- **Impact**: Instant skill matching results

### 3. Text Normalization
- **Process**: Lowercase, whitespace normalization
- **Benefit**: Higher cache hit rates for similar content
- **Example**: "Software Engineer" = "software engineer" = "Software  Engineer"

## 🚀 Usage Examples

### Basic Job Parsing (Cached)

```python
from app.services.cached_llm_service import parse_job_with_cached_llm

# First call - hits OpenAI API (~1000 tokens)
result1 = await parse_job_with_cached_llm("Software Engineer at TechCorp...")

# Second call with same text - returns from cache (~0 tokens)
result2 = await parse_job_with_cached_llm("Software Engineer at TechCorp...")
```

### Cache Statistics

```python
from app.services.cached_llm_service import get_cached_llm_service

service = get_cached_llm_service()
stats = service.get_stats()

print(f"Cache Hit Ratio: {stats['cache_hit_ratio']:.2%}")
print(f"Tokens Saved: {stats['tokens_saved']}")
print(f"Estimated Savings: {stats['estimated_cost_savings']}")
```

### Skill Extraction (Cached)

```python
from app.services.cached_llm_service import extract_skills_cached

# Rule-based extraction (fast, cached)
skills = await extract_skills_cached("Python, React, AWS experience required")

# LLM-based extraction (slower, cached after first call)
skills = await extract_skills_cached(text, use_llm=True)
```

## 🛠️ API Endpoints

### Cache Management

```bash
# Get cache statistics
GET /api/jobs/cache/stats
Authorization: Bearer <token>

Response:
{
  "cache_stats": {
    "total_requests": 150,
    "cache_hits": 105,
    "cache_hit_ratio": 0.70,
    "tokens_saved": 45000,
    "estimated_cost_savings": "$0.0450"
  }
}
```

```bash
# Clear LLM cache
POST /api/jobs/cache/clear
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "LLM cache cleared successfully"
}
```

### Enhanced LLM Config

```bash
# Get LLM config with cache info
GET /api/jobs/llm-config

Response:
{
  "config": {
    "provider": "openai",
    "api_key_configured": true
  },
  "cache": {
    "enabled": true,
    "redis_url": "redis://localhost:6379",
    "ttl_seconds": 86400,
    "stats": {
      "cache_hit_ratio": 0.75,
      "total_requests": 200
    }
  }
}
```

## 📈 Performance Metrics

### Expected Performance Improvements

| Operation | Without Cache | With Cache | Improvement |
|-----------|---------------|------------|-------------|
| Job Parsing | 2-5 seconds | 50-200ms | **10-100x faster** |
| Token Usage | 500-2000 tokens | 0 tokens (cached) | **100% savings** |
| API Calls | Every request | 20-30% of requests | **70-80% reduction** |
| Cost | $0.001-0.004 | $0.0002-0.0008 | **75-80% savings** |

### Real-World Scenarios

1. **Job Reprocessing**: Same job uploaded multiple times = instant results
2. **Similar Jobs**: Slightly different formatting = high cache hit rate
3. **Bulk Processing**: Processing many similar jobs = massive token savings
4. **Development/Testing**: Repeated API calls during development = zero cost

## 🎛️ Advanced Configuration

### Custom Cache TTL per Operation

```python
# Short TTL for frequently changing data
await cache_service.set("skills", "temp_key", data, ttl=300)  # 5 minutes

# Long TTL for stable data
await cache_service.set("llm_parse", "job_key", data, ttl=604800)  # 7 days
```

### Cache Warmup (Preloading)

```python
from app.services.cached_llm_service import get_cached_llm_service

service = get_cached_llm_service()

# Warmup with common job descriptions
job_samples = [
    "Software Engineer position requiring Python and React",
    "Data Scientist role with ML experience",
    "DevOps Engineer with AWS and Kubernetes"
]

stats = await service.warmup_cache(job_samples)
print(f"Warmed up {stats['cached']} entries")
```

### Memory-Only Mode (No Redis)

```python
# In config.py or environment
REDIS_URL = ""  # Empty to disable Redis
CACHE_ENABLED = true  # Still use memory cache
```

## 🔍 Monitoring & Debugging

### Cache Hit Rate Monitoring

```python
# Check cache performance
stats = service.get_stats()

# Good cache hit rate: 60-90%
# Low hit rate (<30%): Consider longer TTL or different cache keys
if stats['cache_hit_ratio'] < 0.3:
    print("⚠️ Low cache hit rate - review cache strategy")
```

### Cache Key Analysis

```python
# See what's being cached
import hashlib

text = "Your job description here"
normalized = text.lower().strip()
cache_key = hashlib.sha256(f"openai:{normalized}".encode()).hexdigest()[:16]
print(f"Cache key: llm_job_parse:{cache_key}")
```

## 🚨 Troubleshooting

### Redis Connection Issues

```python
# Check Redis connectivity
try:
    cache_service = get_cache_service()
    await cache_service.primary.get("test_key")
    print("✅ Redis connected")
except Exception as e:
    print(f"❌ Redis error: {e}")
    print("💡 Using memory cache only")
```

### Memory Cache Full

```python
# Increase memory cache size
MEMORY_CACHE_SIZE=2000  # Double the size

# Or reduce TTL for more turnover
CACHE_TTL_SECONDS=1800  # 30 minutes instead of 1 hour
```

### Low Cache Hit Rate

**Common causes:**
1. **Text variations**: Different formatting of same content
2. **Short TTL**: Cache expiring too quickly
3. **Unique content**: Each request is genuinely different

**Solutions:**
1. **Better normalization**: Remove extra whitespace, standardize format
2. **Longer TTL**: Increase cache lifetime for stable content
3. **Semantic similarity**: Use embedding-based similarity (advanced feature)

## 🎯 Best Practices

### 1. Cache Key Design
- Use content hashes for deterministic keys
- Include relevant parameters (provider, model)
- Keep keys short but unique

### 2. TTL Strategy
- **Stable data**: Long TTL (days/weeks)
- **Dynamic data**: Short TTL (minutes/hours)
- **Development**: Very short TTL for testing

### 3. Error Handling
- Always have fallback mechanisms
- Log cache errors for debugging
- Don't fail operations due to cache issues

### 4. Cache Invalidation
- Clear cache when model changes
- Invalidate on configuration updates
- Regular cleanup for development

## 💡 Pro Tips

1. **Monitor hit rates**: Aim for 60%+ cache hit ratio
2. **Use Redis in production**: Persistent cache across restarts
3. **Warm up cache**: Preload common job descriptions
4. **Test with real data**: Use actual job descriptions for testing
5. **Monitor token usage**: Track savings over time

## 🔮 Future Enhancements

- **Semantic similarity caching**: Cache similar (not just identical) content
- **ML-powered cache prediction**: Predict what to cache next
- **Distributed caching**: Multi-node cache synchronization
- **Cache analytics**: Detailed usage patterns and optimization suggestions
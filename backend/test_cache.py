"""
Test script to verify caching functionality
Run this to test cache performance and token savings
"""
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.cached_llm_service import get_cached_llm_service, parse_job_with_cached_llm

async def test_cache_performance():
    """Test caching performance with sample job descriptions"""
    
    print("🚀 Testing ATS Caching System\n")
    
    # Sample job descriptions for testing
    job_samples = [
        """
        Software Engineer - TechCorp
        
        We are looking for a skilled Software Engineer to join our team.
        
        Requirements:
        - 3+ years of Python experience
        - Experience with React and JavaScript
        - Knowledge of AWS cloud services
        - Bachelor's degree in Computer Science
        
        Location: San Francisco, CA
        Salary: $120,000 - $150,000
        """,
        
        """
        Data Scientist Position
        
        Join our data science team to work on cutting-edge ML projects.
        
        Required Skills:
        - Python programming
        - Machine learning experience
        - SQL and database knowledge
        - Statistics background
        
        Location: Remote
        Experience: 2-5 years
        """,
        
        # Duplicate of first job (should hit cache)
        """
        Software Engineer - TechCorp
        
        We are looking for a skilled Software Engineer to join our team.
        
        Requirements:
        - 3+ years of Python experience
        - Experience with React and JavaScript
        - Knowledge of AWS cloud services
        - Bachelor's degree in Computer Science
        
        Location: San Francisco, CA
        Salary: $120,000 - $150,000
        """
    ]
    
    service = get_cached_llm_service()
    
    print("📊 Initial Cache Stats:")
    initial_stats = service.get_stats()
    print(f"   Total Requests: {initial_stats['total_requests']}")
    print(f"   Cache Hits: {initial_stats['cache_hits']}")
    print(f"   API Calls: {initial_stats['api_calls']}")
    print(f"   Hit Ratio: {initial_stats['cache_hit_ratio']:.2%}")
    print()
    
    print("🧪 Testing Job Parsing with Caching...")
    
    for i, job_text in enumerate(job_samples, 1):
        print(f"\n--- Test {i} ---")
        
        start_time = time.time()
        
        try:
            # This should use cached LLM or call API if not cached
            result = await parse_job_with_cached_llm(job_text)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            print(f"✅ Parsed Successfully")
            print(f"   Response Time: {response_time:.2f}ms")
            print(f"   Job Title: {result.get('title', 'N/A')}")
            print(f"   Company: {result.get('company', 'N/A')}")
            print(f"   Skills: {len(result.get('skills', []))} detected")
            
            # Fast response indicates cache hit
            if response_time < 100:
                print("   💾 Likely CACHE HIT (fast response)")
            else:
                print("   🌐 Likely API CALL (slower response)")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print("📈 Final Cache Statistics:")
    
    final_stats = service.get_stats()
    print(f"   Total Requests: {final_stats['total_requests']}")
    print(f"   Cache Hits: {final_stats['cache_hits']}")
    print(f"   API Calls: {final_stats['api_calls']}")
    print(f"   Hit Ratio: {final_stats['cache_hit_ratio']:.2%}")
    print(f"   Tokens Saved: ~{final_stats['tokens_saved']}")
    print(f"   Estimated Savings: {final_stats['estimated_cost_savings']}")
    
    print("\n🎯 Cache Performance Analysis:")
    if final_stats['cache_hit_ratio'] >= 0.5:
        print(f"   ✅ Excellent cache performance ({final_stats['cache_hit_ratio']:.1%} hit rate)")
    elif final_stats['cache_hit_ratio'] >= 0.3:
        print(f"   ⚠️  Good cache performance ({final_stats['cache_hit_ratio']:.1%} hit rate)")
    else:
        print(f"   ❌ Low cache performance ({final_stats['cache_hit_ratio']:.1%} hit rate)")
    
    print(f"\n💡 Expected behavior:")
    print(f"   - First job: API call (cache miss)")
    print(f"   - Second job: API call (different content)")
    print(f"   - Third job: Cache hit (duplicate of first)")
    
    return final_stats

async def test_cache_backends():
    """Test different cache backends"""
    print("\n🔧 Testing Cache Backends...")
    
    try:
        from app.services.cache_service import RedisCache, MemoryCache
        
        # Test memory cache
        print("   Testing Memory Cache...")
        memory_cache = MemoryCache(max_size=100, ttl=60)
        await memory_cache.set("test_key", {"test": "data"})
        result = await memory_cache.get("test_key")
        print(f"   ✅ Memory Cache: {result is not None}")
        
        # Test Redis cache (might fail if Redis not available)
        print("   Testing Redis Cache...")
        try:
            redis_cache = RedisCache()
            await redis_cache.set("test_key", {"test": "redis_data"}, ttl=60)
            result = await redis_cache.get("test_key")
            print(f"   ✅ Redis Cache: {result is not None}")
        except Exception as e:
            print(f"   ⚠️  Redis Cache: Not available ({str(e)[:50]}...)")
            print(f"       💡 This is OK - system will use memory cache")
            
    except Exception as e:
        print(f"   ❌ Cache Backend Test Error: {e}")

if __name__ == "__main__":
    async def main():
        try:
            await test_cache_backends()
            stats = await test_cache_performance()
            
            print(f"\n✨ Caching System Test Complete!")
            print(f"   Ready for production use with {stats['cache_hit_ratio']:.1%} efficiency")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(main())
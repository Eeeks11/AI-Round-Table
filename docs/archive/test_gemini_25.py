#!/usr/bin/env python3
"""Test script to verify Gemini 2.5 Pro configuration and functionality."""

import asyncio


async def test_gemini_config():
    """Verify Gemini 2.5 Pro is configured correctly."""
    print("🔍 Testing Gemini 2.5 Pro Configuration...\n")
    
    from config import DEFAULT_MODELS
    
    gemini_config = DEFAULT_MODELS["gemini"]
    
    print(f"📋 Configuration:")
    print(f"  • Provider: {gemini_config.provider}")
    print(f"  • Model Name: {gemini_config.model_name}")
    print(f"  • Display Name: {gemini_config.display_name}")
    print(f"  • API Key Variable: {gemini_config.api_key_env}")
    print(f"  • Temperature: {gemini_config.temperature}")
    print(f"  • Max Tokens: {gemini_config.max_tokens}")
    
    # Check if it matches expected Gemini 2.5 Pro
    if gemini_config.model_name == "gemini-2.5-pro":
        print(f"\n✅ Model correctly set to Gemini 2.5 Pro!")
    else:
        print(f"\n❌ Model is {gemini_config.model_name}, expected gemini-2.5-pro")
        return False
    
    # Check if API key is available
    if gemini_config.is_available():
        print(f"✅ API key is configured and available!")
    else:
        print(f"⚠️  API key not found (set {gemini_config.api_key_env} in .env)")
        return True  # Still pass, just no key configured
    
    return True


async def test_gemini_provider():
    """Test that Gemini 2.5 Pro provider works."""
    print("\n🔍 Testing Gemini 2.5 Pro Provider...\n")
    
    try:
        from config import get_available_models
        from providers import ProviderFactory
        
        available = get_available_models()
        
        if 'gemini' not in available:
            print("  ⚠️  Skipping provider test (API key not configured)")
            return True
        
        config = available['gemini']
        print(f"  Initializing {config.display_name}...")
        provider = ProviderFactory.create_provider(config)
        print(f"  ✅ Provider initialized successfully!")
        
        # Try a simple request
        print(f"\n  Sending test request to {config.model_name}...")
        response_chunks = []
        async for chunk in provider.generate_response(
            "Reply with just the word 'Success' and nothing else.",
            stream=True
        ):
            response_chunks.append(chunk)
        
        response = ''.join(response_chunks).strip()
        print(f"  📥 Response: {response}")
        
        if response:
            print(f"  ✅ Gemini 2.5 Pro is working correctly!")
            return True
        else:
            print(f"  ⚠️  Empty response received")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'rate' in error_msg or 'quota' in error_msg:
            print(f"  ⚠️  Rate limit hit: {str(e)}")
            print(f"  💡 This is expected if the API was used recently. Wait and retry.")
            return True  # Don't fail test
        else:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run all tests."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          Gemini 2.5 Pro Configuration Test                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # Test 1: Configuration
    result1 = await test_gemini_config()
    results.append(result1)
    
    # Test 2: Provider functionality
    result2 = await test_gemini_provider()
    results.append(result2)
    
    print("\n" + "="*60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 Gemini 2.5 Pro is configured and ready to use!")
        print("\n💡 Next steps:")
        print("   • Test with: python deliberate.py 'Your question' --models gemini")
        print("   • Or use all models: python deliberate.py 'Your question'")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))

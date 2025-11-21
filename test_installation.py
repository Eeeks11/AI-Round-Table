#!/usr/bin/env python3
"""
Installation and configuration test script.

This script verifies that:
1. All dependencies are installed
2. Code has no syntax errors
3. Configuration is valid
4. At least one API key is configured
"""

import sys
import importlib


def test_dependencies():
    """Test that all required dependencies are installed."""
    print("🔍 Testing dependencies...")
    
    required_packages = {
        'openai': 'OpenAI API client',
        'anthropic': 'Anthropic API client',
        'google.generativeai': 'Google Generative AI client',
        'dotenv': 'Python dotenv',
        'aiohttp': 'Async HTTP client',
        'colorama': 'Colored terminal output',
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"  ✓ {description} ({package})")
        except ImportError:
            print(f"  ✗ {description} ({package}) - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("  ✅ All dependencies installed\n")
    return True


def test_imports():
    """Test that all project modules can be imported."""
    print("🔍 Testing module imports...")
    
    modules = [
        'config',
        'providers',
        'prompts',
        'consensus',
        'orchestrator',
        'deliberate',
    ]
    
    failed = []
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"  ✓ {module}.py")
        except Exception as e:
            print(f"  ✗ {module}.py - ERROR: {str(e)}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("  ✅ All modules imported successfully\n")
    return True


def test_configuration():
    """Test configuration and API key availability."""
    print("🔍 Testing configuration...")
    
    try:
        from config import get_available_models, DEFAULT_MODELS
        
        print(f"  ✓ Found {len(DEFAULT_MODELS)} configured models")
        
        available = get_available_models()
        
        if not available:
            print("\n  ⚠️  No API keys configured!")
            print("     Create a .env file and add at least one API key:")
            print("     - OPENAI_API_KEY=your_key")
            print("     - ANTHROPIC_API_KEY=your_key")
            print("     - GOOGLE_API_KEY=your_key")
            print("     - GROK_API_KEY=your_key")
            print("\n  ℹ️  Copy .env.example to .env to get started")
            return False
        
        print(f"  ✓ {len(available)} models available:")
        for model_id, config in available.items():
            print(f"    - {config.display_name} ({model_id})")
        
        print("  ✅ Configuration valid\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration error: {str(e)}")
        return False


def test_provider_initialization():
    """Test that providers can be initialized."""
    print("🔍 Testing provider initialization...")
    
    try:
        from config import get_available_models
        from providers import ProviderFactory
        
        available = get_available_models()
        
        if not available:
            print("  ⚠️  Skipping (no API keys configured)")
            return True
        
        for model_id, config in available.items():
            try:
                provider = ProviderFactory.create_provider(config)
                print(f"  ✓ {config.display_name} provider initialized")
            except Exception as e:
                print(f"  ✗ {config.display_name} provider failed: {str(e)}")
                return False
        
        print("  ✅ All providers initialized successfully\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Provider initialization error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        Multi-Model Deliberation - Installation Test          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Provider Initialization", test_provider_initialization),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {str(e)}")
            results.append(False)
    
    print("\n" + "="*60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 System is ready to use!")
        print("\nTry: python deliberate.py --status")
        print("  or: python deliberate.py \"Your question here\"")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above before using the system.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

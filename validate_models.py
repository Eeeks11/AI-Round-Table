#!/usr/bin/env python3
"""
Validation script for models.json configuration file.
Run this to check if your models.json is properly formatted.
"""

import json
import sys
from pathlib import Path


def validate_models_json():
    """Validate the models.json configuration file."""
    print("=" * 60)
    print("Model Configuration Validator")
    print("=" * 60)
    
    config_file = Path(__file__).parent / "models.json"
    
    # Check if file exists
    if not config_file.exists():
        print(f"\n❌ ERROR: models.json not found at {config_file}")
        print("\nPlease create a models.json file with your model configurations.")
        return False
    
    print(f"\n✓ Found models.json at {config_file}")
    
    # Try to load JSON
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✓ Valid JSON syntax")
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON syntax")
        print(f"   {e}")
        return False
    
    # Check structure
    if "models" not in data:
        print("\n❌ ERROR: Missing 'models' key in JSON")
        print("   Your JSON should have a 'models' array at the top level")
        return False
    
    print("✓ Valid JSON structure")
    
    models = data.get("models", [])
    if not models:
        print("\n⚠️  WARNING: No models defined in models.json")
        return True
    
    print(f"\n✓ Found {len(models)} model(s)")
    
    # Validate each model
    required_fields = ["id", "provider", "model_name", "display_name", "api_key_env"]
    valid_providers = ["openai", "anthropic", "google", "grok"]
    
    errors = []
    warnings = []
    
    for i, model in enumerate(models):
        model_id = model.get("id", f"<model #{i+1}>")
        print(f"\n  Validating: {model_id}")
        
        # Check required fields
        for field in required_fields:
            if field not in model:
                errors.append(f"    ❌ Model '{model_id}': Missing required field '{field}'")
            else:
                print(f"    ✓ {field}: {model[field]}")
        
        # Validate provider
        if "provider" in model:
            provider = model["provider"]
            if provider not in valid_providers:
                warnings.append(
                    f"    ⚠️  Model '{model_id}': Unknown provider '{provider}'. "
                    f"Valid providers: {', '.join(valid_providers)}"
                )
        
        # Check optional fields
        optional_fields = {
            "temperature": (float, 0.0, 2.0),
            "max_tokens": (int, 1, 100000),
            "timeout": (int, 1, 600),
            "enabled": (bool, None, None),
        }
        
        for field, (expected_type, min_val, max_val) in optional_fields.items():
            if field in model:
                value = model[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"    ❌ Model '{model_id}': Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                elif min_val is not None and max_val is not None:
                    if not (min_val <= value <= max_val):
                        warnings.append(
                            f"    ⚠️  Model '{model_id}': Field '{field}' value {value} "
                            f"outside recommended range [{min_val}, {max_val}]"
                        )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            print(error)
    
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(warning)
    
    if not errors and not warnings:
        print("\n✅ All checks passed! Your models.json is valid.")
        print("\nConfigured models:")
        for model in models:
            enabled = model.get("enabled", True)
            status = "enabled" if enabled else "disabled"
            print(f"  - {model['id']}: {model['display_name']} ({status})")
    elif not errors:
        print("\n✅ No critical errors found (warnings can be ignored)")
    else:
        print("\n❌ Please fix the errors above")
        return False
    
    print("\n" + "=" * 60)
    print("Next step: Run 'python deliberate.py --status' to check API keys")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = validate_models_json()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

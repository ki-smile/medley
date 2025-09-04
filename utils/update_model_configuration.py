#!/usr/bin/env python
"""
Update MEDLEY to use the new model list (10 free + 24 paid = 34 total)
"""

import json
from pathlib import Path

# New model lists
FREE_MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free", 
    "meta-llama/llama-3.1-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openai/gpt-oss-20b:free",
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free"
]

PAID_MODELS = [
    "anthropic/claude-sonnet-4",
    "openai/gpt-4o",
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-3.5-sonnet-20241022",
    "anthropic/claude-3-opus-20240229",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat",
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku-20240307",
    "google/gemini-2.5-flash",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
    "google/gemini-2.5-flash-lite",
    "qwen/qwen-2.5-coder-32b-instruct",
    "mistralai/mistral-large-2411",
    "anthropic/claude-3.5-haiku-20241022",
    "x-ai/grok-4",
    "cohere/command-r-plus",
    "x-ai/grok-2-1212",
    "openrouter/horizon-beta",
    "perplexity/llama-3.1-sonar-large-128k-online",
    "ai21/jamba-1.5-large",
    "microsoft/wizardlm-2-8x22b"
]

ALL_MODELS = FREE_MODELS + PAID_MODELS

def update_general_pipeline():
    """Update general_medical_pipeline.py to use new model list"""
    pipeline_file = Path("general_medical_pipeline.py")
    
    if not pipeline_file.exists():
        print(f"❌ {pipeline_file} not found")
        return
    
    # Read the file
    content = pipeline_file.read_text()
    
    # Find and replace the model list section
    # This is a simplified approach - in production you'd use AST parsing
    
    # Create a config file instead
    config = {
        "free_models": FREE_MODELS,
        "paid_models": PAID_MODELS,
        "all_models": ALL_MODELS,
        "total_count": len(ALL_MODELS),
        "free_count": len(FREE_MODELS),
        "paid_count": len(PAID_MODELS),
        "best_free_orchestrator": "openai/gpt-oss-20b:free",
        "best_paid_orchestrators": [
            "anthropic/claude-3-opus-20240229",
            "anthropic/claude-3.5-sonnet-20241022",
            "openai/gpt-4o"
        ]
    }
    
    config_file = Path("medley_models_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created {config_file}")
    return config

def create_model_summary():
    """Create a summary of the new model configuration"""
    
    # Count by provider
    providers = {}
    countries = {}
    
    for model in ALL_MODELS:
        # Extract provider
        provider = model.split('/')[0]
        providers[provider] = providers.get(provider, 0) + 1
        
        # Estimate country (simplified)
        if 'anthropic' in provider:
            country = 'USA'
        elif 'openai' in provider:
            country = 'USA'
        elif 'google' in provider:
            country = 'USA'
        elif 'meta' in provider:
            country = 'USA'
        elif 'microsoft' in provider:
            country = 'USA'
        elif 'nvidia' in provider:
            country = 'USA'
        elif 'x-ai' in provider:
            country = 'USA'
        elif 'perplexity' in provider:
            country = 'USA'
        elif 'deepseek' in provider:
            country = 'China'
        elif 'qwen' in provider:
            country = 'China'
        elif 'mistral' in provider:
            country = 'France'
        elif 'cohere' in provider:
            country = 'Canada'
        elif 'ai21' in provider:
            country = 'Israel'
        else:
            country = 'Unknown'
        
        countries[country] = countries.get(country, 0) + 1
    
    summary = f"""
# MEDLEY Model Configuration Update
Generated: {Path(__file__).stat().st_mtime if Path(__file__).exists() else 'Now'}

## Total Models: {len(ALL_MODELS)}
- Free Models: {len(FREE_MODELS)}
- Paid Models: {len(PAID_MODELS)}

## By Provider:
"""
    
    for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
        summary += f"- {provider}: {count} models\n"
    
    summary += "\n## By Country (Estimated):\n"
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(ALL_MODELS)) * 100
        summary += f"- {country}: {count} models ({percentage:.1f}%)\n"
    
    summary += f"""
## Free Models:
{chr(10).join(f'{i+1}. {model}' for i, model in enumerate(FREE_MODELS))}

## Best Orchestrators:
### Free:
1. openai/gpt-oss-20b:free (Best)
2. qwen/qwen-2.5-72b-instruct:free
3. google/gemma-3-27b-it:free

### Paid:
1. anthropic/claude-3-opus-20240229
2. anthropic/claude-3.5-sonnet-20241022
3. openai/gpt-4o
4. google/gemini-2.5-pro

## New/Notable Models:
- anthropic/claude-sonnet-4 (New Claude 4)
- anthropic/claude-3.7-sonnet (Latest 3.x)
- nvidia/llama-3.1-nemotron-70b-instruct:free (NVIDIA's Llama)
- perplexity/llama-3.1-sonar-large-128k-online (Online search capable)
- ai21/jamba-1.5-large (Israeli model)
"""
    
    # Save summary
    summary_file = Path("MODEL_CONFIGURATION_SUMMARY.md")
    summary_file.write_text(summary)
    print(f"✅ Created {summary_file}")
    
    return summary

def main():
    print("🔧 Updating MEDLEY Model Configuration")
    print("=" * 60)
    print(f"Total models: {len(ALL_MODELS)} ({len(FREE_MODELS)} free + {len(PAID_MODELS)} paid)")
    
    # Create configuration file
    config = update_general_pipeline()
    
    # Create summary
    summary = create_model_summary()
    
    print("\n📊 Model Distribution:")
    print(f"  Free models: {len(FREE_MODELS)}")
    print(f"  Paid models: {len(PAID_MODELS)}")
    
    # Show provider breakdown
    providers = {}
    for model in ALL_MODELS:
        provider = model.split('/')[0]
        providers[provider] = providers.get(provider, 0) + 1
    
    print("\n🏢 By Provider:")
    for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {provider}: {count} models")
    
    print("\n✅ Configuration updated successfully!")
    print("📄 Files created:")
    print("  - medley_models_config.json")
    print("  - MODEL_CONFIGURATION_SUMMARY.md")
    
    print("\n🎯 Next Steps:")
    print("  1. Update general_medical_pipeline.py to load from medley_models_config.json")
    print("  2. Clear old cache if needed")
    print("  3. Run new analysis with updated model list")

if __name__ == "__main__":
    main()
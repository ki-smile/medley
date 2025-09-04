#!/usr/bin/env python
"""
Query missing models from the 34 model list for Case 13
"""

import json
import requests
import time
import os
from pathlib import Path
from datetime import datetime

# Load the 34 model list
from model_list_2025_updated import ALL_MODELS

# Set up paths
cache_dir = Path("cache/responses/Case_13")
cache_dir.mkdir(parents=True, exist_ok=True)
case_file = Path("usecases/case_013_complex_urology.txt")

# Load case content
case_content = case_file.read_text()

# Create medical prompt
prompt = f"""You are an expert physician. Analyze this medical case and provide a comprehensive assessment in JSON format.

{case_content}

Provide your response ONLY as a valid JSON object with this structure:
{{
    "primary_diagnosis": {{
        "name": "diagnosis name",
        "confidence": 0.0-1.0,
        "icd_code": "ICD-10 code",
        "reasoning": "detailed clinical reasoning"
    }},
    "differential_diagnoses": [
        {{
            "name": "diagnosis name",
            "confidence": 0.0-1.0,
            "icd_code": "ICD-10 code",
            "reasoning": "clinical reasoning"
        }}
    ],
    "key_findings": ["finding 1", "finding 2"],
    "diagnostic_tests": [
        {{
            "test": "test name",
            "purpose": "why needed",
            "priority": "immediate/urgent/routine"
        }}
    ],
    "management_plan": {{
        "immediate_actions": ["action 1", "action 2"],
        "medications": [
            {{
                "drug": "drug name",
                "dose": "dosage",
                "route": "route",
                "duration": "duration",
                "rationale": "why prescribed"
            }}
        ],
        "monitoring": ["parameter 1", "parameter 2"],
        "consultations": [
            {{
                "specialty": "specialty name",
                "urgency": "immediate/urgent/routine",
                "reason": "consultation reason"
            }}
        ]
    }},
    "red_flags": ["red flag 1", "red flag 2"],
    "patient_education": ["education point 1", "education point 2"],
    "follow_up": {{
        "timing": "when to follow up",
        "conditions": "conditions requiring earlier return"
    }},
    "confidence_in_assessment": 0.0-1.0,
    "uncertainties": ["uncertainty 1", "uncertainty 2"]
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""

def get_cached_models():
    """Get list of already cached models"""
    cached = set()
    for cache_file in cache_dir.glob("*.json"):
        # Handle different naming conventions
        filename = cache_file.stem
        # Convert back to model name format
        model_name = filename.replace('_', '/')
        # Add both with and without :free suffix
        cached.add(model_name)
        cached.add(model_name + ":free")
        cached.add(model_name.replace(":free", ""))
    return cached

def query_model(model_name):
    """Query a model via OpenRouter API"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Cache the response
            cache_data = {
                "model": model_name,
                "content": content,
                "response_time": time.time(),
                "cached": False,
                "case_id": "Case_13",
                "timestamp": datetime.now().isoformat(),
                "tokens_used": result.get('usage', {}).get('total_tokens', 0),
                "from_34_list": True
            }
            
            # Save to cache
            safe_model_name = model_name.replace('/', '_').replace(':', '_')
            cache_file = cache_dir / f"{safe_model_name}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return True
        else:
            error = response.json().get('error', {}).get('message', f'Status {response.status_code}')
            print(f"   ❌ API error: {error[:80]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:80]}")
        return False

def main():
    print("🔍 Querying missing models from 34-model list for Case 13")
    print("=" * 60)
    
    # Get already cached models
    cached = get_cached_models()
    print(f"📁 Found {len(cached)} cached model variations")
    
    # Find missing models
    missing = []
    for model in ALL_MODELS:
        # Check various naming patterns
        base_name = model.replace(':free', '')
        if model not in cached and base_name not in cached:
            missing.append(model)
    
    print(f"🔍 Need to query {len(missing)} models from the 34-model list")
    
    if missing:
        print("\n📝 Missing models:")
        for i, model in enumerate(missing[:10], 1):  # Show first 10
            print(f"   {i}. {model}")
        if len(missing) > 10:
            print(f"   ... and {len(missing)-10} more")
    
    # Query missing models
    success = 0
    failed = 0
    
    for i, model in enumerate(missing, 1):
        print(f"\n[{i}/{len(missing)}] Querying {model}...")
        
        if query_model(model):
            print(f"   ✅ Success")
            success += 1
            time.sleep(1)  # Rate limiting
        else:
            failed += 1
        
        # Stop after a reasonable number to avoid timeout
        if i >= 10 and success >= 5:
            print("\n⚠️  Stopping after 10 attempts to avoid timeout")
            print("   Run again to continue with remaining models")
            break
    
    # Final count
    total_cached = len(list(cache_dir.glob("*.json")))
    print(f"\n📊 Results:")
    print(f"   ✅ Successfully added: {success}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total cached: {total_cached}")
    print(f"   🎯 Target: 34 models")
    
    if total_cached >= 30:
        print("\n✨ Sufficient models cached for comprehensive analysis!")
        print("   Ready to regenerate Case 13 report")

if __name__ == "__main__":
    main()
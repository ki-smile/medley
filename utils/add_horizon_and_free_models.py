#!/usr/bin/env python
"""
Add Horizon Beta and other free models to Case 13
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
import os

# Set up paths
cache_dir = Path("cache/responses/Case_13")
cache_dir.mkdir(parents=True, exist_ok=True)
case_file = Path("usecases/case_013_complex_urology.txt")

# Load case content
case_content = case_file.read_text()

# Create the medical prompt (ensure it's unbiased)
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

IMPORTANT: Return ONLY the JSON object, no additional text. Base your diagnosis solely on the clinical findings provided."""

def query_model(model_name):
    """Query a model via OpenRouter API"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print(f"❌ No API key found")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    try:
        print(f"   Querying {model_name}...")
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
                "unbiased": True  # Mark as unbiased query
            }
            
            # Save to cache
            safe_model_name = model_name.replace('/', '_').replace(':', '_')
            cache_file = cache_dir / f"{safe_model_name}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"   ✅ Saved {model_name}")
            return content
        else:
            error_msg = response.json().get('error', {}).get('message', f'Status {response.status_code}')
            print(f"   ❌ {model_name}: {error_msg[:80]}")
            return None
            
    except Exception as e:
        print(f"   ❌ {model_name}: {str(e)[:80]}")
        return None

def main():
    """Add Horizon Beta and other free models"""
    print("🔍 Adding Horizon Beta and additional free models for Case 13")
    print("=" * 60)
    
    # Free models to add
    free_models = [
        "openrouter/horizon-beta",  # New free model requested
        "google/gemma-3-27b-it:free",  # Google's free model
        "google/gemma-3-4b-it:free",   # Smaller Gemma
        "openai/gpt-oss-20b:free",     # OpenAI free model
        "liquid/lfm-40b:free",          # Liquid's free model
        "meta-llama/llama-3.2-1b-instruct:free",  # Small Llama free
        "mistralai/mistral-7b-instruct:free",     # Mistral free
        "qwen/qwen-2.5-72b-instruct:free",        # Qwen free
        "microsoft/phi-3-mini-128k-instruct:free", # Microsoft Phi free
        "nousresearch/hermes-3-llama-3.1-8b:free", # Nous Research free
    ]
    
    # Check which models are already cached
    existing_files = {f.stem for f in cache_dir.glob("*.json")}
    
    success_count = 0
    failed_count = 0
    
    for model in free_models:
        safe_name = model.replace('/', '_').replace(':', '_')
        
        if safe_name in existing_files:
            print(f"⏭️  {model}: Already cached")
            continue
        
        response = query_model(model)
        
        if response:
            success_count += 1
            time.sleep(1)  # Rate limiting for free tier
        else:
            failed_count += 1
    
    # Count total cached models
    total_cached = len(list(cache_dir.glob("*.json")))
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successfully added: {success_count} models")
    print(f"   ❌ Failed: {failed_count} models")
    print(f"   📁 Total cached models: {total_cached}")
    
    if success_count > 0:
        print("\n🎯 Next steps:")
        print("   1. Run: python regenerate_case_13_fixed.py")
        print("   2. This will create a new report with all models")
        print("   3. The consensus will be more robust with additional models")

if __name__ == "__main__":
    main()
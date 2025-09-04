#!/usr/bin/env python
"""
Add missing model responses for Case 13
"""

import json
import time
from pathlib import Path
from datetime import datetime
import os

# Set up paths
cache_dir = Path("cache/responses/Case_13")
case_file = Path("usecases/case_013_complex_urology.txt")

# Load case content
case_content = case_file.read_text()

# Create the medical prompt
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

def query_model_direct(model_name, prompt):
    """Query a model directly using OpenRouter API"""
    import requests
    
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
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }
            
            # Save to cache
            safe_model_name = model_name.replace('/', '_')
            cache_file = cache_dir / f"{safe_model_name}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"✅ {model_name}: Saved to cache")
            return content
        else:
            print(f"❌ {model_name}: API error {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:100]}")
        return None

def main():
    """Add missing model responses"""
    print("🔍 Adding missing model responses for Case 13")
    print("=" * 60)
    
    # Models to add
    missing_models = [
        "anthropic/claude-3.5-sonnet-20241022",  # Latest Claude Sonnet
        "openai/gpt-4-turbo",  # GPT-4 Turbo
        "meta-llama/llama-3.1-70b-instruct",  # Llama 3.1 70B
        "mistralai/mistral-medium",  # Mistral Medium
        "google/gemini-pro",  # Gemini Pro
    ]
    
    # Check which models are already cached
    existing_files = [f.stem for f in cache_dir.glob("*.json")]
    
    success_count = 0
    for model in missing_models:
        safe_name = model.replace('/', '_')
        
        if safe_name in existing_files:
            print(f"⏭️  {model}: Already cached")
            continue
        
        print(f"\n🔄 Querying {model}...")
        response = query_model_direct(model, prompt)
        
        if response:
            success_count += 1
            time.sleep(2)  # Rate limiting
    
    # Count total cached models
    total_cached = len(list(cache_dir.glob("*.json")))
    print(f"\n✅ Added {success_count} new models")
    print(f"📊 Total cached models: {total_cached}")

if __name__ == "__main__":
    main()
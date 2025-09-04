#!/usr/bin/env python3
"""Quick test of free models as orchestrators"""

from web_orchestrator import WebOrchestrator
import time

# Free models to test
FREE_MODELS = [
    'google/gemini-2.0-flash-exp:free',
    'meta-llama/llama-3.1-70b-instruct:free',
    'deepseek/deepseek-chat',
    'qwen/qwq-32b-preview',
]

# Mock responses to test consensus building
mock_responses = [
    {"model_name": "test1", "response": "The diagnosis is McArdle disease"},
    {"model_name": "test2", "response": "Glycogen storage disease type V"},
    {"model_name": "test3", "response": "Muscle phosphorylase deficiency"},
]

print("Testing Free Models as Orchestrators")
print("=" * 50)

for model in FREE_MODELS:
    print(f"\nTesting: {model}")
    print("-" * 30)
    
    try:
        # Initialize orchestrator with free model
        orch = WebOrchestrator(api_key="test", orchestrator_model=model)
        
        # Test 1: Extract diagnoses
        start = time.time()
        diagnoses = orch.extract_diagnoses(mock_responses)
        t1 = time.time() - start
        
        if diagnoses:
            print(f"✅ Extract diagnoses: {t1:.1f}s - Found {len(diagnoses)} diagnoses")
        else:
            print(f"❌ Extract diagnoses failed")
            continue
            
        # Test 2: Build consensus
        start = time.time()
        consensus = orch.build_consensus(diagnoses, mock_responses)
        t2 = time.time() - start
        
        if consensus and 'primary_diagnosis' in consensus:
            print(f"✅ Build consensus: {t2:.1f}s - {consensus['primary_diagnosis'].get('name', 'Unknown')}")
        else:
            print(f"❌ Build consensus failed")
            continue
            
        print(f"✅ {model} WORKS as orchestrator!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

print("\n" + "=" * 50)
print("Test Complete")
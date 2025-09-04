#!/usr/bin/env python
"""
Basic usage example for MEDLEY Medical AI Ensemble System
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_single_case():
    """Example: Run analysis for a single medical case"""
    
    # Import the pipeline
    from general_medical_pipeline import run_pipeline
    
    # Define case parameters
    case_id = "Case_1"
    case_file = "usecases/case_001_fmf.txt"
    
    print(f"Running analysis for {case_id}...")
    
    # Run the pipeline
    success = run_pipeline(case_id, case_file)
    
    if success:
        print(f"✅ Analysis complete!")
        print(f"📄 Report saved to: reports/FINAL_{case_id}_comprehensive_*.pdf")
    else:
        print(f"❌ Analysis failed")
    
    return success

def run_multiple_cases():
    """Example: Run analysis for multiple cases"""
    
    cases = [
        ("Case_1", "usecases/case_001_fmf.txt"),
        ("Case_2", "usecases/case_002_elderly.txt"),
        ("Case_3", "usecases/case_003_homeless.txt"),
    ]
    
    results = []
    
    for case_id, case_file in cases:
        print(f"\n{'='*50}")
        print(f"Processing {case_id}")
        print('='*50)
        
        success = run_pipeline(case_id, case_file)
        results.append((case_id, success))
    
    # Summary
    print("\n📊 Summary:")
    for case_id, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {case_id}")

def check_model_responses():
    """Example: Check which models responded for a case"""
    
    import json
    from pathlib import Path
    
    cache_dir = Path("cache/responses/Case_1")
    
    if not cache_dir.exists():
        print("No cache found. Run analysis first.")
        return
    
    models = []
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file) as f:
                data = json.load(f)
                if data.get('content'):
                    models.append(data.get('model_name', cache_file.stem))
        except:
            pass
    
    print(f"📊 Models that responded: {len(models)}")
    for model in sorted(models):
        print(f"  • {model}")

def view_consensus():
    """Example: View consensus analysis from ensemble data"""
    
    import json
    from pathlib import Path
    
    # Find the latest ensemble data file
    reports_dir = Path("reports")
    ensemble_files = sorted(reports_dir.glob("Case_1_ensemble_data_*.json"))
    
    if not ensemble_files:
        print("No ensemble data found. Run analysis first.")
        return
    
    latest_file = ensemble_files[-1]
    
    with open(latest_file) as f:
        data = json.load(f)
    
    # Extract consensus information
    diagnostic = data.get('diagnostic_landscape', {})
    primary = diagnostic.get('primary_diagnosis', {})
    
    print("🏥 Primary Diagnosis Analysis:")
    print(f"  Diagnosis: {primary.get('name', 'Unknown')}")
    print(f"  Consensus: {primary.get('agreement_percentage', 0):.1f}%")
    print(f"  ICD-10: {primary.get('icd10_code', 'N/A')}")
    print(f"  Confidence: {primary.get('confidence', 'Unknown')}")
    
    # Show alternatives
    alternatives = diagnostic.get('strong_alternatives', [])
    if alternatives:
        print("\n🔄 Alternative Diagnoses:")
        for alt in alternatives[:3]:
            print(f"  • {alt.get('name')}: {alt.get('agreement_percentage', 0):.1f}%")

if __name__ == "__main__":
    print("MEDLEY Usage Examples")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Please set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    # Run examples
    print("\n1. Running single case analysis...")
    run_single_case()
    
    print("\n2. Checking model responses...")
    check_model_responses()
    
    print("\n3. Viewing consensus analysis...")
    view_consensus()
    
    print("\n✅ Examples complete!")
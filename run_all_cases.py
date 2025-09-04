#!/usr/bin/env python
"""
Run pipeline for all medical cases with cache cleanup
"""

import subprocess
import sys
import time
from pathlib import Path
import json

def clear_invalid_cache():
    """Clear invalid or empty cache files"""
    cache_dir = Path("cache/responses")
    if not cache_dir.exists():
        return
    
    invalid_count = 0
    for case_dir in cache_dir.iterdir():
        if not case_dir.is_dir():
            continue
            
        for cache_file in case_dir.glob("*.json"):
            try:
                # Check file size
                if cache_file.stat().st_size < 1024:  # Less than 1KB
                    print(f"  🗑️  Removing small cache file: {cache_file.name}")
                    cache_file.unlink()
                    invalid_count += 1
                    continue
                
                # Check content validity
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    content = data.get('content', '')
                    if len(content) < 50:
                        print(f"  🗑️  Removing empty content cache: {cache_file.name}")
                        cache_file.unlink()
                        invalid_count += 1
            except:
                print(f"  🗑️  Removing corrupted cache: {cache_file.name}")
                cache_file.unlink()
                invalid_count += 1
    
    print(f"✅ Cleared {invalid_count} invalid cache files\n")

def run_case(case_num, case_file):
    """Run pipeline for a single case"""
    case_id = f"Case_{case_num}"
    print(f"\n{'='*80}")
    print(f"🚀 Running pipeline for {case_id}")
    print(f"{'='*80}")
    
    cmd = [
        sys.executable,
        "general_medical_pipeline.py",
        case_id,
        case_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Check if successful
        if "ANALYSIS COMPLETE" in result.stdout:
            print(f"✅ {case_id} completed successfully")
            
            # Extract key metrics
            lines = result.stdout.split('\n')
            for line in lines:
                if "Models Analyzed:" in line:
                    print(f"   {line.strip()}")
                if "Primary Diagnosis:" in line:
                    print(f"   {line.strip()}")
                if "Success Rate:" in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ {case_id} failed")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {case_id} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ {case_id} error: {e}")
        return False

def main():
    """Main execution"""
    print("🧹 STEP 1: Clearing invalid cache files...")
    clear_invalid_cache()
    
    print("📊 STEP 2: Running pipelines for all cases...")
    
    # Define all cases
    cases = [
        (1, "usecases/case_001_fmf.txt"),
        (2, "usecases/case_002_elderly.txt"),
        (3, "usecases/case_003_homeless.txt"),
        (4, "usecases/case_004_rare_genetic.txt"),
        (5, "usecases/case_005_environmental.txt"),
        (6, "usecases/case_006_disability_communication.txt"),
        (7, "usecases/case_007_gender_identity.txt"),
        (8, "usecases/case_008_rural_healthcare.txt"),
        (9, "usecases/case_009_weight_bias.txt"),
        (10, "usecases/case_010_migration_trauma.txt"),
        (11, "usecases/case_011_ethnic_medication.txt"),
    ]
    
    successful = []
    failed = []
    
    for case_num, case_file in cases:
        if run_case(case_num, case_file):
            successful.append(case_num)
        else:
            failed.append(case_num)
        
        # Brief pause between cases
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*80}")
    print("📈 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {len(successful)} cases - {successful}")
    print(f"❌ Failed: {len(failed)} cases - {failed}")
    
    # List generated reports
    reports_dir = Path("reports")
    recent_reports = sorted(reports_dir.glob("FINAL_Case_*_comprehensive_*.pdf"))[-11:]
    
    if recent_reports:
        print(f"\n📄 Generated Reports:")
        for report in recent_reports:
            size_kb = report.stat().st_size / 1024
            print(f"   • {report.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
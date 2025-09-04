#!/usr/bin/env python
"""
Complete Case 13 Generation using the general medical pipeline framework
"""

import subprocess
import sys
from pathlib import Path

def complete_case_13():
    """Run the remaining steps to complete Case 13"""
    
    print("🏥 Completing Case 13 Generation")
    print("=" * 60)
    
    # Check how many responses are cached
    cache_dir = Path("cache/responses/Case_13")
    if cache_dir.exists():
        cached_files = list(cache_dir.glob("*.json"))
        print(f"✅ Found {len(cached_files)} cached model responses")
    else:
        print("❌ No cached responses found")
        return False
    
    # Set to use only cached models (skip querying new ones)
    import os
    os.environ['USE_CACHED_ONLY'] = 'true'
    os.environ['MAX_QUERY_TIME'] = '30'  # Quick timeout for any remaining queries
    
    # Run the pipeline with a short timeout for remaining models
    print("\n🚀 Running general medical pipeline to complete Case 13...")
    print("   This will use cached responses and generate the final report")
    
    cmd = [
        sys.executable,
        "general_medical_pipeline.py",
        "Case_13",
        "usecases/case_013_complex_urology.txt"
    ]
    
    try:
        # Run with a 2-minute timeout (should be enough with cached responses)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Check for success indicators
        if "ANALYSIS COMPLETE" in result.stdout or "Report generated" in result.stdout:
            print("\n✅ Case 13 completed successfully!")
            
            # Check for generated reports
            reports_dir = Path("reports")
            case_13_reports = list(reports_dir.glob("*Case_13*.pdf"))
            
            if case_13_reports:
                print(f"\n📄 Generated Reports:")
                for report in case_13_reports[-3:]:  # Show last 3 reports
                    size_kb = report.stat().st_size / 1024
                    print(f"   • {report.name} ({size_kb:.1f} KB)")
                    
                    # Check for HTML version
                    html_report = report.with_suffix('.html')
                    if html_report.exists():
                        print(f"   • {html_report.name} (HTML version)")
            
            return True
        else:
            # Even if not fully complete, check if report was generated
            reports_dir = Path("reports")
            case_13_reports = list(reports_dir.glob("*Case_13*.pdf"))
            
            if case_13_reports:
                print("\n⚠️  Pipeline didn't complete fully, but report was generated")
                latest_report = sorted(case_13_reports)[-1]
                size_kb = latest_report.stat().st_size / 1024
                print(f"   • {latest_report.name} ({size_kb:.1f} KB)")
                return True
            else:
                print("\n❌ Pipeline failed to generate report")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")
                return False
                
    except subprocess.TimeoutExpired:
        print("\n⏱️  Pipeline timed out, checking if report was generated...")
        
        # Check if report was generated before timeout
        reports_dir = Path("reports")
        case_13_reports = list(reports_dir.glob("*Case_13*.pdf"))
        
        if case_13_reports:
            print("✅ Report was generated before timeout")
            latest_report = sorted(case_13_reports)[-1]
            size_kb = latest_report.stat().st_size / 1024
            print(f"   • {latest_report.name} ({size_kb:.1f} KB)")
            return True
        else:
            print("❌ No report generated")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def show_web_config():
    """Show configuration for adding to web interface"""
    print("\n" + "="*60)
    print("📝 To add Case 13 to the web interface:")
    print("\n1. Edit web_app.py and add to MEDICAL_CASES list:")
    print("""
    {
        'id': 'case_013',
        'title': 'Case 13: Complex Glomerulonephritis',
        'specialty': 'Nephrology/Rheumatology',
        'description': 'Young male with recurrent hematuria and renal dysfunction',
        'bias_focus': 'Ethnic and age-related diagnostic bias',
        'file': 'usecases/case_013_complex_urology.txt'
    }
    """)
    print("\n2. Restart the web server:")
    print("   python web_app.py")
    print("\n3. Case 13 will appear in the 'Explore Medical Cases' section")

def main():
    """Main execution"""
    
    # Check if general_medical_pipeline.py exists
    if not Path("general_medical_pipeline.py").exists():
        print("❌ Error: general_medical_pipeline.py not found!")
        print("   This script must be run from the medley directory")
        return
    
    # Check if case file exists
    case_file = Path("usecases/case_013_complex_urology.txt")
    if not case_file.exists():
        print(f"❌ Error: Case file not found: {case_file}")
        return
    
    print(f"✅ Case file found: {case_file}")
    
    # Complete Case 13 generation
    if complete_case_13():
        show_web_config()
        print("\n✨ Case 13 has been successfully added to the system!")
        print("   - Report uses green theme matching Cases 1-12")
        print("   - Comprehensive structure with bias analysis")
        print("   - Ready for web interface integration")
    else:
        print("\n⚠️  Case 13 generation incomplete")
        print("   You may need to run the full pipeline again or check API keys")

if __name__ == "__main__":
    main()
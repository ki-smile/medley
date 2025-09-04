#!/usr/bin/env python
"""
Generate Case 13 using the same pipeline as Cases 1-12
This ensures consistent structure, theme, and output format
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import shutil

def create_case_13_file():
    """Create a new medical case file for Case 13"""
    case_content = """A 45-year-old woman presents to the emergency department with severe chest pain and shortness of breath. 
The pain started suddenly 2 hours ago while she was at rest. She describes it as sharp, worsening with deep breaths, 
and radiating to her left shoulder. Past medical history includes recent long-haul flight from Australia (20 hours ago), 
oral contraceptive use, and a family history of blood clotting disorders. She appears anxious and tachypneic.
Vital signs: BP 110/70, HR 110, RR 28, O2 sat 92% on room air. Physical exam reveals diminished breath sounds 
on the left side and mild lower extremity edema. D-dimer is elevated at 2500 ng/mL."""
    
    # Save to usecases directory
    case_file = Path("usecases/case_013_pulmonary_embolism.txt")
    case_file.write_text(case_content)
    print(f"✅ Created case file: {case_file}")
    return str(case_file)

def run_pipeline_for_case_13():
    """Run the general medical pipeline for Case 13"""
    
    # Create the case file
    case_file = create_case_13_file()
    
    # Run the pipeline using the same command as run_all_cases.py
    case_id = "Case_13"
    
    print(f"\n{'='*80}")
    print(f"🚀 Running pipeline for {case_id}")
    print(f"   Using the same pipeline as Cases 1-12")
    print(f"   This will generate reports with green theme and consistent structure")
    print(f"{'='*80}\n")
    
    cmd = [
        sys.executable,
        "general_medical_pipeline.py",
        case_id,
        case_file
    ]
    
    try:
        # Run the pipeline
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ {case_id} completed successfully!")
            
            # List generated reports
            reports_dir = Path("reports")
            case_13_reports = sorted(reports_dir.glob("*Case_13*.pdf"))
            
            if case_13_reports:
                print(f"\n📄 Generated Reports for Case 13:")
                for report in case_13_reports:
                    size_kb = report.stat().st_size / 1024
                    print(f"   • {report.name} ({size_kb:.1f} KB)")
                    
                    # Also check for HTML version
                    html_report = report.with_suffix('.html')
                    if html_report.exists():
                        print(f"   • {html_report.name} (HTML version)")
            
            # Show cache location
            cache_dir = Path("cache/responses/Case_13")
            if cache_dir.exists():
                cache_files = list(cache_dir.glob("*.json"))
                print(f"\n💾 Cached responses: {len(cache_files)} models")
            
            return True
        else:
            print(f"❌ {case_id} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return False

def update_web_interface_cases():
    """Update the web interface to include Case 13"""
    web_app_file = Path("web_app.py")
    
    print("\n📝 To add Case 13 to the web interface:")
    print("   1. The case file has been created in usecases/")
    print("   2. The reports have been generated in reports/")
    print("   3. Update web_app.py MEDICAL_CASES list to include Case 13")
    print("   4. Restart the web server to see the new case")
    
    print("\nAdd this to MEDICAL_CASES in web_app.py:")
    print("""
    {
        'id': 'case_013',
        'title': 'Case 13: Pulmonary Embolism Risk',
        'specialty': 'Emergency Medicine',
        'description': 'Post-flight chest pain with risk factors',
        'bias_focus': 'Gender and contraceptive bias',
        'file': 'usecases/case_013_pulmonary_embolism.txt'
    }
    """)

def main():
    """Main execution"""
    print("🏥 MEDLEY Case 13 Generator")
    print("=" * 60)
    print("This script generates Case 13 using the EXACT same pipeline")
    print("as Cases 1-12, ensuring consistent output format and theme.")
    print("=" * 60)
    
    # Check if general_medical_pipeline.py exists
    if not Path("general_medical_pipeline.py").exists():
        print("❌ Error: general_medical_pipeline.py not found!")
        print("   This script must be run from the medley directory")
        return
    
    # Run the pipeline
    success = run_pipeline_for_case_13()
    
    if success:
        update_web_interface_cases()
        print("\n✨ Case 13 has been successfully generated!")
        print("   - Reports use the same green theme as Cases 1-12")
        print("   - Structure matches existing comprehensive reports")
        print("   - Ready to be added to the web interface")
    else:
        print("\n❌ Failed to generate Case 13")

if __name__ == "__main__":
    main()
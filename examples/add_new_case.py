#!/usr/bin/env python
"""
General Pipeline for Adding New Medical Cases to MEDLEY
This script ensures consistent generation of reports matching Cases 1-12 format
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import argparse

class NewCaseGenerator:
    """Generate new medical cases with consistent pipeline"""
    
    def __init__(self, case_number: int, case_file: str, case_title: str = None):
        """
        Initialize new case generator
        
        Args:
            case_number: Case number (e.g., 13 for Case_13)
            case_file: Path to the case file in usecases/
            case_title: Optional title for the case
        """
        self.case_number = case_number
        self.case_id = f"Case_{case_number}"
        self.case_file = Path(case_file)
        self.case_title = case_title or f"Case {case_number}"
        
        # Verify case file exists
        if not self.case_file.exists():
            raise FileNotFoundError(f"Case file not found: {self.case_file}")
            
        print(f"🏥 MEDLEY New Case Generator - {self.case_id}")
        print("=" * 60)
        
    def run_pipeline(self, use_paid_models: bool = False):
        """
        Run the general medical pipeline for the new case
        
        Args:
            use_paid_models: If True, uses premium models for better quality
        """
        print(f"\n🚀 Running pipeline for {self.case_id}")
        print(f"   Case file: {self.case_file}")
        print(f"   Model type: {'Premium' if use_paid_models else 'Free'}")
        print(f"   Using same pipeline as Cases 1-12 for consistency")
        print("=" * 60)
        
        # Set environment variable for model selection
        import os
        if not use_paid_models:
            os.environ['USE_FREE_MODELS'] = 'true'
        
        cmd = [
            sys.executable,
            "general_medical_pipeline.py",
            self.case_id,
            str(self.case_file)
        ]
        
        try:
            # Run the pipeline
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print(f"\n✅ {self.case_id} completed successfully!")
                self._show_generated_reports()
                self._show_cache_info()
                return True
            else:
                print(f"❌ {self.case_id} failed with return code {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ Error running pipeline: {e}")
            return False
    
    def _show_generated_reports(self):
        """Display information about generated reports"""
        reports_dir = Path("reports")
        
        # Find all reports for this case
        pdf_reports = sorted(reports_dir.glob(f"*{self.case_id}*.pdf"))
        html_reports = sorted(reports_dir.glob(f"*{self.case_id}*.html"))
        
        if pdf_reports or html_reports:
            print(f"\n📄 Generated Reports for {self.case_id}:")
            
            for report in pdf_reports:
                size_kb = report.stat().st_size / 1024
                print(f"   • PDF: {report.name} ({size_kb:.1f} KB)")
                
            for report in html_reports:
                size_kb = report.stat().st_size / 1024
                print(f"   • HTML: {report.name} ({size_kb:.1f} KB)")
    
    def _show_cache_info(self):
        """Display cache information"""
        cache_dir = Path("cache/responses") / self.case_id
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.json"))
            print(f"\n💾 Cached responses: {len(cache_files)} models")
    
    def generate_web_config(self, specialty: str, description: str, bias_focus: str):
        """
        Generate configuration for adding case to web interface
        
        Args:
            specialty: Medical specialty (e.g., "Nephrology/Rheumatology")
            description: Brief case description
            bias_focus: Bias consideration for this case
        """
        config = {
            'id': f'case_{self.case_number:03d}',
            'title': self.case_title,
            'specialty': specialty,
            'description': description,
            'bias_focus': bias_focus,
            'file': str(self.case_file)
        }
        
        print("\n📝 To add this case to the web interface:")
        print("   Add the following to MEDICAL_CASES in web_app.py:")
        print("\n" + json.dumps(config, indent=4))
        
        # Save config to file for reference
        config_file = Path(f"case_{self.case_number:03d}_config.json")
        config_file.write_text(json.dumps(config, indent=4))
        print(f"\n   Configuration saved to: {config_file}")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Generate new medical cases for MEDLEY with consistent formatting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Case 13 with free models
  python add_new_case.py 13 usecases/case_013_complex_urology.txt
  
  # Generate Case 14 with premium models
  python add_new_case.py 14 usecases/case_014_cardiology.txt --paid
  
  # Generate with full metadata for web interface
  python add_new_case.py 13 usecases/case_013_complex_urology.txt \\
    --title "Case 13: Complex Glomerulonephritis" \\
    --specialty "Nephrology/Rheumatology" \\
    --description "Young male with recurrent hematuria and renal dysfunction" \\
    --bias "Ethnic and age-related diagnostic bias"
        """
    )
    
    parser.add_argument('case_number', type=int, 
                       help='Case number (e.g., 13 for Case_13)')
    parser.add_argument('case_file', 
                       help='Path to case file in usecases/ directory')
    parser.add_argument('--title', 
                       help='Case title for web interface')
    parser.add_argument('--specialty', 
                       help='Medical specialty')
    parser.add_argument('--description', 
                       help='Brief case description')
    parser.add_argument('--bias', 
                       help='Bias focus for this case')
    parser.add_argument('--paid', action='store_true',
                       help='Use premium models instead of free')
    
    args = parser.parse_args()
    
    # Check if general_medical_pipeline.py exists
    if not Path("general_medical_pipeline.py").exists():
        print("❌ Error: general_medical_pipeline.py not found!")
        print("   This script must be run from the medley directory")
        return
    
    # Create generator
    generator = NewCaseGenerator(
        case_number=args.case_number,
        case_file=args.case_file,
        case_title=args.title
    )
    
    # Run pipeline
    success = generator.run_pipeline(use_paid_models=args.paid)
    
    if success:
        # Generate web config if metadata provided
        if args.specialty and args.description and args.bias:
            generator.generate_web_config(
                specialty=args.specialty,
                description=args.description,
                bias_focus=args.bias
            )
        
        print("\n✨ New case has been successfully generated!")
        print("   - Reports use the same green theme as Cases 1-12")
        print("   - Structure matches existing comprehensive reports")
        print("   - Ready to be added to the web interface")
    else:
        print("\n❌ Failed to generate new case")

if __name__ == "__main__":
    main()
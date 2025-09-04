#!/usr/bin/env python
"""
Generate the final comprehensive report with all content
Uses existing ensemble data to create the complete report
"""

import json
from pathlib import Path
from datetime import datetime
import sys

from src.medley.reporters.final_comprehensive_report import FinalComprehensiveReportGenerator

def main():
    """Generate final comprehensive report"""
    
    print("=" * 70)
    print("Generating Final Comprehensive Report")
    print("=" * 70)
    
    # Find the best ensemble file to use
    ensemble_files = list(Path("reports").glob("*ensemble*.json"))
    
    if not ensemble_files:
        print("❌ No ensemble files found!")
        sys.exit(1)
    
    # Sort by modification time to get the most recent
    ensemble_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Use the most recent file
    ensemble_file = ensemble_files[0]
    
    print(f"\n📄 Using ensemble data from: {ensemble_file}")
    
    with open(ensemble_file, 'r') as f:
        ensemble_results = json.load(f)
    
    # Display statistics
    print(f"\n📊 Ensemble Statistics:")
    print(f"   Case: {ensemble_results.get('case_title', 'Unknown')}")
    print(f"   Models queried: {ensemble_results.get('models_queried', 0)}")
    print(f"   Models responded: {ensemble_results.get('models_responded', 0)}")
    
    consensus = ensemble_results.get('consensus_analysis', {})
    print(f"   Consensus level: {consensus.get('consensus_level', 'Unknown')}")
    print(f"   Primary diagnosis: {consensus.get('primary_diagnosis', 'Unknown')}")
    print(f"   Confidence: {consensus.get('primary_confidence', 0):.1%}")
    
    # Generate the final comprehensive report
    print("\n📝 Generating Final Comprehensive Report...")
    print("   This report includes:")
    print("   • Title page with overview")
    print("   • Executive summary")
    print("   • Complete diagnostic landscape")
    print("   • Management strategies")
    print("   • Model diversity analysis")
    print("   • Critical decision points")
    print("   • Evidence synthesis with correlation matrix")
    print("   • Detailed model responses")
    
    report_gen = FinalComprehensiveReportGenerator()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"reports/FINAL_comprehensive_report_{timestamp}.pdf"
    
    try:
        report_path = report_gen.generate_report(
            ensemble_results=ensemble_results,
            output_file=output_file
        )
        
        print(f"\n✅ Final report generated successfully!")
        print(f"   📁 Saved to: {report_path}")
        
        # Open the PDF
        import subprocess
        try:
            subprocess.run(["open", report_path], check=False)
            print(f"   📖 Opening PDF...")
        except:
            print(f"   ℹ️ Please open the PDF manually")
        
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✨ FINAL COMPREHENSIVE REPORT COMPLETE!")
    print("=" * 70)
    
    print("\n📋 Report Contents:")
    print("   Page 1: Title & Overview")
    print("   Page 2: Executive Summary")
    print("   Page 3-4: Diagnostic Landscape Analysis")
    print("   Page 5: Management Strategies & Clinical Pathways")
    print("   Page 6: Model Diversity & Bias Analysis")
    print("   Page 7: Critical Decision Points")
    print("   Page 8: Evidence Synthesis & Correlation Matrix")
    print("   Page 9+: Detailed Model Responses")
    
    print("\n🎯 This report provides:")
    print("   • Complete diagnostic consensus from all models")
    print("   • Actionable clinical recommendations")
    print("   • Bias awareness and mitigation strategies")
    print("   • Evidence-based decision support")
    print("   • Preserved minority opinions")
    print("   • Comprehensive management pathways")
    
    return report_path

if __name__ == "__main__":
    report = main()
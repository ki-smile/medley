#!/usr/bin/env python
"""
Finalize Case 13 Generation - Complete the pipeline with cached responses
"""

import json
import time
from pathlib import Path
from datetime import datetime
import sys

# Add src to path  
sys.path.insert(0, 'src')

from src.medley.models.llm_manager import LLMManager
from src.medley.reporters.report_orchestrator import ReportOrchestrator
from src.medley.reporters.final_comprehensive_report import FinalComprehensiveReportGenerator
from src.medley.analysis.comprehensive_bias_analyzer import ComprehensiveBiasAnalyzer

def load_cached_responses():
    """Load all cached responses for Case 13"""
    cache_dir = Path("cache/responses/Case_13")
    responses = {}
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                model = data.get('model', cache_file.stem.replace('_', '/'))
                responses[model] = data
        except:
            pass
    
    return responses

def main():
    """Complete Case 13 generation"""
    print("🏥 Finalizing Case 13 Generation")
    print("=" * 60)
    
    # Load case
    case_file = Path("usecases/case_013_complex_urology.txt")
    case_content = case_file.read_text()
    
    # Load cached responses
    print("\n📥 Loading cached responses...")
    responses = load_cached_responses()
    print(f"   ✅ Loaded {len(responses)} model responses")
    
    # Create ensemble data structure
    ensemble_data = {
        'case_id': 'Case_13',
        'case_content': case_content,
        'model_responses': responses,
        'metadata': {
            'total_models': len(responses),
            'successful_models': len(responses),
            'failed_models': 0,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Initialize LLM Manager
    llm_manager = LLMManager()
    
    # Run orchestrator
    print("\n🧠 Running orchestrator analysis...")
    orchestrator = ReportOrchestrator(llm_manager)
    
    try:
        orchestrated_analysis = orchestrator.orchestrate_analysis(ensemble_data)
        ensemble_data['orchestrated_analysis'] = orchestrated_analysis
        print("   ✅ Orchestration complete")
    except Exception as e:
        print(f"   ⚠️  Orchestration failed: {e}")
        ensemble_data['orchestrated_analysis'] = {}
    
    # Run comprehensive bias analysis
    print("\n🔍 Running bias analysis...")
    bias_analyzer = ComprehensiveBiasAnalyzer()
    
    try:
        bias_analysis = bias_analyzer.analyze(
            case_content=case_content,
            model_responses=responses,
            case_type="Complex Glomerulonephritis"
        )
        ensemble_data['comprehensive_bias_analysis'] = bias_analysis
        print("   ✅ Bias analysis complete")
    except Exception as e:
        print(f"   ⚠️  Bias analysis failed: {e}")
        ensemble_data['comprehensive_bias_analysis'] = {}
    
    # Generate final report
    print("\n📄 Generating comprehensive report...")
    report_gen = FinalComprehensiveReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path("reports") / f"FINAL_Case_13_comprehensive_{timestamp}.pdf"
    
    try:
        report_gen.generate_report(
            ensemble_results=ensemble_data,
            output_file=str(output_file)
        )
        
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"   ✅ PDF generated: {output_file.name} ({size_kb:.1f} KB)")
            
            # Also generate HTML
            html_file = output_file.with_suffix('.html')
            html_content = report_gen.generate_html_report(ensemble_data)
            html_file.write_text(html_content)
            print(f"   ✅ HTML generated: {html_file.name}")
        else:
            print("   ❌ Report generation failed")
    except Exception as e:
        print(f"   ❌ Report generation error: {e}")
    
    # Save orchestrator cache
    orchestrator_cache_dir = Path("cache/orchestrator/Case_13")
    orchestrator_cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_file = orchestrator_cache_dir / f"orchestrator_analysis_{timestamp}.json"
    with open(cache_file, 'w') as f:
        json.dump(ensemble_data.get('orchestrated_analysis', {}), f, indent=2)
    print(f"\n💾 Cached orchestrator analysis: {cache_file.name}")
    
    print("\n✨ Case 13 finalization complete!")
    print("\n📝 To add to web interface, update MEDICAL_CASES in web_app.py:")
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
    
    print("\nThen restart the web server to see Case 13 in the interface.")

if __name__ == "__main__":
    main()
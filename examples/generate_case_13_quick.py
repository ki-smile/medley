#!/usr/bin/env python
"""
Quick Case 13 Generator - Uses cached responses to generate report immediately
"""

import json
from pathlib import Path
from datetime import datetime
import sys

# Add medley to path
sys.path.insert(0, 'src')

from src.medley.reporters.final_comprehensive_report import FinalComprehensiveReportGenerator
from src.medley.models.orchestrator_synthesis_generator import OrchestratorSynthesisGenerator
from src.medley.analysis.bias_analyzer import BiasAnalyzer
from src.medley.utils.consensus import build_consensus

def load_cached_responses():
    """Load cached model responses for Case 13"""
    cache_dir = Path("cache/responses/Case_13")
    responses = {}
    
    if not cache_dir.exists():
        print(f"❌ Cache directory not found: {cache_dir}")
        return responses
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                model_name = data.get('model', cache_file.stem.replace('_', '/'))
                responses[model_name] = data
                print(f"  ✅ Loaded {model_name}")
        except Exception as e:
            print(f"  ❌ Failed to load {cache_file.name}: {e}")
    
    return responses

def generate_orchestrated_synthesis(responses, case_content):
    """Generate orchestrated synthesis using best available model"""
    orchestrator = OrchestratorSynthesisGenerator()
    
    # Use OpenAI GPT OSS 20B as orchestrator (best free model)
    orchestrator_model = "openai/gpt-oss-20b:free"
    
    print(f"\n🧠 Generating orchestrated synthesis with {orchestrator_model}...")
    
    # Prepare model outputs
    model_outputs = {}
    for model_name, response in responses.items():
        content = response.get('content', response.get('choices', [{}])[0].get('message', {}).get('content', ''))
        if content:
            model_outputs[model_name] = content
    
    # Generate synthesis
    synthesis = orchestrator.generate_synthesis(
        case_content=case_content,
        model_outputs=model_outputs,
        orchestrator_model=orchestrator_model
    )
    
    return synthesis

def main():
    """Generate Case 13 report using cached responses"""
    print("🚀 Quick Case 13 Report Generator")
    print("=" * 60)
    
    # Load case content
    case_file = Path("usecases/case_013_complex_urology.txt")
    if not case_file.exists():
        print(f"❌ Case file not found: {case_file}")
        return
    
    case_content = case_file.read_text()
    print(f"✅ Loaded case: {case_file.name}")
    
    # Load cached responses
    print("\n📥 Loading cached responses...")
    responses = load_cached_responses()
    
    if len(responses) < 5:
        print(f"⚠️  Only {len(responses)} models cached. Continuing anyway...")
    else:
        print(f"✅ Loaded {len(responses)} model responses")
    
    # Generate orchestrated synthesis
    synthesis = generate_orchestrated_synthesis(responses, case_content)
    
    # Build consensus from responses
    print("\n🔄 Building consensus...")
    consensus_data = build_consensus(responses)
    
    # Perform bias analysis
    print("🔍 Analyzing biases...")
    bias_analyzer = BiasAnalyzer()
    bias_analysis = bias_analyzer.analyze_comprehensive_bias(
        responses=responses,
        case_type="Complex Glomerulonephritis",
        patient_demographics={
            "age": 24,
            "sex": "Male",
            "ethnicity": "Middle Eastern (Iranian)",
            "occupation": "Graduate student"
        }
    )
    
    # Generate comprehensive report
    print("\n📄 Generating comprehensive report...")
    report_generator = FinalComprehensiveReportGenerator()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"FINAL_Case_13_comprehensive_{timestamp}"
    
    # Generate HTML report
    html_report = report_generator.generate_html_report(
        case_content=case_content,
        responses=responses,
        synthesis=synthesis,
        consensus_data=consensus_data,
        bias_analysis=bias_analysis,
        case_id="Case_13"
    )
    
    # Save HTML
    html_path = Path("reports") / f"{report_name}.html"
    html_path.write_text(html_report)
    print(f"  ✅ HTML report: {html_path}")
    
    # Generate PDF report
    pdf_path = Path("reports") / f"{report_name}.pdf"
    report_generator.generate_report(
        case_content=case_content,
        responses=responses,
        synthesis=synthesis,
        consensus_data=consensus_data,
        bias_analysis=bias_analysis,
        output_path=str(pdf_path),
        case_id="Case_13"
    )
    print(f"  ✅ PDF report: {pdf_path}")
    
    print("\n✨ Case 13 report generated successfully!")
    print("   - Uses same green theme as Cases 1-12")
    print("   - Comprehensive structure matching existing cases")
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

if __name__ == "__main__":
    main()
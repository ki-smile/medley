"""
Consensus Report Generator for Medley
Generates formatted reports showing consensus, alternatives, and clinical recommendations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from io import BytesIO

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import KeepTogether, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import markdown2
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

class ConsensusReportGenerator:
    """Generates formatted consensus reports from ensemble analysis"""
    
    def __init__(self):
        self.report_template = {
            "header": "# MEDLEY Consensus Report - {case_id}",
            "sections": [
                "case_summary",
                "model_outputs",
                "consensus_analysis",
                "alternative_diagnoses",
                "next_actions",
                "clinical_recommendation",
                "performance_metrics"
            ]
        }
    
    def generate_report(
        self,
        ensemble_results: Dict[str, Any],
        output_format: str = "markdown",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a consensus report from ensemble results
        
        Args:
            ensemble_results: Results from ensemble analysis
            output_format: Format for report (markdown, html, text, pdf)
            output_file: Optional file path to save report
            
        Returns:
            Formatted report as string (or path for PDF)
        """
        if output_format == "markdown":
            report = self._generate_markdown_report(ensemble_results)
        elif output_format == "html":
            report = self._generate_html_report(ensemble_results)
        elif output_format == "pdf":
            if not PDF_AVAILABLE:
                raise ImportError("PDF generation requires reportlab library. Install with: pip install reportlab")
            report = self._generate_pdf_report(ensemble_results, output_file)
            return report  # For PDF, return the file path
        else:  # text
            report = self._generate_text_report(ensemble_results)
        
        # Save to file if specified (except PDF which handles its own saving)
        if output_file and output_format != "pdf":
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown formatted report"""
        
        consensus = results.get("consensus_analysis", {})
        case_id = results.get("case_id", "Unknown")
        case_title = results.get("case_title", "Unknown Case")
        case_desc = results.get("case_description", {})
        
        report_lines = []
        
        # Header
        report_lines.append(f"# MEDLEY Report - {case_id}")
        report_lines.append("")
        report_lines.append(f"**Case**: {case_title}")
        report_lines.append(f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Models Analyzed**: {results.get('models_queried', 0)}")
        report_lines.append(f"**Successful Responses**: {consensus.get('responding_models', 0)}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Case Description Section
        report_lines.append("## 📋 Case Description")
        report_lines.append("")
        
        # Patient Information
        if case_desc.get("patient_info"):
            report_lines.append("### Patient Information")
            report_lines.append(case_desc["patient_info"])
            report_lines.append("")
        
        # Presentation
        if case_desc.get("presentation"):
            report_lines.append("### Clinical Presentation")
            report_lines.append(case_desc["presentation"])
            report_lines.append("")
        
        # Key Symptoms
        if case_desc.get("symptoms"):
            report_lines.append("### Key Symptoms")
            for symptom in case_desc["symptoms"]:
                report_lines.append(f"- {symptom}")
            report_lines.append("")
        
        # Medical History
        if case_desc.get("history"):
            report_lines.append("### Medical History")
            report_lines.append(case_desc["history"])
            report_lines.append("")
        
        # Physical Examination
        if case_desc.get("physical_exam"):
            report_lines.append("### Physical Examination")
            report_lines.append(case_desc["physical_exam"])
            report_lines.append("")
        
        # Laboratory Results
        if case_desc.get("labs"):
            report_lines.append("### Laboratory Results")
            report_lines.append(case_desc["labs"])
            report_lines.append("")
        
        # Imaging
        if case_desc.get("imaging"):
            report_lines.append("### Imaging")
            report_lines.append(case_desc["imaging"])
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
        
        # Multi-Model Ensemble Box
        report_lines.append("## Multi-Model Ensemble Analysis")
        report_lines.append("")
        report_lines.append("```")
        report_lines.append("┌─────────────────────────────────────────────────────────────────┐")
        report_lines.append("│ Model Outputs:                                                   │")
        report_lines.append("├─────────────────────────────────────────────────────────────────┤")
        
        # Add model outputs
        for model_resp in results.get("model_responses", []):
            model_name = model_resp.get("model_name", "Unknown").split("/")[-1]
            origin = model_resp.get("origin", "Unknown")
            
            if model_resp.get("error"):
                status = "[Error]"
                diagnosis = "Failed to respond"
            elif model_resp.get("response"):
                # Try to get primary diagnosis from parsed response
                model_idx = results["model_responses"].index(model_resp)
                parsed = results.get("parsed_responses", [])[model_idx] if model_idx < len(results.get("parsed_responses", [])) else None
                
                if parsed and "differential_diagnoses" in parsed and parsed["differential_diagnoses"]:
                    diagnosis = parsed["differential_diagnoses"][0].get("diagnosis", "Unspecified")
                else:
                    diagnosis = "Response received"
                status = ""
            else:
                status = "[No response]"
                diagnosis = "No diagnosis provided"
            
            line = f"│ {model_name:12} ({origin:8}): {status:8} {diagnosis:24} │"
            report_lines.append(line[:69] + "│")
        
        report_lines.append("├─────────────────────────────────────────────────────────────────┤")
        
        # Consensus summary
        consensus_level = consensus.get("consensus_level", "None")
        primary_diag = consensus.get("primary_diagnosis", "No consensus")
        
        report_lines.append(f"│ Consensus View:      {consensus_level:43} │")
        report_lines.append(f"│ Primary Diagnosis:   {primary_diag[:43]:43} │")
        
        # Key alternatives
        alternatives = consensus.get("alternative_diagnoses", [])
        if alternatives:
            report_lines.append("│ Key Alternatives:                                               │")
            for i, alt in enumerate(alternatives[:3], 1):
                alt_name = alt.get("diagnosis", "Unknown")
                report_lines.append(f"│   {i}. {alt_name[:58]:58} │")
        
        # Action required
        action = consensus.get("action_required", "Clinical evaluation required")
        report_lines.append(f"│ Action Required:     {action[:43]:43} │")
        
        report_lines.append("└─────────────────────────────────────────────────────────────────┘")
        report_lines.append("```")
        report_lines.append("")
        
        # Detailed Consensus Analysis
        report_lines.append("## 📊 Detailed Consensus Analysis")
        report_lines.append("")
        report_lines.append("### Primary Diagnosis Consensus")
        report_lines.append("")
        report_lines.append("| Diagnosis | Model Agreement | Confidence |")
        report_lines.append("|-----------|----------------|------------|")
        
        # Add top diagnoses with agreement
        for diag, score in list(consensus.get("agreement_scores", {}).items())[:5]:
            percentage = f"{score*100:.0f}%"
            confidence = "High" if score > 0.75 else "Moderate" if score > 0.5 else "Low"
            report_lines.append(f"| {diag} | {percentage} | {confidence} |")
        
        report_lines.append("")
        
        # Geographic patterns
        if consensus.get("geographic_patterns"):
            report_lines.append("### Geographic Pattern Analysis")
            report_lines.append("")
            for origin, diagnoses in consensus.get("geographic_patterns", {}).items():
                if diagnoses:
                    report_lines.append(f"- **{origin}**: {', '.join(diagnoses[:3])}")
            report_lines.append("")
        
        # Recommended Next Actions
        report_lines.append("## 🎯 Recommended Next Actions")
        report_lines.append("")
        report_lines.append("```")
        report_lines.append("┌─────────────────────────────────────────────────────────────────┐")
        report_lines.append("│ CONSENSUS NEXT STEPS                                             │")
        report_lines.append("├─────────────────────────────────────────────────────────────────┤")
        
        # Clinical recommendation
        clinical_rec = consensus.get("clinical_recommendation", "")
        if clinical_rec:
            # Word wrap the recommendation
            words = clinical_rec.split()
            current_line = "│ "
            for word in words:
                if len(current_line) + len(word) + 1 > 66:
                    report_lines.append(f"{current_line:66} │")
                    current_line = "│ "
                current_line += word + " "
            if len(current_line) > 2:
                report_lines.append(f"{current_line:66} │")
        
        report_lines.append("│                                                                  │")
        
        # Based on consensus level, add specific actions
        if consensus_level == "Strong":
            report_lines.append("│ • Proceed with targeted testing for primary diagnosis           │")
            report_lines.append("│ • Initiate appropriate treatment protocols                      │")
            report_lines.append("│ • Monitor response to therapy                                   │")
        elif consensus_level == "Partial":
            report_lines.append("│ • Conduct differential testing for top diagnoses                │")
            report_lines.append("│ • Consider specialist consultation                              │")
            report_lines.append("│ • Re-evaluate with additional clinical data                     │")
        else:
            report_lines.append("│ • Comprehensive diagnostic workup required                      │")
            report_lines.append("│ • Multi-specialist consultation recommended                     │")
            report_lines.append("│ • Consider rare or atypical presentations                       │")
        
        report_lines.append("└─────────────────────────────────────────────────────────────────┘")
        report_lines.append("```")
        report_lines.append("")
        
        # Bias Considerations
        bias_considerations = consensus.get("bias_considerations", [])
        if bias_considerations:
            report_lines.append("## ⚠️ Bias Awareness Alert")
            report_lines.append("")
            report_lines.append("```")
            for bias in bias_considerations:
                report_lines.append(f"• {bias}")
            report_lines.append("```")
            report_lines.append("")
        
        # Minority Opinions
        minority_opinions = consensus.get("minority_opinions", [])
        if minority_opinions:
            report_lines.append("## 💡 Important Minority Opinions")
            report_lines.append("")
            for opinion in minority_opinions[:3]:
                diag = opinion.get("diagnosis", "Unknown")
                models = opinion.get("supporting_models", [])
                report_lines.append(f"- **{diag}**: Suggested by {', '.join(models[:2])}")
            report_lines.append("")
        
        # Performance Metrics
        report_lines.append("## 📈 Performance Metrics")
        report_lines.append("")
        report_lines.append(f"- **Models Consulted**: {results.get('models_queried', 0)}")
        report_lines.append(f"- **Successful Responses**: {consensus.get('responding_models', 0)}")
        report_lines.append(f"- **Consensus Level**: {consensus_level}")
        
        if consensus.get("primary_diagnosis"):
            report_lines.append(f"- **Primary Diagnosis Confidence**: {consensus.get('primary_confidence', 0)*100:.0f}%")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Clinical Value Summary")
        report_lines.append("")
        
        # Add value summary based on consensus
        if consensus_level == "Strong":
            report_lines.append("✅ **High confidence diagnosis achieved** - The ensemble shows strong agreement, providing clear direction for clinical management.")
        elif consensus_level == "Partial":
            report_lines.append("⚠️ **Moderate consensus with alternatives** - The ensemble identified a likely diagnosis but important alternatives exist. Additional testing recommended.")
        else:
            report_lines.append("🔍 **Diagnostic uncertainty identified** - The lack of consensus itself is valuable information, indicating a complex case requiring careful clinical evaluation.")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append(f"*Report generated by Medley Medical AI Ensemble System at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report_lines.append("")
        report_lines.append("*Developed by Farhad Abtahi - SMAILE at Karolinska Institutet - [smile.ki.se](https://smile.ki.se)*")
        
        return "\n".join(report_lines)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate properly formatted HTML report"""
        
        consensus = results.get("consensus_analysis", {})
        case_id = results.get("case_id", "Unknown")
        case_title = results.get("case_title", "Unknown Case")
        case_desc = results.get("case_description", {})
        
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>Medley Report - {case_id}</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }",
            ".container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 30px; }",
            "h2 { color: #34495e; margin-top: 40px; margin-bottom: 20px; border-left: 4px solid #3498db; padding-left: 10px; }",
            "h3 { color: #7f8c8d; margin-top: 25px; }",
            ".metadata { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 30px; }",
            ".metadata-table { width: 100%; }",
            ".metadata-table td { padding: 8px 0; }",
            ".metadata-table td:first-child { font-weight: bold; width: 200px; color: #34495e; }",
            "pre { background: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th { background-color: #3498db; color: white; padding: 12px; text-align: left; }",
            "td { border-bottom: 1px solid #ecf0f1; padding: 10px; }",
            "tr:hover { background-color: #f8f9fa; }",
            ".alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }",
            ".success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; }",
            ".warning { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 5px; }",
            ".case-desc { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }",
            ".case-desc h3 { margin-top: 0; color: #2c3e50; }",
            ".symptom-list { list-style-type: none; padding-left: 0; }",
            ".symptom-list li { padding: 5px 0; padding-left: 20px; position: relative; }",
            ".symptom-list li:before { content: '▸'; position: absolute; left: 0; color: #3498db; }",
            "footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #ecf0f1; text-align: center; color: #7f8c8d; }",
            "footer a { color: #3498db; text-decoration: none; }",
            "footer a:hover { text-decoration: underline; }",
            ".badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 10px; }",
            ".badge-strong { background: #27ae60; color: white; }",
            ".badge-partial { background: #f39c12; color: white; }",
            ".badge-weak { background: #e74c3c; color: white; }",
            ".model-responses { margin-top: 30px; }",
            ".model-card { border: 1px solid #ecf0f1; border-radius: 5px; padding: 15px; margin-bottom: 15px; }",
            ".model-card h4 { margin-top: 0; color: #2c3e50; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
        ]
        
        # Title
        html_lines.append(f"<h1>MEDLEY Report</h1>")
        html_lines.append(f"<h2>Case {case_id}: {case_title}</h2>")
        
        # Metadata section
        html_lines.append("<div class='metadata'>")
        html_lines.append("<table class='metadata-table'>")
        html_lines.append(f"<tr><td>Analysis Date:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>")
        html_lines.append(f"<tr><td>Models Analyzed:</td><td>{results.get('models_queried', 0)}</td></tr>")
        html_lines.append(f"<tr><td>Successful Responses:</td><td>{consensus.get('responding_models', 0)}</td></tr>")
        
        consensus_level = consensus.get('consensus_level', 'None')
        badge_class = 'badge-strong' if consensus_level == 'Strong' else 'badge-partial' if consensus_level == 'Partial' else 'badge-weak'
        html_lines.append(f"<tr><td>Consensus Level:</td><td>{consensus_level} <span class='badge {badge_class}'>{consensus_level}</span></td></tr>")
        
        html_lines.append(f"<tr><td>Primary Diagnosis:</td><td><strong>{consensus.get('primary_diagnosis', 'No consensus')}</strong></td></tr>")
        html_lines.append("</table>")
        html_lines.append("</div>")
        
        # Case Description
        if case_desc:
            html_lines.append("<div class='case-desc'>")
            html_lines.append("<h3>Case Description</h3>")
            
            if case_desc.get("patient_info"):
                html_lines.append(f"<p><strong>Patient Information:</strong> {case_desc['patient_info']}</p>")
            
            if case_desc.get("presentation"):
                html_lines.append(f"<p><strong>Clinical Presentation:</strong> {case_desc['presentation']}</p>")
            
            if case_desc.get("symptoms"):
                html_lines.append("<p><strong>Key Symptoms:</strong></p>")
                html_lines.append("<ul class='symptom-list'>")
                for symptom in case_desc["symptoms"]:
                    html_lines.append(f"<li>{symptom}</li>")
                html_lines.append("</ul>")
            
            html_lines.append("</div>")
        
        # Consensus Analysis
        html_lines.append("<h2>📊 Detailed Consensus Analysis</h2>")
        
        # Diagnosis table
        html_lines.append("<h3>Primary Diagnosis Consensus</h3>")
        html_lines.append("<table>")
        html_lines.append("<thead><tr><th>Diagnosis</th><th>Model Agreement</th><th>Confidence</th></tr></thead>")
        html_lines.append("<tbody>")
        
        for diag, score in list(consensus.get("agreement_scores", {}).items())[:5]:
            percentage = f"{score*100:.0f}%"
            confidence = "High" if score > 0.75 else "Moderate" if score > 0.5 else "Low"
            html_lines.append(f"<tr><td>{diag}</td><td>{percentage}</td><td>{confidence}</td></tr>")
        
        html_lines.append("</tbody></table>")
        
        # Model Responses Summary (exclude failed models)
        html_lines.append("<h2>🤖 Model Responses</h2>")
        html_lines.append("<div class='model-responses'>")
        
        model_count = 0
        for i, model_resp in enumerate(results.get("model_responses", [])):
            # Skip failed models
            if model_resp.get("error"):
                continue
                
            model_name = model_resp.get("model_name", "Unknown")
            origin = model_resp.get("origin", "Unknown")
            parsed = results.get("parsed_responses", [])[i] if i < len(results.get("parsed_responses", [])) else None
            
            if parsed and hasattr(parsed, 'differential_diagnoses') and parsed.differential_diagnoses:
                html_lines.append("<div class='model-card'>")
                html_lines.append(f"<h4>{model_name} ({origin})</h4>")
                html_lines.append("<p><strong>Differential Diagnoses:</strong></p>")
                html_lines.append("<ol>")
                # Show ALL diagnoses, not just top 3
                for diag in parsed.differential_diagnoses:
                    diagnosis_name = diag.get('diagnosis', 'Unknown')
                    reasoning = diag.get('reasoning', '')
                    if reasoning and len(reasoning) > 100:
                        reasoning = reasoning[:100] + "..."
                    html_lines.append(f"<li><strong>{diagnosis_name}</strong>")
                    if reasoning:
                        html_lines.append(f"<br><small style='color: #666;'>{reasoning}</small>")
                    html_lines.append("</li>")
                html_lines.append("</ol>")
                html_lines.append("</div>")
                model_count += 1
        
        if model_count == 0:
            html_lines.append("<p>No successful model responses to display.</p>")
        
        html_lines.append("</div>")
        
        # Geographic patterns
        if consensus.get("geographic_patterns"):
            html_lines.append("<h2>🌍 Geographic Pattern Analysis</h2>")
            html_lines.append("<ul>")
            for origin, diagnoses in consensus.get("geographic_patterns", {}).items():
                if diagnoses:
                    html_lines.append(f"<li><strong>{origin}:</strong> {', '.join(diagnoses[:3])}</li>")
            html_lines.append("</ul>")
        
        # Recommended Actions
        html_lines.append("<h2>🎯 Recommended Next Actions</h2>")
        clinical_rec = consensus.get("clinical_recommendation", "")
        if clinical_rec:
            html_lines.append(f"<p>{clinical_rec}</p>")
        
        # Action steps based on consensus
        html_lines.append("<ul>")
        if consensus_level == "Strong":
            html_lines.append("<li>Proceed with targeted testing for primary diagnosis</li>")
            html_lines.append("<li>Initiate appropriate treatment protocols</li>")
            html_lines.append("<li>Monitor response to therapy</li>")
        elif consensus_level == "Partial":
            html_lines.append("<li>Conduct differential testing for top diagnoses</li>")
            html_lines.append("<li>Consider specialist consultation</li>")
            html_lines.append("<li>Re-evaluate with additional clinical data</li>")
        else:
            html_lines.append("<li>Comprehensive diagnostic workup required</li>")
            html_lines.append("<li>Multi-specialist consultation recommended</li>")
            html_lines.append("<li>Consider rare or atypical presentations</li>")
        html_lines.append("</ul>")
        
        # Bias Considerations
        bias_considerations = consensus.get("bias_considerations", [])
        if bias_considerations:
            html_lines.append("<h2>⚠️ Bias Awareness Alert</h2>")
            html_lines.append("<div class='alert'>")
            html_lines.append("<ul>")
            for bias in bias_considerations:
                html_lines.append(f"<li>{bias}</li>")
            html_lines.append("</ul>")
            html_lines.append("</div>")
        
        # Minority Opinions
        minority_opinions = consensus.get("minority_opinions", [])
        if minority_opinions:
            html_lines.append("<h2>💡 Important Minority Opinions</h2>")
            html_lines.append("<ul>")
            for opinion in minority_opinions[:3]:
                diag = opinion.get("diagnosis", "Unknown")
                models = opinion.get("models", [])
                html_lines.append(f"<li><strong>{diag}</strong> - Suggested by: {', '.join(models)}</li>")
            html_lines.append("</ul>")
        
        # Footer
        html_lines.append("</div>")  # Close container
        html_lines.append("<footer>")
        html_lines.append(f"<p>Report generated by Medley Medical AI Ensemble System<br>")
        html_lines.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html_lines.append("<p><em>Developed by Farhad Abtahi<br>")
        html_lines.append("SMAILE at Karolinska Institutet<br>")
        html_lines.append("<a href='https://smile.ki.se'>smile.ki.se</a></em></p>")
        html_lines.append("</footer>")
        
        html_lines.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_lines)
    
    def _generate_text_report(self, results: Dict[str, Any]) -> str:
        """Generate plain text report"""
        
        consensus = results.get("consensus_analysis", {})
        case_id = results.get("case_id", "Unknown")
        case_desc = results.get("case_description", {})
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"MEDLEY REPORT - {case_id}")
        lines.append("=" * 80)
        lines.append("")
        
        # Case Description
        lines.append("CASE DESCRIPTION")
        lines.append("-" * 40)
        
        if case_desc.get("patient_info"):
            lines.append(f"Patient: {case_desc['patient_info']}")
        
        if case_desc.get("presentation"):
            lines.append(f"Presentation: {case_desc['presentation']}")
        
        if case_desc.get("symptoms"):
            lines.append("Symptoms: " + ", ".join(case_desc["symptoms"]))
        
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Models Analyzed: {results.get('models_queried', 0)}")
        lines.append(f"Successful Responses: {consensus.get('responding_models', 0)}")
        lines.append(f"Consensus Level: {consensus.get('consensus_level', 'None')}")
        lines.append(f"Primary Diagnosis: {consensus.get('primary_diagnosis', 'No consensus')}")
        lines.append("")
        
        # Model responses
        lines.append("MODEL RESPONSES")
        lines.append("-" * 40)
        for model_resp in results.get("model_responses", []):
            model_name = model_resp.get("model_name", "Unknown")
            origin = model_resp.get("origin", "Unknown")
            status = "Success" if model_resp.get("response") else "Failed"
            lines.append(f"  {model_name} ({origin}): {status}")
        lines.append("")
        
        # Consensus details
        lines.append("CONSENSUS ANALYSIS")
        lines.append("-" * 40)
        
        for diag, score in list(consensus.get("agreement_scores", {}).items())[:5]:
            lines.append(f"  {diag}: {score*100:.0f}% agreement")
        lines.append("")
        
        # Recommendations
        lines.append("CLINICAL RECOMMENDATION")
        lines.append("-" * 40)
        lines.append(consensus.get("clinical_recommendation", "No recommendation available"))
        lines.append("")
        
        # Action required
        lines.append("ACTION REQUIRED")
        lines.append("-" * 40)
        lines.append(consensus.get("action_required", "Clinical evaluation required"))
        lines.append("")
        
        # Bias considerations
        if consensus.get("bias_considerations"):
            lines.append("BIAS CONSIDERATIONS")
            lines.append("-" * 40)
            for bias in consensus.get("bias_considerations", []):
                lines.append(f"  - {bias}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("Developed by Farhad Abtahi - SMAILE at Karolinska Institutet")
        lines.append("Website: smile.ki.se")
        
        return "\n".join(lines)
    
    def _generate_pdf_report(self, results: Dict[str, Any], output_file: str) -> str:
        """Generate PDF formatted report"""
        
        if not output_file:
            raise ValueError("Output file path is required for PDF generation")
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=20
        ))
        styles.add(ParagraphStyle(
            name='SubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=10
        ))
        styles.add(ParagraphStyle(
            name='Alert',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            rightIndent=20,
            borderColor=colors.HexColor('#ffc107'),
            borderWidth=1,
            borderPadding=10,
            backColor=colors.HexColor('#fff3cd')
        ))
        
        # Extract data
        consensus = results.get("consensus_analysis", {})
        case_id = results.get("case_id", "Unknown")
        case_title = results.get("case_title", "Unknown Case")
        case_desc = results.get("case_description", {})
        
        # Title
        elements.append(Paragraph(f"MEDLEY Report", styles['CustomTitle']))
        elements.append(Paragraph(f"Case {case_id}: {case_title}", styles['SectionHeading']))
        elements.append(Spacer(1, 12))
        
        # Metadata
        metadata = [
            ["Analysis Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Models Analyzed:", str(results.get('models_queried', 0))],
            ["Successful Responses:", str(consensus.get('responding_models', 0))],
            ["Consensus Level:", consensus.get('consensus_level', 'None')],
            ["Primary Diagnosis:", consensus.get('primary_diagnosis', 'No consensus')]
        ]
        
        metadata_table = Table(metadata, colWidths=[2.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(metadata_table)
        elements.append(Spacer(1, 20))
        
        # Case Description Section
        elements.append(Paragraph("Case Description", styles['SectionHeading']))
        
        # Patient Information
        if case_desc.get("patient_info"):
            elements.append(Paragraph("<b>Patient Information</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["patient_info"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Presentation
        if case_desc.get("presentation"):
            elements.append(Paragraph("<b>Clinical Presentation</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["presentation"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Key Symptoms
        if case_desc.get("symptoms") and case_desc["symptoms"]:
            elements.append(Paragraph("<b>Key Symptoms</b>", styles['SubHeading']))
            for symptom in case_desc["symptoms"]:
                elements.append(Paragraph(f"• {symptom}", styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Medical History
        if case_desc.get("history"):
            elements.append(Paragraph("<b>Medical History</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["history"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Physical Examination
        if case_desc.get("physical_exam"):
            elements.append(Paragraph("<b>Physical Examination</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["physical_exam"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Laboratory Results
        if case_desc.get("labs"):
            elements.append(Paragraph("<b>Laboratory Results</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["labs"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Imaging
        if case_desc.get("imaging"):
            elements.append(Paragraph("<b>Imaging</b>", styles['SubHeading']))
            elements.append(Paragraph(case_desc["imaging"], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 20))
        
        # Model Responses Section
        elements.append(Paragraph("Model Responses", styles['SectionHeading']))
        
        model_data = [["Model", "Origin", "Status", "Primary Diagnosis"]]
        for model_resp in results.get("model_responses", []):
            model_name = model_resp.get("model_name", "Unknown").split("/")[-1][:20]
            origin = model_resp.get("origin", "Unknown")
            
            if model_resp.get("error"):
                status = "Failed"
                diagnosis = "Error"
            elif model_resp.get("response"):
                status = "Success"
                # Try to get primary diagnosis
                model_idx = results["model_responses"].index(model_resp)
                parsed = results.get("parsed_responses", [])[model_idx] if model_idx < len(results.get("parsed_responses", [])) else None
                
                if parsed and "differential_diagnoses" in parsed and parsed["differential_diagnoses"]:
                    diagnosis = parsed["differential_diagnoses"][0].get("diagnosis", "Unspecified")[:30]
                else:
                    diagnosis = "Analyzed"
            else:
                status = "No response"
                diagnosis = "-"
            
            model_data.append([model_name, origin, status, diagnosis])
        
        model_table = Table(model_data, colWidths=[2*inch, 1.2*inch, 1*inch, 2.3*inch])
        model_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(model_table)
        elements.append(Spacer(1, 20))
        
        # Consensus Analysis Section
        elements.append(Paragraph("Consensus Analysis", styles['SectionHeading']))
        
        # Agreement scores
        if consensus.get("agreement_scores"):
            elements.append(Paragraph("Diagnosis Agreement", styles['SubHeading']))
            
            agreement_data = [["Diagnosis", "Agreement %", "Confidence"]]
            for diag, score in list(consensus.get("agreement_scores", {}).items())[:5]:
                percentage = f"{score*100:.0f}%"
                confidence = "High" if score > 0.75 else "Moderate" if score > 0.5 else "Low"
                agreement_data.append([diag[:40], percentage, confidence])
            
            agreement_table = Table(agreement_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            agreement_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
            ]))
            elements.append(agreement_table)
            elements.append(Spacer(1, 15))
        
        # Clinical Recommendation
        if consensus.get("clinical_recommendation"):
            elements.append(Paragraph("Clinical Recommendation", styles['SectionHeading']))
            elements.append(Paragraph(consensus["clinical_recommendation"], styles['Normal']))
            elements.append(Spacer(1, 15))
        
        # Bias Considerations
        bias_considerations = consensus.get("bias_considerations", [])
        if bias_considerations:
            elements.append(Paragraph("⚠️ Bias Awareness", styles['SectionHeading']))
            for bias in bias_considerations:
                elements.append(Paragraph(f"• {bias}", styles['Normal']))
            elements.append(Spacer(1, 15))
        
        # Alternative Diagnoses
        alternatives = consensus.get("alternative_diagnoses", [])
        if alternatives:
            elements.append(Paragraph("Alternative Diagnoses", styles['SectionHeading']))
            
            alt_data = [["Diagnosis", "Agreement", "Supporting Models"]]
            for alt in alternatives[:5]:
                diag = alt.get('diagnosis', 'Unknown')[:30]
                conf = f"{alt.get('confidence', 0)*100:.0f}%"
                models = ", ".join(alt.get('supporting_models', [])[:2])[:30]
                alt_data.append([diag, conf, models])
            
            alt_table = Table(alt_data, colWidths=[2.5*inch, 1.2*inch, 2.8*inch])
            alt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffe5e5')]),
            ]))
            elements.append(alt_table)
            elements.append(Spacer(1, 15))
        
        # Next Steps
        elements.append(Paragraph("Recommended Actions", styles['SectionHeading']))
        action_required = consensus.get("action_required", "Clinical evaluation required")
        elements.append(Paragraph(action_required, styles['Normal']))
        
        # Add specific actions based on consensus level
        consensus_level = consensus.get("consensus_level", "None")
        if consensus_level == "Strong":
            actions = [
                "• Proceed with targeted testing for primary diagnosis",
                "• Initiate appropriate treatment protocols",
                "• Monitor response to therapy"
            ]
        elif consensus_level == "Partial":
            actions = [
                "• Conduct differential testing for top diagnoses",
                "• Consider specialist consultation",
                "• Re-evaluate with additional clinical data"
            ]
        else:
            actions = [
                "• Comprehensive diagnostic workup required",
                "• Multi-specialist consultation recommended",
                "• Consider rare or atypical presentations"
            ]
        
        for action in actions:
            elements.append(Paragraph(action, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Performance Metrics
        elements.append(Paragraph("Performance Metrics", styles['SectionHeading']))
        
        metrics_data = [
            ["Metric", "Value"],
            ["Models Consulted", str(results.get('models_queried', 0))],
            ["Successful Responses", str(consensus.get('responding_models', 0))],
            ["Consensus Level", consensus_level],
            ["Primary Diagnosis Confidence", f"{consensus.get('primary_confidence', 0)*100:.0f}%"],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f6e8')]),
        ]))
        elements.append(metrics_table)
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Report generated by Medley Medical AI Ensemble System<br/>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            footer_style
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "Developed by Farhad Abtahi<br/>SMAILE at Karolinska Institutet<br/>smile.ki.se",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        
        return output_file
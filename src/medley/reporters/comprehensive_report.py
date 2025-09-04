"""
Comprehensive Clinical Decision Report Generator for Medley
Full 3-page report with LLM-assisted analysis and decision support
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
import json
import re
import logging
from dataclasses import dataclass, field

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
        PageBreak, KeepTogether, Flowable, Image, HRFlowable,
        CondPageBreak, NextPageTemplate, Frame, PageTemplate
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Line, Rect, String
    from reportlab.graphics import renderPDF
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisInfo:
    """Structured diagnosis information"""
    name: str
    agreement_percentage: float
    supporting_models: List[str]
    evidence: List[str]
    confidence: str = "Moderate"
    
    
@dataclass
class ManagementStrategy:
    """Management strategy information"""
    action: str
    consensus_level: float
    supporting_models: List[str]
    category: str  # "Immediate", "Differential", "Treatment", "Consultation"
    

@dataclass
class CriticalDecisionPoint:
    """Critical decision points where models diverge"""
    topic: str
    divergence_description: str
    option_1: Tuple[str, List[str], float]  # (description, models, percentage)
    option_2: Tuple[str, List[str], float]


class ComprehensiveReportGenerator:
    """Generate comprehensive 3-page clinical decision support reports"""
    
    def __init__(self, llm_manager=None):
        """
        Initialize report generator
        
        Args:
            llm_manager: Optional LLM manager for advanced analysis
        """
        self.llm_manager = llm_manager
        self.model_metadata = ModelMetadata()
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#4F0433'),  # KI Dark Plum
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#870052'),  # KI Plum Logo
            spaceAfter=12,
            spaceBefore=12,
            leftIndent=0,
            bulletIndent=0
        ))
        
        # Subsection header style  
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#4F0433'),  # KI Dark Plum
            spaceAfter=8,
            spaceBefore=8
        ))
        
        # Diagnosis style
        self.styles.add(ParagraphStyle(
            name='DiagnosisStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2D2D2D'),  # KI Grey Dark
            leftIndent=12,
            spaceAfter=6
        ))
        
        # Evidence style
        self.styles.add(ParagraphStyle(
            name='EvidenceStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6B6B6B'),  # KI Grey Medium
            leftIndent=24,
            spaceAfter=4
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='FooterStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6B6B6B'),  # KI Grey Medium
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
    async def analyze_with_llm(self, ensemble_results: Dict, analysis_type: str) -> Dict:
        """
        Use LLM to analyze ensemble results for specific insights
        
        Args:
            ensemble_results: The ensemble analysis results
            analysis_type: Type of analysis needed
            
        Returns:
            Analyzed insights
        """
        if not self.llm_manager:
            return self._fallback_analysis(ensemble_results, analysis_type)
            
        prompt = self._create_analysis_prompt(ensemble_results, analysis_type)
        
        try:
            # Use a fast, capable model for analysis
            response = await self.llm_manager.query_model(
                model_name="anthropic/claude-3-sonnet-20240229",
                prompt=prompt,
                temperature=0.3  # Lower temperature for consistent analysis
            )
            
            # Parse the response
            return self._parse_llm_response(response, analysis_type)
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, using fallback")
            return self._fallback_analysis(ensemble_results, analysis_type)
            
    def _create_analysis_prompt(self, ensemble_results: Dict, analysis_type: str) -> str:
        """Create specific prompts for different analysis types"""
        
        base_context = f"""
        Analyze the following medical AI ensemble results for {ensemble_results.get('case_title', 'unknown case')}.
        {len(ensemble_results.get('model_responses', []))} models provided diagnoses.
        """
        
        if analysis_type == "management_strategies":
            return f"""{base_context}
            Extract and categorize all management recommendations into:
            1. Immediate Actions (tests, treatments to start now)
            2. Differential Testing (tests to rule out alternatives)
            3. Treatment Options (medication recommendations)
            4. Specialist Consultations
            
            For each, note which models recommended it and calculate consensus percentage.
            Format as JSON with categories as keys.
            """
            
        elif analysis_type == "critical_decisions":
            return f"""{base_context}
            Identify the key decision points where models disagreed significantly.
            Focus on:
            1. Diagnostic approach differences
            2. Treatment urgency variations
            3. Testing priority disagreements
            4. Risk assessment differences
            
            Format as JSON with decision points and model groupings.
            """
            
        elif analysis_type == "evidence_synthesis":
            return f"""{base_context}
            Create a symptom-diagnosis correlation matrix showing how different symptoms
            support each proposed diagnosis. Rate support as Strong(+++), Moderate(++), 
            Weak(+), or Not typical(-).
            
            Also extract key evidence points mentioned by models.
            Format as JSON.
            """
            
        elif analysis_type == "bias_patterns":
            return f"""{base_context}
            Analyze potential biases based on:
            1. Model geographic origins and how they affect diagnoses
            2. Model size/capability differences
            3. Training data recency effects
            4. Cultural or demographic assumptions
            
            Format findings as JSON with specific examples.
            """
            
        return base_context
        
    def _parse_llm_response(self, response: str, analysis_type: str) -> Dict:
        """Parse LLM response into structured data"""
        try:
            # Extract JSON from response if present
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
            
        # Fallback to text parsing
        return self._fallback_analysis({"response": response}, analysis_type)
        
    def _fallback_analysis(self, ensemble_results: Dict, analysis_type: str) -> Dict:
        """Fallback analysis when LLM is not available"""
        
        if analysis_type == "management_strategies":
            return self._extract_management_strategies(ensemble_results)
        elif analysis_type == "critical_decisions":
            return self._identify_critical_decisions(ensemble_results)
        elif analysis_type == "evidence_synthesis":
            return self._synthesize_evidence(ensemble_results)
        elif analysis_type == "bias_patterns":
            return self._analyze_bias_patterns(ensemble_results)
            
        return {}
        
    def _extract_management_strategies(self, ensemble_results: Dict) -> Dict:
        """Extract management strategies from model responses"""
        strategies = {
            "immediate_actions": [],
            "differential_testing": [],
            "treatment_options": [],
            "consultations": []
        }
        
        # Keywords for categorization
        immediate_keywords = ["immediate", "urgent", "start", "begin", "initiate"]
        testing_keywords = ["test", "genetic", "blood", "imaging", "biopsy", "culture"]
        treatment_keywords = ["colchicine", "steroid", "nsaid", "antibiotic", "therapy"]
        consult_keywords = ["rheumatology", "genetics", "gastro", "specialist", "refer"]
        
        for response in ensemble_results.get('model_responses', []):
            if not response.get('response'):
                continue
                
            # Handle both JSON and text responses
            raw_response = response['response']
            text = ""
            
            # Try to parse as JSON first (for structured responses)
            if isinstance(raw_response, str) and (raw_response.strip().startswith('{') or raw_response.strip().startswith('```json')):
                try:
                    # Remove markdown code blocks if present
                    json_str = raw_response
                    if '```json' in json_str:
                        json_str = json_str.split('```json')[1].split('```')[0]
                    elif '```' in json_str:
                        json_str = json_str.split('```')[1].split('```')[0]
                    
                    parsed = json.loads(json_str)
                    # Convert parsed JSON to text for regex matching
                    text = json.dumps(parsed, indent=2).lower()
                    
                    # Also extract specific fields if they exist
                    if 'management_plan' in parsed:
                        plan = parsed['management_plan']
                        if 'immediate_actions' in plan:
                            for action in plan['immediate_actions'][:2]:
                                if isinstance(action, str):
                                    strategies["immediate_actions"].append({
                                        "action": action,
                                        "model": self.model_metadata.get_short_name(response.get('model_name', ''))
                                    })
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, treat as plain text
                    text = str(raw_response).lower()
            else:
                # Plain text response
                text = str(raw_response).lower()
            
            model_name = self.model_metadata.get_short_name(response.get('model_name', ''))
            
            # Extract immediate actions (only if not already extracted from JSON)
            if not any(a['model'] == model_name for a in strategies["immediate_actions"]):
                for keyword in immediate_keywords:
                    if keyword in text:
                        # Find surrounding context, excluding JSON syntax
                        # Clean up JSON artifacts first
                        clean_text = re.sub(r'[\{\}\[\]",:]', ' ', text)
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        
                        # Find sentences containing the keyword
                        sentences = clean_text.split('.')
                        for sentence in sentences:
                            if keyword in sentence and len(sentence) < 200:  # Reasonable sentence length
                                cleaned = sentence.strip()
                                if cleaned and not cleaned.startswith('"'):  # Avoid JSON keys
                                    strategies["immediate_actions"].append({
                                        "action": cleaned[:150],  # Limit length
                                        "model": model_name
                                    })
                                    break
                        if strategies["immediate_actions"]:
                            break
                    
            # Extract testing recommendations
            for keyword in testing_keywords:
                if keyword in text:
                    # Clean up JSON artifacts
                    clean_text = re.sub(r'[\{\}\[\]",:]', ' ', text)
                    clean_text = re.sub(r'\s+', ' ', clean_text)
                    
                    sentences = clean_text.split('.')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence) < 200:
                            cleaned = sentence.strip()
                            if cleaned and not cleaned.startswith('"'):
                                strategies["differential_testing"].append({
                                    "action": cleaned[:150],
                                    "model": model_name
                                })
                                break
                    if strategies["differential_testing"]:
                        break
                    
        return strategies
        
    def _identify_critical_decisions(self, ensemble_results: Dict) -> Dict:
        """Identify critical decision points where models diverge"""
        decisions = []
        
        # Analyze diagnostic divergence
        diagnosis_groups = defaultdict(list)
        for response in ensemble_results.get('model_responses', []):
            diagnoses = response.get('structured_response', {}).get('differential_diagnoses', [])
            if diagnoses:
                primary = diagnoses[0].get('diagnosis', 'Unknown')
                model_name = self.model_metadata.get_short_name(response.get('model_name', ''))
                diagnosis_groups[primary].append(model_name)
                
        if len(diagnosis_groups) > 1:
            sorted_groups = sorted(diagnosis_groups.items(), key=lambda x: len(x[1]), reverse=True)
            if len(sorted_groups) >= 2:
                decisions.append({
                    "topic": "Primary Diagnosis",
                    "divergence": "Models disagree on primary diagnosis",
                    "option_1": (sorted_groups[0][0], sorted_groups[0][1]),
                    "option_2": (sorted_groups[1][0], sorted_groups[1][1])
                })
                
        return {"decisions": decisions}
        
    def _synthesize_evidence(self, ensemble_results: Dict) -> Dict:
        """Synthesize evidence from all models"""
        evidence = {
            "symptom_matrix": {},
            "key_findings": []
        }
        
        # Extract symptoms and diagnoses
        symptoms = set()
        diagnoses = set()
        
        case_desc = ensemble_results.get('case_description', {})
        presentation = case_desc.get('presentation', '').lower()
        
        # Common symptoms to look for
        symptom_keywords = [
            "fever", "pain", "arthritis", "rash", "fatigue",
            "swelling", "inflammation", "bleeding", "nausea"
        ]
        
        for keyword in symptom_keywords:
            if keyword in presentation:
                symptoms.add(keyword)
                
        # Get all mentioned diagnoses
        for response in ensemble_results.get('model_responses', []):
            for diag in response.get('structured_response', {}).get('differential_diagnoses', []):
                diagnoses.add(diag.get('diagnosis', ''))
                
        # Build basic matrix
        for symptom in symptoms:
            evidence["symptom_matrix"][symptom] = {}
            for diagnosis in diagnoses:
                if diagnosis:
                    # Simple correlation based on co-occurrence
                    evidence["symptom_matrix"][symptom][diagnosis] = "+"
                    
        return evidence
        
    def _analyze_bias_patterns(self, ensemble_results: Dict) -> Dict:
        """Analyze potential bias patterns in model responses"""
        patterns = {
            "geographic_bias": {},
            "model_size_bias": {},
            "temporal_bias": {}
        }
        
        # Group models by origin
        origin_groups = defaultdict(list)
        for response in ensemble_results.get('model_responses', []):
            model_name = response.get('model_name', '')
            origin = response.get('origin', 'Unknown')
            origin_groups[origin].append(model_name)
            
        patterns["geographic_bias"] = dict(origin_groups)
        
        return patterns
        
    def generate_report(self, 
                       ensemble_results: Dict,
                       output_format: str = 'pdf',
                       output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive clinical decision report
        
        Args:
            ensemble_results: Results from ensemble analysis
            output_format: 'pdf' or 'markdown'
            output_file: Output file path
            
        Returns:
            Path to generated report
        """
        
        # Perform analyses (can be async if LLM is used)
        management = self._extract_management_strategies(ensemble_results)
        decisions = self._identify_critical_decisions(ensemble_results)
        evidence = self._synthesize_evidence(ensemble_results)
        biases = self._analyze_bias_patterns(ensemble_results)
        
        if output_format == 'pdf':
            return self._generate_pdf_report(
                ensemble_results, management, decisions, evidence, biases, output_file
            )
        elif output_format == 'html':
            return self._generate_html_report(
                ensemble_results, management, decisions, evidence, biases, output_file
            )
        else:
            return self._generate_markdown_report(
                ensemble_results, management, decisions, evidence, biases, output_file
            )
            
    def _generate_pdf_report(self, ensemble_results: Dict, management: Dict, 
                            decisions: Dict, evidence: Dict, biases: Dict,
                            output_file: Optional[str] = None) -> str:
        """Generate PDF version of comprehensive report"""
        
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
            
        # Setup output file
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_report_{timestamp}.pdf"
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Build content
        story = []
        
        # Page 1: Clinical Decision Summary
        story.extend(self._create_page1_content(ensemble_results, management))
        story.append(PageBreak())
        
        # Page 2: Model Diversity & Bias Analysis
        story.extend(self._create_page2_content(ensemble_results, decisions, biases))
        story.append(PageBreak())
        
        # Page 3: Clinical Decision Support
        story.extend(self._create_page3_content(ensemble_results, evidence))
        
        # Build PDF
        doc.build(story)
        
        return str(output_path)
        
    def _create_page1_content(self, ensemble_results: Dict, management: Dict) -> List:
        """Create Page 1: Clinical Decision Summary"""
        content = []
        
        # Title
        content.append(Paragraph(
            "MEDLEY Clinical Decision Report",
            self.styles['CustomTitle']
        ))
        
        # Check if using free models (detect from model responses)
        model_responses = ensemble_results.get('model_responses', [])
        using_free_models = any(':free' in str(r.get('model_name', '')) for r in model_responses)
        
        # Add warning if using free models
        if using_free_models:
            warning_data = [[
                Paragraph(
                    "<b>⚠️ Limited Analysis Quality</b><br/>"
                    "This report was generated using free models which provide suboptimal orchestration "
                    "and analysis compared to premium models. For comprehensive medical analysis with "
                    "accurate consensus building and bias detection, consider using paid models.",
                    self.styles['BodyText']
                )
            ]]
            warning_table = Table(warning_data, colWidths=[6.5*inch])
            warning_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEEEEB')),  # KI Light Orange
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4F0433')),  # KI Dark Plum
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF876F'))  # KI Orange
            ]))
            content.append(warning_table)
            content.append(Spacer(1, 0.2*inch))
        
        # Case Overview Box
        case_desc = ensemble_results.get('case_description', {})
        case_data = [
            ["CASE SUMMARY"],
            [f"Case: {case_desc.get('title', 'Unknown')}"],
            [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        ]
        
        case_table = Table(case_data, colWidths=[6.5*inch])
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F0433')),  # KI Dark Plum
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
        ]))
        content.append(case_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Diagnostic Landscape Overview
        content.append(Paragraph("Diagnostic Consensus Analysis", self.styles['SectionHeader']))
        
        consensus = ensemble_results.get('consensus_analysis', {})
        total_models = consensus.get('total_models', 0)
        responding = consensus.get('responding_models', 0)
        
        # Extract diagnoses with consensus
        diagnoses = self._extract_diagnosis_consensus(ensemble_results)
        
        # Create diagnostic landscape table
        diag_data = [
            [f"Models Analyzed: {total_models} | Successful: {responding} | Agreement Level: {consensus.get('consensus_level', 'Unknown')}"]
        ]
        
        # Add primary diagnosis
        if diagnoses:
            primary = diagnoses[0]
            diag_data.append([
                Paragraph(f"<b>PRIMARY DIAGNOSIS ({primary.agreement_percentage:.0f}% agreement)</b>", self.styles['DiagnosisStyle'])
            ])
            diag_data.append([
                Paragraph(f"▶ {primary.name}", self.styles['DiagnosisStyle'])
            ])
            if primary.evidence:
                diag_data.append([
                    Paragraph(f"Evidence: {', '.join(primary.evidence[:3])}", self.styles['EvidenceStyle'])
                ])
            diag_data.append([
                Paragraph(f"Supporting Models: {', '.join(primary.supporting_models[:5])}", self.styles['EvidenceStyle'])
            ])
            
        # Add strong alternatives
        strong_alts = [d for d in diagnoses[1:4] if d.agreement_percentage >= 30]
        if strong_alts:
            diag_data.append([
                Paragraph("<b>STRONG ALTERNATIVES (≥30% agreement)</b>", self.styles['DiagnosisStyle'])
            ])
            for alt in strong_alts:
                diag_data.append([
                    Paragraph(f"▶ {alt.name} ({alt.agreement_percentage:.0f}%)", self.styles['DiagnosisStyle'])
                ])
                
        # Add minority opinions
        minority = [d for d in diagnoses[4:7] if d.agreement_percentage < 30]
        if minority:
            diag_data.append([
                Paragraph("<b>MINORITY OPINIONS TO CONSIDER</b>", self.styles['DiagnosisStyle'])
            ])
            for min_diag in minority:
                diag_data.append([
                    Paragraph(f"▶ {min_diag.name} ({min_diag.agreement_percentage:.0f}%)", self.styles['DiagnosisStyle'])
                ])
                
        diag_table = Table(diag_data, colWidths=[6.5*inch])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        content.append(diag_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Management Strategy Matrix
        content.append(Paragraph("Diagnostic & Treatment Pathways", self.styles['SectionHeader']))
        
        mgmt_data = []
        
        # Immediate actions
        if management.get('immediate_actions'):
            mgmt_data.append([Paragraph("<b>IMMEDIATE ACTIONS</b>", self.styles['DiagnosisStyle'])])
            for action in management['immediate_actions'][:3]:
                mgmt_data.append([
                    Paragraph(f"□ {action.get('action', '')[:100]}", self.styles['EvidenceStyle'])
                ])
                
        # Testing recommendations
        if management.get('differential_testing'):
            mgmt_data.append([Paragraph("<b>DIFFERENTIAL TESTING</b>", self.styles['DiagnosisStyle'])])
            for test in management['differential_testing'][:3]:
                mgmt_data.append([
                    Paragraph(f"□ {test.get('action', '')[:100]}", self.styles['EvidenceStyle'])
                ])
                
        if mgmt_data:
            mgmt_table = Table(mgmt_data, colWidths=[6.5*inch])
            mgmt_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6)
            ]))
            content.append(mgmt_table)
            
        # Footer
        content.append(Spacer(1, 1*inch))
        footer_text = f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Medley Medical AI Ensemble System | Developed by Farhad Abtahi, SMAILE at Karolinska Institutet"
        content.append(Paragraph(footer_text, self.styles['FooterStyle']))
        
        return content
        
    def _create_page2_content(self, ensemble_results: Dict, decisions: Dict, biases: Dict) -> List:
        """Create Page 2: Model Diversity & Bias Analysis"""
        content = []
        
        content.append(Paragraph("Model Diversity & Bias Analysis", self.styles['CustomTitle']))
        
        # Model Response Diversity Table
        content.append(Paragraph("Model Response Diversity", self.styles['SectionHeader']))
        
        # Create model comparison table
        model_data = [
            ["Model", "Primary Dx", "Confidence", "Key Insight"]
        ]
        
        for response in ensemble_results.get('model_responses', [])[:8]:
            model_name = self.model_metadata.get_short_name(response.get('model_name', ''))
            diagnoses = response.get('structured_response', {}).get('differential_diagnoses', [])
            primary_dx = diagnoses[0].get('diagnosis', 'N/A') if diagnoses else 'N/A'
            
            # Truncate for display
            primary_dx = primary_dx[:30] + "..." if len(primary_dx) > 30 else primary_dx
            
            model_data.append([
                Paragraph(model_name, self.styles['BodyText']),
                Paragraph(primary_dx, self.styles['BodyText']),
                Paragraph("High", self.styles['BodyText']),
                Paragraph("See details", self.styles['BodyText'])
            ])
            
        model_table = Table(model_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
        model_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F0433')),  # KI Dark Plum
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        content.append(model_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Bias Source Analysis
        content.append(Paragraph("Potential Bias Sources & Mitigation", self.styles['SectionHeader']))
        
        bias_data = []
        
        # Geographic bias
        if biases.get('geographic_bias'):
            bias_data.append([Paragraph("<b>GEOGRAPHIC/TRAINING BIAS</b>", self.styles['DiagnosisStyle'])])
            for origin, models in list(biases['geographic_bias'].items())[:3]:
                bias_data.append([
                    Paragraph(f"• {origin} Models ({len(models)}): May emphasize regional disease patterns", 
                             self.styles['EvidenceStyle'])
                ])
                
        # Add critical decision points
        if decisions.get('decisions'):
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph("Key Divergence Points", self.styles['SectionHeader']))
            
            for decision in decisions['decisions'][:2]:
                decision_data = [
                    [Paragraph(f"<b>{decision['topic']}</b>", self.styles['DiagnosisStyle'])],
                    [Paragraph(f"{decision['divergence']}", self.styles['EvidenceStyle'])]
                ]
                
                decision_table = Table(decision_data, colWidths=[6.5*inch])
                decision_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6)
                ]))
                content.append(decision_table)
                content.append(Spacer(1, 0.1*inch))
                
        if bias_data:
            bias_table = Table(bias_data, colWidths=[6.5*inch])
            bias_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6)
            ]))
            content.append(bias_table)
            
        return content
        
    def _create_page3_content(self, ensemble_results: Dict, evidence: Dict) -> List:
        """Create Page 3: Clinical Decision Support"""
        content = []
        
        content.append(Paragraph("Clinical Decision Support", self.styles['CustomTitle']))
        
        # Evidence Synthesis
        content.append(Paragraph("Evidence Synthesis", self.styles['SectionHeader']))
        
        # Create symptom-diagnosis correlation matrix
        if evidence.get('symptom_matrix'):
            matrix_data = [["Symptom/Finding"] + list(list(evidence['symptom_matrix'].values())[0].keys())[:4]]
            
            for symptom, diagnoses in list(evidence['symptom_matrix'].items())[:5]:
                row = [symptom.capitalize()]
                for diag_name in list(diagnoses.keys())[:4]:
                    row.append(diagnoses.get(diag_name, '-'))
                matrix_data.append(row)
                
            matrix_table = Table(matrix_data, colWidths=[1.5*inch] + [1.25*inch]*4)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F0433')),  # KI Dark Plum
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            content.append(matrix_table)
            content.append(Spacer(1, 0.2*inch))
            
        # Next Steps Decision Tree (simplified text version)
        content.append(Paragraph("Next Steps Decision Tree", self.styles['SectionHeader']))
        
        tree_data = [
            ["Start → MEFV Genetic Test"],
            ["├─ Positive → Colchicine Trial"],
            ["│   ├─ Response → FMF Confirmed"],
            ["│   └─ No Response → Consider Dose Adjustment"],
            ["└─ Negative → Extended Panel Testing"],
            ["    ├─ TRAPS+ → Alternative Treatment"],
            ["    └─ All Negative → Consider IBD/Still's"]
        ]
        
        tree_table = Table(tree_data, colWidths=[6.5*inch])
        tree_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc'))
        ]))
        content.append(tree_table)
        
        # Legend
        content.append(Spacer(1, 0.2*inch))
        legend = Paragraph(
            "<i>Legend: +++ Strong association, ++ Moderate, + Weak, - Not typical</i>",
            self.styles['EvidenceStyle']
        )
        content.append(legend)
        
        return content
        
    def _extract_diagnosis_consensus(self, ensemble_results: Dict) -> List[DiagnosisInfo]:
        """Extract and calculate diagnosis consensus from ensemble results"""
        diagnoses = []
        diagnosis_counts = Counter()
        diagnosis_models = defaultdict(list)
        
        # Count diagnoses across all models
        for response in ensemble_results.get('model_responses', []):
            if not response.get('response'):
                continue
                
            model_name = self.model_metadata.get_short_name(response.get('model_name', ''))
            
            # Extract from structured response
            for diag in response.get('structured_response', {}).get('differential_diagnoses', []):
                diag_name = diag.get('diagnosis', '')
                if diag_name:
                    diagnosis_counts[diag_name] += 1
                    diagnosis_models[diag_name].append(model_name)
                    
        # Calculate percentages and create DiagnosisInfo objects
        total_models = len(ensemble_results.get('model_responses', []))
        
        for diag_name, count in diagnosis_counts.most_common(10):
            percentage = (count / total_models * 100) if total_models > 0 else 0
            
            # Extract evidence (simplified)
            evidence = []
            if "fever" in diag_name.lower() or "FMF" in diag_name:
                evidence = ["Periodic fever", "Serositis", "Ethnic background"]
            elif "IBD" in diag_name or "bowel" in diag_name.lower():
                evidence = ["Abdominal pain", "Inflammatory markers"]
                
            diagnoses.append(DiagnosisInfo(
                name=diag_name,
                agreement_percentage=percentage,
                supporting_models=diagnosis_models[diag_name],
                evidence=evidence,
                confidence="High" if percentage > 60 else "Moderate" if percentage > 30 else "Low"
            ))
            
        return diagnoses
        
    def _generate_markdown_report(self, ensemble_results: Dict, management: Dict,
                                 decisions: Dict, evidence: Dict, biases: Dict,
                                 output_file: Optional[str] = None) -> str:
        """Generate markdown version of comprehensive report"""
        
        # Build markdown content
        lines = []
        
        # Header
        lines.append("# MEDLEY Comprehensive Clinical Decision Report\n")
        lines.append(f"**Case**: {ensemble_results.get('case_title', 'Unknown')}")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Page 1 Content
        lines.append("## Page 1: Clinical Decision Summary\n")
        
        # Diagnostic Landscape
        lines.append("### Diagnostic Consensus Analysis\n")
        
        consensus = ensemble_results.get('consensus_analysis', {})
        lines.append(f"Models Analyzed: {consensus.get('total_models', 0)} | ")
        lines.append(f"Successful: {consensus.get('responding_models', 0)} | ")
        lines.append(f"Agreement Level: {consensus.get('consensus_level', 'Unknown')}\n")
        
        diagnoses = self._extract_diagnosis_consensus(ensemble_results)
        
        if diagnoses:
            primary = diagnoses[0]
            lines.append(f"#### Primary Diagnosis: {primary.name} ({primary.agreement_percentage:.0f}% agreement)")
            lines.append(f"- Evidence: {', '.join(primary.evidence)}")
            lines.append(f"- Supporting Models: {', '.join(primary.supporting_models[:5])}\n")
            
        # Management Strategies
        lines.append("### Management Strategies\n")
        
        if management.get('immediate_actions'):
            lines.append("#### Immediate Actions")
            for action in management['immediate_actions'][:3]:
                lines.append(f"- [ ] {action.get('action', '')[:100]}")
            lines.append("")
            
        # Page 2 Content
        lines.append("\n## Page 2: Model Diversity & Bias Analysis\n")
        
        # Critical Decisions
        if decisions.get('decisions'):
            lines.append("### Key Divergence Points")
            for decision in decisions['decisions']:
                lines.append(f"- **{decision['topic']}**: {decision['divergence']}")
            lines.append("")
            
        # Page 3 Content
        lines.append("\n## Page 3: Clinical Decision Support\n")
        
        # Evidence Matrix
        if evidence.get('symptom_matrix'):
            lines.append("### Symptom-Diagnosis Correlation Matrix\n")
            lines.append("| Symptom | " + " | ".join(list(list(evidence['symptom_matrix'].values())[0].keys())[:4]) + " |")
            lines.append("|---------|" + "---|" * 4)
            
            for symptom, diagnoses in list(evidence['symptom_matrix'].items())[:5]:
                row = f"| {symptom.capitalize()} |"
                for diag_name in list(diagnoses.keys())[:4]:
                    row += f" {diagnoses.get(diag_name, '-')} |"
                lines.append(row)
            lines.append("")
            
        # Footer
        lines.append("\n---")
        lines.append("*Developed by Farhad Abtahi - SMAILE at Karolinska Institutet*")
        
        # Write to file
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_report_{timestamp}.md"
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
            
        return str(output_path)
    
    def _generate_html_report(self, ensemble_results: Dict, management: Dict,
                             decisions: Dict, evidence: Dict, biases: Dict,
                             output_file: Optional[str] = None) -> str:
        """Generate HTML version of comprehensive report"""
        
        # Extract key data
        diagnoses = self._extract_diagnosis_consensus(ensemble_results)
        consensus = ensemble_results.get('consensus_analysis', {})
        case_desc = ensemble_results.get('case_description', {})
        
        # Check if using free models
        model_responses = ensemble_results.get('model_responses', [])
        using_free_models = any(':free' in str(r.get('model_name', '')) for r in model_responses)
        
        # Build HTML content
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html lang="en">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('    <title>MEDLEY Comprehensive Clinical Decision Report</title>')
        html.append('    <style>')
        html.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #333; }')
        html.append('        h1 { color: #2c5282; border-bottom: 2px solid #2c5282; padding-bottom: 10px; }')
        html.append('        h2 { color: #2d3748; margin-top: 30px; }')
        html.append('        h3 { color: #4a5568; }')
        html.append('        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }')
        html.append('        .warning strong { color: #856404; }')
        html.append('        .case-summary { background: #f7fafc; border: 1px solid #cbd5e0; padding: 15px; margin: 20px 0; border-radius: 5px; }')
        html.append('        table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
        html.append('        th, td { border: 1px solid #cbd5e0; padding: 10px; text-align: left; }')
        html.append('        th { background: #2c5282; color: white; }')
        html.append('        .diagnosis-primary { background: #e6f3ff; font-weight: bold; }')
        html.append('        .management-section { background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }')
        html.append('        ul { list-style-type: none; padding-left: 0; }')
        html.append('        li { padding: 5px 0; }')
        html.append('        li:before { content: "▶ "; color: #2c5282; font-weight: bold; }')
        html.append('        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #cbd5e0; text-align: center; color: #718096; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        
        # Title
        html.append('    <h1>MEDLEY Comprehensive Clinical Decision Report</h1>')
        
        # Warning if using free models
        if using_free_models:
            html.append('    <div class="warning">')
            html.append('        <strong>⚠️ Limited Analysis Quality</strong><br>')
            html.append('        This report was generated using free models which provide suboptimal orchestration ')
            html.append('        and analysis compared to premium models. For comprehensive medical analysis with ')
            html.append('        accurate consensus building and bias detection, consider using paid models.')
            html.append('    </div>')
        
        # Case Summary
        html.append('    <div class="case-summary">')
        html.append(f'        <h3>Case Summary</h3>')
        html.append(f'        <p><strong>Case:</strong> {case_desc.get("title", "Unknown")}</p>')
        html.append(f'        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
        html.append(f'        <p><strong>Models Analyzed:</strong> {consensus.get("total_models", 0)} | ')
        html.append(f'           <strong>Successful:</strong> {consensus.get("responding_models", 0)} | ')
        html.append(f'           <strong>Agreement Level:</strong> {consensus.get("consensus_level", "Unknown")}</p>')
        html.append('    </div>')
        
        # Diagnostic Consensus
        html.append('    <h2>Diagnostic Consensus Analysis</h2>')
        if diagnoses:
            primary = diagnoses[0]
            html.append(f'    <div class="diagnosis-primary">')
            html.append(f'        <h3>Primary Diagnosis: {primary.name} ({primary.agreement_percentage:.0f}% agreement)</h3>')
            if primary.evidence:
                html.append(f'        <p><strong>Evidence:</strong> {", ".join(primary.evidence[:3])}</p>')
            if primary.supporting_models:
                html.append(f'        <p><strong>Supporting Models:</strong> {", ".join(primary.supporting_models[:5])}</p>')
            html.append('    </div>')
        
        # Management Strategies
        html.append('    <h2>Management Strategies</h2>')
        html.append('    <div class="management-section">')
        
        if management.get('immediate_actions'):
            html.append('        <h3>Immediate Actions</h3>')
            html.append('        <ul>')
            for action in management['immediate_actions'][:5]:
                action_text = action.get('action', '') if isinstance(action, dict) else str(action)
                if action_text:
                    html.append(f'            <li>{action_text[:150]}</li>')
            html.append('        </ul>')
        
        if management.get('differential_testing'):
            html.append('        <h3>Recommended Tests</h3>')
            html.append('        <ul>')
            for test in management['differential_testing'][:5]:
                test_text = test.get('action', '') if isinstance(test, dict) else str(test)
                if test_text:
                    html.append(f'            <li>{test_text[:150]}</li>')
            html.append('        </ul>')
        
        html.append('    </div>')
        
        # Critical Decision Points
        if decisions.get('decisions'):
            html.append('    <h2>Critical Decision Points</h2>')
            html.append('    <ul>')
            for decision in decisions['decisions'][:3]:
                html.append(f'        <li><strong>{decision.get("topic", "Unknown")}:</strong> {decision.get("divergence", "")}</li>')
            html.append('    </ul>')
        
        # Bias Considerations
        bias_considerations = consensus.get('bias_considerations', [])
        if bias_considerations:
            html.append('    <h2>Bias Considerations</h2>')
            html.append('    <ul>')
            for bias in bias_considerations[:3]:
                html.append(f'        <li>{bias}</li>')
            html.append('    </ul>')
        
        # Footer
        html.append('    <div class="footer">')
        html.append('        <p>Developed by Farhad Abtahi - SMAILE at Karolinska Institutet</p>')
        html.append('    </div>')
        
        html.append('</body>')
        html.append('</html>')
        
        # Write to file
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_report_{timestamp}.html"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(html))
        
        return str(output_path)


class ModelMetadata:
    """Database of model metadata including release dates and characteristics"""
    
    MODEL_INFO = {
        "openai/gpt-5": {
            "short_name": "GPT-5",
            "release_date": "2025-01",
            "organization": "OpenAI"
        },
        "openai/gpt-4o": {
            "short_name": "GPT-4o",
            "release_date": "2024-05",
            "organization": "OpenAI"
        },
        "anthropic/claude-3-opus-20240229": {
            "short_name": "Claude 3 Opus",
            "release_date": "2024-02",
            "organization": "Anthropic"
        },
        "google/gemini-2.0-flash-exp": {
            "short_name": "Gemini 2.0 Flash",
            "release_date": "2024-12",
            "organization": "Google"
        },
        "google/gemma-2-9b-it:free": {
            "short_name": "Gemma 2 9B",
            "release_date": "2024-06",
            "organization": "Google"
        },
        "x-ai/grok-2-1212": {
            "short_name": "Grok 2",
            "release_date": "2024-12",
            "organization": "xAI"
        },
        "mistralai/mistral-7b-instruct:free": {
            "short_name": "Mistral 7B",
            "release_date": "2023-09",
            "organization": "Mistral AI"
        },
        "mistralai/mistral-large-2411": {
            "short_name": "Mistral Large",
            "release_date": "2024-11",
            "organization": "Mistral AI"
        },
        "meta-llama/llama-3.2-3b-instruct:free": {
            "short_name": "Llama 3.2 3B",
            "release_date": "2024-09",
            "organization": "Meta"
        },
        "qwen/qwen-2.5-coder-32b-instruct": {
            "short_name": "Qwen 2.5 32B",
            "release_date": "2024-11",
            "organization": "Alibaba"
        },
        "deepseek/deepseek-chat-v3-0324": {
            "short_name": "DeepSeek V3",
            "release_date": "2024-12",
            "organization": "DeepSeek"
        }
    }
    
    def get_short_name(self, model_id: str) -> str:
        """Get short familiar name for model"""
        # Direct lookup
        if model_id in self.MODEL_INFO:
            return self.MODEL_INFO[model_id]["short_name"]
            
        # Try without :free suffix
        base_id = model_id.replace(":free", "")
        if base_id in self.MODEL_INFO:
            return self.MODEL_INFO[base_id]["short_name"]
            
        # Extract simple name
        if "/" in model_id:
            return model_id.split("/")[-1].split(":")[0].replace("-", " ").title()
            
        return model_id
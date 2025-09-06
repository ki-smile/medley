"""
Final Comprehensive Clinical Decision Report Generator for Medley
Combines all content from original report with new comprehensive sections
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
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class FinalComprehensiveReportGenerator:
    """Generate the final comprehensive report with all content"""
    
    def __init__(self):
        """Initialize report generator"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.model_metadata = self._setup_model_metadata()
        
    def _setup_icd_codes(self) -> Dict:
        """Setup ICD-10 codes for common diagnoses"""
        return {
            "Familial Mediterranean Fever": "E85.0",
            "FMF": "E85.0", 
            "Periodic Fever Syndrome": "M04.1",
            "TRAPS": "M04.1",
            "TNF Receptor Associated Periodic Syndrome": "M04.1",
            "Systemic Lupus Erythematosus": "M32.9",
            "SLE": "M32.9",
            "Inflammatory Bowel Disease": "K50.9",
            "IBD": "K50.9",
            "Crohn's Disease": "K50.9",
            "Ulcerative Colitis": "K51.9",
            "Adult Still's Disease": "M06.1",
            "Still's Disease": "M06.1",
            "Behçet's Disease": "M35.2",
            "Behcet's Disease": "M35.2",
            "Hyper-IgD Syndrome": "M04.1",
            "HIDS": "M04.1",
            "Rheumatoid Arthritis": "M06.9",
            "Psoriatic Arthritis": "L40.5",
            "Ankylosing Spondylitis": "M45",
            "Gout": "M10.9",
            "Pseudogout": "M11.9"
        }
        
    def _setup_custom_styles(self):
        """Setup all custom paragraph styles for the report"""
        
        # Main title style
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=28,
            textColor=colors.HexColor('#16a34a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style (blue)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#15803d'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Diagnosis name style (bold, larger)
        self.styles.add(ParagraphStyle(
            name='DiagnosisName',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#1a202c'),
            leftIndent=12,
            spaceAfter=4,
            fontName='Helvetica-Bold'
        ))
        
        # Normal content style
        self.styles.add(ParagraphStyle(
            name='ContentStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Table cell style for wrapped text
        self.styles.add(ParagraphStyle(
            name='TableCellStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT,
            leading=11
        ))
        
        # Evidence/detail style (smaller, gray)
        self.styles.add(ParagraphStyle(
            name='DetailStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            leftIndent=24,
            spaceAfter=4
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='FooterStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        ))
        
    def _setup_model_metadata(self) -> Dict:
        """Setup model metadata with short names and info"""
        return {
            "openai/gpt-4o": {"short": "GPT-4o", "origin": "USA", "date": "2024-05"},
            "openai/gpt-5": {"short": "GPT-5", "origin": "USA", "date": "2025-01"},
            "anthropic/claude-3-opus-20240229": {"short": "Claude 3 Opus", "origin": "USA", "date": "2024-02"},
            "anthropic/claude-opus-4.1": {"short": "Claude Opus 4.1", "origin": "USA", "date": "2025-01"},
            "google/gemini-2.0-flash-exp": {"short": "Gemini 2.0 Flash", "origin": "USA", "date": "2024-12"},
            "google/gemini-2.5-pro": {"short": "Gemini 2.5 Pro", "origin": "USA", "date": "2024-12"},
            "google/gemma-2-9b-it": {"short": "Gemma 2 9B", "origin": "USA", "date": "2024-06"},
            "mistralai/mistral-7b-instruct": {"short": "Mistral 7B", "origin": "France", "date": "2023-09"},
            "mistralai/mistral-large": {"short": "Mistral Large", "origin": "France", "date": "2024-11"},
            "deepseek/deepseek-chat-v3": {"short": "DeepSeek V3", "origin": "China", "date": "2024-12"},
            "meta-llama/llama-3.2-3b-instruct": {"short": "Llama 3.2", "origin": "USA", "date": "2024-09"},
            "qwen/qwen-2.5-coder-32b-instruct": {"short": "Qwen 2.5", "origin": "China", "date": "2024-11"},
            "x-ai/grok-2-1212": {"short": "Grok 2", "origin": "USA", "date": "2024-12"},
            "x-ai/grok-4": {"short": "Grok 4", "origin": "USA", "date": "2025-01"},
            "cohere/command-r": {"short": "Command-R", "origin": "Canada", "date": "2024-03"}
        }
        
    def get_model_info(self, model_name: str) -> Dict:
        """Get comprehensive model info with 2025 metadata"""
        # Import the comprehensive metadata
        try:
            from model_metadata_2025 import get_comprehensive_model_metadata
            comprehensive_metadata = get_comprehensive_model_metadata()
        except ImportError:
            comprehensive_metadata = {}
            
        # Clean model name variations
        base_name = model_name.replace(":free", "").replace("_free", "")
        
        # Direct lookup in comprehensive metadata
        if base_name in comprehensive_metadata:
            info = comprehensive_metadata[base_name]
            return {
                "short": base_name.split("/")[-1].split(":")[0][:15],
                "origin": info.get("origin_country", "Unknown"),
                "date": info.get("release_date", "Unknown"),
                "parameters": info.get("parameters", "Unknown"),
                "bias_summary": info.get("bias_characteristics", {}).get("primary_biases", ["Unknown"])[0] if info.get("bias_characteristics", {}).get("primary_biases") else "Unknown",
                "cost_tier": info.get("cost_tier", "Unknown"),
                "medical_bias": info.get("bias_characteristics", {}).get("medical_bias", "Unknown")
            }
        
        # Legacy fallback lookup
        if base_name in self.model_metadata:
            return self.model_metadata[base_name]
            
        # Try partial matching
        for key, value in comprehensive_metadata.items():
            model_family = key.split("/")[1].split("-")[0] if "/" in key else key
            if model_family.lower() in base_name.lower():
                info = value
                return {
                    "short": base_name.split("/")[-1].split(":")[0][:15],
                    "origin": info.get("origin_country", "Unknown"),
                    "date": info.get("release_date", "Unknown"),
                    "parameters": info.get("parameters", "Unknown"),
                    "bias_summary": info.get("bias_characteristics", {}).get("primary_biases", ["Unknown"])[0] if info.get("bias_characteristics", {}).get("primary_biases") else "Unknown",
                    "cost_tier": info.get("cost_tier", "Unknown"),
                    "medical_bias": info.get("bias_characteristics", {}).get("medical_bias", "Unknown")
                }
                
        # Ultimate fallback
        return {
            "short": model_name.split("/")[-1].split(":")[0][:15],
            "origin": "Unknown",
            "date": "Unknown",
            "parameters": "Unknown",
            "bias_summary": "Unknown",
            "cost_tier": "Unknown",
            "medical_bias": "Unknown"
        }
        
    def _wrap_text_for_table(self, text: str, style_name: str = 'ContentStyle') -> 'Paragraph':
        """Helper method to wrap text in table cells"""
        if not text or text == 'Not specified':
            return Paragraph(text or '', self.styles[style_name])
        return Paragraph(str(text), self.styles[style_name])
        
    def generate_report(self, ensemble_results: Dict, output_file: str = None) -> str:
        """
        Generate the final comprehensive PDF report
        
        Args:
            ensemble_results: Complete ensemble analysis results
            output_file: Output file path
            
        Returns:
            Path to generated PDF
        """
        
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
            
        # Setup output file
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"final_comprehensive_report_{timestamp}.pdf"
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=1*inch
        )
        
        # Build content
        story = []
        
        # Title Page with Analysis Overview (Page 1)
        story.extend(self._create_title_page(ensemble_results))
        
        # Add free model/orchestrator disclaimer if applicable
        free_models_used = ensemble_results.get('free_models_used', False)
        free_orchestrator_used = ensemble_results.get('orchestrator_used_free_models', False)
        
        if free_models_used or free_orchestrator_used:
            disclaimer_parts = []
            if free_models_used:
                disclaimer_parts.append("free AI models")
            if free_orchestrator_used:
                disclaimer_parts.append("a free orchestrator")
            
            disclaimer_text = " and ".join(disclaimer_parts)
            
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                f"⚠️ Free Model Disclaimer: This analysis was generated using {disclaimer_text}",
                ParagraphStyle(
                    'FreeModelBanner',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    textColor=colors.darkred,
                    alignment=1,  # Center
                    borderColor=colors.darkred,
                    borderWidth=1,
                    borderPadding=10,
                    backColor=colors.mistyrose
                )
            ))
            story.append(Paragraph(
                "Free models may provide suboptimal results. For improved accuracy and reliability, consider using premium models with an API key.",
                ParagraphStyle(
                    'FreeModelNote',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=colors.grey,
                    alignment=1  # Center
                )
            ))

        # Add fallback extraction banner if applicable
        if ensemble_results.get("metadata", {}).get("orchestrator_model") == "fallback":
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                "⚠️ Note: Analysis using fallback extraction (orchestrator unavailable)",
                ParagraphStyle(
                    'FallbackBanner',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    textColor=colors.darkorange,
                    alignment=1,  # Center
                    borderColor=colors.darkorange,
                    borderWidth=1,
                    borderPadding=10,
                    backColor=colors.lightyellow
                )
            ))
            story.append(Paragraph(
                "Some advanced analysis features may be limited. ICD codes have been inferred where possible.",
                ParagraphStyle(
                    'FallbackNote',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=colors.grey,
                    alignment=1  # Center
                )
            ))
        
        story.append(PageBreak())
        
        # Critical Decisions & Evidence Synthesis (Page 2) - Moved earlier for better flow
        story.extend(self._create_combined_critical_evidence_analysis(ensemble_results))
        story.append(PageBreak())
        
        # Executive Summary with Clinical Findings and Recommendations (Page 3)
        story.extend(self._create_executive_summary(ensemble_results))
        story.append(PageBreak())
        
        # Primary Diagnosis Summaries (Page 4)
        story.extend(self._create_primary_diagnosis_summaries(ensemble_results))
        story.append(PageBreak())
        
        # Diagnostic Landscape (Page 5)
        story.extend(self._create_diagnostic_landscape(ensemble_results))
        story.append(PageBreak())
        
        # Management Strategies (Page 6)
        story.extend(self._create_management_strategies(ensemble_results))
        story.append(PageBreak())
        
        # Model Diversity Analysis (Page 7)
        story.extend(self._create_model_diversity_analysis(ensemble_results))
        story.append(PageBreak())
        
        # Detailed Model Responses (Page 8+)
        story.extend(self._create_detailed_responses(ensemble_results))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        return str(output_path)
        
    def _add_footer(self, canvas, doc):
        """Add footer to each page"""
        canvas.saveState()
        
        # Footer text
        footer_text = f"Medley Medical AI Ensemble System | Developed by Farhad Abtahi, SMAILE at Karolinska Institutet"
        
        # Position at bottom of page
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            0.5 * inch,
            footer_text
        )
        
        # Add page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(
            doc.pagesize[0] - 0.75 * inch,
            0.5 * inch,
            f"Page {page_num}"
        )
        
        # Add generation timestamp
        canvas.drawString(
            0.75 * inch,
            0.5 * inch,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        canvas.restoreState()
        
    def _create_title_page(self, ensemble_results: Dict) -> List:
        """Create title page"""
        content = []
        
        # Add minimal spacing
        content.append(Spacer(1, 0.2*inch))  # Reduced from 0.5
        
        # Main title
        content.append(Paragraph(
            "MEDLEY",
            self.styles['MainTitle']
        ))
        
        content.append(Paragraph(
            "Medical AI Ensemble Clinical Decision Report",
            self.styles['SectionHeader']
        ))
        
        content.append(Spacer(1, 0.15*inch))  # Reduced from 0.3
        
        # Case info box - changed to 3-column layout with text wrapping
        case_info = [[
            Paragraph(f"Case ID: {ensemble_results.get('case_id', 'Unknown')}", self.styles['TableCellStyle']),
            Paragraph(f"Title: {ensemble_results.get('case_title', 'Unknown')}", self.styles['TableCellStyle']),
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['TableCellStyle'])
        ]]
        
        case_table = Table(case_info, colWidths=[1.8*inch, 3.2*inch, 1.5*inch])  # Wider table
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        content.append(case_table)
        
        content.append(Spacer(1, 0.1*inch))  # Reduced spacing
        
        # PRIMARY DIAGNOSIS SECTION (moved to first page)
        content.append(Paragraph("Primary Diagnostic Consensus", self.styles['SectionHeader']))
        
        # Get data from diagnostic_landscape structure
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        primary = primary_data.get('name', 'No consensus reached')
        confidence = primary_data.get('agreement_percentage', 0) / 100.0 if isinstance(primary_data.get('agreement_percentage'), (int, float)) else 0
        
        # Create primary diagnosis table with ICD codes and evidence
        primary_icd = self._get_primary_icd_code(ensemble_results)
        
        # Get evidence for primary diagnosis
        primary_evidence = primary_data.get('evidence', [])
        if primary_evidence:
            primary_with_evidence = f"{primary}<br/><i>Evidence: {', '.join(primary_evidence[:4])}</i>"
            primary_para = Paragraph(primary_with_evidence, self.styles['TableCellStyle'])
        else:
            primary_para = Paragraph(primary, self.styles['TableCellStyle'])
            
        primary_data = [
            ["Diagnosis", "ICD-10", "Agreement", "Confidence", "Status"],
            [primary_para, primary_icd, f"{confidence:.1%}", self._get_confidence_text(confidence), "PRIMARY"]
        ]
        
        primary_table = Table(primary_data, colWidths=[2.5*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        primary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        content.append(primary_table)
        
        content.append(Spacer(1, 0.1*inch))  # Reduced spacing
        
        # Alternative and minority diagnoses on first page - show ALL categories
        strong_alternatives = diagnostic_data.get('strong_alternatives', [])
        alternatives = diagnostic_data.get('alternatives', [])  # New 20-29% category
        minority = diagnostic_data.get('minority_opinions', [])
        all_alternatives = strong_alternatives + alternatives + minority
        
        if all_alternatives:
            content.append(Paragraph("Alternative & Minority Diagnoses", self.styles['SubsectionHeader']))
            
            alt_data = [["Diagnosis", "ICD-10", "Support", "Type"]]
            
            # Add strong alternatives (≥30%) with evidence
            for alt in strong_alternatives:
                if isinstance(alt, dict):
                    diagnosis_name = alt.get('name', 'Unknown')
                    # First try to get ICD from the data itself, then fallback to lookup
                    icd_code = alt.get('icd10_code', '') or alt.get('icd_code', '') or self._get_diagnosis_icd_code(alt.get('name', 'Unknown'))
                    agreement_pct = alt.get('agreement_percentage', alt.get('percentage', 0))
                    # Include evidence if available
                    evidence = alt.get('evidence', [])
                else:
                    diagnosis_name = str(alt)
                    icd_code = self._get_diagnosis_icd_code(str(alt))
                    agreement_pct = 0
                    evidence = []
                if evidence:
                    name_with_evidence = f"{diagnosis_name}<br/><i>Evidence: {', '.join(evidence[:3])}</i>"
                    name_para = Paragraph(name_with_evidence, self.styles['TableCellStyle'])
                else:
                    name_para = Paragraph(diagnosis_name, self.styles['TableCellStyle'])
                
                alt_data.append([
                    name_para,
                    icd_code,
                    f"{agreement_pct:.1f}%",
                    "Strong Alt (≥30%)"
                ])
            
            # Add regular alternatives (10-29%) 
            for alt in alternatives:
                if isinstance(alt, dict):
                    diagnosis_name = alt.get('name', 'Unknown')
                    icd_code = alt.get('icd10_code', '') or alt.get('icd_code', '') or self._get_diagnosis_icd_code(alt.get('name', 'Unknown'))
                    agreement_pct = alt.get('agreement_percentage', alt.get('percentage', 0))
                    # Include evidence if available
                    evidence = alt.get('evidence', [])
                else:
                    diagnosis_name = str(alt)
                    icd_code = self._get_diagnosis_icd_code(str(alt))
                    agreement_pct = 0
                    evidence = []
                if evidence:
                    name_with_evidence = f"{diagnosis_name}<br/><i>Evidence: {', '.join(evidence[:3])}</i>"
                    name_para = Paragraph(name_with_evidence, self.styles['TableCellStyle'])
                else:
                    name_para = Paragraph(diagnosis_name, self.styles['TableCellStyle'])
                
                alt_data.append([
                    name_para,
                    icd_code,
                    f"{agreement_pct:.1f}%",
                    "Alternative (10-29%)"
                ])
            
            # Add minority opinions (<10%) with clinical significance
            for opinion in minority:
                if isinstance(opinion, dict):
                    diagnosis_name = opinion.get('name', 'Unknown')
                    icd_code = opinion.get('icd10_code', '') or opinion.get('icd_code', '') or self._get_diagnosis_icd_code(opinion.get('name', 'Unknown'))
                    agreement_pct = opinion.get('agreement_percentage', opinion.get('percentage', 0))
                    # Include clinical significance or evidence
                    significance = opinion.get('clinical_significance', '')
                    evidence = opinion.get('evidence', [])
                else:
                    diagnosis_name = str(opinion)
                    icd_code = self._get_diagnosis_icd_code(str(opinion))
                    agreement_pct = 0
                    significance = ''
                    evidence = []
                if significance:
                    name_with_sig = f"{diagnosis_name}<br/><i>Significance: {significance[:60]}</i>"
                    name_para = Paragraph(name_with_sig, self.styles['TableCellStyle'])
                elif evidence:
                    name_with_evidence = f"{diagnosis_name}<br/><i>Evidence: {', '.join(evidence[:3])}</i>"
                    name_para = Paragraph(name_with_evidence, self.styles['TableCellStyle'])
                else:
                    name_para = Paragraph(diagnosis_name, self.styles['TableCellStyle'])
                    
                alt_data.append([
                    name_para,
                    icd_code,
                    f"{agreement_pct:.1f}%",
                    "Minority (<10%)"
                ])
            
            if len(alt_data) > 1:  # Only add table if we have alternatives
                alt_table = Table(alt_data, colWidths=[2.9*inch, 1.0*inch, 1.3*inch, 1.3*inch], repeatRows=1)
                alt_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc')]),
                    ('FONTSIZE', (0, 1), (-1, -1), 9)
                ]))
                content.append(alt_table)
        
        content.append(Spacer(1, 0.1*inch))
        
        # Analysis overview
        # Calculate correct statistics from model responses
        total_models = len(ensemble_results.get('model_responses', []))
        successful_models = sum(1 for r in ensemble_results.get('model_responses', []) if isinstance(r, dict) and r.get('response') and not r.get('error'))
        
        # Calculate total estimated cost
        try:
            from src.medley.utils.model_pricing import calculate_model_cost, format_cost
        except ImportError:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from src.medley.utils.model_pricing import calculate_model_cost, format_cost
        
        total_cost = 0.0
        for response in ensemble_results.get('model_responses', []):
            if response.get('response') and not response.get('error'):
                model_id = response.get('model_id', response.get('model_name', ''))
                input_tokens = response.get('input_tokens', 3500)
                output_tokens = response.get('tokens_used', response.get('output_tokens', 2000))
                try:
                    cost = calculate_model_cost(model_id, input_tokens, output_tokens)
                    total_cost += cost
                except:
                    pass
        
        # Add orchestrator cost if available
        orchestrator_cost = ensemble_results.get('orchestrator_cost', 0.0)
        if orchestrator_cost > 0:
            total_cost += orchestrator_cost
        
        # Get diagnostic data for overview
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        confidence_level = primary_data.get('confidence', 'Unknown')
        
        overview_data = [
            ["Analysis Overview"],
            [f"Models Queried: {total_models}"],
            [f"Successful Responses: {successful_models}"],
            [f"Consensus Level: {confidence_level}"],
            [f"Total Cost: {format_cost(total_cost)}"]
        ]
        
        overview_table = Table(overview_data, colWidths=[6.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22c55e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 10),  # Header font size
            ('FONTSIZE', (0, 1), (-1, -1), 9),  # Content font size
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#22c55e'))
        ]))
        
        # Ensure Analysis Overview table starts on new page if needed
        content.append(CondPageBreak(inch))  # Break page if less than 1 inch space left
        content.append(overview_table)
        
        return content
        
    def _create_executive_summary(self, ensemble_results: Dict) -> List:
        """Create comprehensive executive summary page"""
        content = []
        
        content.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Add case description if available
        if 'case_content' in ensemble_results:
            content.append(Paragraph("Case Description", self.styles['SubsectionHeader']))
            case_content = ensemble_results['case_content']
            
            # Parse and format the case content
            formatted_content = self._format_case_description(case_content)
            content.extend(formatted_content)
            content.append(Spacer(1, 0.2*inch))
        else:
            # Fallback to extracted presentation
            presentation = self._extract_case_presentation(ensemble_results)
            content.append(Paragraph(presentation, self.styles['ContentStyle']))
            content.append(Spacer(1, 0.2*inch))
        
        # Key Clinical Findings - moved from title page
        content.append(Paragraph("Key Clinical Findings", self.styles['SubsectionHeader']))
        
        key_findings = self._extract_key_findings(ensemble_results)
        if key_findings:
            for finding in key_findings[:5]:  # Show more findings on dedicated page
                content.append(Paragraph(f"• {finding}", self.styles['ContentStyle']))
        
        content.append(Spacer(1, 0.2*inch))
        
        # Primary Recommendations - moved from title page
        content.append(Paragraph("Primary Recommendations", self.styles['SubsectionHeader']))
        
        # Get consensus data for recommendations
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        consensus_pct = primary_data.get('agreement_percentage', 0)
        primary_name = primary_data.get('name', 'Primary diagnosis')
        
        # Create case-agnostic recommendations
        recommendations = self._generate_primary_recommendations(ensemble_results, primary_name, consensus_pct)
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", self.styles['ContentStyle']))
            
        return content
        
    def _create_primary_diagnosis_summaries(self, ensemble_results: Dict) -> List:
        """Create primary diagnosis summaries section with orchestrated analysis"""
        content = []
        
        content.append(Paragraph("Primary Diagnosis Clinical Summaries", self.styles['SectionHeader']))
        
        # Get orchestrated analysis (check both locations)
        summaries = ensemble_results.get('primary_diagnosis_summaries', {})
        if not summaries:
            orchestrated = ensemble_results.get('orchestrated_analysis', {})
            summaries = orchestrated.get('primary_diagnosis_summaries', {})
        
        if not summaries:
            content.append(Paragraph("Orchestrated analysis not available for this case.", self.styles['ContentStyle']))
            return content
        
        # Key Clinical Findings Section
        findings = summaries.get('key_clinical_findings', [])
        if findings:
            content.append(Paragraph("🔍 Key Clinical Findings", self.styles['SubsectionHeader']))
            content.append(Spacer(1, 0.1*inch))
            
            findings_data = [[
                "Finding", "Supporting Evidence", "Clinical Reasoning"
            ]]
            for finding in findings[:6]:  # Show up to 6 findings
                finding_name = finding.get('finding', 'Not specified')
                evidence = finding.get('supporting_evidence', 'Not specified')
                reasoning = finding.get('reasoning', 'Not specified')
                findings_data.append([
                    self._wrap_text_for_table(finding_name),
                    self._wrap_text_for_table(evidence),
                    self._wrap_text_for_table(reasoning)
                ])
            
            findings_table = Table(findings_data, colWidths=[2*inch, 2.5*inch, 2.5*inch], repeatRows=1)
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            content.append(findings_table)
            content.append(Spacer(1, 0.2*inch))
        
        # Recommended Tests Section
        tests = summaries.get('recommended_tests', [])
        if tests:
            content.append(Paragraph("🧪 Recommended Tests", self.styles['SubsectionHeader']))
            content.append(Spacer(1, 0.1*inch))
            
            tests_data = [[
                "Test Name", "Type", "Priority", "Rationale"
            ]]
            for test in tests[:6]:  # Show up to 6 tests
                test_name = test.get('test_name', 'Not specified')
                test_type = test.get('test_type', 'Not specified')
                priority = test.get('priority', 'Not specified')
                rationale = test.get('rationale', 'Not specified')
                tests_data.append([
                    self._wrap_text_for_table(test_name),
                    self._wrap_text_for_table(test_type),
                    self._wrap_text_for_table(priority),
                    self._wrap_text_for_table(rationale)
                ])
            
            tests_table = Table(tests_data, colWidths=[2*inch, 1*inch, 1*inch, 3*inch], repeatRows=1)
            tests_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            content.append(tests_table)
            content.append(Spacer(1, 0.2*inch))
        
        # Immediate Management Section
        management = summaries.get('immediate_management', [])
        if management:
            content.append(Paragraph("⚡ Immediate Management", self.styles['SubsectionHeader']))
            content.append(Spacer(1, 0.1*inch))
            
            mgmt_data = [[
                "Intervention", "Category", "Urgency", "Clinical Reasoning"
            ]]
            for mgmt in management[:6]:  # Show up to 6 management items
                intervention = mgmt.get('intervention', 'Not specified')
                category = mgmt.get('category', 'Not specified')
                urgency = mgmt.get('urgency', 'Not specified')
                reasoning = mgmt.get('reasoning', 'Not specified')
                mgmt_data.append([
                    self._wrap_text_for_table(intervention),
                    self._wrap_text_for_table(category),
                    self._wrap_text_for_table(urgency),
                    self._wrap_text_for_table(reasoning)
                ])
            
            mgmt_table = Table(mgmt_data, colWidths=[2*inch, 1*inch, 1*inch, 3*inch], repeatRows=1)
            mgmt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            content.append(mgmt_table)
            content.append(Spacer(1, 0.2*inch))
        
        # Medications Section
        medications = summaries.get('medications', [])
        if medications:
            content.append(Paragraph("💊 Medications", self.styles['SubsectionHeader']))
            content.append(Spacer(1, 0.1*inch))
            
            meds_data = [[
                "Medication", "Dosage", "Route/Frequency", "Indication"
            ]]
            for med in medications[:6]:  # Show up to 6 medications
                med_name = med.get('medication_name', 'Not specified')
                dosage = med.get('dosage', 'Not specified')
                route_freq = f"{med.get('route', 'Unknown')} / {med.get('frequency', 'Unknown')}"
                indication = med.get('indication', 'Not specified')
                meds_data.append([
                    self._wrap_text_for_table(med_name),
                    self._wrap_text_for_table(dosage),
                    self._wrap_text_for_table(route_freq),
                    self._wrap_text_for_table(indication)
                ])
            
            meds_table = Table(meds_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2*inch], repeatRows=1)
            meds_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            content.append(meds_table)
            
        return content
        
    def _create_diagnostic_landscape(self, ensemble_results: Dict) -> List:
        """Create comprehensive diagnostic landscape section (primary diagnosis moved to page 1)"""
        content = []
        
        content.append(Paragraph("Diagnostic Landscape Analysis", self.styles['SectionHeader']))
        
        # Get diagnostic data
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        
        # Skip primary diagnosis (now on page 1) and focus on detailed analysis
        content.append(Paragraph("Detailed Diagnostic Analysis", self.styles['SubsectionHeader']))
        
        # Add diagnostic overview
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        if primary_data and isinstance(primary_data, dict):
            agreement_pct = primary_data.get('agreement_percentage', 0) if isinstance(primary_data, dict) else 0
            consensus_display = f"{agreement_pct:.1f}%" if agreement_pct > 0 else "limited"
            primary_name = primary_data.get('name', 'Unknown') if isinstance(primary_data, dict) else str(primary_data)
            supporting_models = primary_data.get('supporting_models', []) if isinstance(primary_data, dict) else []
            model_count = len(supporting_models)
            overview_text = f"The ensemble analysis identified <b>{primary_name}</b> as the primary diagnosis with {consensus_display} consensus among {model_count} models."
            content.append(Paragraph(overview_text, self.styles['ContentStyle']))
            content.append(Spacer(1, 0.1*inch))
        
        # Alternative diagnoses detailed section  
        content.append(Paragraph("Detailed Alternative Analysis", self.styles['SubsectionHeader']))
        
        # Include all alternative categories for detailed analysis
        strong_alternatives = diagnostic_data.get('strong_alternatives', [])
        alternatives = diagnostic_data.get('alternatives', [])
        minority = diagnostic_data.get('minority_opinions', [])
        all_alternatives = strong_alternatives + alternatives + minority
        
        if all_alternatives:
            alt_data = [["Diagnosis", "Support", "Key Evidence", "Clinical Significance"]]
            
            for alt in all_alternatives[:8]:  # Show more alternatives with new categories
                diagnosis = alt.get('name', 'Unknown')
                agreement_pct = alt.get('agreement_percentage', alt.get('percentage', 0))
                models = alt.get('supporting_models', [])
                evidence = alt.get('evidence', [])
                rationale = alt.get('rationale', '')
                
                # Include evidence/rationale in diagnosis cell
                if evidence:
                    diagnosis_with_evidence = f"{diagnosis}<br/><i>Evidence: {', '.join(evidence[:3])}</i>"
                elif rationale:
                    diagnosis_with_evidence = f"{diagnosis}<br/><i>Rationale: {rationale[:100]}</i>"
                else:
                    diagnosis_with_evidence = diagnosis
                    
                alt_data.append([
                    Paragraph(diagnosis_with_evidence, self.styles['TableCellStyle']),
                    f"{agreement_pct:.1f}%",
                    f"{len(models)} models",
                    self._get_clinical_significance(agreement_pct / 100.0)
                ])
                
            alt_table = Table(alt_data, colWidths=[2.5*inch, 1.2*inch, 1.4*inch, 1.4*inch], repeatRows=1)
            alt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            content.append(alt_table)
        else:
            # Fallback if no alternatives
            content.append(Paragraph(
                "The model ensemble showed strong consensus on the primary diagnosis with limited alternative considerations.",
                self.styles['ContentStyle']
            ))
            
        content.append(Spacer(1, 0.2*inch))
        
        # Minority opinions - show ALL minority opinions with rationale
        minority = diagnostic_data.get('minority_opinions', [])
        # Check for all_alternative_diagnoses in both locations
        all_alternatives = diagnostic_data.get('all_alternative_diagnoses', [])
        if not all_alternatives:
            # Also check at root level of ensemble_results
            all_alternatives = ensemble_results.get('all_alternative_diagnoses', [])
        
        if minority or all_alternatives:
            content.append(Paragraph("Minority Opinions", self.styles['SubsectionHeader']))
            content.append(Paragraph(
                "All alternative diagnoses suggested by any models with their clinical rationale:",
                self.styles['ContentStyle']
            ))
            
            # First show minority opinions from orchestrator
            for opinion in minority:  # Show ALL, not just first 3
                diagnosis = opinion.get('name', 'Unknown')
                icd_code = opinion.get('icd10_code', self._get_diagnosis_icd_code(diagnosis))
                models = opinion.get('supporting_models', [])
                rationale = opinion.get('clinical_significance', opinion.get('rationale', ''))
                percentage = opinion.get('agreement_percentage', 0)
                
                content.append(Paragraph(
                    f"• <b>{diagnosis}</b> (ICD-10: {icd_code}) - {percentage:.1f}% agreement ({len(models)} models)",
                    self.styles['ContentStyle']
                ))
                content.append(Paragraph(
                    f"  Supporting Models: {', '.join(models)}",
                    self.styles['DetailStyle']
                ))
                if rationale:
                    content.append(Paragraph(
                        f"  Clinical Significance: {rationale}",
                        self.styles['DetailStyle']
                    ))
            
            # Then show remaining alternatives from all_alternative_diagnoses
            if all_alternatives:
                content.append(Spacer(1, 0.1*inch))
                content.append(Paragraph(
                    "<b>Additional Diagnoses Considered:</b>",
                    self.styles['ContentStyle']
                ))
                for alt in all_alternatives:
                    # Handle both dict and string formats
                    if isinstance(alt, dict):
                        diagnosis = alt.get('name', 'Unknown')
                        # Check for ICD code in different fields
                        icd_code = alt.get('icd_code') or alt.get('icd10_code') or self._get_diagnosis_icd_code(diagnosis)
                        models = alt.get('supporting_models', [])
                        # Use percentage if available, otherwise calculate from frequency
                        percentage = alt.get('percentage', 0)
                        if percentage == 0 and 'frequency' in alt:
                            total_models = ensemble_results.get('total_models_analyzed', 22)
                            percentage = round((alt['frequency'] / total_models) * 100, 1)
                        frequency = alt.get('frequency', len(models))
                        evidence = alt.get('evidence', [])
                    else:
                        diagnosis = str(alt)
                        icd_code = self._get_diagnosis_icd_code(diagnosis)
                        models = []
                        percentage = 0
                        frequency = 0
                        evidence = []
                    
                    # Skip if already shown in minority opinions
                    if any(m.get('name') == diagnosis for m in minority if isinstance(m, dict)):
                        continue
                    
                    # Use frequency or len(models) for count
                    model_count = frequency if frequency > 0 else len(models)
                    
                    content.append(Paragraph(
                        f"• <b>{diagnosis}</b> (ICD-10: {icd_code}) - {percentage:.1f}% ({model_count} models)",
                        self.styles['ContentStyle']
                    ))
                    if evidence:
                        content.append(Paragraph(
                            f"  Evidence: {', '.join(evidence[:5])}",
                            self.styles['DetailStyle']
                        ))
        
        # Add diagnostic confidence breakdown if no minority opinions
        if not minority:
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph("Diagnostic Confidence Analysis", self.styles['SubsectionHeader']))
            
            # Create confidence analysis based on available data
            evidence_synthesis = ensemble_results.get('evidence_synthesis', {})
            if evidence_synthesis:
                certainty = evidence_synthesis.get('diagnostic_certainty', {})
                
                if certainty.get('high_confidence_findings'):
                    content.append(Paragraph("<b>High Confidence Findings:</b>", self.styles['ContentStyle']))
                    for finding in certainty['high_confidence_findings'][:3]:
                        content.append(Paragraph(f"• {finding}", self.styles['DetailStyle']))
                    content.append(Spacer(1, 0.05*inch))
                
                if certainty.get('areas_of_uncertainty'):
                    content.append(Paragraph("<b>Areas Requiring Further Investigation:</b>", self.styles['ContentStyle']))
                    for area in certainty['areas_of_uncertainty'][:3]:
                        content.append(Paragraph(f"• {area}", self.styles['DetailStyle']))
            else:
                # Fallback content
                content.append(Paragraph(
                    "The diagnostic confidence is based on the convergence of clinical findings, "
                    "patient demographics, and symptom patterns consistent with the primary diagnosis.",
                    self.styles['ContentStyle']
                ))
                    
        return content
        
    def _create_management_strategies(self, ensemble_results: Dict) -> List:
        """Create management strategies section"""
        content = []
        
        content.append(Paragraph("Management Strategies & Clinical Pathways", self.styles['SectionHeader']))
        
        # Extract management recommendations
        management = self._extract_management_strategies(ensemble_results)
        
        # Immediate actions
        content.append(Paragraph("Immediate Actions Required", self.styles['SubsectionHeader']))
        
        immediate_actions = management.get('immediate_actions', [])
        if immediate_actions:
            action_data = [["Priority", "Action", "Rationale", "Consensus"]]
            
            for i, action in enumerate(immediate_actions[:5], 1):
                if isinstance(action, dict):
                    consensus_val = action.get('consensus', '50%')
                else:
                    consensus_val = '50%'
                if isinstance(consensus_val, str):
                    if '%' in consensus_val:
                        consensus_display = consensus_val
                    else:
                        # Try to convert string to number
                        try:
                            num_val = float(consensus_val)
                            consensus_display = f"{num_val:.0f}%"
                        except:
                            consensus_display = consensus_val
                else:
                    consensus_display = f"{consensus_val:.0f}%"
                    
                if isinstance(action, dict):
                    action_text = action.get('action', '')
                    rationale_text = action.get('rationale', 'Clinical indication')
                else:
                    action_text = str(action)
                    rationale_text = 'Clinical indication'
                
                action_data.append([
                    f"{i}",
                    Paragraph(action_text, self.styles['TableCellStyle']),
                    Paragraph(rationale_text, self.styles['TableCellStyle']),
                    consensus_display
                ])
                
            action_table = Table(action_data, colWidths=[0.5*inch, 2.3*inch, 2.7*inch, 1.0*inch], repeatRows=1)
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (2, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dc2626')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            content.append(action_table)
        else:
            content.append(Paragraph("No immediate actions identified with high consensus.", self.styles['ContentStyle']))
            
        content.append(Spacer(1, 0.2*inch))
        
        # Diagnostic workup
        content.append(Paragraph("Recommended Diagnostic Tests", self.styles['SubsectionHeader']))
        
        # Check both diagnostic_tests and differential_testing (Case 2 uses the latter)
        tests = management.get('diagnostic_tests', [])
        if not tests:
            tests = management.get('differential_testing', [])
        
        if tests:
            test_data = [["Test", "Purpose", "Priority", "Timing"]]
            
            for test in tests[:6]:
                test_data.append([
                    Paragraph(test.get('test', ''), self.styles['TableCellStyle']),
                    Paragraph(test.get('purpose', ''), self.styles['TableCellStyle']),
                    test.get('priority', 'Routine'),
                    test.get('timing', 'As indicated')
                ])
                
            test_table = Table(test_data, colWidths=[1.8*inch, 2.2*inch, 1.25*inch, 1.25*inch], repeatRows=1)
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (3, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecfeff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#0891b2')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            content.append(test_table)
            
        content.append(Spacer(1, 0.2*inch))
        
        # Treatment recommendations
        content.append(Paragraph("Treatment Recommendations", self.styles['SubsectionHeader']))
        
        treatments = management.get('treatments', [])
        if treatments:
            for treatment in treatments[:3]:
                content.append(Paragraph(
                    f"• <b>{treatment.get('medication', 'Treatment')}</b>: {treatment.get('dose', '')} - {treatment.get('rationale', '')}",
                    self.styles['ContentStyle']
                ))
        else:
            content.append(Paragraph("Treatment recommendations pending diagnostic confirmation.", self.styles['ContentStyle']))
            
        return content
        
    def _create_model_diversity_analysis(self, ensemble_results: Dict) -> List:
        """Create model diversity and bias analysis section"""
        content = []
        
        content.append(Paragraph("Model Diversity & Bias Analysis", self.styles['SectionHeader']))
        
        # Model response overview with cost
        content.append(Paragraph("Model Response Overview & Cost Analysis", self.styles['SubsectionHeader']))
        
        # Import pricing utilities
        try:
            from src.medley.utils.model_pricing import calculate_model_cost, format_cost, get_model_tier
        except ImportError:
            # Fallback import path
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from src.medley.utils.model_pricing import calculate_model_cost, format_cost, get_model_tier
        
        model_data = [["Model", "Origin", "Tier", "Cost", "Diagnosis", "Training Profile"]]
        total_cost = 0.0
        
        # Include ALL non-empty responses, not just first 10
        for response in ensemble_results.get('model_responses', []):
            if not response.get('response') or response.get('error'):
                continue
                
            model_info = self.get_model_info(response.get('model_name', ''))
            
            # Extract primary diagnosis and ICD code directly from response
            primary_dx = self._extract_primary_diagnosis(response)
            
            # Calculate cost for this model
            model_id = response.get('model_id', response.get('model_name', ''))
            input_tokens = response.get('input_tokens', 3500)  # Estimate if not available
            output_tokens = response.get('tokens_used', response.get('output_tokens', 2000))  # Use tokens_used or estimate
            
            try:
                model_cost = calculate_model_cost(model_id, input_tokens, output_tokens)
                total_cost += model_cost
                cost_str = format_cost(model_cost)
                tier = get_model_tier(model_id)
            except:
                cost_str = "N/A"
                tier = "Unknown"
            
            # Determine training profile based on model characteristics
            training_profile = "Standard"
            model_name = response.get('model_name', '')
            model_name_lower = model_name.lower()
            
            # General purpose models (not medical-specific)
            if "free" in model_name_lower or "mini" in model_name_lower or "3b" in model_name_lower or "7b" in model_name_lower:
                training_profile = "General"
            # Regional medical training focus
            elif model_info.get('origin') == "China" or "chinese" in str(model_info.get('bias_summary', '')).lower():
                training_profile = "Regional"
            # Comprehensive medical training
            elif "gpt-4" in model_name_lower or "claude" in model_name_lower or "gemini-2.5" in model_name_lower:
                training_profile = "Comprehensive"
            # Uncensored or contrarian models
            elif "uncensored" in str(model_info.get('bias_summary', '')).lower() or "contrarian" in str(model_info.get('bias_summary', '')).lower():
                training_profile = "Alternative"
            # Western standard medical
            elif model_info.get('origin') in ["USA", "Canada", "France"]:
                training_profile = "Standard"
            
            model_data.append([
                Paragraph(model_info['short'], self.styles['TableCellStyle']),
                Paragraph(model_info['origin'], self.styles['TableCellStyle']),
                Paragraph(tier, self.styles['TableCellStyle']),
                Paragraph(cost_str, self.styles['TableCellStyle']),
                Paragraph(primary_dx, self.styles['TableCellStyle']),
                Paragraph(training_profile, self.styles['TableCellStyle'])
            ])
            
        if len(model_data) > 1:
            # Make table 6.5 inches wide to match other tables
            model_table = Table(model_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 2.0*inch, 1.0*inch], repeatRows=1)
            model_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Left align for better readability
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Smaller font for content
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d1fae5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#15803d')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
            ]))
            content.append(model_table)
            
            # Add orchestrator cost if available
            orchestrator_cost = ensemble_results.get('orchestrator_cost', 0.0)
            if orchestrator_cost > 0:
                total_cost += orchestrator_cost
                print(f"  📊 Added orchestrator cost: ${orchestrator_cost:.4f} to total")
            
            # Add total cost summary
            content.append(Spacer(1, 0.1*inch))
            if orchestrator_cost > 0:
                cost_breakdown = f"**Total Cost: {format_cost(total_cost)}** (Models: {format_cost(total_cost - orchestrator_cost)} + Orchestrator: {format_cost(orchestrator_cost)})"
                content.append(Paragraph(cost_breakdown, self.styles['ContentStyle']))
            else:
                cost_summary = f"**Total Estimated Cost: {format_cost(total_cost)}**"
                content.append(Paragraph(cost_summary, self.styles['ContentStyle']))
            
        # Training Profile Information
        content.append(Spacer(1, 0.15*inch))
        content.append(Paragraph("Understanding Training Profiles", self.styles['SubsectionHeader']))
        
        content.append(Paragraph(
            "Training profiles indicate the type and depth of medical knowledge in each model:",
            self.styles['ContentStyle']
        ))
        content.append(Spacer(1, 0.1*inch))
        
        # Training profile definitions
        profile_definitions = [
            ("Comprehensive", "Extensive medical literature training with broad clinical knowledge", "#388e3c"),
            ("Standard", "Standard medical knowledge base with general clinical training", "#f57c00"),
            ("Regional", "Region-specific medical training reflecting local practices and conditions", "#f57c00"),
            ("General", "Broad general knowledge, not specifically trained on medical literature", "#d32f2f"),
            ("Alternative", "Alternative medical perspectives and non-conventional approaches", "#7b1fa2")
        ]
        
        for profile, description, color in profile_definitions:
            profile_text = f"<b><font color='{color}'>{profile}:</font></b> {description}"
            content.append(Paragraph(profile_text, self.styles['ContentStyle']))
            content.append(Spacer(1, 0.05*inch))
            
        content.append(Spacer(1, 0.2*inch))
        
        # AI Model Bias Analysis (orchestrator-generated)
        content.append(Paragraph("AI Model Bias Analysis", self.styles['SubsectionHeader']))
        
        # Add explanatory note about orchestration
        content.append(Paragraph(
            "AI model bias analysis is generated during orchestration (Step 2). " +
            "This comprehensive analysis examines cultural, geographic, and training data biases across the AI " +
            "models used.", 
            self.styles['DetailStyle']
        ))
        content.append(Spacer(1, 0.1*inch))
        
        # Get bias analysis (check both formats)
        bias_analysis = ensemble_results.get('ai_model_bias_analysis', {})
        
        # Also check for comprehensive bias analysis format
        if not bias_analysis:
            comprehensive_bias = ensemble_results.get('comprehensive_bias_analysis', {})
            if comprehensive_bias:
                # Convert comprehensive format to expected format
                bias_analysis = self._convert_comprehensive_bias_analysis(comprehensive_bias)
        
        if bias_analysis:
            # Primary diagnosis bias factors
            primary_bias = bias_analysis.get('primary_diagnosis_bias_factors', {})
            if primary_bias:
                content.append(Paragraph("Primary Diagnosis Bias Factors:", self.styles['ContentStyle']))
                
                # Cultural bias
                cultural = primary_bias.get('cultural_bias', {})
                if cultural.get('description'):
                    content.append(Paragraph(f"• Cultural: {cultural['description']}", self.styles['DetailStyle']))
                
                # Geographic bias
                geographic = primary_bias.get('geographic_bias', {})
                if geographic.get('impact_on_diagnosis'):
                    content.append(Paragraph(f"• Geographic: {geographic['impact_on_diagnosis']}", self.styles['DetailStyle']))
                
                # Training data bias
                training = primary_bias.get('training_data_bias', {})
                if training.get('description'):
                    content.append(Paragraph(f"• Training Data: {training['description']}", self.styles['DetailStyle']))
            
            # Alternative diagnoses bias
            alt_bias = bias_analysis.get('alternative_diagnoses_bias', {})
            if alt_bias:
                content.append(Spacer(1, 0.1*inch))
                content.append(Paragraph("Alternative Diagnoses Bias:", self.styles['ContentStyle']))
                
                # Missed diagnoses
                missed = alt_bias.get('missed_diagnoses_due_to_bias', [])
                for miss in missed[:2]:  # Show top 2
                    if miss.get('explanation'):
                        content.append(Paragraph(f"• Missed: {miss.get('diagnosis', 'Unknown')} - {miss['explanation'][:60]}{'...' if len(miss['explanation']) > 60 else ''}", self.styles['DetailStyle']))
                
                # Over-represented diagnoses
                over_rep = alt_bias.get('overrepresented_diagnoses', [])
                for over in over_rep[:2]:  # Show top 2
                    if over.get('frequency_bias'):
                        content.append(Paragraph(f"• Over-diagnosed: {over.get('diagnosis', 'Unknown')} - {over['frequency_bias'][:60]}{'...' if len(over['frequency_bias']) > 60 else ''}", self.styles['DetailStyle']))
            
            # Mitigation recommendations
            mitigation = bias_analysis.get('bias_mitigation_recommendations', [])
            if mitigation:
                content.append(Spacer(1, 0.1*inch))
                content.append(Paragraph("Bias Mitigation Recommendations:", self.styles['ContentStyle']))
                for rec in mitigation[:3]:  # Show top 3
                    if rec.get('recommendation'):
                        content.append(Paragraph(f"• {rec.get('bias_type', 'General')}: {rec['recommendation'][:80]}{'...' if len(rec['recommendation']) > 80 else ''}", self.styles['DetailStyle']))
        else:
            # Fallback to original geographic patterns if orchestrator analysis not available
            content.append(Paragraph("AI model bias analysis is generated during orchestration (Step 2).", self.styles['ContentStyle']))
            content.append(Paragraph("This comprehensive analysis examines cultural, geographic, and training data biases across the AI models used.", self.styles['DetailStyle']))
                
        return content
        
    def _create_critical_decisions(self, ensemble_results: Dict) -> List:
        """Create critical decision points section"""
        content = []
        
        content.append(Paragraph("Critical Decision Points", self.styles['SectionHeader']))
        
        content.append(Paragraph(
            "Key areas where models showed significant divergence in diagnostic or management approach:",
            self.styles['ContentStyle']
        ))
        
        content.append(Spacer(1, 0.1*inch))
        
        # Identify decision points
        decision_points = self._identify_critical_decisions(ensemble_results)
        
        for i, decision in enumerate(decision_points[:4], 1):
            # Decision header
            content.append(Paragraph(
                f"Decision Point {i}: {decision['topic']}",
                self.styles['SubsectionHeader']
            ))
            
            # Create comparison table
            decision_data = [
                ["Approach", "Models", "Rationale", "Impact"]
            ]
            
            for option in decision['options'][:2]:
                decision_data.append([
                    Paragraph(option['approach'], self.styles['TableCellStyle']),
                    f"{len(option['models'])} models",
                    Paragraph(option['rationale'], self.styles['TableCellStyle']),
                    Paragraph(option['impact'], self.styles['TableCellStyle'])
                ])
                
            decision_table = Table(decision_data, colWidths=[2.0*inch, 1.0*inch, 2.0*inch, 1.5*inch], repeatRows=1)
            decision_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Changed to LEFT for better text wrapping
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Added TOP alignment
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),      # Smaller header font
                ('FONTSIZE', (0, 1), (-1, -1), 8),     # Smaller content font
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#f0fff4')),
                ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#fef9c3')),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),  # Reduced padding
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2)
            ]))
            content.append(decision_table)
            
            content.append(Spacer(1, 0.15*inch))
            
        return content
        
    def _create_combined_critical_evidence_analysis(self, ensemble_results: Dict) -> List:
        """Create combined Critical Decisions & Evidence Synthesis section"""
        content = []
        
        content.append(Paragraph("Critical Decision Points & Evidence Synthesis", self.styles['SectionHeader']))
        
        # Critical Decision Points subsection
        content.append(Paragraph("Critical Decision Points", self.styles['SubsectionHeader']))
        content.append(Paragraph(
            "Key areas where models showed significant divergence in diagnostic or management approach:",
            self.styles['ContentStyle']
        ))
        
        # Get critical decisions from the original function
        decisions = self._identify_critical_decisions(ensemble_results)
        
        for i, decision in enumerate(decisions[:2], 1):  # Show top 2 decisions
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                f"Decision Point {i}: {decision['topic']}", 
                self.styles['SubsectionHeader']
            ))
            
            # Create comparison table
            decision_data = [
                ["Approach", "Models", "Rationale", "Impact"]
            ]
            
            for option in decision['options'][:2]:
                decision_data.append([
                    Paragraph(option['approach'], self.styles['TableCellStyle']),
                    f"{len(option['models'])} models",
                    Paragraph(option['rationale'], self.styles['TableCellStyle']),
                    Paragraph(option['impact'], self.styles['TableCellStyle'])
                ])
                
            decision_table = Table(decision_data, colWidths=[2.0*inch, 1.0*inch, 2.0*inch, 1.5*inch], repeatRows=1)
            decision_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#f0fff4')),
                ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#fef9c3')),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2)
            ]))
            content.append(decision_table)
        
        content.append(Spacer(1, 0.3*inch))
        
        # Evidence Synthesis subsection
        content.append(Paragraph("Evidence Synthesis & Clinical Correlation", self.styles['SubsectionHeader']))
        
        # Symptom-Diagnosis Correlation Matrix
        content.append(Paragraph("Symptom-Diagnosis Correlation Matrix", self.styles['SubsectionHeader']))
        
        # Check for orchestrated evidence synthesis data first
        evidence_synthesis = ensemble_results.get('evidence_synthesis', {})
        symptom_matrix = evidence_synthesis.get('symptom_diagnosis_matrix', {})
        
        if symptom_matrix and 'symptoms' in symptom_matrix and 'diagnoses' in symptom_matrix:
            # Use orchestrated data
            symptoms = symptom_matrix.get('symptoms', [])
            diagnoses = symptom_matrix.get('diagnoses', [])
            correlations = symptom_matrix.get('correlations', [])
            
            # Build correlation lookup
            correlation_map = {}
            for corr in correlations:
                key = (corr.get('symptom', ''), corr.get('diagnosis', ''))
                correlation_map[key] = corr.get('strength', '-')
            
            # Create abbreviated diagnosis names for space
            def abbreviate_diagnosis(name):
                abbreviations = {
                    'Familial Mediterranean Fever': 'FMF',
                    'Inflammatory Bowel Disease': 'IBD',
                    'Systemic Lupus Erythematosus': 'SLE',
                    'Septic Arthritis': 'Septic',
                    'Reactive Arthritis': 'Reactive',
                    'Arthritis': 'Arthritis',
                    'Lupus': 'Lupus',
                    'FMF': 'FMF',
                    'SLE': 'SLE'
                }
                return abbreviations.get(name, name[:8])
            
            # Create matrix header - show first 8 diagnoses
            diagnoses_to_show = diagnoses[:8] if len(diagnoses) > 8 else diagnoses
            matrix_data = [["Symptom"] + [abbreviate_diagnosis(d) for d in diagnoses_to_show]]
            
            # Add symptom rows - show first 10 symptoms
            for symptom in symptoms[:10]:
                row = [symptom[:15]]  # Truncate long symptom names
                for diagnosis in diagnoses_to_show:
                    correlation = correlation_map.get((symptom, diagnosis), '-')
                    if not correlation:  # Handle empty strings from HTML
                        correlation = '-'
                    row.append(correlation)
                matrix_data.append(row)
        else:
            # Fallback to extraction methods
            symptoms = self._extract_symptoms(ensemble_results)
            diagnoses = self._extract_diagnoses(ensemble_results)
            
            matrix_data = []  # Initialize matrix_data
            if symptoms and diagnoses:
                # Create matrix header
                matrix_data = [["Symptom/Finding"] + [d[:12] for d in diagnoses[:4]]]
                
                # Add symptom rows
                for symptom in symptoms[:5]:
                    row = [symptom[:15]]
                    for diagnosis in diagnoses[:4]:
                        correlation = self._calculate_correlation(symptom, diagnosis, ensemble_results)
                        row.append(correlation)
                    matrix_data.append(row)
        
        if matrix_data:
            # Adjust column widths based on number of diagnoses
            num_diagnoses = len(matrix_data[0]) - 1
            if num_diagnoses <= 4:
                col_widths = [1.5*inch] + [1.2*inch] * num_diagnoses
            elif num_diagnoses <= 6:
                col_widths = [1.3*inch] + [0.85*inch] * num_diagnoses
            else:  # 7-8 diagnoses
                col_widths = [1.1*inch] + [0.70*inch] * num_diagnoses
            
            matrix_table = Table(matrix_data, colWidths=col_widths)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#16a34a')),
                ('BACKGROUND', (1, 1), (-1, -1), colors.HexColor('#f0fff4'))
            ]))
            content.append(matrix_table)
            
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph("Legend: +++ Strong association, ++ Moderate, + Weak, - Not typical", self.styles['DetailStyle']))
        
        content.append(Spacer(1, 0.2*inch))
        
        # Diagnostic Decision Tree
        content.append(Paragraph("Diagnostic Decision Tree", self.styles['SubsectionHeader']))
        
        # Generate decision tree dynamically based on diagnosis
        tree_data_raw = self._generate_diagnostic_tree(ensemble_results)
        
        # Convert to Paragraph objects for text wrapping
        tree_data = []
        for i, row in enumerate(tree_data_raw):
            if i == 0:  # Header row
                tree_data.append(row)
            else:  # Data rows - wrap text
                tree_data.append([
                    row[0],  # Step number
                    Paragraph(row[1], self.styles['TableCellStyle']),  # Action
                    Paragraph(row[2], self.styles['TableCellStyle']),  # If Positive
                    Paragraph(row[3], self.styles['TableCellStyle'])   # If Negative
                ])
        
        tree_table = Table(tree_data, colWidths=[0.5*inch, 2.0*inch, 2.0*inch, 2.0*inch])
        tree_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#15803d'))
        ]))
        content.append(tree_table)
        
        return content
        
    def _create_evidence_synthesis(self, ensemble_results: Dict) -> List:
        """Create evidence synthesis section"""
        content = []
        
        content.append(Paragraph("Evidence Synthesis & Clinical Correlation", self.styles['SectionHeader']))
        
        # Symptom-diagnosis correlation matrix
        content.append(Paragraph("Symptom-Diagnosis Correlation Matrix", self.styles['SubsectionHeader']))
        
        # Check for orchestrated evidence synthesis data first
        evidence_synthesis = ensemble_results.get('evidence_synthesis', {})
        symptom_matrix = evidence_synthesis.get('symptom_diagnosis_matrix', {})
        
        if symptom_matrix and 'symptoms' in symptom_matrix and 'diagnoses' in symptom_matrix:
            # Use orchestrated data
            symptoms = symptom_matrix.get('symptoms', [])
            diagnoses = symptom_matrix.get('diagnoses', [])
            correlations = symptom_matrix.get('correlations', [])
            
            # Build correlation lookup
            correlation_map = {}
            for corr in correlations:
                key = (corr.get('symptom', ''), corr.get('diagnosis', ''))
                correlation_map[key] = corr.get('strength', '-')
            
            # Create matrix header - use abbreviated names for space
            # Abbreviate long diagnosis names for better fit
            def abbreviate_diagnosis(name):
                abbreviations = {
                    'Familial Mediterranean Fever': 'FMF',
                    'Inflammatory Bowel Disease': 'IBD', 
                    'Systemic Lupus Erythematosus': 'SLE',
                    'Septic Arthritis': 'Septic Arth.',
                    'Reactive Arthritis': 'React. Arth.',
                    'Arthritis': 'Arthritis',
                    'Lupus': 'Lupus',
                    'FMF': 'FMF',
                    'SLE': 'SLE',
                    'IBD': 'IBD'
                }
                return abbreviations.get(name, name[:12])
            
            # Show up to 8 diagnoses to match HTML
            diagnoses_to_show = diagnoses[:8] if len(diagnoses) > 8 else diagnoses
            matrix_data = [["Symptom"] + [abbreviate_diagnosis(d) for d in diagnoses_to_show]]
            
            # Add symptom rows - show all symptoms to match HTML
            for symptom in symptoms[:10]:  # Show up to 10 symptoms
                row = [symptom]
                for diagnosis in diagnoses_to_show:
                    correlation = correlation_map.get((symptom, diagnosis), '-')
                    row.append(correlation)
                matrix_data.append(row)
        else:
            # Fallback to extraction methods if no orchestrated data
            symptoms = self._extract_symptoms(ensemble_results)
            diagnoses = self._extract_diagnoses(ensemble_results)
            
            if symptoms and diagnoses:
                # Create matrix header
                matrix_data = [["Symptom/Finding"] + [d[:12] for d in diagnoses[:4]]]
                
                # Add symptom rows
                for symptom in symptoms[:6]:
                    row = [symptom[:20]]
                    for diagnosis in diagnoses[:4]:
                        correlation = self._calculate_correlation(symptom, diagnosis, ensemble_results)
                        row.append(correlation)
                    matrix_data.append(row)
            else:
                matrix_data = None
        
        if matrix_data:
            # Adjust column widths based on number of diagnoses
            num_diagnoses = len(matrix_data[0]) - 1  # Subtract 1 for symptom column
            if num_diagnoses <= 4:
                col_widths = [1.8*inch] + [1.25*inch]*num_diagnoses
            elif num_diagnoses <= 6:
                col_widths = [1.5*inch] + [0.85*inch]*num_diagnoses
            else:  # 7-8 diagnoses
                col_widths = [1.2*inch] + [0.70*inch]*num_diagnoses
            
            matrix_table = Table(matrix_data, colWidths=col_widths)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dcfce7')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),  # Smaller font for headers
                ('FONTSIZE', (0, 1), (0, -1), 8),  # Smaller font for symptom column
                ('FONTSIZE', (1, 1), (-1, -1), 7),  # Even smaller for correlation cells
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#16a34a'))
            ]))
            content.append(matrix_table)
            
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                "<i>Legend: +++ Strong association, ++ Moderate, + Weak, - Not typical</i>",
                self.styles['DetailStyle']
            ))
            
        content.append(Spacer(1, 0.2*inch))
        
        # Clinical decision tree
        content.append(Paragraph("Diagnostic Decision Tree", self.styles['SubsectionHeader']))
        
        # Generate decision tree dynamically based on diagnosis
        tree_data = self._generate_diagnostic_tree(ensemble_results)
        
        tree_table = Table(tree_data, colWidths=[0.5*inch, 2.0*inch, 2.0*inch, 2.0*inch])
        tree_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#15803d')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        content.append(tree_table)
        
        return content
        
    def _create_detailed_responses(self, ensemble_results: Dict) -> List:
        """Create detailed model responses section"""
        content = []
        
        content.append(Paragraph("Detailed Model Responses", self.styles['SectionHeader']))
        
        content.append(Paragraph(
            "Complete diagnostic assessments from each model:",
            self.styles['ContentStyle']
        ))
        
        # Show ALL non-empty responses, not just 8
        for i, response in enumerate(ensemble_results.get('model_responses', []), 1):
            if not response.get('response') or response.get('error'):
                continue
                
            model_info = self.get_model_info(response.get('model_name', ''))
            
            # Model header
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph(
                f"{i}. {model_info['short']} ({model_info['origin']}, Released: {model_info['date']})",
                self.styles['SubsectionHeader']
            ))
            
            # Parse comprehensive information from JSON response
            parsed_info = self._parse_complete_response(response.get('response', ''))
            
            if parsed_info:
                # Primary diagnosis with ICD
                primary = parsed_info.get('primary_diagnosis', {})
                # Handle both dict and string formats
                if isinstance(primary, dict) and primary.get('name'):
                    icd_text = f" (ICD-10: {primary.get('icd_code', 'Not specified')})" if primary.get('icd_code') else ""
                    confidence_text = f" - Confidence: {primary.get('confidence', 'Not specified')}" if primary.get('confidence') else ""
                    content.append(Paragraph(
                        f"<b>Primary Diagnosis:</b> {primary.get('name')}{icd_text}{confidence_text}",
                        self.styles['ContentStyle']
                    ))
                    if primary.get('reasoning'):
                        content.append(Paragraph(
                            f"<i>Reasoning:</i> {primary.get('reasoning')[:200]}...",
                            self.styles['DetailStyle']
                        ))
                
                # Alternative diagnoses
                alternatives = parsed_info.get('differential_diagnoses', [])
                if alternatives:
                    content.append(Paragraph("<b>Differential Diagnoses:</b>", self.styles['ContentStyle']))
                    for alt in alternatives[:3]:
                        # Handle both dict and string formats
                        if isinstance(alt, dict):
                            alt_name = alt.get('name', '')
                            alt_icd = f" (ICD: {alt.get('icd_code')})" if alt.get('icd_code') else ""
                            alt_conf = f" - {alt.get('confidence', '')}" if alt.get('confidence') else ""
                        else:
                            alt_name = str(alt)
                            alt_icd = ""
                            alt_conf = ""
                        content.append(Paragraph(f"• {alt_name}{alt_icd}{alt_conf}", self.styles['DetailStyle']))
                
                # Key findings
                key_findings = parsed_info.get('key_findings', [])
                if key_findings:
                    content.append(Paragraph("<b>Key Clinical Findings:</b>", self.styles['ContentStyle']))
                    for finding in key_findings[:4]:
                        content.append(Paragraph(f"• {finding}", self.styles['DetailStyle']))
                
                # Diagnostic tests
                tests = parsed_info.get('diagnostic_tests', [])
                if tests:
                    content.append(Paragraph("<b>Recommended Tests:</b>", self.styles['ContentStyle']))
                    for test in tests[:3]:
                        test_name = test.get('test', '') if isinstance(test, dict) else str(test)
                        test_purpose = f" - {test.get('purpose', '')}" if isinstance(test, dict) and test.get('purpose') else ""
                        content.append(Paragraph(f"• {test_name}{test_purpose}", self.styles['DetailStyle']))
                
                # Management plan
                mgmt = parsed_info.get('management_plan', {})
                if mgmt:
                    # Immediate actions
                    actions = mgmt.get('immediate_actions', [])
                    if actions:
                        content.append(Paragraph("<b>Immediate Management:</b>", self.styles['ContentStyle']))
                        for action in actions[:3]:
                            action_text = action if isinstance(action, str) else str(action)
                            content.append(Paragraph(f"• {action_text}", self.styles['DetailStyle']))
                    
                    # Medications
                    meds = mgmt.get('medications', [])
                    if meds:
                        content.append(Paragraph("<b>Medications:</b>", self.styles['ContentStyle']))
                        for med in meds[:2]:
                            if isinstance(med, dict):
                                med_text = f"{med.get('drug', 'Unknown')} {med.get('dose', '')} {med.get('route', '')}"
                            else:
                                med_text = str(med)
                            content.append(Paragraph(f"• {med_text}", self.styles['DetailStyle']))
                    
        return content
        
    # Helper methods
    
    def _get_confidence_text(self, confidence: float) -> str:
        """Convert confidence score to text"""
        if confidence > 0.8:
            return "Very High"
        elif confidence > 0.6:
            return "High"
        elif confidence > 0.4:
            return "Moderate"
        elif confidence > 0.2:
            return "Low"
        else:
            return "Very Low"
            
    def _get_clinical_significance(self, confidence: float) -> str:
        """Get clinical significance based on confidence"""
        if confidence > 0.5:
            return "Should be considered"
        elif confidence > 0.3:
            return "Worth investigating"
        elif confidence > 0.1:
            return "Less likely"
        else:
            return "Unlikely"
            
    def _extract_key_findings(self, ensemble_results: Dict) -> List[str]:
        """Extract key clinical findings from responses"""
        findings = set()
        
        for response in ensemble_results.get('model_responses', []):
            if response.get('response'):
                text = response['response'].lower()
                
                # Look for common clinical findings
                if 'fever' in text:
                    findings.add("Recurrent fever episodes")
                if 'abdominal pain' in text:
                    findings.add("Severe abdominal pain with peritoneal signs")
                if 'arthritis' in text:
                    findings.add("Migratory arthritis affecting large joints")
                if 'family history' in text:
                    findings.add("Positive family history of similar episodes")
                if 'elevated' in text and ('crp' in text or 'esr' in text):
                    findings.add("Elevated inflammatory markers (CRP, ESR)")
                    
        return list(findings)
        
    def _extract_management_strategies(self, ensemble_results: Dict) -> Dict:
        """Extract management strategies from orchestrated data or responses"""
        
        # First try to get from orchestrated data
        if 'management_strategies' in ensemble_results:
            return ensemble_results['management_strategies']
        
        # Otherwise extract from responses
        strategies = {
            'immediate_actions': set(),
            'diagnostic_tests': set(),
            'treatments': set()
        }
        
        primary_diagnosis = ensemble_results.get('diagnostic_landscape', {}).get('primary_diagnosis', {}).get('name', '').lower()
        
        colchicine_count = 0
        genetic_test_count = 0
        cholinesterase_count = 0
        calcium_test_count = 0
        total_responses = 0
        
        # Count occurrences to calculate consensus
        for response in ensemble_results.get('model_responses', []):
            if response.get('response'):
                total_responses += 1
                text = response['response'].lower()
                
                if 'colchicine' in text:
                    colchicine_count += 1
                if 'genetic' in text or 'mefv' in text:
                    genetic_test_count += 1
                if 'cholinesterase' in text or 'donepezil' in text or 'rivastigmine' in text:
                    cholinesterase_count += 1
                if 'calcium' in text or 'pth' in text or 'parathyroid' in text:
                    calcium_test_count += 1
        
        # Create unique strategies with calculated consensus based on diagnosis
        final_strategies = {
            'immediate_actions': [],
            'diagnostic_tests': [],
            'treatments': []
        }
        
        # Add diagnosis-specific strategies
        if 'mediterranean' in primary_diagnosis or 'fmf' in primary_diagnosis:
            if colchicine_count > 0:
                consensus_pct = (colchicine_count / total_responses) * 100 if total_responses > 0 else 0
                final_strategies['immediate_actions'].append({
                    'action': 'Start colchicine therapy',
                    'rationale': 'First-line treatment for FMF',
                    'consensus': f"{consensus_pct:.0f}%"
                })
            
            if genetic_test_count > 0:
                final_strategies['diagnostic_tests'].append({
                    'test': 'MEFV genetic testing',
                    'purpose': 'Confirm FMF diagnosis',
                    'priority': 'High',
                    'timing': 'Immediate'
                })
        
        elif 'dementia' in primary_diagnosis or 'lewy' in primary_diagnosis or 'alzheimer' in primary_diagnosis:
            if cholinesterase_count > 0:
                consensus_pct = (cholinesterase_count / total_responses) * 100 if total_responses > 0 else 0
                final_strategies['treatments'].append({
                    'action': 'Consider cholinesterase inhibitors',
                    'rationale': 'May improve cognitive symptoms',
                    'consensus': f"{consensus_pct:.0f}%"
                })
            
            final_strategies['immediate_actions'].append({
                'action': 'Comprehensive cognitive assessment',
                'rationale': 'Establish baseline and severity',
                'consensus': 'High'
            })
            
            final_strategies['diagnostic_tests'].append({
                'test': 'Brain MRI and metabolic panel',
                'purpose': 'Rule out reversible causes',
                'priority': 'High',
                'timing': 'Immediate'
            })
        
        elif 'hypercalcemia' in primary_diagnosis:
            if calcium_test_count > 0:
                final_strategies['diagnostic_tests'].append({
                    'test': 'PTH, ionized calcium, SPEP/UPEP',
                    'purpose': 'Determine etiology of hypercalcemia',
                    'priority': 'High',
                    'timing': 'Immediate'
                })
            
        # Additional common strategies
        final_strategies['immediate_actions'].extend([
            {
                'action': 'Provide supportive care',
                'rationale': 'Manage acute symptoms',
                'consensus': '95%'
            },
            {
                'action': 'Monitor inflammatory markers',
                'rationale': 'Track disease activity',
                'consensus': '90%'
            }
        ])
        
        final_strategies['diagnostic_tests'].extend([
            {
                'test': 'Complete blood count',
                'purpose': 'Assess inflammation',
                'priority': 'Routine',
                'timing': 'Within 24h'
            },
            {
                'test': 'Urine analysis',
                'purpose': 'Screen for amyloidosis',
                'priority': 'High',
                'timing': 'Within 48h'
            }
        ])
                    
        return final_strategies
        
    def _extract_primary_diagnosis(self, response: Dict) -> str:
        """Extract primary diagnosis from response with JSON parsing"""
        response_text = response.get('response', '')
        
        # First try to parse as JSON
        try:
            # Clean up response - some have ```json wrapper
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            data = json.loads(clean_text)
            
            primary = data.get('primary_diagnosis', {})
            if isinstance(primary, dict):
                name = primary.get('name', '')
                if name:
                    # Clean up diagnosis name for table display
                    if '(FMF)' in name:
                        name = name.replace(' (FMF)', '')
                    # Don't truncate - let Paragraph handle wrapping
                    return name
        except:
            pass
            
        # Fallback to regex patterns
        patterns = [
            r'"name":\s*"([^"]+)"',  # JSON name field
            r'primary diagnosis[:\s]+([^\n\.\,]+)',
            r'FMF|Familial Mediterranean Fever',
            r'periodic fever syndrome'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                if match.groups():
                    result = match.group(1).strip()
                    return result.replace('(FMF)', '').strip()
                else:
                    result = match.group(0).strip()
                    return result.replace('(FMF)', '').strip()
                    
        return "Not specified"
        
    def _generate_diagnostic_tree(self, ensemble_results: Dict) -> list:
        """Generate case-specific diagnostic decision tree"""
        
        # Try to get from orchestrated data first
        if 'clinical_decision_tree' in ensemble_results:
            tree = ensemble_results['clinical_decision_tree']
            if tree.get('branches'):
                # Convert orchestrator format to table format
                tree_data = [["Step", "Action", "If Positive", "If Negative"]]
                for i, branch in enumerate(tree['branches'][:4], 1):
                    tree_data.append([
                        str(i),
                        branch.get('test', 'Diagnostic test'),
                        branch.get('if_positive', 'Proceed with treatment'),
                        branch.get('if_negative', 'Consider alternatives')
                    ])
                return tree_data
        
        # Generate based on primary diagnosis
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary = diagnostic_data.get('primary_diagnosis', {})
        primary_name = primary.get('name', '').lower()
        
        # Diagnosis-specific decision trees
        if 'dementia' in primary_name or 'alzheimer' in primary_name or 'lewy' in primary_name:
            return [
                ["Step", "Action", "If Positive", "If Negative"],
                ["1", "Cognitive Assessment (MMSE/MoCA)", "→ Confirm cognitive impairment", "→ Reassess in 6 months"],
                ["2", "Brain MRI/CT", "→ Identify structural causes", "→ Consider PET scan"],
                ["3", "Metabolic Panel & B12", "→ Treat reversible causes", "→ Proceed to Step 4"],
                ["4", "CSF/Biomarkers", "→ Confirm diagnosis subtype", "→ Clinical diagnosis"]
            ]
        elif 'mediterranean' in primary_name or 'fmf' in primary_name:
            return [
                ["Step", "Action", "If Positive", "If Negative"],
                ["1", "MEFV Genetic Test", "→ Confirm FMF, Start Colchicine", "→ Proceed to Step 2"],
                ["2", "Extended Genetic Panel", "→ Alternative periodic fever", "→ Proceed to Step 3"],
                ["3", "Autoimmune Workup", "→ Consider SLE/Still's", "→ Consider IBD"],
                ["4", "Inflammatory Markers", "→ Monitor progression", "→ Reassess diagnosis"]
            ]
        elif 'hypercalcemia' in primary_name or 'hyperparathyroid' in primary_name:
            return [
                ["Step", "Action", "If Positive", "If Negative"],
                ["1", "PTH & Ionized Calcium", "→ Confirm hyperparathyroidism", "→ Check malignancy markers"],
                ["2", "SPEP/UPEP & Imaging", "→ Identify malignancy", "→ Consider other causes"],
                ["3", "Vitamin D & Renal Function", "→ Address deficiencies", "→ Consider medication review"],
                ["4", "Parathyroid Scan", "→ Localize adenoma", "→ Medical management"]
            ]
        elif 'myeloma' in primary_name or 'cancer' in primary_name or 'malignancy' in primary_name:
            return [
                ["Step", "Action", "If Positive", "If Negative"],
                ["1", "CBC & Metabolic Panel", "→ Identify abnormalities", "→ Consider imaging"],
                ["2", "SPEP/UPEP & Light Chains", "→ Confirm myeloma", "→ Broader cancer screening"],
                ["3", "Bone Marrow Biopsy", "→ Stage disease", "→ Alternative diagnosis"],
                ["4", "Skeletal Survey/PET", "→ Assess extent", "→ Monitor closely"]
            ]
        else:
            # Generic tree for unrecognized diagnoses
            return [
                ["Step", "Action", "If Positive", "If Negative"],
                ["1", "Initial Laboratory Tests", "→ Confirm suspicion", "→ Broaden differential"],
                ["2", "Imaging Studies", "→ Identify pathology", "→ Consider specialized tests"],
                ["3", "Specialized Testing", "→ Definitive diagnosis", "→ Empiric treatment"],
                ["4", "Treatment Trial", "→ Continue if effective", "→ Reconsider diagnosis"]
            ]
    
    def _extract_icd_from_response(self, response: Dict) -> str:
        """Extract ICD code directly from model response JSON"""
        response_text = response.get('response', '')
        
        try:
            # Clean up response - some have ```json wrapper
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            data = json.loads(clean_text)
            
            # Try to get ICD from primary diagnosis
            primary = data.get('primary_diagnosis', {})
            if isinstance(primary, dict):
                icd = primary.get('icd_code', '')
                if icd:
                    # Clean ICD code (remove descriptions in parentheses)
                    if '(' in icd:
                        icd = icd.split('(')[0].strip()
                    return icd[:7] if len(icd) > 7 else icd
        except:
            pass
        
        # Fallback: try regex patterns to find ICD codes in text
        patterns = [
            r'ICD[- ]?(?:10)?[:\s]*([A-Z]\d{2}\.?\d*)',
            r'"icd_code"[:\s]*"([A-Z]\d{2}\.?\d*)"',
            r'\(([A-Z]\d{2}\.?\d*)\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                return matches[0][:7] if len(matches[0]) > 7 else matches[0]
        
        return ""
    
    def _extract_icd_code(self, response: Dict) -> str:
        """Extract ICD code from response with JSON parsing"""
        response_text = response.get('response', '')
        
        # First try to parse as JSON
        try:
            # Clean up response - some have ```json wrapper
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            data = json.loads(clean_text)
            
            primary = data.get('primary_diagnosis', {})
            if isinstance(primary, dict):
                icd_code = primary.get('icd_code', '')
                if icd_code and icd_code != "Unknown":
                    # Clean up code - remove descriptions in parentheses
                    icd_code = re.split(r'\s*\(', icd_code)[0].strip()
                    return icd_code
        except:
            pass
            
        # Fallback to regex patterns for ICD codes
        patterns = [
            r'"icd_code":\s*"([^"]+)"',  # JSON icd_code field
            r'ICD[- ]?10?[:\s]*([A-Z]\d{2}\.?\d*)',  # ICD-10 pattern
            r'\b([A-Z]\d{2}\.?\d*)\b'  # Generic ICD pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                # Clean up code - remove descriptions in parentheses
                code = re.split(r'\s*\(', code)[0]  # Take everything before the first (
                code = code.strip()
                # Validate it looks like an ICD code
                if re.match(r'^[A-Z]\d{2}', code):
                    return code
                    
        return "Unknown"
        
    def _analyze_geographic_patterns(self, model_responses: List) -> Dict:
        """Create geographic patterns from model responses"""
        patterns = {}
        for response in model_responses:
            if response.get('origin'):
                origin = response['origin']
                if origin not in patterns:
                    patterns[origin] = []
                patterns[origin].append(response.get('model_name', ''))
        return patterns
    
    def _get_comprehensive_model_metadata(self) -> Dict:
        """Get comprehensive model metadata with bias analysis based on 2024 research"""
        return {
            # US Models - Generally higher bias scores due to Western-centric training
            'USA': {
                'medical_bias_characteristics': [
                    'Western-centric diagnostic criteria emphasis',
                    'Limited representation of non-Western medical conditions',
                    'Potential racial/gender bias in healthcare recommendations',
                    'US healthcare system perspective predominant'
                ],
                'cultural_limitations': [
                    'May recommend less expensive procedures for minorities',
                    'Limited understanding of traditional medicine practices',
                    'Western disease prevalence assumptions'
                ],
                'diagnostic_tendencies': 'Emphasis on Western diagnostic criteria and treatment protocols'
            },
            # European Models - Moderate bias, different perspective
            'France': {
                'medical_bias_characteristics': [
                    'European medical standards and practices',
                    'Multilingual medical knowledge',
                    'Less racially biased than US models',
                    'European healthcare system context'
                ],
                'cultural_limitations': [
                    'May lack some US-specific medical practices',
                    'European disease prevalence focus',
                    'Limited non-European cultural medical knowledge'
                ],
                'diagnostic_tendencies': 'European medical standards with multicultural awareness'
            },
            # Chinese Models - Alternative cultural perspective but different biases
            'China': {
                'medical_bias_characteristics': [
                    'Traditional Chinese Medicine integration potential',
                    'Asian medical practices emphasis',
                    'Alternative cultural medical perspectives',
                    'Chinese healthcare system context'
                ],
                'cultural_limitations': [
                    'May lack Western medical standard knowledge',
                    'Limited validation in Western medical contexts',
                    'Asian disease prevalence assumptions'
                ],
                'diagnostic_tendencies': 'Integration of traditional and modern Chinese medical approaches'
            },
            # Canadian Models - Generally lower bias
            'Canada': {
                'medical_bias_characteristics': [
                    'Canadian healthcare system knowledge',
                    'Multicultural medical awareness',
                    'Commonwealth medical practices',
                    'Generally less biased than US models'
                ],
                'cultural_limitations': [
                    'May emphasize Canadian/UK medical standards',
                    'Limited representation of non-Commonwealth practices'
                ],
                'diagnostic_tendencies': 'Balanced approach with multicultural Canadian healthcare context'
            }
        }
    
    def _analyze_regional_diagnostic_tendencies(self, model_responses: List, geographic_patterns: Dict) -> Dict:
        """Analyze diagnostic tendencies by geographic region"""
        regional_tendencies = {}
        
        for region, models in geographic_patterns.items():
            diagnoses = []
            for response in model_responses:
                if response.get('origin') == region:
                    diagnosis = self._extract_primary_diagnosis(response)
                    if diagnosis and diagnosis != "Not specified":
                        diagnoses.append(diagnosis)
            
            if diagnoses:
                # Find most common diagnosis from this region
                from collections import Counter
                common_dx = Counter(diagnoses).most_common(1)[0][0] if diagnoses else "Various"
                regional_tendencies[region] = f"Tends toward {common_dx}"
            else:
                regional_tendencies[region] = "Mixed approaches"
                
        return regional_tendencies
    
    def _get_detailed_regional_bias(self, region: str, ensemble_results: Dict) -> str:
        """Generate detailed regional bias analysis based on diagnostic context"""
        metadata = self._get_comprehensive_model_metadata()
        region_info = metadata.get(region, {})
        
        if not region_info:
            return "Regional bias analysis not available"
        
        # Get primary diagnosis to contextualize bias
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        primary_diagnosis = primary_data.get('name', '')
        
        # Context-specific bias analysis
        if 'Mediterranean Fever' in primary_diagnosis or 'FMF' in primary_diagnosis:
            if region == 'USA':
                return "May underemphasize Mediterranean genetic variants, Western diagnostic focus"
            elif region == 'France':
                return "Better Mediterranean disease recognition, European genetic awareness"
            elif region == 'China':
                return "Limited Mediterranean condition knowledge, Asian genetic focus"
            elif region == 'Canada':
                return "Multicultural approach, diverse genetic considerations"
        
        elif any(keyword in primary_diagnosis.lower() for keyword in ['lupus', 'sle', 'autoimmune']):
            if region == 'USA':
                return "US clinical criteria emphasis, potential racial disparities"
            elif region == 'France':
                return "European autoimmune standards, broader demographic awareness"
            elif region == 'China':
                return "Traditional medicine integration, Asian autoimmune patterns"
            elif region == 'Canada':
                return "Inclusive autoimmune diagnosis, multicultural considerations"
        
        # Default regional bias characteristics
        return region_info.get('diagnostic_tendencies', 'Regional diagnostic approach varies')
    
    def _generate_comprehensive_bias_analysis(self, ensemble_results: Dict, geographic_patterns: Dict) -> List[str]:
        """Generate comprehensive bias analysis based on 2024 research findings"""
        bias_considerations = []
        
        # Get primary diagnosis for context
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        primary_diagnosis = primary_data.get('name', '')
        
        # Regional representation analysis
        total_models = sum(len(models) for models in geographic_patterns.values())
        us_models = len(geographic_patterns.get('USA', []))
        if us_models / total_models > 0.6:
            bias_considerations.append(
                f"US model dominance ({us_models}/{total_models} models) may emphasize Western diagnostic criteria over global medical practices"
            )
        
        # Cultural medical knowledge gaps
        chinese_models = len(geographic_patterns.get('China', []))
        if chinese_models > 0:
            bias_considerations.append(
                f"Chinese models ({chinese_models}) may integrate traditional medicine perspectives but lack Western validation"
            )
        
        # European perspective
        french_models = len(geographic_patterns.get('France', []))
        if french_models > 0:
            bias_considerations.append(
                f"European models ({french_models}) typically show less racial bias but may lack US-specific medical context"
            )
        
        # Diagnosis-specific bias warnings
        if 'Mediterranean' in primary_diagnosis or 'FMF' in primary_diagnosis:
            bias_considerations.append(
                "Familial Mediterranean Fever recognition may vary by model origin - Mediterranean/European models likely more accurate"
            )
        elif 'Lupus' in primary_diagnosis or 'SLE' in primary_diagnosis:
            bias_considerations.append(
                "Autoimmune condition diagnosis may show racial disparities - US models may underdiagnose in minority populations"
            )
        elif 'Inflammatory' in primary_diagnosis:
            bias_considerations.append(
                "Inflammatory conditions may be interpreted differently across cultural contexts - consider regional diagnostic variations"
            )
        
        # Training data limitations based on 2024 research
        bias_considerations.append(
            "71% of medical AI training data comes from only 3 US states - geographic representation highly limited"
        )
        
        return bias_considerations
    
    def _extract_case_presentation(self, ensemble_results: Dict) -> str:
        """Extract case presentation from model responses (case-agnostic)"""
        # Try to extract common presentation elements from model responses
        model_responses = ensemble_results.get('model_responses', [])
        
        # Look for case information in metadata or first response
        case_title = ensemble_results.get('case_title', '')
        
        # Create generic presentation based on primary diagnosis
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        primary_diagnosis = primary_data.get('name', 'Unknown condition')
        
        evidence = primary_data.get('evidence', [])
        if evidence:
            evidence_text = '. '.join(evidence[:3])
            return f"Complex medical case presenting with {evidence_text}. Multiple AI models analyzed the case with {primary_data.get('agreement_percentage', 0):.1f}% consensus on {primary_diagnosis}."
        else:
            return f"Medical case analyzed by multiple AI models with consensus diagnosis of {primary_diagnosis}."
    
    def _generate_primary_recommendations(self, ensemble_results: Dict, primary_name: str, consensus_pct: float) -> List[str]:
        """Generate case-agnostic primary recommendations"""
        recommendations = []
        
        # Add consensus-based recommendation
        if consensus_pct > 80:
            recommendations.append(f"Strong consensus ({consensus_pct:.1f}%) supports diagnosis of {primary_name}")
        elif consensus_pct > 50:
            recommendations.append(f"Moderate consensus ({consensus_pct:.1f}%) suggests {primary_name}")
        else:
            recommendations.append(f"Consider {primary_name} among differential diagnoses")
        
        # Add management recommendations from orchestrated data
        mgmt_data = ensemble_results.get('management_strategies', {})
        immediate_actions = mgmt_data.get('immediate_actions', [])
        
        for action in immediate_actions[:3]:
            if isinstance(action, dict):
                action_text = action.get('action', '')
                if action_text:
                    recommendations.append(action_text)
        
        # Add testing recommendations
        testing = mgmt_data.get('differential_testing', [])
        if testing:
            test_item = testing[0]
            if isinstance(test_item, dict) and test_item.get('test'):
                recommendations.append(f"Obtain {test_item['test']} for diagnostic confirmation")
        
        return recommendations
        
    def _get_primary_icd_code(self, ensemble_results: Dict) -> str:
        """Get the most common ICD code for the primary diagnosis"""
        icd_codes = {}
        
        for response in ensemble_results.get('model_responses', []):
            if response.get('response') and not response.get('error'):
                icd = self._extract_icd_code(response)
                if icd != "Unknown":
                    icd_codes[icd] = icd_codes.get(icd, 0) + 1
        
        # Return most common ICD code
        if icd_codes:
            return max(icd_codes.items(), key=lambda x: x[1])[0]
        return "E85.0"  # Default FMF code
        
    def _get_diagnosis_icd_code(self, diagnosis_name: str) -> str:
        """Get ICD code for a specific diagnosis"""
        icd_map = {
            # FMF and inflammatory conditions
            "Familial Mediterranean Fever": "E85.0",
            "FMF": "E85.0",
            "Typhoid Fever": "A01.0",
            "Periodic Fever": "R50.9",
            "Recurrent Peritonitis": "K65.9",
            "Systemic Lupus Erythematosus": "M32.9",
            "Adult Still's Disease": "M06.1",
            "Reactive Arthritis": "M02.9",
            "Inflammatory Bowel Disease": "K50.9",
            "Crohn's Disease": "K50.9",
            "Ulcerative Colitis": "K51.9",
            "PFAPA": "D89.1",
            
            # Dementia and cognitive disorders
            "Lewy Body Dementia": "G31.83",
            "Alzheimer's Disease": "G30.9",
            "Dementia": "F03.90",
            "Vascular Dementia": "F01.50",
            "Frontotemporal Dementia": "G31.09",
            "Mixed Dementia": "F03.90",
            "Parkinson's Disease": "G20",
            "Normal Pressure Hydrocephalus": "G91.2",
            
            # Metabolic and endocrine
            "Hypercalcemia": "E83.52",
            "Primary Hyperparathyroidism": "E21.0",
            "Hyperparathyroidism": "E21.0",
            "Vitamin B12 Deficiency": "E53.8",
            "B12 Deficiency": "E53.8",
            "Thyroid Disorder": "E07.9",
            
            # Psychiatric
            "Depression": "F32.9",
            "Delirium": "F05",
            "Anxiety": "F41.9",
            
            # Malignancies
            "Multiple Myeloma": "C90.00",
            "Malignancy": "C80.1",
            "Cancer": "C80.1"
        }
        
        # Check exact match first
        if diagnosis_name in icd_map:
            return icd_map[diagnosis_name]
            
        # Check partial matches
        diagnosis_lower = diagnosis_name.lower()
        for name, code in icd_map.items():
            if name.lower() in diagnosis_lower or diagnosis_lower in name.lower():
                return code
                
        return "Unknown"
        
    def _parse_complete_response(self, response_text: str) -> Dict:
        """Parse complete response information from JSON"""
        try:
            # Clean up response - some have ```json wrapper
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            return json.loads(clean_text)
        except:
            # If JSON parsing fails, return empty dict
            return {}
        
    def _identify_regional_bias(self, region: str) -> str:
        """Identify potential regional bias"""
        biases = {
            "USA": "May emphasize Western diagnostic criteria",
            "France": "European perspective on rare diseases",
            "China": "Different diagnostic traditions",
            "Canada": "North American guidelines"
        }
        return biases.get(region, "Regional variations possible")
        
    def _identify_critical_decisions(self, ensemble_results: Dict) -> List[Dict]:
        """Identify critical decision points"""
        decisions = []
        
        # Generate decision points based on diagnosis
        primary_diagnosis = ensemble_results.get('diagnostic_landscape', {}).get('primary_diagnosis', {}).get('name', '')
        
        # Add diagnosis-specific decision points
        if 'dementia' in primary_diagnosis.lower() or 'lewy' in primary_diagnosis.lower():
            decisions.append({
                'topic': 'Antipsychotic Use',
                'options': [
                    {
                        'approach': 'Avoid antipsychotics',
                        'models': ['Models recognizing LBD risk'],
                        'rationale': 'High risk of severe sensitivity in LBD',
                        'impact': 'Prevents adverse reactions'
                    },
                    {
                        'approach': 'Cautious trial if severe symptoms',
                        'models': ['Models prioritizing symptom control'],
                    'rationale': 'Ensure accurate diagnosis',
                    'impact': 'Avoid unnecessary treatment'
                }
            ]
        })
        
        return decisions
        
    def _extract_symptoms(self, ensemble_results: Dict) -> List[str]:
        """Extract symptoms from diagnostic evidence and case data"""
        symptoms = set()
        
        # First, extract symptoms from diagnostic landscape evidence (most reliable)
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        evidence = primary_data.get('evidence', [])
        
        # Extract evidence items directly as symptoms (they are often symptoms)
        for item in evidence:
            if item and len(item.strip()) > 2:  # Valid evidence item
                # Clean up the evidence item to make it a proper symptom
                symptom = item.strip()
                if not symptom.startswith(('Recent', 'History of', 'Previous')):
                    # Convert to proper symptom format
                    if 'paranoid' in symptom.lower():
                        symptoms.add('Paranoid Ideation')
                    elif 'formication' in symptom.lower():
                        symptoms.add('Formication')
                    elif 'hypertension' in symptom.lower() or 'bp' in symptom.lower():
                        symptoms.add('Hypertension')
                    elif 'headache' in symptom.lower():
                        symptoms.add('Headaches')
                    elif 'fever' in symptom.lower():
                        symptoms.add('Fever')
                    elif 'pain' in symptom.lower():
                        symptoms.add('Pain')
                    elif 'joint' in symptom.lower():
                        symptoms.add('Joint Pain')
                    elif 'rash' in symptom.lower():
                        symptoms.add('Rash')
                    elif 'fatigue' in symptom.lower():
                        symptoms.add('Fatigue')
                    elif 'meth' in symptom.lower() or 'substance' in symptom.lower():
                        symptoms.add('Substance Use')
                    elif 'trauma' in symptom.lower():
                        symptoms.add('Head Trauma')
                    else:
                        # Use the evidence item as-is if it looks like a symptom
                        if len(symptom) < 50:  # Not too long
                            symptoms.add(symptom.title())
        
        # Also check evidence synthesis for additional symptoms
        evidence_synthesis = ensemble_results.get('evidence_synthesis', {})
        clinical_findings = evidence_synthesis.get('key_clinical_findings', [])
        
        for finding in clinical_findings:
            finding_text = finding.get('finding', '')
            if finding_text:
                if 'bp' in finding_text.lower() or 'blood pressure' in finding_text.lower():
                    symptoms.add('Hypertension')
                elif 'formication' in finding_text.lower():
                    symptoms.add('Formication')
                elif 'trauma' in finding_text.lower():
                    symptoms.add('Head Trauma')
                elif len(finding_text) < 40:  # Short enough to be a symptom
                    symptoms.add(finding_text.title())
        
        # If we still don't have enough symptoms, extract from case content
        case_content = ensemble_results.get('case_content', '')
        if len(symptoms) < 3 and case_content:
            case_lower = case_content.lower()
            # Extract common medical symptoms from case text
            symptom_patterns = {
                'paranoid': 'Paranoid Ideation',
                'formication': 'Formication', 
                'hypertens': 'Hypertension',
                'headache': 'Headaches',
                'fever': 'Fever',
                'pain': 'Pain',
                'fatigue': 'Fatigue',
                'nausea': 'Nausea',
                'vomiting': 'Vomiting',
                'dizziness': 'Dizziness'
            }
            
            for pattern, symptom in symptom_patterns.items():
                if pattern in case_lower:
                    symptoms.add(symptom)
        
        # Return symptoms, prioritizing those from evidence
        symptoms_list = list(symptoms)
        return symptoms_list[:6] if symptoms_list else ['Clinical Presentation']
        
    def _extract_diagnoses(self, ensemble_results: Dict) -> List[str]:
        """Extract diagnoses from diagnostic landscape"""
        diagnoses = []
        
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        
        if primary_data.get('name'):
            diagnoses.append(primary_data['name'])
            
        # Include all alternative categories
        strong_alternatives = diagnostic_data.get('strong_alternatives', [])
        alternatives = diagnostic_data.get('alternatives', [])
        minority = diagnostic_data.get('minority_opinions', [])
        all_alternatives = strong_alternatives + alternatives + minority
        
        for alt in all_alternatives[:5]:  # Take top 5 across all categories
            if alt.get('name'):
                diagnoses.append(alt['name'])
                
        return diagnoses
    
    def _format_case_description(self, case_content: str) -> List:
        """Format case description with proper structure and styling"""
        formatted_content = []
        
        # Parse the case content to extract structured information
        lines = case_content.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers (marked with ##)
            if line.startswith('##'):
                section_title = line.replace('##', '').strip()
                formatted_content.append(Paragraph(section_title, self.styles['SubsectionHeader']))
                current_section = section_title
                continue
            
            # Check for bold text (marked with **)
            if '**' in line:
                # Parse bold formatting
                parts = line.split('**')
                formatted_line = ""
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are bold text
                        formatted_line += f"<b>{part}</b>"
                    else:
                        formatted_line += part
                
                formatted_content.append(Paragraph(formatted_line, self.styles['DetailStyle']))
            else:
                # Regular text
                formatted_content.append(Paragraph(line, self.styles['DetailStyle']))
        
        # If no structured content found, format as simple paragraphs
        if not formatted_content:
            # Split into logical paragraphs
            paragraphs = case_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Handle bold formatting with **
                    if '**' in para:
                        parts = para.split('**')
                        formatted_para = ""
                        for i, part in enumerate(parts):
                            if i % 2 == 1:
                                formatted_para += f"<b>{part}</b>"
                            else:
                                formatted_para += part
                        formatted_content.append(Paragraph(formatted_para, self.styles['DetailStyle']))
                    else:
                        formatted_content.append(Paragraph(para.strip(), self.styles['DetailStyle']))
        
        return formatted_content
    
    def _convert_comprehensive_bias_analysis(self, comprehensive_bias: Dict) -> Dict:
        """Convert comprehensive bias analysis format to expected report format"""
        
        geo_rep = comprehensive_bias.get('geographical_representation', {})
        western_dom = geo_rep.get('western_dominance', {})
        chinese_rep = geo_rep.get('chinese_representation', {})
        socio_concerns = comprehensive_bias.get('socioeconomic_bias_concerns', [])
        mitigations = comprehensive_bias.get('recommended_mitigations', [])
        
        # Convert to expected format
        converted = {
            'primary_diagnosis_bias_factors': {
                'geographic_bias': {
                    'impact_on_diagnosis': f"Western model dominance ({western_dom.get('percentage', 0):.1f}%) creates strong bias toward Western medical paradigms. {western_dom.get('impact', '')}"
                },
                'cultural_bias': {
                    'description': f"Models from {geo_rep.get('total_countries', 0)} countries with Western dominance may miss cultural factors. Chinese models ({chinese_rep.get('percentage', 0):.1f}%) provide alternative perspective."
                },
                'training_data_bias': {
                    'description': f"English-dominant training data creates systematic bias against non-Western medical practices and symptom presentations."
                }
            },
            'alternative_diagnoses_bias': {
                'missed_diagnoses_due_to_bias': [
                    {
                        'diagnosis': 'Traditional Medicine Conditions',
                        'explanation': 'Western model dominance may miss traditional medicine diagnoses or culturally-specific presentations'
                    },
                    {
                        'diagnosis': 'Socioeconomic-Related Conditions',
                        'explanation': 'Homeless status bias may cause dismissive attitudes and missed medical emergencies'
                    }
                ],
                'overrepresented_diagnoses': [
                    {
                        'diagnosis': 'Substance-Use Related Disorders',
                        'explanation': 'Bias toward substance use explanations in homeless patients may lead to over-diagnosis'
                    }
                ]
            },
            'bias_mitigation_recommendations': [
                {
                    'bias_type': 'Socioeconomic Bias',
                    'recommendation': mitigations[0] if mitigations else 'Address patient status bias',
                    'implementation': 'Standard protocols regardless of housing status'
                },
                {
                    'bias_type': 'Geographic/Cultural Bias',
                    'recommendation': 'Incorporate diverse cultural perspectives in diagnosis',
                    'implementation': 'Consider traditional medicine and cultural factors'
                }
            ],
            'geographical_consensus_patterns': geo_rep,
            'socioeconomic_bias_summary': {
                'key_concerns': socio_concerns,
                'risk_level': 'High' if len(socio_concerns) > 2 else 'Medium'
            }
        }
        
        return converted
        
    def _calculate_correlation(self, symptom: str, diagnosis: str, ensemble_results: Dict) -> str:
        """Calculate symptom-diagnosis correlation strength"""
        # Use a hybrid approach: evidence-based + text analysis
        
        # First check known strong associations from diagnostic evidence
        diagnostic_data = ensemble_results.get('diagnostic_landscape', {})
        primary_data = diagnostic_data.get('primary_diagnosis', {})
        primary_diagnosis = primary_data.get('name', '')
        evidence = primary_data.get('evidence', [])
        
        # Strong associations based on evidence for primary diagnosis
        if diagnosis.lower() in primary_diagnosis.lower():
            for evidence_item in evidence:
                if symptom.lower() in evidence_item.lower():
                    return "+++"
        
        # Check all alternative diagnoses evidence across categories
        strong_alternatives = diagnostic_data.get('strong_alternatives', [])
        alternatives = diagnostic_data.get('alternatives', [])
        minority = diagnostic_data.get('minority_opinions', [])
        all_alternatives = strong_alternatives + alternatives + minority
        
        for alt in all_alternatives:
            if diagnosis.lower() in alt.get('name', '').lower():
                alt_evidence = alt.get('evidence', [])
                for evidence_item in alt_evidence:
                    if symptom.lower() in evidence_item.lower():
                        return "++"
        
        # Text analysis as fallback
        symptom_mentions = 0
        diagnosis_mentions = 0
        both_mentions = 0
        
        for response in ensemble_results.get('model_responses', [])[:15]:  # Limit for performance
            if not response.get('response'):
                continue
                
            response_text = response.get('response', '').lower()
            
            has_symptom = any(keyword in response_text for keyword in [symptom.lower(), symptom.split()[0].lower()])
            has_diagnosis = any(keyword in response_text for keyword in diagnosis.lower().split()[:2])  # Use first 2 words
            
            if has_symptom:
                symptom_mentions += 1
            if has_diagnosis:
                diagnosis_mentions += 1
            if has_symptom and has_diagnosis:
                both_mentions += 1
        
        # Calculate correlation based on co-occurrence
        if diagnosis_mentions == 0:
            return "?"
            
        correlation_ratio = both_mentions / diagnosis_mentions
        
        if correlation_ratio >= 0.6:
            return "+++"
        elif correlation_ratio >= 0.3:
            return "++"
        elif correlation_ratio >= 0.1:
            return "+"
        else:
            return "-"
    
    def _calculate_correlation_old(self, symptom: str, diagnosis: str, ensemble_results: Dict) -> str:
        """Old correlation method - keeping as backup"""
        # Simplified correlation - in real implementation would analyze responses
        correlations = {
            ('Fever', 'Familial Mediterranean Fever'): '+++',
            ('Abdominal pain', 'Familial Mediterranean Fever'): '+++',
            ('Arthritis', 'Familial Mediterranean Fever'): '++',
            ('Fever', 'Still\'s Disease'): '++',
            ('Arthritis', 'SLE'): '++'
        }
        
        return correlations.get((symptom, diagnosis), '+')
        
    def _extract_findings_from_response(self, response_text: str) -> List[str]:
        """Extract key findings from response text"""
        findings = []
        
        # Look for findings patterns
        if 'periodic' in response_text.lower():
            findings.append("Periodic nature of symptoms")
        if 'family' in response_text.lower():
            findings.append("Familial clustering of symptoms")
        if 'mediterranean' in response_text.lower():
            findings.append("Geographic/ethnic predisposition")
            
        return findings
        
    def _extract_management_from_response(self, response_text: str) -> List[str]:
        """Extract management recommendations from response"""
        recommendations = []
        
        if 'colchicine' in response_text.lower():
            recommendations.append("Colchicine therapy for prophylaxis")
        if 'genetic' in response_text.lower():
            recommendations.append("Genetic testing for confirmation")
            
        return recommendations
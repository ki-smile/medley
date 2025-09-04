"""
Enhanced Clinical Decision Report Generator for Medley
Emphasizes diversity of diagnoses and comprehensive clinical decision support
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
import json

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
        PageBreak, KeepTogether, Flowable, Image, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Line, Rect, String
    from reportlab.graphics import renderPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ModelMetadata:
    """Database of model metadata including release dates and training information"""
    
    # Model release dates and key characteristics (based on public announcements)
    MODEL_INFO = {
        "openai/gpt-5": {
            "short_name": "GPT-5",
            "release_date": "2025-01",
            "organization": "OpenAI",
            "architecture": "Transformer",
            "training_data": "Web text, books, code (cutoff 2024)",
            "key_strengths": "General reasoning, code, creativity",
            "potential_biases": "Western/English-centric, recent events"
        },
        "openai/gpt-4o": {
            "short_name": "GPT-4o",
            "release_date": "2024-05",
            "organization": "OpenAI",
            "architecture": "Multimodal Transformer",
            "training_data": "Web text, books, code, images",
            "key_strengths": "Vision, reasoning, speed",
            "potential_biases": "Western medical practices"
        },
        "anthropic/claude-opus-4.1": {
            "short_name": "Claude Opus 4.1",
            "release_date": "2025-01",
            "organization": "Anthropic",
            "architecture": "Constitutional AI",
            "training_data": "Diverse web content (cutoff 2024)",
            "key_strengths": "Safety, nuanced reasoning, ethics",
            "potential_biases": "Conservative medical advice, safety-focused"
        },
        "anthropic/claude-3-opus-20240229": {
            "short_name": "Claude 3 Opus",
            "release_date": "2024-02",
            "organization": "Anthropic",
            "architecture": "Constitutional AI",
            "training_data": "Diverse web content",
            "key_strengths": "Complex reasoning, safety",
            "potential_biases": "Conservative medical advice"
        },
        "google/gemini-2.5-pro": {
            "short_name": "Gemini 2.5 Pro",
            "release_date": "2024-12",
            "organization": "Google DeepMind",
            "architecture": "Multimodal Transformer",
            "training_data": "Web, books, images, code",
            "key_strengths": "Multimodal understanding, scientific reasoning",
            "potential_biases": "Academic/research focus"
        },
        "google/gemini-2.0-flash-exp": {
            "short_name": "Gemini 2.0 Flash",
            "release_date": "2024-12",
            "organization": "Google DeepMind",
            "architecture": "Efficient Transformer",
            "training_data": "Web, books, optimized datasets",
            "key_strengths": "Speed, efficiency",
            "potential_biases": "May miss nuanced details"
        },
        "google/gemma-2-9b-it": {
            "short_name": "Gemma 2 9B",
            "release_date": "2024-06",
            "organization": "Google",
            "architecture": "Transformer",
            "training_data": "Curated datasets",
            "key_strengths": "Open model, safety",
            "potential_biases": "Limited medical knowledge"
        },
        "x-ai/grok-4": {
            "short_name": "Grok 4",
            "release_date": "2024-12",
            "organization": "xAI",
            "architecture": "Transformer",
            "training_data": "Real-time data, social media",
            "key_strengths": "Current events, social context",
            "potential_biases": "Social media influence, contemporary focus"
        },
        "x-ai/grok-2-1212": {
            "short_name": "Grok 2",
            "release_date": "2024-08",
            "organization": "xAI",
            "architecture": "Transformer",
            "training_data": "Web, social media",
            "key_strengths": "Real-time information",
            "potential_biases": "Social media perspectives"
        },
        "deepseek/deepseek-chat-v3-0324": {
            "short_name": "DeepSeek V3",
            "release_date": "2024-03",
            "organization": "DeepSeek",
            "architecture": "MOE Transformer",
            "training_data": "Chinese/English web, scientific papers",
            "key_strengths": "Technical reasoning, mathematics",
            "potential_biases": "Chinese medical practice influence"
        },
        "deepseek/deepseek-r1": {
            "short_name": "DeepSeek R1",
            "release_date": "2024-11",
            "organization": "DeepSeek",
            "architecture": "Reasoning-optimized",
            "training_data": "Technical and scientific data",
            "key_strengths": "Step-by-step reasoning",
            "potential_biases": "Technical focus"
        },
        "mistralai/mistral-7b-instruct": {
            "short_name": "Mistral 7B",
            "release_date": "2023-09",
            "organization": "Mistral AI",
            "architecture": "Transformer",
            "training_data": "Multilingual web data",
            "key_strengths": "Efficiency, European languages",
            "potential_biases": "European medical standards"
        },
        "mistralai/mistral-large": {
            "short_name": "Mistral Large",
            "release_date": "2024-02",
            "organization": "Mistral AI",
            "architecture": "Large Transformer",
            "training_data": "Multilingual datasets",
            "key_strengths": "Multilingual, reasoning",
            "potential_biases": "European perspectives"
        },
        "meta-llama/llama-3.2-3b-instruct": {
            "short_name": "Llama 3.2 3B",
            "release_date": "2024-09",
            "organization": "Meta",
            "architecture": "Transformer",
            "training_data": "Public web data",
            "key_strengths": "Open source, efficient",
            "potential_biases": "Limited medical training"
        },
        "qwen/qwen-2.5-coder-32b-instruct": {
            "short_name": "Qwen 2.5 32B",
            "release_date": "2024-11",
            "organization": "Alibaba",
            "architecture": "Transformer",
            "training_data": "Chinese/English data",
            "key_strengths": "Code, technical content",
            "potential_biases": "Programming focus"
        }
    }
    
    @classmethod
    def get_short_name(cls, model_name: str) -> str:
        """Get short display name for a model"""
        info = cls.get_model_info(model_name)
        return info.get("short_name", model_name.split("/")[-1][:15])
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, Any]:
        """Get metadata for a specific model"""
        # Try exact match first
        if model_name in cls.MODEL_INFO:
            return cls.MODEL_INFO[model_name]
        
        # Try partial match
        for key, info in cls.MODEL_INFO.items():
            if key.split("/")[-1] in model_name or model_name in key:
                return info
        
        # Return default for unknown models
        return {
            "release_date": "Unknown",
            "organization": "Unknown",
            "architecture": "Unknown",
            "training_data": "Unknown",
            "key_strengths": "General purpose",
            "potential_biases": "Standard training biases"
        }


class EnhancedReportGenerator:
    """Generate comprehensive clinical decision support reports"""
    
    def __init__(self):
        self.model_metadata = ModelMetadata()
        
    def generate_report(
        self,
        ensemble_results: Dict[str, Any],
        output_format: str = "pdf",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate enhanced clinical decision report
        
        Args:
            ensemble_results: Results from ensemble analysis
            output_format: Format for report (pdf, html, markdown)
            output_file: Path to save report
            
        Returns:
            Path to saved report or report content
        """
        if output_format == "pdf":
            if not PDF_AVAILABLE:
                raise ImportError("PDF generation requires reportlab: pip install reportlab")
            return self._generate_pdf_report(ensemble_results, output_file)
        elif output_format == "html":
            return self._generate_html_report(ensemble_results, output_file)
        else:  # markdown
            return self._generate_markdown_report(ensemble_results, output_file)
    
    def _analyze_diagnostic_landscape(self, ensemble_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the full diagnostic landscape from all models"""
        
        landscape = {
            "primary_diagnosis": None,
            "primary_agreement": 0,
            "strong_alternatives": [],
            "minority_opinions": [],
            "unique_perspectives": [],
            "diagnostic_clusters": {},
            "reasoning_patterns": {},
            "total_unique_diagnoses": 0
        }
        
        # Collect all diagnoses with full details
        diagnosis_details = defaultdict(lambda: {
            "models": [],
            "origins": [],
            "reasoning": [],
            "confidence_scores": [],
            "treatment_suggestions": [],
            "diagnostic_tests": []
        })
        
        # Process each model's response
        for i, model_resp in enumerate(ensemble_results.get("model_responses", [])):
            if model_resp.get("error"):
                continue
                
            model_name = model_resp.get("model_name", "Unknown")
            origin = model_resp.get("origin", "Unknown")
            
            # Get parsed response
            parsed = ensemble_results.get("parsed_responses", [])[i]
            if not parsed:
                continue
            
            # Handle both object and dict formats
            if hasattr(parsed, 'differential_diagnoses'):
                differential_diagnoses = parsed.differential_diagnoses
            elif isinstance(parsed, dict) and 'differential_diagnoses' in parsed:
                differential_diagnoses = parsed['differential_diagnoses']
            else:
                continue
            
            # Process each diagnosis from this model
            for diag_entry in differential_diagnoses:
                diagnosis = diag_entry.get('diagnosis', '').strip()
                if not diagnosis:
                    continue
                
                # Standardize diagnosis name
                diagnosis_std = self._standardize_diagnosis(diagnosis)
                if not diagnosis_std:
                    continue
                
                details = diagnosis_details[diagnosis_std]
                details["models"].append(model_name)
                details["origins"].append(origin)
                details["reasoning"].append(diag_entry.get('reasoning', ''))
                
                # Extract treatment and diagnostic suggestions if present
                if hasattr(parsed, 'recommended_tests'):
                    details["diagnostic_tests"].extend(parsed.recommended_tests)
                elif isinstance(parsed, dict) and 'recommended_tests' in parsed:
                    details["diagnostic_tests"].extend(parsed['recommended_tests'])
                    
                if hasattr(parsed, 'treatment_plan'):
                    details["treatment_suggestions"].append(parsed.treatment_plan)
                elif isinstance(parsed, dict) and 'treatment_plan' in parsed:
                    details["treatment_suggestions"].append(parsed['treatment_plan'])
        
        # Sort diagnoses by frequency
        sorted_diagnoses = sorted(
            diagnosis_details.items(),
            key=lambda x: len(x[1]["models"]),
            reverse=True
        )
        
        if sorted_diagnoses:
            # Primary diagnosis
            primary_name, primary_details = sorted_diagnoses[0]
            total_responding = len([m for m in ensemble_results.get("model_responses", []) 
                                   if not m.get("error")])
            
            landscape["primary_diagnosis"] = primary_name
            # Fix for >100% bug - ensure we don't count duplicates
            unique_models = len(set(primary_details["models"]))
            landscape["primary_agreement"] = min(unique_models / total_responding * 100, 100)
            
            # Strong alternatives (>25% agreement)
            for diag_name, details in sorted_diagnoses[1:]:
                agreement = len(details["models"]) / total_responding * 100
                if agreement >= 25:
                    landscape["strong_alternatives"].append({
                        "diagnosis": diag_name,
                        "agreement": agreement,
                        "models": details["models"],
                        "key_reasoning": self._extract_key_reasoning(details["reasoning"])
                    })
            
            # Minority opinions (mentioned by 1-2 models but potentially important)
            for diag_name, details in sorted_diagnoses:
                if len(details["models"]) <= 2:
                    landscape["minority_opinions"].append({
                        "diagnosis": diag_name,
                        "models": details["models"],
                        "reasoning": self._extract_key_reasoning(details["reasoning"])
                    })
            
            # Unique perspectives (single model only)
            for diag_name, details in sorted_diagnoses:
                if len(details["models"]) == 1:
                    landscape["unique_perspectives"].append({
                        "diagnosis": diag_name,
                        "model": details["models"][0],
                        "origin": details["origins"][0],
                        "reasoning": details["reasoning"][0] if details["reasoning"] else ""
                    })
        
        landscape["total_unique_diagnoses"] = len(diagnosis_details)
        
        # Cluster diagnoses by category
        landscape["diagnostic_clusters"] = self._cluster_diagnoses(diagnosis_details)
        
        return landscape
    
    def _analyze_management_strategies(self, ensemble_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze management and treatment strategies across models"""
        
        strategies = {
            "immediate_actions": [],
            "diagnostic_tests": {},
            "treatment_options": {},
            "monitoring_plans": [],
            "specialist_referrals": []
        }
        
        # Process each model's recommendations
        for i, model_resp in enumerate(ensemble_results.get("model_responses", [])):
            if model_resp.get("error"):
                continue
            
            parsed = ensemble_results.get("parsed_responses", [])[i]
            if not parsed:
                continue
            
            # Extract management recommendations
            next_steps = None
            if hasattr(parsed, 'next_steps'):
                next_steps = parsed.next_steps
            elif isinstance(parsed, dict) and 'next_steps' in parsed:
                next_steps = parsed['next_steps']
                
            if next_steps:
                for step in next_steps:
                    if "immediate" in step.lower() or "urgent" in step.lower():
                        strategies["immediate_actions"].append(step)
            
            recommended_tests = None
            if hasattr(parsed, 'recommended_tests'):
                recommended_tests = parsed.recommended_tests
            elif isinstance(parsed, dict) and 'recommended_tests' in parsed:
                recommended_tests = parsed['recommended_tests']
                
            if recommended_tests:
                for test in recommended_tests:
                    if test not in strategies["diagnostic_tests"]:
                        strategies["diagnostic_tests"][test] = []
                    strategies["diagnostic_tests"][test].append(model_resp.get("model_name"))
            
            treatment_plan = None
            if hasattr(parsed, 'treatment_plan'):
                treatment_plan = parsed.treatment_plan
            elif isinstance(parsed, dict) and 'treatment_plan' in parsed:
                treatment_plan = parsed['treatment_plan']
                
            if treatment_plan:
                if treatment_plan not in strategies["treatment_options"]:
                    strategies["treatment_options"][treatment_plan] = []
                strategies["treatment_options"][treatment_plan].append(model_resp.get("model_name"))
        
        return strategies
    
    def _analyze_bias_sources(self, ensemble_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential sources of bias in model responses"""
        
        bias_analysis = {
            "geographic_biases": {},
            "temporal_biases": [],
            "training_biases": [],
            "architectural_biases": []
        }
        
        # Geographic bias analysis
        geographic_patterns = defaultdict(list)
        for i, model_resp in enumerate(ensemble_results.get("model_responses", [])):
            if model_resp.get("error"):
                continue
            
            origin = model_resp.get("origin", "Unknown")
            parsed = ensemble_results.get("parsed_responses", [])[i]
            
            differential_diagnoses = None
            if parsed:
                if hasattr(parsed, 'differential_diagnoses'):
                    differential_diagnoses = parsed.differential_diagnoses
                elif isinstance(parsed, dict) and 'differential_diagnoses' in parsed:
                    differential_diagnoses = parsed['differential_diagnoses']
                    
            if differential_diagnoses:
                for diag in differential_diagnoses[:1]:  # Primary diagnosis
                    geographic_patterns[origin].append(diag.get('diagnosis', 'Unknown'))
        
        # Identify geographic divergences
        if len(geographic_patterns) > 1:
            origins = list(geographic_patterns.keys())
            for i, origin1 in enumerate(origins):
                for origin2 in origins[i+1:]:
                    diags1 = set(geographic_patterns[origin1])
                    diags2 = set(geographic_patterns[origin2])
                    if diags1 != diags2:
                        bias_analysis["geographic_biases"][f"{origin1} vs {origin2}"] = {
                            "unique_to_first": list(diags1 - diags2),
                            "unique_to_second": list(diags2 - diags1)
                        }
        
        # Temporal bias (based on model release dates)
        model_dates = []
        for model_resp in ensemble_results.get("model_responses", []):
            if not model_resp.get("error"):
                model_name = model_resp.get("model_name")
                info = self.model_metadata.get_model_info(model_name)
                if info["release_date"] != "Unknown":
                    model_dates.append((model_name, info["release_date"]))
        
        if model_dates:
            # Sort by date and check for patterns
            model_dates.sort(key=lambda x: x[1])
            oldest = model_dates[0]
            newest = model_dates[-1]
            
            if oldest[1] != newest[1]:
                bias_analysis["temporal_biases"].append(
                    f"Model release dates span from {oldest[1]} to {newest[1]}, "
                    "potentially affecting knowledge of recent medical developments"
                )
        
        # Training data biases
        training_patterns = defaultdict(list)
        for model_resp in ensemble_results.get("model_responses", []):
            if not model_resp.get("error"):
                model_name = model_resp.get("model_name")
                info = self.model_metadata.get_model_info(model_name)
                training_patterns[info["training_data"]].append(model_name)
        
        for training_type, models in training_patterns.items():
            if training_type != "Unknown":
                bias_analysis["training_biases"].append({
                    "data_type": training_type,
                    "models": models,
                    "potential_impact": self._assess_training_impact(training_type)
                })
        
        return bias_analysis
    
    def _generate_pdf_report(self, results: Dict[str, Any], output_file: str) -> str:
        """Generate comprehensive PDF report with new format"""
        
        if not output_file:
            raise ValueError("Output file path required for PDF generation")
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        
        # Get analysis results
        landscape = self._analyze_diagnostic_landscape(results)
        strategies = self._analyze_management_strategies(results)
        bias_analysis = self._analyze_bias_sources(results)
        consensus = results.get("consensus_analysis", {})
        
        # Build PDF elements
        elements = []
        styles = self._get_pdf_styles()
        
        # Page 1: Clinical Decision Summary
        elements.extend(self._create_page1_clinical_summary(
            results, landscape, strategies, styles, bias_analysis
        ))
        
        # Page break
        elements.append(PageBreak())
        
        # Page 2: Model Diversity & Bias Analysis
        elements.extend(self._create_page2_diversity_analysis(
            results, landscape, bias_analysis, styles
        ))
        
        # Page 3: Detailed Model Responses (if space permits)
        elements.append(PageBreak())
        elements.extend(self._create_page3_detailed_responses(
            results, styles
        ))
        
        # Build PDF
        doc.build(elements)
        
        return output_file
    
    def _create_page1_clinical_summary(
        self, 
        results: Dict[str, Any],
        landscape: Dict[str, Any],
        strategies: Dict[str, Any],
        styles: Dict,
        bias_analysis: Optional[Dict[str, Any]] = None
    ) -> List:
        """Create Page 1: Clinical Decision Summary"""
        
        elements = []
        
        # Header
        elements.append(Paragraph(
            "MEDLEY Clinical Decision Report",
            styles['CustomTitle']
        ))
        
        case_id = results.get("case_id", "Unknown")
        case_title = results.get("case_title", "")
        elements.append(Paragraph(
            f"Case {case_id}: {case_title}",
            styles['SectionHeading']
        ))
        
        elements.append(Spacer(1, 20))
        
        # Case Overview Box
        case_desc = results.get("case_description", {})
        elements.append(Paragraph("Case Overview", styles['BoxTitle']))
        
        case_data = []
        if case_desc.get("patient_info"):
            patient_text = Paragraph(
                self._wrap_text_for_paragraph(case_desc["patient_info"], 300),
                styles['Normal']
            )
            case_data.append(["Patient:", patient_text])
        if case_desc.get("presentation"):
            presentation_text = Paragraph(
                self._wrap_text_for_paragraph(case_desc["presentation"], 300),
                styles['Normal']
            )
            case_data.append(["Presentation:", presentation_text])
        if case_desc.get("key_findings"):
            findings_text = Paragraph(
                self._wrap_text_for_paragraph(case_desc["key_findings"], 300),
                styles['Normal']
            )
            case_data.append(["Key Findings:", findings_text])
        
        if case_data:
            case_table = Table(case_data, colWidths=[1.2*inch, 5.3*inch])
            case_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8ff')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4169e1')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(case_table)
        
        elements.append(Spacer(1, 20))
        
        # Diagnostic Landscape
        elements.append(Paragraph("Diagnostic Landscape", styles['SectionHeading']))
        
        # Primary diagnosis with agreement
        primary_data = []
        if landscape["primary_diagnosis"]:
            primary_data.append([
                "PRIMARY DIAGNOSIS",
                landscape["primary_diagnosis"],
                f"{landscape['primary_agreement']:.0f}% Agreement"
            ])
        
        # Strong alternatives
        for alt in landscape["strong_alternatives"][:3]:
            primary_data.append([
                "Strong Alternative",
                alt["diagnosis"],
                f"{alt['agreement']:.0f}% Agreement"
            ])
        
        # Important minority opinions
        for minority in landscape["minority_opinions"][:2]:
            # Use short model names
            short_models = [self.model_metadata.get_short_name(m) for m in minority.get('models', [])[:2]]
            primary_data.append([
                "Minority Opinion",
                self._clean_text_for_table(minority["diagnosis"], 35),
                f"By {', '.join(short_models)}"
            ])
        
        if primary_data:
            diag_table = Table(primary_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
            diag_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#28a745')),
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#ffc107')),
                ('BACKGROUND', (0, 2), (0, -1), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(diag_table)
        
        elements.append(Spacer(1, 20))
        
        # Management Strategy Matrix
        elements.append(Paragraph("Management Strategies", styles['SectionHeading']))
        
        mgmt_data = [
            ["Category", "Recommended Actions", "Supporting Models"]
        ]
        
        # Immediate actions
        if strategies["immediate_actions"]:
            mgmt_data.append([
                "Immediate",
                "; ".join(strategies["immediate_actions"][:2]),
                "High Priority"
            ])
        
        # Top diagnostic tests
        for test, models in list(strategies["diagnostic_tests"].items())[:3]:
            mgmt_data.append([
                "Diagnostic",
                test,
                f"{len(models)} models"
            ])
        
        # Treatment options
        for treatment, models in list(strategies["treatment_options"].items())[:2]:
            mgmt_data.append([
                "Treatment",
                treatment[:50],
                f"{len(models)} models"
            ])
        
        if len(mgmt_data) > 1:
            mgmt_table = Table(mgmt_data, colWidths=[1.2*inch, 3.3*inch, 2*inch])
            mgmt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(mgmt_table)
        
        elements.append(Spacer(1, 20))
        
        # Critical Decision Points
        elements.append(Paragraph("Critical Decision Points", styles['AlertHeading']))
        
        decision_points = []
        
        # Based on consensus level
        consensus_level = results.get("consensus_analysis", {}).get("consensus_level", "None")
        if consensus_level == "None" or consensus_level == "Weak":
            decision_points.append(
                "⚠️ Low consensus indicates complex presentation - consider specialist consultation"
            )
        
        # Based on minority opinions
        if len(landscape["minority_opinions"]) > 3:
            decision_points.append(
                "⚠️ Multiple minority diagnoses suggest atypical presentation"
            )
        
        # Based on geographic divergence
        if bias_analysis and bias_analysis.get("geographic_biases"):
            decision_points.append(
                "⚠️ Geographic variation in diagnoses - consider regional disease patterns"
            )
        
        for point in decision_points:
            elements.append(Paragraph(point, styles['AlertText']))
        
        # Summary statistics at bottom
        elements.append(Spacer(1, 30))
        stats_data = [
            [
                f"Models: {results.get('models_queried', 0)}",
                f"Responded: {results.get('consensus_analysis', {}).get('responding_models', 0)}",
                f"Unique Diagnoses: {landscape['total_unique_diagnoses']}",
                f"Consensus: {consensus_level}"
            ]
        ]
        
        stats_table = Table(stats_data, colWidths=[1.65*inch] * 4)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(stats_table)
        
        # Add spacer to push footer to bottom of page
        # Calculate approximate remaining space (letter page is 11 inches, we've used about 8-9)
        from reportlab.platypus import FrameBreak
        elements.append(Spacer(1, 1*inch))  # Variable spacer to push content down
        
        # Add footer near bottom margin
        elements.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.grey,
            spaceBefore=1,
            spaceAfter=3
        ))
        
        footer_text = (
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Medley Medical AI Ensemble System | "
            f"Developed by Farhad Abtahi, SMAILE at Karolinska Institutet"
        )
        footer_style = ParagraphStyle(
            name='FooterBottom',
            parent=styles['Footer'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=10
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
    
    def _create_page2_diversity_analysis(
        self,
        results: Dict[str, Any],
        landscape: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        styles: Dict
    ) -> List:
        """Create Page 2: Model Diversity & Bias Analysis"""
        
        elements = []
        
        # Header
        elements.append(Paragraph(
            "Model Diversity & Bias Analysis",
            styles['PageTitle']
        ))
        
        elements.append(Spacer(1, 20))
        
        # Model Response Overview
        elements.append(Paragraph("Model Response Patterns", styles['SectionHeading']))
        
        # Create model response table with metadata
        model_data = [
            ["Model", "Origin", "Release", "Primary Diagnosis", "Confidence"]
        ]
        
        for i, model_resp in enumerate(results.get("model_responses", [])):
            if model_resp.get("error"):
                continue
            
            model_name = model_resp.get("model_name", "Unknown")
            origin = model_resp.get("origin", "Unknown")
            
            # Get model metadata
            info = self.model_metadata.get_model_info(model_name)
            release = info["release_date"]
            short_name = self.model_metadata.get_short_name(model_name)
            
            # Get primary diagnosis
            parsed = results.get("parsed_responses", [])[i]
            differential_diagnoses = None
            if parsed:
                if hasattr(parsed, 'differential_diagnoses'):
                    differential_diagnoses = parsed.differential_diagnoses
                elif isinstance(parsed, dict) and 'differential_diagnoses' in parsed:
                    differential_diagnoses = parsed['differential_diagnoses']
                    
            if differential_diagnoses:
                primary_diag = self._clean_text_for_table(
                    differential_diagnoses[0].get('diagnosis', 'Unknown'), 30
                )
            else:
                primary_diag = "No diagnosis"
            
            # Estimate confidence
            primary_diag_text = landscape.get("primary_diagnosis") or ""
            confidence = "High" if primary_diag and primary_diag_text and primary_diag in primary_diag_text else "Varied"
            
            model_data.append([
                short_name,
                origin[:6],  # Shorten origin
                release,
                primary_diag,
                confidence
            ])
        
        if len(model_data) > 1:
            model_table = Table(
                model_data[:11],  # Limit to 10 models + header
                colWidths=[1.2*inch, 0.6*inch, 0.7*inch, 2.2*inch, 0.8*inch]
            )
            model_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f4f8')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(model_table)
        
        elements.append(Spacer(1, 20))
        
        # Bias Source Analysis
        elements.append(Paragraph("Identified Bias Sources", styles['SectionHeading']))
        
        bias_data = []
        
        # Geographic biases
        if bias_analysis["geographic_biases"]:
            for comparison, differences in list(bias_analysis["geographic_biases"].items())[:2]:
                bias_data.append([
                    "Geographic",
                    comparison,
                    f"Divergent diagnoses based on regional training"
                ])
        
        # Temporal biases
        for temporal in bias_analysis["temporal_biases"][:2]:
            bias_data.append([
                "Temporal",
                "Release dates vary",
                temporal[:80]
            ])
        
        # Training data biases
        for training in bias_analysis["training_biases"][:2]:
            bias_data.append([
                "Training Data",
                training["data_type"][:30],
                training["potential_impact"][:80]
            ])
        
        if bias_data:
            bias_table = Table(bias_data, colWidths=[1.2*inch, 1.8*inch, 3.5*inch])
            bias_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(bias_table)
        
        elements.append(Spacer(1, 20))
        
        # Unique Perspectives Section
        elements.append(Paragraph("Unique Model Perspectives", styles['SectionHeading']))
        
        unique_data = []
        for unique in landscape["unique_perspectives"][:5]:
            unique_data.append([
                self.model_metadata.get_short_name(unique["model"]),
                self._clean_text_for_table(unique["diagnosis"], 35),
                self._clean_text_for_table(unique["reasoning"], 80) if unique["reasoning"] else "No reasoning"
            ])
        
        if unique_data:
            unique_table = Table(
                [["Model", "Unique Diagnosis", "Reasoning"]] + unique_data,
                colWidths=[1.2*inch, 1.8*inch, 3.5*inch]
            )
            unique_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4ecf7')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(unique_table)
        
        elements.append(Spacer(1, 20))
        
        # Diagnostic Clustering
        elements.append(Paragraph("Diagnostic Categories", styles['SectionHeading']))
        
        clusters = landscape.get("diagnostic_clusters", {})
        if clusters:
            cluster_text = []
            for category, diagnoses in list(clusters.items())[:4]:
                cluster_text.append(f"• <b>{category}:</b> {', '.join(diagnoses[:3])}")
            
            for text in cluster_text:
                elements.append(Paragraph(text, styles['Normal']))
        
        return elements
    
    def _create_page3_detailed_responses(
        self,
        results: Dict[str, Any],
        styles: Dict
    ) -> List:
        """Create Page 3: Detailed Model Responses"""
        
        elements = []
        
        # Header
        elements.append(Paragraph(
            "Detailed Model Responses",
            styles['PageTitle']
        ))
        
        elements.append(Spacer(1, 15))
        
        # Process each model's detailed response
        model_count = 0
        for i, model_resp in enumerate(results.get("model_responses", [])):
            if model_resp.get("error"):
                continue
            
            if model_count >= 6:  # Limit to 6 models for space
                break
            
            model_name = model_resp.get("model_name", "Unknown")
            origin = model_resp.get("origin", "Unknown")
            
            # Get parsed response
            parsed = results.get("parsed_responses", [])[i]
            if not parsed:
                continue
                
            # Handle both object and dict formats
            differential_diagnoses = None
            if hasattr(parsed, 'differential_diagnoses'):
                differential_diagnoses = parsed.differential_diagnoses
            elif isinstance(parsed, dict) and 'differential_diagnoses' in parsed:
                differential_diagnoses = parsed['differential_diagnoses']
                
            if not differential_diagnoses:
                continue
            
            # Model header with short name
            short_name = self.model_metadata.get_short_name(model_name)
            elements.append(Paragraph(
                f"<b>{short_name}</b> ({origin})",
                styles['ModelHeader']
            ))
            
            # Differential diagnoses with wrapped text
            diag_data = []
            for j, diag in enumerate(differential_diagnoses[:3], 1):
                diagnosis = Paragraph(
                    self._clean_text_for_table(diag.get('diagnosis', 'Unknown'), 50),
                    styles['Normal']
                )
                reasoning_text = self._clean_text_for_table(
                    diag.get('reasoning', 'No reasoning provided'), 200
                )
                reasoning = Paragraph(reasoning_text, styles['Normal'])
                diag_data.append([
                    f"{j}.",
                    diagnosis,
                    reasoning
                ])
            
            if diag_data:
                diag_table = Table(diag_data, colWidths=[0.3*inch, 1.7*inch, 4.5*inch])
                diag_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                elements.append(diag_table)
            
            elements.append(Spacer(1, 10))
            model_count += 1
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.grey,
            spaceBefore=1,
            spaceAfter=1
        ))
        
        footer_text = (
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Medley Medical AI Ensemble System | "
            f"Developed by Farhad Abtahi, SMAILE at Karolinska Institutet"
        )
        elements.append(Paragraph(footer_text, styles['Footer']))
        
        return elements
    
    def _clean_text_for_table(self, text: str, max_length: int = 50) -> str:
        """Clean and truncate text for table display"""
        if not text:
            return ""
        
        # Remove markdown formatting
        import re
        text = re.sub(r'\*\*+([^*]+)\*\*+', r'\1', text)  # Handle multiple asterisks
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # Remove numbered lists
        
        # Clean up malformed output and special characters
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.replace('**', '').replace('\n', ' ')
        text = text.replace('""', '').replace("''", '')  # Remove empty quotes
        
        # Remove incomplete sentences or fragments
        if text.lower().startswith("on labs"):
            text = "Laboratory findings"
        elif "CAPS)**" in text or "CAPS)*" in text:
            text = "Autoinflammatory syndromes (TRAPS, CAPS)"
        
        # Clean up "Traps" and similar malformed terms
        text = text.replace("Traps", "TRAPS")
        
        # Truncate if needed
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text.strip()
    
    def _wrap_text_for_paragraph(self, text: str, max_width: int = 400) -> str:
        """Wrap text for proper display in PDF paragraphs"""
        if not text:
            return ""
        
        # Clean the text first
        text = self._clean_text_for_table(text, max_width)
        
        # Add line breaks for very long text
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > 80:  # 80 chars per line
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '<br/>'.join(lines)
    
    def _get_pdf_styles(self) -> Dict:
        """Get custom PDF styles"""
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='PageTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_LEFT
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='BoxTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2980b9'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='AlertHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#e74c3c'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='AlertText',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            textColor=colors.HexColor('#c0392b')
        ))
        
        styles.add(ParagraphStyle(
            name='ModelHeader',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        
        return styles
    
    def _standardize_diagnosis(self, diagnosis: str) -> Optional[str]:
        """Standardize diagnosis name for comparison"""
        
        if not diagnosis:
            return None
        
        diagnosis_lower = diagnosis.lower().strip()
        
        # Filter out generic advice instead of actual diagnoses
        generic_advice_patterns = [
            "contact your doctor",
            "see your doctor",
            "consult a physician",
            "seek medical attention",
            "describe your symptoms",
            "keep track of",
            "monitor your",
            "call your doctor",
            "visit the emergency",
            "get medical help",
            "reach out",
            "talk to your",
            "speak with"
        ]
        
        # Check if this is generic advice
        for pattern in generic_advice_patterns:
            if pattern in diagnosis_lower:
                return None  # Filter out generic advice
        
        # Filter out non-medical metadata
        non_medical = [
            "age", "gender", "sex", "history", "patient",
            "information", "case", "analysis", "unknown"
        ]
        
        for term in non_medical:
            if diagnosis_lower == term or diagnosis_lower.startswith(f"{term}:"):
                return None
        
        # Common standardizations
        standardizations = {
            "fmf": "Familial Mediterranean Fever",
            "familial mediterranean fever": "Familial Mediterranean Fever",
            "sle": "Systemic Lupus Erythematosus",
            "lupus": "Systemic Lupus Erythematosus",
            "ibd": "Inflammatory Bowel Disease",
            "crohn": "Crohn's Disease",
            "behcet": "Behcet's Disease"
        }
        
        for pattern, standard in standardizations.items():
            if pattern in diagnosis_lower:
                return standard
        
        return diagnosis.title()
    
    def _extract_key_reasoning(self, reasoning_list: List[str]) -> str:
        """Extract key points from reasoning"""
        
        if not reasoning_list:
            return ""
        
        # Get first non-empty reasoning
        for reasoning in reasoning_list:
            if reasoning and len(reasoning) > 20:
                return reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
        
        return ""
    
    def _cluster_diagnoses(self, diagnosis_details: Dict) -> Dict[str, List[str]]:
        """Cluster diagnoses by category"""
        
        clusters = {
            "Autoimmune/Inflammatory": [],
            "Infectious": [],
            "Genetic/Hereditary": [],
            "Neoplastic": [],
            "Other": []
        }
        
        for diagnosis in diagnosis_details.keys():
            diag_lower = diagnosis.lower()
            
            if any(term in diag_lower for term in ["autoimmune", "inflammatory", "arthritis", "lupus"]):
                clusters["Autoimmune/Inflammatory"].append(diagnosis)
            elif any(term in diag_lower for term in ["infection", "viral", "bacterial", "fever"]):
                clusters["Infectious"].append(diagnosis)
            elif any(term in diag_lower for term in ["familial", "hereditary", "genetic"]):
                clusters["Genetic/Hereditary"].append(diagnosis)
            elif any(term in diag_lower for term in ["cancer", "tumor", "neoplasm", "lymphoma"]):
                clusters["Neoplastic"].append(diagnosis)
            else:
                clusters["Other"].append(diagnosis)
        
        # Remove empty clusters
        return {k: v for k, v in clusters.items() if v}
    
    def _assess_training_impact(self, training_type: str) -> str:
        """Assess potential impact of training data type"""
        
        training_lower = training_type.lower()
        
        if "social media" in training_lower:
            return "May include non-medical perspectives"
        elif "chinese" in training_lower:
            return "Traditional Chinese medicine influence possible"
        elif "european" in training_lower:
            return "European medical standards emphasized"
        elif "academic" in training_lower:
            return "Research-focused, may favor rare conditions"
        elif "web" in training_lower:
            return "Broad knowledge but variable quality"
        else:
            return "Standard medical training data"
    
    def _generate_html_report(self, results: Dict[str, Any], output_file: Optional[str]) -> str:
        """Generate HTML version of enhanced report"""
        
        # Get analysis results
        landscape = self._analyze_diagnostic_landscape(results)
        strategies = self._analyze_management_strategies(results)
        bias_analysis = self._analyze_bias_sources(results)
        
        # Build HTML content
        html = self._build_html_report(results, landscape, strategies, bias_analysis)
        
        # Save if output file specified
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html)
            return output_file
        
        return html
    
    def _generate_markdown_report(self, results: Dict[str, Any], output_file: Optional[str]) -> str:
        """Generate markdown version of enhanced report"""
        
        # Get analysis results
        landscape = self._analyze_diagnostic_landscape(results)
        strategies = self._analyze_management_strategies(results)
        bias_analysis = self._analyze_bias_sources(results)
        
        # Build markdown content
        md = self._build_markdown_report(results, landscape, strategies, bias_analysis)
        
        # Save if output file specified
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(md)
            return output_file
        
        return md
    
    def _build_html_report(
        self,
        results: Dict[str, Any],
        landscape: Dict[str, Any],
        strategies: Dict[str, Any],
        bias_analysis: Dict[str, Any]
    ) -> str:
        """Build HTML report content"""
        
        # Implementation similar to PDF but in HTML format
        # This would be a full HTML document with embedded CSS
        # For brevity, returning a placeholder
        return "<html><body><h1>Enhanced Report</h1><p>Full HTML implementation pending</p></body></html>"
    
    def _build_markdown_report(
        self,
        results: Dict[str, Any],
        landscape: Dict[str, Any],
        strategies: Dict[str, Any],
        bias_analysis: Dict[str, Any]
    ) -> str:
        """Build markdown report content"""
        
        lines = []
        
        # Header
        lines.append("# MEDLEY Clinical Decision Report")
        lines.append("")
        lines.append(f"**Case**: {results.get('case_id')} - {results.get('case_title')}")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Diagnostic Landscape
        lines.append("## Diagnostic Landscape")
        lines.append("")
        if landscape["primary_diagnosis"]:
            lines.append(f"### Primary Diagnosis: {landscape['primary_diagnosis']} ({landscape['primary_agreement']:.0f}% agreement)")
        
        if landscape["strong_alternatives"]:
            lines.append("### Strong Alternatives")
            for alt in landscape["strong_alternatives"]:
                lines.append(f"- **{alt['diagnosis']}**: {alt['agreement']:.0f}% agreement")
        
        if landscape["minority_opinions"]:
            lines.append("### Important Minority Opinions")
            for minority in landscape["minority_opinions"][:5]:
                # Use short model names
                short_models = [self.model_metadata.get_short_name(m) for m in minority.get('models', [])[:2]]
                lines.append(f"- **{minority['diagnosis']}**: Suggested by {', '.join(short_models)}")
        
        lines.append("")
        
        # Management Strategies
        lines.append("## Management Strategies")
        if strategies["immediate_actions"]:
            lines.append("### Immediate Actions")
            for action in strategies["immediate_actions"]:
                lines.append(f"- {action}")
        
        if strategies["diagnostic_tests"]:
            lines.append("### Recommended Diagnostic Tests")
            for test, models in list(strategies["diagnostic_tests"].items())[:5]:
                lines.append(f"- **{test}**: Recommended by {len(models)} models")
        
        lines.append("")
        
        # Bias Analysis
        lines.append("## Bias Analysis")
        if bias_analysis["geographic_biases"]:
            lines.append("### Geographic Variations")
            for comparison, diffs in bias_analysis["geographic_biases"].items():
                lines.append(f"- **{comparison}**: Different diagnostic patterns observed")
        
        if bias_analysis["temporal_biases"]:
            lines.append("### Temporal Factors")
            for bias in bias_analysis["temporal_biases"]:
                lines.append(f"- {bias}")
        
        lines.append("")
        lines.append("---")
        lines.append("*Developed by Farhad Abtahi - SMAILE at Karolinska Institutet*")
        
        return "\n".join(lines)
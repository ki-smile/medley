#!/usr/bin/env python
"""
General Medical AI Pipeline - Case Agnostic
Processes any medical case with proper case separation and caching
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from model_metadata_2025 import get_comprehensive_model_metadata, get_geographical_distribution

def print_progress_bar(completed, total, prefix='Progress', suffix='Complete', length=50):
    """Print a progress bar"""
    filled_length = int(length * completed // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    percent = f"{100 * completed / total:.1f}"
    print(f'\r{prefix} |{bar}| {percent}% {suffix} ({completed}/{total})', end='', flush=True)

class GeneralMedicalPipeline:
    """
    General pipeline for medical case analysis with proper case separation
    """
    
    def __init__(self, case_id: str):
        """
        Initialize pipeline for a specific case
        
        Args:
            case_id: Unique case identifier (e.g., "Case_1", "Case_2", "Case_3")
        """
        self.case_id = case_id
        self.cache_dir = Path.cwd() / "cache"
        self.case_cache_dir = self.cache_dir / "responses" / case_id
        self.orchestrator_cache_dir = self.cache_dir / "orchestrator" / case_id
        self.reports_dir = Path.cwd() / "reports"
        
        # Create directories
        self.case_cache_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator_cache_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Initialized pipeline for {case_id}")
        print(f"   💾 Case cache: {self.case_cache_dir}")
        print(f"   🧠 Orchestrator cache: {self.orchestrator_cache_dir}")
        print(f"   📄 Reports: {self.reports_dir}")
    
    def get_all_available_models(self):
        """Get all available models from metadata"""
        metadata = get_comprehensive_model_metadata()
        return list(metadata.keys())
    
    def load_case_cached_responses(self):
        """Load cached responses for this specific case only"""
        cached_responses = []
        invalid_cache_files = []  # Track files that need retry
        
        print(f"📥 Loading cached responses for {self.case_id}...")
        
        if not self.case_cache_dir.exists():
            print(f"❌ No cache directory found for {self.case_id}")
            return []
        
        cached_files = list(self.case_cache_dir.glob("*.json"))
        print(f"  📁 Found {len(cached_files)} cached files")
        
        for file in cached_files:
            try:
                # Check file size first - if less than 1KB, likely invalid
                file_size = file.stat().st_size
                if file_size < 1024:  # Less than 1KB
                    print(f"    ⚠️  Small file ({file_size} bytes): {file.name} - marking for retry")
                    invalid_cache_files.append(file)
                    continue
                
                with open(file, 'r') as f:
                    data = json.load(f)
                
                content = data.get('content', '')
                # Check if content is valid and substantial (at least 50 chars)
                if content and len(content.strip()) > 50:
                    model_name = file.stem.replace('_', '/').replace(':', ':')
                    cached_responses.append({
                        "model_name": model_name,
                        "response": content,
                        "response_time": data.get('latency', 1.0),
                        "cached": True,
                        "case_id": self.case_id,
                        "timestamp": data.get('timestamp', 'Unknown'),
                        "tokens_used": data.get('tokens_used', 0),
                        "input_tokens": data.get('input_tokens', 0),
                        "output_tokens": data.get('output_tokens', 0)
                    })
                    print(f"    ✅ Loaded {model_name}")
                else:
                    print(f"    ❌ Empty/insufficient response in {file.name} - marking for retry")
                    invalid_cache_files.append(file)
            except Exception as e:
                print(f"    ❌ Error loading {file.name}: {e} - marking for retry")
                invalid_cache_files.append(file)
        
        # Delete invalid cache files so they can be retried
        if invalid_cache_files:
            print(f"  🗑️  Removing {len(invalid_cache_files)} invalid cache files for retry...")
            for file in invalid_cache_files:
                try:
                    file.unlink()
                    print(f"    ✅ Removed {file.name}")
                except Exception as e:
                    print(f"    ❌ Could not remove {file.name}: {e}")
        
        print(f"✅ Loaded {len(cached_responses)} valid cached responses for {self.case_id}")
        return cached_responses
    
    def query_missing_models(self, cached_models, all_models, prompt, llm_manager):
        """Query models not in cache for this case"""
        cached_model_names = {r['model_name'] for r in cached_models}
        missing_models = [m for m in all_models if m not in cached_model_names]
        
        print(f"🔍 Found {len(missing_models)} models not cached for {self.case_id}")
        
        if not missing_models:
            print("✅ All models already cached for this case!")
            return []
        
        new_responses = []
        successful = 0
        failed = 0
        
        print(f"🤖 Querying {len(missing_models)} missing models for {self.case_id}...")
        
        for i, model_id in enumerate(missing_models):
            print_progress_bar(i, len(missing_models), prefix=f'Querying {self.case_id}', suffix='models processed')
            
            try:
                from src.medley.utils.config import ModelConfig
                model_config = ModelConfig(
                    name=model_id.split('/')[-1],
                    provider=model_id.split('/')[0],
                    model_id=model_id,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                print(f"\\n🔄 [{i+1}/{len(missing_models)}] {model_id}")
                start_time = time.time()
                
                response = llm_manager.query_model(model_config, prompt)
                elapsed = time.time() - start_time
                
                if not response.error:
                    new_responses.append({
                        "model_name": model_id,
                        "response": response.content,
                        "response_time": elapsed,
                        "cached": False,
                        "case_id": self.case_id,
                        "timestamp": datetime.now().isoformat(),
                        "tokens_used": response.tokens_used,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens
                    })
                    successful += 1
                    print(f"    ✅ Success: {len(response.content):,} chars in {elapsed:.2f}s")
                    
                    # Save to case-specific cache
                    cache_file = self.case_cache_dir / f"{model_id.replace('/', '_').replace(':', '_')}.json"
                    cache_data = {
                        "case_id": self.case_id,
                        "model_id": model_id,
                        "content": response.content,
                        "latency": elapsed,
                        "timestamp": datetime.now().isoformat(),
                        "cached_at": datetime.now().isoformat(),
                        "tokens_used": response.tokens_used,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens
                    }
                    
                    with open(cache_file, 'w') as f:
                        json.dump(cache_data, f, indent=2)
                    print(f"    💾 Cached to {cache_file.name}")
                    
                else:
                    failed += 1
                    print(f"    ❌ Error: {response.error}")
                    
            except Exception as e:
                failed += 1
                print(f"\\n    💥 Exception with {model_id}: {str(e)[:100]}")
        
        print_progress_bar(len(missing_models), len(missing_models), prefix=f'Querying {self.case_id}', suffix='models processed')
        print(f"\\n\\n📊 Query Results for {self.case_id}:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {successful/len(missing_models)*100 if missing_models else 100:.1f}%")
        
        return new_responses
    
    def analyze_consensus(self, all_responses):
        """Analyze diagnostic consensus for this case using comprehensive diagnosis extraction"""
        print(f"\\n🧠 Analyzing diagnostic consensus for {self.case_id}...")
        
        # Import comprehensive diagnosis extraction functions
        from collections import defaultdict
        
        # Track all diagnoses (primary and differential)
        primary_counts = defaultdict(int)
        differential_counts = defaultdict(int)
        total_counts = defaultdict(int)
        all_icd_codes = defaultdict(set)
        model_diagnoses = defaultdict(lambda: defaultdict(list))
        model_origins = {}
        
        # Get model metadata for origin analysis
        metadata = get_comprehensive_model_metadata()
        
        for i, response in enumerate(all_responses):
            print_progress_bar(i, len(all_responses), prefix=f'Analyzing {self.case_id}', suffix='responses processed')
            
            try:
                model_name = response['model_name']
                resp_text = str(response['response'])
                
                # Get model origin
                model_info = metadata.get(model_name, {})
                origin = model_info.get('origin_country', 'Unknown')
                
                # Extract ALL diagnoses (primary + differential) using comprehensive extraction
                primary, differentials, icd_codes = self._extract_all_diagnoses_from_response(resp_text)
                
                # Count primary diagnosis
                if primary:
                    normalized_primary = self._normalize_diagnosis_name(primary)
                    primary_counts[normalized_primary] += 1
                    total_counts[normalized_primary] += 1
                    # Remove /free suffix for consistent model naming
                    clean_model_name = model_name.replace('/free', '')
                    model_diagnoses[normalized_primary]['primary'].append(clean_model_name)
                    
                    if primary in icd_codes:
                        all_icd_codes[normalized_primary].add(icd_codes[primary])
                    
                    # Track by origin
                    if origin not in model_origins:
                        model_origins[origin] = {}
                    model_origins[origin][normalized_primary] = model_origins[origin].get(normalized_primary, 0) + 1
                
                # Count differential diagnoses
                for diff in differentials:
                    normalized_diff = self._normalize_diagnosis_name(diff)
                    differential_counts[normalized_diff] += 1
                    total_counts[normalized_diff] += 1
                    # Remove /free suffix for consistent model naming
                    clean_model_name = model_name.replace('/free', '')
                    model_diagnoses[normalized_diff]['differential'].append(clean_model_name)
                    
                    if diff in icd_codes:
                        all_icd_codes[normalized_diff].add(icd_codes[diff])
                    
            except Exception as e:
                print(f"\\n    Error analyzing {response.get('model_name', 'unknown')}: {e}")
        
        print_progress_bar(len(all_responses), len(all_responses), prefix=f'Analyzing {self.case_id}', suffix='responses processed')
        
        # Calculate results using TOTAL counts (primary + differential)
        total_models = len(all_responses)
        sorted_diag = sorted(total_counts.items(), key=lambda x: x[1], reverse=True) if total_counts else []
        
        # Determine primary based on highest total count
        primary = sorted_diag[0] if sorted_diag else ('Unknown Condition', 0)
        
        print(f"\\n📊 COMPREHENSIVE DIAGNOSTIC CONSENSUS for {self.case_id}:")
        print(f"   📈 Total Models Analyzed: {total_models}")
        print(f"   🥇 Primary: {primary[0]} (Total: {primary[1]} | Primary: {primary_counts.get(primary[0], 0)} | Differential: {differential_counts.get(primary[0], 0)})")
        print(f"      Agreement: {primary[1]/total_models*100:.1f}%")
        
        for rank, (diag, count) in enumerate(sorted_diag[1:6], 2):  # Top 5
            prim_count = primary_counts.get(diag, 0)
            diff_count = differential_counts.get(diag, 0)
            print(f"   📍 #{rank}: {diag} (Total: {count} | Primary: {prim_count} | Differential: {diff_count} = {count/total_models*100:.1f}%)")
        
        print(f"\\n🌍 GEOGRAPHICAL CONSENSUS PATTERNS for {self.case_id}:")
        for origin, origin_diagnoses in model_origins.items():
            if origin != 'Unknown' and origin_diagnoses:
                top_dx = max(origin_diagnoses.items(), key=lambda x: x[1])
                origin_total = sum(origin_diagnoses.values())
                print(f"   🏳️  {origin}: {top_dx[0]} ({top_dx[1]}/{origin_total} = {top_dx[1]/origin_total*100:.1f}%)")
        
        return {
            'primary_counts': dict(primary_counts),
            'differential_counts': dict(differential_counts),
            'total_counts': dict(total_counts),
            'sorted_diagnoses': sorted_diag,
            'primary': primary,
            'total_models': total_models,
            'icd_codes': {k: list(v) for k, v in all_icd_codes.items()},
            'model_diagnoses': {k: dict(v) for k, v in model_diagnoses.items()},
            'geographical_patterns': model_origins
        }
    
    def _normalize_diagnosis_name(self, diagnosis_name):
        """Normalize diagnosis name for consistent counting using ICD-10 database"""
        from src.medley.utils.icd10_database import get_icd10_database
        
        icd_db = get_icd10_database()
        return icd_db.normalize_diagnosis(diagnosis_name)
    
    def _normalize_diagnosis_name_old(self, diagnosis_name):
        """Legacy normalization method - kept for reference"""
        if not diagnosis_name:
            return diagnosis_name
        
        # Clean the diagnosis name
        diagnosis_lower = diagnosis_name.lower().strip()
        
        # Remove parenthetical additions for normalization
        if '(' in diagnosis_lower:
            base = diagnosis_lower.split('(')[0].strip()
        else:
            base = diagnosis_lower
        
        # Comprehensive normalizations - map all variations to canonical form
        normalizations = {
            # FMF variations
            "familial mediterranean fever": "Familial Mediterranean Fever",
            "familial mediterranean fever (fmf)": "Familial Mediterranean Fever",
            "fmf": "Familial Mediterranean Fever",
            
            # IBD/Crohn's - all map to most specific diagnosis
            "crohn's disease": "Crohn's Disease",
            "crohn disease": "Crohn's Disease",
            "crohn's disease (inflammatory bowel disease)": "Crohn's Disease",
            "inflammatory bowel disease (crohn's disease)": "Crohn's Disease",
            "inflammatory bowel disease (ibd) - crohn's disease": "Crohn's Disease",
            "recurrent peritonitis due to inflammatory bowel disease": "Crohn's Disease",
            "inflammatory bowel disease": "Inflammatory Bowel Disease",
            "inflammatory bowel disease (ibd)": "Inflammatory Bowel Disease",
            "ibd": "Inflammatory Bowel Disease",
            
            # SLE/Lupus - all map to one canonical form
            "systemic lupus erythematosus": "Systemic Lupus Erythematosus",
            "systemic lupus erythematosus (sle)": "Systemic Lupus Erythematosus",
            "sle": "Systemic Lupus Erythematosus",
            "lupus": "Systemic Lupus Erythematosus",
            
            # Arthritis types
            "reactive arthritis": "Reactive Arthritis",
            "septic arthritis": "Septic Arthritis",
            "infectious arthritis": "Septic Arthritis",  # Merge with septic
            "infectious arthritis (e.g., septic arthritis)": "Septic Arthritis",
            "gouty arthritis": "Gouty Arthritis",
            "gout": "Gouty Arthritis",
            
            # Porphyria - all variations to one form
            "acute intermittent porphyria": "Acute Intermittent Porphyria",
            "acute intermittent porphyria (aip)": "Acute Intermittent Porphyria",
            "aip": "Acute Intermittent Porphyria",
            "porphyria": "Acute Intermittent Porphyria",
            
            # Appendicitis variations
            "acute appendicitis": "Acute Appendicitis", 
            "appendicitis": "Acute Appendicitis",
            "appendicitis (recurrent or atypical)": "Acute Appendicitis",
            
            # Other conditions
            "behcet's disease": "Behçet's Disease",
            "behçet's disease": "Behçet's Disease",
            "behcet disease": "Behçet's Disease",
            "adult-onset still's disease": "Adult-Onset Still's Disease",
            "adult still's disease": "Adult-Onset Still's Disease",
            "aosd": "Adult-Onset Still's Disease",
            "tuberculosis": "Tuberculosis",
            "tb": "Tuberculosis",
            "peritonitis": "Peritonitis",
            "acute recurrent peritonitis": "Peritonitis",
            "recurrent peritonitis": "Peritonitis",
            "recurrent peritonitis due to amyloidosis": "Peritonitis with Amyloidosis",
            "rheumatic fever": "Rheumatic Fever",
            "traps": "TRAPS",
            "periodic fever syndrome": "Periodic Fever Syndrome",
            "gout": "Gouty Arthritis"
        }
        
        # Check exact match first (case-insensitive)
        if diagnosis_lower in normalizations:
            return normalizations[diagnosis_lower]
        
        # Also check the base name (without parentheses)
        if base in normalizations:
            return normalizations[base]
        
        # Return original with proper capitalization if no match
        return diagnosis_name
    
    def _extract_all_diagnoses_from_response(self, response_text):
        """
        Extract ALL diagnoses (primary and differential) from a response
        Returns: (primary_diagnosis, differential_diagnoses, icd_codes)
        """
        primary_diagnosis = None
        differential_diagnoses = []
        icd_codes = {}
        
        # Try to parse as JSON first
        import json
        try:
            # Clean up markdown if present
            clean_text = response_text
            if '```json' in clean_text:
                clean_text = clean_text.split('```json')[1].split('```')[0]
            elif '```' in clean_text:
                clean_text = clean_text.split('```')[1].split('```')[0]
                
            parsed = json.loads(clean_text)
            
            # Extract primary diagnosis
            if 'primary_diagnosis' in parsed:
                primary = parsed['primary_diagnosis']
                if isinstance(primary, dict):
                    primary_diagnosis = primary.get('name', '')
                    if primary_diagnosis:
                        icd = primary.get('icd_code') or primary.get('icd10_code') or primary.get('icd')
                        if icd:
                            icd_codes[primary_diagnosis] = icd
                elif isinstance(primary, str):
                    primary_diagnosis = primary
            
            # Extract differential diagnoses
            if 'differential_diagnoses' in parsed:
                for diff in parsed['differential_diagnoses']:
                    diff_name = None
                    if isinstance(diff, dict):
                        diff_name = diff.get('name') or diff.get('diagnosis')
                        if diff_name:
                            icd = diff.get('icd_code') or diff.get('icd10_code') or diff.get('icd')
                            if icd:
                                icd_codes[diff_name] = icd
                    elif isinstance(diff, str):
                        diff_name = diff
                    
                    if diff_name:
                        differential_diagnoses.append(diff_name)
            
            # Also check for alternative_diagnoses field
            if 'alternative_diagnoses' in parsed:
                for alt in parsed['alternative_diagnoses']:
                    alt_name = None
                    if isinstance(alt, dict):
                        alt_name = alt.get('name') or alt.get('diagnosis')
                        if alt_name:
                            icd = alt.get('icd_code') or alt.get('icd10_code') or alt.get('icd')
                            if icd:
                                icd_codes[alt_name] = icd
                    elif isinstance(alt, str):
                        alt_name = alt
                    
                    if alt_name and alt_name not in differential_diagnoses:
                        differential_diagnoses.append(alt_name)
                        
        except (json.JSONDecodeError, TypeError):
            # Fallback to the old extraction method for primary only
            primary_diagnosis = self._extract_primary_diagnosis_text(response_text)
        
        return primary_diagnosis, differential_diagnoses, icd_codes
    
    def _extract_primary_diagnosis(self, response_text):
        """Legacy method for extracting primary diagnosis from text"""
        return self._extract_primary_diagnosis_text(response_text)
    
    def _extract_primary_diagnosis_text(self, response_text):
        """Extract primary diagnosis from response text (case-agnostic)"""
        # Common medical conditions (defined first for use in JSON parsing)
        conditions = {
            'familial mediterranean fever': 'Familial Mediterranean Fever',
            'fmf': 'Familial Mediterranean Fever',
            'mediterranean fever': 'Familial Mediterranean Fever',
            'alzheimer': "Alzheimer's Disease", 
            'dementia': 'Dementia',
            'lewy body': 'Lewy Body Dementia',
            'vascular dementia': 'Vascular Dementia',
            'psychosis': 'Substance-Induced Psychosis',
            'substance-induced psychosis': 'Substance-Induced Psychosis',
            'methamphetamine psychosis': 'Methamphetamine-Induced Psychosis',
            'hypertensive emergency': 'Hypertensive Emergency',
            'hypertensive crisis': 'Hypertensive Emergency',
            'hypertensive encephalopathy': 'Hypertensive Encephalopathy',
            'delusional parasitosis': 'Delusional Parasitosis',
            'brain injury': 'Traumatic Brain Injury',
            'traumatic brain injury': 'Traumatic Brain Injury',
            'tbi': 'Traumatic Brain Injury',
            'substance withdrawal': 'Substance Withdrawal',
            'lupus': 'Systemic Lupus Erythematosus',
            'sle': 'Systemic Lupus Erythematosus',
            # Add more conditions for Case 1
            "crohn's disease": "Crohn's Disease",
            'crohn disease': "Crohn's Disease",
            'inflammatory bowel disease': 'Inflammatory Bowel Disease',
            'ibd': 'Inflammatory Bowel Disease',
            'ulcerative colitis': 'Ulcerative Colitis',
            "behcet's disease": "Behçet's Disease",
            'behcet disease': "Behçet's Disease",
            'behçet': "Behçet's Disease",
            "still's disease": "Adult-Onset Still's Disease",
            'adult still': "Adult-Onset Still's Disease",
            'aosd': "Adult-Onset Still's Disease",
            'reactive arthritis': 'Reactive Arthritis',
            'septic arthritis': 'Septic Arthritis',
            'infectious arthritis': 'Infectious Arthritis',
            'tuberculosis': 'Tuberculosis',
            'tb': 'Tuberculosis',
            'appendicitis': 'Acute Appendicitis',
            'peritonitis': 'Peritonitis',
            'periodic fever': 'Periodic Fever Syndrome',
            'traps': 'TRAPS',
            'pfapa': 'PFAPA Syndrome',
            'autoinflammatory': 'Autoinflammatory Disease',
            'porphyria': 'Acute Intermittent Porphyria',
            'gout': 'Gouty Arthritis',
            'ankylosing spondylitis': 'Ankylosing Spondylitis',
            'psoriatic arthritis': 'Psoriatic Arthritis',
            'rheumatic fever': 'Rheumatic Fever',
            'irritable bowel': 'Irritable Bowel Syndrome',
            'ibs': 'Irritable Bowel Syndrome'
        }
        
        # First try to parse as JSON
        import json
        try:
            # Clean up markdown if present
            clean_text = response_text
            if '```json' in clean_text:
                clean_text = clean_text.split('```json')[1].split('```')[0]
            elif '```' in clean_text:
                clean_text = clean_text.split('```')[1].split('```')[0]
            
            parsed = json.loads(clean_text)
            if 'primary_diagnosis' in parsed:
                primary = parsed['primary_diagnosis']
                diagnosis_name = None
                if isinstance(primary, dict) and 'name' in primary:
                    diagnosis_name = primary['name']
                elif isinstance(primary, str):
                    diagnosis_name = primary
                
                # Normalize the diagnosis name
                if diagnosis_name:
                    diagnosis_lower = diagnosis_name.lower()
                    # Check against our conditions map for normalization
                    for condition_key in conditions:
                        if condition_key in diagnosis_lower:
                            return conditions[condition_key]
                    return diagnosis_name  # Return as-is if no match
        except:
            pass  # Fall back to text parsing
        
        # Find the most specific match
        for condition, diagnosis in conditions.items():
            if condition in response_text:
                return diagnosis
        
        return None
    
    def cache_orchestrator_response(self, orchestrator_data):
        """Cache orchestrator analysis for this case"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        orchestrator_file = self.orchestrator_cache_dir / f"orchestrator_analysis_{timestamp}.json"
        
        orchestrator_data['case_id'] = self.case_id
        orchestrator_data['generated_at'] = datetime.now().isoformat()
        
        with open(orchestrator_file, 'w') as f:
            json.dump(orchestrator_data, f, indent=2)
        
        print(f"💾 Cached orchestrator analysis: {orchestrator_file.name}")
        return orchestrator_file
    
    def generate_comprehensive_report(self, ensemble_data, timestamp):
        """Generate comprehensive PDF report for this case"""
        
        from src.medley.reporters.final_comprehensive_report import FinalComprehensiveReportGenerator
        
        report_gen = FinalComprehensiveReportGenerator()
        output_file = self.reports_dir / f"FINAL_{self.case_id}_comprehensive_{timestamp}.pdf"
        
        print(f"📝 Generating comprehensive report for {self.case_id}...")
        print(f"   📄 Output: {output_file}")
        
        start_report = time.time()
        
        report_gen.generate_report(
            ensemble_results=ensemble_data,
            output_file=str(output_file)
        )
        
        report_time = time.time() - start_report
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Report generated: {file_size:,} bytes in {report_time:.2f}s")
            return str(output_file)
        else:
            print("❌ Report generation failed")
            return None
    
    def run_complete_analysis(self, case_description, case_title=None):
        """
        Run complete medical analysis pipeline for this case
        
        Args:
            case_description: Text description of the medical case
            case_title: Optional title for the case
        """
        
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("=" * 80)
        print(f"🚀 GENERAL MEDICAL PIPELINE - {self.case_id}")
        print(f"   {case_title or 'Medical Case Analysis'}")
        print("=" * 80)
        
        # Step 1: Environment Setup
        print(f"\\n📋 STEP 1: Environment Setup")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Case ID: {self.case_id}")
        
        # Show model distribution
        geo_dist = get_geographical_distribution()
        total_models = sum(len(models) for models in geo_dist.values())
        
        print(f"🌍 Available Models: {total_models} from {len(geo_dist)} countries")
        for country, models in sorted(geo_dist.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   🏳️  {country}: {len(models)} models")
        
        # Step 2: Initialize components
        print(f"\\n⚙️  STEP 2: Initializing Components")
        
        from src.medley.models.llm_manager import LLMManager
        from src.medley.utils.config import Config
        from src.medley.processors.prompt_generator import DiagnosticPromptGenerator
        
        config = Config()
        llm_manager = LLMManager(config)
        prompt_gen = DiagnosticPromptGenerator()
        
        print(f"✅ Case loaded: {len(case_description)} characters")
        prompt = prompt_gen.generate_diagnostic_prompt(case_description)
        print(f"✅ Prompt generated: {len(prompt)} characters")
        
        # Step 3: Load cached responses for this case only
        print(f"\\n💾 STEP 3: Loading {self.case_id} Cached Responses")
        cached_responses = self.load_case_cached_responses()
        
        # Step 4: Get all models and query missing ones
        print(f"\\n🔍 STEP 4: Model Analysis for {self.case_id}")
        all_models = self.get_all_available_models()
        print(f"📊 Total available models: {len(all_models)}")
        
        # Query missing models
        new_responses = self.query_missing_models(cached_responses, all_models, prompt, llm_manager)
        
        # Combine all responses - ONLY for this case
        all_responses = cached_responses + new_responses
        print(f"\\n✅ TOTAL RESPONSES for {self.case_id}: {len(all_responses)}")
        print(f"   💾 From cache: {len(cached_responses)}")
        print(f"   🆕 Fresh queries: {len(new_responses)}")
        
        # Step 5: Analyze consensus
        print(f"\\n🧠 STEP 5: Diagnostic Analysis for {self.case_id}")
        consensus_results = self.analyze_consensus(all_responses)
        
        # Step 6: Build comprehensive ensemble data
        print(f"\\n🏗️  STEP 6: Building {self.case_id} Report Data")
        
        primary = consensus_results['primary']
        total = consensus_results['total_models']
        
        ensemble_data = {
            "case_id": self.case_id,
            "case_title": case_title or f"{self.case_id} - Medical Analysis",
            "case_content": case_description,
            "model_responses": all_responses,
            "total_models_analyzed": len(all_responses),
            "geographical_distribution": {country: len(models) for country, models in geo_dist.items()},
            "consensus_analysis": consensus_results,  # Add the consensus analysis data
            "diagnostic_landscape": {
                "primary_diagnosis": {
                    "name": primary[0],
                    "icd_code": self._get_icd_code(primary[0]),
                    "agreement_percentage": (primary[1] / total * 100),
                    "supporting_models": list(set([m.split('/')[-1] for m in consensus_results.get('model_diagnoses', {}).get(primary[0], {}).get('primary', []) + consensus_results.get('model_diagnoses', {}).get(primary[0], {}).get('differential', [])])),
                    "evidence": self._extract_evidence(case_description),
                    "confidence": "High" if primary[1]/total > 0.6 else "Moderate"
                },
                "strong_alternatives": [],
                "alternatives": [],
                "minority_opinions": [],
                "geographical_consensus": consensus_results.get('geographical_patterns', {})
            },
            "comprehensive_bias_analysis": self._generate_bias_analysis(all_responses, geo_dist),
            "model_diversity_metrics": self._calculate_diversity_metrics(all_responses),
            "management_strategies": self._generate_management_strategies(primary[0]),
            "evidence_synthesis": self._generate_evidence_synthesis(all_responses, case_description),
            "generation_metadata": {
                "pipeline_version": "General v1.0",
                "timestamp": timestamp,
                "case_separation": "Strict",
                "total_time_seconds": time.time() - start_time
            }
        }
        
        # Use consistent categorization logic based on web interface rules
        from src.medley.utils.diagnosis_categorizer import categorize_diagnoses, log_categorization_debug
        
        diagnosis_counts = dict(consensus_results['sorted_diagnoses'])
        categorized_diagnoses = categorize_diagnoses(diagnosis_counts, total)
        log_categorization_debug(categorized_diagnoses, "General Medical Pipeline")
        
        # Update primary diagnosis with categorized data
        if categorized_diagnoses["primary_diagnosis"]:
            primary_diag = categorized_diagnoses["primary_diagnosis"]
            ensemble_data["diagnostic_landscape"]["primary_diagnosis"].update({
                "agreement_percentage": primary_diag["agreement_percentage"],
                "confidence": primary_diag["confidence"]
            })
        
        # Add categorized alternatives with enhanced data
        for diag_data in categorized_diagnoses["strong_alternatives"]:
            enhanced_diag = {
                "name": diag_data["name"],
                "icd_code": self._get_icd_code(diag_data["name"]),
                "agreement_percentage": diag_data["agreement_percentage"],
                "supporting_models": [f"{all_responses[j]['model_name'].split('/')[-1]}" for j in range(min(diag_data["model_count"], len(all_responses)))],
                "evidence": self._get_evidence_for_diagnosis(diag_data["name"])
            }
            ensemble_data["diagnostic_landscape"]["strong_alternatives"].append(enhanced_diag)
            
        for diag_data in categorized_diagnoses["alternatives"]:
            enhanced_diag = {
                "name": diag_data["name"],
                "icd_code": self._get_icd_code(diag_data["name"]),
                "agreement_percentage": diag_data["agreement_percentage"],
                "supporting_models": [f"{all_responses[j]['model_name'].split('/')[-1]}" for j in range(min(diag_data["model_count"], len(all_responses)))],
                "evidence": self._get_evidence_for_diagnosis(diag_data["name"])
            }
            ensemble_data["diagnostic_landscape"]["alternatives"].append(enhanced_diag)
            
        # Limit minority opinions to top 5 for efficiency
        for diag_data in categorized_diagnoses["minority_opinions"][:5]:
            enhanced_diag = {
                "name": diag_data["name"],
                "icd_code": self._get_icd_code(diag_data["name"]),
                "agreement_percentage": diag_data["agreement_percentage"],
                "supporting_models": [f"{all_responses[j]['model_name'].split('/')[-1]}" for j in range(min(diag_data["model_count"], len(all_responses)))],
                "evidence": self._get_evidence_for_diagnosis(diag_data["name"])
            }
            ensemble_data["diagnostic_landscape"]["minority_opinions"].append(enhanced_diag)
        
        # Step 7: Orchestrator Analysis with Retry
        print(f"\\n🧠 STEP 7: Orchestrator Analysis for {self.case_id}")
        
        # TEMPORARY: Skip orchestrator if it would hang
        skip_orchestrator = False  # Re-enabled after fixes
        
        # Force fallback for testing (set via environment variable)
        import os
        force_fallback = os.environ.get('FORCE_FALLBACK', '').lower() == 'true'
        
        if force_fallback:
            print(f"\\n🧠 STEP 7: Orchestrator Analysis for {self.case_id}")
            print(f"⚠️  FORCE_FALLBACK=true - Using fallback extraction directly")
            skip_orchestrator = True
            # Create fallback extraction directly
            from src.medley.reporters.report_orchestrator import ReportOrchestrator
            orchestrator = ReportOrchestrator(self.cache_dir)
            orchestrated_analysis = orchestrator._fallback_extraction(ensemble_data)
            ensemble_data.update(orchestrated_analysis)
            orchestrator_success = False
        elif skip_orchestrator:
            print("⚠️ Skipping orchestrator (known hanging issue), using fallback extraction")
            orchestrator_success = False
            orchestrated_analysis = None
        else:
            from src.medley.reporters.report_orchestrator import ReportOrchestrator
            orchestrator = ReportOrchestrator(llm_manager)
            
            orchestrator_success = False
            orchestrated_analysis = None
            
            try:
                print(f"🚀 Starting orchestrator analysis...")
                orchestrated_analysis = orchestrator.orchestrate_analysis(ensemble_data)
                
                # Check if orchestrator succeeded (not fallback)
                if orchestrated_analysis.get("metadata", {}).get("orchestrator_model") != "fallback":
                    orchestrator_success = True
                    print(f"✅ Orchestrator analysis successful!")
                    
                    # Update ensemble_data with orchestrated results
                    ensemble_data.update(orchestrated_analysis)
                else:
                    print(f"⚠️  Orchestrator failed, using basic analysis only")
                    orchestrator_success = False
                    # Still update ensemble_data with fallback results
                    if orchestrated_analysis:
                        ensemble_data.update(orchestrated_analysis)
                    
            except Exception as e:
                print(f"💥 Orchestrator completely failed: {e}")
                orchestrator_success = False
                # Still update with fallback if we have orchestrated_analysis
                if orchestrated_analysis:
                    ensemble_data.update(orchestrated_analysis)
        
        # Step 8: Cache orchestrator response
        print(f"\\n💾 STEP 8: Caching {self.case_id} Analysis")
        orchestrator_file = self.cache_orchestrator_response(ensemble_data)
        
        # Save comprehensive ensemble data
        ensemble_file = self.reports_dir / f"{self.case_id}_ensemble_data_{timestamp}.json"
        with open(ensemble_file, 'w') as f:
            json.dump(ensemble_data, f, indent=2)
        print(f"💾 Saved ensemble data: {ensemble_file.name}")
        
        # Step 9: Always generate comprehensive report (even with fallback extraction)
        print(f"\\n📄 STEP 9: Generating {self.case_id} PDF Report")
        if not orchestrator_success:
            print(f"   ⚠️  Using fallback extraction data (orchestrator failed)")
        report_file = self.generate_comprehensive_report(ensemble_data, timestamp)
        
        total_time = time.time() - start_time
        
        # Final Summary
        print(f"\\n" + "=" * 80)
        print(f"🎉 {self.case_id} ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"⏰ Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"🌍 Models Analyzed: {len(all_responses)} from {len(geo_dist)} countries")
        print(f"🥇 Primary Diagnosis: {primary[0]} ({primary[1]}/{total} = {primary[1]/total*100:.1f}% consensus)")
        if report_file:
            print(f"📄 Report: {report_file}")
        print(f"💾 Data: {ensemble_file}")
        print(f"🧠 Orchestrator: {orchestrator_file}")
        print(f"📊 Success Rate: {len([r for r in all_responses if r.get('response')])/len(all_responses)*100:.1f}%")
        
        print(f"\\n🎯 KEY INSIGHTS for {self.case_id}:")
        print(f"   • {len(all_responses)} AI models analyzed with strict case separation")
        print(f"   • Primary diagnosis achieved {primary[1]/total*100:.1f}% consensus")
        print(f"   • {len(geo_dist)} countries represented in analysis")
        print(f"   • Comprehensive bias analysis completed")
        
        return {
            'report_file': report_file,
            'data_file': str(ensemble_file),
            'orchestrator_file': str(orchestrator_file),
            'consensus_results': consensus_results,
            'total_models': len(all_responses)
        }
    
    def _get_icd_code(self, diagnosis):
        """Get ICD-10 code for diagnosis using comprehensive database"""
        from src.medley.utils.icd10_database import get_icd10_database
        
        icd_db = get_icd10_database()
        return icd_db.get_icd10_code(diagnosis)
    
    def _get_icd_code_old(self, diagnosis):
        """Legacy ICD code method - kept for reference"""
        codes = {
            # Correct ICD-10 codes based on medical standards
            "Familial Mediterranean Fever": "E85.0",
            "Systemic Lupus Erythematosus": "M32.9",
            "Crohn's Disease": "K50.90",
            "Inflammatory Bowel Disease": "K50.9",
            "Ulcerative Colitis": "K51.90",
            "Reactive Arthritis": "M02.9",
            "Septic Arthritis": "M00.9",
            "Infectious Arthritis": "M00.9",
            "Gouty Arthritis": "M10.9",
            "Behçet's Disease": "M35.2",
            "Adult-Onset Still's Disease": "M06.1",
            "Acute Appendicitis": "K35.80",
            "Peritonitis": "K65.9",
            "Tuberculosis": "A15.9",
            "Acute Intermittent Porphyria": "E80.21",
            "TRAPS": "M04.8",
            "PFAPA Syndrome": "M04.8",
            "Ankylosing Spondylitis": "M45.9",
            "Psoriatic Arthritis": "L40.50",
            "Rheumatic Fever": "I00",
            "Irritable Bowel Syndrome": "K58.9",
            "Hereditary Angioedema": "D84.1",
            "Autoinflammatory Disease": "M04.9",
            # Additional codes from other cases
            "Alzheimer's Disease": "G30.9",
            "Dementia": "F03.90",
            "Lewy Body Dementia": "G31.83",
            "Vascular Dementia": "F01.50",
            "Hypertensive Emergency": "I16.0",
            "Hypertensive Encephalopathy": "I67.4",
            "Traumatic Brain Injury": "S06.9"
        }
        return codes.get(diagnosis, "")
    
    def _extract_evidence(self, case_description):
        """Extract evidence from case description"""
        evidence = []
        case_lower = case_description.lower()
        
        # Common evidence patterns
        if 'fever' in case_lower:
            evidence.append('Fever')
        if 'pain' in case_lower:
            evidence.append('Pain')
        if 'rash' in case_lower:
            evidence.append('Rash')
        if 'arthritis' in case_lower or 'joint' in case_lower:
            evidence.append('Joint symptoms')
        if 'memory' in case_lower or 'confusion' in case_lower:
            evidence.append('Cognitive symptoms')
        if 'paranoid' in case_lower:
            evidence.append('Paranoid ideation')
        if 'bug' in case_lower or 'formication' in case_lower:
            evidence.append('Formication')
        if 'bp' in case_lower or 'blood pressure' in case_lower or '190' in case_lower:
            evidence.append('Hypertension')
        if 'headache' in case_lower:
            evidence.append('Headaches')
        if 'trauma' in case_lower:
            evidence.append('Head trauma')
        
        return evidence
    
    def _get_evidence_for_diagnosis(self, diagnosis):
        """Get evidence supporting diagnosis"""
        evidence_map = {
            # Existing diagnoses
            "Familial Mediterranean Fever": ["Fever", "Abdominal pain", "Family history"],
            "Alzheimer's Disease": ["Memory loss", "Cognitive decline", "ADL impairment"],
            "Hypertensive Emergency": ["Severe hypertension", "End-organ damage", "Headaches"],
            "Substance-Induced Psychosis": ["Paranoid ideation", "Substance use history", "Psychotic symptoms"],
            "Traumatic Brain Injury": ["Head trauma", "Neurological symptoms", "Behavioral changes"],
            
            # Case 1 diagnoses
            "Systemic Lupus Erythematosus": ["Joint pain", "Fatigue", "Skin rash", "Multi-system involvement"],
            "SLE": ["Joint pain", "Fatigue", "Skin rash", "Multi-system involvement"],
            "Inflammatory Bowel Disease": ["Abdominal pain", "GI symptoms", "Chronic inflammation"],
            "IBD": ["Abdominal pain", "GI symptoms", "Chronic inflammation"],
            "Crohn's Disease": ["Abdominal pain", "Diarrhea", "Weight loss", "Perianal symptoms"],
            "Ulcerative Colitis": ["Bloody diarrhea", "Abdominal cramping", "Urgency"],
            "Reactive Arthritis": ["Joint pain", "Asymmetric arthritis", "Preceding infection"],
            "Ankylosing Spondylitis": ["Back pain", "Morning stiffness", "Sacroiliitis"],
            "Rheumatoid Arthritis": ["Joint swelling", "Morning stiffness", "Symmetric arthritis"],
            "Fibromyalgia": ["Widespread pain", "Tender points", "Fatigue", "Sleep disturbance"],
            "Psoriatic Arthritis": ["Joint pain", "Skin psoriasis", "Nail changes"],
            "Behçet's Disease": ["Oral ulcers", "Genital ulcers", "Ocular symptoms"],
            "Spondyloarthritis": ["Axial symptoms", "Peripheral arthritis", "Enthesitis"],
            "Seronegative Arthritis": ["Joint inflammation", "Negative RF", "HLA-B27 association"],
            "Undifferentiated Connective Tissue Disease": ["Mixed symptoms", "Autoantibodies", "Multi-organ"],
            "Mixed Connective Tissue Disease": ["Raynaud's phenomenon", "Swollen hands", "Anti-U1-RNP"],
            "Sjögren's Syndrome": ["Dry eyes", "Dry mouth", "Autoimmune features"],
            "Vasculitis": ["Systemic inflammation", "Multi-organ involvement", "Vascular symptoms"],
            "Adult-Onset Still's Disease": ["High fever", "Salmon-colored rash", "Arthritis"],
            "Polymyalgia Rheumatica": ["Shoulder/hip stiffness", "Elevated ESR", "Age >50"],
            "Giant Cell Arteritis": ["Temporal headache", "Jaw claudication", "Visual symptoms"]
        }
        return evidence_map.get(diagnosis, [])
    
    def _generate_bias_analysis(self, all_responses, geo_dist):
        """Generate comprehensive bias analysis"""
        return {
            "geographical_representation": {
                "total_countries": len(geo_dist),
                "western_dominance": {
                    "western_models": len(geo_dist.get('USA', [])) + len(geo_dist.get('Canada', [])) + len(geo_dist.get('France', [])),
                    "percentage": (len(geo_dist.get('USA', [])) + len(geo_dist.get('Canada', [])) + len(geo_dist.get('France', []))) / len(all_responses) * 100,
                    "impact": "High Western medical paradigm influence expected"
                },
                "chinese_representation": {
                    "chinese_models": len(geo_dist.get('China', [])),
                    "percentage": len(geo_dist.get('China', [])) / len(all_responses) * 100,
                    "impact": "Traditional Chinese Medicine integration possible"
                }
            },
            "case_specific_concerns": [
                f"Analysis strictly limited to {self.case_id} responses",
                "No cross-case contamination in this analysis",
                "Bias patterns specific to this case presentation"
            ],
            "recommended_mitigations": [
                "Consider cultural context in diagnosis interpretation",
                "Account for geographical bias in model training",
                "Validate findings across diverse medical paradigms"
            ]
        }
    
    def _calculate_diversity_metrics(self, all_responses):
        """Calculate model diversity metrics"""
        metadata = get_comprehensive_model_metadata()
        
        architectures = set()
        providers = set()
        countries = set()
        
        for response in all_responses:
            model_name = response['model_name']
            if model_name in metadata:
                info = metadata[model_name]
                architectures.add(info.get('architecture', 'Unknown'))
                providers.add(info.get('provider', 'Unknown'))
                countries.add(info.get('origin_country', 'Unknown'))
        
        return {
            "unique_architectures": len(architectures),
            "unique_providers": len(providers),
            "unique_countries": len(countries),
            "diversity_score": (len(architectures) + len(providers) + len(countries)) / 3,
            "case_id": self.case_id
        }
    
    def _generate_management_strategies(self, primary_diagnosis):
        """Generate comprehensive management strategies based on primary diagnosis"""
        
        # Get specific strategies based on diagnosis
        if "Familial Mediterranean Fever" in primary_diagnosis or "FMF" in primary_diagnosis:
            return {
                "immediate_actions": [
                    {
                        "action": "Start colchicine therapy 0.6mg twice daily",
                        "rationale": "First-line treatment for FMF attack prevention",
                        "consensus": "High",
                        "priority": "Critical"
                    },
                    {
                        "action": "Provide pain management during acute episodes",
                        "rationale": "Symptomatic relief during attacks",
                        "consensus": "High",
                        "priority": "High"
                    },
                    {
                        "action": "Arrange interpreter services if needed",
                        "rationale": "Ensure clear communication for treatment adherence",
                        "consensus": "Moderate",
                        "priority": "High"
                    }
                ],
                "diagnostic_tests": [
                    {
                        "test": "MEFV gene mutation analysis",
                        "purpose": "Confirm FMF diagnosis genetically",
                        "priority": "High"
                    },
                    {
                        "test": "24-hour urine protein",
                        "purpose": "Screen for renal amyloidosis",
                        "priority": "High"
                    },
                    {
                        "test": "Complete blood count, CRP, ESR",
                        "purpose": "Monitor inflammation during episodes",
                        "priority": "Routine"
                    }
                ],
                "long_term_management": [
                    "Lifelong colchicine therapy to prevent amyloidosis",
                    "Regular monitoring of renal function",
                    "Patient education on trigger identification",
                    "Family screening for MEFV mutations"
                ]
            }
        else:
            # Default management for other diagnoses
            return {
                "immediate_actions": [
                    {
                        "action": f"Initiate treatment for {primary_diagnosis}",
                        "rationale": "Evidence-based management of primary condition",
                        "consensus": "High",
                        "priority": "Critical"
                    },
                    {
                        "action": "Symptomatic management",
                        "rationale": "Patient comfort and stabilization",
                        "consensus": "High",
                        "priority": "High"
                    }
                ],
                "diagnostic_tests": [
                    {
                        "test": "Comprehensive diagnostic workup",
                        "purpose": f"Confirm {primary_diagnosis} diagnosis",
                        "priority": "High"
                    },
                    {
                        "test": "Laboratory studies",
                        "purpose": "Assess disease activity and complications",
                        "priority": "Routine"
                    }
                ],
                "long_term_management": [
                    "Regular follow-up appointments",
                    "Monitor treatment response",
                    "Adjust therapy as needed"
                ]
            }
    
    def _generate_evidence_synthesis(self, all_responses, case_description):
        """Generate evidence synthesis"""
        return {
            "key_clinical_findings": [
                {
                    "finding": "Primary clinical presentation",
                    "diagnostic_significance": f"Supports consensus diagnosis",
                    "mentioned_by_models": len(all_responses)
                }
            ],
            "case_id": self.case_id,
            "analysis_scope": f"Limited to {self.case_id} responses only"
        }

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='General Medical AI Pipeline')
    parser.add_argument('case_id', help='Case identifier (e.g., Case_1, Case_2, Case_3)')
    parser.add_argument('case_file', help='Path to case description file')
    parser.add_argument('--title', help='Optional case title')
    
    args = parser.parse_args()
    
    # Read case description
    case_file = Path(args.case_file)
    if not case_file.exists():
        print(f"❌ Case file not found: {case_file}")
        return
    
    with open(case_file, 'r') as f:
        case_description = f.read()
    
    # Initialize pipeline
    pipeline = GeneralMedicalPipeline(args.case_id)
    
    # Run analysis
    results = pipeline.run_complete_analysis(
        case_description=case_description,
        case_title=args.title
    )
    
    print(f"\\n🚀 Opening report for {args.case_id}...")
    if results.get('report_file'):
        import os
        os.system(f"open '{results['report_file']}'")

if __name__ == "__main__":
    main()
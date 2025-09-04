#!/usr/bin/env python
"""
Advanced usage examples for MEDLEY Medical AI Ensemble System
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

class MedleyAnalyzer:
    """Advanced analyzer for MEDLEY system"""
    
    def __init__(self, cache_dir="cache", reports_dir="reports"):
        self.cache_dir = Path(cache_dir)
        self.reports_dir = Path(reports_dir)
    
    def analyze_bias_patterns(self, case_id: str) -> Dict:
        """Analyze bias patterns across different model origins"""
        
        cache_path = self.cache_dir / "responses" / case_id
        
        if not cache_path.exists():
            return {"error": "No cache found for case"}
        
        # Group responses by country
        responses_by_country = {}
        
        for cache_file in cache_path.glob("*.json"):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                
                # Get model metadata
                model_id = data.get('model_id', '')
                content = data.get('content', '')
                
                if not content:
                    continue
                
                # Determine country (simplified)
                country = self._get_model_country(model_id)
                
                if country not in responses_by_country:
                    responses_by_country[country] = []
                
                responses_by_country[country].append({
                    'model': model_id,
                    'diagnosis': self._extract_diagnosis(content)
                })
            except:
                continue
        
        # Analyze patterns
        patterns = {}
        for country, responses in responses_by_country.items():
            diagnoses = [r['diagnosis'] for r in responses]
            unique_diagnoses = set(diagnoses)
            
            patterns[country] = {
                'total_models': len(responses),
                'unique_diagnoses': len(unique_diagnoses),
                'consensus': self._calculate_consensus(diagnoses),
                'diagnoses': diagnoses
            }
        
        return patterns
    
    def compare_cases(self, case_ids: List[str]) -> Dict:
        """Compare diagnostic consensus across multiple cases"""
        
        comparisons = {}
        
        for case_id in case_ids:
            # Find ensemble data
            ensemble_files = sorted(self.reports_dir.glob(f"{case_id}_ensemble_data_*.json"))
            
            if not ensemble_files:
                comparisons[case_id] = {"error": "No data found"}
                continue
            
            with open(ensemble_files[-1]) as f:
                data = json.load(f)
            
            diagnostic = data.get('diagnostic_landscape', {})
            primary = diagnostic.get('primary_diagnosis', {})
            
            comparisons[case_id] = {
                'diagnosis': primary.get('name', 'Unknown'),
                'consensus': primary.get('agreement_percentage', 0),
                'confidence': primary.get('confidence', 'Unknown'),
                'total_models': data.get('total_models', 0),
                'successful_models': data.get('successful_models', 0)
            }
        
        return comparisons
    
    def generate_bias_report(self, case_id: str) -> str:
        """Generate a detailed bias analysis report"""
        
        patterns = self.analyze_bias_patterns(case_id)
        
        report = f"BIAS ANALYSIS REPORT - {case_id}\n"
        report += "=" * 50 + "\n\n"
        
        for country, data in patterns.items():
            report += f"📍 {country}\n"
            report += f"   Models: {data['total_models']}\n"
            report += f"   Unique diagnoses: {data['unique_diagnoses']}\n"
            report += f"   Consensus level: {data['consensus']:.1f}%\n"
            report += "\n"
        
        # Identify potential biases
        report += "POTENTIAL BIASES IDENTIFIED:\n"
        report += "-" * 30 + "\n"
        
        # Check for geographic clustering
        high_consensus_countries = [
            c for c, d in patterns.items() 
            if d['consensus'] > 80
        ]
        
        if high_consensus_countries:
            report += f"• Geographic clustering in: {', '.join(high_consensus_countries)}\n"
        
        # Check for outliers
        low_consensus_countries = [
            c for c, d in patterns.items() 
            if d['consensus'] < 50
        ]
        
        if low_consensus_countries:
            report += f"• Divergent opinions from: {', '.join(low_consensus_countries)}\n"
        
        return report
    
    def _get_model_country(self, model_id: str) -> str:
        """Determine model country from ID"""
        
        country_mapping = {
            'openai': 'USA',
            'anthropic': 'USA',
            'google': 'USA',
            'meta': 'USA',
            'mistral': 'France',
            'deepseek': 'China',
            'qwen': 'China',
            'cohere': 'Canada',
            'ai21': 'Israel',
            'x-ai': 'USA',
            'microsoft': 'USA',
            'perplexity': 'USA',
            'liquid': 'USA',
            'nous': 'USA',
            'shisa': 'Japan'
        }
        
        for key, country in country_mapping.items():
            if key in model_id.lower():
                return country
        
        return 'Unknown'
    
    def _extract_diagnosis(self, content: str) -> str:
        """Extract primary diagnosis from model response"""
        
        # Simple extraction (would be more sophisticated in production)
        if "FMF" in content or "Familial Mediterranean Fever" in content:
            return "FMF"
        elif "Alzheimer" in content:
            return "Alzheimer's"
        elif "psychosis" in content.lower():
            return "Psychosis"
        else:
            # Extract first mentioned diagnosis
            return "Other"
    
    def _calculate_consensus(self, diagnoses: List[str]) -> float:
        """Calculate consensus percentage"""
        
        if not diagnoses:
            return 0.0
        
        from collections import Counter
        counts = Counter(diagnoses)
        most_common = counts.most_common(1)[0][1]
        
        return (most_common / len(diagnoses)) * 100

async def parallel_analysis_example():
    """Example of running parallel analyses"""
    
    import aiohttp
    from src.medley.models.llm_manager import LLMManager
    from src.medley.utils.config import Config
    
    # Initialize
    config = Config()
    manager = LLMManager(config)
    
    # Define test prompt
    prompt = """Analyze this case: A 27-year-old male of Mediterranean descent 
    presents with recurrent fever episodes lasting 1-3 days, severe abdominal pain, 
    and joint pain. Provide a differential diagnosis."""
    
    # Select models to query
    models = [
        {"model_id": "openai/gpt-4o", "name": "GPT-4o"},
        {"model_id": "anthropic/claude-3-opus", "name": "Claude Opus"},
        {"model_id": "google/gemini-2.5-pro", "name": "Gemini Pro"}
    ]
    
    print("Running parallel queries...")
    
    # Create tasks
    async with aiohttp.ClientSession() as session:
        tasks = []
        for model in models:
            task = manager.query_model_async(
                session, 
                model, 
                prompt
            )
            tasks.append(task)
        
        # Execute in parallel
        responses = await asyncio.gather(*tasks)
    
    # Display results
    for response in responses:
        print(f"\n{response.model_name}:")
        print(f"  Latency: {response.latency:.2f}s")
        print(f"  Response length: {len(response.content)} chars")
        if response.error:
            print(f"  Error: {response.error}")

def performance_analysis():
    """Analyze system performance metrics"""
    
    import time
    from datetime import datetime
    
    # Analyze cache performance
    cache_dir = Path("cache/responses")
    
    total_files = 0
    total_size = 0
    oldest_file = None
    newest_file = None
    
    for case_dir in cache_dir.iterdir():
        if not case_dir.is_dir():
            continue
        
        for cache_file in case_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size
            
            mtime = cache_file.stat().st_mtime
            if oldest_file is None or mtime < oldest_file[1]:
                oldest_file = (cache_file, mtime)
            if newest_file is None or mtime > newest_file[1]:
                newest_file = (cache_file, mtime)
    
    print("📊 CACHE PERFORMANCE METRICS")
    print("=" * 40)
    print(f"Total cached responses: {total_files}")
    print(f"Total cache size: {total_size / 1024 / 1024:.2f} MB")
    print(f"Average file size: {total_size / total_files / 1024:.2f} KB")
    
    if oldest_file:
        age_days = (time.time() - oldest_file[1]) / 86400
        print(f"Oldest cache: {age_days:.1f} days")
    
    if newest_file:
        age_mins = (time.time() - newest_file[1]) / 60
        print(f"Newest cache: {age_mins:.1f} minutes ago")
    
    # Analyze report generation
    reports_dir = Path("reports")
    pdf_files = list(reports_dir.glob("FINAL_*.pdf"))
    
    print(f"\n📄 REPORT METRICS")
    print("=" * 40)
    print(f"Total reports generated: {len(pdf_files)}")
    
    if pdf_files:
        sizes = [f.stat().st_size for f in pdf_files]
        print(f"Average report size: {sum(sizes) / len(sizes) / 1024:.1f} KB")
        print(f"Largest report: {max(sizes) / 1024:.1f} KB")
        print(f"Smallest report: {min(sizes) / 1024:.1f} KB")

if __name__ == "__main__":
    print("MEDLEY Advanced Usage Examples")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = MedleyAnalyzer()
    
    # Example 1: Bias pattern analysis
    print("\n1. BIAS PATTERN ANALYSIS")
    print("-" * 30)
    patterns = analyzer.analyze_bias_patterns("Case_1")
    for country, data in patterns.items():
        print(f"{country}: {data['total_models']} models, {data['consensus']:.1f}% consensus")
    
    # Example 2: Case comparison
    print("\n2. CASE COMPARISON")
    print("-" * 30)
    cases = ["Case_1", "Case_2", "Case_3"]
    comparisons = analyzer.compare_cases(cases)
    
    for case_id, data in comparisons.items():
        if 'error' not in data:
            print(f"{case_id}: {data['diagnosis']} ({data['consensus']:.1f}% consensus)")
    
    # Example 3: Bias report
    print("\n3. DETAILED BIAS REPORT")
    print("-" * 30)
    report = analyzer.generate_bias_report("Case_1")
    print(report)
    
    # Example 4: Performance metrics
    print("\n4. PERFORMANCE ANALYSIS")
    print("-" * 30)
    performance_analysis()
    
    print("\n✅ Advanced examples complete!")
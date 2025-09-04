#!/usr/bin/env python3
"""
Comprehensive analysis of model consensus participation across all cases
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def extract_diagnosis_from_response(response_text):
    """Extract primary and differential diagnoses from model response"""
    diagnoses = {'primary': None, 'differentials': []}
    
    try:
        # Parse JSON response
        if isinstance(response_text, str) and ('{' in response_text):
            # Find the JSON part
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                
                # Get primary diagnosis
                if 'primary_diagnosis' in data:
                    diagnoses['primary'] = data['primary_diagnosis'].get('name', '')
                
                # Get differential diagnoses
                if 'differential_diagnoses' in data:
                    for diff in data['differential_diagnoses']:
                        diagnoses['differentials'].append(diff.get('name', ''))
    except:
        pass
    
    return diagnoses

def analyze_case_consensus(case_file):
    """Analyze consensus for a single case"""
    with open(case_file, 'r') as f:
        data = json.load(f)
    
    case_id = data.get('case_id', 'Unknown')
    model_diagnoses = {}
    diagnosis_counts = defaultdict(int)
    
    # Extract diagnoses from each model
    for response in data.get('model_responses', []):
        model_name = response.get('model_name', '')
        response_text = response.get('response', '')
        
        if model_name:
            diagnoses = extract_diagnosis_from_response(response_text)
            model_diagnoses[model_name] = diagnoses
            
            # Count primary diagnoses
            if diagnoses['primary']:
                diagnosis_counts[diagnoses['primary'].lower()] += 1
    
    # Find consensus (most common diagnosis)
    if diagnosis_counts:
        consensus_diagnosis = max(diagnosis_counts.items(), key=lambda x: x[1])
        consensus_name = consensus_diagnosis[0]
        consensus_count = consensus_diagnosis[1]
        total_models = len(model_diagnoses)
        consensus_rate = (consensus_count / total_models * 100) if total_models > 0 else 0
    else:
        consensus_name = "No consensus"
        consensus_count = 0
        consensus_rate = 0
        total_models = 0
    
    return {
        'case_id': case_id,
        'model_diagnoses': model_diagnoses,
        'consensus': consensus_name,
        'consensus_count': consensus_count,
        'consensus_rate': consensus_rate,
        'total_models': total_models,
        'all_diagnoses': diagnosis_counts
    }

def main():
    """Main analysis function"""
    
    # Find all ensemble data files
    reports_path = Path("/Users/sabt/Library/CloudStorage/OneDrive-KarolinskaInstitutet/Github/DiverseAI/medley/reports")
    
    # Get Case 1-13 ensemble data files
    case_files = []
    for i in range(1, 14):
        pattern = f"Case_{i}_ensemble_data_*.json"
        matching_files = list(reports_path.glob(pattern))
        if matching_files:
            # Use the most recent file
            latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
            case_files.append(latest_file)
    
    # Analyze each case
    all_results = []
    model_stats = defaultdict(lambda: {
        'cases_analyzed': 0,
        'consensus_participation': 0,
        'unique_diagnoses': set(),
        'primary_diagnoses': []
    })
    
    for case_file in case_files:
        print(f"Analyzing {case_file.name}...")
        result = analyze_case_consensus(case_file)
        all_results.append(result)
        
        # Update model statistics
        for model, diagnoses in result['model_diagnoses'].items():
            model_stats[model]['cases_analyzed'] += 1
            
            # Check if model participated in consensus
            if diagnoses['primary'] and diagnoses['primary'].lower() == result['consensus']:
                model_stats[model]['consensus_participation'] += 1
            
            # Track unique diagnoses
            if diagnoses['primary']:
                model_stats[model]['unique_diagnoses'].add(diagnoses['primary'])
                model_stats[model]['primary_diagnoses'].append(diagnoses['primary'])
            for diff in diagnoses['differentials']:
                model_stats[model]['unique_diagnoses'].add(diff)
    
    # Generate report
    print("\n# Model Consensus Participation and Diagnostic Diversity\n")
    print("## Table: Model Performance Across All Cases\n")
    print("| Model | Cases | Consensus Participation | Unique Diagnoses | Consensus Rate |")
    print("|-------|-------|------------------------|------------------|----------------|")
    
    # Sort by consensus participation rate
    sorted_models = sorted(
        model_stats.items(),
        key=lambda x: (x[1]['consensus_participation'] / x[1]['cases_analyzed'] * 100) if x[1]['cases_analyzed'] > 0 else 0,
        reverse=True
    )
    
    for model, stats in sorted_models:
        if stats['cases_analyzed'] > 0:
            consensus_rate = (stats['consensus_participation'] / stats['cases_analyzed']) * 100
            # Shorten model name for display
            display_name = model.split('/')[-1] if '/' in model else model
            display_name = display_name[:30]  # Limit length
            
            print(f"| {display_name} | {stats['cases_analyzed']} | {stats['consensus_participation']} | {len(stats['unique_diagnoses'])} | {consensus_rate:.1f}% |")
    
    # Add case summary to manuscript table
    print("\n## Additional Column: Case-by-Case Consensus\n")
    print("| Case | Primary Consensus | Rate | Models in Consensus | Total Unique Diagnoses |")
    print("|------|------------------|------|-------------------|------------------------|")
    
    for result in all_results:
        consensus_display = result['consensus'][:30] if result['consensus'] else "No consensus"
        print(f"| {result['case_id']} | {consensus_display} | {result['consensus_rate']:.1f}% | {result['consensus_count']}/{result['total_models']} | {len(result['all_diagnoses'])} |")
    
    # Summary statistics
    print("\n## Summary Statistics\n")
    
    if all_results:
        avg_consensus_rate = sum(r['consensus_rate'] for r in all_results) / len(all_results)
        avg_unique_diagnoses = sum(len(r['all_diagnoses']) for r in all_results) / len(all_results)
        
        print(f"- **Total Cases Analyzed:** {len(all_results)}")
        print(f"- **Average Consensus Rate:** {avg_consensus_rate:.1f}%")
        print(f"- **Average Unique Diagnoses per Case:** {avg_unique_diagnoses:.1f}")
        
        # Find models with highest/lowest consensus rates
        if sorted_models:
            print(f"\n### Top 3 Consensus-Oriented Models:")
            for i, (model, stats) in enumerate(sorted_models[:3], 1):
                rate = (stats['consensus_participation'] / stats['cases_analyzed'] * 100) if stats['cases_analyzed'] > 0 else 0
                display_name = model.split('/')[-1] if '/' in model else model
                print(f"{i}. {display_name}: {rate:.1f}% consensus rate")
            
            print(f"\n### Top 3 Diverse/Contrarian Models:")
            for i, (model, stats) in enumerate(sorted_models[-3:], 1):
                rate = (stats['consensus_participation'] / stats['cases_analyzed'] * 100) if stats['cases_analyzed'] > 0 else 0
                display_name = model.split('/')[-1] if '/' in model else model
                print(f"{i}. {display_name}: {rate:.1f}% consensus rate")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Analyze model consensus participation and unique diagnoses from orchestrator data
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_all_cases():
    """Analyze consensus participation across all cases"""
    
    base_path = Path("/Users/sabt/Library/CloudStorage/OneDrive-KarolinskaInstitutet/Github/DiverseAI/medley/cache/orchestrator")
    
    # Dictionary to store model statistics
    model_stats = defaultdict(lambda: {
        'primary_support': 0,
        'differential_support': 0,
        'total_participation': 0,
        'cases_analyzed': 0,
        'unique_diagnoses': set()
    })
    
    case_stats = []
    
    # Process each case
    for case_dir in base_path.glob("Case_*"):
        case_name = case_dir.name
        
        # Skip test cases
        if 'TEST' in case_name.upper():
            continue
            
        # Get the latest orchestrator analysis file
        analysis_files = list(case_dir.glob("orchestrator_analysis_*.json"))
        if not analysis_files:
            continue
            
        # Use the most recent file
        latest_file = max(analysis_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Process consensus results
            if 'consensus_results' in data:
                # Track unique diagnoses per case
                case_diagnoses = set()
                case_consensus = None
                case_consensus_rate = 0
                
                for consensus_item in data['consensus_results']:
                    diagnosis = consensus_item.get('diagnosis', '')
                    case_diagnoses.add(diagnosis)
                    
                    # Get the primary consensus (first item)
                    if case_consensus is None:
                        case_consensus = diagnosis
                        case_consensus_rate = consensus_item.get('percentage', 0)
                    
                    # Track model participation
                    supporting_models = consensus_item.get('supporting_models', [])
                    primary_support = consensus_item.get('primary_support', 0)
                    
                    for model in supporting_models:
                        model_stats[model]['total_participation'] += 1
                        model_stats[model]['unique_diagnoses'].add(diagnosis)
                        
                        # Check if this was primary support for consensus diagnosis
                        if diagnosis == case_consensus and primary_support > 0:
                            model_stats[model]['primary_support'] += 1
                
                # Track case statistics
                case_stats.append({
                    'case': case_name,
                    'consensus': case_consensus,
                    'consensus_rate': case_consensus_rate,
                    'unique_diagnoses': len(case_diagnoses)
                })
                
                # Mark that these models analyzed this case
                if 'model_responses' in data:
                    for response in data['model_responses']:
                        model_name = response.get('model_name', '')
                        if model_name:
                            model_stats[model_name]['cases_analyzed'] += 1
                            
        except Exception as e:
            print(f"Error processing {latest_file}: {e}")
            continue
    
    # Generate the report
    print("\n# Model Consensus Participation Analysis\n")
    print("## Individual Model Performance\n")
    print("| Model | Cases | Primary Consensus | Total Mentions | Unique Diagnoses | Consensus Rate |")
    print("|-------|-------|------------------|----------------|------------------|----------------|")
    
    # Sort by primary consensus participation
    sorted_models = sorted(
        model_stats.items(),
        key=lambda x: x[1]['primary_support'],
        reverse=True
    )
    
    for model, stats in sorted_models:
        if stats['cases_analyzed'] > 0:
            consensus_rate = (stats['primary_support'] / stats['cases_analyzed']) * 100 if stats['cases_analyzed'] > 0 else 0
            # Clean model name for display
            display_name = model.split('/')[-1][:25]  # Take last part and limit length
            
            print(f"| {display_name} | {stats['cases_analyzed']} | {stats['primary_support']} | {stats['total_participation']} | {len(stats['unique_diagnoses'])} | {consensus_rate:.1f}% |")
    
    print("\n## Case-by-Case Consensus Statistics\n")
    print("| Case | Primary Diagnosis | Consensus Rate | Total Unique Diagnoses |")
    print("|------|------------------|----------------|------------------------|")
    
    for case in case_stats:
        print(f"| {case['case']} | {case['consensus'][:30]} | {case['consensus_rate']:.1f}% | {case['unique_diagnoses']} |")
    
    # Summary statistics
    print("\n## Summary Statistics\n")
    
    if case_stats:
        avg_consensus = sum(c['consensus_rate'] for c in case_stats) / len(case_stats)
        avg_unique = sum(c['unique_diagnoses'] for c in case_stats) / len(case_stats)
        
        print(f"- **Total Cases Analyzed:** {len(case_stats)}")
        print(f"- **Average Consensus Rate:** {avg_consensus:.1f}%")
        print(f"- **Average Unique Diagnoses per Case:** {avg_unique:.1f}")
        
        # Find high and low consensus cases
        sorted_cases = sorted(case_stats, key=lambda x: x['consensus_rate'], reverse=True)
        
        print(f"\n### Highest Consensus Cases:")
        for case in sorted_cases[:3]:
            print(f"- {case['case']}: {case['consensus_rate']:.1f}% ({case['consensus']})")
        
        print(f"\n### Lowest Consensus Cases:")
        for case in sorted_cases[-3:]:
            print(f"- {case['case']}: {case['consensus_rate']:.1f}% ({case['consensus']})")

if __name__ == "__main__":
    analyze_all_cases()
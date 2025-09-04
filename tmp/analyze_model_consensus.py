#!/usr/bin/env python3
"""
Analyze model consensus participation and unique diagnoses
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_model_consensus():
    """Analyze each model's unique diagnoses and consensus participation"""
    
    # Find all orchestrator analysis files
    base_path = Path("/Users/sabt/Library/CloudStorage/OneDrive-KarolinskaInstitutet/Github/DiverseAI/medley/cache/orchestrator")
    
    # Dictionary to store model statistics
    model_stats = defaultdict(lambda: {
        'primary_diagnoses': [],
        'consensus_participation': 0,
        'unique_diagnoses': set(),
        'total_cases': 0
    })
    
    # Process each case
    for case_dir in base_path.glob("Case_*"):
        # Get the latest orchestrator analysis file
        analysis_files = list(case_dir.glob("orchestrator_analysis_*.json"))
        if not analysis_files:
            continue
            
        # Use the most recent file
        latest_file = max(analysis_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Get the primary consensus diagnosis
        if 'diagnostic_analysis' in data and 'primary_consensus' in data['diagnostic_analysis']:
            consensus_diagnosis = data['diagnostic_analysis']['primary_consensus'].get('diagnosis', '')
            consensus_count = data['diagnostic_analysis']['primary_consensus'].get('count', 0)
            total_models = data['diagnostic_analysis']['primary_consensus'].get('total_models', 0)
            
            # Track which models participated in consensus
            if 'model_responses' in data:
                for response in data['model_responses']:
                    model_name = response.get('model_name', '')
                    if not model_name:
                        continue
                    
                    model_stats[model_name]['total_cases'] += 1
                    
                    # Extract primary diagnosis
                    try:
                        response_text = response.get('response', '')
                        if isinstance(response_text, str) and response_text.strip().startswith('{'):
                            response_json = json.loads(response_text)
                            primary_diag = response_json.get('primary_diagnosis', {}).get('name', '')
                            
                            model_stats[model_name]['primary_diagnoses'].append(primary_diag)
                            
                            # Check if this model participated in consensus
                            if primary_diag and consensus_diagnosis and primary_diag.lower() in consensus_diagnosis.lower():
                                model_stats[model_name]['consensus_participation'] += 1
                            
                            # Collect all diagnoses (primary + differentials)
                            model_stats[model_name]['unique_diagnoses'].add(primary_diag)
                            for diff in response_json.get('differential_diagnoses', []):
                                model_stats[model_name]['unique_diagnoses'].add(diff.get('name', ''))
                    except:
                        pass
    
    # Create summary table
    print("\n# Model Consensus Participation and Diagnostic Diversity Analysis\n")
    print("| Model | Cases Analyzed | Consensus Participation | Unique Diagnoses | Consensus Rate |")
    print("|-------|----------------|------------------------|------------------|----------------|")
    
    for model, stats in sorted(model_stats.items()):
        if stats['total_cases'] > 0:
            consensus_rate = (stats['consensus_participation'] / stats['total_cases']) * 100
            unique_count = len(stats['unique_diagnoses'])
            
            # Clean model name for display
            display_name = model.replace('/', '-')
            
            print(f"| {display_name} | {stats['total_cases']} | {stats['consensus_participation']} | {unique_count} | {consensus_rate:.1f}% |")
    
    # Additional analysis
    print("\n## Summary Statistics\n")
    
    total_models = len(model_stats)
    avg_consensus_rate = sum(
        (stats['consensus_participation'] / stats['total_cases'] * 100) if stats['total_cases'] > 0 else 0
        for stats in model_stats.values()
    ) / total_models if total_models > 0 else 0
    
    avg_unique_diagnoses = sum(len(stats['unique_diagnoses']) for stats in model_stats.values()) / total_models if total_models > 0 else 0
    
    print(f"- **Total Models Analyzed:** {total_models}")
    print(f"- **Average Consensus Rate:** {avg_consensus_rate:.1f}%")
    print(f"- **Average Unique Diagnoses per Model:** {avg_unique_diagnoses:.1f}")
    
    # Find most and least consensus-oriented models
    if model_stats:
        sorted_by_consensus = sorted(
            [(model, (stats['consensus_participation'] / stats['total_cases'] * 100) if stats['total_cases'] > 0 else 0) 
             for model, stats in model_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        print(f"\n### Top 3 Consensus-Oriented Models:")
        for model, rate in sorted_by_consensus[:3]:
            print(f"1. {model}: {rate:.1f}% consensus rate")
        
        print(f"\n### Top 3 Diverse/Contrarian Models:")
        for model, rate in sorted_by_consensus[-3:]:
            print(f"1. {model}: {rate:.1f}% consensus rate")

if __name__ == "__main__":
    analyze_model_consensus()
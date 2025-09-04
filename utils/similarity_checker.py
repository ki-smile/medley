#!/usr/bin/env python
"""
Case Similarity Checker for MEDLEY
Identifies similar cases in the database for comparison and learning
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import hashlib

class CaseSimilarityChecker:
    """Check similarity between medical cases"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path("cache/responses")
        # Medical keywords for weighted similarity
        self.medical_keywords = {
            # Symptoms
            'fever': 3, 'pain': 2, 'cough': 2, 'fatigue': 2, 'headache': 2,
            'nausea': 2, 'vomiting': 2, 'diarrhea': 2, 'rash': 3, 'bleeding': 3,
            'swelling': 2, 'dyspnea': 3, 'chest': 3, 'abdominal': 2,
            
            # Conditions
            'diabetes': 3, 'hypertension': 3, 'cancer': 4, 'infection': 3,
            'pneumonia': 3, 'asthma': 3, 'copd': 3, 'heart': 3, 'kidney': 3,
            'liver': 3, 'stroke': 4, 'sepsis': 4, 'trauma': 3,
            
            # Demographics
            'male': 1, 'female': 1, 'child': 2, 'elderly': 2, 'pregnant': 3,
            'infant': 2, 'adolescent': 1, 'adult': 1,
            
            # Urgency
            'emergency': 4, 'acute': 3, 'chronic': 2, 'severe': 3, 'mild': 1,
            'critical': 4, 'stable': 1, 'deteriorating': 3
        }
    
    def extract_features(self, case_text: str) -> Dict[str, any]:
        """
        Extract key features from case text
        
        Args:
            case_text: Medical case description
            
        Returns:
            Dictionary of extracted features
        """
        case_lower = case_text.lower()
        
        # Extract age
        age = None
        age_match = re.search(r'(\d+)[\s-]*(year|yr|y\.?o\.?|month|mo|day|week)', case_lower)
        if age_match:
            age = int(age_match.group(1))
            if 'month' in age_match.group(2):
                age = age / 12  # Convert months to years
            elif 'day' in age_match.group(2):
                age = age / 365  # Convert days to years
            elif 'week' in age_match.group(2):
                age = age / 52  # Convert weeks to years
        
        # Extract gender
        gender = None
        if re.search(r'\b(male|man|boy|he|his)\b', case_lower):
            gender = 'male'
        elif re.search(r'\b(female|woman|girl|she|her)\b', case_lower):
            gender = 'female'
        
        # Extract symptoms and conditions
        found_keywords = {}
        for keyword, weight in self.medical_keywords.items():
            if keyword in case_lower:
                found_keywords[keyword] = weight
        
        # Extract vital signs
        vitals = {}
        # Blood pressure
        bp_match = re.search(r'(\d+)/(\d+)\s*mm\s*hg', case_lower)
        if bp_match:
            vitals['bp_systolic'] = int(bp_match.group(1))
            vitals['bp_diastolic'] = int(bp_match.group(2))
        
        # Heart rate
        hr_match = re.search(r'(hr|heart rate|pulse)[:\s]*(\d+)', case_lower)
        if hr_match:
            vitals['heart_rate'] = int(hr_match.group(2))
        
        # Temperature
        temp_match = re.search(r'(temp|temperature)[:\s]*(\d+\.?\d*)\s*[cf°]', case_lower)
        if temp_match:
            vitals['temperature'] = float(temp_match.group(2))
        
        # SpO2
        spo2_match = re.search(r'(spo2|o2\s*sat|oxygen)[:\s]*(\d+)%?', case_lower)
        if spo2_match:
            vitals['spo2'] = int(spo2_match.group(2))
        
        return {
            'age': age,
            'gender': gender,
            'keywords': found_keywords,
            'vitals': vitals,
            'text_length': len(case_text),
            'hash': hashlib.md5(case_text.encode()).hexdigest()[:8]
        }
    
    def calculate_similarity(
        self, 
        case1_text: str, 
        case2_text: str,
        use_weighted: bool = True
    ) -> float:
        """
        Calculate similarity score between two cases
        
        Args:
            case1_text: First case text
            case2_text: Second case text
            use_weighted: Use weighted medical keywords
            
        Returns:
            Similarity score (0-100)
        """
        # Extract features
        features1 = self.extract_features(case1_text)
        features2 = self.extract_features(case2_text)
        
        scores = []
        weights = []
        
        # Text similarity (base)
        text_similarity = SequenceMatcher(None, case1_text.lower(), case2_text.lower()).ratio()
        scores.append(text_similarity * 100)
        weights.append(2)
        
        # Age similarity
        if features1['age'] and features2['age']:
            age_diff = abs(features1['age'] - features2['age'])
            age_similarity = max(0, 100 - age_diff * 2)  # 2% penalty per year difference
            scores.append(age_similarity)
            weights.append(1)
        
        # Gender match
        if features1['gender'] and features2['gender']:
            gender_match = 100 if features1['gender'] == features2['gender'] else 0
            scores.append(gender_match)
            weights.append(0.5)
        
        # Keyword overlap (weighted if enabled)
        if features1['keywords'] and features2['keywords']:
            common_keywords = set(features1['keywords'].keys()) & set(features2['keywords'].keys())
            
            if use_weighted:
                # Weighted score based on importance
                total_weight1 = sum(features1['keywords'].values())
                total_weight2 = sum(features2['keywords'].values())
                common_weight = sum(features1['keywords'].get(k, 0) for k in common_keywords)
                keyword_similarity = (common_weight / max(total_weight1, total_weight2)) * 100
            else:
                # Simple Jaccard similarity
                all_keywords = set(features1['keywords'].keys()) | set(features2['keywords'].keys())
                keyword_similarity = (len(common_keywords) / len(all_keywords)) * 100 if all_keywords else 0
            
            scores.append(keyword_similarity)
            weights.append(3)
        
        # Vital signs similarity
        if features1['vitals'] and features2['vitals']:
            vital_scores = []
            for vital in ['bp_systolic', 'heart_rate', 'temperature', 'spo2']:
                if vital in features1['vitals'] and vital in features2['vitals']:
                    v1 = features1['vitals'][vital]
                    v2 = features2['vitals'][vital]
                    # Normalize difference based on vital type
                    if vital == 'bp_systolic':
                        diff_penalty = abs(v1 - v2) / 2  # 50% at 100 mmHg difference
                    elif vital == 'heart_rate':
                        diff_penalty = abs(v1 - v2) / 1  # 50% at 50 bpm difference
                    elif vital == 'temperature':
                        diff_penalty = abs(v1 - v2) * 20  # 50% at 2.5°C difference
                    else:  # spo2
                        diff_penalty = abs(v1 - v2) * 2  # 50% at 25% difference
                    
                    vital_scores.append(max(0, 100 - diff_penalty))
            
            if vital_scores:
                scores.append(sum(vital_scores) / len(vital_scores))
                weights.append(1)
        
        # Calculate weighted average
        if scores:
            total_score = sum(s * w for s, w in zip(scores, weights))
            total_weight = sum(weights)
            similarity = total_score / total_weight
        else:
            similarity = text_similarity * 100
        
        return round(similarity, 2)
    
    def find_similar_cases(
        self,
        case_text: str,
        cases_dir: Path = None,
        threshold: float = 70.0,
        top_n: int = 5
    ) -> List[Tuple[str, float, Dict]]:
        """
        Find similar cases in the database
        
        Args:
            case_text: Case to compare
            cases_dir: Directory with case files
            threshold: Minimum similarity score
            top_n: Maximum number of results
            
        Returns:
            List of (case_id, similarity_score, features) tuples
        """
        cases_dir = cases_dir or Path("usecases")
        similar_cases = []
        
        # Check all case files
        for case_file in cases_dir.glob("*.txt"):
            try:
                with open(case_file, 'r', encoding='utf-8') as f:
                    other_case_text = f.read()
                
                # Skip if same case
                if case_text.strip() == other_case_text.strip():
                    continue
                
                similarity = self.calculate_similarity(case_text, other_case_text)
                
                if similarity >= threshold:
                    features = self.extract_features(other_case_text)
                    similar_cases.append((
                        case_file.stem,
                        similarity,
                        features
                    ))
            except Exception as e:
                print(f"Error processing {case_file}: {e}")
                continue
        
        # Sort by similarity and return top N
        similar_cases.sort(key=lambda x: x[1], reverse=True)
        return similar_cases[:top_n]
    
    def get_similarity_report(
        self,
        case_text: str,
        similar_cases: List[Tuple[str, float, Dict]]
    ) -> Dict:
        """
        Generate similarity analysis report
        
        Args:
            case_text: Original case
            similar_cases: List of similar cases
            
        Returns:
            Similarity report dictionary
        """
        features = self.extract_features(case_text)
        
        report = {
            'case_features': features,
            'similar_cases': [],
            'common_patterns': {},
            'recommendations': []
        }
        
        # Analyze similar cases
        for case_id, similarity, case_features in similar_cases:
            report['similar_cases'].append({
                'case_id': case_id,
                'similarity_score': similarity,
                'matching_keywords': list(
                    set(features['keywords'].keys()) & 
                    set(case_features['keywords'].keys())
                ),
                'age_match': abs(features.get('age', 0) - case_features.get('age', 0)) < 10 if features.get('age') else None,
                'gender_match': features.get('gender') == case_features.get('gender')
            })
        
        # Find common patterns
        all_keywords = []
        for _, _, case_features in similar_cases:
            all_keywords.extend(case_features['keywords'].keys())
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        report['common_patterns'] = dict(keyword_counts.most_common(10))
        
        # Generate recommendations
        if similar_cases:
            report['recommendations'].append(
                f"Found {len(similar_cases)} similar cases with average similarity of "
                f"{sum(s[1] for s in similar_cases) / len(similar_cases):.1f}%"
            )
            
            if report['common_patterns']:
                top_pattern = list(report['common_patterns'].keys())[0]
                report['recommendations'].append(
                    f"Most common pattern in similar cases: {top_pattern}"
                )
        
        return report


# Example usage
if __name__ == "__main__":
    checker = CaseSimilarityChecker()
    
    # Example cases
    case1 = """
    A 45-year-old male presents with chest pain, shortness of breath, and 
    diaphoresis. BP 160/95, HR 110, SpO2 92%. History of hypertension and diabetes.
    """
    
    case2 = """
    A 50-year-old man with acute chest pain radiating to left arm. 
    BP 155/90, HR 105, SpO2 93%. Known diabetic and hypertensive.
    """
    
    case3 = """
    A 12-year-old girl with fever, rash, and joint pain for 3 days.
    Temperature 39°C, HR 95. No significant past medical history.
    """
    
    # Calculate similarities
    print(f"Case 1 vs Case 2: {checker.calculate_similarity(case1, case2):.1f}%")
    print(f"Case 1 vs Case 3: {checker.calculate_similarity(case1, case3):.1f}%")
    print(f"Case 2 vs Case 3: {checker.calculate_similarity(case2, case3):.1f}%")
    
    # Extract features
    features = checker.extract_features(case1)
    print(f"\nCase 1 features: {json.dumps(features, indent=2)}")
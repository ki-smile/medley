"""
ICD-10 Database and Intelligent Diagnosis Normalization
"""
from typing import Dict, List, Tuple, Optional
import difflib
import re

class ICD10Database:
    """Comprehensive ICD-10 database with intelligent diagnosis matching"""
    
    def __init__(self):
        # Comprehensive ICD-10 mapping with variations
        self.icd10_codes = {
            # Infectious diseases (A00-B99)
            "Tuberculosis": {"code": "A15.9", "variations": ["tb", "tuberculosis", "mycobacterium tuberculosis"]},
            "Abdominal Tuberculosis": {"code": "A18.31", "variations": ["abdominal tb", "intestinal tuberculosis"]},
            "Tuberculous Peritonitis": {"code": "A18.31", "variations": ["tb peritonitis", "peritoneal tuberculosis"]},
            "Melioidosis": {"code": "A24.4", "variations": ["whitmore's disease", "pseudomonas pseudomallei"]},
            
            # Neoplasms (C00-D49)
            "Lymphoma": {"code": "C85.9", "variations": ["lymphatic cancer", "hodgkin", "non-hodgkin"]},
            
            # Blood disorders (D50-D89)
            "Thrombotic Thrombocytopenic Purpura": {"code": "M31.1", "variations": ["ttp", "moschcowitz syndrome"]},
            "Hereditary Angioedema": {"code": "D84.1", "variations": ["hae", "c1 esterase inhibitor deficiency"]},
            
            # Endocrine disorders (E00-E89)
            "Thyroid Storm": {"code": "E05.01", "variations": ["thyrotoxic crisis", "hyperthyroid crisis"]},
            "Diabetes Mellitus": {"code": "E11.9", "variations": ["dm", "type 2 diabetes", "diabetes type 2"]},
            "Acute Intermittent Porphyria": {"code": "E80.21", "variations": ["aip", "porphyria", "acute porphyria"]},
            "Familial Mediterranean Fever": {"code": "E85.0", "variations": ["fmf", "mediterranean fever", "periodic fever"]},
            
            # Mental disorders (F00-F99)
            "Dementia": {"code": "F03.90", "variations": ["cognitive decline", "memory loss", "alzheimer"]},
            "Alzheimer's Disease": {"code": "G30.9", "variations": ["alzheimer", "ad", "alzheimer's dementia"]},
            "Delirium": {"code": "F05.9", "variations": ["acute confusion", "altered mental status"]},
            
            # Nervous system (G00-G99)
            "Parkinson's Disease": {"code": "G20", "variations": ["parkinsonism", "pd", "parkinsons"]},
            "Multiple Sclerosis": {"code": "G35", "variations": ["ms", "disseminated sclerosis"]},
            "Myasthenia Gravis": {"code": "G70.00", "variations": ["mg", "muscle weakness"]},
            
            # Circulatory system (I00-I99)
            "Rheumatic Fever": {"code": "I00", "variations": ["acute rheumatic fever", "rheumatic heart disease"]},
            "Hypertensive Emergency": {"code": "I16.0", "variations": ["malignant hypertension", "hypertensive crisis"]},
            "Heart Failure": {"code": "I50.9", "variations": ["chf", "congestive heart failure", "cardiac failure"]},
            
            # Respiratory system (J00-J99)
            "Pneumonia": {"code": "J18.9", "variations": ["lung infection", "chest infection", "cap"]},
            "Asthma": {"code": "J45.909", "variations": ["bronchial asthma", "reactive airway disease"]},
            "COPD": {"code": "J44.9", "variations": ["chronic obstructive pulmonary disease", "emphysema"]},
            
            # Digestive system (K00-K95)
            "Crohn's Disease": {"code": "K50.90", "variations": ["crohn", "crohns", "regional enteritis", "crohn's"]},
            "Ulcerative Colitis": {"code": "K51.90", "variations": ["uc", "colitis ulcerosa"]},
            "Inflammatory Bowel Disease": {"code": "K52.9", "variations": ["ibd", "inflammatory bowel", "bowel inflammation"]},
            "Irritable Bowel Syndrome": {"code": "K58.9", "variations": ["ibs", "spastic colon", "nervous colon"]},
            "Acute Appendicitis": {"code": "K35.80", "variations": ["appendicitis", "appendix inflammation"]},
            "Peritonitis": {"code": "K65.9", "variations": ["peritoneal inflammation", "acute peritonitis"]},
            "Celiac Disease": {"code": "K90.0", "variations": ["coeliac", "gluten sensitivity", "sprue"]},
            
            # Skin disorders (L00-L99)
            "Psoriasis": {"code": "L40.9", "variations": ["psoriatic disease", "plaque psoriasis"]},
            "Psoriatic Arthritis": {"code": "L40.50", "variations": ["psa", "arthropathic psoriasis"]},
            "Atopic Dermatitis": {"code": "L20.9", "variations": ["eczema", "atopic eczema"]},
            
            # Musculoskeletal (M00-M99)
            "Septic Arthritis": {"code": "M00.9", "variations": ["infectious arthritis", "joint infection", "pyogenic arthritis"]},
            "Reactive Arthritis": {"code": "M02.9", "variations": ["reiter's syndrome", "post-infectious arthritis"]},
            "Rheumatoid Arthritis": {"code": "M06.9", "variations": ["ra", "chronic polyarthritis"]},
            "Adult-Onset Still's Disease": {"code": "M06.1", "variations": ["aosd", "still's disease", "adult still"]},
            "Gouty Arthritis": {"code": "M10.9", "variations": ["gout", "podagra", "tophaceous gout"]},
            "Systemic Lupus Erythematosus": {"code": "M32.9", "variations": ["sle", "lupus", "systemic lupus"]},
            "Behçet's Disease": {"code": "M35.2", "variations": ["behcet", "behcet's syndrome", "silk road disease"]},
            "Sjögren's Syndrome": {"code": "M35.00", "variations": ["sjogren", "sicca syndrome"]},
            "Polymyalgia Rheumatica": {"code": "M35.3", "variations": ["pmr", "polymyalgia"]},
            "Fibromyalgia": {"code": "M79.7", "variations": ["fibromyalgia syndrome", "fms"]},
            "Ankylosing Spondylitis": {"code": "M45.9", "variations": ["as", "bechterew's disease", "marie-strumpell disease"]},
            "PFAPA Syndrome": {"code": "M04.8", "variations": ["periodic fever syndrome", "marshall syndrome"]},
            "TRAPS": {"code": "M04.8", "variations": ["tnf receptor associated periodic syndrome", "familial hibernian fever"]},
            "Autoinflammatory Disease": {"code": "M04.9", "variations": ["autoinflammatory syndrome", "periodic fever"]},
            
            # Genitourinary (N00-N99)
            "Urinary Tract Infection": {"code": "N39.0", "variations": ["uti", "cystitis", "bladder infection"]},
            "Pyelonephritis": {"code": "N10", "variations": ["kidney infection", "upper uti"]},
            
            # Pregnancy related (O00-O9A)
            "Pre-eclampsia": {"code": "O14.90", "variations": ["preeclampsia", "pregnancy hypertension"]},
            
            # Congenital (Q00-Q99)
            "Marfan Syndrome": {"code": "Q87.40", "variations": ["marfan", "marfan's syndrome"]},
            
            # Symptoms/signs (R00-R99)
            "Fever of Unknown Origin": {"code": "R50.9", "variations": ["fuo", "pyrexia of unknown origin"]},
            "Chest Pain": {"code": "R07.9", "variations": ["thoracic pain", "precordial pain"]},
            
            # Injury/poisoning (S00-T88)
            "Lead Poisoning": {"code": "T56.0X1A", "variations": ["plumbism", "lead toxicity", "lead intoxication"]},
            
            # External causes (V00-Y99)
            
            # Special codes (Z00-Z99)
            "Long COVID": {"code": "U09.9", "variations": ["post covid", "post-covid syndrome", "long hauler"]}
        }
        
        # Create reverse mapping for quick lookup
        self.variation_to_diagnosis = {}
        for diagnosis, info in self.icd10_codes.items():
            for variation in info["variations"]:
                self.variation_to_diagnosis[variation.lower()] = diagnosis
    
    def normalize_diagnosis(self, diagnosis_text: str) -> str:
        """
        Normalize a diagnosis name to its canonical form
        Uses fuzzy matching if exact match not found
        """
        if not diagnosis_text:
            return diagnosis_text
        
        # Clean the input
        text = diagnosis_text.strip()
        text_lower = text.lower()
        
        # Remove common parenthetical additions
        if '(' in text_lower:
            base = text_lower.split('(')[0].strip()
        else:
            base = text_lower
        
        # Check exact match in canonical names
        for canonical_name in self.icd10_codes.keys():
            if canonical_name.lower() == base:
                return canonical_name
        
        # Check variations
        if base in self.variation_to_diagnosis:
            return self.variation_to_diagnosis[base]
        
        # Fuzzy matching for close matches
        best_match = self._fuzzy_match_diagnosis(base)
        if best_match:
            return best_match
        
        # Return original with proper capitalization if no match
        return self._title_case_medical(diagnosis_text)
    
    def _fuzzy_match_diagnosis(self, text: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find the best fuzzy match for a diagnosis
        """
        all_terms = list(self.icd10_codes.keys()) + list(self.variation_to_diagnosis.keys())
        matches = difflib.get_close_matches(text, all_terms, n=1, cutoff=threshold)
        
        if matches:
            match = matches[0]
            # Return canonical form
            if match in self.icd10_codes:
                return match
            elif match.lower() in self.variation_to_diagnosis:
                return self.variation_to_diagnosis[match.lower()]
        
        return None
    
    def _title_case_medical(self, text: str) -> str:
        """
        Properly capitalize medical terms
        """
        # List of words that should stay lowercase
        lowercase_words = {'of', 'and', 'or', 'the', 'in', 'with', 'due', 'to', 'by'}
        # List of acronyms that should stay uppercase
        acronyms = {'ibd', 'sle', 'copd', 'uti', 'fmf', 'tb', 'hiv', 'aids', 'icu'}
        
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in acronyms:
                result.append(word.upper())
            elif i == 0 or word_lower not in lowercase_words:
                result.append(word.capitalize())
            else:
                result.append(word_lower)
        
        return ' '.join(result)
    
    def get_icd10_code(self, diagnosis: str) -> str:
        """
        Get the ICD-10 code for a diagnosis
        """
        # First normalize the diagnosis
        normalized = self.normalize_diagnosis(diagnosis)
        
        # Look up the code
        if normalized in self.icd10_codes:
            return self.icd10_codes[normalized]["code"]
        
        # Return empty string if not found
        return ""
    
    def merge_similar_diagnoses(self, diagnoses: Dict[str, int]) -> Dict[str, int]:
        """
        Merge similar diagnoses based on normalization
        Returns a dictionary with merged counts
        """
        merged = {}
        
        for diagnosis, count in diagnoses.items():
            normalized = self.normalize_diagnosis(diagnosis)
            if normalized in merged:
                merged[normalized] += count
            else:
                merged[normalized] = count
        
        return merged
    
    def extract_icd_from_text(self, text: str) -> Optional[str]:
        """
        Extract ICD-10 code from text using regex
        """
        # Common ICD-10 patterns
        patterns = [
            r'[A-Z]\d{2}(?:\.\d{1,2})?',  # Basic ICD-10 format
            r'[A-Z]\d{2}\.X\d[A-Z]?',      # Extended format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None


# Singleton instance
_icd10_db = None

def get_icd10_database() -> ICD10Database:
    """Get or create the singleton ICD-10 database instance"""
    global _icd10_db
    if _icd10_db is None:
        _icd10_db = ICD10Database()
    return _icd10_db
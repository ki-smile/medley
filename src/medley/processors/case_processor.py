"""
Case Processor for medical case files
Handles reading, parsing, and preparing medical cases for analysis
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class MedicalCase:
    """Structured representation of a medical case"""
    case_id: str
    title: str
    patient_info: str
    presentation: str
    symptoms: List[str]
    history: Optional[str] = None
    labs: Optional[str] = None
    imaging: Optional[str] = None
    physical_exam: Optional[str] = None
    metadata: Dict[str, Any] = None
    bias_testing_target: Optional[str] = None  # Internal use only, not sent to LLMs
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding bias_testing_target"""
        data = asdict(self)
        # Remove bias_testing_target from external representation
        data.pop('bias_testing_target', None)
        return data
    
    def to_prompt(self) -> str:
        """Convert case to a formatted prompt string (excludes bias testing info)"""
        # IMPORTANT: Never include bias_testing_target in prompts
        prompt_parts = [
            f"**Case ID:** {self.case_id}",
            f"**Title:** {self.title}",
            f"\n**Patient Information:**\n{self.patient_info}",
            f"\n**Presentation:**\n{self.presentation}"
        ]
        
        if self.symptoms:
            prompt_parts.append(f"\n**Key Symptoms:**\n- " + "\n- ".join(self.symptoms))
        
        if self.history:
            prompt_parts.append(f"\n**Medical History:**\n{self.history}")
        
        if self.physical_exam:
            prompt_parts.append(f"\n**Physical Examination:**\n{self.physical_exam}")
        
        if self.labs:
            prompt_parts.append(f"\n**Laboratory Results:**\n{self.labs}")
        
        if self.imaging:
            prompt_parts.append(f"\n**Imaging:**\n{self.imaging}")
        
        return "\n".join(prompt_parts)

class CaseProcessor:
    """Processes medical case files for analysis"""
    
    def __init__(self, cases_dir: Optional[Path] = None):
        self.cases_dir = cases_dir or Path.cwd() / "usecases"
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        
    def load_case_from_file(self, file_path: Path) -> MedicalCase:
        """Load a medical case from a text or JSON file"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"Case file not found: {file_path}")
        
        # Determine file type and parse accordingly
        if file_path.suffix == ".json":
            return self._load_json_case(file_path)
        elif file_path.suffix in [".txt", ".md"]:
            return self._parse_text_case(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def _load_json_case(self, file_path: Path) -> MedicalCase:
        """Load case from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return MedicalCase(
            case_id=data.get("case_id", file_path.stem),
            title=data.get("title", "Untitled Case"),
            patient_info=data.get("patient_info", ""),
            presentation=data.get("presentation", ""),
            symptoms=data.get("symptoms", []),
            history=data.get("history"),
            labs=data.get("labs"),
            imaging=data.get("imaging"),
            physical_exam=data.get("physical_exam"),
            metadata=data.get("metadata", {}),
            bias_testing_target=data.get("bias_testing_target")  # Load but won't send to LLMs
        )
    
    def _parse_text_case(self, file_path: Path) -> MedicalCase:
        """Parse case from text/markdown file"""
        with open(file_path, 'r') as f:
            original_content = f.read()
        
        # Extract bias testing target before filtering (for internal use)
        bias_testing_target = None
        for line in original_content.split('\n'):
            if "bias testing target" in line.lower() or "evaluation target" in line.lower():
                # Extract everything after the colon
                if ':' in line:
                    bias_testing_target = line.split(':', 1)[1].strip()
                    break
        
        # IMPORTANT: Remove bias testing targets and metadata that shouldn't be sent to LLMs
        # These lines typically start with "**Bias Testing Target:**" or similar
        lines_to_exclude = [
            "bias testing target",
            "evaluation target",
            "test target",
            "metadata:",
            "scoring:",
            "evaluation criteria:"
        ]
        
        # Filter out lines containing bias/evaluation metadata
        filtered_lines = []
        for line in original_content.split('\n'):
            # Check if line contains any excluded patterns
            line_lower = line.lower()
            
            # More precise filtering - only exclude if line starts with metadata marker
            should_exclude = False
            
            # Check if line starts with **Bias or similar metadata markers
            if line.strip().startswith("**"):
                # Only exclude if it's a bias/evaluation metadata line
                for pattern in lines_to_exclude:
                    if pattern in line_lower and ":" in line:
                        should_exclude = True
                        break
            
            if not should_exclude:
                filtered_lines.append(line)
        
        # Reconstruct content without bias metadata
        content = '\n'.join(filtered_lines)
        
        # Simple parsing for structured text cases
        # Looking for patterns like "**Patient:**" or "## Case X:"
        
        lines = content.split('\n')
        case_id = file_path.stem
        title = ""
        patient_info = ""
        presentation = ""
        symptoms = []
        
        # Try to extract case number from filename or content
        for line in lines[:5]:  # Check first 5 lines for case identifier
            if "Case" in line and (":" in line or "#" in line):
                parts = line.replace("#", "").replace("*", "").split(":")
                if len(parts) >= 2:
                    case_id = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else ""
                break
        
        # Extract patient information and presentation
        if "**Patient:**" in content:
            # Patient info is marked with **Patient:**
            start = content.index("**Patient:**")
            # Get everything after **Patient:** as the presentation
            full_patient_text = content[start:].strip()
            presentation = full_patient_text
            # Don't duplicate the title line in patient_info
            patient_info = ""
        else:
            # Fallback: use paragraphs approach
            paragraphs = content.split("\n\n")
            # Skip the first paragraph if it's the title line
            if paragraphs and paragraphs[0].startswith("##"):
                # First paragraph is title, second is actual content
                presentation = "\n\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""
            else:
                presentation = content.strip()
            patient_info = ""
        
        # Extract symptoms if listed
        if "symptoms" in content.lower() or "presents with" in content.lower():
            # Basic symptom extraction
            symptom_keywords = [
                "fever", "pain", "fatigue", "weight loss", "confusion",
                "tremor", "weakness", "rash", "arthritis", "headache",
                "nausea", "vomiting", "diarrhea", "cough", "dyspnea"
            ]
            for keyword in symptom_keywords:
                if keyword in content.lower():
                    symptoms.append(keyword.capitalize())
        
        return MedicalCase(
            case_id=case_id,
            title=title or f"Medical Case from {file_path.name}",
            patient_info=patient_info,
            presentation=presentation or content,
            symptoms=symptoms,
            metadata={"source_file": str(file_path)},
            bias_testing_target=bias_testing_target  # Store internally but won't be sent to LLMs
        )
    
    def load_all_cases(self) -> List[MedicalCase]:
        """Load all cases from the cases directory"""
        cases = []
        
        for file_path in self.cases_dir.glob("*"):
            # Skip non-case files like summaries and documentation
            if file_path.name.upper() in ["README.MD", "CASE_SUMMARY.MD", "INDEX.MD"]:
                continue
            
            if file_path.suffix in [".txt", ".md", ".json"]:
                # Only load files that start with "case_"
                if file_path.stem.lower().startswith("case_"):
                    try:
                        case = self.load_case_from_file(file_path)
                        cases.append(case)
                    except Exception as e:
                        print(f"Error loading case {file_path}: {e}")
        
        return cases
    
    def save_case(self, case: MedicalCase, file_path: Optional[Path] = None):
        """Save a case to a JSON file"""
        if not file_path:
            file_path = self.cases_dir / f"{case.case_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(case.to_dict(), f, indent=2, default=str)
    
    def create_case_from_text(
        self,
        text: str,
        case_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> MedicalCase:
        """Create a case object from raw text"""
        
        if not case_id:
            case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Simple parsing to extract patient info from first paragraph
        paragraphs = text.strip().split("\n\n")
        patient_info = paragraphs[0] if paragraphs else text
        presentation = "\n\n".join(paragraphs[1:]) if len(paragraphs) > 1 else text
        
        return MedicalCase(
            case_id=case_id,
            title=title or "Medical Case",
            patient_info=patient_info,
            presentation=presentation,
            symptoms=[],  # Would need NLP to extract properly
            metadata={"created": datetime.now().isoformat()}
        )
"""
Cache Manager for storing and retrieving LLM responses
Implements hash-based caching to avoid redundant API calls
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import asdict

from ..models.llm_manager import LLMResponse

class CacheManager:
    """Manages file-based caching of LLM responses"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.cwd() / "cache"
        self.responses_dir = self.cache_dir / "responses"
        self.ensembles_dir = self.cache_dir / "ensembles"
        self.metadata_dir = self.cache_dir / "metadata"
        
        # Create cache directories
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.ensembles_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create cache index
        self.index_file = self.metadata_dir / "cache_index.json"
        self.prompt_hashes_file = self.metadata_dir / "prompt_hashes.json"
        self.cache_index = self._load_cache_index()
        self.prompt_hashes = self._load_prompt_hashes()
        
    def _load_cache_index(self) -> Dict[str, Any]:
        """Load cache index from file"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_prompt_hashes(self) -> Dict[str, str]:
        """Load prompt hash mappings"""
        if self.prompt_hashes_file.exists():
            with open(self.prompt_hashes_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache_index(self):
        """Save cache index to file"""
        with open(self.index_file, 'w') as f:
            json.dump(self.cache_index, f, indent=2, default=str)
    
    def _save_prompt_hashes(self):
        """Save prompt hash mappings"""
        with open(self.prompt_hashes_file, 'w') as f:
            json.dump(self.prompt_hashes, f, indent=2)
    
    def generate_cache_key(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate unique cache key for a prompt-model combination"""
        
        # Combine all inputs for hashing
        cache_input = f"{prompt}|{model_id}"
        if system_prompt:
            cache_input += f"|{system_prompt}"
        
        # Generate SHA256 hash
        hash_object = hashlib.sha256(cache_input.encode())
        cache_key = hash_object.hexdigest()[:16]  # Use first 16 chars
        
        # Store mapping for debugging
        self.prompt_hashes[cache_key] = {
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "model_id": model_id,
            "timestamp": datetime.now().isoformat()
        }
        self._save_prompt_hashes()
        
        return cache_key
    
    def get_cached_response(
        self,
        case_id: str,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_age_hours: int = 24
    ) -> Optional[LLMResponse]:
        """Retrieve cached response if available and fresh"""
        
        cache_key = self.generate_cache_key(prompt, model_id, system_prompt)
        
        # Check if response exists in index
        if cache_key not in self.cache_index:
            return None
        
        cache_entry = self.cache_index[cache_key]
        
        # Check age of cache entry
        cached_time = datetime.fromisoformat(cache_entry["timestamp"])
        if datetime.now() - cached_time > timedelta(hours=max_age_hours):
            return None
        
        # Load response from file
        response_file = Path(cache_entry["file_path"])
        if not response_file.exists():
            # Cache index is out of sync, remove entry
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        with open(response_file, 'r') as f:
            response_data = json.load(f)
        
        # Reconstruct LLMResponse object
        return LLMResponse(**response_data)
    
    def save_response(
        self,
        case_id: str,
        model_id: str,
        prompt: str,
        response: LLMResponse,
        system_prompt: Optional[str] = None
    ):
        """Save LLM response to cache"""
        
        cache_key = self.generate_cache_key(prompt, model_id, system_prompt)
        
        # Create case directory if needed
        case_dir = self.responses_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from model name
        safe_model_name = model_id.replace("/", "_").replace(":", "_")
        response_file = case_dir / f"{safe_model_name}_{cache_key}.json"
        
        # Save response data
        with open(response_file, 'w') as f:
            json.dump(response.to_dict(), f, indent=2, default=str)
        
        # Update cache index
        self.cache_index[cache_key] = {
            "case_id": case_id,
            "model_id": model_id,
            "model_name": response.model_name,
            "file_path": str(response_file),
            "timestamp": datetime.now().isoformat(),
            "tokens_used": response.tokens_used,
            "latency": response.latency
        }
        self._save_cache_index()
    
    def get_case_responses(self, case_id: str) -> List[LLMResponse]:
        """Get all cached responses for a specific case"""
        
        case_dir = self.responses_dir / case_id
        if not case_dir.exists():
            return []
        
        responses = []
        for response_file in case_dir.glob("*.json"):
            with open(response_file, 'r') as f:
                response_data = json.load(f)
                responses.append(LLMResponse(**response_data))
        
        return responses
    
    def save_ensemble_result(
        self,
        case_id: str,
        ensemble_data: Dict[str, Any]
    ):
        """Save ensemble analysis result"""
        
        ensemble_file = self.ensembles_dir / f"{case_id}_ensemble.json"
        
        # Add metadata
        ensemble_data["timestamp"] = datetime.now().isoformat()
        ensemble_data["case_id"] = case_id
        
        with open(ensemble_file, 'w') as f:
            json.dump(ensemble_data, f, indent=2, default=str)
    
    def get_ensemble_result(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve ensemble analysis result"""
        
        ensemble_file = self.ensembles_dir / f"{case_id}_ensemble.json"
        
        if not ensemble_file.exists():
            return None
        
        with open(ensemble_file, 'r') as f:
            return json.load(f)
    
    def clear_case_cache(self, case_id: str):
        """Clear all cached data for a specific case"""
        
        # Remove response files
        case_dir = self.responses_dir / case_id
        if case_dir.exists():
            for file in case_dir.glob("*.json"):
                file.unlink()
            case_dir.rmdir()
        
        # Remove ensemble file
        ensemble_file = self.ensembles_dir / f"{case_id}_ensemble.json"
        if ensemble_file.exists():
            ensemble_file.unlink()
        
        # Update cache index
        keys_to_remove = [
            key for key, entry in self.cache_index.items()
            if entry.get("case_id") == case_id
        ]
        for key in keys_to_remove:
            del self.cache_index[key]
        self._save_cache_index()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics"""
        
        total_responses = len(self.cache_index)
        total_tokens = sum(entry.get("tokens_used", 0) for entry in self.cache_index.values())
        avg_latency = (
            sum(entry.get("latency", 0) for entry in self.cache_index.values()) / total_responses
            if total_responses > 0 else 0
        )
        
        # Count responses by model
        model_counts = {}
        for entry in self.cache_index.values():
            model_name = entry.get("model_name", "unknown")
            model_counts[model_name] = model_counts.get(model_name, 0) + 1
        
        # Count cases
        cases = set(entry.get("case_id") for entry in self.cache_index.values())
        
        return {
            "total_cached_responses": total_responses,
            "total_tokens_used": total_tokens,
            "average_latency": round(avg_latency, 2),
            "unique_cases": len(cases),
            "responses_by_model": model_counts,
            "cache_size_mb": round(self._get_cache_size() / (1024 * 1024), 2)
        }
    
    def _get_cache_size(self) -> int:
        """Calculate total cache size in bytes"""
        total_size = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
    
    def validate_cache(self) -> Dict[str, Any]:
        """Validate cache integrity"""
        
        issues = []
        
        # Check for orphaned index entries
        for cache_key, entry in self.cache_index.items():
            file_path = Path(entry["file_path"])
            if not file_path.exists():
                issues.append(f"Missing file for cache key {cache_key}: {file_path}")
        
        # Check for orphaned files
        for response_file in self.responses_dir.rglob("*.json"):
            # Check if file is referenced in index
            file_str = str(response_file)
            referenced = any(
                entry["file_path"] == file_str
                for entry in self.cache_index.values()
            )
            if not referenced:
                issues.append(f"Orphaned file not in index: {response_file}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "checked_entries": len(self.cache_index),
            "timestamp": datetime.now().isoformat()
        }
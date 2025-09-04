#!/usr/bin/env python
"""
Project Health Check Script for MEDLEY
Performs comprehensive validation of project structure and functionality
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

class HealthCheck:
    """Comprehensive health check for MEDLEY project"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success = []
        self.stats = {}
        
    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        print("🏥 MEDLEY PROJECT HEALTH CHECK")
        print("=" * 50)
        
        # Structure checks
        self.check_directory_structure()
        self.check_file_organization()
        self.check_dependencies()
        
        # Code quality checks
        self.check_python_files()
        self.check_tests()
        
        # Web application check
        self.check_web_app()
        
        # Data checks
        self.check_cache_integrity()
        self.check_reports()
        
        # Cleanup suggestions
        self.identify_cleanup_candidates()
        
        return self.generate_report()
    
    def check_directory_structure(self):
        """Check if all required directories exist"""
        print("\n📁 Checking directory structure...")
        
        required_dirs = [
            "src/medley",
            "src/medley/models",
            "src/medley/processors",
            "src/medley/reporters",
            "src/medley/utils",
            "usecases",
            "cache",
            "cache/responses",
            "cache/orchestrator",
            "reports",
            "tests",
            "tests/unit",
            "tests/integration",
            "examples",
            "docs"
        ]
        
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                self.success.append(f"✅ Directory exists: {dir_path}")
            else:
                self.issues.append(f"❌ Missing directory: {dir_path}")
    
    def check_file_organization(self):
        """Check for misplaced files"""
        print("\n📄 Checking file organization...")
        
        # Check for files that shouldn't be in root
        root_files = list(Path(".").glob("*"))
        
        problematic_patterns = {
            "*.pyc": "Python bytecode files",
            "*.log": "Log files",
            "*.cache": "Cache files",
            ".DS_Store": "macOS metadata",
            "test_*.py": "Test files",
            "*_test.py": "Test files",
            "debug_*.py": "Debug scripts",
            "temp_*.py": "Temporary files"
        }
        
        for pattern, description in problematic_patterns.items():
            matches = list(Path(".").glob(pattern))
            if matches:
                for match in matches:
                    self.warnings.append(f"⚠️  {description} in root: {match.name}")
        
        # Check for empty directories
        for root, dirs, files in os.walk("."):
            if not dirs and not files and ".git" not in root:
                self.warnings.append(f"⚠️  Empty directory: {root}")
    
    def check_dependencies(self):
        """Check if all dependencies are properly declared"""
        print("\n📦 Checking dependencies...")
        
        requirements_file = Path("requirements.txt")
        
        if requirements_file.exists():
            with open(requirements_file) as f:
                requirements = f.read().splitlines()
            
            required_packages = [
                "reportlab",
                "aiohttp",
                "python-dotenv",
                "pytest",
                "requests"
            ]
            
            for package in required_packages:
                if any(package in req for req in requirements):
                    self.success.append(f"✅ Required package found: {package}")
                else:
                    self.warnings.append(f"⚠️  Missing from requirements: {package}")
        else:
            self.issues.append("❌ requirements.txt not found")
    
    def check_python_files(self):
        """Check Python files for issues"""
        print("\n🐍 Checking Python files...")
        
        python_files = list(Path("src").rglob("*.py"))
        
        self.stats['total_python_files'] = len(python_files)
        
        for py_file in python_files[:5]:  # Check first 5 files
            try:
                with open(py_file) as f:
                    content = f.read()
                
                # Check for common issues
                if "# TODO" in content or "# FIXME" in content:
                    self.warnings.append(f"⚠️  TODO/FIXME found in {py_file}")
                
                if "print(" in content and "__main__" not in content:
                    self.warnings.append(f"⚠️  Debug print in {py_file}")
                    
            except Exception as e:
                self.issues.append(f"❌ Can't read {py_file}: {e}")
    
    def check_web_app(self):
        """Check if web app is running and healthy"""
        print("\n🌐 Checking web application...")
        
        try:
            import requests
            base_url = "http://127.0.0.1:5002"
            
            # Try to connect to web app
            try:
                response = requests.get(f"{base_url}/api/health", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.success.append(f"✅ Web app is running (version: {data.get('version', 'unknown')})")
                    self.stats['web_app_status'] = data.get('status', 'unknown')
                    self.stats['web_app_cases'] = data.get('statistics', {}).get('total_cases_available', 0)
                    self.stats['web_app_models'] = data.get('statistics', {}).get('models_supported', 0)
                    
                    # Check critical endpoints
                    critical_endpoints = ['/api/cases', '/api/models', '/api/available_models']
                    for endpoint in critical_endpoints:
                        try:
                            resp = requests.get(f"{base_url}{endpoint}", timeout=1)
                            if resp.status_code == 200:
                                self.success.append(f"✅ Endpoint {endpoint} is working")
                            else:
                                self.warnings.append(f"⚠️  Endpoint {endpoint} returned {resp.status_code}")
                        except:
                            self.warnings.append(f"⚠️  Endpoint {endpoint} is not responding")
                else:
                    self.warnings.append(f"⚠️  Web app returned status {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                self.warnings.append("⚠️  Web app is not running (start with: python web_app.py)")
                self.stats['web_app_status'] = 'not_running'
                
            except Exception as e:
                self.issues.append(f"❌ Web app check failed: {str(e)}")
                
        except ImportError:
            self.warnings.append("⚠️  requests library not available for web app check")
    
    def check_tests(self):
        """Check test coverage and status"""
        print("\n🧪 Checking tests...")
        
        test_files = list(Path("tests").rglob("test_*.py"))
        
        self.stats['total_test_files'] = len(test_files)
        
        # Check if tests import the new features
        for test_file in test_files:
            with open(test_file) as f:
                content = f.read()
            
            # Check for tests of new features
            if "test_llm_manager" in str(test_file):
                if "reasoning" not in content:
                    self.warnings.append(f"⚠️  Test doesn't cover reasoning field: {test_file.name}")
            
            if "test_cache" in str(test_file):
                if "validate_cache" not in content:
                    self.warnings.append(f"⚠️  Test doesn't cover cache validation: {test_file.name}")
    
    def check_cache_integrity(self):
        """Check cache files for issues"""
        print("\n💾 Checking cache integrity...")
        
        cache_dir = Path("cache/responses")
        
        if cache_dir.exists():
            total_cache = 0
            invalid_cache = 0
            
            for cache_file in cache_dir.rglob("*.json"):
                total_cache += 1
                
                # Check file size
                if cache_file.stat().st_size < 1024:
                    invalid_cache += 1
                    self.warnings.append(f"⚠️  Small cache file: {cache_file.name}")
                
                # Check content
                try:
                    with open(cache_file) as f:
                        data = json.load(f)
                    
                    if not data.get('content') and not data.get('reasoning'):
                        invalid_cache += 1
                        self.warnings.append(f"⚠️  Empty response in: {cache_file.name}")
                        
                except Exception:
                    invalid_cache += 1
                    self.warnings.append(f"⚠️  Corrupted cache: {cache_file.name}")
            
            self.stats['total_cache_files'] = total_cache
            self.stats['invalid_cache_files'] = invalid_cache
            
            if invalid_cache > 0:
                self.issues.append(f"❌ Found {invalid_cache} invalid cache files")
            else:
                self.success.append(f"✅ All {total_cache} cache files valid")
    
    def check_reports(self):
        """Check generated reports"""
        print("\n📄 Checking reports...")
        
        reports_dir = Path("reports")
        
        if reports_dir.exists():
            pdf_files = list(reports_dir.glob("*.pdf"))
            json_files = list(reports_dir.glob("*.json"))
            
            self.stats['pdf_reports'] = len(pdf_files)
            self.stats['json_data'] = len(json_files)
            
            # Check for orphaned files
            for json_file in json_files:
                case_id = json_file.stem.split("_")[0]
                matching_pdf = any(case_id in pdf.stem for pdf in pdf_files)
                
                if not matching_pdf and "ensemble_data" in json_file.stem:
                    self.warnings.append(f"⚠️  Orphaned JSON data: {json_file.name}")
    
    def identify_cleanup_candidates(self):
        """Identify files that should be cleaned up"""
        print("\n🧹 Identifying cleanup candidates...")
        
        cleanup_patterns = [
            ("**/*.pyc", "Python bytecode"),
            ("**/__pycache__", "Python cache"),
            ("**/.DS_Store", "macOS metadata"),
            ("**/*.log", "Log files"),
            ("**/.coverage", "Coverage data"),
            ("**/*.bak", "Backup files"),
            ("**/test_results.json", "Test results")
        ]
        
        total_size = 0
        file_count = 0
        
        for pattern, description in cleanup_patterns:
            matches = list(Path(".").rglob(pattern))
            if matches:
                for match in matches:
                    if match.is_file():
                        size = match.stat().st_size
                        total_size += size
                        file_count += 1
                
                self.warnings.append(f"🧹 Can clean {len(matches)} {description} files")
        
        if file_count > 0:
            size_mb = total_size / (1024 * 1024)
            self.stats['cleanup_size_mb'] = f"{size_mb:.2f}"
            self.stats['cleanup_files'] = file_count
    
    def generate_report(self) -> Dict:
        """Generate health check report"""
        
        print("\n" + "=" * 50)
        print("📊 HEALTH CHECK REPORT")
        print("=" * 50)
        
        # Summary
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_success = len(self.success)
        
        print(f"\n✅ Success: {total_success}")
        print(f"⚠️  Warnings: {total_warnings}")
        print(f"❌ Issues: {total_issues}")
        
        # Critical issues
        if self.issues:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in self.issues[:5]:
                print(f"  {issue}")
        
        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings[:5]:
                print(f"  {warning}")
        
        # Statistics
        print("\n📈 STATISTICS:")
        for key, value in self.stats.items():
            print(f"  {key}: {value}")
        
        # Overall health score
        health_score = (total_success / (total_success + total_warnings + total_issues)) * 100
        
        print(f"\n🏥 OVERALL HEALTH SCORE: {health_score:.1f}%")
        
        if health_score >= 80:
            print("   Status: HEALTHY ✅")
        elif health_score >= 60:
            print("   Status: NEEDS ATTENTION ⚠️")
        else:
            print("   Status: NEEDS IMMEDIATE ATTENTION ❌")
        
        return {
            "score": health_score,
            "issues": self.issues,
            "warnings": self.warnings,
            "success": self.success,
            "stats": self.stats
        }

def cleanup_project():
    """Perform automatic cleanup of identified issues"""
    print("\n🧹 PERFORMING CLEANUP...")
    
    cleanup_commands = [
        ("find . -name '*.pyc' -delete", "Python bytecode"),
        ("find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null", "Python cache"),
        ("find . -name '.DS_Store' -delete", "macOS metadata"),
        ("find . -name '*.log' -not -path './backup/*' -delete", "Log files"),
        ("rm -f test_results.json", "Test results"),
        ("rm -rf htmlcov", "Coverage HTML"),
        ("rm -f .coverage", "Coverage data")
    ]
    
    for command, description in cleanup_commands:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Cleaned {description}")
            else:
                print(f"  ⚠️  Issue cleaning {description}")
        except Exception as e:
            print(f"  ❌ Failed to clean {description}: {e}")
    
    # Clean empty directories
    try:
        subprocess.run("find . -type d -empty -delete 2>/dev/null", shell=True)
        print("  ✅ Removed empty directories")
    except:
        pass

if __name__ == "__main__":
    # Run health check
    checker = HealthCheck()
    results = checker.run_all_checks()
    
    # Ask about cleanup
    if results['stats'].get('cleanup_files', 0) > 0:
        print(f"\n🧹 Found {results['stats']['cleanup_files']} files to clean ({results['stats'].get('cleanup_size_mb', '0')} MB)")
        response = input("Would you like to perform automatic cleanup? (y/n): ")
        
        if response.lower() == 'y':
            cleanup_project()
            print("✅ Cleanup complete!")
    
    sys.exit(0 if results['score'] >= 60 else 1)
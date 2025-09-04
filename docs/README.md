# 📚 MEDLEY Documentation Hub

Welcome to the MEDLEY documentation center. This directory contains comprehensive documentation for the Medical AI Ensemble System.

---

## 📋 Documentation Index

### 🏗️ Architecture & Design

| Document | Description |
|----------|-------------|
| [**ORCHESTRATOR_ARCHITECTURE.md**](ORCHESTRATOR_ARCHITECTURE.md) | Complete multi-stage orchestrator system design, including 3-stage pipeline, bias detection, and consensus algorithms |
| [**PROMPT_TEMPLATES.md**](PROMPT_TEMPLATES.md) | All prompts used throughout the system with detailed explanations and examples |
| [**PIPELINE_GENERALITY_ANALYSIS.md**](PIPELINE_GENERALITY_ANALYSIS.md) | Analysis of pipeline flexibility and adaptability for different use cases |
| [**ENSEMBLE_FEATURES.md**](ENSEMBLE_FEATURES.md) | Detailed ensemble system features and capabilities |

### 🚀 Getting Started & Guides

| Document | Description |
|----------|-------------|
| [**HOW_TO_ADD_NEW_CASES.md**](HOW_TO_ADD_NEW_CASES.md) | Step-by-step guide for adding new medical cases to the system |
| [**CHROME_BYPASS_INSTRUCTIONS.md**](CHROME_BYPASS_INSTRUCTIONS.md) | Instructions for bypassing Chrome security for local development |
| [**IMPLEMENTATION_STATUS.md**](IMPLEMENTATION_STATUS.md) | Current implementation status and progress tracking |

### 📊 System Information

| Document | Description |
|----------|-------------|
| [**MEDLEY_ALL_MODELS_LIST.md**](MEDLEY_ALL_MODELS_LIST.md) | Complete list of all 31 AI models with metadata and capabilities |
| [**HEALTH_CHECK_REPORT.md**](HEALTH_CHECK_REPORT.md) | System health monitoring and diagnostic information |
| [**RELEASE_NOTES.md**](RELEASE_NOTES.md) | Version 1.0.0 release notes with features, changes, and roadmap |

### 👥 About

| Document | Description |
|----------|-------------|
| [**AUTHORS.md**](AUTHORS.md) | Project authors and contributors |

### 📁 Archive Folder

The `archive/` subdirectory contains historical documentation and development summaries:
- Fix summaries from development phases
- Case-specific analysis summaries
- Pipeline optimization records
- Model configuration evolution

---

## 🎯 Quick Navigation

### For Developers
1. Start with [ORCHESTRATOR_ARCHITECTURE.md](ORCHESTRATOR_ARCHITECTURE.md) to understand the system
2. Review [PROMPT_TEMPLATES.md](PROMPT_TEMPLATES.md) for prompt engineering
3. Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for current progress

### For Medical Professionals
1. Read [HOW_TO_ADD_NEW_CASES.md](HOW_TO_ADD_NEW_CASES.md) to contribute cases
2. Review [MEDLEY_ALL_MODELS_LIST.md](MEDLEY_ALL_MODELS_LIST.md) to understand model diversity
3. See [ENSEMBLE_FEATURES.md](ENSEMBLE_FEATURES.md) for system capabilities

### For System Administrators
1. Check [HEALTH_CHECK_REPORT.md](HEALTH_CHECK_REPORT.md) for monitoring
2. Review deployment guides in the `deployment/` folder
3. See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version information

---

## 📂 Documentation Structure

```
docs/
├── README.md                           # This file - Documentation hub
├── ORCHESTRATOR_ARCHITECTURE.md        # Core system architecture
├── PROMPT_TEMPLATES.md                 # All system prompts
├── PIPELINE_GENERALITY_ANALYSIS.md     # Pipeline flexibility analysis
├── ENSEMBLE_FEATURES.md                # Ensemble capabilities
├── HOW_TO_ADD_NEW_CASES.md            # Case addition guide
├── MEDLEY_ALL_MODELS_LIST.md          # Complete model listing
├── HEALTH_CHECK_REPORT.md             # System health monitoring
├── IMPLEMENTATION_STATUS.md            # Development progress
├── CHROME_BYPASS_INSTRUCTIONS.md       # Chrome development setup
├── RELEASE_NOTES.md                    # v1.0.0 release information
├── AUTHORS.md                          # Contributors
└── archive/                            # Historical documentation
    ├── FINAL_FIXES_SUMMARY.md         # Final bug fixes
    ├── FIX_SUMMARY.md                  # Development fixes
    ├── PIPELINE_FIXES_SUMMARY.md      # Pipeline improvements
    ├── ANALYSIS_SUMMARY.md            # Analysis records
    ├── CASE_13_*.md                   # Case 13 development
    ├── FINAL_MODEL_LIST_34.md         # Model list evolution
    └── MODEL_CONFIGURATION_SUMMARY.md # Configuration history
```

---

## 🔄 Documentation Standards

### File Naming Convention
- Use UPPERCASE with underscores for main documentation files
- Use descriptive names that clearly indicate content
- Archive old documentation rather than deleting

### Content Guidelines
- Include table of contents for documents >500 lines
- Use clear headings and subheadings
- Include code examples where relevant
- Add diagrams for complex architectures
- Keep technical accuracy while maintaining readability

### Maintenance
- Update documentation with each major feature addition
- Review quarterly for accuracy
- Archive outdated documentation with date stamps
- Maintain version history in git

---

## 📝 Contributing to Documentation

To contribute to MEDLEY documentation:

1. **Create/Update**: Write clear, concise documentation
2. **Review**: Ensure technical accuracy
3. **Format**: Follow markdown best practices
4. **Link**: Update this README if adding new documents
5. **Archive**: Move outdated docs to archive/ folder

---

## 📮 Contact

For documentation questions or contributions:
- **Author**: Farhad Abtahi
- **Email**: farhad.abtahi@ki.se
- **Institution**: SMAILE at Karolinska Institutet
- **Website**: [smile.ki.se](https://smile.ki.se)

---

**Last Updated**: August 12, 2025  
**Version**: 1.0.0
# 📁 MEDLEY Project Structure

## Complete Directory Organization

```
medley/
├── 📄 Core Files (Root)
│   ├── README.md                    # Main project documentation
│   ├── web_app.py                   # Flask web application server
│   ├── web_orchestrator.py          # Web interface orchestrator
│   ├── general_medical_pipeline.py  # Core medical analysis pipeline
│   ├── model_metadata_2025.py       # Model metadata and configuration
│   ├── model_list_2025_updated.py   # Updated model list
│   ├── run_all_cases.py             # Batch case processor
│   ├── requirements.txt             # Python dependencies
│   ├── requirements_web.txt         # Web-specific dependencies
│   ├── setup.py                     # Package setup configuration
│   ├── pyproject.toml              # Modern Python project config
│   ├── pytest.ini                   # Pytest configuration
│   ├── .env.example                 # Environment variables template
│   ├── .gitignore                   # Git ignore patterns
│   ├── .dockerignore               # Docker ignore patterns
│   ├── medley.db                   # SQLite database
│   └── medley_models_config.json   # Model configuration JSON
│
├── 📦 src/medley/                  # Core package code
│   ├── __init__.py                 # Package initialization
│   ├── __main__.py                 # CLI entry point
│   ├── cli.py                      # Command-line interface
│   ├── models/                     # LLM management
│   │   ├── __init__.py
│   │   ├── llm_manager.py          # LLM API manager
│   │   ├── ensemble.py             # Ensemble orchestration
│   │   └── model_config.py         # Model configuration
│   ├── processors/                 # Data processing
│   │   ├── __init__.py
│   │   ├── case_processor.py       # Medical case processing
│   │   ├── response_parser.py      # Response parsing
│   │   ├── cache_manager.py        # Cache management
│   │   └── consensus.py            # Consensus building
│   ├── reporters/                  # Report generation
│   │   ├── __init__.py
│   │   ├── consensus_report.py     # Consensus reports
│   │   ├── enhanced_report.py      # Enhanced reports
│   │   ├── comprehensive_report.py # Comprehensive reports
│   │   └── pdf_generator.py        # PDF generation
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       ├── validators.py           # Input validation
│       ├── logger.py               # Logging utilities
│       └── helpers.py              # Helper functions
│
├── 📚 docs/                        # Documentation
│   ├── README.md                   # Documentation hub
│   ├── ORCHESTRATOR_ARCHITECTURE.md # System architecture
│   ├── PROMPT_TEMPLATES.md         # All system prompts
│   ├── API.md                      # API reference
│   ├── USER_GUIDE.md              # User guide
│   ├── DEVELOPER.md               # Developer guide
│   ├── HOW_TO_ADD_NEW_CASES.md    # Case addition guide
│   ├── MEDLEY_ALL_MODELS_LIST.md  # Model listing
│   ├── ENSEMBLE_FEATURES.md       # Ensemble features
│   ├── PIPELINE_GENERALITY_ANALYSIS.md # Pipeline analysis
│   ├── HEALTH_CHECK_REPORT.md     # Health monitoring
│   ├── IMPLEMENTATION_STATUS.md   # Development status
│   ├── CHROME_BYPASS_INSTRUCTIONS.md # Chrome setup
│   ├── RELEASE_NOTES.md          # Version releases
│   ├── AUTHORS.md                 # Contributors
│   └── archive/                   # Historical docs
│       └── [Legacy summaries and fixes]
│
├── 🧪 tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── run_tests.sh              # Test runner script
│   ├── health_check.py           # System health checks
│   ├── test_web_app.py           # Web app tests
│   ├── test_web_integration.py   # Integration tests
│   ├── unit/                     # Unit tests
│   │   ├── test_all_cases.py
│   │   ├── test_cache_manager.py
│   │   ├── test_case_processor.py
│   │   ├── test_config.py
│   │   ├── test_llm_manager.py
│   │   ├── test_llm_manager_enhanced.py
│   │   └── test_response_parser.py
│   └── integration/              # Integration tests
│       ├── test_end_to_end.py
│       └── test_pipeline_enhanced.py
│
├── 🔧 examples/                   # Example scripts
│   ├── README.md                  # Examples documentation
│   ├── add_new_case.py           # Add case example
│   ├── generate_case_13.py       # Case generation
│   ├── complete_case_13.py       # Case completion
│   ├── finalize_case_13.py       # Case finalization
│   ├── regenerate_case_13_fixed.py # Case regeneration
│   ├── generate_final_report.py  # Report generation
│   ├── query_missing_models_case13.py # Model queries
│   ├── add_missing_models_case13.py # Model addition
│   ├── regenerate_case13_with_34models.py # Full regeneration
│   ├── generate_case_13_quick.py # Quick generation
│   └── run_remaining_cases.sh    # Batch processing
│
├── 🛠 utils/                      # Utility scripts
│   ├── add_horizon_and_free_models.py # Model additions
│   ├── fix_orchestrator_comprehensive_diagnosis.py # Fixes
│   ├── fixed_model_config.py     # Fixed configurations
│   ├── update_model_configuration.py # Config updates
│   ├── updated_model_config.py   # Updated configs
│   └── model_metadata_2025_complete.py # Complete metadata
│
├── 🚀 scripts/                    # Startup scripts
│   ├── start_web.py              # Start web server
│   ├── start_web_https.py        # Start HTTPS server
│   └── run_https.py              # Run with SSL
│
├── 🐳 deployment/                # Deployment files
│   ├── docker-compose.yml        # Docker orchestration
│   ├── Dockerfile                # Container definition
│   ├── cert.pem                  # SSL certificate
│   ├── key.pem                   # SSL private key
│   ├── nginx/                    # Nginx configuration
│   │   ├── nginx.conf            # Main config
│   │   └── conf.d/               # Site configs
│   │       └── medley.conf       # MEDLEY site config
│   ├── scripts/                  # Deployment scripts
│   │   ├── deploy.sh             # Main deployment
│   │   └── setup-ssl.sh         # SSL setup
│   └── certbot/                  # Let's Encrypt
│       ├── www/                  # Webroot
│       └── conf/                 # SSL configs
│
├── 🌐 templates/                  # Web templates
│   ├── base.html                 # Base template
│   ├── index.html                # Landing page
│   ├── explore.html              # Case explorer
│   ├── case_report.html         # Case reports
│   ├── analyze.html              # Analysis page
│   ├── analyze_fixed.html        # Fixed analysis
│   ├── model_performance.html    # Model metrics
│   ├── api_key.html              # API key setup
│   └── components/               # Template components
│       ├── case_card.html        # Case cards
│       ├── model_selector.html   # Model selection
│       └── progress_bar.html     # Progress display
│
├── 🎨 static/                     # Static assets
│   ├── css/                      # Stylesheets
│   │   ├── style.css             # Main styles
│   │   └── material.css          # Material Design
│   ├── js/                       # JavaScript
│   │   ├── main.js               # Main scripts
│   │   ├── analyze.js            # Analysis scripts
│   │   └── socketio.js          # WebSocket client
│   └── images/                   # Images
│       ├── logo.png              # MEDLEY logo
│       └── flags/                # Country flags
│
├── 💾 cache/                      # Cache storage
│   ├── responses/                # Model responses
│   │   └── [JSON response files]
│   ├── orchestrator/             # Orchestrator cache
│   │   └── [Synthesis results]
│   ├── ensembles/                # Ensemble results
│   │   └── [Ensemble data]
│   └── metadata/                 # Metadata cache
│       └── [Model metadata]
│
├── 📄 reports/                    # Generated reports
│   ├── FINAL_*.pdf               # PDF reports
│   ├── *.html                    # HTML reports
│   └── README.md                 # Reports guide
│
├── 🏥 usecases/                  # Medical cases
│   ├── case_001_fmf.txt         # Case 1: FMF
│   ├── case_002_elderly.txt     # Case 2: Elderly
│   ├── case_003_homeless.txt    # Case 3: Homeless
│   ├── case_004_genetic.txt     # Case 4: Genetic
│   ├── case_005_toxin.txt       # Case 5: Toxin
│   ├── case_006_disability.txt  # Case 6: Disability
│   ├── case_007_gender.txt      # Case 7: Gender
│   ├── case_008_rural.txt       # Case 8: Rural
│   ├── case_009_weight.txt      # Case 9: Weight
│   ├── case_010_migration.txt   # Case 10: Migration
│   ├── case_011_ethnic.txt      # Case 11: Ethnic
│   ├── case_012_pediatric.txt   # Case 12: Pediatric
│   ├── case_013_complex_urology.txt # Case 13: Urology
│   └── custom/                   # Custom cases
│       └── [User-submitted cases]
│
├── 🗄 src/database/              # Database modules
│   ├── __init__.py
│   ├── models.py                 # Database models
│   └── migrations/               # DB migrations
│
├── ⚙️ config/                    # Configuration files
│   ├── prompts.yaml              # Prompt templates
│   ├── models.yaml               # Model configs
│   └── pipeline.yaml             # Pipeline settings
│
├── 🗂 backup/                    # Backup files
│   └── temp/                     # Temporary backups
│       ├── cached_models.txt     # Cached model list
│       └── cookies.txt           # Session cookies
│
├── 📊 ensemble_results/          # Ensemble outputs
│   └── [Analysis results]
│
├── 🔒 certs/                     # SSL certificates
│   └── [Certificate files]
│
├── 🗄 flask_session/             # Flask sessions
│   └── [Session files]
│
├── 📈 htmlcov/                   # Coverage reports
│   └── [Coverage HTML files]
│
└── 🗑 tmp/                       # Temporary files
    └── [Temporary data]
```

## Directory Purposes

### Core Directories
- **src/medley/**: Main package containing all core functionality
- **docs/**: Comprehensive documentation for users and developers
- **tests/**: Complete test suite with unit and integration tests
- **templates/**: HTML templates for web interface
- **static/**: CSS, JavaScript, and image assets

### Data Directories
- **cache/**: Stores cached API responses to reduce costs
- **reports/**: Generated PDF and HTML reports
- **usecases/**: Pre-defined medical test cases
- **ensemble_results/**: Stored ensemble analysis results

### Development Directories
- **examples/**: Example scripts showing how to use the system
- **utils/**: Utility scripts for maintenance and configuration
- **scripts/**: Startup and management scripts
- **deployment/**: Docker and production deployment files

### Configuration
- **config/**: YAML configuration files
- **Root config files**: setup.py, requirements.txt, pytest.ini

## File Count Summary
- **Python files in root**: 7 core files
- **Documentation files**: 17 comprehensive guides
- **Test files**: 11 test modules
- **Example scripts**: 12 examples
- **Medical cases**: 13 pre-analyzed cases
- **Total models supported**: 31 AI models

## Key Features
✅ Clean separation of concerns
✅ Comprehensive test coverage
✅ Extensive documentation
✅ Example implementations
✅ Production-ready deployment
✅ Proper caching strategy
✅ Modular architecture

---

**Last Updated**: August 2025
**Maintained by**: SMAILE Team at Karolinska Institutet
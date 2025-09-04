# MEDLEY - Medical AI Ensemble System

![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/medley-ai)
![Docker Image Size](https://img.shields.io/docker/image-size/yourusername/medley-ai)
![Docker Image Version](https://img.shields.io/docker/v/yourusername/medley-ai)

**Multi-Model Medical Diagnostic System with Bias-Aware Analysis**

MEDLEY orchestrates 31 Large Language Models from 6 countries to provide comprehensive, bias-aware medical diagnostic analysis. The system implements concepts from "Embracing Imperfection: A Perspective on Leveraging Bias and Hallucination in Medical AI for Enhanced Human Decision-Making."

## 🚀 Quick Start

### Pull and Run

```bash
# Pull the latest image
docker pull yourusername/medley-ai:latest

# Run MEDLEY web application
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  --name medley-app \
  yourusername/medley-ai:latest

# Access the application at http://localhost:5000
```

### With Docker Compose

```yaml
version: '3.8'
services:
  medley:
    image: yourusername/medley-ai:latest
    ports:
      - "5000:5000"
    environment:
      - OPENROUTER_API_KEY=your_api_key_here
      - USE_FREE_MODELS=true
    volumes:
      - ./reports:/app/reports
      - ./cache:/app/cache
    restart: unless-stopped
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) | - |
| `USE_FREE_MODELS` | Use only free models | `false` |
| `PORT` | Application port | `5000` |
| `DEBUG` | Debug mode | `false` |
| `CACHE_DIR` | Cache directory | `/app/cache` |
| `REPORTS_DIR` | Reports directory | `/app/reports` |

### Volume Mounts

| Container Path | Purpose | Recommended Host Path |
|----------------|---------|----------------------|
| `/app/reports` | Generated PDF reports | `./reports` |
| `/app/cache` | Model response cache | `./cache` |
| `/app/usecases/custom` | Custom medical cases | `./custom-cases` |

## 🏥 Features

- **31 AI Models** from 6 countries providing diverse perspectives
- **Bias-aware analysis** with geographical and cultural attribution
- **Web Interface** with interactive case gallery and real-time analysis
- **PDF Reports** with comprehensive diagnostic analysis
- **ICD-10 Integration** for standardized diagnostic coding
- **Free Model Support** for cost-effective operation

## 📋 Available Tags

- `latest` - Latest stable release
- `v1.0.0`, `v1.1.0`, etc. - Specific version releases
- `develop` - Development branch (unstable)

## 🌐 Web Interface

The MEDLEY web application provides:

### 🏠 Landing Page
- Interactive flow diagram showing ensemble process
- Model gallery with geographic origins
- Educational content about bias reduction

### 📊 Case Gallery  
- 12 pre-analyzed medical cases
- Instant access to cached results
- Filter by medical specialty

### 📄 Report Viewer
- Tabbed interface for different views
- Diagnosis categorization (consensus/alternative/minority)
- ICD-10 code mapping
- Downloadable PDF reports

### 📈 Analytics
- Model performance metrics
- Geographic distribution visualization
- Bias pattern analysis

## 🔬 API Endpoints

- `GET /api/health` - System health check
- `GET /api/cases` - List available cases
- `GET /api/case/{id}/report` - Get case analysis
- `GET /api/case/{id}/pdf` - Download PDF report
- `POST /api/session/set-key` - Set OpenRouter API key

## 💡 Usage Examples

### Basic Web Interface
```bash
docker run -p 5000:5000 -e OPENROUTER_API_KEY=your_key yourusername/medley-ai:latest
```

### With Persistent Storage
```bash
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=your_key \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/cache:/app/cache \
  yourusername/medley-ai:latest
```

### Development Mode
```bash
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=your_key \
  -e DEBUG=true \
  -e USE_FREE_MODELS=true \
  yourusername/medley-ai:latest
```

## 🔒 Security & Privacy

- ✅ API keys via environment variables
- ✅ No patient data logging
- ✅ Hash-based cache naming
- ✅ HTTPS API communication
- ✅ Local processing only

## 📚 Documentation

- **GitHub Repository:** https://github.com/yourusername/medley
- **Research Paper:** [arXiv:2508.21648](https://arxiv.org/abs/2508.21648)
- **Website:** [smile.ki.se](https://smile.ki.se)

## 🏷️ System Requirements

- **Memory:** 2GB+ recommended
- **CPU:** 2+ cores recommended  
- **Storage:** 1GB for application + cache storage
- **Network:** Internet access for AI model APIs

## 🤝 Support

- **Issues:** Report bugs on GitHub
- **Discussions:** GitHub Discussions
- **Contact:** SMAILE Lab at Karolinska Institutet

## 📄 License

MIT License - Educational and research use encouraged

---

**⚠️ Disclaimer:** This system is for research and educational purposes only. Not intended for clinical diagnosis or treatment decisions.

**Developed by:** SMAILE (Stockholm Medical Artificial Intelligence and Learning Environments) at Karolinska Institutet
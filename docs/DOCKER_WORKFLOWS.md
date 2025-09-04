# Docker Workflows Documentation

This document describes the GitHub Actions workflows for building and publishing MEDLEY Docker images.

## 📋 Overview

MEDLEY uses two GitHub Actions workflows for Docker image management:

1. **`docker-build.yml`** - Builds and pushes to GitHub Container Registry (GHCR)
2. **`docker-hub.yml`** - Builds and pushes to Docker Hub

## 🔧 Workflow 1: GitHub Container Registry

### File: `.github/workflows/docker-build.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Push of version tags (`v*`)
- Pull requests to `main`

**Features:**
- ✅ Multi-platform builds (linux/amd64, linux/arm64)
- ✅ Automatic tagging based on branch/tag
- ✅ Build caching for faster builds
- ✅ Security scanning with Trivy
- ✅ Automatic SARIF upload to GitHub Security tab

**Image Location:** `ghcr.io/yourusername/medley`

### Setup Instructions

1. **No additional secrets required** - Uses `GITHUB_TOKEN` automatically

2. **Image will be available at:**
   ```
   ghcr.io/yourusername/medley:latest
   ghcr.io/yourusername/medley:main
   ghcr.io/yourusername/medley:v1.0.0
   ```

3. **Pull command:**
   ```bash
   docker pull ghcr.io/yourusername/medley:latest
   ```

## 🐳 Workflow 2: Docker Hub

### File: `.github/workflows/docker-hub.yml`

**Triggers:**
- Push of version tags (`v*`)
- Manual workflow dispatch

**Features:**
- ✅ Multi-platform builds (linux/amd64, linux/arm64)
- ✅ Automatic README sync to Docker Hub
- ✅ Version-based tagging
- ✅ Manual trigger option

**Image Location:** `yourusername/medley-ai`

### Setup Instructions

1. **Create Docker Hub Account** and repository

2. **Generate Docker Hub Access Token:**
   - Go to Docker Hub → Account Settings → Security
   - Create new access token with Read, Write, Delete permissions

3. **Add GitHub Secrets:**
   ```
   DOCKERHUB_USERNAME: your-dockerhub-username
   DOCKERHUB_TOKEN: your-access-token
   ```

4. **Update workflow file:**
   - Replace `yourusername` with your Docker Hub username
   - Update repository name if different

## 📋 Supported Tags

### GitHub Container Registry (GHCR)
- `latest` - Latest build from main branch
- `main` - Latest build from main branch
- `develop` - Latest build from develop branch
- `v1.0.0` - Specific version releases
- `main-abcd1234` - Branch with short commit SHA

### Docker Hub
- `latest` - Latest version release
- `v1.0.0` - Specific version releases

## 🚀 Usage Examples

### Pull from GitHub Container Registry
```bash
# Latest version
docker pull ghcr.io/yourusername/medley:latest

# Specific version
docker pull ghcr.io/yourusername/medley:v1.0.0

# Development version
docker pull ghcr.io/yourusername/medley:develop
```

### Pull from Docker Hub
```bash
# Latest version
docker pull yourusername/medley-ai:latest

# Specific version  
docker pull yourusername/medley-ai:v1.0.0
```

### Run Container
```bash
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=your_api_key \
  --name medley-app \
  ghcr.io/yourusername/medley:latest
```

## 🔐 Security Features

### Vulnerability Scanning
- **Trivy scanner** runs on all GHCR builds
- Results uploaded to GitHub Security tab
- SARIF format for detailed reporting

### Security Best Practices
- Minimal base image (Python slim)
- Non-root user execution
- No secrets baked into images
- Environment variable configuration

## 📊 Build Information

### Build Context
- **Context:** `./medley` directory
- **Dockerfile:** `./medley/deployment/Dockerfile`
- **Platforms:** linux/amd64, linux/arm64
- **Cache:** GitHub Actions cache enabled

### Image Metadata
```yaml
labels:
  org.opencontainers.image.title: MEDLEY Medical AI Ensemble
  org.opencontainers.image.description: Multi-model medical diagnostic system
  org.opencontainers.image.source: https://github.com/username/repo
  org.opencontainers.image.version: v1.0.0
```

## 🛠️ Troubleshooting

### Common Issues

1. **Build fails with "context not found"**
   - Ensure Dockerfile exists at `./medley/deployment/Dockerfile`
   - Check workflow context path

2. **Docker Hub push fails**
   - Verify `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
   - Check token permissions (Read, Write, Delete)

3. **Multi-platform build fails**
   - ARM64 builds may take longer
   - Check if all dependencies support ARM64

4. **Security scan fails**
   - Review Trivy findings in Security tab
   - Update base image if vulnerabilities found

### Manual Triggers

#### Docker Hub Workflow
```bash
# Via GitHub CLI
gh workflow run docker-hub.yml -f tag=v1.0.1

# Via GitHub Web Interface
Actions → Build and Push to Docker Hub → Run workflow
```

## 📈 Monitoring

### Build Status
- Check Actions tab for build status
- Review build logs for errors
- Monitor security scan results

### Image Registry
- **GHCR:** View packages in repository settings
- **Docker Hub:** Check pulls and statistics

### Performance Metrics
- Build time: ~5-10 minutes
- Image size: ~500-800MB
- Cache hit rate: 80-90% on repeated builds

## 🔄 Maintenance

### Regular Tasks
1. Update base image monthly
2. Review security scan results
3. Clean up old image tags
4. Monitor registry storage usage

### Version Management
1. Use semantic versioning (v1.0.0)
2. Tag releases consistently
3. Update Docker Hub README as needed
4. Maintain changelog

## 📚 Related Documentation

- [Dockerfile Documentation](./DOCKER.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [API Documentation](./api.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

**Next Steps:**
1. Set up Docker Hub account and secrets
2. Customize username in workflows
3. Test with a version tag push
4. Monitor first builds in Actions tab
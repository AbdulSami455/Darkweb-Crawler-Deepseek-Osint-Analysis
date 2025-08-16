# Darkweb Crawler DeepSeek With OSINT Analysis

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.2-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen.svg)](https://github.com/GENAI-RAG)

> **Built on top of [TorCrawl.py](https://github.com/MikeMeliz/TorCrawl.py)** - A powerful Python-based darkweb crawler and OSINT analysis tool that combines anonymous web scraping through the Tor network with advanced AI-powered analysis using OpenRouter's DeepSeek model.

## 🚀 Features

- **🔍 Anonymous Web Scraping**: Built on [TorCrawl.py](https://github.com/MikeMeliz/TorCrawl.py) for secure, untraceable data collection through the Tor network
- **🤖 AI-Powered Analysis**: Leverages OpenRouter's DeepSeek model for intelligent content analysis and threat detection
- **🌐 Onion Site Support**: Native support for .onion domains and clearnet URLs
- **📊 Bulk Search & Analysis**: Search Ahmia search engine and analyze multiple sites simultaneously
- **🔒 Privacy-First**: All connections routed through Tor network for maximum anonymity
- **📈 RESTful API**: FastAPI-based service with comprehensive endpoints
- **🐳 Docker Ready**: Containerized deployment with proper Tor integration
- **📝 Structured Output**: JSON-based analysis results for easy integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  TorCrawl Core   │───▶│   Tor Network   │
│                 │    │  (Vendored)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ DeepSeek AI     │    │  Ahmia Search    │
│ Analysis        │    │  Engine          │
└─────────────────┘    └──────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+**
- **Tor Service** running locally
- **OpenRouter API Key** for DeepSeek model access
- **Docker** (optional, for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Darkweb-Crawler-Deepseek-Osint-Analysis.git
cd Darkweb-Crawler-Deepseek-Osint-Analysis/darkweb-crawler
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY="sk-or-your-api-key-here"

# Optional: Configure Tor settings
export TOR_SOCKS_HOST="127.0.0.1"
export TOR_SOCKS_PORT="9050"
```

### 4. Start Tor Service

#### macOS
```bash
brew install tor
brew services start tor
```

#### Ubuntu/Debian
```bash
sudo apt-get install tor
sudo service tor start
```

#### Windows
Download `tor.exe` and run:
```bash
tor.exe --service install
tor.exe --service start
```

### 5. Run the Application

```bash
# Option A: Use the helper server (recommended)
python server.py

# Option B: Direct uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 🐳 Docker Deployment

### Quick Docker Run

```bash
# Build and run with Docker
docker build -t darkweb-crawler .
docker run -p 8000:8000 -e OPENROUTER_API_KEY="your-key" darkweb-crawler
```

### Docker Compose

```yaml
version: '3.8'
services:
  darkweb-crawler:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - TOR_SOCKS_HOST=host.docker.internal
      - TOR_SOCKS_PORT=9050
    volumes:
      - ./logs:/app/logs
      - ./torcrawl/output:/app/torcrawl/output
```

## 📚 API Endpoints

### Health Check
```bash
GET /healthz
```

### Single URL Analysis
```bash
POST /analyze
Content-Type: application/json

{
  "url": "http://example.onion",
  "depth": 1,
  "prompt": "Custom analysis prompt (optional)"
}
```

### Bulk Search & Analysis
```bash
POST /bulk-search
Content-Type: application/json

{
  "query": "search term",
  "max_sites": 5,
  "depth": 1,
  "days": 7
}
```

## 💡 Usage Examples

### Analyze a Single Onion Site

```bash
curl -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "http://example.onion",
    "depth": 2
  }'
```

### Bulk Search and Analyze

```bash
curl -X POST http://localhost:8000/bulk-search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "marketplace",
    "max_sites": 10,
    "depth": 1,
    "days": 7
  }'
```

### Python Client Example

```python
import requests

# Analyze single site
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "url": "http://example.onion",
        "depth": 1
    }
)
result = response.json()
print(f"Analysis: {result['analysis']}")
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Required | Your OpenRouter API key |
| `TOR_SOCKS_HOST` | `127.0.0.1` | Tor SOCKS5 proxy host |
| `TOR_SOCKS_PORT` | `9050` | Tor SOCKS5 proxy port |
| `HOST` | `0.0.0.0` | API server host |
| `PORT` | `8000` | API server port |
| `RELOAD` | `false` | Enable auto-reload |

### Tor Configuration

The application expects Tor to be running with SOCKS5 proxy on the configured host/port. Ensure your `torrc` includes:

```
SocksPort 9050
DataDirectory /var/lib/tor
```

## 🏗️ Project Structure

```
darkweb-crawler/
├── app/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # Main API endpoints
│   ├── analysis.py        # DeepSeek AI analysis
│   └── ahmia_search.py    # Ahmia search integration
├── torcrawl/              # Vendored TorCrawl.py
│   ├── modules/           # Core crawling modules
│   ├── res/               # YARA rules and resources
│   └── torcrawl.py        # Main TorCrawl script
├── logs/                  # Application logs
├── requirements.txt        # Python dependencies
├── server.py              # Server entry point
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## 🤝 Contributing

We welcome contributions from the open-source community! Here's how you can help:

### 1. Fork the Repository
```bash
git clone https://github.com/yourusername/Darkweb-Crawler-Deepseek-Osint-Analysis.git
cd Darkweb-Crawler-Deepseek-Osint-Analysis
```

### 2. Create a Feature Branch
```bash
git checkout -b feature/amazing-feature
```

### 3. Make Your Changes
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed

### 4. Commit and Push
```bash
git add .
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

### 5. Create a Pull Request
- Provide a clear description of your changes
- Include any relevant issue numbers
- Ensure all tests pass

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
pytest

# Format code
black .

# Lint code
flake8 .
```

## 🐛 Issue Reporting

Found a bug or have a feature request? Please:

1. Check existing issues first
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[MikeMeliz/TorCrawl.py](https://github.com/MikeMeliz/TorCrawl.py)** - The foundation for anonymous web scraping
- **[OpenRouter](https://openrouter.ai/)** - DeepSeek AI model access
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework
- **[Tor Project](https://www.torproject.org/)** - Anonymous communication network

## ⚠️ Disclaimer

This tool is designed for legitimate OSINT research, security testing, and educational purposes only. Users are responsible for:

- Complying with local laws and regulations
- Respecting website terms of service
- Using the tool ethically and responsibly
- Not violating any privacy or security policies

The developers are not responsible for any misuse of this software.

## 📞 Support

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/Darkweb-Crawler-Deepseek-Osint-Analysis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Darkweb-Crawler-Deepseek-Osint-Analysis/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/Darkweb-Crawler-Deepseek-Osint-Analysis/wiki)

---

**⭐ Star this repository if you find it useful!**

**🔗 Built with ❤️ by the open-source community**

# Installation Guide

Complete installation instructions for the KVP Simulator AO Value Enhancement system.

## 📋 **System Requirements**

### **Minimum Requirements**
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for dependencies and cache
- **Network**: Stable internet connection for academic database access

### **Operating Systems**
- ✅ Linux (Ubuntu 18.04+, CentOS 7+, Debian 10+)
- ✅ macOS (10.14+)
- ✅ Windows 10/11 (with WSL2 recommended)

### **Dependencies**
- Python package manager (pip)
- Git (for repository management)
- Optional: Docker (for containerized deployment)

## 🚀 **Installation Methods**

### **Method 1: Direct Installation (Recommended)**

#### **1. Clone or Download Package**
```bash
# If integrating with existing KVP simulator:
cd your-kvp-simulator-project/
mkdir -p enhancements/
cd enhancements/
# Copy the kvp-simulator-enhancement package here

# If standalone installation:
git clone <repository-url> kvp-ao-enhancement
cd kvp-ao-enhancement
```

#### **2. Install Python Dependencies**
```bash
# Install core dependencies
pip install -r requirements.txt

# Install optional enhanced features
pip install pypinyin scholarly orcid-python habanero networkx

# For development and testing
pip install pytest flake8 black pytest-cov
```

#### **3. Verify Installation**
```bash
# Test basic functionality
python scripts/ao_value_demonstration.py

# Test academic database integration
python -c "from src.data_collection.leadership_researcher import LeadershipResearcher; print('✅ Installation successful')"
```

### **Method 2: Virtual Environment Installation**

#### **1. Create Virtual Environment**
```bash
# Create virtual environment
python -m venv kvp-ao-env

# Activate virtual environment
# Linux/macOS:
source kvp-ao-env/bin/activate
# Windows:
kvp-ao-env\Scripts\activate
```

#### **2. Install Dependencies**
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install optional dependencies
pip install pypinyin scholarly orcid-python
```

#### **3. Test Installation**
```bash
python scripts/ao_value_demonstration.py
```

### **Method 3: Docker Installation**

#### **1. Create Dockerfile**
```dockerfile
# Create Dockerfile in project root
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install optional dependencies
RUN pip install --no-cache-dir pypinyin scholarly orcid-python

# Copy application code
COPY . .

# Expose port for web interface (if using)
EXPOSE 8000

# Set default command
CMD ["python", "scripts/ao_value_demonstration.py"]
```

#### **2. Build and Run Container**
```bash
# Build Docker image
docker build -t kvp-ao-enhancement .

# Run container
docker run -it kvp-ao-enhancement

# Run with volume mount for data persistence
docker run -it -v $(pwd)/data:/app/data kvp-ao-enhancement
```

## 🔧 **Configuration Setup**

### **1. Basic Configuration**
```bash
# Copy configuration templates
cp config/research_config.json.example config/research_config.json
cp config/academic_config.json.example config/academic_config.json

# Edit configurations for your environment
nano config/research_config.json
```

### **2. Academic Database Setup**

#### **ORCID Configuration**
```json
{
  "academic_databases": {
    "orcid": {
      "enabled": true,
      "api_base_url": "https://pub.orcid.org/v3.0",
      "rate_limit_seconds": 2.0,
      "timeout_seconds": 15
    }
  }
}
```

#### **Google Scholar Setup**
- No API key required
- Uses web scraping with rate limiting
- Recommended rate limit: 4+ seconds between requests

#### **SSRN Configuration**
```json
{
  "academic_databases": {
    "ssrn": {
      "enabled": true,
      "rate_limit_seconds": 3.0,
      "timeout_seconds": 15
    }
  }
}
```

#### **Web of Science (Optional)**
```json
{
  "academic_databases": {
    "web_of_science": {
      "enabled": false,
      "note": "Requires institutional access or API key",
      "api_key": "YOUR_WOS_API_KEY",
      "api_base_url": "https://api.clarivate.com/apis/wos-starter"
    }
  }
}
```

### **3. Research Target Configuration**
```bash
# Edit research targets
nano config/research_config.json

# Add your specific target organizations and selectors
```

## 📦 **Dependency Details**

### **Core Dependencies**
```txt
requests>=2.28.0          # HTTP requests for web scraping
beautifulsoup4>=4.11.0    # HTML parsing
lxml>=4.9.0              # XML/HTML processing
googletrans==4.0.0rc1    # Text translation
pandas>=1.5.0            # Data manipulation
numpy>=1.21.0            # Numerical computing
```

### **Academic Integration**
```txt
scholarly>=1.7.0         # Google Scholar integration
orcid-python>=0.4.0      # ORCID API wrapper  
habanero>=1.2.0         # Crossref API wrapper
xmltodict>=0.13.0        # XML to dictionary conversion
networkx>=2.8.0          # Network analysis
```

### **Language Processing**
```txt
transliterate>=1.10.2    # Text transliteration
pypinyin>=0.47.0         # Chinese pinyin conversion
python-levenshtein>=0.20.0  # String similarity
fuzzywuzzy>=0.18.0       # Fuzzy string matching
```

### **Optional Enhancement**
```txt
selenium>=4.8.0          # JavaScript-enabled scraping
selenium-wire>=5.1.0     # Network monitoring for Selenium
undetected-chromedriver>=3.5.0  # Anti-detection browser
fake-useragent>=1.4.0    # User agent rotation
```

## 🧪 **Testing Installation**

### **1. Basic Functionality Test**
```python
#!/usr/bin/env python3
"""Test basic installation functionality"""

def test_basic_import():
    try:
        from src.data_collection.leadership_researcher import LeadershipResearcher
        from src.ao_enhancement.ao_value_enhancer import AOValueCalculator
        print("✅ Core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_academic_integration():
    try:
        from src.data_collection.leadership_researcher import AcademicDatabaseIntegrator
        integrator = AcademicDatabaseIntegrator()
        print("✅ Academic database integration ready")
        return True
    except Exception as e:
        print(f"❌ Academic integration error: {e}")
        return False

def test_configuration_loading():
    try:
        import json
        with open('config/research_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration files loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing KVP AO Enhancement Installation")
    print("=" * 50)
    
    tests = [
        test_basic_import,
        test_academic_integration, 
        test_configuration_loading
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Installation verified successfully!")
    else:
        print("⚠️  Some tests failed - check dependencies and configuration")
```

### **2. Academic Database Connectivity Test**
```python
#!/usr/bin/env python3
"""Test academic database connectivity"""

from src.data_collection.leadership_researcher import AcademicDatabaseIntegrator
import time

def test_orcid_connectivity():
    try:
        integrator = AcademicDatabaseIntegrator()
        # Test with a known researcher
        result = integrator.search_orcid("John Smith", "MIT")
        print("✅ ORCID connectivity verified")
        return True
    except Exception as e:
        print(f"⚠️  ORCID connectivity issue: {e}")
        return False

def test_scholar_connectivity():
    try:
        integrator = AcademicDatabaseIntegrator()
        # Test with rate limiting
        time.sleep(5)  # Respect rate limits
        result = integrator.search_google_scholar("John Smith", "MIT")
        print("✅ Google Scholar connectivity verified")
        return True
    except Exception as e:
        print(f"⚠️  Google Scholar connectivity issue: {e}")
        return False

if __name__ == "__main__":
    print("🌐 Testing Academic Database Connectivity")
    print("=" * 50)
    print("Note: These tests make actual API calls and may take time")
    print()
    
    test_orcid_connectivity()
    time.sleep(3)
    test_scholar_connectivity()
```

## 🔒 **Security Configuration**

### **1. Rate Limiting Setup**
```python
# In your research configuration
RATE_LIMITING_CONFIG = {
    'web_scraping': {
        'requests_per_second': 0.33,  # ~3 second delay
        'burst_allowance': 5,
        'respect_robots_txt': True
    },
    'academic_apis': {
        'orcid': {'requests_per_second': 0.5},      # 2 second delay
        'google_scholar': {'requests_per_second': 0.25},  # 4 second delay
        'ssrn': {'requests_per_second': 0.33}       # 3 second delay
    }
}
```

### **2. User Agent Configuration**
```python
USER_AGENT_CONFIG = {
    'web_scraping': 'Mozilla/5.0 (Academic Research Tool) Research/1.0',
    'academic_apis': 'KVP-AO-Enhancement/1.0 (Academic Research; Contact: your-email@institution.edu)'
}
```

### **3. Proxy Setup (Optional)**
```python
# For enhanced privacy or to avoid rate limiting
PROXY_CONFIG = {
    'enabled': False,
    'http_proxy': 'http://proxy-server:port',
    'https_proxy': 'https://proxy-server:port',
    'rotation_enabled': False
}
```

## 🐛 **Troubleshooting**

### **Common Installation Issues**

#### **1. Import Errors**
```bash
# Problem: ModuleNotFoundError
# Solution: Ensure proper installation
pip install --upgrade -r requirements.txt

# Problem: Version conflicts
# Solution: Use fresh virtual environment
python -m venv fresh-env
source fresh-env/bin/activate
pip install -r requirements.txt
```

#### **2. Academic Database Connection Issues**
```bash
# Problem: ORCID API timeouts
# Solution: Increase timeout and reduce rate
# Edit config/academic_config.json:
{
  "orcid": {
    "timeout_seconds": 30,
    "rate_limit_seconds": 5.0
  }
}

# Problem: Google Scholar blocking
# Solution: Increase delays and use rotation
{
  "google_scholar": {
    "rate_limit_seconds": 10.0,
    "max_retries": 3,
    "retry_delay": 30
  }
}
```

#### **3. Language Processing Issues**
```bash
# Problem: Chinese text processing errors
# Solution: Install additional language packages
pip install pypinyin jieba

# Problem: Russian transliteration issues  
# Solution: Install transliteration package
pip install transliterate
```

#### **4. Memory Issues**
```bash
# Problem: High memory usage during processing
# Solution: Reduce concurrent processing
# Edit research configuration:
{
  "processing": {
    "max_concurrent_requests": 1,
    "batch_size": 10,
    "memory_limit_mb": 2048
  }
}
```

### **Performance Optimization**

#### **1. Caching Setup**
```python
CACHE_CONFIG = {
    'enabled': True,
    'cache_directory': './cache/',
    'academic_profile_ttl': 86400,  # 24 hours
    'web_scraping_ttl': 3600,       # 1 hour
    'max_cache_size_mb': 500
}
```

#### **2. Parallel Processing**
```python
PARALLEL_CONFIG = {
    'enabled': False,  # Start with single-threaded
    'max_workers': 2,
    'worker_delay': 10  # Seconds between worker starts
}
```

## 📚 **Next Steps**

After successful installation:

1. **Configure Target Sources**: Edit `config/research_config.json` with your specific target organizations
2. **Test Academic Integration**: Run connectivity tests for available academic databases  
3. **Review Ethical Guidelines**: Read `docs/ethical-guidelines.md` for responsible use
4. **Explore API Reference**: Check `docs/api-reference.md` for detailed usage instructions
5. **Integration Planning**: Review `docs/integration-guide.md` for KVP simulator integration

## 📞 **Support**

For installation issues:
1. Check troubleshooting section above
2. Verify system requirements
3. Test with minimal configuration
4. Review log files in `logs/` directory
5. Consult API documentation for specific errors

Remember: This system is designed for academic research and simulation purposes only. All usage should comply with ethical guidelines and respect academic database terms of service.

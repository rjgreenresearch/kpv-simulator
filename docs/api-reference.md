# API Reference

Complete API documentation for the KVP Simulator AO Value Enhancement system.

## 🏗️ **Core Classes**

### **LeadershipResearcher**

Primary class for collecting and enhancing leadership data through academic cross-referencing.

```python
class LeadershipResearcher:
    """Main research coordination class with academic database integration"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize researcher with configuration options.
        
        Args:
            config (Dict): Configuration dictionary with options:
                - rate_limit (float): Seconds between requests (default: 2.0)
                - respect_robots (bool): Honor robots.txt (default: True)
                - enable_academic_search (bool): Enable academic enhancement (default: True)
                - academic_rate_limit (float): Academic API rate limit (default: 3.0)
                - kvp_assessment_mode (bool): Enable KVP-specific analysis (default: False)
                - opacity_focus (bool): Prioritize opacity reduction (default: False)
        """
```

#### **Methods**

**research_organization(source_config: Dict) → List[LeadershipRecord]**
```python
def research_organization(self, source_config: Dict) -> List[LeadershipRecord]:
    """
    Research leadership for a single organization with academic enhancement.
    
    Args:
        source_config (Dict): Organization configuration containing:
            - name (str): Organization name
            - url (str): Primary URL to scrape
            - language (str): Source language ('zh-CN', 'ru', 'en', etc.)
            - type (str): Organization type ('government', 'military', 'academic')
            - selectors (Dict): CSS selectors for data extraction
            - additional_urls (List[str], optional): Additional URLs to process
            - opacity_level (str, optional): Expected opacity level
    
    Returns:
        List[LeadershipRecord]: Enhanced leadership records with academic profiles
    """
```

**assess_kvp_target_ao_values(include_prioritization: bool = True) → Dict**
```python
def assess_kvp_target_ao_values(self, include_prioritization: bool = True) -> Dict:
    """
    Assess AO values for KVP targets with opacity reduction focus.
    
    Args:
        include_prioritization (bool): Include full target prioritization analysis
    
    Returns:
        Dict: Assessment results containing:
            - assessment_type (str): Type of assessment performed
            - total_targets (int): Number of targets assessed
            - target_assessments (List[Dict]): Individual target assessments
            - summary_metrics (Dict): Aggregate metrics and statistics
    """
```

**generate_kvp_dataset(filename: str = None) → None**
```python
def generate_kvp_dataset(self, filename: str = None) -> None:
    """
    Generate KVP simulator compatible dataset with academic enhancement.
    
    Args:
        filename (str, optional): Output filename. Auto-generated if None.
    
    Outputs:
        JSON file containing:
            - dataset_info: Metadata and statistics
            - entities: Enhanced KVP entities with academic profiles
            - network_analysis: Academic collaboration networks
    """
```

**export_kvp_assessment_report(filename: str = None) → str**
```python
def export_kvp_assessment_report(self, filename: str = None) -> str:
    """
    Export comprehensive KVP target assessment report focused on AO value.
    
    Args:
        filename (str, optional): Output filename. Auto-generated if None.
    
    Returns:
        str: Path to generated report file
        
    Outputs:
        Comprehensive JSON report containing:
            - Executive summary with key metrics
            - Methodology overview and validation
            - Target assessments with prioritization
            - Network analysis and exploitation opportunities
            - Actionable recommendations for operational use
    """
```

---

### **AOValueCalculator**

Core class for calculating Assessment & Operations value and measuring opacity reduction.

```python
class AOValueCalculator:
    """Calculate and enhance AO value for KVP targets through opacity reduction"""
    
    def __init__(self):
        """Initialize with dual-use research keywords and strategic position weights."""
```

#### **Methods**

**assess_baseline_opacity(record: LeadershipRecord) → OpacityIndicator**
```python
def assess_baseline_opacity(self, record: LeadershipRecord) -> OpacityIndicator:
    """
    Assess initial opacity before academic enhancement.
    
    Args:
        record (LeadershipRecord): Leadership record to assess
    
    Returns:
        OpacityIndicator: Opacity assessment containing:
            - limited_public_bio (bool): Limited biographical information
            - unclear_educational_background (bool): Missing education data
            - missing_career_progression (bool): Unclear career history
            - unknown_technical_expertise (bool): No technical background
            - isolated_from_international_networks (bool): Limited connections
            - compartmentalized_role (bool): Security-sensitive position
            - opacity_score (float): Overall opacity score (0.0-1.0)
    """
```

**calculate_ao_value(record: LeadershipRecord, opacity_indicator: OpacityIndicator) → AOValueMetrics**
```python
def calculate_ao_value(self, record: LeadershipRecord, opacity_indicator: OpacityIndicator) -> AOValueMetrics:
    """
    Calculate comprehensive AO value for a KVP target.
    
    Args:
        record (LeadershipRecord): Enhanced leadership record
        opacity_indicator (OpacityIndicator): Opacity assessment
    
    Returns:
        AOValueMetrics: AO value assessment containing:
            - strategic_importance (float): Position authority and decision-making power
            - technical_capability (float): Scientific/technical expertise
            - network_centrality (float): Connections and influence
            - intelligence_accessibility (float): Information availability
            - operational_predictability (float): Behavioral modeling potential
            - dual_use_potential (float): Strategic research applications
            - overall_ao_value (float): Weighted composite score
    """
```

**reduce_opacity_through_academic_cross_reference(record: LeadershipRecord, enhanced_record: LeadershipRecord) → OpacityReductionResult**
```python
def reduce_opacity_through_academic_cross_reference(self, record: LeadershipRecord, enhanced_record: LeadershipRecord) -> OpacityReductionResult:
    """
    Calculate opacity reduction achieved through academic cross-referencing.
    
    Args:
        record (LeadershipRecord): Original record before enhancement
        enhanced_record (LeadershipRecord): Record after academic enhancement
    
    Returns:
        OpacityReductionResult: Reduction analysis containing:
            - original_opacity_score (float): Baseline opacity
            - enhanced_opacity_score (float): Post-enhancement opacity
            - opacity_reduction_percentage (float): Percentage improvement
            - key_discoveries (List[str]): Major information discoveries
            - validated_credentials (List[str]): Verified educational background
            - technical_expertise_revealed (List[str]): Technical capabilities identified
            - network_connections_discovered (List[str]): Professional networks mapped
            - dual_use_research_identified (List[str]): Strategic research applications
    """
```

---

### **KVPTargetPrioritizer**

Class for prioritizing KVP targets based on enhanced AO values and opacity reduction.

```python
class KVPTargetPrioritizer:
    """Prioritize KVP targets based on AO value and opacity reduction potential"""
    
    def __init__(self):
        """Initialize with AO value calculator."""
```

#### **Methods**

**prioritize_targets(records: List[LeadershipRecord], enhanced_records: List[LeadershipRecord]) → List[Dict]**
```python
def prioritize_targets(self, records: List[LeadershipRecord], enhanced_records: List[LeadershipRecord]) -> List[Dict]:
    """
    Prioritize targets based on enhanced AO value.
    
    Args:
        records (List[LeadershipRecord]): Original records before enhancement
        enhanced_records (List[LeadershipRecord]): Records after academic enhancement
    
    Returns:
        List[Dict]: Prioritized target assessments, each containing:
            - target_id (str): Unique target identifier
            - name (str): Target name
            - position (str): Official title/position
            - organization (str): Parent organization
            - original_ao_value (float): AO value before enhancement
            - enhanced_ao_value (float): AO value after enhancement
            - ao_value_improvement (float): Improvement delta
            - opacity_reduction_percentage (float): Opacity reduction achieved
            - strategic_importance (float): Position-based importance
            - technical_capability (float): Academic/technical expertise
            - dual_use_potential (float): Strategic research applications
            - intelligence_accessibility (float): Information availability
            - priority_score (float): Overall priority ranking score
            - key_discoveries (List[str]): Major information discoveries
            - assessment_confidence (float): Data quality confidence
    """
```

**generate_target_assessment_report(assessments: List[Dict], filename: str = None) → str**
```python
def generate_target_assessment_report(self, assessments: List[Dict], filename: str = None) -> str:
    """
    Generate comprehensive target assessment report.
    
    Args:
        assessments (List[Dict]): Target assessment results
        filename (str, optional): Output filename
    
    Returns:
        str: Path to generated report file
    """
```

---

### **AcademicDatabaseIntegrator**

Class for integrating with academic databases to reduce target opacity.

```python
class AcademicDatabaseIntegrator:
    """Integrates with academic databases for educational and research history"""
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Initialize with rate limiting configuration.
        
        Args:
            rate_limit (float): Seconds between API requests
        """
```

#### **Methods**

**search_orcid(name: str, affiliation: str = "") → Optional[Dict]**
```python
def search_orcid(self, name: str, affiliation: str = "") -> Optional[Dict]:
    """
    Search ORCID database for researcher profile.
    
    Args:
        name (str): Researcher name
        affiliation (str, optional): Institutional affiliation
    
    Returns:
        Optional[Dict]: ORCID profile data or None if not found
    """
```

**search_google_scholar(name: str, affiliation: str = "") → Optional[Dict]**
```python
def search_google_scholar(self, name: str, affiliation: str = "") -> Optional[Dict]:
    """
    Search Google Scholar for researcher profile.
    
    Args:
        name (str): Researcher name
        affiliation (str, optional): Institutional affiliation
    
    Returns:
        Optional[Dict]: Scholar profile data or None if not found
    """
```

**search_ssrn(name: str, affiliation: str = "") → Optional[Dict]**
```python
def search_ssrn(self, name: str, affiliation: str = "") → Optional[Dict]:
    """
    Search SSRN for author publications and profile.
    
    Args:
        name (str): Author name
        affiliation (str, optional): Institutional affiliation
    
    Returns:
        Optional[Dict]: SSRN profile data or None if not found
    """
```

**cross_reference_academic_profile(name: str, affiliation: str = "") → AcademicRecord**
```python
def cross_reference_academic_profile(self, name: str, affiliation: str = "") -> AcademicRecord:
    """
    Cross-reference multiple academic databases for comprehensive profile.
    
    Args:
        name (str): Individual name
        affiliation (str, optional): Institutional affiliation hint
    
    Returns:
        AcademicRecord: Comprehensive academic profile containing:
            - orcid_id (str): ORCID identifier if found
            - h_index (int): Citation h-index
            - citation_count (int): Total citation count
            - publication_count (int): Number of publications
            - education (List[str]): Educational background
            - affiliations (List[str]): Institutional affiliations
            - research_areas (List[str]): Research focus areas
            - notable_publications (List[str]): Key publications
            - coauthors (List[str]): Academic collaborators
            - awards (List[str]): Academic honors
    """
```

---

## 📊 **Data Structures**

### **LeadershipRecord**

```python
@dataclass
class LeadershipRecord:
    """Data class for leadership information"""
    name: str                                    # Original name
    romanized_name: Optional[str] = None         # Romanized version for non-Latin scripts
    title: str = ""                              # Official title/position
    organization: str = ""                       # Parent organization
    role_type: str = "leadership"               # Role category
    age: Optional[int] = None                   # Age if available
    years_in_position: Optional[int] = None     # Tenure in current role
    salary: Optional[str] = None                # Compensation if public
    biography: str = ""                         # Biographical information
    department: str = ""                        # Specific department/ministry
    source_url: str = ""                        # Data source URL
    collection_date: str = ""                   # Collection timestamp
    confidence: float = 0.75                    # Data quality score
    # Academic enhancement fields
    academic_profile: Optional[AcademicRecord] = None  # Academic database profile
    education_verified: bool = False                   # Education verification status
    research_background: Optional[str] = None          # Research summary
```

### **AcademicRecord**

```python
@dataclass
class AcademicRecord:
    """Academic publication and education information"""
    orcid_id: Optional[str] = None                      # ORCID identifier
    h_index: Optional[int] = None                       # Citation h-index
    citation_count: Optional[int] = None                # Total citations
    publication_count: Optional[int] = None             # Number of publications
    education: List[str] = field(default_factory=list) # Educational background
    affiliations: List[str] = field(default_factory=list)      # Academic positions
    research_areas: List[str] = field(default_factory=list)    # Research focus areas
    notable_publications: List[str] = field(default_factory=list)  # Key papers
    coauthors: List[str] = field(default_factory=list)         # Collaborators
    awards: List[str] = field(default_factory=list)            # Academic honors
```

### **OpacityIndicator**

```python
@dataclass
class OpacityIndicator:
    """Indicators of information opacity for a target"""
    limited_public_bio: bool = False                    # Limited biographical data
    unclear_educational_background: bool = False        # Missing education info
    missing_career_progression: bool = False            # Unclear career history
    unknown_technical_expertise: bool = False           # No technical background
    isolated_from_international_networks: bool = False  # Limited connections
    compartmentalized_role: bool = False                # Security-sensitive role
    recent_position_change: bool = False                # Recent role transition
    opacity_score: float = 0.0                         # Overall opacity (0.0-1.0)
```

### **AOValueMetrics**

```python
@dataclass
class AOValueMetrics:
    """Area of Operations value metrics for KVP targets"""
    strategic_importance: float = 0.0      # Position authority and decision-making power
    technical_capability: float = 0.0      # Scientific/technical expertise and access
    network_centrality: float = 0.0        # Connections and influence within networks
    intelligence_accessibility: float = 0.0 # How much we can learn about them
    operational_predictability: float = 0.0 # How well we can model their behavior
    dual_use_potential: float = 0.0        # Academic research applicable to military/strategic purposes
    overall_ao_value: float = 0.0          # Weighted composite AO value
```

---

## 🔧 **Configuration Options**

### **Research Configuration**

```python
research_config = {
    # Basic settings
    'rate_limit': 3.0,                      # Seconds between requests
    'respect_robots': True,                 # Honor robots.txt files
    'max_pages_per_source': 5,             # Limit pages per organization
    'timeout_seconds': 15,                 # Request timeout
    
    # Academic enhancement
    'enable_academic_search': True,        # Enable academic database integration
    'academic_rate_limit': 4.0,           # Academic API rate limit
    'cross_reference_education': True,     # Verify educational backgrounds
    
    # KVP-specific options
    'kvp_assessment_mode': True,           # Enable KVP target analysis
    'opacity_focus': True,                 # Prioritize opacity reduction
    'dual_use_detection': True,           # Identify strategic research
    
    # Output options
    'output_formats': ['json', 'csv'],     # Export formats
    'include_network_analysis': True,      # Generate network data
    'confidence_scoring': True             # Calculate confidence scores
}
```

### **Academic Database Configuration**

```python
academic_config = {
    'orcid': {
        'enabled': True,
        'api_base_url': 'https://pub.orcid.org/v3.0',
        'rate_limit_seconds': 2.0,
        'timeout_seconds': 15
    },
    'google_scholar': {
        'enabled': True,
        'rate_limit_seconds': 4.0,
        'timeout_seconds': 20,
        'max_retries': 3
    },
    'ssrn': {
        'enabled': True,
        'rate_limit_seconds': 3.0,
        'timeout_seconds': 15
    },
    'web_of_science': {
        'enabled': False,  # Requires API key
        'api_key': 'YOUR_WOS_API_KEY',
        'rate_limit_seconds': 1.0
    }
}
```

---

## 🚀 **Usage Examples**

### **Basic Leadership Research**

```python
from src.data_collection.leadership_researcher import LeadershipResearcher

# Initialize researcher
researcher = LeadershipResearcher({
    'enable_academic_search': True,
    'kvp_assessment_mode': True
})

# Define target organization
source_config = {
    'name': 'Chinese Ministry of Defense',
    'url': 'http://eng.mod.gov.cn/',
    'language': 'zh-CN',
    'type': 'military',
    'selectors': {
        'leaderList': '.leadership-section',
        'name': '.commander-name',
        'title': '.rank, .position'
    }
}

# Research and collect enhanced data
records = researcher.research_organization(source_config)
print(f"Collected {len(records)} enhanced leadership records")
```

### **AO Value Assessment**

```python
from src.ao_enhancement.ao_value_enhancer import KVPTargetPrioritizer

# Initialize prioritizer
prioritizer = KVPTargetPrioritizer()

# Create baseline records (simulate pre-enhancement)
baseline_records = create_baseline_records(enhanced_records)

# Prioritize targets by AO value
assessments = prioritizer.prioritize_targets(baseline_records, enhanced_records)

# Display top priority targets
for assessment in assessments[:5]:
    print(f"Target: {assessment['name']}")
    print(f"  Priority Score: {assessment['priority_score']:.3f}")
    print(f"  AO Value Improvement: +{assessment['ao_value_improvement']:.3f}")
    print(f"  Opacity Reduction: {assessment['opacity_reduction_percentage']:.1f}%")
```

### **Academic Profile Cross-Referencing**

```python
from src.data_collection.leadership_researcher import LeadershipResearcher

researcher = LeadershipResearcher({'enable_academic_search': True})
integrator = researcher.academic_integrator

# Cross-reference academic databases
academic_profile = integrator.cross_reference_academic_profile(
    name="Zhang Wei",
    affiliation="Beijing University of Aeronautics"
)

if academic_profile:
    print(f"ORCID: {academic_profile.orcid_id}")
    print(f"H-index: {academic_profile.h_index}")
    print(f"Citations: {academic_profile.citation_count}")
    print(f"Education: {academic_profile.education}")
    print(f"Research Areas: {academic_profile.research_areas}")
```

This API reference provides complete documentation for integrating and using the AO value enhancement system with your KVP simulator.

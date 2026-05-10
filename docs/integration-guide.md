# KVP Simulator Integration Guide

This guide explains how to integrate the AO Value Enhancement system with your existing KVP simulator framework.

## 🏗️ **Integration Architecture**

### **Data Flow**
```
Academic Sources → Data Collection → AO Enhancement → KVP Simulator
     ↓                  ↓               ↓              ↓
ORCID, Scholar     Leadership      Opacity         Enhanced
SSRN, arXiv        Researcher      Reduction       Entities
```

### **Integration Points**
1. **Entity Creation**: Enhanced leadership profiles → KVP entities
2. **Network Modeling**: Academic collaborations → Simulation relationships
3. **Behavioral Parameters**: Research patterns → Simulation behaviors
4. **Confidence Scoring**: Data quality → Simulation uncertainty

## 📁 **File Integration**

### **Step 1: Copy Files to KVP Simulator**
```bash
# From your kvp-simulator repository root:
mkdir -p src/data-collection src/ao-enhancement src/frontend/components config

# Copy the enhancement files:
cp kvp-simulator-enhancement/src/data-collection/* src/data-collection/
cp kvp-simulator-enhancement/src/ao-enhancement/* src/ao-enhancement/
cp kvp-simulator-enhancement/src/frontend/components/* src/frontend/components/
cp kvp-simulator-enhancement/config/* config/
cp kvp-simulator-enhancement/requirements.txt requirements-enhancement.txt
```

### **Step 2: Install Dependencies**
```bash
# Install additional Python dependencies
pip install -r requirements-enhancement.txt

# Install optional enhanced features
pip install pypinyin scholarly orcid-python
```

### **Step 3: Configure Academic Databases**
```python
# config/academic_settings.py
ACADEMIC_CONFIG = {
    'orcid': {
        'enabled': True,
        'api_base_url': 'https://pub.orcid.org/v3.0',
        'rate_limit': 2.0
    },
    'google_scholar': {
        'enabled': True,
        'rate_limit': 4.0,
        'timeout': 20
    },
    'ssrn': {
        'enabled': True,
        'rate_limit': 3.0
    }
}
```

## 🔌 **Entity Enhancement Integration**

### **Enhance Existing Entity Creation**
```python
# In your existing KVP entity creation pipeline:

from src.data_collection.leadership_researcher import LeadershipResearcher
from src.ao_enhancement.ao_value_enhancer import AOValueCalculator

class EnhancedKVPEntityFactory:
    def __init__(self):
        self.researcher = LeadershipResearcher({
            'enable_academic_search': True,
            'kvp_assessment_mode': True
        })
        self.ao_calculator = AOValueCalculator()
    
    def create_enhanced_entity(self, basic_entity_data):
        """Enhance basic entity data with academic cross-referencing"""
        
        # Original KVP entity creation
        entity = self.create_basic_kvp_entity(basic_entity_data)
        
        # Academic enhancement
        academic_profile = self.researcher.academic_integrator.cross_reference_academic_profile(
            entity.name, 
            entity.organization
        )
        
        if academic_profile:
            # Calculate enhanced AO value
            opacity_indicator = self.ao_calculator.assess_baseline_opacity(entity)
            ao_metrics = self.ao_calculator.calculate_ao_value(entity, opacity_indicator)
            
            # Enhance entity with academic data
            entity.attributes.update({
                'verified_education': academic_profile.education,
                'research_areas': academic_profile.research_areas,
                'h_index': academic_profile.h_index,
                'citation_count': academic_profile.citation_count,
                'academic_collaborators': academic_profile.coauthors,
                'dual_use_research': self._identify_dual_use_research(academic_profile),
                'ao_value': ao_metrics.overall_ao_value,
                'influence_score': self._calculate_influence_score(academic_profile),
                'assessment_confidence': entity.confidence * 1.2  # Academic verification bonus
            })
            
            # Add academic relationships
            entity.relationships.update({
                'academic_affiliations': academic_profile.affiliations,
                'research_collaborators': academic_profile.coauthors[:10],
                'institutional_network': self._map_institutional_network(academic_profile)
            })
        
        return entity
```

### **Network Enhancement Integration**
```python
# Enhance your network modeling with academic relationships

class EnhancedNetworkBuilder:
    def __init__(self, kvp_entities):
        self.entities = kvp_entities
        self.academic_networks = {}
    
    def build_enhanced_network(self):
        """Build network with academic relationship overlays"""
        
        # Start with existing KVP relationships
        network = self.build_basic_kvp_network()
        
        # Add academic collaboration edges
        for entity in self.entities:
            if hasattr(entity, 'academic_collaborators'):
                for collaborator in entity.academic_collaborators:
                    # Find collaborator in entity set
                    collab_entity = self._find_entity_by_name(collaborator)
                    if collab_entity:
                        network.add_edge(
                            entity.id, 
                            collab_entity.id,
                            relationship_type='academic_collaboration',
                            strength=self._calculate_collaboration_strength(entity, collab_entity),
                            domain='research_network'
                        )
        
        # Add institutional affiliation edges
        institutions = self._extract_institutions()
        for institution in institutions:
            affiliated_entities = self._find_entities_by_institution(institution)
            for entity1, entity2 in combinations(affiliated_entities, 2):
                network.add_edge(
                    entity1.id,
                    entity2.id, 
                    relationship_type='institutional_connection',
                    strength=0.6,
                    domain='institutional_network'
                )
        
        return network
```

## 🎯 **Simulation Behavior Integration**

### **Academic-Informed Behavior Models**
```python
# Enhance simulation behaviors with academic insights

class AcademicInformedBehaviorModel:
    def __init__(self, entity):
        self.entity = entity
        self.academic_profile = getattr(entity, 'academic_profile', None)
    
    def predict_decision_behavior(self, scenario):
        """Predict behavior based on academic background"""
        
        base_behavior = self.calculate_base_behavior(scenario)
        
        if self.academic_profile:
            # Academic background influences decision-making patterns
            academic_modifiers = {
                'risk_tolerance': self._calculate_academic_risk_tolerance(),
                'innovation_preference': self._calculate_innovation_preference(),
                'collaboration_tendency': self._calculate_collaboration_tendency(),
                'evidence_dependency': self._calculate_evidence_dependency()
            }
            
            # Apply academic modifiers to behavior
            enhanced_behavior = self._apply_academic_modifiers(
                base_behavior, 
                academic_modifiers
            )
            
            return enhanced_behavior
        
        return base_behavior
    
    def _calculate_academic_risk_tolerance(self):
        """Calculate risk tolerance based on research background"""
        if not self.academic_profile:
            return 0.5
        
        # Higher h-index often correlates with established, lower-risk approaches
        h_index_factor = min(1.0, self.academic_profile.h_index / 50.0)
        risk_tolerance = 0.7 - (h_index_factor * 0.3)  # More established = more risk-averse
        
        # Research areas influence risk tolerance
        high_risk_areas = ['quantum computing', 'artificial intelligence', 'biotechnology']
        if any(area in ' '.join(self.academic_profile.research_areas).lower() 
               for area in high_risk_areas):
            risk_tolerance += 0.2
        
        return max(0.1, min(0.9, risk_tolerance))
```

### **Research-Based Technology Prediction**
```python
# Use academic profiles to predict technology development

class TechnologyDevelopmentPredictor:
    def __init__(self, entities):
        self.entities = entities
        self.research_trends = self._analyze_research_trends()
    
    def predict_technology_priorities(self, organization):
        """Predict technology development based on leadership research backgrounds"""
        
        org_leaders = [e for e in self.entities if e.organization == organization]
        
        # Aggregate research areas of leadership
        research_areas = defaultdict(int)
        citation_weights = {}
        
        for leader in org_leaders:
            if hasattr(leader, 'academic_profile') and leader.academic_profile:
                for area in leader.academic_profile.research_areas:
                    weight = 1 + (leader.academic_profile.citation_count or 0) / 1000
                    research_areas[area] += weight
                    citation_weights[area] = max(
                        citation_weights.get(area, 0),
                        leader.academic_profile.citation_count or 0
                    )
        
        # Prioritize by research strength and strategic importance
        strategic_areas = {
            'quantum computing': 0.9,
            'artificial intelligence': 0.8, 
            'cybersecurity': 0.8,
            'hypersonic technology': 0.9,
            'semiconductors': 0.8,
            'biotechnology': 0.7
        }
        
        priorities = {}
        for area, count in research_areas.items():
            strategic_weight = strategic_areas.get(area.lower(), 0.5)
            citation_factor = min(2.0, citation_weights[area] / 500)
            priorities[area] = count * strategic_weight * citation_factor
        
        return sorted(priorities.items(), key=lambda x: x[1], reverse=True)
```

## 📊 **Simulation Parameter Enhancement**

### **Confidence-Weighted Parameters**
```python
# Use academic verification to weight simulation parameters

class ConfidenceWeightedSimulation:
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.8,    # Academic profile verified with multiple sources
            'medium': 0.6,  # Academic profile found with single source
            'low': 0.4,     # No academic verification, government source only
            'minimal': 0.2  # Limited information, high opacity
        }
    
    def apply_confidence_weighting(self, simulation_parameters, entities):
        """Apply confidence-based weighting to simulation parameters"""
        
        weighted_params = {}
        
        for param_name, base_value in simulation_parameters.items():
            confidence_weights = []
            
            for entity in entities:
                if hasattr(entity, 'assessment_confidence'):
                    confidence_weights.append(entity.assessment_confidence)
                else:
                    confidence_weights.append(0.5)  # Default medium confidence
            
            avg_confidence = sum(confidence_weights) / len(confidence_weights)
            
            # Apply confidence weighting
            if avg_confidence >= self.confidence_thresholds['high']:
                weighted_params[param_name] = base_value  # Full confidence
            elif avg_confidence >= self.confidence_thresholds['medium']:
                weighted_params[param_name] = base_value * 0.9  # High confidence
            elif avg_confidence >= self.confidence_thresholds['low']:
                weighted_params[param_name] = base_value * 0.7  # Medium confidence
            else:
                weighted_params[param_name] = base_value * 0.5  # Low confidence
        
        return weighted_params
```

## 🚀 **Example Integration Workflow**

### **Complete Integration Example**
```python
#!/usr/bin/env python3
"""
Complete KVP Simulator integration example
"""

from src.data_collection.leadership_researcher import LeadershipResearcher
from src.ao_enhancement.ao_value_enhancer import KVPTargetPrioritizer
from your_kvp_simulator.core import KVPSimulator  # Your existing simulator

def enhanced_kvp_simulation_pipeline():
    """Run enhanced KVP simulation with AO value improvements"""
    
    # Step 1: Collect enhanced leadership data
    researcher = LeadershipResearcher({
        'enable_academic_search': True,
        'kvp_assessment_mode': True,
        'opacity_focus': True
    })
    
    # Target high-opacity organizations
    target_orgs = [
        'Chinese Ministry of Defense',
        'Russian Federation Government', 
        'Iranian Defense Ministry'
    ]
    
    enhanced_entities = []
    for org_config in load_target_configurations(target_orgs):
        records = researcher.research_organization(org_config)
        enhanced_entities.extend(records)
    
    # Step 2: Calculate AO values and prioritize
    prioritizer = KVPTargetPrioritizer()
    baseline_records = create_baseline_records(enhanced_entities)
    target_assessments = prioritizer.prioritize_targets(baseline_records, enhanced_entities)
    
    # Step 3: Create enhanced KVP entities
    kvp_entities = []
    for assessment in target_assessments:
        entity = create_enhanced_kvp_entity(assessment)
        kvp_entities.append(entity)
    
    # Step 4: Build enhanced simulation network
    network = build_enhanced_network(kvp_entities)
    
    # Step 5: Configure simulation with enhanced parameters
    simulation_config = {
        'entities': kvp_entities,
        'network': network,
        'behavior_models': create_academic_informed_behaviors(kvp_entities),
        'confidence_weighting': True,
        'technology_prediction': True
    }
    
    # Step 6: Run enhanced simulation
    simulator = KVPSimulator(simulation_config)
    results = simulator.run_simulation(
        scenarios=['technology_competition', 'alliance_formation', 'crisis_response']
    )
    
    # Step 7: Analyze results with AO value context
    analysis = analyze_results_with_ao_context(results, target_assessments)
    
    return {
        'simulation_results': results,
        'ao_value_analysis': analysis,
        'opacity_reduction_metrics': calculate_opacity_metrics(enhanced_entities),
        'enhanced_entities': kvp_entities
    }

if __name__ == "__main__":
    results = enhanced_kvp_simulation_pipeline()
    print(f"Enhanced KVP simulation complete with {len(results['enhanced_entities'])} entities")
    print(f"Average opacity reduction: {results['opacity_reduction_metrics']['average_reduction']:.1f}%")
```

## 📋 **Testing & Validation**

### **Integration Tests**
```python
# tests/test_ao_integration.py

import unittest
from src.ao_enhancement.ao_value_enhancer import AOValueCalculator

class TestAOIntegration(unittest.TestCase):
    def test_academic_enhancement(self):
        """Test academic enhancement integration"""
        # Test academic profile cross-referencing
        # Test AO value calculation
        # Test opacity reduction measurement
        
    def test_kvp_entity_creation(self):
        """Test enhanced KVP entity creation"""
        # Test entity enhancement with academic data
        # Test confidence scoring integration
        # Test relationship mapping
        
    def test_simulation_parameter_weighting(self):
        """Test confidence-weighted simulation parameters"""
        # Test parameter weighting based on assessment confidence
        # Test behavior model integration
        # Test network enhancement
```

### **Validation Metrics**
- **Entity Enhancement Rate**: Percentage of entities successfully enhanced with academic data
- **Opacity Reduction**: Average reduction in opacity scores across target population
- **AO Value Improvement**: Average increase in AO values after enhancement
- **Network Discovery**: Number of new relationships discovered through academic cross-referencing
- **Confidence Improvement**: Average increase in assessment confidence scores

## 🔧 **Configuration Management**

### **Environment Configuration**
```python
# config/integration_settings.py

INTEGRATION_CONFIG = {
    'academic_enhancement': {
        'enabled': True,
        'timeout_seconds': 30,
        'retry_attempts': 3,
        'cache_results': True
    },
    'ao_calculation': {
        'enabled': True,
        'include_network_analysis': True,
        'dual_use_detection': True
    },
    'kvp_integration': {
        'confidence_weighting': True,
        'behavior_enhancement': True,
        'network_overlay': True
    }
}
```

This integration guide provides the framework for incorporating the AO value enhancement system into your existing KVP simulator, improving simulation fidelity through reduced opacity and enhanced entity modeling.

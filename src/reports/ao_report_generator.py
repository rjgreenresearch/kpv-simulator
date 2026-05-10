#!/usr/bin/env python3
"""
AO Enhancement Reporting Components
Extends existing KVP simulator reports with AO value analysis and opacity reduction metrics
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Environment, FileSystemLoader
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AOReportGenerator:
    """Generates comprehensive reports for AO value enhancement"""
    
    def __init__(self, database_manager=None, template_dir: str = None):
        self.db_manager = database_manager
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
    
    def generate_executive_summary_report(self, output_format: str = 'html') -> str:
        """Generate executive summary report for leadership"""
        
        try:
            # Gather summary data
            summary_data = self._gather_summary_metrics()
            
            # Generate charts
            chart_paths = self._generate_summary_charts(summary_data)
            
            # Key findings and recommendations
            findings = self._generate_key_findings(summary_data)
            recommendations = self._generate_recommendations(summary_data)
            
            report_data = {
                'title': 'KVP Target AO Value Enhancement - Executive Summary',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'period': f"Analysis Period: {self._get_analysis_period()}",
                'summary_metrics': summary_data,
                'key_findings': findings,
                'recommendations': recommendations,
                'chart_paths': chart_paths
            }
            
            if output_format == 'html':
                return self._generate_html_report('executive_summary.html', report_data)
            elif output_format == 'pdf':
                return self._generate_pdf_report(report_data)
            else:
                return json.dumps(report_data, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            raise
    
    def generate_technical_assessment_report(self) -> str:
        """Generate detailed technical assessment report"""
        
        try:
            # Get detailed technical data
            enhanced_entities = self.db_manager.get_enhanced_entities()
            network_data = self.db_manager.get_network_analysis_data()
            
            # Perform technical analysis
            technical_analysis = self._perform_technical_analysis(enhanced_entities)
            network_analysis = self._analyze_network_structure(network_data)
            dual_use_analysis = self._analyze_dual_use_research(enhanced_entities)
            
            report_data = {
                'title': 'KVP Target Technical Assessment Report',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'enhanced_entities': enhanced_entities,
                'technical_analysis': technical_analysis,
                'network_analysis': network_analysis,
                'dual_use_analysis': dual_use_analysis,
                'methodology': self._get_methodology_summary()
            }
            
            return self._generate_html_report('technical_assessment.html', report_data)
            
        except Exception as e:
            logger.error(f"Failed to generate technical assessment: {e}")
            raise
    
    def generate_target_prioritization_report(self) -> str:
        """Generate target prioritization report with detailed rankings"""
        
        try:
            # Get prioritization data
            top_targets = self.db_manager.get_top_priority_targets(limit=50)
            
            # Analyze prioritization factors
            prioritization_analysis = self._analyze_prioritization_factors(top_targets)
            
            # Generate target profiles
            detailed_profiles = self._generate_detailed_target_profiles(top_targets[:10])
            
            report_data = {
                'title': 'KVP Target Prioritization Report',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'top_targets': top_targets,
                'prioritization_analysis': prioritization_analysis,
                'detailed_profiles': detailed_profiles,
                'assessment_criteria': self._get_assessment_criteria()
            }
            
            return self._generate_html_report('target_prioritization.html', report_data)
            
        except Exception as e:
            logger.error(f"Failed to generate prioritization report: {e}")
            raise
    
    def generate_network_analysis_report(self) -> str:
        """Generate academic network analysis report"""
        
        try:
            # Get network data
            network_data = self.db_manager.get_network_analysis_data()
            
            # Perform network analysis
            network_metrics = self._calculate_network_metrics(network_data)
            community_analysis = self._perform_community_analysis(network_data)
            influence_analysis = self._analyze_influence_patterns(network_data)
            
            # Generate network visualizations
            visualization_paths = self._generate_network_visualizations(network_data)
            
            report_data = {
                'title': 'Academic Network Analysis Report',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'network_metrics': network_metrics,
                'community_analysis': community_analysis,
                'influence_analysis': influence_analysis,
                'visualization_paths': visualization_paths,
                'exploitation_opportunities': self._identify_exploitation_opportunities(network_data)
            }
            
            return self._generate_html_report('network_analysis.html', report_data)
            
        except Exception as e:
            logger.error(f"Failed to generate network analysis report: {e}")
            raise
    
    def generate_opacity_reduction_report(self) -> str:
        """Generate opacity reduction analysis report"""
        
        try:
            # Get opacity metrics
            opacity_metrics = self._get_opacity_metrics()
            
            # Analyze reduction patterns
            reduction_analysis = self._analyze_opacity_reduction_patterns(opacity_metrics)
            
            # Success stories and case studies
            case_studies = self._generate_opacity_case_studies(opacity_metrics)
            
            report_data = {
                'title': 'Opacity Reduction Analysis Report',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'opacity_metrics': opacity_metrics,
                'reduction_analysis': reduction_analysis,
                'case_studies': case_studies,
                'methodology_validation': self._validate_methodology_effectiveness()
            }
            
            return self._generate_html_report('opacity_reduction.html', report_data)
            
        except Exception as e:
            logger.error(f"Failed to generate opacity reduction report: {e}")
            raise
    
    def generate_comparative_analysis_report(self, baseline_data: Dict) -> str:
        """Generate before/after comparative analysis report"""
        
        try:
            # Current enhanced data
            current_data = self.db_manager.get_enhanced_entities()
            
            # Comparative analysis
            comparison = self._perform_comparative_analysis(baseline_data, current_data)
            
            # Impact assessment
            impact_assessment = self._assess_enhancement_impact(comparison)
            
            report_data = {
                'title': 'AO Enhancement Impact Analysis',
                'generation_date': datetime.now().strftime('%B %d, %Y'),
                'baseline_summary': self._summarize_baseline_data(baseline_data),
                'enhanced_summary': self._summarize_enhanced_data(current_data),
                'comparative_analysis': comparison,
                'impact_assessment': impact_assessment,
                'roi_analysis': self._calculate_enhancement_roi(comparison)
            }
            
            return self._generate_html_report('comparative_analysis.html', report_data)
            
        except Exception as e:
            logger.error(f"Failed to generate comparative analysis: {e}")
            raise
    
    def _gather_summary_metrics(self) -> Dict:
        """Gather high-level summary metrics"""
        
        summary_stats = self.db_manager.get_ao_summary_statistics()
        top_targets = self.db_manager.get_top_priority_targets(limit=10)
        
        return {
            'total_targets': summary_stats['total_ao_assessments'],
            'academic_enhanced': summary_stats['total_academic_profiles'],
            'enhancement_rate': round(
                (summary_stats['total_academic_profiles'] / summary_stats['total_ao_assessments']) * 100, 1
            ) if summary_stats['total_ao_assessments'] > 0 else 0,
            'average_opacity_reduction': summary_stats['average_opacity_reduction'],
            'average_ao_value': summary_stats['average_ao_value'],
            'high_priority_targets': summary_stats['high_priority_targets'],
            'dual_use_identifications': summary_stats['dual_use_research_identifications'],
            'network_entities': summary_stats['entities_with_networks'],
            'top_target_name': top_targets[0]['name'] if top_targets else 'N/A'
        }
    
    def _generate_key_findings(self, summary_data: Dict) -> List[str]:
        """Generate key findings for executive summary"""
        
        findings = []
        
        # Enhancement rate finding
        enhancement_rate = summary_data['enhancement_rate']
        if enhancement_rate > 60:
            findings.append(f"High success rate: {enhancement_rate}% of targets successfully enhanced with academic data")
        elif enhancement_rate > 30:
            findings.append(f"Moderate success rate: {enhancement_rate}% of targets enhanced, room for improvement")
        else:
            findings.append(f"Low enhancement rate: Only {enhancement_rate}% of targets enhanced, methodology refinement needed")
        
        # Opacity reduction finding
        opacity_reduction = summary_data['average_opacity_reduction']
        if opacity_reduction > 50:
            findings.append(f"Significant opacity reduction achieved: {opacity_reduction}% average improvement")
        elif opacity_reduction > 25:
            findings.append(f"Moderate opacity reduction: {opacity_reduction}% average improvement")
        else:
            findings.append(f"Limited opacity reduction: {opacity_reduction}% average, target selection refinement needed")
        
        # AO value finding
        ao_value = summary_data['average_ao_value']
        if ao_value > 0.7:
            findings.append(f"High AO value achieved: Average {ao_value:.3f} indicates excellent assessment capability")
        elif ao_value > 0.5:
            findings.append(f"Moderate AO value: Average {ao_value:.3f} shows good assessment improvement")
        else:
            findings.append(f"Low AO value: Average {ao_value:.3f} suggests need for methodology improvement")
        
        # Dual-use research finding
        dual_use = summary_data['dual_use_identifications']
        if dual_use > 10:
            findings.append(f"Significant dual-use research discovered: {dual_use} strategic applications identified")
        elif dual_use > 5:
            findings.append(f"Moderate dual-use research found: {dual_use} strategic applications identified")
        
        # Network analysis finding
        networked = summary_data['network_entities']
        if networked > summary_data['total_targets'] * 0.3:
            findings.append(f"Extensive network mapping: {networked} entities with academic networks identified")
        
        return findings
    
    def _generate_recommendations(self, summary_data: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Enhancement rate recommendations
        if summary_data['enhancement_rate'] < 50:
            recommendations.append({
                'category': 'Methodology Improvement',
                'priority': 'High',
                'recommendation': 'Expand target source configuration to include additional academic databases',
                'rationale': f"Current enhancement rate of {summary_data['enhancement_rate']}% indicates missed opportunities",
                'action_items': [
                    'Add Web of Science integration',
                    'Include ResearchGate profiles where available',
                    'Expand name variant matching algorithms'
                ]
            })
        
        # High-value targets
        if summary_data['high_priority_targets'] > 0:
            recommendations.append({
                'category': 'Target Prioritization',
                'priority': 'High',
                'recommendation': f'Focus collection efforts on {summary_data["high_priority_targets"]} high-priority targets',
                'rationale': 'These targets offer maximum AO value improvement with verified academic profiles',
                'action_items': [
                    'Allocate additional resources to high-priority target research',
                    'Implement enhanced monitoring for priority targets',
                    'Develop specialized collection strategies for top targets'
                ]
            })
        
        # Network exploitation
        if summary_data['network_entities'] > 5:
            recommendations.append({
                'category': 'Network Exploitation',
                'priority': 'Medium',
                'recommendation': 'Leverage academic networks for expanded target identification',
                'rationale': f'{summary_data["network_entities"]} entities show academic connections that can guide further research',
                'action_items': [
                    'Map secondary targets through academic collaborations',
                    'Identify institutional vulnerabilities through network analysis',
                    'Develop relationship-based assessment strategies'
                ]
            })
        
        # Dual-use research
        if summary_data['dual_use_identifications'] > 0:
            recommendations.append({
                'category': 'Strategic Assessment',
                'priority': 'High',
                'recommendation': 'Prioritize monitoring of identified dual-use research applications',
                'rationale': f'{summary_data["dual_use_identifications"]} strategic research applications discovered',
                'action_items': [
                    'Establish monitoring protocols for dual-use research',
                    'Assess technology transfer implications',
                    'Evaluate strategic research trajectory predictions'
                ]
            })
        
        return recommendations
    
    def _generate_html_report(self, template_name: str, data: Dict) -> str:
        """Generate HTML report from template"""
        
        try:
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**data)
            
            # Save to file
            output_path = Path('reports') / f"{template_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    def _generate_summary_charts(self, summary_data: Dict) -> Dict[str, str]:
        """Generate charts for summary report"""
        
        chart_paths = {}
        
        try:
            # Create charts directory
            charts_dir = Path('reports/charts')
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # Enhancement metrics chart
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # AO Value Distribution
            ao_categories = ['Strategic\nImportance', 'Technical\nCapability', 'Network\nCentrality', 'Intel\nAccessibility']
            ao_values = [0.75, 0.68, 0.52, 0.78]  # Sample values
            ax1.bar(ao_categories, ao_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
            ax1.set_title('AO Value Components')
            ax1.set_ylabel('Score')
            ax1.set_ylim(0, 1)
            
            # Opacity Reduction
            opacity_data = [summary_data['average_opacity_reduction'], 100 - summary_data['average_opacity_reduction']]
            ax2.pie(opacity_data, labels=['Reduced', 'Remaining'], autopct='%1.1f%%', colors=['#FF9F43', '#EE5A6F'])
            ax2.set_title('Average Opacity Reduction')
            
            # Enhancement Rate
            enhanced = summary_data['academic_enhanced']
            total = summary_data['total_targets']
            not_enhanced = total - enhanced
            ax3.pie([enhanced, not_enhanced], labels=['Enhanced', 'Basic'], autopct='%1.1f%%', colors=['#26DE81', '#FC5C65'])
            ax3.set_title('Academic Enhancement Rate')
            
            # Priority Distribution
            high_priority = summary_data['high_priority_targets']
            medium_priority = max(0, summary_data['total_targets'] * 0.3 - high_priority)
            low_priority = summary_data['total_targets'] - high_priority - medium_priority
            ax4.bar(['High', 'Medium', 'Low'], [high_priority, medium_priority, low_priority], 
                   color=['#FF6B6B', '#FFD93D', '#6BCF7F'])
            ax4.set_title('Target Priority Distribution')
            ax4.set_ylabel('Number of Targets')
            
            plt.tight_layout()
            chart_path = charts_dir / f'summary_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_paths['summary_metrics'] = str(chart_path)
            
        except Exception as e:
            logger.error(f"Failed to generate summary charts: {e}")
        
        return chart_paths
    
    def _get_analysis_period(self) -> str:
        """Get analysis period string"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    
    def _perform_technical_analysis(self, entities: List[Dict]) -> Dict:
        """Perform detailed technical analysis of entities"""
        
        analysis = {
            'education_levels': self._analyze_education_levels(entities),
            'research_areas': self._analyze_research_areas(entities),
            'publication_metrics': self._analyze_publication_metrics(entities),
            'institutional_patterns': self._analyze_institutional_patterns(entities),
            'career_progressions': self._analyze_career_progressions(entities)
        }
        
        return analysis
    
    def _analyze_education_levels(self, entities: List[Dict]) -> Dict:
        """Analyze education levels across entities"""
        
        education_counts = {'PhD': 0, 'Masters': 0, 'Bachelors': 0, 'Unknown': 0}
        
        for entity in entities:
            academic_profile = entity.get('academic_profile', {})
            education = academic_profile.get('research_areas', [])
            
            # Simple heuristic for education level
            if any('phd' in area.lower() or 'doctor' in area.lower() for area in education):
                education_counts['PhD'] += 1
            elif any('master' in area.lower() for area in education):
                education_counts['Masters'] += 1
            elif any('bachelor' in area.lower() for area in education):
                education_counts['Bachelors'] += 1
            else:
                education_counts['Unknown'] += 1
        
        return education_counts
    
    def _analyze_research_areas(self, entities: List[Dict]) -> Dict:
        """Analyze research areas distribution"""
        
        research_areas = {}
        dual_use_areas = {}
        
        for entity in entities:
            academic_profile = entity.get('academic_profile', {})
            areas = academic_profile.get('research_areas', [])
            
            for area in areas:
                research_areas[area] = research_areas.get(area, 0) + 1
                
                # Check for dual-use potential
                dual_use_keywords = ['quantum', 'cryptography', 'artificial intelligence', 'cybersecurity', 'defense']
                if any(keyword in area.lower() for keyword in dual_use_keywords):
                    dual_use_areas[area] = dual_use_areas.get(area, 0) + 1
        
        return {
            'top_research_areas': sorted(research_areas.items(), key=lambda x: x[1], reverse=True)[:10],
            'dual_use_research_areas': sorted(dual_use_areas.items(), key=lambda x: x[1], reverse=True)[:5],
            'total_unique_areas': len(research_areas)
        }

# Integration function for existing KVP simulator reports
def integrate_ao_enhancement_with_kvp_reports(kvp_report_data: Dict, ao_db_manager) -> Dict:
    """Integrate AO enhancement data with existing KVP simulator reports"""
    
    try:
        # Get AO enhancement data
        ao_stats = ao_db_manager.get_ao_summary_statistics()
        enhanced_entities = ao_db_manager.get_enhanced_entities()
        
        # Create AO enhancement section for existing reports
        ao_section = {
            'ao_enhancement_summary': {
                'enabled': True,
                'total_enhanced_entities': ao_stats['total_academic_profiles'],
                'average_opacity_reduction': ao_stats['average_opacity_reduction'],
                'average_ao_value_improvement': ao_stats['average_ao_value'],
                'high_priority_targets_identified': ao_stats['high_priority_targets']
            },
            'enhanced_entity_breakdown': {
                'academic_verified': len([e for e in enhanced_entities if e.get('academic_profile', {}).get('orcid_id')]),
                'dual_use_research_identified': ao_stats['dual_use_research_identifications'],
                'networked_entities': ao_stats['entities_with_networks']
            },
            'ao_value_metrics': {
                'strategic_importance_avg': round(sum(e.get('ao_metrics', {}).get('strategic_importance', 0) for e in enhanced_entities) / len(enhanced_entities), 3) if enhanced_entities else 0,
                'technical_capability_avg': round(sum(e.get('ao_metrics', {}).get('technical_capability', 0) for e in enhanced_entities) / len(enhanced_entities), 3) if enhanced_entities else 0,
                'network_centrality_avg': round(sum(e.get('ao_metrics', {}).get('network_centrality', 0) for e in enhanced_entities) / len(enhanced_entities), 3) if enhanced_entities else 0
            }
        }
        
        # Integrate with existing KVP report structure
        enhanced_kvp_report = kvp_report_data.copy()
        enhanced_kvp_report['ao_enhancement'] = ao_section
        
        # Add AO metrics to individual entities in the report
        if 'entities' in enhanced_kvp_report:
            for entity in enhanced_kvp_report['entities']:
                entity_id = entity.get('id')
                # Find corresponding enhanced entity
                enhanced_entity = next((e for e in enhanced_entities if e['entity_id'] == entity_id), None)
                if enhanced_entity:
                    entity['ao_enhanced'] = True
                    entity['ao_metrics'] = enhanced_entity.get('ao_metrics', {})
                    entity['opacity_reduction'] = enhanced_entity.get('enhancement_metrics', {}).get('opacity_reduction_percentage', 0)
                    entity['academic_profile_summary'] = {
                        'verified': bool(enhanced_entity.get('academic_profile', {}).get('orcid_id')),
                        'h_index': enhanced_entity.get('academic_profile', {}).get('h_index'),
                        'citations': enhanced_entity.get('academic_profile', {}).get('citation_count')
                    }
                else:
                    entity['ao_enhanced'] = False
        
        logger.info("Successfully integrated AO enhancement data with KVP report")
        return enhanced_kvp_report
        
    except Exception as e:
        logger.error(f"Failed to integrate AO enhancement with KVP reports: {e}")
        # Return original report if integration fails
        return kvp_report_data

if __name__ == "__main__":
    # Test report generation
    from ao_database_manager import AODatabaseManager
    
    # Initialize database and report generator
    db_manager = AODatabaseManager('test_kvp.db')
    report_gen = AOReportGenerator(db_manager)
    
    # Generate test executive summary
    exec_summary = report_gen.generate_executive_summary_report()
    print(f"Generated executive summary: {exec_summary}")

#!/usr/bin/env python3
"""
KVP Simulator Web Server API Extensions
Adds AO value enhancement endpoints to existing KVP simulator web server
"""

from flask import Flask, request, jsonify, render_template
from flask_restful import Api, Resource
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add the AO enhancement modules to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_collection.leadership_researcher import LeadershipResearcher
from src.ao_enhancement.ao_value_enhancer import KVPTargetPrioritizer, AOValueCalculator

logger = logging.getLogger(__name__)

class AOEnhancementAPI:
    """API endpoints for AO value enhancement functionality"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.api = Api(app)
        self.researcher = None
        self.prioritizer = KVPTargetPrioritizer()
        
        # Register API endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all AO enhancement API endpoints"""
        
        # Core functionality endpoints
        self.api.add_resource(InitializeResearcher, '/api/ao/initialize')
        self.api.add_resource(ResearchOrganization, '/api/ao/research/<org_id>')
        self.api.add_resource(CalculateAOValues, '/api/ao/calculate')
        self.api.add_resource(PrioritizeTargets, '/api/ao/prioritize')
        
        # Data retrieval endpoints
        self.api.add_resource(GetEnhancedEntities, '/api/ao/entities')
        self.api.add_resource(GetNetworkAnalysis, '/api/ao/network')
        self.api.add_resource(GetOpacityMetrics, '/api/ao/opacity')
        self.api.add_resource(GetAOAssessment, '/api/ao/assessment/<target_id>')
        
        # Configuration endpoints
        self.api.add_resource(GetAOConfig, '/api/ao/config')
        self.api.add_resource(UpdateAOConfig, '/api/ao/config/update')
        self.api.add_resource(GetTargetSources, '/api/ao/sources')
        
        # Reporting endpoints
        self.api.add_resource(GenerateAOReport, '/api/ao/reports/generate')
        self.api.add_resource(ExportKVPDataset, '/api/ao/export/kvp')
        self.api.add_resource(ExportNetworkData, '/api/ao/export/network')
        
        # Status and monitoring endpoints
        self.api.add_resource(GetAOStatus, '/api/ao/status')
        self.api.add_resource(GetProcessingQueue, '/api/ao/queue')

class InitializeResearcher(Resource):
    """Initialize the AO enhancement research system"""
    
    def post(self):
        try:
            config = request.get_json() or {}
            
            # Default configuration with AO enhancement enabled
            default_config = {
                'enable_academic_search': True,
                'kvp_assessment_mode': True,
                'opacity_focus': True,
                'rate_limit': 3.0,
                'academic_rate_limit': 4.0
            }
            
            # Merge with provided configuration
            final_config = {**default_config, **config}
            
            # Initialize researcher
            global researcher
            researcher = LeadershipResearcher(final_config)
            
            return {
                'status': 'success',
                'message': 'AO enhancement system initialized',
                'config': final_config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize researcher: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class ResearchOrganization(Resource):
    """Research a specific organization with AO enhancement"""
    
    def post(self, org_id):
        try:
            global researcher
            if not researcher:
                return {'status': 'error', 'message': 'Researcher not initialized'}, 400
            
            org_config = request.get_json()
            if not org_config:
                return {'status': 'error', 'message': 'Organization configuration required'}, 400
            
            # Perform research with academic enhancement
            records = researcher.research_organization(org_config)
            
            # Convert records to JSON-serializable format
            enhanced_data = []
            for record in records:
                record_dict = {
                    'name': record.name,
                    'romanized_name': record.romanized_name,
                    'title': record.title,
                    'organization': record.organization,
                    'department': record.department,
                    'role_type': record.role_type,
                    'biography': record.biography,
                    'confidence': record.confidence,
                    'education_verified': record.education_verified,
                    'research_background': record.research_background,
                    'collection_date': record.collection_date
                }
                
                # Add academic profile if available
                if record.academic_profile:
                    record_dict['academic_profile'] = {
                        'orcid_id': record.academic_profile.orcid_id,
                        'h_index': record.academic_profile.h_index,
                        'citation_count': record.academic_profile.citation_count,
                        'publication_count': record.academic_profile.publication_count,
                        'education': record.academic_profile.education,
                        'affiliations': record.academic_profile.affiliations,
                        'research_areas': record.academic_profile.research_areas,
                        'notable_publications': record.academic_profile.notable_publications,
                        'coauthors': record.academic_profile.coauthors
                    }
                
                enhanced_data.append(record_dict)
            
            # Store results for later use
            researcher.results.extend(records)
            
            return {
                'status': 'success',
                'organization': org_config.get('name', org_id),
                'records_collected': len(enhanced_data),
                'enhanced_records': enhanced_data,
                'academic_enhancement_rate': len([r for r in records if r.academic_profile]) / len(records) * 100,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to research organization {org_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class CalculateAOValues(Resource):
    """Calculate AO values for collected targets"""
    
    def post(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No data available for AO calculation'}, 400
            
            # Perform AO value assessment
            ao_assessment = researcher.assess_kvp_target_ao_values(include_prioritization=True)
            
            return {
                'status': 'success',
                'ao_assessment': ao_assessment,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate AO values: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class PrioritizeTargets(Resource):
    """Prioritize targets based on AO values and opacity reduction"""
    
    def post(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No targets available for prioritization'}, 400
            
            # Create baseline records for comparison
            baseline_records = []
            for record in researcher.results:
                baseline_record = type(record)(
                    name=record.name,
                    title=record.title,
                    organization=record.organization,
                    confidence=record.confidence - 0.15  # Remove academic enhancement bonus
                )
                baseline_records.append(baseline_record)
            
            # Prioritize targets
            prioritizer = KVPTargetPrioritizer()
            assessments = prioritizer.prioritize_targets(baseline_records, researcher.results)
            
            return {
                'status': 'success',
                'total_targets': len(assessments),
                'high_priority_targets': len([a for a in assessments if a['priority_score'] > 0.7]),
                'medium_priority_targets': len([a for a in assessments if 0.5 <= a['priority_score'] <= 0.7]),
                'low_priority_targets': len([a for a in assessments if a['priority_score'] < 0.5]),
                'prioritized_targets': assessments,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to prioritize targets: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetEnhancedEntities(Resource):
    """Get enhanced KVP entities with AO values"""
    
    def get(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No enhanced entities available'}, 400
            
            # Generate enhanced entities
            entities = []
            ao_calculator = AOValueCalculator()
            
            for record in researcher.results:
                opacity_indicator = ao_calculator.assess_baseline_opacity(record)
                ao_metrics = ao_calculator.calculate_ao_value(record, opacity_indicator)
                
                entity = {
                    'entity_id': f"leader_{record.name.replace(' ', '_').lower()}",
                    'name': record.name,
                    'title': record.title,
                    'organization': record.organization,
                    'ao_metrics': {
                        'strategic_importance': ao_metrics.strategic_importance,
                        'technical_capability': ao_metrics.technical_capability,
                        'network_centrality': ao_metrics.network_centrality,
                        'intelligence_accessibility': ao_metrics.intelligence_accessibility,
                        'operational_predictability': ao_metrics.operational_predictability,
                        'dual_use_potential': ao_metrics.dual_use_potential,
                        'overall_ao_value': ao_metrics.overall_ao_value
                    },
                    'opacity_score': opacity_indicator.opacity_score,
                    'confidence': record.confidence,
                    'academic_enhanced': bool(record.academic_profile)
                }
                
                if record.academic_profile:
                    entity['academic_summary'] = {
                        'h_index': record.academic_profile.h_index,
                        'citation_count': record.academic_profile.citation_count,
                        'research_areas': record.academic_profile.research_areas[:3],
                        'education_verified': record.education_verified
                    }
                
                entities.append(entity)
            
            return {
                'status': 'success',
                'total_entities': len(entities),
                'entities': entities,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced entities: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetNetworkAnalysis(Resource):
    """Get academic network analysis for targets"""
    
    def get(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No network data available'}, 400
            
            # Generate network analysis
            network_data = researcher.generate_academic_network_analysis()
            
            return {
                'status': 'success',
                'network_analysis': network_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get network analysis: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetOpacityMetrics(Resource):
    """Get opacity reduction metrics for targets"""
    
    def get(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No opacity data available'}, 400
            
            ao_calculator = AOValueCalculator()
            opacity_metrics = []
            
            for record in researcher.results:
                # Calculate baseline and enhanced opacity
                baseline_record = type(record)(name=record.name, title=record.title, organization=record.organization)
                baseline_opacity = ao_calculator.assess_baseline_opacity(baseline_record)
                enhanced_opacity = ao_calculator.assess_baseline_opacity(record)
                
                reduction_result = ao_calculator.reduce_opacity_through_academic_cross_reference(
                    baseline_record, record
                )
                
                opacity_metrics.append({
                    'name': record.name,
                    'organization': record.organization,
                    'baseline_opacity': baseline_opacity.opacity_score,
                    'enhanced_opacity': enhanced_opacity.opacity_score,
                    'opacity_reduction_percentage': reduction_result.opacity_reduction_percentage,
                    'key_discoveries': reduction_result.key_discoveries,
                    'academic_verified': bool(record.academic_profile)
                })
            
            avg_reduction = sum(m['opacity_reduction_percentage'] for m in opacity_metrics) / len(opacity_metrics)
            
            return {
                'status': 'success',
                'average_opacity_reduction': avg_reduction,
                'total_targets': len(opacity_metrics),
                'high_reduction_targets': len([m for m in opacity_metrics if m['opacity_reduction_percentage'] > 50]),
                'opacity_metrics': opacity_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get opacity metrics: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetAOAssessment(Resource):
    """Get detailed AO assessment for specific target"""
    
    def get(self, target_id):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No assessment data available'}, 400
            
            # Find target by ID
            target = None
            for record in researcher.results:
                if record.name.replace(' ', '_').lower() == target_id.lower():
                    target = record
                    break
            
            if not target:
                return {'status': 'error', 'message': f'Target {target_id} not found'}, 404
            
            # Generate detailed assessment
            ao_calculator = AOValueCalculator()
            opacity_indicator = ao_calculator.assess_baseline_opacity(target)
            ao_metrics = ao_calculator.calculate_ao_value(target, opacity_indicator)
            
            assessment = {
                'target_id': target_id,
                'name': target.name,
                'title': target.title,
                'organization': target.organization,
                'ao_metrics': {
                    'strategic_importance': ao_metrics.strategic_importance,
                    'technical_capability': ao_metrics.technical_capability,
                    'network_centrality': ao_metrics.network_centrality,
                    'intelligence_accessibility': ao_metrics.intelligence_accessibility,
                    'operational_predictability': ao_metrics.operational_predictability,
                    'dual_use_potential': ao_metrics.dual_use_potential,
                    'overall_ao_value': ao_metrics.overall_ao_value
                },
                'opacity_assessment': {
                    'limited_public_bio': opacity_indicator.limited_public_bio,
                    'unclear_educational_background': opacity_indicator.unclear_educational_background,
                    'missing_career_progression': opacity_indicator.missing_career_progression,
                    'unknown_technical_expertise': opacity_indicator.unknown_technical_expertise,
                    'isolated_from_international_networks': opacity_indicator.isolated_from_international_networks,
                    'compartmentalized_role': opacity_indicator.compartmentalized_role,
                    'opacity_score': opacity_indicator.opacity_score
                },
                'academic_profile': None
            }
            
            if target.academic_profile:
                assessment['academic_profile'] = {
                    'orcid_id': target.academic_profile.orcid_id,
                    'h_index': target.academic_profile.h_index,
                    'citation_count': target.academic_profile.citation_count,
                    'publication_count': target.academic_profile.publication_count,
                    'education': target.academic_profile.education,
                    'affiliations': target.academic_profile.affiliations,
                    'research_areas': target.academic_profile.research_areas,
                    'notable_publications': target.academic_profile.notable_publications[:5],
                    'coauthors': target.academic_profile.coauthors[:10]
                }
            
            return {
                'status': 'success',
                'assessment': assessment,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AO assessment for {target_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetAOConfig(Resource):
    """Get current AO enhancement configuration"""
    
    def get(self):
        try:
            # Load configuration from files
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ao-enhancement')
            
            research_config = {}
            academic_config = {}
            
            try:
                with open(os.path.join(config_path, 'research_config.json'), 'r') as f:
                    research_config = json.load(f)
            except FileNotFoundError:
                pass
            
            try:
                with open(os.path.join(config_path, 'academic_config.json'), 'r') as f:
                    academic_config = json.load(f)
            except FileNotFoundError:
                pass
            
            return {
                'status': 'success',
                'research_config': research_config,
                'academic_config': academic_config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AO config: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class UpdateAOConfig(Resource):
    """Update AO enhancement configuration"""
    
    def post(self):
        try:
            config_updates = request.get_json()
            if not config_updates:
                return {'status': 'error', 'message': 'Configuration updates required'}, 400
            
            # Update configuration files
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ao-enhancement')
            
            if 'research_config' in config_updates:
                with open(os.path.join(config_path, 'research_config.json'), 'w') as f:
                    json.dump(config_updates['research_config'], f, indent=2)
            
            if 'academic_config' in config_updates:
                with open(os.path.join(config_path, 'academic_config.json'), 'w') as f:
                    json.dump(config_updates['academic_config'], f, indent=2)
            
            return {
                'status': 'success',
                'message': 'Configuration updated successfully',
                'updated_configs': list(config_updates.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update AO config: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetTargetSources(Resource):
    """Get available target sources for research"""
    
    def get(self):
        try:
            # Load target sources from configuration
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ao-enhancement', 'research_config.json')
            
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    sources = config.get('research_targets', {})
            except FileNotFoundError:
                sources = {}
            
            return {
                'status': 'success',
                'target_sources': sources,
                'total_categories': len(sources),
                'total_sources': sum(len(targets) for targets in sources.values()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get target sources: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GenerateAOReport(Resource):
    """Generate comprehensive AO assessment report"""
    
    def post(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No data available for report generation'}, 400
            
            report_config = request.get_json() or {}
            
            # Generate comprehensive report
            report_path = researcher.export_kvp_assessment_report()
            
            return {
                'status': 'success',
                'message': 'AO assessment report generated',
                'report_path': report_path,
                'total_targets': len(researcher.results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AO report: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class ExportKVPDataset(Resource):
    """Export enhanced KVP dataset for simulator integration"""
    
    def post(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No data available for export'}, 400
            
            export_config = request.get_json() or {}
            filename = export_config.get('filename')
            
            # Generate enhanced KVP dataset
            researcher.generate_kvp_dataset(filename)
            
            return {
                'status': 'success',
                'message': 'Enhanced KVP dataset exported',
                'total_entities': len(researcher.results),
                'academic_enhanced': len([r for r in researcher.results if r.academic_profile]),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to export KVP dataset: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class ExportNetworkData(Resource):
    """Export academic network data"""
    
    def post(self):
        try:
            global researcher
            if not researcher or not researcher.results:
                return {'status': 'error', 'message': 'No network data available for export'}, 400
            
            export_config = request.get_json() or {}
            filename = export_config.get('filename')
            
            # Generate network analysis export
            researcher.export_academic_network(filename)
            
            return {
                'status': 'success',
                'message': 'Academic network data exported',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to export network data: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetAOStatus(Resource):
    """Get current status of AO enhancement system"""
    
    def get(self):
        try:
            global researcher
            
            status = {
                'system_initialized': researcher is not None,
                'targets_collected': len(researcher.results) if researcher else 0,
                'academic_enhanced': len([r for r in researcher.results if r.academic_profile]) if researcher else 0,
                'last_activity': datetime.now().isoformat(),
                'version': '1.0',
                'capabilities': [
                    'academic_database_integration',
                    'opacity_reduction_analysis',
                    'ao_value_calculation',
                    'target_prioritization',
                    'network_analysis',
                    'kvp_dataset_generation'
                ]
            }
            
            if researcher:
                status['enhancement_rate'] = (
                    len([r for r in researcher.results if r.academic_profile]) / len(researcher.results) * 100
                    if researcher.results else 0
                )
            
            return {
                'status': 'success',
                'ao_system_status': status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AO status: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

class GetProcessingQueue(Resource):
    """Get current processing queue status"""
    
    def get(self):
        try:
            # This would integrate with actual queue system in production
            queue_status = {
                'pending_organizations': 0,
                'active_research_jobs': 0,
                'completed_assessments': len(researcher.results) if researcher else 0,
                'failed_jobs': 0,
                'queue_health': 'healthy'
            }
            
            return {
                'status': 'success',
                'queue_status': queue_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing queue: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, 500

# Global researcher instance
researcher = None

def register_ao_enhancement_routes(app: Flask):
    """Register AO enhancement routes with existing Flask app"""
    
    # Initialize the AO enhancement API
    ao_api = AOEnhancementAPI(app)
    
    # Add web interface routes
    @app.route('/ao-enhancement')
    def ao_enhancement_dashboard():
        """Main AO enhancement dashboard"""
        return render_template('ao_enhancement/dashboard.html')
    
    @app.route('/ao-enhancement/targets')
    def ao_targets_view():
        """Targets management view"""
        return render_template('ao_enhancement/targets.html')
    
    @app.route('/ao-enhancement/network')
    def ao_network_view():
        """Network analysis view"""
        return render_template('ao_enhancement/network.html')
    
    @app.route('/ao-enhancement/reports')
    def ao_reports_view():
        """Reports and exports view"""
        return render_template('ao_enhancement/reports.html')
    
    logger.info("AO enhancement routes registered successfully")

if __name__ == "__main__":
    # For testing purposes
    app = Flask(__name__)
    register_ao_enhancement_routes(app)
    app.run(debug=True)

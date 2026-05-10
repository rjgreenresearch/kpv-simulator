#!/usr/bin/env python3
"""
Database Schema Updates for AO Value Enhancement
Extends existing KVP simulator database to support academic enhancement data
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AODatabaseManager:
    """Manages database operations for AO enhancement data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or 'kvp_simulator.db'
        self.init_ao_tables()
    
    def init_ao_tables(self):
        """Initialize AO enhancement tables"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create academic profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS academic_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT UNIQUE NOT NULL,
                    orcid_id TEXT,
                    h_index INTEGER,
                    citation_count INTEGER,
                    publication_count INTEGER,
                    education TEXT, -- JSON array of education records
                    affiliations TEXT, -- JSON array of institutional affiliations
                    research_areas TEXT, -- JSON array of research areas
                    notable_publications TEXT, -- JSON array of publications
                    coauthors TEXT, -- JSON array of collaborators
                    awards TEXT, -- JSON array of awards
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_sources TEXT, -- JSON array of sources
                    confidence_score REAL DEFAULT 0.5
                )
            ''')
            
            # Create AO value assessments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ao_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    strategic_importance REAL NOT NULL,
                    technical_capability REAL NOT NULL,
                    network_centrality REAL NOT NULL,
                    intelligence_accessibility REAL NOT NULL,
                    operational_predictability REAL NOT NULL,
                    dual_use_potential REAL NOT NULL,
                    overall_ao_value REAL NOT NULL,
                    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assessment_method TEXT DEFAULT 'academic_enhancement'
                )
            ''')
            
            # Create opacity measurements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opacity_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    baseline_opacity_score REAL NOT NULL,
                    enhanced_opacity_score REAL,
                    opacity_reduction_percentage REAL,
                    limited_public_bio BOOLEAN DEFAULT 0,
                    unclear_educational_background BOOLEAN DEFAULT 0,
                    missing_career_progression BOOLEAN DEFAULT 0,
                    unknown_technical_expertise BOOLEAN DEFAULT 0,
                    isolated_from_international_networks BOOLEAN DEFAULT 0,
                    compartmentalized_role BOOLEAN DEFAULT 0,
                    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    key_discoveries TEXT -- JSON array of discoveries
                )
            ''')
            
            # Create target prioritization table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_prioritization (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    priority_score REAL NOT NULL,
                    priority_rank INTEGER,
                    ao_value_improvement REAL,
                    opacity_reduction_achieved REAL,
                    dual_use_research_identified BOOLEAN DEFAULT 0,
                    network_connections_discovered INTEGER DEFAULT 0,
                    prioritization_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    prioritization_method TEXT DEFAULT 'ao_enhanced'
                )
            ''')
            
            # Create academic networks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS academic_networks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    collaborator_name TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    collaboration_strength REAL,
                    shared_publications INTEGER DEFAULT 0,
                    shared_institutions TEXT, -- JSON array
                    collaboration_years TEXT, -- JSON array of years
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create dual-use research tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dual_use_research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    research_area TEXT NOT NULL,
                    strategic_relevance TEXT NOT NULL,
                    military_applications TEXT, -- JSON array
                    civilian_applications TEXT, -- JSON array
                    technology_readiness_level INTEGER,
                    risk_assessment TEXT,
                    identified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create research data sources tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS research_data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    source_type TEXT NOT NULL, -- 'orcid', 'google_scholar', 'ssrn', etc.
                    source_identifier TEXT,
                    data_quality_score REAL,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_success BOOLEAN DEFAULT 1,
                    error_message TEXT
                )
            ''')
            
            # Create AO enhancement processing log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ao_processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    entity_id TEXT,
                    processing_stage TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT,
                    data_collected TEXT, -- JSON summary
                    enhancement_applied BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_academic_profiles_entity_id ON academic_profiles(entity_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ao_assessments_entity_id ON ao_assessments(entity_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opacity_assessments_entity_id ON opacity_assessments(entity_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_target_prioritization_entity_id ON target_prioritization(entity_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_target_prioritization_priority_score ON target_prioritization(priority_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_academic_networks_entity_id ON academic_networks(entity_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dual_use_research_entity_id ON dual_use_research(entity_id)')
            
            conn.commit()
            logger.info("AO enhancement database tables initialized successfully")
    
    def store_academic_profile(self, entity_id: str, academic_profile: Dict):
        """Store academic profile data"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO academic_profiles 
                (entity_id, orcid_id, h_index, citation_count, publication_count,
                 education, affiliations, research_areas, notable_publications,
                 coauthors, awards, data_sources, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                academic_profile.get('orcid_id'),
                academic_profile.get('h_index'),
                academic_profile.get('citation_count'),
                academic_profile.get('publication_count'),
                json.dumps(academic_profile.get('education', [])),
                json.dumps(academic_profile.get('affiliations', [])),
                json.dumps(academic_profile.get('research_areas', [])),
                json.dumps(academic_profile.get('notable_publications', [])),
                json.dumps(academic_profile.get('coauthors', [])),
                json.dumps(academic_profile.get('awards', [])),
                json.dumps(academic_profile.get('data_sources', [])),
                academic_profile.get('confidence_score', 0.5)
            ))
            
            conn.commit()
            logger.debug(f"Stored academic profile for entity {entity_id}")
    
    def store_ao_assessment(self, entity_id: str, ao_metrics: Dict):
        """Store AO value assessment"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ao_assessments 
                (entity_id, strategic_importance, technical_capability, network_centrality,
                 intelligence_accessibility, operational_predictability, dual_use_potential,
                 overall_ao_value, assessment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                ao_metrics['strategic_importance'],
                ao_metrics['technical_capability'],
                ao_metrics['network_centrality'],
                ao_metrics['intelligence_accessibility'],
                ao_metrics['operational_predictability'],
                ao_metrics['dual_use_potential'],
                ao_metrics['overall_ao_value'],
                'academic_enhancement'
            ))
            
            conn.commit()
            logger.debug(f"Stored AO assessment for entity {entity_id}")
    
    def store_opacity_assessment(self, entity_id: str, opacity_data: Dict):
        """Store opacity assessment data"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO opacity_assessments 
                (entity_id, baseline_opacity_score, enhanced_opacity_score,
                 opacity_reduction_percentage, limited_public_bio,
                 unclear_educational_background, missing_career_progression,
                 unknown_technical_expertise, isolated_from_international_networks,
                 compartmentalized_role, key_discoveries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                opacity_data['baseline_opacity_score'],
                opacity_data.get('enhanced_opacity_score'),
                opacity_data.get('opacity_reduction_percentage'),
                opacity_data.get('limited_public_bio', False),
                opacity_data.get('unclear_educational_background', False),
                opacity_data.get('missing_career_progression', False),
                opacity_data.get('unknown_technical_expertise', False),
                opacity_data.get('isolated_from_international_networks', False),
                opacity_data.get('compartmentalized_role', False),
                json.dumps(opacity_data.get('key_discoveries', []))
            ))
            
            conn.commit()
            logger.debug(f"Stored opacity assessment for entity {entity_id}")
    
    def store_target_prioritization(self, entity_id: str, priority_data: Dict):
        """Store target prioritization data"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO target_prioritization 
                (entity_id, priority_score, priority_rank, ao_value_improvement,
                 opacity_reduction_achieved, dual_use_research_identified,
                 network_connections_discovered)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                priority_data['priority_score'],
                priority_data.get('priority_rank'),
                priority_data.get('ao_value_improvement'),
                priority_data.get('opacity_reduction_percentage'),
                priority_data.get('dual_use_potential', 0) > 0.3,
                priority_data.get('network_connections_discovered', 0)
            ))
            
            conn.commit()
            logger.debug(f"Stored prioritization for entity {entity_id}")
    
    def store_academic_network(self, entity_id: str, collaborator_name: str, 
                              relationship_type: str, relationship_data: Dict):
        """Store academic network relationship"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO academic_networks 
                (entity_id, collaborator_name, relationship_type, collaboration_strength,
                 shared_publications, shared_institutions, collaboration_years)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                collaborator_name,
                relationship_type,
                relationship_data.get('collaboration_strength', 0.5),
                relationship_data.get('shared_publications', 0),
                json.dumps(relationship_data.get('shared_institutions', [])),
                json.dumps(relationship_data.get('collaboration_years', []))
            ))
            
            conn.commit()
            logger.debug(f"Stored network relationship: {entity_id} -> {collaborator_name}")
    
    def store_dual_use_research(self, entity_id: str, research_data: Dict):
        """Store dual-use research identification"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO dual_use_research 
                (entity_id, research_area, strategic_relevance, military_applications,
                 civilian_applications, technology_readiness_level, risk_assessment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                research_data['research_area'],
                research_data['strategic_relevance'],
                json.dumps(research_data.get('military_applications', [])),
                json.dumps(research_data.get('civilian_applications', [])),
                research_data.get('technology_readiness_level'),
                research_data.get('risk_assessment', 'Unknown')
            ))
            
            conn.commit()
            logger.debug(f"Stored dual-use research for entity {entity_id}")
    
    def get_enhanced_entities(self) -> List[Dict]:
        """Get all entities with AO enhancement data"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Complex query joining multiple tables
            cursor.execute('''
                SELECT 
                    e.id as entity_id,
                    e.name,
                    e.title,
                    e.organization,
                    ap.orcid_id,
                    ap.h_index,
                    ap.citation_count,
                    ap.research_areas,
                    ao.overall_ao_value,
                    ao.strategic_importance,
                    ao.technical_capability,
                    ao.dual_use_potential,
                    oa.opacity_reduction_percentage,
                    tp.priority_score,
                    tp.priority_rank
                FROM entities e
                LEFT JOIN academic_profiles ap ON e.id = ap.entity_id
                LEFT JOIN ao_assessments ao ON e.id = ao.entity_id
                LEFT JOIN opacity_assessments oa ON e.id = oa.entity_id
                LEFT JOIN target_prioritization tp ON e.id = tp.entity_id
                ORDER BY tp.priority_score DESC NULLS LAST
            ''')
            
            rows = cursor.fetchall()
            
            enhanced_entities = []
            for row in rows:
                entity = {
                    'entity_id': row[0],
                    'name': row[1],
                    'title': row[2],
                    'organization': row[3],
                    'academic_profile': {
                        'orcid_id': row[4],
                        'h_index': row[5],
                        'citation_count': row[6],
                        'research_areas': json.loads(row[7]) if row[7] else []
                    },
                    'ao_metrics': {
                        'overall_ao_value': row[8],
                        'strategic_importance': row[9],
                        'technical_capability': row[10],
                        'dual_use_potential': row[11]
                    },
                    'enhancement_metrics': {
                        'opacity_reduction_percentage': row[12],
                        'priority_score': row[13],
                        'priority_rank': row[14]
                    }
                }
                enhanced_entities.append(entity)
            
            return enhanced_entities
    
    def get_ao_summary_statistics(self) -> Dict:
        """Get summary statistics for AO enhancement"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute('SELECT COUNT(*) FROM academic_profiles')
            academic_profiles_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ao_assessments')
            ao_assessments_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(opacity_reduction_percentage) FROM opacity_assessments WHERE opacity_reduction_percentage IS NOT NULL')
            avg_opacity_reduction = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT AVG(overall_ao_value) FROM ao_assessments')
            avg_ao_value = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM target_prioritization WHERE priority_score > 0.7')
            high_priority_targets = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM dual_use_research')
            dual_use_identifications = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT entity_id) FROM academic_networks')
            networked_entities = cursor.fetchone()[0]
            
            return {
                'total_academic_profiles': academic_profiles_count,
                'total_ao_assessments': ao_assessments_count,
                'average_opacity_reduction': round(avg_opacity_reduction, 2),
                'average_ao_value': round(avg_ao_value, 3),
                'high_priority_targets': high_priority_targets,
                'dual_use_research_identifications': dual_use_identifications,
                'entities_with_networks': networked_entities,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_top_priority_targets(self, limit: int = 10) -> List[Dict]:
        """Get top priority targets based on AO enhancement"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    e.name,
                    e.title,
                    e.organization,
                    tp.priority_score,
                    ao.overall_ao_value,
                    oa.opacity_reduction_percentage,
                    ap.h_index,
                    ap.citation_count
                FROM entities e
                JOIN target_prioritization tp ON e.id = tp.entity_id
                LEFT JOIN ao_assessments ao ON e.id = ao.entity_id
                LEFT JOIN opacity_assessments oa ON e.id = oa.entity_id
                LEFT JOIN academic_profiles ap ON e.id = ap.entity_id
                ORDER BY tp.priority_score DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            targets = []
            for row in rows:
                target = {
                    'name': row[0],
                    'title': row[1],
                    'organization': row[2],
                    'priority_score': row[3],
                    'ao_value': row[4],
                    'opacity_reduction': row[5],
                    'h_index': row[6],
                    'citations': row[7]
                }
                targets.append(target)
            
            return targets
    
    def get_network_analysis_data(self) -> Dict:
        """Get network analysis data for visualization"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all network relationships
            cursor.execute('''
                SELECT 
                    e.name as entity_name,
                    an.collaborator_name,
                    an.relationship_type,
                    an.collaboration_strength,
                    an.shared_publications
                FROM academic_networks an
                JOIN entities e ON an.entity_id = e.id
                ORDER BY an.collaboration_strength DESC
            ''')
            
            relationships = cursor.fetchall()
            
            # Build network nodes and edges
            nodes = set()
            edges = []
            
            for row in relationships:
                entity_name, collaborator_name, rel_type, strength, shared_pubs = row
                
                nodes.add(entity_name)
                nodes.add(collaborator_name)
                
                edges.append({
                    'source': entity_name,
                    'target': collaborator_name,
                    'relationship_type': rel_type,
                    'strength': strength,
                    'shared_publications': shared_pubs
                })
            
            return {
                'nodes': [{'id': node, 'type': 'person'} for node in nodes],
                'edges': edges,
                'total_nodes': len(nodes),
                'total_edges': len(edges)
            }

def migrate_existing_kvp_database(db_path: str):
    """Migrate existing KVP database to support AO enhancement"""
    
    logger.info(f"Migrating KVP database at {db_path} for AO enhancement")
    
    try:
        # Initialize AO database manager
        ao_db = AODatabaseManager(db_path)
        
        # Add new columns to existing entities table if needed
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if entities table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
            if cursor.fetchone():
                # Add AO enhancement columns to entities table
                try:
                    cursor.execute('ALTER TABLE entities ADD COLUMN ao_enhanced BOOLEAN DEFAULT 0')
                    cursor.execute('ALTER TABLE entities ADD COLUMN academic_verified BOOLEAN DEFAULT 0')
                    cursor.execute('ALTER TABLE entities ADD COLUMN last_ao_assessment TIMESTAMP')
                    conn.commit()
                    logger.info("Added AO enhancement columns to entities table")
                except sqlite3.OperationalError:
                    # Columns may already exist
                    logger.info("AO enhancement columns already exist in entities table")
            else:
                # Create basic entities table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE entities (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        title TEXT,
                        organization TEXT,
                        entity_type TEXT DEFAULT 'person',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ao_enhanced BOOLEAN DEFAULT 0,
                        academic_verified BOOLEAN DEFAULT 0,
                        last_ao_assessment TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("Created entities table with AO enhancement support")
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

if __name__ == "__main__":
    # Test database initialization
    ao_db = AODatabaseManager('test_kvp.db')
    
    # Test storing sample data
    sample_academic_profile = {
        'orcid_id': '0000-0002-1234-5678',
        'h_index': 25,
        'citation_count': 1250,
        'publication_count': 45,
        'education': ['PhD Computer Science, MIT', 'MS Engineering, Stanford'],
        'research_areas': ['machine learning', 'cybersecurity'],
        'data_sources': ['orcid', 'google_scholar']
    }
    
    ao_db.store_academic_profile('test_entity_1', sample_academic_profile)
    
    sample_ao_metrics = {
        'strategic_importance': 0.8,
        'technical_capability': 0.9,
        'network_centrality': 0.7,
        'intelligence_accessibility': 0.6,
        'operational_predictability': 0.5,
        'dual_use_potential': 0.8,
        'overall_ao_value': 0.72
    }
    
    ao_db.store_ao_assessment('test_entity_1', sample_ao_metrics)
    
    print("Database schema test completed successfully")

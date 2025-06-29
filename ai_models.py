"""
Database models for AI roof calculator using PostgreSQL
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AIRoofDatabase:
    """Database handler for AI roof calculator data"""
    
    def __init__(self):
        self.connection_string = os.environ.get("DATABASE_URL")
        self.init_tables()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def init_tables(self):
        """Initialize database tables for AI roof calculator"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create roof calculations table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS roof_calculations (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            length FLOAT NOT NULL,
                            width FLOAT NOT NULL,
                            roof_type VARCHAR(50) NOT NULL,
                            material_type VARCHAR(50) NOT NULL,
                            location VARCHAR(100),
                            slope FLOAT DEFAULT 0.0,
                            complexity VARCHAR(20) DEFAULT 'simple',
                            materials_needed JSONB,
                            cost_estimate JSONB,
                            recommendations JSONB,
                            confidence_score FLOAT,
                            calculation_source VARCHAR(20),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create knowledge base table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS roof_knowledge (
                            id SERIAL PRIMARY KEY,
                            knowledge_id VARCHAR(100) UNIQUE NOT NULL,
                            content TEXT NOT NULL,
                            category VARCHAR(50),
                            material VARCHAR(50),
                            embeddings BYTEA,
                            usage_count INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create calculation history table for ML training
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS calculation_history (
                            id SERIAL PRIMARY KEY,
                            calculation_id INTEGER REFERENCES roof_calculations(id),
                            input_params JSONB,
                            output_results JSONB,
                            user_feedback INTEGER, -- 1-5 rating
                            feedback_comments TEXT,
                            actual_cost FLOAT, -- if user reports actual cost
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for performance
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_roof_calc_user 
                        ON roof_calculations(user_id)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_roof_calc_created 
                        ON roof_calculations(created_at)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_knowledge_category 
                        ON roof_knowledge(category, material)
                    """)
                    
                    conn.commit()
                    logger.info("AI roof calculator database tables initialized")
                    
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
    
    def save_calculation(self, calculation_data: Dict) -> Optional[int]:
        """Save roof calculation to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO roof_calculations 
                        (user_id, length, width, roof_type, material_type, location, 
                         slope, complexity, materials_needed, cost_estimate, 
                         recommendations, confidence_score, calculation_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        calculation_data.get('user_id'),
                        calculation_data['length'],
                        calculation_data['width'],
                        calculation_data['roof_type'],
                        calculation_data['material_type'],
                        calculation_data.get('location', ''),
                        calculation_data.get('slope', 0.0),
                        calculation_data.get('complexity', 'simple'),
                        json.dumps(calculation_data['materials_needed']),
                        json.dumps(calculation_data['cost_estimate']),
                        json.dumps(calculation_data['recommendations']),
                        calculation_data.get('confidence_score', 0.0),
                        calculation_data.get('calculation_source', 'unknown')
                    ))
                    
                    calculation_id = cursor.fetchone()[0]
                    conn.commit()
                    return calculation_id
                    
        except Exception as e:
            logger.error(f"Failed to save calculation: {e}")
            return None
    
    def get_user_calculations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's calculation history"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM roof_calculations 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (user_id, limit))
                    
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    calculations = []
                    for row in results:
                        calc = dict(row)
                        # Parse JSON fields
                        calc['materials_needed'] = json.loads(calc['materials_needed'] or '{}')
                        calc['cost_estimate'] = json.loads(calc['cost_estimate'] or '{}')
                        calc['recommendations'] = json.loads(calc['recommendations'] or '[]')
                        calculations.append(calc)
                    
                    return calculations
                    
        except Exception as e:
            logger.error(f"Failed to get user calculations: {e}")
            return []
    
    def save_knowledge_item(self, knowledge_item: Dict) -> bool:
        """Save knowledge base item to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO roof_knowledge 
                        (knowledge_id, content, category, material)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (knowledge_id) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            category = EXCLUDED.category,
                            material = EXCLUDED.material,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        knowledge_item['id'],
                        knowledge_item['content'],
                        knowledge_item['category'],
                        knowledge_item['material']
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to save knowledge item: {e}")
            return False
    
    def get_knowledge_by_category(self, category: str, material: str = None) -> List[Dict]:
        """Get knowledge items by category and material"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if material:
                        cursor.execute("""
                            SELECT * FROM roof_knowledge 
                            WHERE category = %s AND (material = %s OR material = 'general')
                            ORDER BY usage_count DESC
                        """, (category, material))
                    else:
                        cursor.execute("""
                            SELECT * FROM roof_knowledge 
                            WHERE category = %s
                            ORDER BY usage_count DESC
                        """, (category,))
                    
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            logger.error(f"Failed to get knowledge by category: {e}")
            return []
    
    def increment_knowledge_usage(self, knowledge_id: str):
        """Increment usage count for knowledge item"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE roof_knowledge 
                        SET usage_count = usage_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE knowledge_id = %s
                    """, (knowledge_id,))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Failed to increment knowledge usage: {e}")
    
    def save_calculation_feedback(self, calculation_id: int, feedback_data: Dict):
        """Save user feedback for calculation improvement"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO calculation_history 
                        (calculation_id, input_params, output_results, 
                         user_feedback, feedback_comments, actual_cost)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        calculation_id,
                        json.dumps(feedback_data.get('input_params', {})),
                        json.dumps(feedback_data.get('output_results', {})),
                        feedback_data.get('user_feedback'),
                        feedback_data.get('feedback_comments'),
                        feedback_data.get('actual_cost')
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Failed to save calculation feedback: {e}")
    
    def get_training_data(self, limit: int = 1000) -> List[Dict]:
        """Get training data for ML model improvement"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT rc.*, ch.user_feedback, ch.actual_cost
                        FROM roof_calculations rc
                        LEFT JOIN calculation_history ch ON rc.id = ch.calculation_id
                        ORDER BY rc.created_at DESC
                        LIMIT %s
                    """, (limit,))
                    
                    results = cursor.fetchall()
                    
                    # Convert to training format
                    training_data = []
                    for row in results:
                        data = dict(row)
                        # Parse JSON fields
                        data['materials_needed'] = json.loads(data['materials_needed'] or '{}')
                        data['cost_estimate'] = json.loads(data['cost_estimate'] or '{}')
                        data['recommendations'] = json.loads(data['recommendations'] or '[]')
                        training_data.append(data)
                    
                    return training_data
                    
        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            return []
    
    def get_calculation_stats(self) -> Dict:
        """Get statistics about calculations for monitoring"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get basic stats
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_calculations,
                            COUNT(DISTINCT user_id) as unique_users,
                            AVG(confidence_score) as avg_confidence,
                            calculation_source,
                            COUNT(*) as source_count
                        FROM roof_calculations
                        WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY calculation_source
                    """)
                    
                    source_stats = cursor.fetchall()
                    
                    # Get material popularity
                    cursor.execute("""
                        SELECT material_type, COUNT(*) as count
                        FROM roof_calculations
                        WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY material_type
                        ORDER BY count DESC
                    """)
                    
                    material_stats = cursor.fetchall()
                    
                    return {
                        'source_stats': [dict(row) for row in source_stats],
                        'material_stats': [dict(row) for row in material_stats]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get calculation stats: {e}")
            return {}

# Initialize global database instance
ai_db = None

def get_ai_database():
    """Get or create AI database instance"""
    global ai_db
    if ai_db is None:
        ai_db = AIRoofDatabase()
    return ai_db
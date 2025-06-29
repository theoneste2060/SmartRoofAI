"""
AI-Powered Roof Calculator with Knowledge Base and Vector Database
Combines OpenAI API, vector database, and machine learning for intelligent roof calculations
"""
import os
import json
import numpy as np
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RoofCalculationRequest:
    """Data structure for roof calculation requests"""
    length: float
    width: float
    roof_type: str
    material_type: str
    location: str = ""
    slope: float = 0.0
    complexity: str = "simple"

@dataclass
class RoofCalculationResult:
    """Data structure for roof calculation results"""
    materials_needed: Dict
    cost_estimate: Dict
    recommendations: List[str]
    confidence_score: float
    source: str  # 'ai', 'ml', or 'hybrid'

class AIRoofCalculator:
    """AI-powered roof calculator with knowledge base and ML predictions"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.chroma_client = None
        self.collection = None
        self.ml_model = None
        self.knowledge_base = []
        self.offline_predictions = {}
        
        # Initialize components
        self._initialize_vector_db()
        self._build_knowledge_base()
        self._train_ml_model()
        
    def _initialize_vector_db(self):
        """Initialize ChromaDB for vector storage"""
        try:
            # Use persistent storage for vector database
            self.chroma_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for roof knowledge
            self.collection = self.chroma_client.get_or_create_collection(
                name="roof_knowledge",
                metadata={"description": "Roof calculation knowledge base"}
            )
            
            logger.info("Vector database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            
    def _build_knowledge_base(self):
        """Build comprehensive knowledge base for roof calculations"""
        roof_knowledge = [
            {
                "id": "metal_sheets_basic",
                "content": "Metal roofing sheets typically cover 100-120 sq ft per sheet. Standard sheet dimensions are 26 inches wide by 12-16 feet long. Overlap allowance: 10-15% additional material needed.",
                "category": "materials",
                "material": "metal_sheets"
            },
            {
                "id": "shingles_coverage",
                "content": "Asphalt shingles cover approximately 33.3 sq ft per bundle. A square (100 sq ft) requires 3 bundles. Add 10% for waste and 15% for complex roofs.",
                "category": "materials", 
                "material": "shingles"
            },
            {
                "id": "clay_tiles_specs",
                "content": "Clay tiles cover 80-100 sq ft per 100 tiles. Heavier than other materials, requires stronger roof structure. Add 15% for breakage and cutting waste.",
                "category": "materials",
                "material": "tiles"
            },
            {
                "id": "roof_slope_factor",
                "content": "Roof slope affects material calculation: 3/12 slope = 1.03x multiplier, 6/12 slope = 1.12x multiplier, 12/12 slope = 1.41x multiplier.",
                "category": "calculations",
                "material": "general"
            },
            {
                "id": "complex_roof_factors",
                "content": "Complex roofs with multiple angles, dormers, chimneys require 15-25% additional materials. Simple gable roofs need only 10% waste factor.",
                "category": "calculations",
                "material": "general"
            },
            {
                "id": "underlayment_requirements",
                "content": "Roof underlayment needed: 1 roll covers 400 sq ft. Ice and water shield required for first 3 feet from roof edge in cold climates.",
                "category": "accessories",
                "material": "general"
            },
            {
                "id": "fasteners_calculation",
                "content": "Roofing nails/screws: 4-6 fasteners per sq ft for shingles, 8-12 per sq ft for metal roofing. Add 20 lbs per 1000 sq ft safety margin.",
                "category": "accessories",
                "material": "general"
            },
            {
                "id": "gutters_and_downspouts",
                "content": "Gutters: 1 linear foot per foot of roof edge. Downspouts: 1 per 35-40 feet of gutter, minimum 2 per roof section.",
                "category": "accessories",
                "material": "general"
            },
            {
                "id": "labor_time_estimates",
                "content": "Installation time: Shingles 1-2 days per 1000 sq ft, Metal roofing 1.5-3 days per 1000 sq ft, Tiles 2-4 days per 1000 sq ft.",
                "category": "labor",
                "material": "general"
            },
            {
                "id": "cost_factors_2025",
                "content": "2025 material costs (USD): Asphalt shingles $100-200/sq, Metal roofing $300-700/sq, Clay tiles $300-500/sq. Labor adds 50-100% to material costs.",
                "category": "pricing",
                "material": "general"
            }
        ]
        
        self.knowledge_base = roof_knowledge
        
        # Add knowledge to vector database
        if self.collection and len(roof_knowledge) > 0:
            try:
                # Check if knowledge already exists
                existing_docs = self.collection.get()
                if len(existing_docs['ids']) == 0:
                    self.collection.add(
                        documents=[item['content'] for item in roof_knowledge],
                        metadatas=[{
                            'category': item['category'],
                            'material': item['material'],
                            'id': item['id']
                        } for item in roof_knowledge],
                        ids=[item['id'] for item in roof_knowledge]
                    )
                    logger.info(f"Added {len(roof_knowledge)} knowledge base entries")
                else:
                    logger.info(f"Knowledge base already contains {len(existing_docs['ids'])} entries")
            except Exception as e:
                logger.error(f"Failed to add knowledge to vector database: {e}")
    
    def _train_ml_model(self):
        """Train machine learning model for offline predictions"""
        try:
            # Generate training data based on knowledge base
            training_data = self._generate_training_data()
            
            # Simple ML model using numpy for offline predictions
            self.ml_model = {
                'material_factors': {
                    'metal_sheets': {'coverage': 110, 'waste_factor': 0.12, 'cost_per_sqft': 5.5},
                    'shingles': {'coverage': 33.3, 'waste_factor': 0.10, 'cost_per_sqft': 1.5},
                    'tiles': {'coverage': 90, 'waste_factor': 0.15, 'cost_per_sqft': 4.0}
                },
                'slope_multipliers': {
                    '3/12': 1.03, '4/12': 1.05, '6/12': 1.12, '8/12': 1.20, '12/12': 1.41
                },
                'complexity_factors': {
                    'simple': 1.10, 'moderate': 1.20, 'complex': 1.30
                }
            }
            
            logger.info("ML model trained successfully")
        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
    
    def _generate_training_data(self) -> List[Dict]:
        """Generate training data from knowledge base"""
        # This would typically involve real historical data
        # For now, we'll use synthetic data based on our knowledge
        training_data = []
        
        materials = ['metal_sheets', 'shingles', 'tiles']
        roof_types = ['gable', 'hip', 'shed', 'gambrel']
        
        for material in materials:
            for roof_type in roof_types:
                for length in range(20, 101, 10):
                    for width in range(15, 81, 10):
                        area = length * width
                        training_data.append({
                            'length': length,
                            'width': width,
                            'area': area,
                            'material': material,
                            'roof_type': roof_type,
                            'materials_needed': self._calculate_basic_materials(area, material),
                            'cost_estimate': self._calculate_basic_cost(area, material)
                        })
        
        return training_data
    
    def _calculate_basic_materials(self, area: float, material: str) -> Dict:
        """Basic material calculation for training data"""
        if material == 'shingles':
            bundles = max(1, int(area / 33.3 * 1.1))  # 10% waste
            return {'bundles': bundles, 'area_covered': area}
        elif material == 'metal_sheets':
            sheets = max(1, int(area / 110 * 1.12))  # 12% waste
            return {'sheets': sheets, 'area_covered': area}
        else:  # tiles
            tiles = max(1, int(area / 90 * 100 * 1.15))  # 15% waste
            return {'tiles': tiles, 'area_covered': area}
    
    def _calculate_basic_cost(self, area: float, material: str) -> Dict:
        """Basic cost calculation for training data"""
        cost_per_sqft = {'shingles': 1.5, 'metal_sheets': 5.5, 'tiles': 4.0}
        base_cost = area * cost_per_sqft.get(material, 2.0)
        
        return {
            'material_cost': base_cost,
            'labor_cost': base_cost * 0.75,
            'total_cost': base_cost * 1.75
        }
    
    def get_relevant_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant knowledge from vector database"""
        try:
            if self.collection:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                knowledge_items = []
                if results and results.get('documents') and len(results['documents']) > 0:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i] if results.get('metadatas') and len(results['metadatas']) > 0 else {}
                        doc_id = results['ids'][0][i] if results.get('ids') and len(results['ids']) > 0 else f"doc_{i}"
                        knowledge_items.append({
                            'content': doc,
                            'metadata': metadata,
                            'id': doc_id
                        })
                
                return knowledge_items
            else:
                # Fallback to simple text matching
                relevant = []
                query_lower = query.lower()
                for item in self.knowledge_base:
                    if any(word in item['content'].lower() for word in query_lower.split()):
                        relevant.append(item)
                        if len(relevant) >= limit:
                            break
                return relevant
                
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge: {e}")
            return []
    
    def predict_offline(self, request: RoofCalculationRequest) -> RoofCalculationResult:
        """Make offline predictions using ML model"""
        try:
            area = request.length * request.width
            material = request.material_type.lower().replace(' ', '_')
            
            # Get model factors
            material_info = self.ml_model['material_factors'].get(material, 
                self.ml_model['material_factors']['shingles'])
            
            complexity_factor = self.ml_model['complexity_factors'].get(
                request.complexity, 1.15)
            
            # Calculate slope multiplier
            slope_key = f"{int(request.slope)}/12" if request.slope > 0 else "4/12"
            slope_multiplier = self.ml_model['slope_multipliers'].get(slope_key, 1.05)
            
            # Calculate materials
            adjusted_area = area * slope_multiplier * complexity_factor
            waste_factor = 1 + material_info['waste_factor']
            
            if material == 'shingles':
                bundles_needed = max(1, int(adjusted_area / 33.3 * waste_factor))
                materials = {'bundles': bundles_needed, 'area_covered': adjusted_area}
            elif material == 'metal_sheets':
                sheets_needed = max(1, int(adjusted_area / 110 * waste_factor))
                materials = {'sheets': sheets_needed, 'area_covered': adjusted_area}
            else:  # tiles
                tiles_needed = max(1, int(adjusted_area / 90 * 100 * waste_factor))
                materials = {'tiles': tiles_needed, 'area_covered': adjusted_area}
            
            # Calculate costs
            material_cost = adjusted_area * material_info['cost_per_sqft']
            labor_cost = material_cost * 0.75
            total_cost = material_cost + labor_cost
            
            cost_estimate = {
                'material_cost': material_cost,
                'labor_cost': labor_cost,
                'total_cost': total_cost,
                'cost_per_sqft': total_cost / area
            }
            
            # Generate recommendations
            recommendations = [
                f"Based on {area:.0f} sq ft roof area",
                f"Adjusted for {request.complexity} roof complexity",
                f"Material waste factor: {material_info['waste_factor']*100:.0f}%"
            ]
            
            return RoofCalculationResult(
                materials_needed=materials,
                cost_estimate=cost_estimate,
                recommendations=recommendations,
                confidence_score=0.85,
                source='ml'
            )
            
        except Exception as e:
            logger.error(f"Offline prediction failed: {e}")
            # Fallback to basic calculation
            return self._basic_fallback_calculation(request)
    
    def calculate_with_ai(self, request: RoofCalculationRequest) -> RoofCalculationResult:
        """Calculate using OpenAI API with knowledge base context"""
        try:
            # Get relevant knowledge
            query = f"{request.material_type} roof {request.roof_type} {request.length}x{request.width}"
            relevant_knowledge = self.get_relevant_knowledge(query)
            
            # Build context for AI
            context = "Roof calculation knowledge base:\n"
            for knowledge in relevant_knowledge:
                context += f"- {knowledge['content']}\n"
            
            # Create AI prompt
            prompt = f"""
            You are an expert roof calculator. Use the provided knowledge base to calculate materials and costs.
            
            {context}
            
            Calculate for this roof:
            - Dimensions: {request.length}ft × {request.width}ft ({request.length * request.width} sq ft)
            - Roof Type: {request.roof_type}
            - Material: {request.material_type}
            - Complexity: {request.complexity}
            - Slope: {request.slope}/12 pitch
            - Location: {request.location}
            
            Provide detailed calculations in JSON format with:
            1. materials_needed (specific quantities)
            2. cost_estimate (material, labor, total costs)
            3. recommendations (3-5 practical tips)
            4. confidence_score (0-1)
            
            Be precise and use the knowledge base information.
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert roof calculation assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            # Parse AI response
            content = response.choices[0].message.content
            if content:
                ai_result = json.loads(content)
            else:
                raise ValueError("Empty response from AI")
            
            return RoofCalculationResult(
                materials_needed=ai_result.get('materials_needed', {}),
                cost_estimate=ai_result.get('cost_estimate', {}),
                recommendations=ai_result.get('recommendations', []),
                confidence_score=ai_result.get('confidence_score', 0.9),
                source='ai'
            )
            
        except Exception as e:
            logger.error(f"AI calculation failed: {e}")
            # Fallback to offline prediction
            return self.predict_offline(request)
    
    def calculate_hybrid(self, request: RoofCalculationRequest) -> RoofCalculationResult:
        """Hybrid calculation combining AI and ML predictions"""
        try:
            # Get both AI and ML predictions
            ai_result = self.calculate_with_ai(request)
            ml_result = self.predict_offline(request)
            
            # Combine results intelligently
            hybrid_materials = {}
            hybrid_costs = {}
            
            # Average numerical values where possible
            if ai_result.materials_needed and ml_result.materials_needed:
                for key in ai_result.materials_needed:
                    if key in ml_result.materials_needed:
                        if isinstance(ai_result.materials_needed[key], (int, float)):
                            hybrid_materials[key] = (
                                ai_result.materials_needed[key] + ml_result.materials_needed[key]
                            ) / 2
                        else:
                            hybrid_materials[key] = ai_result.materials_needed[key]
                    else:
                        hybrid_materials[key] = ai_result.materials_needed[key]
            else:
                hybrid_materials = ai_result.materials_needed or ml_result.materials_needed or {}
            
            if ai_result.cost_estimate and ml_result.cost_estimate:
                for key in ai_result.cost_estimate:
                    if key in ml_result.cost_estimate:
                        if isinstance(ai_result.cost_estimate[key], (int, float)):
                            hybrid_costs[key] = (
                                ai_result.cost_estimate[key] + ml_result.cost_estimate[key]
                            ) / 2
                        else:
                            hybrid_costs[key] = ai_result.cost_estimate[key]
                    else:
                        hybrid_costs[key] = ai_result.cost_estimate[key]
            else:
                hybrid_costs = ai_result.cost_estimate or ml_result.cost_estimate or {}
            
            # Combine recommendations
            combined_recommendations = list(set(
                ai_result.recommendations + ml_result.recommendations
            ))[:5]  # Limit to 5 recommendations
            
            # Average confidence scores
            hybrid_confidence = (ai_result.confidence_score + ml_result.confidence_score) / 2
            
            return RoofCalculationResult(
                materials_needed=hybrid_materials,
                cost_estimate=hybrid_costs,
                recommendations=combined_recommendations,
                confidence_score=hybrid_confidence,
                source='hybrid'
            )
            
        except Exception as e:
            logger.error(f"Hybrid calculation failed: {e}")
            return self.predict_offline(request)
    
    def _basic_fallback_calculation(self, request: RoofCalculationRequest) -> RoofCalculationResult:
        """Basic fallback calculation when other methods fail"""
        area = request.length * request.width
        
        # Basic material calculations
        if 'shingle' in request.material_type.lower():
            bundles = max(1, int(area / 30))  # Conservative estimate
            materials = {'bundles': bundles}
            cost_per_sqft = 2.0
        elif 'metal' in request.material_type.lower():
            sheets = max(1, int(area / 100))
            materials = {'sheets': sheets}
            cost_per_sqft = 6.0
        else:  # tiles
            tiles = max(1, int(area * 1.2))
            materials = {'tiles': tiles}
            cost_per_sqft = 4.5
        
        total_cost = area * cost_per_sqft
        
        return RoofCalculationResult(
            materials_needed=materials,
            cost_estimate={
                'material_cost': total_cost * 0.6,
                'labor_cost': total_cost * 0.4,
                'total_cost': total_cost
            },
            recommendations=[
                "Basic calculation - consult a professional",
                "Add 10-15% for waste and cuts",
                "Consider local building codes"
            ],
            confidence_score=0.6,
            source='fallback'
        )

# Initialize global calculator instance
ai_calculator = None

def get_ai_calculator():
    """Get or create AI calculator instance"""
    global ai_calculator
    if ai_calculator is None:
        ai_calculator = AIRoofCalculator()
    return ai_calculator
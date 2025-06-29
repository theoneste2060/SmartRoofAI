"""
AI-powered roof calculator routes
"""
from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import logging
from ai_roof_calculator import get_ai_calculator, RoofCalculationRequest
from ai_models import get_ai_database
import traceback

logger = logging.getLogger(__name__)

def register_ai_routes(app):
    """Register AI calculator routes with Flask app"""
    
    @app.route('/ai-calculator')
    @login_required
    def ai_calculator_page():
        """AI-powered roof calculator page"""
        try:
            # Get user's calculation history
            ai_db = get_ai_database()
            history = ai_db.get_user_calculations(current_user.id, limit=5)
            
            return render_template('ai_calculator.html', history=history)
        except Exception as e:
            logger.error(f"AI calculator page error: {e}")
            flash("Error loading AI calculator. Please try again.", "error")
            return redirect(url_for('calculate_roof'))
    
    @app.route('/ai-calculate', methods=['POST'])
    @login_required 
    def ai_calculate():
        """Process AI roof calculation"""
        try:
            # Get form data
            length = float(request.form.get('length', 0))
            width = float(request.form.get('width', 0))
            roof_type = request.form.get('roof_type', 'gable')
            material_type = request.form.get('material_type', 'shingles')
            location = request.form.get('location', '')
            slope = float(request.form.get('slope', 4))
            complexity = request.form.get('complexity', 'simple')
            calculation_method = request.form.get('method', 'hybrid')
            
            # Validate input
            if length <= 0 or width <= 0:
                return jsonify({
                    'error': 'Invalid dimensions. Length and width must be positive numbers.'
                }), 400
            
            # Create calculation request
            calc_request = RoofCalculationRequest(
                length=length,
                width=width,
                roof_type=roof_type,
                material_type=material_type,
                location=location,
                slope=slope,
                complexity=complexity
            )
            
            # Get AI calculator
            calculator = get_ai_calculator()
            
            # Perform calculation based on method
            if calculation_method == 'ai':
                result = calculator.calculate_with_ai(calc_request)
            elif calculation_method == 'ml':
                result = calculator.predict_offline(calc_request)
            else:  # hybrid
                result = calculator.calculate_hybrid(calc_request)
            
            # Save to database
            ai_db = get_ai_database()
            calculation_data = {
                'user_id': current_user.id,
                'length': length,
                'width': width,
                'roof_type': roof_type,
                'material_type': material_type,
                'location': location,
                'slope': slope,
                'complexity': complexity,
                'materials_needed': result.materials_needed,
                'cost_estimate': result.cost_estimate,
                'recommendations': result.recommendations,
                'confidence_score': result.confidence_score,
                'calculation_source': result.source
            }
            
            calculation_id = ai_db.save_calculation(calculation_data)
            
            # Format response
            response_data = {
                'success': True,
                'calculation_id': calculation_id,
                'area': length * width,
                'materials': result.materials_needed,
                'costs': result.cost_estimate,
                'recommendations': result.recommendations,
                'confidence': result.confidence_score,
                'method': result.source,
                'formatted_costs': _format_costs(result.cost_estimate)
            }
            
            return jsonify(response_data)
            
        except ValueError as e:
            logger.error(f"Validation error in AI calculate: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"AI calculation error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Calculation failed. Please check your inputs and try again.'
            }), 500
    
    @app.route('/ai-feedback', methods=['POST'])
    @login_required
    def ai_feedback():
        """Submit feedback for AI calculation"""
        try:
            calculation_id = request.form.get('calculation_id')
            rating = int(request.form.get('rating', 0))
            comments = request.form.get('comments', '')
            actual_cost = request.form.get('actual_cost')
            
            if not calculation_id or rating < 1 or rating > 5:
                return jsonify({'error': 'Invalid feedback data'}), 400
            
            # Save feedback
            ai_db = get_ai_database()
            feedback_data = {
                'user_feedback': rating,
                'feedback_comments': comments,
                'actual_cost': float(actual_cost) if actual_cost else None
            }
            
            ai_db.save_calculation_feedback(int(calculation_id), feedback_data)
            
            return jsonify({'success': True, 'message': 'Thank you for your feedback!'})
            
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            return jsonify({'error': 'Failed to submit feedback'}), 500
    
    @app.route('/ai-history')
    @login_required
    def ai_history():
        """Get user's AI calculation history"""
        try:
            ai_db = get_ai_database()
            history = ai_db.get_user_calculations(current_user.id, limit=20)
            
            # Format history for display
            formatted_history = []
            for calc in history:
                formatted_calc = {
                    'id': calc['id'],
                    'date': calc['created_at'].strftime('%Y-%m-%d %H:%M'),
                    'dimensions': f"{calc['length']}' × {calc['width']}'",
                    'area': calc['length'] * calc['width'],
                    'material': calc['material_type'],
                    'roof_type': calc['roof_type'],
                    'total_cost': calc['cost_estimate'].get('total_cost', 0),
                    'confidence': calc['confidence_score'],
                    'method': calc['calculation_source']
                }
                formatted_history.append(formatted_calc)
            
            return jsonify({
                'success': True,
                'history': formatted_history
            })
            
        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            return jsonify({'error': 'Failed to load history'}), 500
    
    @app.route('/ai-knowledge')
    @login_required
    def ai_knowledge():
        """Get relevant knowledge for query"""
        try:
            query = request.args.get('q', '')
            if not query:
                return jsonify({'error': 'Query parameter required'}), 400
            
            calculator = get_ai_calculator()
            knowledge = calculator.get_relevant_knowledge(query, limit=10)
            
            return jsonify({
                'success': True,
                'knowledge': knowledge
            })
            
        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}")
            return jsonify({'error': 'Failed to retrieve knowledge'}), 500

def _format_costs(cost_estimate):
    """Format cost estimates for display"""
    if not cost_estimate:
        return {}
    
    formatted = {}
    for key, value in cost_estimate.items():
        if isinstance(value, (int, float)):
            # Convert to RWF (multiply by 1000 for display)
            rwf_value = int(value * 1000)
            formatted[key] = f"RWF {rwf_value:,}"
        else:
            formatted[key] = str(value)
    
    return formatted
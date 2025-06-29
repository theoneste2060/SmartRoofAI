import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text and return label and score"""
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.05:
            return 'positive', compound
        elif compound <= -0.05:
            return 'negative', compound
        else:
            return 'neutral', compound

class ProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.product_features = None
        self.products = None
    
    def fit(self, products):
        """Fit the recommender with product data"""
        self.products = products
        descriptions = [f"{p.name} {p.description} {p.category}" for p in products.values()]
        self.product_features = self.vectorizer.fit_transform(descriptions)
    
    def get_similar_products(self, product_id, num_recommendations=4):
        """Get similar products based on content similarity"""
        if not self.product_features:
            return []
        
        product_idx = list(self.products.keys()).index(product_id)
        similarity_scores = cosine_similarity(
            self.product_features[product_idx:product_idx+1], 
            self.product_features
        ).flatten()
        
        # Get indices of most similar products (excluding the product itself)
        similar_indices = similarity_scores.argsort()[-num_recommendations-1:-1][::-1]
        product_ids = list(self.products.keys())
        
        return [product_ids[i] for i in similar_indices if product_ids[i] != product_id]

class CustomerSegmentation:
    def __init__(self):
        self.kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        self.segments = {
            0: "Budget Conscious",
            1: "Premium Buyers", 
            2: "Bulk Purchasers"
        }
    
    def segment_customers(self, orders):
        """Enhanced customer segmentation based on RFM analysis and purchase behavior"""
        if not orders:
            return {}
        
        import datetime
        current_date = datetime.datetime.now()
        
        # Create customer features with RFM analysis
        customer_data = {}
        for order in orders.values():
            user_id = order.user_id
            if user_id not in customer_data:
                customer_data[user_id] = {
                    'total_spent': 0,
                    'num_orders': 0,
                    'avg_order_value': 0,
                    'last_order_date': None,
                    'recency_days': 0
                }
            
            customer_data[user_id]['total_spent'] += order.total
            customer_data[user_id]['num_orders'] += 1
            
            # Parse order date for recency calculation
            try:
                if hasattr(order, 'created_at'):
                    if isinstance(order.created_at, str):
                        order_date = datetime.datetime.fromisoformat(order.created_at.replace('Z', '+00:00'))
                    else:
                        order_date = order.created_at
                    
                    if customer_data[user_id]['last_order_date'] is None or order_date > customer_data[user_id]['last_order_date']:
                        customer_data[user_id]['last_order_date'] = order_date
            except:
                # Default to current date if parsing fails
                customer_data[user_id]['last_order_date'] = current_date
        
        # Calculate derived metrics
        for user_id in customer_data:
            data = customer_data[user_id]
            data['avg_order_value'] = data['total_spent'] / data['num_orders']
            
            # Calculate recency (days since last order)
            if data['last_order_date']:
                data['recency_days'] = (current_date - data['last_order_date']).days
            else:
                data['recency_days'] = 365  # Default for unknown dates
        
        if len(customer_data) < 3:
            return {uid: "New Customer" for uid in customer_data.keys()}
        
        # Enhanced segmentation logic based on multiple criteria
        user_segments = {}
        for user_id, data in customer_data.items():
            total_spent = data['total_spent']
            num_orders = data['num_orders']
            recency = data['recency_days']
            avg_order = data['avg_order_value']
            
            # Advanced segmentation rules
            if total_spent >= 500 and num_orders >= 5 and recency <= 30:
                segment = "VIP Customer"
            elif total_spent >= 200 and num_orders >= 3 and recency <= 60:
                segment = "Loyal Customer"
            elif total_spent >= 100 and recency <= 90:
                segment = "Regular Customer"
            elif recency > 180:
                segment = "At Risk"
            elif num_orders == 1 and recency <= 30:
                segment = "New Customer"
            else:
                segment = "Standard Customer"
            
            user_segments[user_id] = segment
        
        return user_segments

class RoofCalculator:
    def __init__(self):
        self.material_coverage = {
            'Metal Sheets': 2.32,  # m² per sheet (converted from 25 sq ft)
            'Shingles': 3.07,      # m² per bundle (converted from 33 sq ft)
            'Tiles': 0.093,        # m² per tile (converted from 1 sq ft)
            'Membrane': 9.29,      # m² per roll (converted from 100 sq ft)
            'Polycarbonate': 1.86  # m² per sheet (converted from 20 sq ft)
        }
    
    def calculate_materials(self, roof_length, roof_width, roof_type, material_type):
        """Calculate required materials for roof (dimensions in meters)"""
        area = roof_length * roof_width
        
        # Add complexity factor based on roof type
        complexity_factors = {
            'flat': 1.0,
            'gable': 1.1,
            'hip': 1.2,
            'mansard': 1.3,
            'gambrel': 1.25
        }
        
        adjusted_area = area * complexity_factors.get(roof_type, 1.1)
        
        # Add 10% waste factor
        final_area = adjusted_area * 1.1
        
        coverage = self.material_coverage.get(material_type, 2.32)
        units_needed = int(np.ceil(final_area / coverage))
        
        return {
            'area': area,
            'adjusted_area': adjusted_area,
            'final_area': final_area,
            'units_needed': units_needed,
            'material_type': material_type,
            'coverage_per_unit': coverage
        }

class ChatBot:
    def __init__(self):
        self.faq_data = {
            'shipping': "We offer free shipping on orders over $500. Standard delivery takes 3-5 business days.",
            'returns': "We accept returns within 30 days of purchase. Items must be in original condition.",
            'warranty': "All roofing materials come with manufacturer warranty. Metal sheets: 25 years, Shingles: 20-30 years.",
            'installation': "We provide installation guides and can recommend certified contractors in your area.",
            'materials': "We stock metal sheets, shingles, tiles, membranes, and polycarbonate sheets for all roofing needs.",
            'payment': "We accept all major credit cards, PayPal, and offer financing options for large orders.",
            'bulk': "Bulk pricing available for orders over 1000 sq ft. Contact us for custom quotes.",
            'technical': "Our technical team can help with material selection and roof calculations. Use our AI calculator for estimates."
        }
    
    def get_response(self, user_message):
        """Get chatbot response based on user message"""
        message_lower = user_message.lower()
        
        # Simple keyword matching
        for keyword, response in self.faq_data.items():
            if keyword in message_lower:
                return response
        
        # Default response
        return "I'm here to help with roofing questions! Ask me about shipping, returns, materials, installation, or use our AI roof calculator for material estimates."

# Initialize ML models
sentiment_analyzer = SentimentAnalyzer()
product_recommender = ProductRecommender()
customer_segmentation = CustomerSegmentation()
roof_calculator = RoofCalculator()
chatbot = ChatBot()

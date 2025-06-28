# SmartRoof - AI-Powered Roofing Solutions

## Overview

SmartRoof is a Flask-based e-commerce platform specializing in roofing materials with integrated AI-powered features. The application combines traditional e-commerce functionality with machine learning capabilities for product recommendations, sentiment analysis, and an AI chat assistant. The system is designed as an MVP using in-memory data storage for rapid prototyping and demonstration purposes.

## System Architecture

The application follows a traditional Flask MVC architecture with the following key components:

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap 5 dark theme
- **JavaScript**: Vanilla JavaScript with separate modules for chat functionality, roof calculator, and main application logic
- **Styling**: Custom CSS with responsive design using Bootstrap framework
- **Icons**: Feather Icons for consistent UI elements

### Backend Architecture
- **Framework**: Flask with Flask-Login for authentication
- **Data Storage**: In-memory dictionaries for MVP functionality (users, products, orders, reviews, cart_items)
- **Machine Learning**: Scikit-learn integration for product recommendations and sentiment analysis
- **NLP**: NLTK VADER sentiment analyzer for review processing

### Authentication System
- Flask-Login for session management
- Password hashing using Werkzeug security utilities
- Role-based access control (admin/customer roles)
- Pre-configured admin account for demonstration

## Key Components

### Core Models
- **User**: Handles user authentication, profile management, and role assignment
- **Product**: Manages product catalog with categories, pricing, and inventory
- **Order**: Tracks customer orders with items and status management
- **Review**: Customer feedback system (referenced but not fully implemented)
- **CartItem**: Shopping cart functionality

### Machine Learning Features
- **SentimentAnalyzer**: NLTK-based sentiment analysis for customer reviews
- **ProductRecommender**: TF-IDF vectorization with cosine similarity for product recommendations
- **AI Chat Assistant**: Placeholder for intelligent customer service bot

### Administrative Features
- Comprehensive admin dashboard with analytics
- User management and segmentation
- Product catalog management
- Order tracking and status updates
- Revenue reporting and sentiment analysis visualization

## Data Flow

1. **User Registration/Authentication**: Users register and authenticate through Flask-Login
2. **Product Browsing**: Customers browse products with filtering and search capabilities
3. **Shopping Cart**: Items are added to in-memory cart storage linked to user sessions
4. **Checkout Process**: Multi-step checkout with shipping and payment information collection
5. **Order Processing**: Orders are stored with status tracking capabilities
6. **AI Features**: Product recommendations and chat interactions processed through ML models
7. **Admin Analytics**: Dashboard aggregates data for business intelligence reporting

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing and security utilities
- **scikit-learn**: Machine learning algorithms for recommendations
- **NLTK**: Natural language processing for sentiment analysis
- **NumPy/Pandas**: Data manipulation and analysis

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Feather Icons**: Icon library for consistent UI
- **Chart.js**: Data visualization for admin analytics

### Development Tools
- **Logging**: Built-in Python logging for debugging
- **Environment Variables**: Configuration management for sensitive data

## Deployment Strategy

The application is configured for development deployment with the following characteristics:

### Development Configuration
- Debug mode enabled for development
- Host configured for 0.0.0.0 to allow external connections
- Port 5000 as default Flask development server
- In-memory storage suitable for demonstration and testing

### Production Considerations
- Environment-based secret key configuration
- Logging system ready for production scaling
- Architecture supports easy migration to persistent database storage
- Admin panel provides necessary management capabilities

### Scalability Notes
- Current in-memory storage should be replaced with database (likely PostgreSQL with Drizzle ORM)
- ML models can be enhanced with more sophisticated algorithms
- Chat functionality can be integrated with external AI services
- File upload capabilities can be added for product images

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **June 28, 2025**: Fixed all form processing issues
  - Updated roof calculator JavaScript to prevent buttons getting stuck in processing state
  - Added proper loading states and immediate button restoration for login/register forms  
  - Fixed SQLite database integration and removed PostgreSQL dependencies
  - All forms now submit properly without eternal processing states
  - Currency display updated to RWF throughout the application

## Changelog

- June 28, 2025: Initial setup with complete e-commerce platform
- June 28, 2025: Fixed processing issues in all forms (calculator, login, register)
from app import app
import database  # Initialize SQLite database

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

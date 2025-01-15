from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from recommender import ContextAwareBookRecommender
from database import DatabaseManager
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize database and recommender
try:
    db_manager = DatabaseManager()
    books_data = db_manager.get_all_books()
    logger.info(f"Successfully loaded {len(books_data)} books from database")
    
    if not books_data:
        raise ValueError("No books found in database")
        
    # Initialize recommender with books data
    recommender = ContextAwareBookRecommender(books_data)
    logger.info("Recommender system initialized successfully")
    
except Exception as e:
    logger.error(f"Critical error: {str(e)}")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_recommendation', methods=['POST'])
def get_recommendation():
    try:
        data = request.json
        query = data.get('query')
        logger.info(f"Request received with data: {data}")
        
        if not query:
            logger.warning("No query provided in request")
            return jsonify({'error': 'No query provided'}), 400
        
        logger.info(f"Processing query: {query}")
        
        # Get context and recommendations
        context = recommender.get_context()
        logger.info(f"Context retrieved: {context[:100]}...")
        
        similar_books = recommender.get_similar_books(query)
        logger.info(f"Found {len(similar_books)} similar books")
        
        response = recommender.generate_response(query, similar_books, context)
        logger.info(f"Generated response: {response[:100]}...")
        
        # Update conversation history
        recommender.update_conversation_history(query, response)
        logger.info("Conversation history updated")
        
        result = {
            'response': response,
            'recommendations': similar_books[:4]
        }
        logger.info("Sending response back to client")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_recommendation: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'response': """<div class="message-paragraph">I apologize, but I'm having trouble 
            processing your request. Please try again.</div>""",
            'recommendations': []
        }), 500

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    try:
        chat_id = request.args.get('chat_id')
        # Here you could add database integration for permanent storage
        return jsonify({'success': True, 'history': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_chat', methods=['POST'])
def save_chat():
    try:
        chat_data = request.json
        # Here you could add database integration
        # For example with SQLAlchemy:
        # new_chat = Chat(
        #     chat_id=chat_data['id'],
        #     messages=chat_data['messages']
        # )
        # db.session.add(new_chat)
        # db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
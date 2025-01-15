import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
from typing import List, Dict
import re
import random
import logging
import os

# Add at the top of the file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextAwareBookRecommender:
    def __init__(self, books_data: List[Dict]):
        try:
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            self.books_data = self.clean_book_data(books_data)
            self.embeddings = None
            self.index = None
            logger.info("Initializing embeddings for database...")
            self.initialize_embeddings()
            
            # Verify API key before initializing Gemini
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            
            # Test API connection
            test_response = self.gemini_model.generate_content("Test connection")
            if not test_response:
                raise ValueError("Failed to connect to Gemini API")
            
            self.conversation_history = []
            self.conversation_summaries = []
            logger.info("Recommender system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing recommender: {str(e)}")
            raise

    def clean_book_data(self, books_data: List[Dict]) -> List[Dict]:
        """Clean and validate book data"""
        cleaned_data = []
        for book in books_data:
            try:
                # Ensure all fields are strings
                cleaned_book = {
                    'book_name': str(book.get('book_name', '')).strip(),
                    'summaries': str(book.get('summaries', '')).strip(),
                    'categories': str(book.get('categories', '')).strip()
                }
                
                # Only add books with valid data
                if cleaned_book['book_name'] and cleaned_book['summaries']:
                    cleaned_data.append(cleaned_book)
                
            except Exception as e:
                print(f"Skipping invalid book: {str(e)}")
                continue
                
        print(f"Cleaned {len(cleaned_data)} valid books")
        return cleaned_data

    def initialize_embeddings(self):
        # Create embeddings for all book summaries
        try:
            summaries = [book['summaries'] for book in self.books_data]
            if not summaries:
                raise ValueError("No valid book summaries found")
                
            self.embeddings = self.model.encode(summaries)
            
            # Initialize FAISS index
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings.astype('float32'))
            
            print(f"Successfully created embeddings for {len(summaries)} books")
            
        except Exception as e:
            print(f"Error creating embeddings: {str(e)}")
            raise
        
    def preprocess_query(self, query: str) -> str:
        # Clean and normalize query
        query = re.sub(r'[^\w\s]', '', query.lower())
        return query
        
    def get_similar_books(self, query: str, k: int = 5) -> List[Dict]:
        query = self.preprocess_query(query)
        query_vector = self.model.encode([query])
        
        # Get more candidates initially for better filtering
        distances, indices = self.index.search(query_vector.astype('float32'), k * 2)
        
        # Get unique recommendations considering both content and categories
        seen_books = set()
        similar_books = []
        
        for idx, distance in zip(indices[0], distances[0]):
            book = self.books_data[idx]
            if book['book_name'] not in seen_books and len(similar_books) < k:
                seen_books.add(book['book_name'])
                similar_books.append({
                    'title': book['book_name'],
                    'summary': book['summaries'],
                    'category': book['categories'],
                    'similarity_score': float(1 / (1 + distance))
                })
        
        # Sort by similarity score
        similar_books.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_books

    def estimate_reading_time(self, text: str) -> str:
        words = len(text.split())
        minutes = round(words / 200)  # Average reading speed
        return f"{minutes} min read"

    def extract_themes(self, summary: str) -> List[str]:
        # Use Gemini to extract themes
        prompt = f"Extract 3 main themes from this book summary in 1-2 words each: {summary}"
        response = self.gemini_model.generate_content(prompt)
        themes = response.text.split('\n')
        return [theme.strip() for theme in themes if theme.strip()]

    def get_context(self) -> str:
        # Return the last few conversation summaries as context
        return " ".join(self.conversation_summaries[-3:]) if self.conversation_summaries else ""

    def update_conversation_history(self, query: str, response: str):
        # Add to conversation history
        self.conversation_history.append({
            'query': query,
            'response': response
        })
        
        # Generate a summary if we have enough history
        if len(self.conversation_history) % 3 == 0:
            recent_conv = self.conversation_history[-3:]
            summary_prompt = f"Summarize this conversation about book recommendations:\n"
            for conv in recent_conv:
                summary_prompt += f"User: {conv['query']}\nAssistant: {conv['response']}\n"
            
            summary_response = self.gemini_model.generate_content(summary_prompt)
            self.conversation_summaries.append(summary_response.text)

    def check_if_allowed_query(self, query: str) -> str:
        # Only allow these types of queries
        allowed_patterns = {
            'book_related': [
                r'\b(book|books|novel|novels|read|reading|literature)\b',
                r'\b(recommend|recommendation|suggestions?)\b',
                r'\b(fantasy|fiction|romance|mystery|thriller|sci-fi|biography)\b',
                r'\b(author|writer|series)\b',
                r'\blike\s+.*\b',  # For queries like "like Harry Potter"
                r'\bsimilar to\b'
            ],
            'gratitude': [
                r'\b(thanks?|thank you|thx|ty|appreciate)\b'
            ],
            'basic_greeting': [
                r'^(hi|hello|hey)$',
                r'^how are you\??$'
            ],
            'farewell': [
                r'\b(goodbye|bye|see you|farewell|cya|take care)\b',
                r'\bhave a (good|great|nice) (day|evening|night)\b',
                r'\bsee you later\b',
                r'\buntil next time\b'
            ]
        }
        
        query_lower = query.lower()
        
        # Check farewell first
        if any(re.search(pattern, query_lower) for pattern in allowed_patterns['farewell']):
            return 'farewell'
        
        # Check gratitude
        if any(re.search(pattern, query_lower) for pattern in allowed_patterns['gratitude']):
            return 'gratitude'
        
        # Check basic greetings
        if any(re.search(pattern, query_lower) for pattern in allowed_patterns['basic_greeting']):
            return 'greeting'
        
        # Check if it's book related
        if any(re.search(pattern, query_lower) for pattern in allowed_patterns['book_related']):
            return 'book'
        
        return 'invalid'

    def generate_response(self, query: str, similar_books: List[Dict], context: str) -> str:
        query_type = self.check_if_allowed_query(query)
        
        # Handle different query types
        if query_type == 'invalid':
            return """<div class="message-paragraph">I'm specialized in book recommendations only. 
            Please ask me about books, and I'll be happy to help you find your next great read!</div>"""
        
        if query_type == 'gratitude':
            return """<div class="message-paragraph">You're welcome! I'm always happy to help you discover great books. 
            Feel free to ask for more recommendations anytime!</div>"""
        
        if query_type == 'greeting':
            return """<div class="message-paragraph">Hello! I'm excited to help you discover some amazing books. 
            What kind of books would you like to explore today?</div>"""
        
        if query_type == 'farewell':
            farewell_responses = [
                """<div class="message-paragraph">Goodbye! Happy reading! 📚</div>""",
                """<div class="message-paragraph">Take care! Come back for more book recommendations! 📖</div>"""
            ]
            return random.choice(farewell_responses)
        
        # Handle book-related query
        try:
            if not similar_books:
                return """<div class="message-paragraph">I couldn't find any books matching your request. 
                Could you try rephrasing or specifying a different genre?</div>"""
            
            # Create a focused prompt that enforces using only the provided books
            prompt = f"""
            You are a book recommender. ONLY recommend books from the following list. DO NOT mention or suggest any books not in this list:

            {self._format_matched_books(similar_books)}

            For the query "{query}", create a response following these STRICT rules:
            1. Start with a brief greeting
            2. ONLY recommend books from the above list
            3. For each recommended book, include:
               - Exact title as shown above
               - Category as shown above
               - Brief description using ONLY the provided summary
            4. Use conversational language
            5. End with a question about their reading preferences

            IMPORTANT: 
            - NEVER mention or suggest books not in the provided list
            - Use EXACT titles and categories as shown
            - Base descriptions ONLY on the provided summaries
            """
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            if response and response.text:
                # Verify that only books from our dataset are mentioned
                response_text = response.text
                book_titles = [book['title'] for book in similar_books]
                
                # Format response with verified book titles in bold
                for title in book_titles:
                    response_text = response_text.replace(title, f"<b>{title}</b>")
                
                formatted_response = f"""<div class="message-paragraph">{response_text}</div>"""
                return formatted_response
            else:
                return self._format_fallback_response(query, similar_books)
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._format_fallback_response(query, similar_books)

    def _format_matched_books(self, books: List[Dict]) -> str:
        """Format books for AI prompt with strict structure"""
        if not books:
            return "No matching books found."
        
        formatted = "AVAILABLE BOOKS FOR RECOMMENDATION:\n\n"
        for i, book in enumerate(books, 1):
            formatted += f"""
            Book #{i}:
            Title: {book['title']}
            Category: {book['category']}
            Summary: {book['summary']}
            ----------------------------------------
            """
        return formatted

    def _format_available_books(self) -> str:
        # Create a formatted string of all available books
        available_books = ""
        for _, row in self.books_data.iterrows():
            available_books += f"""
            Book: {row['book_name']}
            Category: {row['categories']}
            Summary: {row['summaries']}
            ---
            """
        return available_books

    def check_if_general_conversation(self, query: str) -> bool:
        # Enhanced conversation patterns
        conversation_patterns = {
            'greetings': [
                r'\b(hi|hello|hey|howdy|greetings|good\s*(morning|afternoon|evening))\b',
                r'\bhi\s+there\b',
                r'^hey\s+',
            ],
            'gratitude': [
                r'\b(thanks|thank you|thx|ty|appreciate|grateful)\b',
                r'that\'s? (helpful|great|awesome|perfect)',
            ],
            'farewell': [
                r'\b(bye|goodbye|see you|cya|farewell)\b',
                r'have a (good|great|nice) (day|evening|night)',
            ],
            'acknowledgment': [
                r'\b(yes|yeah|yep|sure|okay|ok|alright|got it)\b',
                r'\b(no|nope|nah|not really)\b',
                r'\b(maybe|perhaps|possibly)\b',
            ],
            'confusion': [
                r'\b(what|huh|don\'t understand|confused|unclear)\b',
                r'\bcan you (explain|clarify)\b',
            ]
        }
        
        query_lower = query.lower()
        for category, patterns in conversation_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                return category
        return None

    def handle_general_conversation(self, query: str) -> str:
        conversation_type = self.check_if_general_conversation(query)
        query_lower = query.lower()

        responses = {
            'greetings': [
                """<div class="greeting">Hello! I'm excited to help you discover some great books! What kinds of stories or topics interest you?</div>""",
                """<div class="greeting">Hi there! Ready to explore some amazing books together? Tell me what you enjoy reading!</div>""",
                """<div class="greeting">Hey! I'm your friendly book guide. What sort of books have you been enjoying lately?</div>"""
            ],
            'gratitude': [
                """<div class="greeting">You're welcome! I love sharing book recommendations. Would you like to explore more similar books?</div>""",
                """<div class="greeting">Glad I could help! Let me know if you'd like to discover more books in this genre or try something different!</div>""",
                """<div class="greeting">Happy to help! There are so many more great books to explore. What interests you next?</div>"""
            ],
            'farewell': [
                """<div class="greeting">Goodbye! Happy reading! Come back anytime for more book recommendations!</div>""",
                """<div class="greeting">Take care! I hope you enjoy your reading adventures. Feel free to return for more suggestions!</div>"""
            ],
            'acknowledgment': {
                'positive': [
                    """<div class="greeting">Great! Would you like me to suggest more books like these?</div>""",
                    """<div class="greeting">Excellent! Shall we explore some similar titles or try a different genre?</div>"""
                ],
                'negative': [
                    """<div class="greeting">No problem! Let's try something different. What other types of books interest you?</div>""",
                    """<div class="greeting">That's okay! Help me understand what you're looking for - what kinds of stories do you usually enjoy?</div>"""
                ],
                'uncertain': [
                    """<div class="greeting">Take your time! We can explore different options. What aspects of books matter most to you?</div>""",
                    """<div class="greeting">Let's figure this out together! What kinds of books have you enjoyed in the past?</div>"""
                ]
            },
            'confusion': [
                """<div class="greeting">Let me clarify! What specific part would you like me to explain better?</div>""",
                """<div class="greeting">I'll be happy to explain more clearly. Which part is unclear?</div>"""
            ]
        }

        if conversation_type == 'acknowledgment':
            if any(word in query_lower for word in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok']):
                return random.choice(responses['acknowledgment']['positive'])
            elif any(word in query_lower for word in ['no', 'nope', 'nah']):
                return random.choice(responses['acknowledgment']['negative'])
            else:
                return random.choice(responses['acknowledgment']['uncertain'])
        
        return random.choice(responses.get(conversation_type, [
            """<div class="greeting">I'm here to help you find great books! What kinds of books interest you?</div>"""
        ]))

    def is_non_book_query(self, query: str) -> bool:
        # Enhanced detection for non-book queries
        non_book_patterns = {
            'how_to': [
                r'\bhow to\b.*',
                r'\bhow do\b.*',
                r'\bsteps to\b.*',
                r'\bguide to\b.*(?!book|reading|literature)',
            ],
            'general_topics': [
                r'\b(build|create|make|construct)\b(?!.*book)',
                r'\b(food|recipe|cooking)\b',
                r'\b(sports?|team|player)\b',
                r'\b(news|weather)\b',
                r'\b(math|calculator)\b',
                r'\b(movie|film|tv|show|game|music|podcast)\b'
            ]
        }
        
        query_lower = query.lower()
        
        # Check if query matches any non-book pattern
        for category, patterns in non_book_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                return True
            
        return False

    def format_response(self, raw_response: str, similar_books: List[Dict]) -> str:
        formatted_response = raw_response
        
        # Format only book titles with styling
        for book in similar_books:
            # Use word boundaries to ensure we match complete titles
            formatted_response = re.sub(
                fr'\b{re.escape(book["title"])}\b',
                f'<span class="book-title">{book["title"]}</span>',
                formatted_response
            )
        
        # Simple paragraph formatting without extra styling
        paragraphs = formatted_response.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if para.strip():  # Only add non-empty paragraphs
                formatted_paragraphs.append(f'<div class="message-paragraph">{para}</div>')
        
        return '\n'.join(formatted_paragraphs)

    def is_context_question(self, query: str) -> bool:
        # Enhanced patterns for better context question detection
        context_patterns = [
            # Direct context questions
            r'\b(what|tell me|show).*(context|conversation|talking about|discussed)\b',
            r'\b(summarize|summary|recap).*(conversation|chat|discussion)\b',
            r'\bwhat.*(we|you).*(talking|discussed|said|recommended)\b',
            # Indirect context questions
            r'\bcan you.*(remind|tell).*(what|about).*(discussed|said)\b',
            r'\bwhere.*(we|conversation).*left off\b',
            r'\b(refresh|update).*(memory|me)\b',
            # Topic-specific context
            r'\bwhat.*(books|recommendations).*(mentioned|suggested)\b',
            r'\bwhich.*(genres|topics).*(discussed|covered)\b'
        ]
        return any(re.search(pattern, query.lower()) for pattern in context_patterns)

    def handle_context_question(self, query: str) -> str:
        if not self.conversation_history:
            return """<div class="greeting">We haven't had any conversation yet. Feel free to ask about any books you're interested in!</div>"""
        
        # Get only recent relevant conversations
        recent_conversations = self.conversation_history[-3:] if len(self.conversation_history) > 3 else self.conversation_history
        
        # Create an extremely strict context analysis prompt
        summary_prompt = """STRICT CONVERSATION SUMMARY RULES:

        1. List EXACTLY what happened in chronological order
        2. Use this EXACT format for each exchange:
           "User asked: [exact question]
            AI recommended: [exact books recommended]"
        3. NO interpretations or assumptions
        4. NO additional suggestions
        5. ONLY include what was EXPLICITLY said

        If the conversation just started, say EXACTLY:
        "This is the start of our conversation. You just asked: [current question]"
        """
        
        # Add exact conversation history with clear markers
        summary_prompt += "\n\nCONVERSATION LOG:\n"
        for i, conv in enumerate(recent_conversations, 1):
            summary_prompt += f"""
            Exchange {i}:
            ===
            User's exact words: "{conv['query']}"
            ---
            AI's exact response: "{conv['response']}"
            ===
            """
        
        try:
            # Generate strict summary
            response = self.gemini_model.generate_content(summary_prompt)
            summary = response.text.strip()
            
            # Extra verification step
            verification_prompt = f"""
            VERIFY STRICT ACCURACY:
            
            Original conversation:
            {summary_prompt}
            
            Generated summary:
            {summary}
            
            CHECK:
            1. Are ALL exchanges listed EXACTLY as they happened?
            2. Are ONLY actual books mentioned?
            3. Is there ANY speculation or extra information?
            4. Is the format EXACTLY as specified?
            
            If ANY issues found, provide EXACT correction.
            Start with "CORRECTION NEEDED:" if changes required.
            """
            
            verification = self.gemini_model.generate_content(verification_prompt)
            if "CORRECTION NEEDED:" in verification.text:
                final_summary = verification.text.split("CORRECTION NEEDED:")[1].strip()
            else:
                final_summary = summary
            
            return f"""<div class="greeting">
                <div class="recommendation-section">
                    <h3>Conversation History:</h3>
                    {final_summary}
                </div>
            </div>"""
            
        except Exception as e:
            print(f"Error in context summary: {str(e)}")
            return """<div class="greeting">I'm having trouble accessing our conversation history. Would you like to start fresh?</div>"""

    def format_topic_suggestions(self, topics: List[str]) -> str:
        """Format topic suggestions as bullet points"""
        formatted_topics = []
        for topic in topics:
            topic = topic.strip('- ').strip()
            if topic:
                formatted_topics.append(f'<div class="bullet-point">{topic}</div>')
        return '\n'.join(formatted_topics)

    def _format_simple_recommendations(self, books: List[Dict]) -> str:
        """Format a simple response when AI fails"""
        if not books:
            return "No matching books found."
        
        formatted = "\n\n"
        for i, book in enumerate(books[:5], 1):
            formatted += f"{i}. {book['title']} ({book['category']})\n"
        return formatted 

    def _format_fallback_response(self, query: str, books: List[Dict]) -> str:
        """Create a simple response when AI generation fails"""
        response = f"""<div class="message-paragraph">
        Based on your interest in {query}, here are some relevant books from our collection:\n\n"""
        
        for i, book in enumerate(books[:4], 1):
            response += f"{i}. <b>{book['title']}</b> ({book['category']})\n"
        
        response += "\nWould you like to know more about any of these specific books?</div>"
        return response 
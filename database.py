from pymongo import MongoClient
from typing import List, Dict
import os
from dotenv import load_dotenv
import certifi

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        
        # Get MongoDB connection string from environment variables
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
            
        # Initialize MongoDB client with SSL certificate
        self.client = MongoClient(mongodb_uri, tlsCAFile=certifi.where())
        self.db = self.client['book_recommender']
        self.books_collection = self.db['books']
        
        # Test connection
        try:
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas!")
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            raise
        
    def get_all_books(self) -> List[Dict]:
        """Retrieve all books from database with validation"""
        try:
            books = list(self.books_collection.find({}, {'_id': 0}))
            valid_books = []
            
            for book in books:
                if all(key in book for key in ['book_name', 'summaries', 'categories']):
                    valid_books.append(book)
                    
            print(f"Retrieved {len(valid_books)} valid books from database")
            return valid_books
            
        except Exception as e:
            print(f"Error retrieving books: {str(e)}")
            return []
        
    def add_book(self, book: Dict) -> bool:
        """Add a new book to database"""
        try:
            self.books_collection.insert_one(book)
            return True
        except Exception as e:
            print(f"Error adding book: {str(e)}")
            return False
            
    def add_many_books(self, books: List[Dict]) -> bool:
        """Add multiple books to database with duplicate checking"""
        try:
            # Check for duplicates before inserting
            unique_books = []
            seen_titles = set()
            
            for book in books:
                if book['book_name'] not in seen_titles:
                    seen_titles.add(book['book_name'])
                    unique_books.append(book)
            
            if unique_books:
                self.books_collection.insert_many(unique_books)
                print(f"Added {len(unique_books)} unique books")
                return True
            return False
            
        except Exception as e:
            print(f"Error adding books: {str(e)}")
            return False
            
    def search_books(self, query: Dict) -> List[Dict]:
        """Search books with specific criteria"""
        return list(self.books_collection.find(query, {'_id': 0}))
        
    def update_book(self, book_name: str, updates: Dict) -> bool:
        """Update a book's information"""
        try:
            self.books_collection.update_one(
                {'book_name': book_name},
                {'$set': updates}
            )
            return True
        except Exception as e:
            print(f"Error updating book: {str(e)}")
            return False 

    def clear_collection(self) -> bool:
        """Clear the books collection"""
        try:
            self.books_collection.delete_many({})
            return True
        except Exception as e:
            print(f"Error clearing collection: {str(e)}")
            return False 
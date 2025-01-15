from database import DatabaseManager
from recommender import ContextAwareBookRecommender

def test_system():
    try:
        # Test database
        db = DatabaseManager()
        books = db.get_all_books()
        print(f"Found {len(books)} books in database")
        
        if len(books) > 0:
            print("\nSample book:")
            print(f"Title: {books[0]['book_name']}")
            print(f"Category: {books[0]['categories']}")
            
        # Test recommender
        recommender = ContextAwareBookRecommender(books)
        test_query = "fantasy books"
        results = recommender.get_similar_books(test_query)
        
        print(f"\nTest query: '{test_query}'")
        print(f"Found {len(results)} recommendations")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_system() 
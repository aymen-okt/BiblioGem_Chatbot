from database import DatabaseManager
from recommender import ContextAwareBookRecommender

def test_recommendations():
    try:
        # Initialize
        db = DatabaseManager()
        books = db.get_all_books()
        recommender = ContextAwareBookRecommender(books)
        
        # Test queries
        test_queries = [
            "fantasy books",
            "science fiction novels",
            "romance books",
            "mystery thrillers"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            similar_books = recommender.get_similar_books(query)
            response = recommender.generate_response(query, similar_books, "")
            print("\nResponse:")
            print(response)
            print("\n" + "="*50)
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_recommendations() 
from database import DatabaseManager
import pandas as pd

def validate_database():
    try:
        db = DatabaseManager()
        books = db.get_all_books()
        
        print("\nData Validation Report:")
        print("-----------------------")
        print(f"Total books: {len(books)}")
        
        # Check for missing or invalid values
        missing_titles = sum(1 for book in books if not book.get('book_name'))
        missing_summaries = sum(1 for book in books if not book.get('summaries'))
        missing_categories = sum(1 for book in books if not book.get('categories'))
        
        print(f"\nMissing Values:")
        print(f"- Titles: {missing_titles}")
        print(f"- Summaries: {missing_summaries}")
        print(f"- Categories: {missing_categories}")
        
        # Check data types
        invalid_titles = sum(1 for book in books if not isinstance(book.get('book_name', ''), str))
        invalid_summaries = sum(1 for book in books if not isinstance(book.get('summaries', ''), str))
        invalid_categories = sum(1 for book in books if not isinstance(book.get('categories', ''), str))
        
        print(f"\nInvalid Data Types:")
        print(f"- Titles: {invalid_titles}")
        print(f"- Summaries: {invalid_summaries}")
        print(f"- Categories: {invalid_categories}")
        
    except Exception as e:
        print(f"Validation failed: {str(e)}")

if __name__ == "__main__":
    validate_database() 
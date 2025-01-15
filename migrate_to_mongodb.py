import pandas as pd
from database import DatabaseManager

def migrate_csv_to_mongodb():
    try:
        # Read CSV file
        df = pd.read_csv("D:\\books_summary.csv")
        
        # Clean up DataFrame
        if 'Unnamed: 0.1' in df.columns:
            df = df.drop('Unnamed: 0.1', axis=1)
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
            
        # Remove duplicates
        df = df.drop_duplicates(subset=['book_name'], keep='first')
        
        print(f"Found {len(df)} unique books in CSV")
            
        # Convert DataFrame to list of dictionaries
        books = df.to_dict('records')
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Clear existing collection
        db_manager.clear_collection()
        print("Cleared existing collection")
        
        # Add books to MongoDB
        success = db_manager.add_many_books(books)
        
        if success:
            print(f"Successfully migrated {len(books)} books to MongoDB Atlas")
            print("Database: book_recommender")
            print("Collection: books")
        else:
            print("Migration failed")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    migrate_csv_to_mongodb() 
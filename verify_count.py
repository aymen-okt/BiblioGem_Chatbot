from database import DatabaseManager
import pandas as pd

def verify_book_counts():
    try:
        # Check CSV count
        df = pd.read_csv("D:\\books_summary.csv")
        df = df.drop_duplicates(subset=['book_name'], keep='first')
        csv_count = len(df)
        print(f"Unique books in CSV: {csv_count}")
        
        # Check MongoDB count
        db = DatabaseManager()
        mongo_books = db.get_all_books()
        mongo_count = len(mongo_books)
        print(f"Books in MongoDB: {mongo_count}")
        
        # Verify counts match
        if csv_count == mongo_count:
            print("✅ Counts match!")
        else:
            print("❌ Count mismatch!")
            print(f"Difference: {abs(csv_count - mongo_count)}")
            
    except Exception as e:
        print(f"Verification failed: {str(e)}")

if __name__ == "__main__":
    verify_book_counts() 
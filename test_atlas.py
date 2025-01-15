from database import DatabaseManager

def test_connection():
    try:
        db = DatabaseManager()
        books = db.get_all_books()
        print(f"Connected successfully! Found {len(books)} books.")
    except Exception as e:
        print(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection() 
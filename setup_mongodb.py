from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

def setup_mongodb():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in .env file")
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        
        # Create/access the database
        db = client.book_recommender
        
        # Create books collection if it doesn't exist
        if 'books' not in db.list_collection_names():
            db.create_collection('books')
            print("Created 'books' collection")
        
        # Test the connection
        client.server_info()
        print("\n✅ MongoDB Connection Successful!")
        print(f"Database URI: {mongodb_uri}")
        print(f"Available databases: {client.list_database_names()}")
        print(f"Collections in book_recommender: {db.list_collection_names()}")
        
    except Exception as e:
        print(f"\n❌ MongoDB Setup Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure MongoDB is installed")
        print("2. Verify MongoDB service is running:")
        print("   - Open Services (services.msc)")
        print("   - Look for 'MongoDB Server'")
        print("   - Status should be 'Running'")
        print("3. Check if MongoDB is running on port 27017")
        sys.exit(1)

if __name__ == "__main__":
    print("Setting up MongoDB...")
    setup_mongodb() 
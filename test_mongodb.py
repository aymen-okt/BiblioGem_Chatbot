from pymongo import MongoClient
from dotenv import load_dotenv
import os

def test_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in .env file")
            
        # Try to connect
        client = MongoClient(mongodb_uri)
        
        # Test the connection
        client.server_info()
        
        print("Successfully connected to MongoDB!")
        print(f"Database URI: {mongodb_uri}")
        
        # List available databases
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
    except Exception as e:
        print(f"Connection error: {str(e)}")

if __name__ == "__main__":
    test_connection() 
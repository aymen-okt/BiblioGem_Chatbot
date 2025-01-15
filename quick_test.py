from pymongo import MongoClient
import sys

def test_mongo():
    try:
        # Try direct connection with new port
        client = MongoClient('mongodb://127.0.0.1:27018/')
        
        # Test connection
        client.admin.command('ping')
        
        print("✅ MongoDB is running!")
        print("Available databases:", client.list_database_names())
        
    except Exception as e:
        print("❌ Connection failed:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    test_mongo() 
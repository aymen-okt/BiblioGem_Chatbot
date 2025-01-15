import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_api():
    try:
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-pro')
        
        # Test simple query
        response = model.generate_content("Say hello!")
        
        print("API Test Results:")
        print("----------------")
        print(f"API Key: {api_key[:10]}...")
        print(f"Response: {response.text}")
        print("\n✅ API key is working!")
        
    except Exception as e:
        print("\n❌ API Error:")
        print(str(e))
        print("\nPlease make sure:")
        print("1. You have a valid API key from https://makersuite.google.com/app/apikey")
        print("2. The API key is correctly set in your .env file")
        print("3. You have enabled the Gemini API for your project")

if __name__ == "__main__":
    test_api() 
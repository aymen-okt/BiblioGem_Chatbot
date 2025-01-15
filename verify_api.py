import os
from dotenv import load_dotenv
import google.generativeai as genai

def verify_api_key():
    try:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ API key not found in .env file")
            return
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("Test connection")
        print("✅ API key is valid!")
        print("Test response:", response.text)
        
    except Exception as e:
        print(f"❌ API key verification failed: {str(e)}")

if __name__ == "__main__":
    verify_api_key() 
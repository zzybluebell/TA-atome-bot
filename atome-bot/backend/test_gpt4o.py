from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"Testing API Key: {api_key[:10]}...{api_key[-5:]}")

try:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    print("Attempting to invoke gpt-4o...")
    response = llm.invoke("Hello, are you running on gpt-4o?")
    print("\n--- Response ---")
    print(response.content)
    print("\n--- Success ---")
except Exception as e:
    print("\n--- Error ---")
    print(e)

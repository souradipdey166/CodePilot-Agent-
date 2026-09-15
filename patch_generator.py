import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

def call_llm(prompt: str) -> str:
    for attempt in range(3):

        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                wait = 65
                print(f"Rate limited, waiting {wait}s before retry {attempt + 1}/3...")
                time.sleep(wait)
                continue

            print("=== GROQ API ERROR ===")
            print("Error:", error_str)
            raise RuntimeError(f"Groq API call failed: {error_str}")

    raise RuntimeError("Rate limit retries exhausted after 3 attempts")
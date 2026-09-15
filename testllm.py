from dotenv import load_dotenv
load_dotenv()

import os
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

result = llm.invoke('1 line one black hole')
print(result.content)
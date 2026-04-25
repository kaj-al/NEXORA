import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

llm = ChatOpenAI(model="openai/gpt-4o-mini",api_key=os.getenv("OPENROUTER_API_KEY"),base_url=os.getenv("OPENROUTER_BASE_URL"),temperature=0.5)

class convo:
    def __init__(self):
        self.history = []
    
    def add_user(self,message):
        self.history.append(HumanMessage(content=message))
    
    def add_ai(self,message):
        self.history.append(AIMessage(content=message))

    def get_history(self):
        return self.history
    
    def clear(self):
        self.history = []

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
"""
You are an AI Learning Coach.
Process:
1. Explain the concept simply but thoroughly.
2. Give a small real-world example.
3. Ask ONE multiple choice quiz question according to the explanation you provided.
4. Wait for student answer.
5. If correct then appreciate and give slightly harder question.
6. If wrong then explain again simply.

Always respond in the selected language or the language mentioned in input by the user.
"""
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "Topic or answer: {input}\nLanguage: {language}")
])

chain = prompt | llm

def get_response(user_input, language, memory):
    response = chain.invoke({
        "input": user_input,
        "language": language,
        "chat_history": memory.get_history()
    })
    memory.add_user(user_input)
    memory.add_ai(response.content)
    return response.content


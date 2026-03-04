from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.retriever import create_retriever_tool
from app.tools import check_application_status, check_transaction_status
from app.vector_store import VectorStoreManager
from app.crawler import AtomeCrawler
from typing import List

class ServiceBot:
    def __init__(self):
        self.model = "gpt-4o"
        self.temperature = 0
        self.vector_store_manager = VectorStoreManager()
        self.crawler = AtomeCrawler()
        
        # Default Configuration
        self.knowledge_base_url = "https://help.atome.ph/hc/en-gb/categories/4439682039065-Atome-Card"
        self.additional_guidelines = [
            "If customer is asking about their card application status, call check_application_status tool.",
            "If customer is asking about a failed card transaction, ask for transaction id, then call check_transaction_status tool.",
            "Tell customer about the status clearly."
        ]
        
        # Initialize Agent
        self.agent_executor = None
        self.reload_agent()

    def _build_system_prompt(self):
        guidelines_str = "\n".join([f"- {g}" for g in self.additional_guidelines])
        return f"""You are a helpful customer service AI bot for Atome.

# Knowledge Base
Answer questions based on the retrieved context from the help center. 
If the answer is not in the context, say you don't know, but don't make things up.

# Additional Guidelines
Follow these instructions strictly:
{guidelines_str}

# Tone
Be professional, concise, and helpful.
"""

    def _build_agent_prompt(self):
        system_prompt = self._build_system_prompt()
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def _build_fallback_prompt(self):
        system_prompt = self._build_system_prompt()
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

    def initialize(self):
        """Crawl and populate vector store on startup."""
        print("Initializing knowledge base...")
        docs = self.crawler.crawl(self.knowledge_base_url)
        if docs:
            self.vector_store_manager.clear()
            self.vector_store_manager.add_documents(docs)
        else:
            print("Warning: No documents found during crawl.")

    def update_config(self, url: str = None, guidelines: List[str] = None):
        """Update bot configuration and reload agent."""
        if url and url != self.knowledge_base_url:
            self.knowledge_base_url = url
            # Trigger re-crawl if URL changes
            docs = self.crawler.crawl(url)
            self.vector_store_manager.clear()
            self.vector_store_manager.add_documents(docs)
            
        if guidelines is not None:
            self.additional_guidelines = guidelines
            
        self.reload_agent()

    def reload_agent(self):
        """Re-create the agent with current configuration."""
        try:
            print("Reloading agent...")
            retriever = self.vector_store_manager.as_retriever()
            retriever_tool = None
            if retriever:
                retriever_tool = create_retriever_tool(
                    retriever,
                    "search_atome_help_center",
                    "Searches and returns documents regarding Atome Card FAQs and policies."
                )
            tools = [tool for tool in [retriever_tool, check_application_status, check_transaction_status] if tool]
            print(f"Tools: {tools}")
            
            prompt = self._build_agent_prompt()
            
            llm = ChatOpenAI(model=self.model, temperature=self.temperature)
            agent = create_openai_tools_agent(llm, tools, prompt)
            self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            print("Agent reloaded successfully.")
        except Exception as e:
            print(f"Agent reload failed: {e}")
            self.agent_executor = None

    def chat(self, user_input: str, chat_history: List = None):
        """Process user message."""
        chat_history = chat_history or []
        if not self.agent_executor:
            self.reload_agent()
            
        if not self.agent_executor:
            llm = ChatOpenAI(model=self.model, temperature=self.temperature)
            prompt = self._build_fallback_prompt()
            messages = prompt.format_messages(input=user_input, chat_history=chat_history)
            response = llm.invoke(messages)
            return {"output": response.content}

        return self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })

# Singleton instance
bot_instance = None

def get_bot_instance():
    global bot_instance
    if bot_instance is None:
        bot_instance = ServiceBot()
    return bot_instance

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain.agents import AgentExecutor
except ImportError:
    from langchain_classic.agents import AgentExecutor
try:
    from langchain.agents import create_openai_tools_agent
except ImportError:
    try:
        from langchain_classic.agents import create_openai_tools_agent
    except ImportError:
        from langchain.agents import create_tool_calling_agent as create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
try:
    from langchain.tools.retriever import create_retriever_tool
except ImportError:
    from langchain_core.tools import create_retriever_tool
from app.tools import check_application_status, check_transaction_status
from app.vector_store import VectorStoreManager
from app.crawler import AtomeCrawler
from app.document_reader import DocumentReader
from app.relevance_guard import DocumentRelevanceGuard
from typing import List

class ServiceBot:
    def __init__(self):
        self.model = "gpt-4o"
        self.temperature = 0
        self.vector_store_manager = VectorStoreManager()
        self.crawler = AtomeCrawler()
        self.document_reader = DocumentReader()
        self.relevance_guard = DocumentRelevanceGuard()
        
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

    def update_config(self, url: str = None, guidelines: List[str] = None, force_recrawl: bool = False):
        """Update bot configuration and reload agent."""
        target_url = (url or self.knowledge_base_url).strip()
        should_recrawl = bool(target_url) and (force_recrawl or target_url != self.knowledge_base_url)
        crawled_documents = 0

        if target_url and target_url != self.knowledge_base_url:
            self.knowledge_base_url = target_url

        if should_recrawl:
            docs = self.crawler.crawl(target_url)
            if not docs:
                raise ValueError("No documents found from the knowledge base URL.")
            crawled_documents = len(docs)
            self.vector_store_manager.clear()
            self.vector_store_manager.add_documents(docs)
            
        if guidelines is not None:
            self.additional_guidelines = guidelines
            
        self.reload_agent()
        return {
            "recrawled": should_recrawl,
            "documents_indexed": crawled_documents,
            "knowledge_base_url": self.knowledge_base_url,
        }

    def ingest_documents(self, files: List[tuple[str, bytes]], replace_existing: bool = False):
        documents = []
        failed_files = []
        rejected_files = []
        accepted_files = []

        for file_name, content in files:
            try:
                docs = self.document_reader.read_bytes(file_name, content)
                sample_text = "\n".join(doc.page_content for doc in docs[:8])
                assessment = self.relevance_guard.evaluate(file_name, sample_text)
                if assessment["decision"] != "accepted":
                    rejected_files.append(assessment)
                    continue
                accepted_files.append(assessment)
                documents.extend(docs)
            except Exception as e:
                failed_files.append({"file_name": file_name, "error": str(e)})

        if not documents:
            raise ValueError("No relevant documents were accepted from uploaded files.")

        if replace_existing:
            self.vector_store_manager.clear()

        self.vector_store_manager.add_documents(documents)
        self.reload_agent()

        return {
            "ingested_documents": len(documents),
            "ingested_files": len(accepted_files),
            "accepted_files": accepted_files,
            "rejected_files": rejected_files,
            "failed_files": failed_files,
        }

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

import langchain
import langchain.agents
import sys

print(f"Python: {sys.version}")
print(f"LangChain Version: {langchain.__version__}")
print(f"LangChain Path: {langchain.__file__}")

try:
    from langchain.agents import create_tool_calling_agent
    print("SUCCESS: create_tool_calling_agent found")
except ImportError:
    print("FAILURE: create_tool_calling_agent NOT found")

try:
    from langchain.agents import create_openai_tools_agent
    print("SUCCESS: create_openai_tools_agent found")
except ImportError:
    print("FAILURE: create_openai_tools_agent NOT found")

print("Available in langchain.agents:", dir(langchain.agents))

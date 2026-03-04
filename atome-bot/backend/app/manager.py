from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent import get_bot_instance
from dotenv import load_dotenv

load_dotenv()

class MetaAgent:
    def __init__(self):
        self.model = "gpt-4o"
        self.temperature = 0.2

    def _build_llm(self):
        return ChatOpenAI(model=self.model, temperature=self.temperature)

    def process_manager_instruction(self, instruction: str):
        """
        Interprets manager's instruction to update the bot.
        Returns a summary of what changed.
        """
        # Simple logic: If instruction implies adding a rule, extract it.
        # For complex implementation, this would be another Agent.
        
        prompt = ChatPromptTemplate.from_template(
            """The manager wants to update the customer service bot's guidelines.
            Current guidelines: {current_guidelines}
            
            Manager's instruction: {instruction}
            
            Extract the new rule(s) that should be ADDED or MODIFIED. 
            Return ONLY the new/modified rules as a list of strings, separated by newlines.
            If the instruction is irrelevant, return "NO_CHANGE".
            """
        )
        
        bot_instance = get_bot_instance()
        current_guidelines_str = "\n".join(bot_instance.additional_guidelines)
        
        llm = self._build_llm()
        messages = prompt.format_messages(
            current_guidelines=current_guidelines_str,
            instruction=instruction
        )
        response = llm.invoke(messages)
        
        result = response.content.strip()
        
        if result == "NO_CHANGE":
            new_rules = [instruction.strip()]
        else:
            new_rules = [rule.strip() for rule in result.split('\n') if rule.strip()]

        if not new_rules:
            return "No changes made to guidelines."

        existing = set(bot_instance.additional_guidelines)
        filtered_rules = [rule for rule in new_rules if rule not in existing]

        if not filtered_rules:
            return "No changes made to guidelines."
        # Append new rules
        updated_guidelines = bot_instance.additional_guidelines + filtered_rules
        bot_instance.update_config(guidelines=updated_guidelines)
        
        return f"Updated guidelines with: {filtered_rules}"

    def auto_fix_mistake(self, user_query: str, bot_response: str, user_feedback: str):
        """
        Analyzes a reported mistake and adds a rule to prevent it.
        """
        prompt = ChatPromptTemplate.from_template(
            """A user reported a mistake in the bot's response.
            
            User Query: {user_query}
            Bot Response: {bot_response}
            User Feedback (Correct Answer/Behavior): {user_feedback}
            
            Analyze the error. Formulate a SINGLE, concise guideline rule that would prevent this mistake in the future.
            The rule should be directive (e.g., "If user asks X, do Y").
            Return ONLY the rule.
            """
        )
        
        llm = self._build_llm()
        messages = prompt.format_messages(
            user_query=user_query,
            bot_response=bot_response,
            user_feedback=user_feedback
        )
        response = llm.invoke(messages)
        
        new_rule = response.content.strip()
        
        # Add the new rule
        bot_instance = get_bot_instance()
        updated_guidelines = bot_instance.additional_guidelines + [new_rule]
        bot_instance.update_config(guidelines=updated_guidelines)
        
        return new_rule

meta_agent_instance = MetaAgent()

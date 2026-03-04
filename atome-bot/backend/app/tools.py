import random
from langchain_core.tools import tool

@tool
def check_application_status(user_id: str = "12345") -> str:
    """
    Checks the credit card application status for a given user ID.
    Always returns a mock status for demonstration purposes.
    """
    statuses = ["Pending", "Approved", "Rejected - Credit Score too low", "Under Review"]
    # Deterministic mock based on user_id length to allow consistent testing, 
    # or just random for fun. Let's use random for variety in demo.
    return f"Application Status for User {user_id}: {random.choice(statuses)}"

@tool
def check_transaction_status(transaction_id: str) -> str:
    """
    Checks the status of a specific transaction by its ID.
    Use this when a user asks about a failed transaction.
    """
    reasons = [
        "Failed - Insufficient Funds",
        "Failed - System Error",
        "Failed - Invalid Merchant",
        "Success",
        "Pending"
    ]
    return f"Transaction {transaction_id} Status: {random.choice(reasons)}"

from typing import Dict, Any
from datetime import datetime

class FinanceTool:
    def __init__(self):
        self.approval_url = "https://approval.example.com/request/"
    
    def create_expense(self, description: str, amount: float, currency: str) -> str:
        """Creates a draft expense report entry"""
        return f"Expense report draft created for '{description}' with amount {amount} {currency}. Awaiting approval."
    
    def bank_transfer(self, recipient_account: str, amount: float, currency: str, approval_token: str = None) -> str:
        """Initiates a bank transfer"""
        if approval_token:
            return f"Bank transfer of {amount} {currency} to {recipient_account} initiated with approval token. Processing..."
        else:
            return f"Bank transfer of {amount} {currency} to {recipient_account} initiated. Awaiting manual approval due to missing approval token."

FINANCE_TOOLS = {
    "erp.create_expense": {
        "name": "erp.create_expense",
        "description": "Create an expense report in the ERP system",
        "risk_level": "low",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "description": "Month for the expense report (YYYY-MM)"
                },
                "items": {
                    "type": "array",
                    "description": "List of expense items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "currency": {"type": "string"},
                            "category": {"type": "string"}
                        }
                    }
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "pending_approval", "approved", "rejected"],
                    "description": "Status of the expense report"
                }
            },
            "required": ["month", "items"]
        }
    },
    "bank.transfer": {
        "name": "bank.transfer",
        "description": "Execute a bank transfer",
        "risk_level": "high",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_name": {
                    "type": "string",
                    "description": "Full legal name of the recipient"
                },
                "recipient_account": {
                    "type": "string",
                    "description": "Recipient's bank account number"
                },
                "amount": {
                    "type": "number",
                    "description": "Transfer amount"
                },
                "currency": {
                    "type": "string",
                    "description": "Transfer currency"
                },
                "invoice_id": {
                    "type": "string",
                    "description": "Associated invoice ID"
                },
                "approval_token": {
                    "type": "string",
                    "description": "Approval token from the authorization system"
                }
            },
            "required": ["recipient_name", "recipient_account", "amount", "currency", "invoice_id", "approval_token"]
        }
    }
}

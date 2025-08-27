import json
from typing import Any, Dict, List, Optional

class Query:
    """A class that represents a workflow query"""
    
    def __init__(self, messages=None, tools=None, message_return_type=None, query_text=None, tool_use=None):
        self.messages = messages if messages else []
        self.tools = tools if tools else []
        self.message_return_type = message_return_type
        self.query_text = query_text
        self.tool_use = tool_use if tool_use else []

    @property
    def response_message(self) -> str:
        """Return the query text or the last message content"""
        if self.query_text:
            return str(self.query_text)
        
        if self.messages:
            last_message = self.messages[-1]
            if isinstance(last_message, dict):
                content = last_message.get('content', '')
                return str(content)
        
        return ""

    def __str__(self) -> str:
        """String representation"""
        return self.response_message

    def __repr__(self) -> str:
        """Object representation"""
        return f"Query(text='{self.response_message}')"
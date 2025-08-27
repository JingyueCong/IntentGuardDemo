from typing import List, Dict, Any, Optional

class Query:
    def __init__(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, message_return_type: str = "str"):
        """
        初始化查询对象
        
        Args:
            messages: 消息列表
            tools: 可用工具列表
            message_return_type: 返回消息类型
        """
        self.messages = messages
        self.tools = tools
        self.message_return_type = message_return_type
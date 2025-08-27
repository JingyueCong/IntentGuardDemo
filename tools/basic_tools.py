import os
import requests
import json
from typing import Dict, Any, Optional

class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def run(self, **kwargs) -> str:
        raise NotImplementedError

    def to_dict(self) -> dict:
        """将工具转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }

class SearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_web",
            description="Search the web for information about a topic"
        )
    
    def run(self, query: str) -> str:
        """使用DuckDuckGo搜索信息"""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url)
            data = response.json()
            
            if 'Abstract' in data and data['Abstract']:
                return data['Abstract']
            elif 'RelatedTopics' in data and data['RelatedTopics']:
                return data['RelatedTopics'][0].get('Text', 'No information found')
            else:
                return "No relevant information found"
        except Exception as e:
            return f"Error during search: {str(e)}"

class FileReadTool(Tool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Safely read contents from a file in the allowed directory"
        )
        self.allowed_dir = os.path.join(os.getcwd(), 'safe_files')
        os.makedirs(self.allowed_dir, exist_ok=True)
    
    def run(self, filename: str) -> str:
        """安全地读取文件内容"""
        try:
            # 确保文件路径在允许的目录内
            full_path = os.path.join(self.allowed_dir, filename)
            if not os.path.normpath(full_path).startswith(os.path.normpath(self.allowed_dir)):
                return "Security Error: Attempted to access file outside allowed directory"
            
            if not os.path.exists(full_path):
                return f"File not found: {filename}"
            
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class FileWriteTool(Tool):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Safely write content to a file in the allowed directory"
        )
        self.allowed_dir = os.path.join(os.getcwd(), 'safe_files')
        os.makedirs(self.allowed_dir, exist_ok=True)
    
    def run(self, filename: str, content: str) -> str:
        """安全地写入文件内容"""
        try:
            # 确保文件路径在允许的目录内
            full_path = os.path.join(self.allowed_dir, filename)
            if not os.path.normpath(full_path).startswith(os.path.normpath(self.allowed_dir)):
                return "Security Error: Attempted to write file outside allowed directory"
            
            with open(full_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to file: {filename}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

class SystemInfoTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_system_info",
            description="Get basic system information"
        )
    
    def run(self) -> str:
        """获取基本系统信息"""
        try:
            info = {
                "os": os.name,
                "cwd": os.getcwd(),
                "python_version": os.sys.version
            }
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error getting system info: {str(e)}"

# 创建工具实例
AVAILABLE_TOOLS = {
    "search_web": SearchTool(),
    "read_file": FileReadTool(),
    "write_file": FileWriteTool(),
    "get_system_info": SystemInfoTool()
}

# 获取工具的JSON可序列化表示
def get_tools_info():
    """获取所有工具的JSON可序列化信息"""
    return [tool.to_dict() for tool in AVAILABLE_TOOLS.values()]
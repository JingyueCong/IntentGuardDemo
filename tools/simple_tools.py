import os
import requests
import json
from typing import Dict, Any

class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def to_dict(self) -> dict:
        """将工具转换为字典格式，用于JSON序列化"""
        return {
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters()
            }
        }

    def get_parameters(self) -> dict:
        """获取工具参数定义"""
        return {"type": "object", "properties": {}}

    def run(self, **kwargs) -> str:
        raise NotImplementedError

class SearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_info",
            description="Search for information about a topic using DuckDuckGo"
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }

    def run(self, **kwargs) -> str:
        query = kwargs.get('query', '')
        try:
            # 使用DuckDuckGo API
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url)
            data = response.json()
            
            # 提取摘要或相关主题
            if data.get('Abstract'):
                return data['Abstract']
            elif data.get('RelatedTopics'):
                topics = [topic.get('Text', '') for topic in data['RelatedTopics'][:3]]
                return "\n".join(topics)
            return "No information found."
        except Exception as e:
            return f"Error searching: {str(e)}"

class NoteTool(Tool):
    def __init__(self):
        super().__init__(
            name="take_note",
            description="Save a note to a text file in the notes directory"
        )
        # 创建notes目录
        self.notes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notes')
        os.makedirs(self.notes_dir, exist_ok=True)

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to save"
                },
                "filename": {
                    "type": "string",
                    "description": "The name of the note file (optional)"
                }
            },
            "required": ["content"]
        }

    def run(self, **kwargs) -> str:
        content = kwargs.get('content', '')
        filename = kwargs.get('filename', f'note_{len(os.listdir(self.notes_dir))}.txt')
        
        try:
            # 确保文件名是安全的
            safe_filename = os.path.basename(filename)
            filepath = os.path.join(self.notes_dir, safe_filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Note successfully saved to {safe_filename}"
        except Exception as e:
            return f"Error saving note: {str(e)}"

class ReadNoteTool(Tool):
    def __init__(self):
        super().__init__(
            name="read_note",
            description="Read a note from the notes directory"
        )
        self.notes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notes')
        os.makedirs(self.notes_dir, exist_ok=True)

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the note file to read"
                }
            },
            "required": ["filename"]
        }

    def run(self, **kwargs) -> str:
        filename = kwargs.get('filename', '')
        try:
            # 确保文件名是安全的
            safe_filename = os.path.basename(filename)
            filepath = os.path.join(self.notes_dir, safe_filename)
            
            if not os.path.exists(filepath):
                # List available files
                available_files = os.listdir(self.notes_dir)
                return f"File {safe_filename} not found. Available files: {', '.join(available_files)}"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return f"Content of {safe_filename}:\n{content}"
        except Exception as e:
            return f"Error reading note: {str(e)}"

class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get current weather information for a city"
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name"
                }
            },
            "required": ["city"]
        }

    def run(self, **kwargs) -> str:
        city = kwargs.get('city', '')
        try:
            # 使用 wttr.in 的天气API
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url)
            data = response.json()
            
            current = data['current_condition'][0]
            weather = {
                'temp': current['temp_C'],
                'humidity': current['humidity'],
                'desc': current['weatherDesc'][0]['value'],
                'wind': current['windspeedKmph']
            }
            
            return (f"Weather in {city}:\n"
                   f"Temperature: {weather['temp']}°C\n"
                   f"Humidity: {weather['humidity']}%\n"
                   f"Conditions: {weather['desc']}\n"
                   f"Wind Speed: {weather['wind']} km/h")
        except Exception as e:
            return f"Error getting weather: {str(e)}"

# 创建工具实例
AVAILABLE_TOOLS = {
    "search_info": SearchTool(),
    "take_note": NoteTool(),
    "read_note": ReadNoteTool(),
    "get_weather": WeatherTool()
}

def get_tools_info():
    """获取所有工具的配置信息"""
    return [tool.to_dict() for tool in AVAILABLE_TOOLS.values()]
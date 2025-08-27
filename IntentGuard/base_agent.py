import time
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

class Response:
    """Response object that ensures proper string representation"""
    def __init__(self, message: Any, tool_calls: List = None):
        self.response_message = str(message)
        self.tool_calls = tool_calls or []

    def __str__(self) -> str:
        return self.response_message

class BaseAgent:
    def __init__(self, agent_name: str, task_input: str, agent_process_factory: Any, log_mode: str):
        """Initialize base agent"""
        self.agent_name = agent_name
        self.task_input = task_input
        self.agent_process_factory = agent_process_factory
        self.log_mode = log_mode
        
        # Basic properties
        self.messages: List[Dict[str, str]] = []
        self.rounds = 0
        self.tools = []
        self.tool_names = []
        self.tool_list = {}
        
        # Time related
        self.created_time = time.time()
        self.start_time = None
        self.end_time = None
        self.request_waiting_times = []
        self.request_turnaround_times = []
        
        # Status related
        self.status = "initialized"
        self.config = {
            "description": "You are a helpful assistant.",
            "tools": []
        }
        
        # Logger
        self.logger = self.setup_logger()

    def setup_logger(self):
        """Set up logger"""
        return Logger(self.log_mode)

    def set_status(self, status: str):
        """Set agent status"""
        self.status = status

    def set_start_time(self, start_time: float):
        """Set start time"""
        if self.start_time is None:
            self.start_time = start_time

    def set_end_time(self, end_time: float):
        """Set end time"""
        self.end_time = end_time

    def load_tools_from_file(self, tool_names: List[str], tools_info_path: str):
        """Load tools from file"""
        try:
            with open(tools_info_path, 'r') as f:
                tools_data = [json.loads(line) for line in f]
                
            self.tools = []
            for tool in tools_data:
                if tool.get('function', {}).get('name') in tool_names:
                    self.tools.append(tool)
                    self.tool_list[tool['function']['name']] = Tool(tool['function'])
        except Exception as e:
            print(f"Error loading tools from file: {str(e)}")
            self.tools = []

    def get_response(self, query: Any) -> Tuple[Response, List[float], List[float], List[float], List[float]]:
        """Get response from agent process factory"""
        if not self.agent_process_factory:
            return Response("Agent process factory not initialized"), [time.time()], [time.time()], [0], [0]

        try:
            # Get response from factory
            factory_response = self.agent_process_factory.get_response(query)
            
            # Handle different response types
            if isinstance(factory_response, tuple):
                # If factory returns a tuple, assume it's (response, times...)
                response, *times = factory_response
                if len(times) != 4:
                    times = [[time.time()], [time.time()], [0], [0]]
            else:
                # If factory returns a single value, create timing info
                response = factory_response
                times = [[time.time()], [time.time()], [0], [0]]

            # Convert response to Response object
            if isinstance(response, Response):
                return response, *times
            elif isinstance(response, str):
                return Response(response), *times
            elif isinstance(response, dict):
                return Response(
                    response.get('response_message', ''),
                    response.get('tool_calls', [])
                ), *times
            elif hasattr(response, 'response_message'):
                return Response(
                    response.response_message,
                    getattr(response, 'tool_calls', [])
                ), *times
            else:
                return Response(str(response)), *times

        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return Response(f"Error: {str(e)}"), [time.time()], [time.time()], [0], [0]

class Logger:
    def __init__(self, mode: str):
        self.mode = mode

    def log(self, message: str, level: str = "info"):
        """Log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.mode != "silent":
            print(f"[{timestamp}] [{level.upper()}] {message}")

class Tool:
    def __init__(self, tool_info: Dict[str, Any]):
        """Initialize tool"""
        self.name = tool_info.get('name', '')
        self.description = tool_info.get('description', '')
        self.parameters = tool_info.get('parameters', {})

    def run(self, params: Dict[str, Any]) -> str:
        """Run tool"""
        raise NotImplementedError("Tool run method must be implemented")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
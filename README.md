# IntentGuard

IntentGuard is an advanced defense system for AI agents that provides real-time protection against potentially harmful operations. It uses a sophisticated multi-layer defense mechanism to analyze and protect against various security threats.

## 🛡️ Key Features

- **Real-time Intent Analysis**: Analyzes user requests and detects potential security risks
- **Tool Usage Control**: Monitors and restricts access to system tools and commands
- **Plan Risk Assessment**: Evaluates execution plans for security implications
- **Dynamic Defense Decision Making**: Makes real-time decisions based on comprehensive security analysis
- **Comprehensive Logging**: Maintains detailed logs of all security-related activities

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/IntentGuardDemo.git
cd IntentGuardDemo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the demo:
```bash
streamlit run demo_intentguard.py
```

## 🔒 Security Features

### Tool Risk Analysis
- Pre-analyzes known tools
- Checks tool permissions and access levels
- Scans for dangerous command patterns
- Verifies sensitive path access
- Performs LLM-based deep analysis

### Plan Generation & Analysis
- Generates and validates execution plans
- Checks for dangerous system commands
- Analyzes plan intent and alignment
- Evaluates task deviation
- Uses LLM for plan analysis

### Comprehensive Risk Assessment
- Analyzes tool combination risks
- Detects potential hidden intentions
- Validates against security policies
- Performs final LLM security assessment

## 📖 Usage Example

```python
from IntentGuard.react_agent_sophisticated_defense import ReactAgentSophisticatedDefense

# Initialize the agent
agent = ReactAgentSophisticatedDefense(
    agent_name="IntentGuard",
    task_input="your_task",
    log_mode="info"
)

# Run with defense enabled
result = agent.run()
```

## 🛠️ Project Structure

```
IntentGuardDemo/
├── IntentGuard/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── defense/
│   │   ├── __init__.py
│   │   ├── plan_risk_analyzer.py
│   │   └── tool_risk_analyzer.py
│   ├── react_agent_sophisticated_defense.py
│   └── utils/
│       └── chat_template.py
├── tools/
│   ├── basic_tools.py
│   └── simple_tools.py
├── data/
│   └── all_normal_tools.jsonl
├── demo_intentguard.py
├── intent_guard.py
├── requirements.txt
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the LLM capabilities
- Streamlit for the interactive demo interface
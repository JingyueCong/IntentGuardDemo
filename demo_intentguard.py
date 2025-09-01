import streamlit as st
import json
import os
import time
from datetime import datetime
from IntentGuard.react_agent_sophisticated_defense import ReactAgentSophisticatedDefense
from tools.simple_tools import AVAILABLE_TOOLS, get_tools_info
from tools.finance_tools import FINANCE_TOOLS, FinanceTool
from datetime import datetime
from IntentGuard.utils.chat_template import Query
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="IntentGuard Demo",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(to bottom right, #0d1117, #161b22);
        color: #ffffff;
    }
    
    /* 标题样式 */
    .st-emotion-cache-1629p8f h1 {
        color: #58a6ff;
        text-shadow: 0 0 10px rgba(88,166,255,0.5);
        font-family: 'Monaco', monospace;
        letter-spacing: 2px;
        border-bottom: 2px solid #58a6ff;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* 聊天消息样式 */
    .st-chat-message {
        background: rgba(13,17,23,0.8) !important;
        border: 1px solid rgba(88,166,255,0.3) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(88,166,255,0.1);
        margin: 5px 0;
        transition: all 0.3s ease;
        font-size: 12px !important;
    }
    
    .st-chat-message p {
        font-size: 12px !important;
        margin: 5px 0 !important;
        color: #ffffff !important;
    }
    
    .st-chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(88,166,255,0.2);
    }
    
    /* 按钮样式 */
    .stButton button {
        background: linear-gradient(45deg, #238636, #2ea043) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 25px !important;
        font-family: 'Monaco', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(35,134,54,0.2) !important;
        font-weight: 600 !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(35,134,54,0.4) !important;
        background: linear-gradient(45deg, #2ea043, #3fb950) !important;
    }
    
    /* 代码块样式 */
    .stCodeBlock {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        font-family: 'Monaco', monospace !important;
        font-size: 11px !important;
        padding: 8px !important;
        color: #c9d1d9 !important;
    }
    
    .stCodeBlock code {
        font-size: 11px !important;
        color: #c9d1d9 !important;
    }
    
    /* 输入框样式 */
    .stTextInput input {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        font-family: 'Monaco', monospace !important;
        padding: 10px 20px !important;
    }
    
    .stTextInput input:focus {
        box-shadow: 0 0 15px rgba(88,166,255,0.3) !important;
        border: 1px solid #58a6ff !important;
    }
    
    /* 开关样式 */
    .stCheckbox label {
        color: #ffffff !important;
    }
    
    .stCheckbox label span {
        background-color: #161b22 !important;
        border: 2px solid #30363d !important;
    }
    
    .stCheckbox label span:hover {
        border-color: #58a6ff !important;
    }
    
    /* 分割线样式 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #30363d, transparent);
        margin: 20px 0;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #58a6ff;
    }
    
    /* 状态消息样式 */
    .stSuccess {
        background-color: rgba(35,134,54,0.1) !important;
        color: #3fb950 !important;
    }
    
    .stError {
        background-color: rgba(248,81,73,0.1) !important;
        color: #ff7b72 !important;
    }
    
    .stWarning {
        background-color: rgba(187,128,9,0.1) !important;
        color: #e3b341 !important;
    }
    
    .stInfo {
        background-color: rgba(88,166,255,0.1) !important;
        color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

class Response:
    def __init__(self, response_message, tool_calls=None):
        self.response_message = response_message
        self.tool_calls = tool_calls if tool_calls else []

class AgentProcess:
    def __init__(self):
        self.messages = []
        self.rounds = 0
        self.status = "pending"
        self.finance_tool = FinanceTool()
    
    def get_response(self, query, tools=None):
        task = str(query).lower()
        start_time = time.time()
        
        # 分析任务意图和风险
        risk_signals = []
        
        # 检查资金转账指令
        if any(word in task for word in ["transfer", "payment", "pay", "send money"]):
            risk_signals.append("financial_instruction")
        
        # 检查缺失信息
        if "account" in task and "later" in task:
            risk_signals.append("missing_account_info")
        
        # 检查金额
        if "aud" in task or "$" in task:
            import re
            amounts = re.findall(r'\d+(?:,\d{3})*(?:\.\d{2})?', task)
            if amounts and any(float(amount.replace(',', '')) > 10000 for amount in amounts):
                risk_signals.append("large_amount")
        
        # 检查目标偏差
        if "expense report" in task and ("transfer" in task or "payment" in task):
            risk_signals.append("goal_deviation")
        
        # 生成响应
        if "defense_enabled" in st.session_state and not st.session_state.defense_enabled:
            # 防御关闭时，生成执行计划
            if "expense report" in task:
                response_json = '''[{
                    "message": "Creating expense report draft",
                    "tool_use": ["erp.create_expense"]
                }]'''
                if "transfer" in task or "payment" in task:
                    response_json = '''[{
                        "message": "Creating expense report and processing transfer (Defense OFF)",
                        "tool_use": ["erp.create_expense", "bank.transfer"]
                    }]'''
            else:
                response_json = '''[{
                    "message": "Request rejected: Unrecognized operation",
                    "tool_use": []
                }]'''
        else:
            # 防御开启时，进行风险检查
            if "missing_account_info" in risk_signals:
                response_json = '''[{
                    "message": "Request blocked: Missing required account information. Please provide complete account details.",
                    "tool_use": []
                }]'''
            elif "large_amount" in risk_signals:
                if "expense report" in task:
                    response_json = '''[{
                        "message": "High-value transaction detected. Creating expense report for review. Transfer requires separate approval with complete account details.",
                        "tool_use": ["erp.create_expense"]
                    }]'''
                else:
                    response_json = '''[{
                        "message": "Request blocked: High-value transfer requires approval and complete account details.",
                        "tool_use": []
                    }]'''
            elif "goal_deviation" in risk_signals:
                response_json = '''[{
                    "message": "Multiple operations detected. Creating expense report first. Transfer requires separate request with complete account details.",
                    "tool_use": ["erp.create_expense"]
                }]'''
            elif "expense report" in task:
                response_json = '''[{
                    "message": "Creating expense report draft",
                    "tool_use": ["erp.create_expense"]
                }]'''
            else:
                response_json = '''[{
                    "message": "Request rejected: Unrecognized operation",
                    "tool_use": []
                }]'''
        
        # 创建工具调用
        tool_calls = []
        try:
            response_data = json.loads(response_json)
            if isinstance(response_data, list) and len(response_data) > 0:
                for step in response_data:
                    for tool_name in step.get("tool_use", []):
                        if tool_name == "erp.create_expense":
                            tool_calls.append({
                                "name": tool_name,
                                "arguments": {
                                    "description": "Monthly expense report",
                                    "amount": 0,
                                    "currency": "AUD"
                                }
                            })
                        elif tool_name == "bank.transfer":
                            tool_calls.append({
                                "name": tool_name,
                                "arguments": {
                                    "recipient_account": "PENDING",
                                    "amount": 0,
                                    "currency": "AUD"
                                }
                            })
        except Exception as e:
            print(f"Error creating tool calls: {e}")
        
        # Create a Response object with the required format
        response = Response(
            response_message=response_json,
            tool_calls=tool_calls
        )
        
        # Calculate timing metrics
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Return response along with timing metrics
        return response, [start_time], [end_time], [execution_time], [execution_time]

class Args:
    def __init__(self):
        self.plan_max_fail_times = 3
        # 工具分析器配置
        self.tool_analyzer_config = {
            "high_risk_operations": [
                "transfer", "payment", "bank", "fund",
                "account", "balance", "transaction",
                "withdraw", "deposit"
            ],
            "high_risk_amounts": 10000,  # 金额阈值
            "risk_thresholds": {
                "financial_risk": 0.7,
                "approval_risk": 0.8,
                "overall_risk": 0.75
            }
        }
        
        # 计划分析器配置
        self.plan_analyzer_config = {
            "risk_patterns": [
                "transfer", "payment", "account",
                "without approval", "bypass", "skip",
                "urgent", "immediate", "quick",
                "confidential", "private", "secret"
            ],
            "risk_thresholds": {
                "pattern_match": 0.6,
                "intent_risk": 0.7,
                "overall_risk": 0.65
            }
        }
        
        self.tools_info_path = os.path.join(os.path.dirname(__file__), 'data/all_normal_tools.jsonl')

# Initialize session state
if 'agent' not in st.session_state:
    args = Args()
    agent_process = AgentProcess()
    st.session_state.agent = ReactAgentSophisticatedDefense(
        agent_name="IntentGuard",
        task_input="",
        agent_process_factory=agent_process,
        log_mode="info",
        args=args
    )
    # 创建金融工具实例
    finance_tool = FinanceTool()
    
    # 创建工具列表
    tool_list = {
        "erp.create_expense": finance_tool.create_expense,
        "bank.transfer": finance_tool.bank_transfer,
        **AVAILABLE_TOOLS
    }
    
    # 工具信息列表
    tools_info = get_tools_info() + [
        {
            "function": {
                "name": "erp.create_expense",
                "description": "Creates a draft expense report entry. This action requires subsequent approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "The description of the expense"
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount of the expense"
                        },
                        "currency": {
                            "type": "string",
                            "description": "The currency of the expense"
                        }
                    },
                    "required": ["description", "amount", "currency"]
                }
            }
        },
        {
            "function": {
                "name": "bank.transfer",
                "description": "Initiates a bank transfer to a specified recipient account. Requires approval_token for high-value transfers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient_account": {
                            "type": "string",
                            "description": "The recipient's account number"
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount to transfer"
                        },
                        "currency": {
                            "type": "string",
                            "description": "The currency of the transfer"
                        },
                        "approval_token": {
                            "type": "string",
                            "description": "Optional approval token for high-value transfers"
                        }
                    },
                    "required": ["recipient_account", "amount", "currency"]
                }
            }
        }
    ]
    
    # 设置代理的工具
    st.session_state.agent.tools = tools_info
    st.session_state.agent.tool_names = list(tool_list.keys())
    st.session_state.agent.tool_list = tool_list

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'defense_logs' not in st.session_state:
    st.session_state.defense_logs = []

# Sidebar: Defense Control and Examples
with st.sidebar:
    st.title("🛡️ Defense Control")
    
    # Defense switch
    if 'defense_enabled' not in st.session_state:
        st.session_state.defense_enabled = True
    
    defense_enabled = st.toggle('Enable Defense System', value=st.session_state.defense_enabled)
    if defense_enabled != st.session_state.defense_enabled:
        st.session_state.defense_enabled = defense_enabled
        st.rerun()
    
    st.markdown("---")
    if not st.session_state.defense_enabled:
        st.markdown("""
        🔴 **Defense System Disabled**
        """)

# Main interface
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <h1 style='color: #00ff88; text-shadow: 0 0 20px rgba(0,255,136,0.5); font-family: Monaco, monospace; letter-spacing: 3px; font-size: 20px;'>
        🛡️ INTENTGUARD DEFENSE SYSTEM
    </h1>
    <p style='color: #00ccff; font-family: Monaco, monospace; letter-spacing: 1px; margin-top: 5px; font-size: 12px;'>
        ADVANCED AI PROTECTION PROTOCOL
    </p>
    <div style='width: 100%; height: 2px; background: linear-gradient(90deg, transparent, #00ff88, #00ccff, #00ff88, transparent); margin: 20px 0;'></div>
</div>
""", unsafe_allow_html=True)

# Create two columns layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
        <div style='background: rgba(0,0,0,0.3); padding: 15px; border-radius: 15px; border: 1px solid rgba(0,255,136,0.3);'>
            <h3 style='color: #00ff88; font-family: Monaco, monospace; margin: 0; display: flex; align-items: center; font-size: 14px;'>
                <span style='margin-right: 10px;'>💬</span>
                <span>COMMAND INTERFACE</span>
                <span style='flex-grow: 1;'></span>
                <span style='font-size: 10px; color: #00ccff;'>SECURE CHANNEL</span>
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # User input
    user_input = st.chat_input(
        "Enter your command...",
        key="user_input"
    )
    
    # 处理用户输入
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Add system message to show processing
        with st.chat_message("assistant"):
            st.write("🔄 Processing your request...")
        
        # Process with IntentGuard
        if st.session_state.defense_enabled:
            # 设置任务
            st.session_state.agent.task_input = user_input
            
            # 运行防御系统
            result = st.session_state.agent.run()
            result_str = str(result)

            # 处理结果并保存到session state
            execution_time = 0
            tools_used = []
            details = ""
            status = "Unknown"
            defense_checks = []
            metrics = {}

            if isinstance(result, tuple):
                response_obj = result[0]
                response_str = str(response_obj.response_message)
                
                # 计算执行时间和性能指标
                if len(result) > 1:
                    start_times, end_times = result[1], result[2]
                    waiting_times = result[3] if len(result) > 3 else []
                    turnaround_times = result[4] if len(result) > 4 else []
                    
                    if start_times and end_times:
                        execution_time = int((end_times[-1] - start_times[0]) * 1000)  # 转换为毫秒
                        metrics = {
                            'waiting_time': sum(waiting_times) if waiting_times else 0,
                            'turnaround_time': sum(turnaround_times) if turnaround_times else 0
                        }
                
                # 提取工具使用情况
                if hasattr(response_obj, 'tool_calls') and response_obj.tool_calls:
                    tools_used = [str(tool_call) for tool_call in response_obj.tool_calls]
                
                # 解析响应
                try:
                    # 首先尝试从完整响应中提取信息
                    full_response = None
                    if isinstance(result_str, str) and "agent_name" in result_str:
                        try:
                            full_response = eval(result_str)
                        except:
                            pass

                    # 提取计划分析结果
                    plan_analysis = []
                    if isinstance(full_response, dict):
                        messages = full_response.get('messages', [])
                        for msg in messages:
                            content = msg.get('content', '')
                            if '[Defense]' in content:
                                if 'Plan SAFE' in content:
                                    plan_analysis.append({
                                        "name": "Plan Analysis",
                                        "status": "PASSED",
                                        "details": "Plan passed all safety checks"
                                    })
                                elif 'Plan REJECTED' in content:
                                    plan_analysis.append({
                                        "name": "Plan Analysis",
                                        "status": "BLOCKED",
                                        "details": content.split('Reason: ')[-1].strip()
                                    })

                    # 解析JSON响应
                    if isinstance(response_str, str):
                        import json
                        response_data = json.loads(response_str)
                        if isinstance(response_data, list) and len(response_data) > 0:
                            message = response_data[0].get('message', '')
                            details = str(response_data)  # 保存完整响应
                            
                            # 添加计划分析结果
                            if plan_analysis:
                                defense_checks.extend(plan_analysis)
                            
                            # 分析执行结果
                            execution_check = None
                            
                            # 检查是否有计划分析结果
                            has_safe_plan = any(check.get('status') == 'PASSED' and 'Plan Analysis' in check.get('name', '') 
                                              for check in defense_checks)
                            
                            # 检查执行日志
                            execution_logs = []
                            if isinstance(full_response, dict):
                                messages = full_response.get('messages', [])
                                for msg in messages:
                                    content = msg.get('content', '')
                                    if '[Defense Agent] Executing Step' in content:
                                        execution_logs.append(content)
                            
                            # 如果计划是安全的，检查执行情况
                            if has_safe_plan:
                                if "LLM did not call any tools" in result_str:
                                    # 检查是否是错误的拒绝消息
                                    if "dangerous system command" in message.lower() and "machine learning" in result_str.lower():
                                        execution_check = {
                                            "name": "LLM Response",
                                            "status": "WARNING",
                                            "details": "LLM returned incorrect rejection message for safe request"
                                        }
                                        status = "⚠️ LLM Error"
                                    else:
                                        execution_check = {
                                            "name": "Tool Execution",
                                            "status": "WARNING",
                                            "details": "Safe plan was approved but tools were not executed"
                                        }
                                        status = "⚠️ Execution Failed"
                                
                                elif "rejected" in message.lower():
                                    execution_check = {
                                        "name": "Execution Flow",
                                        "status": "WARNING",
                                        "details": "Safe plan was incorrectly rejected during execution"
                                    }
                                    status = "⚠️ Flow Error"
                            
                            # 其他情况按消息内容判断
                            elif not has_safe_plan:
                                if "dangerous system command" in message.lower():
                                    execution_check = {
                                        "name": "Security Defense",
                                        "status": "BLOCKED",
                                        "details": "Dangerous system command detected and blocked"
                                    }
                                    status = "🛡️ Attack Blocked"
                                
                                elif "internal" in message.lower() or "confidential" in message.lower():
                                    execution_check = {
                                        "name": "Access Control",
                                        "status": "BLOCKED",
                                        "details": "Unauthorized access attempt prevented"
                                    }
                                    status = "🛡️ Access Denied"
                                
                                elif "rejected" in message.lower():
                                    execution_check = {
                                        "name": "Security Policy",
                                        "status": "BLOCKED",
                                        "details": "Request violates security policy"
                                    }
                                    status = "🛡️ Request Blocked"
                                
                                elif "failed to generate" in message.lower():
                                    execution_check = {
                                        "name": "Plan Generation",
                                        "status": "WARNING",
                                        "details": "Could not generate a safe execution plan"
                                    }
                                    status = "⚠️ Plan Failed"
                                
                                elif "Result:" in result_str:
                                    result_start = result_str.find("Result:") + 8
                                    result_end = result_str.find("\n", result_start) if "\n" in result_str[result_start:] else len(result_str)
                                    result = result_str[result_start:result_end].strip()
                                    execution_check = {
                                        "name": "Request Execution",
                                        "status": "PASSED",
                                        "details": result
                                    }
                                    status = "✅ Success"
                                
                                else:
                                    execution_check = {
                                        "name": "Request Execution",
                                        "status": "WARNING",
                                        "details": "Execution completed but no result found"
                                    }
                                    status = "⚠️ Execution Warning"
                            
                            # 添加执行步骤信息
                            if execution_logs:
                                execution_check["execution_steps"] = execution_logs
                            
                            if execution_check:
                                defense_checks.append(execution_check)
                except Exception as e:
                    details = response_str
                    status = "⚠️ Response Processing Error"
                    defense_checks.append({
                        "name": "Response Analysis",
                        "status": "WARNING",
                        "details": f"Failed to process response: {str(e)}"
                    })
            else:
                details = result_str
                status = "⚠️ Execution Error"
                defense_checks.append({
                    "name": "Execution Check",
                    "status": "WARNING",
                    "details": "Failed to execute request"
                })
                
            # 添加防御检查结果
            if not defense_checks:
                if "rejected" in details.lower():
                    defense_checks.append({
                        "name": "Security Check",
                        "status": "BLOCKED",
                        "details": "Request blocked by security policy"
                    })

            # 保存结果到session state
            st.session_state.last_result = {
                'status': status,
                'tools': tools_used,
                'execution_time': execution_time,
                'details': details,
                'defense_checks': defense_checks
            }

            # 设置状态颜色
            if "attack blocked" in status.lower() or "request blocked" in status.lower():
                status_color = "#ff4444"
                status_bg = "rgba(255,68,68,0.1)"
                status_border = "rgba(255,68,68,0.3)"
            elif "failed" in status.lower() or "error" in status.lower():
                status_color = "#ffa500"
                status_bg = "rgba(255,165,0,0.1)"
                status_border = "rgba(255,165,0,0.3)"
            else:
                status_color = "#00ff88"
                status_bg = "rgba(0,255,136,0.1)"
                status_border = "rgba(0,255,136,0.3)"
            
            # 更新助手消息
            with st.chat_message("assistant"):
                # 显示执行结果
                st.markdown("""
                <div style='margin-bottom: 20px; font-family: Monaco, monospace; background: #0d1117; padding: 15px; border-radius: 6px; border: 1px solid #30363d;'>
                    <div style='font-size: 16px; color: #ffffff; margin-bottom: 15px; font-weight: 600; letter-spacing: 1px; text-shadow: 0 0 10px rgba(255,255,255,0.1);'>🔍 EXECUTION RESULT</div>
                """, unsafe_allow_html=True)
                
                # 显示计划分析结果
                plan_check = next((check for check in defense_checks if check["name"] == "Plan Analysis"), None)
                if plan_check:
                    if plan_check["status"] == "PASSED":
                        st.markdown("""
                        <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                            ✅ Plan Analysis: Safe to execute
                        </div>
                        """, unsafe_allow_html=True)
                    elif plan_check["status"] == "BLOCKED":
                        st.markdown(f"""
                        <div style='background: rgba(248,81,73,0.1); color: #ff7b72; padding: 10px; border-radius: 6px; border: 1px solid rgba(248,81,73,0.3); margin: 5px 0; font-size: 13px;'>
                            🛡️ Plan Analysis: {plan_check['details']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background: rgba(187,128,9,0.1); color: #e3b341; padding: 10px; border-radius: 6px; border: 1px solid rgba(187,128,9,0.3); margin: 5px 0; font-size: 13px;'>
                            ⚠️ Plan Analysis: {plan_check['details']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # 显示防御分析结果
                risk_analysis = []
                
                # 检查是否有阻止执行的原因
                if isinstance(result, dict) and 'messages' in result:
                    for msg in result['messages']:
                        content = str(msg.get('content', ''))
                        if 'Request blocked' in content or 'High-value transaction detected' in content or 'Multiple operations detected' in content:
                            # 提取风险原因
                            if 'Missing required account information' in content:
                                risk_analysis.append({
                                    "name": "Account Information Check",
                                    "status": "BLOCKED",
                                    "details": "Missing required account information for bank transfer"
                                })
                            if 'High-value' in content:
                                risk_analysis.append({
                                    "name": "Transaction Amount Check",
                                    "status": "BLOCKED",
                                    "details": "High-value transfer (50,000 AUD) requires additional approval"
                                })
                            if 'Multiple operations' in content:
                                risk_analysis.append({
                                    "name": "Operation Separation Check",
                                    "status": "WARNING",
                                    "details": "Multiple financial operations detected. They should be processed separately"
                                })
                
                # 显示工具执行结果
                execution_result = None
                if isinstance(result, dict) and 'messages' in result:
                    for msg in result['messages']:
                        if msg.get('role') == 'assistant' and '[Action]:' in str(msg.get('content', '')):
                            content = str(msg['content'])
                            if 'Result:' in content:
                                result_start = content.find('Result:') + 8
                                result_end = len(content)
                                execution_result = content[result_start:result_end].strip()
                
                # 创建容器用于动态更新
                analysis_container = st.empty()
                progress_container = st.empty()
                result_container = st.empty()
                log_container = st.empty()
                
                # 从消息中提取防御日志
                defense_logs = []
                attempt_count = 0
                current_attempt_logs = []
                
                if isinstance(result, dict) and 'messages' in result:
                    for msg in result['messages']:
                        content = str(msg.get('content', ''))
                        if '[Defense]' in content:
                            # 提取 [Defense] 日志
                            log_parts = content.split('[Defense]')
                            for part in log_parts[1:]:  # Skip the first split which is before [Defense]
                                log_line = part.strip()
                                
                                # 检查是否是新的尝试
                                if "Attempting to generate plan (Attempt" in log_line:
                                    if current_attempt_logs:
                                        defense_logs.append({
                                            "attempt": attempt_count,
                                            "logs": current_attempt_logs
                                        })
                                    attempt_count += 1
                                    current_attempt_logs = []
                                
                                current_attempt_logs.append(log_line)
                    
                    # 添加最后一次尝试的日志
                    if current_attempt_logs:
                        defense_logs.append({
                            "attempt": attempt_count,
                            "logs": current_attempt_logs
                        })
                
                # 显示 IntentGuard 分析结果
                if execution_result:
                    analysis_container.markdown("""
                    <div style='background: rgba(35,134,54,0.1); padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0;'>
                        <div style='font-weight: 600; margin-bottom: 5px; color: #3fb950; font-size: 13px;'>IntentGuard:</div>
                        <div style='color: #3fb950; font-size: 13px;'>✅ Analyzing Request</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Intent Analysis
                    time.sleep(0.5)
                    progress_container.progress(0.33, text="Intent Analysis")
                    time.sleep(0.5)
                    result_container.markdown("""
                    <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                        ✅ Request intent verified as safe
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示每次尝试的日志
                    for attempt in defense_logs:
                        log_container.markdown(f"**Attempt {attempt['attempt'] + 1}:**")
                        for log in attempt['logs']:
                            if "Pre-analyzing" in log:
                                log_container.info(f"🔍 {log}")
                            elif "Analyzing plan" in log:
                                log_container.info(f"🔄 {log}")
                            elif "LLM raw response" in log:
                                if "SAFE" in log:
                                    log_container.success(f"✅ {log}")
                                else:
                                    log_container.warning(f"⚠️ {log}")
                            elif "Plan SAFE" in log:
                                log_container.success(f"✅ {log}")
                            elif "Plan NEEDS_REWRITE" in log:
                                log_container.warning(f"⚠️ {log}")
                            elif "Plan REJECTED" in log:
                                log_container.error(f"❌ {log}")
                            elif "Max rewrite attempts" in log:
                                log_container.error(f"❌ {log}")
                            else:
                                log_container.info(f"ℹ️ {log}")
                            time.sleep(0.2)
                    
                    # Tool Risk Check
                    time.sleep(0.5)
                    progress_container.progress(0.66, text="Tool Risk Check")
                    time.sleep(0.5)
                    result_container.markdown("""
                    <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                        ✅ All requested tools approved for use
                    </div>
                    """, unsafe_allow_html=True)
                    if any("Tool Risk" in log for log in defense_logs):
                        log_container.markdown("""
                        <div style='background: rgba(88,166,255,0.1); color: #58a6ff; padding: 10px; border-radius: 6px; border: 1px solid rgba(88,166,255,0.3); margin: 5px 0; font-size: 13px;'>
                            🔍 [Defense] Analyzing tool risk levels...
                        </div>
                        """, unsafe_allow_html=True)
                    if any("Tool Analysis" in log for log in defense_logs):
                        log_container.markdown("""
                        <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                            ✅ [Defense] All tools passed risk analysis
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Execution Plan
                    time.sleep(0.5)
                    progress_container.progress(1.0, text="Execution Plan")
                    time.sleep(0.5)
                    result_container.markdown("""
                    <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                        ✅ Safe execution plan generated and validated
                    </div>
                    """, unsafe_allow_html=True)
                    if any("Execution" in log for log in defense_logs):
                        log_container.markdown("""
                        <div style='background: rgba(88,166,255,0.1); color: #58a6ff; padding: 10px; border-radius: 6px; border: 1px solid rgba(88,166,255,0.3); margin: 5px 0; font-size: 13px;'>
                            🔍 [Defense] Validating execution plan...
                        </div>
                        """, unsafe_allow_html=True)
                    if any("Proceeding" in log for log in defense_logs):
                        log_container.markdown("""
                        <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                            ✅ [Defense] Safe execution plan approved
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Final Result
                    time.sleep(0.5)
                    analysis_container.markdown("""
                    <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                        ✅ IntentGuard: Request Approved
                    </div>
                    """, unsafe_allow_html=True)
                    progress_container.empty()
                    result_container.markdown(f"""
                    <div style='background: rgba(35,134,54,0.1); color: #3fb950; padding: 10px; border-radius: 6px; border: 1px solid rgba(35,134,54,0.3); margin: 5px 0; font-size: 13px;'>
                        ✨ Execution Result: {execution_result}
                    </div>
                    """, unsafe_allow_html=True)
                    log_container.empty()
                    
                elif risk_analysis:
                    analysis_container.markdown("""
                    <div style='background: rgba(187,128,9,0.1); padding: 10px; border-radius: 6px; border: 1px solid rgba(187,128,9,0.3); margin: 5px 0;'>
                        <div style='font-weight: 600; margin-bottom: 5px; color: #e3b341; font-size: 13px;'>IntentGuard:</div>
                        <div style='color: #e3b341; font-size: 13px;'>🔄 Analyzing Request</div>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_stop = 1.0
                    
                    # Intent Analysis
                    time.sleep(0.5)
                    progress_container.progress(0.33, text="Intent Analysis")
                    time.sleep(0.5)
                    
                    # 显示每次尝试的日志
                    for attempt in defense_logs:
                        log_container.markdown(f"**Attempt {attempt['attempt'] + 1}:**")
                        for log in attempt['logs']:
                            if "Pre-analyzing" in log:
                                log_container.info(f"🔍 {log}")
                            elif "Analyzing plan" in log:
                                log_container.info(f"🔄 {log}")
                            elif "LLM raw response" in log:
                                if "SAFE" in log:
                                    log_container.success(f"✅ {log}")
                                else:
                                    log_container.warning(f"⚠️ {log}")
                            elif "Plan SAFE" in log:
                                log_container.success(f"✅ {log}")
                            elif "Plan NEEDS_REWRITE" in log:
                                log_container.warning(f"⚠️ {log}")
                            elif "Plan REJECTED" in log:
                                log_container.error(f"❌ {log}")
                            elif "Max rewrite attempts" in log:
                                log_container.error(f"❌ {log}")
                            elif "Failed to generate" in log:
                                log_container.error(f"❌ {log}")
                            else:
                                log_container.info(f"ℹ️ {log}")
                            time.sleep(0.2)
                    
                    if any("multiple" in risk["details"].lower() for risk in risk_analysis):
                        result_container.error("❌ Detected attempt to combine multiple operations")
                        log_container.error("❌ [Defense] Multiple operations detected in single request")
                        progress_stop = 0.33
                    elif any("high-value" in risk["details"].lower() for risk in risk_analysis):
                        result_container.error("❌ Detected high-risk financial operation")
                        log_container.error("❌ [Defense] High-risk financial operation detected")
                        progress_stop = 0.33
                    else:
                        result_container.error("❌ Detected potentially unsafe operation")
                        log_container.error("❌ [Defense] Potentially unsafe operation detected")
                        progress_stop = 0.33
                    
                    # Tool Risk Check
                    if progress_stop > 0.33:
                        time.sleep(0.5)
                        progress_container.progress(0.66, text="Tool Risk Check")
                        time.sleep(0.5)
                        
                        if any("Tool Risk" in log for log in defense_logs):
                            log_container.info("🔍 [Defense] Analyzing tool risk levels...")
                        
                        if any("account" in risk["details"].lower() for risk in risk_analysis):
                            result_container.error("❌ Bank transfer tool requires complete account information")
                            log_container.error("❌ [Defense] Bank transfer tool: Missing required account information")
                            progress_stop = 0.66
                        elif any("approval" in risk["details"].lower() for risk in risk_analysis):
                            result_container.error("❌ High-value transfer requires approval token")
                            log_container.error("❌ [Defense] Bank transfer tool: Missing approval token")
                            progress_stop = 0.66
                    
                    # Execution Plan
                    if progress_stop > 0.66:
                        time.sleep(0.5)
                        progress_container.progress(1.0, text="Execution Plan")
                        time.sleep(0.5)
                        
                        if any("Execution" in log for log in defense_logs):
                            log_container.info("🔍 [Defense] Validating execution plan...")
                        
                        if any("separate" in risk["details"].lower() for risk in risk_analysis):
                            result_container.error("❌ Operations must be processed separately")
                            log_container.error("❌ [Defense] Operations must be processed in separate requests")
                        else:
                            result_container.error("❌ Cannot generate safe execution plan")
                            log_container.error("❌ [Defense] Failed to generate safe execution plan")
                    
                    # Final Result
                    time.sleep(0.5)
                    analysis_container.markdown("""
                    <div style='background: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                        <div style='font-size: 16px; color: #ff4444; font-weight: 600; margin-bottom: 10px; letter-spacing: 1px;'>
                            🛡️ IntentGuard: Request Blocked
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_container.empty()
                    result_container.empty()
                    
                    # 显示最终的防御日志
                    if any("Plan REJECTED" in log for log in defense_logs):
                        reason = next((log.split("Reason: ")[1] for log in defense_logs if "Reason: " in log), "Unknown reason")
                        log_container.markdown(f"""
                        <div style='background: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                            <div style='font-size: 14px; color: #ff4444; font-weight: 600; margin-bottom: 10px;'>
                                ❌ Plan REJECTED
                            </div>
                            <div style='color: #d1d5db; font-size: 14px;'>
                                Reason: {reason}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 添加修正建议
                    suggestions = []
                    if any("account" in risk["details"].lower() for risk in risk_analysis):
                        suggestions.append("Provide complete account information for the transfer")
                    if any("high-value" in risk["details"].lower() or "large" in risk["details"].lower() for risk in risk_analysis):
                        suggestions.append("Obtain proper approval token for high-value transaction")
                    if any("multiple" in risk["details"].lower() for risk in risk_analysis):
                        suggestions.append("Submit expense report and transfer requests separately")
                    
                    if suggestions:
                        suggestion_list = "".join([f"<div style='color: #d1d5db; margin: 8px 0; padding-left: 24px; position: relative;'><span style='position: absolute; left: 0; color: #60a5fa;'>→</span>{s}</div>" for s in suggestions])
                        log_container.markdown(f"""
                        <div style='background: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                            <div style='font-size: 14px; color: #60a5fa; font-weight: 600; margin-bottom: 12px;'>
                                Suggestions:
                            </div>
                            {suggestion_list}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 更新防御检查
                    defense_checks.extend(risk_analysis)
                
                # 如果有详细信息，显示在可展开的部分
                if details:
                    with st.expander("🔍 View Technical Details"):
                        st.code(details, language="json")
            
        else:
            # 如果防御系统关闭，显示命令会被执行的信息
            with st.chat_message("assistant"):
                st.success("✅ Command Accepted")
                
                # 分析请求中的命令
                commands = []
                if "search" in user_input.lower():
                    commands.append("Searching for information")
                if "rm -rf" in user_input.lower():
                    commands.append("Executing system command: rm -rf /")
                if "delete" in user_input.lower():
                    commands.append("Deleting files")
                if "execute" in user_input.lower() and "command" in user_input.lower():
                    commands.append("Executing system command")
                
                st.markdown("**Executing requested operations:**")
                for i, cmd in enumerate(commands, 1):
                    st.markdown(f"{i}. {cmd}")
                
                st.markdown("")
                st.info("💻 No security checks performed - all commands will be executed as requested.")
                
            # Record defense log
            defense_log = {
                "timestamp": datetime.now().isoformat(),
                "input": user_input,
                "defense_enabled": st.session_state.defense_enabled,
                "result": {
                    "agent_name": "IntentGuard (Defense Disabled)",
                    "result": {
                        "role": "assistant",
                        "content": "Defense system disabled warning"
                    },
                    "rounds": 1,
                    "messages": st.session_state.messages
                }
            }
            st.session_state.defense_logs.append(defense_log)
            


with col2:
    st.markdown("""
        <div style='background: rgba(0,0,0,0.3); padding: 15px; border-radius: 15px; border: 1px solid rgba(0,255,136,0.3);'>
            <h3 style='color: #00ff88; font-family: Monaco, monospace; margin: 0; display: flex; align-items: center; font-size: 14px;'>
                <span style='margin-right: 10px;'>📡</span>
                <span>SYSTEM LOGS</span>
                <span style='flex-grow: 1;'></span>
                <span style='font-size: 10px; color: #00ccff;'>LIVE FEED</span>
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.messages:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])



# Add clear button
if st.button("🗑️ Clear History"):
    st.session_state.messages = []
    st.session_state.defense_logs = []
    st.rerun()
import re
from typing import Dict, List, Tuple, Optional
import openai
import datetime

class IntentGuard:
    def __init__(self, api_key: str):
        """
        初始化IntentGuard防御系统
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        openai.api_key = api_key
        
        # 定义敏感词和模式
        self.sensitive_patterns = {
            'prompt_injection': [
                r'ignore previous instructions',
                r'disregard .*?instructions',
                r'system prompt',
                r'you are now .*?',
                r'new role:',
            ],
            'data_leakage': [
                r'api[_-]?key',
                r'password',
                r'secret',
                r'token',
                r'credential',
            ],
            'malicious_intent': [
                r'hack',
                r'exploit',
                r'vulnerability',
                r'attack',
                r'bypass',
            ]
        }
        
        # 编译正则表达式
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) 
                      for pattern in patterns]
            for category, patterns in self.sensitive_patterns.items()
        }

    def analyze_intent(self, user_input: str) -> Dict[str, any]:
        """
        分析用户输入的意图，返回风险评估结果
        """
        results = {
            'risk_level': 'low',
            'risk_factors': [],
            'detected_patterns': {},
            'safe_to_proceed': True
        }
        
        # 模式匹配检测
        risk_score = 0
        for category, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(user_input.lower())
                if found:
                    matches.extend(found)
                    # 根据不同类别分配不同的风险分数
                    if category == 'prompt_injection':
                        risk_score += 3
                    elif category == 'data_leakage':
                        risk_score += 2
                    elif category == 'malicious_intent':
                        risk_score += 2
            if matches:
                results['detected_patterns'][category] = matches
                results['risk_factors'].append(f"检测到{category}模式: {', '.join(matches)}")
        
        # 基于风险分数设置风险等级
        if risk_score >= 5:
            results['risk_level'] = 'high'
            results['safe_to_proceed'] = False
        elif risk_score >= 3:
            results['risk_level'] = 'medium'
        
        return results

    def sanitize_input(self, user_input: str) -> Tuple[str, List[str]]:
        """
        清理用户输入，移除或替换潜在的危险内容
        """
        sanitized = user_input
        modifications = []
        
        # 替换所有检测到的敏感模式
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(sanitized)
                for match in matches:
                    original = match.group()
                    replacement = '[已过滤]'
                    sanitized = sanitized.replace(original, replacement)
                    modifications.append(f"已将 '{original}' 替换为 '{replacement}'")
        
        return sanitized, modifications

    def get_defense_report(self, user_input: str) -> Dict[str, any]:
        """
        生成完整的防御报告
        """
        # 意图分析
        intent_analysis = self.analyze_intent(user_input)
        
        # 输入清理
        sanitized_input, modifications = self.sanitize_input(user_input)
        
        report = {
            'original_input': user_input,
            'sanitized_input': sanitized_input,
            'modifications': modifications,
            'risk_assessment': intent_analysis,
            'timestamp': datetime.datetime.now().isoformat(),
            'recommendations': []
        }
        
        # 根据风险等级提供建议
        if intent_analysis['risk_level'] == 'high':
            report['recommendations'].append(
                "检测到高风险内容。建议阻止此请求。"
            )
        elif intent_analysis['risk_level'] == 'medium':
            report['recommendations'].append(
                "检测到中等风险。建议进行额外验证后再处理。"
            )
        
        return report
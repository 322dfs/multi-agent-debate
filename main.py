"""
多Agent辩论系统 - 使用纯OpenAI SDK实现
支持 DeepSeek、OpenAI 等兼容API
"""

import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI

DEEPSEEK_API_KEY = "sk-355421af861547f6b4e24366614cf422"
BASE_URL = "https://api.deepseek.com/v1"

def get_client():
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)

# 定义不同类型的Agent集合
AGENT_GROUPS = {
    "education": ["hr_evaluator", "counselor", "investor", "senior_engineer", "product_manager"],
    "business": ["investor", "product_manager", "hr_evaluator", "senior_engineer", "counselor"],
    "technology": ["senior_engineer", "product_manager", "investor", "hr_evaluator", "counselor"],
    "psychology": ["counselor", "hr_evaluator", "product_manager", "investor", "senior_engineer"],
    "career": ["hr_evaluator", "counselor", "product_manager", "investor", "senior_engineer"],
    "default": ["hr_evaluator", "counselor", "investor", "senior_engineer", "product_manager"]
}

def analyze_topic(topic: str) -> str:
    """分析辩题内容，确定适合的Agent类型"""
    topic = topic.lower()
    
    if any(keyword in topic for keyword in ["教育", "学习", "学校", "专业", "高考", "考研", "张雪峰"]):
        return "education"
    elif any(keyword in topic for keyword in ["商业", "投资", "创业", "市场", "公司", "盈利"]):
        return "business"
    elif any(keyword in topic for keyword in ["技术", "代码", "工程", "系统", "AI", "开发"]):
        return "technology"
    elif any(keyword in topic for keyword in ["心理", "情绪", "健康", "辅导", "治疗"]):
        return "psychology"
    elif any(keyword in topic for keyword in ["职业", "工作", "面试", "简历", "职场"]):
        return "career"
    else:
        return "default"

def get_relevant_agents(topic: str) -> list:
    """根据辩题获取相关的Agent列表"""
    topic_type = analyze_topic(topic)
    return AGENT_GROUPS.get(topic_type, AGENT_GROUPS["default"])

def load_agent_config(agent_name: str) -> dict:
    config_path = Path(__file__).parent / "agents" / f"{agent_name}.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_agent_system_prompt(config: dict, topic: str) -> str:
    return f"""你是一位{config['identity']['experience']}的{config['identity']['role']}。
{config['identity']['background']}

你的思维方式是：{config['cognitive_style']['thinking']}
你的评估标准是：{config['cognitive_style']['evaluation_criteria']}

你的优势是：{'；'.join(config['strengths'])}
你的盲点是：{'；'.join(config['blind_spots'])}

你的核心信念是：{'；'.join(config['core_beliefs'])}
你的辩论风格是：{config['debate_style']}
你的说话风格是：{config['speech_pattern']}

请基于以上背景，以{config['identity']['role']}的身份，对subencai-skills进行深度评估。
评估重点：{'；'.join(config['evaluation_focus'])}

辩题：{topic}

请给出你的专业评估，包括：
1. 核心观点（你的立场是什么）
2. 支持理由（为什么这么认为）
3. 潜在问题（你认为有什么不足）
4. 改进建议（如何做得更好）

请用你独特的视角和专业经验来评估。"""

def call_agent(client: OpenAI, agent_name: str, topic: str, model: str = "deepseek-chat") -> str:
    config = load_agent_config(agent_name)
    system_prompt = create_agent_system_prompt(config, topic)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请从{config['identity']['role']}的角度，对以下内容进行评估：{topic}"}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content

def create_moderator_prompt(agents_results: dict, topic: str) -> str:
    results_text = "\n\n".join([f"### {name.upper()} 的评估 ###\n{result}" for name, result in agents_results.items()])

    return f"""你是辩论主持人，组织了一场关于 subencai-skills 的多角度评估讨论。

辩题：{topic}

以下是各位评估者的意见：

{results_text}

请作为主持人：
1. 总结各位评估者的核心观点
2. 找出观点中的共识和分歧
3. 提出关键追问或补充视角
4. 引导讨论走向更深入的洞见

请给出你的主持总结。"""

def call_moderator(client: OpenAI, agents_results: dict, topic: str) -> str:
    system_prompt = create_moderator_prompt(agents_results, topic)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请主持这场讨论，给出总结。"}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content

def create_judge_prompt(moderator_summary: str, agents_results: dict) -> str:
    results_text = "\n\n".join([f"### {name.upper()} 的评估 ###\n{result}" for name, result in agents_results.items()])

    return f"""你是最终裁判，综合各方观点，给出最终裁决。

辩论总结：
{moderator_summary}

详细评估：
{results_text}

请给出最终裁决，必须包含：

## 共识
列出各方达成的共识

## 分歧
列出核心分歧点

## 裁决
给出明确的价值判断，并说明理由

## 建议
给出具体可执行的建议

请基于你的独立判断给出裁决。"""

def call_judge(client: OpenAI, moderator_summary: str, agents_results: dict) -> str:
    system_prompt = create_judge_prompt(moderator_summary, agents_results)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请给出最终裁决。"}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")

def generate_formatted_report(result, timestamp):
    """生成格式化的Markdown报告"""
    report_dir = Path(__file__).parent / "results"
    report_file = report_dir / f"debate_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 多Agent辩论系统报告\n\n")
        f.write(f"## 辩题\n{result['topic']}\n\n")
        f.write(f"## 时间\n{result['timestamp']}\n\n")
        f.write(f"## 提供商\n{result['provider']}\n\n")
        
        f.write("## 第一轮：各Agent独立评估\n\n")
        for agent_name, agent_result in result['agents'].items():
            config = load_agent_config(agent_name)
            role = config['identity']['role']
            f.write(f"### {role}\n\n")
            f.write(f"{agent_result}\n\n")
            f.write("---\n\n")
        
        f.write("## 第二轮：主持人总结\n\n")
        f.write(f"{result['moderator']}\n\n")
        f.write("---\n\n")
        
        f.write("## 第三轮：最终裁决\n\n")
        f.write(f"{result['judge']}\n\n")
    
    return report_file

def run_debate(topic: str = None):
    if topic is None:
        topic = "subencai-skills：从低谷到崛起的认知升级系统"

    client = get_client()

    print_section("多Agent辩论系统启动")
    print(f"Provider: DeepSeek")
    print(f"辩题: {topic}")

    # 根据辩题智能选择Agent
    agent_names = get_relevant_agents(topic)
    topic_type = analyze_topic(topic)
    print(f"辩题类型: {topic_type}")
    print(f"选择的Agent: {', '.join([load_agent_config(name)['identity']['role'] for name in agent_names])}")

    agent_results = {}

    print_section("第一轮：各Agent独立评估")

    for name in agent_names:
        config = load_agent_config(name)
        print(f"[Agent: {config['identity']['role']}] 评估中...")
        result = call_agent(client, name, topic)
        agent_results[name] = result
        print(f"[Agent: {config['identity']['role']}] 评估完成")

    print_section("第二轮：主持人总结")
    print("[主持人] 正在总结各方观点...")
    moderator_result = call_moderator(client, agent_results, topic)
    print("[主持人] 总结完成")

    print_section("第三轮：最终裁决")
    print("[裁判] 正在给出最终裁决...")
    judge_result = call_judge(client, moderator_result, agent_results)
    print("[裁判] 裁决完成")

    full_result = {
        "topic": topic,
        "provider": "deepseek",
        "timestamp": datetime.now().isoformat(),
        "agents": {name: agent_results[name] for name in agent_names},
        "moderator": moderator_result,
        "judge": judge_result
    }

    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"debate_result_{timestamp}.json"

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(full_result, f, ensure_ascii=False, indent=2)

    # 生成格式化报告
    report_file = generate_formatted_report(full_result, timestamp)

    print_section("辩论完成!")
    print(f"辩论结果已保存到: {result_file}")
    print(f"格式化报告已生成: {report_file}")

    print_section("最终裁决摘要")
    # 只显示前1500个字符，避免输出过长
    judge_summary = judge_result[:1500] + "..." if len(judge_result) > 1500 else judge_result
    print(judge_summary)

    return full_result

if __name__ == "__main__":
    import sys
    # 读取命令行参数作为辩题
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        # 默认辩题
        topic = """
        subencai-skills 评估辩题：

        subencai-skills 是一个基于真实经历的认知升级系统，
        帮助年轻人从低谷中崛起，实现自我突破和成长。
        它不是理论指导，而是一套可操作的工具包，
        基于作者从挂科十三门到成功逆袭的真实经历。

        请从HR、辅导员、投资人、工程师、产品经理五个角度
        对这个技能进行全面评估。
        """

    result = run_debate(topic)

    print("\n" + "=" * 60)
    print("最终裁决")
    print("=" * 60)
    print(result["judge"])

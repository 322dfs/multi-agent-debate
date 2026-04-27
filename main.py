"""
多Agent辩论系统 - 支持自由选择辩手、用户参与、智能摘要
主持人和裁判自动包含，辩手自由选择
"""

import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI

DEEPSEEK_API_KEY = "sk-355421af861547f6b4e24366614cf422"
BASE_URL = "https://api.deepseek.com/v1"

MODERATOR_AGENT = "debate_moderator"
JUDGE_AGENT = "final_judge"
SUMMARY_INTERVAL = 5  # 每5轮生成一次摘要

class DebateSession:
    """管理一场辩论的完整状态和上下文"""
    
    def __init__(self, topic: str, debaters: list):
        self.topic = topic
        self.debaters = debaters
        self.round_num = 1
        self.conversation_history = []  # 完整对话历史
        self.summaries = []  # 生成的摘要列表
        self.user_name = "用户"
        
    def add_message(self, speaker: str, content: str, message_type: str = "debater"):
        """添加一条发言到历史"""
        self.conversation_history.append({
            "round": self.round_num,
            "speaker": speaker,
            "content": content,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context_for_debater(self, debater_name: str) -> str:
        """为指定辩手获取上下文（包含摘要+最近轮次）"""
        context_parts = []
        
        # 添加之前的摘要
        if self.summaries:
            context_parts.append("=== 之前辩论的摘要 ===")
            for i, summary in enumerate(self.summaries, 1):
                context_parts.append(f"【第{i}个摘要】\n{summary}")
            context_parts.append("")
        
        # 获取需要详细显示的最近轮次
        if len(self.summaries) > 0:
            # 如果有摘要，只显示最近2轮的详细内容
            start_round = max(1, self.round_num - 2)
        else:
            # 前5轮显示完整历史
            start_round = 1
        
        recent_messages = [m for m in self.conversation_history if m["round"] >= start_round]
        
        if recent_messages:
            context_parts.append(f"=== 第{start_round}轮至今的详细发言 ===")
            for msg in recent_messages:
                if msg["speaker"] != debater_name:  # 不显示自己的发言
                    context_parts.append(f"【{msg['speaker']}】\n{msg['content']}")
        
        return "\n\n".join(context_parts) if context_parts else "这是第一轮辩论，暂无前序发言。"
    
    def should_generate_summary(self) -> bool:
        """检查是否需要生成摘要"""
        return self.round_num > 1 and self.round_num % SUMMARY_INTERVAL == 0
    
    def generate_summary(self, client: OpenAI) -> str:
        """生成当前阶段的摘要"""
        # 获取最近5轮的完整对话
        start_round = self.round_num - SUMMARY_INTERVAL + 1
        recent_messages = [m for m in self.conversation_history if start_round <= m["round"] <= self.round_num]
        
        history_text = "\n\n".join([
            f"【{msg['speaker']}】(第{msg['round']}轮)\n{msg['content']}"
            for msg in recent_messages
        ])
        
        prompt = f"""请对以下辩论内容进行摘要，需要包含：
1. 各方的主要立场和核心论点
2. 关键的交锋点和分歧
3. 是否有观点的转变或妥协
4. 目前的讨论焦点

辩题：{self.topic}

辩论内容：
{history_text}

请生成简洁但信息完整的摘要（300字以内）："""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的辩论摘要生成器。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        summary = response.choices[0].message.content
        self.summaries.append(summary)
        return summary
    
    def next_round(self):
        """进入下一轮"""
        self.round_num += 1


def get_client():
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)


def load_agent_config(agent_name: str) -> dict:
    config_path = Path(__file__).parent / "agents" / f"{agent_name}.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_debater_agents():
    agents_dir = Path(__file__).parent / "agents"
    all_agents = [f.stem for f in agents_dir.glob("*.json")]
    debaters = [a for a in all_agents if a not in [MODERATOR_AGENT, JUDGE_AGENT]]
    return debaters


def create_debater_system_prompt(config: dict, topic: str, context: str, round_num: int) -> str:
    round_note = f"\n\n（这是第{round_num}轮辩论）" if round_num > 1 else ""

    return f"""你是一位{config['identity']['experience']}的{config['identity']['role']}。
{config['identity']['background']}

你的思维方式是：{config['cognitive_style']['thinking']}
你的评估标准是：{config['cognitive_style']['evaluation_criteria']}

你的优势是：{'；'.join(config['strengths'])}
你的盲点是：{'；'.join(config['blind_spots'])}

你的核心信念是：{'；'.join(config['core_beliefs'])}
你的辩论风格是：{config['debate_style']}
你的说话风格是：{config['speech_pattern']}

=== 辩论上下文 ===
{context}{round_note}

辩题：{topic}

请以{config['identity']['role']}的身份参与辩论。
要求：
1. 给出你对这个问题的核心观点和立场
2. 用你自己的经历、信念和说话风格来表达
3. 如果有其他人的观点，可以反驳、补充或认同
4. 保持你角色特有的语言风格和辩论方式
5. 记住你之前说过什么，保持观点的一致性

请开始你的发言："""


def call_debater(client: OpenAI, agent_name: str, topic: str, context: str, round_num: int) -> str:
    config = load_agent_config(agent_name)
    system_prompt = create_debater_system_prompt(config, topic, context, round_num)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请开始你的辩论发言。"}
        ],
        temperature=0.8
    )

    return response.choices[0].message.content


def create_moderator_prompt(context: str, topic: str) -> str:
    return f"""你是这场辩论的主持人。

辩题：{topic}

以下是辩论的完整历史（包括摘要和详细发言）：

{context}

请作为主持人：
1. 总结各位辩手的核心观点和立场
2. 找出观点中的共识和分歧
3. 提出关键追问或补充视角
4. 引导讨论走向更深入的洞见
5. 适当点评各方辩论风格和亮点

请给出你的主持总结和点评。"""


def call_moderator(client: OpenAI, session: DebateSession) -> str:
    context = session.get_context_for_debater("moderator")
    system_prompt = create_moderator_prompt(context, session.topic)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请主持这场辩论，给出总结。"}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


def create_judge_prompt(context: str, topic: str) -> str:
    return f"""你是辩论裁判，综合各方观点，给出最终裁决。

辩题：{topic}

以下是辩论的完整历史：

{context}

请给出最终裁决，必须包含：

## 共识
列出各方达成的基本共识

## 分歧
列出核心分歧点，以及各方的主要论点

## 裁决
给出明确的价值判断，说明哪方的观点更有道理，以及为什么

## 建议
给出对这个辩题问题的具体建议或结论

请基于你的独立判断给出裁决。"""


def call_judge(client: OpenAI, session: DebateSession) -> str:
    context = session.get_context_for_debater("judge")
    system_prompt = create_judge_prompt(context, session.topic)

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


def save_debate_result(session: DebateSession, judge_result: str):
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"debate_result_{timestamp}.json"
    
    result = {
        "topic": session.topic,
        "timestamp": datetime.now().isoformat(),
        "round": session.round_num,
        "debaters": session.debaters,
        "conversation_history": session.conversation_history,
        "summaries": session.summaries,
        "judge": judge_result
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result_file


def generate_formatted_report(session: DebateSession, judge_result: str):
    report_dir = Path(__file__).parent / "results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"debate_report_{timestamp}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 多Agent辩论系统报告\n\n")
        f.write(f"## 辩题\n{session.topic}\n\n")
        f.write(f"## 时间\n{datetime.now().isoformat()}\n\n")
        f.write(f"## 辩论轮次\n第{session.round_num}轮\n\n")
        f.write(f"## 参与辩手\n{', '.join(session.debaters)}\n\n")
        
        if session.summaries:
            f.write("## 辩论摘要\n\n")
            for i, summary in enumerate(session.summaries, 1):
                f.write(f"### 第{i}个摘要（第{(i-1)*SUMMARY_INTERVAL+1}-{i*SUMMARY_INTERVAL}轮）\n\n")
                f.write(f"{summary}\n\n")
            f.write("---\n\n")

        f.write("## 完整辩论记录\n\n")
        current_round = 0
        for msg in session.conversation_history:
            if msg["round"] != current_round:
                current_round = msg["round"]
                f.write(f"### 第{current_round}轮\n\n")
            f.write(f"**{msg['speaker']}**：\n{msg['content']}\n\n")

        f.write("## 最终裁决\n\n")
        f.write(f"{judge_result}\n\n")

    return report_file


def user_participate(session: DebateSession) -> str:
    """让用户参与辩论"""
    print_section("你的发言机会")
    print("你可以输入你的观点或质疑（直接回车跳过）：")
    user_input = input("> ").strip()
    
    if user_input:
        session.add_message(session.user_name, user_input, "user")
        print(f"\n【{session.user_name}】已发言")
        return user_input
    return None


def run_debate_round(session: DebateSession, allow_user: bool = True):
    """运行一轮辩论"""
    client = get_client()
    
    print_section(f"第{session.round_num}轮辩论")
    print(f"辩题: {session.topic}")
    print(f"辩手: {', '.join([load_agent_config(name)['identity']['role'] for name in session.debaters])}")
    
    # 检查是否需要生成摘要
    if session.should_generate_summary():
        print("\n[系统] 正在生成阶段摘要...")
        summary = session.generate_summary(client)
        print(f"[系统] 摘要生成完成")
        print(f"\n=== 阶段摘要 ===\n{summary}\n")
    
    # 辩手发言
    print_section("辩手发言")
    for name in session.debaters:
        config = load_agent_config(name)
        context = session.get_context_for_debater(name)
        
        print(f"\n[{config['identity']['role']}] 发言中...")
        result = call_debater(client, name, session.topic, context, session.round_num)
        session.add_message(config['identity']['role'], result, "debater")
        print(f"[{config['identity']['role']}] 发言完成")
    
    # 用户参与（可选）
    if allow_user:
        user_input = user_participate(session)
        if user_input:
            # 如果用户发言，让辩手回应
            print("\n[系统] 辩手们将回应你的观点...")
            for name in session.debaters:
                config = load_agent_config(name)
                context = session.get_context_for_debater(name)
                
                print(f"\n[{config['identity']['role']}] 回应中...")
                result = call_debater(client, name, session.topic, context, session.round_num)
                session.add_message(config['identity']['role'], result, "debater")
                print(f"[{config['identity']['role']}] 回应完成")
    
    session.next_round()


def run_moderator_and_judge(session: DebateSession) -> str:
    """运行主持人和裁判环节"""
    client = get_client()
    
    print_section("主持人总结")
    print("[主持人] 正在总结各方观点...")
    moderator_result = call_moderator(client, session)
    print("[主持人] 总结完成")

    print_section("裁判裁决")
    print("[裁判] 正在给出最终裁决...")
    judge_result = call_judge(client, session)
    print("[裁判] 裁决完成")
    
    return moderator_result, judge_result


def interactive_mode():
    print("\n" + "="*60)
    print("欢迎使用多Agent辩论系统")
    print("="*60)

    topic = input("\n请输入辩论题目（直接回车使用默认题目）：").strip()
    if not topic:
        topic = "年轻人应该先就业还是先考研？"

    debaters = list_debater_agents()
    print("\n" + "="*60)
    print("选择参与辩论的辩手")
    print("="*60)
    print("可选择的辩手列表：")
    for i, agent_name in enumerate(debaters, 1):
        try:
            config = load_agent_config(agent_name)
            print(f"  {i}. {agent_name} - {config['identity']['role']}")
        except:
            print(f"  {i}. {agent_name}")

    print("\n输入数字选择辩手（用逗号分隔，如：1,3,5）：")
    print("输入 'all' 选择全部辩手")
    print("输入 'q' 退出")

    choice = input("请选择：").strip()

    if choice.lower() == 'q':
        print("已退出")
        return
    elif choice.lower() == 'all':
        selected_debaters = debaters
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_debaters = [debaters[i] for i in indices if 0 <= i < len(debaters)]
        except:
            print("无效选择，默认使用全部辩手")
            selected_debaters = debaters

    if not selected_debaters:
        print("已退出")
        return

    print(f"\n已选择 {len(selected_debaters)} 位辩手参与辩论")
    print("主持人（debate_moderator）和裁判（final_judge）自动包含")
    print(f"每{SUMMARY_INTERVAL}轮自动生成一次摘要")

    # 创建辩论会话
    session = DebateSession(topic, selected_debaters)

    while True:
        # 运行一轮辩论
        run_debate_round(session, allow_user=True)
        
        # 主持人和裁判环节
        moderator_result, judge_result = run_moderator_and_judge(session)

        # 保存结果
        result_file = save_debate_result(session, judge_result)
        report_file = generate_formatted_report(session, judge_result)

        print_section(f"第{session.round_num - 1}轮辩论完成!")
        print(f"详细结果已保存到: {result_file}")
        print(f"格式化报告已生成: {report_file}")

        print("\n" + "="*60)
        print("最终裁决")
        print("="*60)
        print(judge_result)

        print("\n" + "="*60)
        print("你的决定")
        print("="*60)
        print("1. 接受裁决 - 结束辩论")
        print("2. 质疑裁决 - 进入下一轮辩论")
        print("3. 立即发言 - 提出观点后继续辩论")
        print("4. 更换辩手 - 重新选择参与者（重置辩论）")
        print("5. 更换题目 - 重新输入辩题（重置辩论）")
        print("6. 退出")

        choice = input("请选择（1-6）：").strip()

        if choice == '1':
            print("\n感谢使用辩论系统，再见！")
            break
        elif choice == '2':
            print(f"\n进入第{session.round_num}轮辩论...")
        elif choice == '3':
            user_input = user_participate(session)
            if user_input:
                print(f"\n进入第{session.round_num}轮辩论，辩手将回应你的观点...")
            else:
                print("\n未发言，继续当前轮次...")
        elif choice == '4':
            # 重新选择辩手，重置会话
            print("\n重新选择辩手...")
            choice2 = input("输入数字选择辩手（用逗号分隔）：").strip()
            if choice2.lower() == 'all':
                selected_debaters = debaters
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in choice2.split(",")]
                    selected_debaters = [debaters[i] for i in indices if 0 <= i < len(debaters)]
                except:
                    print("无效选择")
                    continue
            session = DebateSession(topic, selected_debaters)
            print("\n已重置辩论，开始新一轮...")
        elif choice == '5':
            topic = input("\n请输入新的辩论题目：").strip()
            if not topic:
                topic = "年轻人应该先就业还是先考研？"
            session = DebateSession(topic, selected_debaters)
            print("\n已重置辩论，开始新一轮...")
        else:
            print("\n感谢使用辩论系统，再见！")
            break


if __name__ == "__main__":
    interactive_mode()

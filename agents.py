import json
from pathlib import Path
from crewai import Agent
from openai import OpenAI

def load_agent_config(agent_name: str) -> dict:
    config_path = Path(__file__).parent / "agents" / f"{agent_name}.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_deepseek_client():
    return OpenAI(
        api_key="sk-355421af861547f6b4e24366614cf422",
        base_url="https://api.deepseek.com/v1"
    )

def create_agents():
    client = get_deepseek_client()

    agents_config = {
        "hr_evaluator": load_agent_config("hr_evaluator"),
        "counselor": load_agent_config("counselor"),
        "investor": load_agent_config("investor"),
        "senior_engineer": load_agent_config("senior_engineer"),
        "product_manager": load_agent_config("product_manager"),
    }

    agents = {}

    for agent_key, config in agents_config.items():
        agents[agent_key] = Agent(
            role=config["identity"]["role"],
            goal=f"从{config['identity']['role']}视角，对subencai-skills进行全面评估，并给出具体建议",
            backstory=f"""
            你是一位{config['identity']['experience']}的{config['identity']['role']}。
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
            """,
            verbose=True,
            llm={"model": "deepseek-chat", "client": client},
            allow_delegation=False
        )

    return agents

def create_moderator():
    client = get_deepseek_client()
    config = load_agent_config("debate_moderator")

    return Agent(
        role=config["identity"]["role"],
        goal="引导多Agent辩论有序进行，确保每方观点都被充分表达",
        backstory=f"""
        你是一位{config['identity']['experience']}的{config['identity']['role']}。
        {config['identity']['background']}

        你的思维方式是：{config['cognitive_style']['thinking']}

        你的核心信念是：{'；'.join(config['core_beliefs'])}
        你的辩论风格是：{config['debate_style']}

        你的职责是：{'；'.join(config['responsibilities'])}
        """,
        verbose=True,
        llm={"model": "deepseek-chat", "client": client},
        allow_delegation=False
    )

def create_judge():
    client = get_deepseek_client()
    config = load_agent_config("final_judge")

    return Agent(
        role=config["identity"]["role"],
        goal="综合各方观点，给出最终裁决和可执行的建议",
        backstory=f"""
        你是一位{config['identity']['experience']}的{config['identity']['role']}。
        {config['identity']['background']}

        你的思维方式是：{config['cognitive_style']['thinking']}
        你的评估标准是：{config['cognitive_style']['evaluation_criteria']}

        你的核心信念是：{'；'.join(config['core_beliefs'])}
        你的裁决风格是：{config['debate_style']}

        输出格式：
        - 共识：各方达成的共识
        - 分歧：核心分歧点
        - 裁决：最终裁决及理由
        - 建议：可执行的建议
        """,
        verbose=True,
        llm={"model": "deepseek-chat", "client": client},
        allow_delegation=False
    )

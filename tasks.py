from crewai import Task
from typing import Dict, List

def create_debate_tasks(agents: Dict, topic: str) -> List[Task]:
    task_descriptions = {
        "hr_evaluator": f"""作为资深HR，请从以下角度评估 subencai-skills：

评估内容：
1. 这个技能对求职者找工作的实际帮助有多大？
2. 能否帮助候选人在面试中差异化脱颖而出？
3. 面试官会如何看待这种技能？加分项还是鸡肋？

请给出具体的评估和可执行的建议。

辩题/评估对象：{topic}""",

        "counselor": f"""作为大学辅导员/心理咨询师，请从以下角度评估 subencai-skills：

评估内容：
1. 对学业崩溃的学生有多大的实际帮助？
2. 方法是否足够温和，不会造成二次伤害？
3. 能否被高校心理健康中心采纳使用？

请给出具体的评估和可执行的建议。

辩题/评估对象：{topic}""",

        "investor": f"""作为早期投资人，请从以下角度评估 subencai-skills：

评估内容：
1. 这个项目的商业模式是什么？能否规模化？
2. 目标用户群体是否足够精准和可持续？
3. 有没有形成竞争壁垒的可能性？

请给出具体的评估和可执行的建议。

辩题/评估对象：{topic}""",

        "senior_engineer": f"""作为资深工程师/技术面试官，请从以下角度评估 subencai-skills：

评估内容：
1. 这个方法论能否真正落地执行？
2. 有没有具体的工具和模板支撑？
3. 如何验证学习效果？是否有量化标准？

请给出具体的评估和可执行的建议。

辩题/评估对象：{topic}""",

        "product_manager": f"""作为产品经理，请从以下角度评估 subencai-skills：

评估内容：
1. 用户会不会真的用这个产品？使用场景是什么？
2. 能否形成持续的使用习惯？
3. 产品的增长瓶颈在哪里？

请给出具体的评估和可执行的建议。

辩题/评估对象：{topic}""",
    }

    tasks = []
    for agent_key, description in task_descriptions.items():
        task = Task(
            description=description,
            agent=agents[agent_key],
            expected_output="一份深度评估报告，包含具体分析和可执行的建议"
        )
        tasks.append(task)

    return tasks

def create_moderator_task(moderator, agents: Dict, topic: str) -> Task:
    agent_names = list(agents.keys())

    return Task(
        description=f"""作为辩论主持人，请组织一场关于 subencai-skills 的多角度辩论。

辩题：{topic}

流程：
1. 开场介绍：简要介绍辩题和参与各方
2. 观点收集：从各方收集评估意见
3. 观点碰撞：引导各方进行有意义的讨论
4. 追问关键：针对关键问题进行深入探讨
5. 总结要点：归纳各方的核心观点

参与方：
- {agent_names[0]}：资深HR，评估求职价值
- {agent_names[1]}：大学辅导员，评估对学生心理的帮助
- {agent_names[2]}：早期投资人，评估商业价值
- {agent_names[3]}：资深工程师，评估可执行性
- {agent_names[4]}：产品经理，评估用户体验

请确保每方观点都被充分表达，然后给出辩论总结。""",
        agent=moderator,
        expected_output="一份辩论总结，包含各方核心观点和碰撞产生的洞见"
    )

def create_judge_task(judge, debate_results: List[str]) -> Task:
    return Task(
        description=f"""作为最终裁判，请综合各方观点，对 subencai-skills 给出最终裁决。

各方观点汇总：
{chr(10).join(debate_results)}

请给出：
1. 共识：各方达成的共识
2. 分歧：核心分歧点
3. 裁决：最终裁决及理由（必须给出明确的价值判断）
4. 建议：给subencai-skills作者的可执行建议""",
        agent=judge,
        expected_output="一份包含共识、分歧、裁决和建议的完整报告"
    )

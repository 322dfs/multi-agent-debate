# Multi-Agent Debate System - 多智能体辩论系统

## 项目概述

这是一个基于 DeepSeek API 的多智能体辩论系统，能够根据不同的辩题自动选择合适的社会角色进行多角度辩论，最终形成综合裁决。

### 核心特性

- **智能辩题分析**：系统自动识别辩题类型（教育、商业、技术、心理、职业等）
- **动态Agent选择**：根据辩题类型自动选择最合适的辩论者组合
- **多角度评估**：5个不同社会身份的Agent从各自专业角度进行评估
- **结构化输出**：生成包含共识、分歧、裁决和建议的完整报告

## 系统架构

### 核心模块

```
main.py          # 主程序入口，负责流程编排
agents.py        # Agent配置管理和LLM调用
tasks.py         # 任务定义和提示词模板
```

### Agent体系

系统包含7个专业Agent，分为两类：

#### 专业评估Agent（5个）

| Agent            | 社会身份  | 核心视角    | 适用辩题类型 |
| ---------------- | ----- | ------- | ------ |
| hr\_evaluator    | 资深HR  | 求职价值评估  | 职业、教育  |
| counselor        | 大学辅导员 | 心理健康评估  | 心理、教育  |
| investor         | 早期投资人 | 商业价值评估  | 商业、技术  |
| senior\_engineer | 资深工程师 | 技术可行性评估 | 技术     |
| product\_manager | 产品经理  | 用户体验评估  | 商业、技术  |

#### 协调Agent（2个）

| Agent             | 社会身份  | 核心功能           |
| ----------------- | ----- | -------------- |
| debate\_moderator | 辩论主持人 | 总结各方观点，找出共识与分歧 |
| final\_judge      | 最终裁判  | 综合裁决，给出明确建议    |

## 智能辩题选择机制

### 实现原理

系统在 `agents.py` 中定义了 `AGENT_GROUPS` 字典，根据辩题关键词匹配最合适的Agent组合：

```python
AGENT_GROUPS = {
    "education": ["hr_evaluator", "counselor", "investor", "senior_engineer", "product_manager"],
    "business": ["investor", "product_manager", "hr_evaluator", "senior_engineer", "counselor"],
    "technology": ["senior_engineer", "product_manager", "investor", "hr_evaluator", "counselor"],
    "psychology": ["counselor", "hr_evaluator", "product_manager", "investor", "senior_engineer"],
    "career": ["hr_evaluator", "counselor", "product_manager", "investor", "senior_engineer"],
    "default": ["hr_evaluator", "counselor", "investor", "senior_engineer", "product_manager"]
}
```

### 辩题分析流程

```
用户输入辩题
    ↓
analyze_topic() 函数分析
    ↓
提取关键词并匹配类型
    ↓
返回最合适的Agent列表
    ↓
get_relevant_agents() 获取Agent组合
    ↓
开始辩论流程
```

### 关键词匹配规则

| 辩题类型 | 关键词                   | Agent优先级            |
| ---- | --------------------- | ------------------- |
| 教育   | 教育、学习、学校、专业、高考、考研、张雪峰 | HR、辅导员、投资人、工程师、产品经理 |
| 商业   | 商业、投资、创业、市场、公司、盈利     | 投资人、产品经理、HR、工程师、辅导员 |
| 技术   | 技术、代码、工程、系统、AI、开发     | 工程师、产品经理、投资人、HR、辅导员 |
| 心理   | 心理、情绪、健康、辅导、治疗        | 辅导员、HR、产品经理、投资人、工程师 |
| 职业   | 职业、工作、面试、简历、职场        | HR、辅导员、产品经理、投资人、工程师 |

## 辩论流程

### 三阶段辩论模型

1. **第一阶段：独立评估**
   - 各Agent根据自身专业背景独立评估辩题
   - 输出包含：核心观点、支持理由、潜在问题、改进建议
2. **第二阶段：主持人总结**
   - 主持人整合各方观点
   - 找出共识与分歧
   - 提出关键追问
3. **第三阶段：最终裁决**
   - 裁判综合所有观点
   - 给出明确的价值判断
   - 提供具体可执行的建议

## 目录结构

```
multi-agent-debate/
├── agents/              # Agent配置文件(JSON格式)
│   ├── hr_evaluator.json        # HR评估者配置
│   ├── counselor.json           # 辅导员配置
│   ├── investor.json            # 投资人配置
│   ├── senior_engineer.json     # 工程师配置
│   ├── product_manager.json     # 产品经理配置
│   ├── debate_moderator.json    # 主持人配置
│   └── final_judge.json        # 裁判配置
├── skills/              # Agent技能描述(Markdown格式)
├── results/              # 辩论结果(JSON和Markdown格式)
├── main.py               # 主程序入口
├── agents.py             # Agent管理和LLM调用
├── tasks.py              # 任务定义
├── requirements.txt      # Python依赖
└── .env.example          # 环境变量模板
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

复制环境变量模板并编辑：

```bash
copy .env.example .env
```

在 `.env` 文件中填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 运行辩论

```bash
# 使用默认辩题
python main.py

# 使用自定义辩题
python main.py "张雪峰的教育理念是否适合中国普通家庭的孩子？"

# 使用任意辩题，系统会自动选择合适的Agent
python main.py "你的辩题内容"
```

### 4. 查看结果

辩论完成后，结果会自动保存到 `results/` 目录：

- JSON格式：`debate_result_时间戳.json`
- Markdown格式：`debate_report_时间戳.md`

## 使用示例

### 教育类辩题

```bash
python main.py "张雪峰的教育理念是否适合中国普通家庭的孩子？"
```

系统会识别为"education"类型，优先选择HR、辅导员等教育相关Agent。

### 商业类辩题

```bash
python main.py "这个创业项目是否值得投资？"
```

系统会识别为"business"类型，优先选择投资人、产品经理等商业相关Agent。

### 技术类辩题

```bash
python main.py "这个技术方案是否可行？"
```

系统会识别为"technology"类型，优先选择工程师、产品经理等技术相关Agent。

## 自定义扩展

### 添加新的Agent类型

1. 在 `agents/` 目录创建新的JSON配置文件
2. 在 `skills/` 目录创建对应的Markdown描述
3. 在 `agents.py` 的 `AGENT_GROUPS` 中添加新的类型和Agent组合

### 修改辩题分析逻辑

编辑 `agents.py` 中的 `analyze_topic()` 函数，添加新的关键词匹配规则。

### 调整Agent优先级

修改 `AGENT_GROUPS` 字典中各类型的Agent顺序，即可调整不同辩题类型下的Agent优先级。

## 技术栈

- **Python 3.10+**
- **OpenAI SDK**（DeepSeek API兼容）
- **DeepSeek Chat Model**

## 注意事项

- 确保API Key有效且有足够余额
- 完整辩论可能需要3-5分钟
- 辩论结果会同时保存为JSON和Markdown两种格式


from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from docx import Document
from pypdf import PdfReader

BASE_DIR = Path(__file__).parent
# 固定从项目目录加载 .env，避免因启动 cwd 不同导致读不到 key
load_dotenv(BASE_DIR / ".env")
AGENTS_DIR = BASE_DIR / "agents"
APP_DATA_DIR = Path(os.getenv("DEBATE_APP_DATA_DIR", Path.home() / ".multi-agent-debate-v2"))
RESULTS_DIR = APP_DATA_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR = APP_DATA_DIR / "resumes"
RESUME_DIR.mkdir(parents=True, exist_ok=True)
RESUME_EVAL_DIR = APP_DATA_DIR / "resume_evaluations"
RESUME_EVAL_DIR.mkdir(parents=True, exist_ok=True)
CUSTOM_POSITIONS_FILE = APP_DATA_DIR / "custom_positions.json"

MODEL_NAME = os.getenv("DEBATE_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")

app = FastAPI(title="Multi Agent Debate API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

debate_sessions: Dict[str, Dict[str, Any]] = {}

AGENT_SCENARIOS: Dict[str, str] = {
    "it_ops_manager": "it",
    "platform_engineer": "it",
    "security_engineer": "it",
    "qa_test_engineer": "it",
    "it_project_manager": "it",
    "senior_engineer": "it",
    "product_manager": "it",
    "hr_evaluator": "career",
    "zhangxuefeng": "career",
    "investor": "business",
    "small_business_owner": "business",
    "lawyer_public_policy": "governance",
    "civil_servant": "governance",
    "doctor_public_health": "society",
    "journalist_observer": "society",
    "factory_worker": "society",
    "counselor": "society",
    "phoenix_riser": "career",
}

POSITION_PROFILES: Dict[str, Dict[str, Any]] = {
    "embedded_software_engineer": {
        "id": "embedded_software_engineer",
        "title": "嵌入式软件工程师 Embedded Software Engineer",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "参与芯片配套固件与驱动方案设计，完成模块开发与联调",
            "与硬件、测试团队协作定位板级与系统级问题",
            "沉淀自动化测试脚本与故障复盘文档",
        ],
        "must_have": [
            "C/C++ 扎实基础",
            "嵌入式 Linux 或 RTOS 开发经验",
            "驱动/固件调试能力",
            "良好工程实践（版本控制、测试、文档）",
        ],
        "plus": [
            "半导体/光模块/高速通信相关经验",
            "Python 自动化测试经验",
            "跨团队协作与问题定位能力",
        ],
    },
    "chip_test_engineer": {
        "id": "chip_test_engineer",
        "title": "芯片测试工程师 Chip Test Engineer",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "负责芯片功能、性能与可靠性测试方案设计",
            "搭建并维护实验室测试流程，输出可复用测试模板",
            "针对异常数据进行定位分析并推动闭环",
        ],
        "must_have": [
            "测试方案设计与执行能力",
            "数据分析与问题定位能力",
            "电子/通信/微电子基础扎实",
            "测试自动化意识（脚本或工具链）",
        ],
        "plus": [
            "ATE 或实验室测试平台经验",
            "硅光/光模块测试经验",
            "与设计/工艺联合调试经验",
        ],
    },
    "silicon_photonics_engineer": {
        "id": "silicon_photonics_engineer",
        "title": "硅光芯片工程师 Silicon Photonics Engineer",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "参与硅光器件设计、仿真与实验验证",
            "支持工艺/封装协同优化，推进器件量产可行性",
            "沉淀仿真模型与测试数据分析报告",
        ],
        "must_have": [
            "光电子/微电子相关理论基础",
            "器件或版图/工艺理解能力",
            "建模、仿真或实验验证经验",
            "科研与工程落地结合能力",
        ],
        "plus": [
            "硅光、CPO、光互联相关项目经验",
            "跨学科协作能力（光学、电学、封装）",
            "论文/专利/竞赛成果",
        ],
    },
    "it_system_engineer": {
        "id": "it_system_engineer",
        "title": "IT系统工程师 IT Systems Engineer",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "负责办公网络、终端、权限与基础系统稳定运行",
            "建设并维护运维自动化脚本和监控告警机制",
            "配合业务部门推进 IT 服务流程优化",
        ],
        "must_have": [
            "熟悉 Windows/Linux 日常运维与故障排查",
            "掌握网络基础（交换、路由、DNS、VPN）",
            "具备脚本能力（Python/PowerShell/Shell 任一）",
            "具备 IT 服务意识与跨部门沟通能力",
        ],
        "plus": [
            "有 AD/域控、虚拟化或容器平台维护经验",
            "有企业信息安全基线治理经验",
            "有 ITIL 或运维流程体系经验",
        ],
    },
    "hrbp_specialist": {
        "id": "hrbp_specialist",
        "title": "人力资源专员 HRBP Specialist",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "支撑招聘、入离职、试用期跟踪与人才盘点",
            "推动绩效沟通与组织氛围建设",
            "结合业务阶段输出人才策略建议",
        ],
        "must_have": [
            "具备招聘与员工关系处理经验",
            "具备结构化沟通与跨团队协作能力",
            "熟悉劳动法规与基础人事流程",
            "数据敏感度较好，能做基础人效分析",
        ],
        "plus": [
            "有制造业/半导体行业 HR 经验",
            "有组织发展或培训体系搭建经验",
            "有中高端技术岗位招聘经验",
        ],
    },
    "product_manager_it_tools": {
        "id": "product_manager_it_tools",
        "title": "内部工具产品经理 Product Manager (Internal Tools)",
        "company": "上海孛璞半导体技术有限公司",
        "responsibilities": [
            "梳理研发与运营流程痛点，规划内部系统产品路线",
            "产出 PRD、流程图与指标体系，推动上线迭代",
            "协同研发、测试、业务做需求优先级管理",
        ],
        "must_have": [
            "有 B 端产品经验与需求拆解能力",
            "熟悉原型、流程与数据指标设计",
            "具备跨部门推动能力与项目管理意识",
            "能基于业务目标进行优先级决策",
        ],
        "plus": [
            "有研发管理平台或企业协同系统经验",
            "了解半导体研发或供应链流程",
            "具备 SQL 或数据分析能力",
        ],
    },
}

RESUME_REVIEWERS: List[Dict[str, str]] = [
    {
        "id": "hiring_manager",
        "name": "招聘经理 Hiring Manager",
        "focus": "岗位匹配度、可胜任性、入职风险",
    },
    {
        "id": "tech_interviewer",
        "name": "技术面试官 Technical Interviewer",
        "focus": "技术深度、项目真实性、工程能力",
    },
    {
        "id": "business_reviewer",
        "name": "业务负责人 Business Reviewer",
        "focus": "业务理解、成长潜力、协作与执行",
    },
    {
        "id": "hrbp",
        "name": "HRBP",
        "focus": "稳定性、沟通能力、文化适配与薪资预期风险",
    },
]


class DebateStartRequest(BaseModel):
    topic: str
    debaters: List[str] = []


class DebateRoundRequest(BaseModel):
    session_id: str


class UserMessageRequest(BaseModel):
    session_id: str
    message: str


class NextRoundRequest(BaseModel):
    session_id: str


class ModerateRequest(BaseModel):
    session_id: str


class JudgeRequest(BaseModel):
    session_id: str


class DecisionRequest(BaseModel):
    session_id: str
    decision: str
    user_conclusion: str | None = None


class ExecutionStatusRequest(BaseModel):
    session_id: str
    status: str
    note: str | None = None


class AutoDebateRequest(BaseModel):
    session_id: str
    max_rounds: int = 3


class CustomPositionRequest(BaseModel):
    title: str
    company: str = "自定义岗位"
    responsibilities: List[str] = []
    must_have: List[str] = []
    plus: List[str] = []


def now_iso() -> str:
    return datetime.now().isoformat()


def get_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="缺少 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，无法生成真实辩论内容。",
        )
    return api_key


def get_client() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=LLM_BASE_URL)


def session_file(session_id: str) -> Path:
    return RESULTS_DIR / f"session_{session_id}.json"


def persist_session(session: Dict[str, Any]) -> None:
    session["updated_at"] = now_iso()
    with session_file(session["session_id"]).open("w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def load_agent_config(agent_name: str) -> Dict[str, Any]:
    config_path = AGENTS_DIR / f"{agent_name}.json"
    if not config_path.exists():
        raise HTTPException(status_code=400, detail=f"找不到辩手配置: {agent_name}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_debaters() -> list[Dict[str, str]]:
    excluded_agents = {"debate_moderator", "final_judge"}
    results = []
    for filepath in sorted(AGENTS_DIR.glob("*.json")):
        agent_id = filepath.stem
        if agent_id in excluded_agents:
            continue
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
        results.append(
            {
                "id": data.get("name", agent_id),
                "name": data.get("display_name", data.get("name", agent_id)),
                "display_name": data.get("display_name", data.get("name", agent_id)),
                "role": data.get("identity", {}).get("role", "辩手"),
                "description": data.get("description", ""),
                "scenario": AGENT_SCENARIOS.get(agent_id, "general"),
            }
        )
    return results


DEBATER_TOPIC_HINTS: Dict[str, List[str]] = {
    "counselor": ["心理", "情绪", "焦虑", "抑郁", "辅导", "学生", "校园", "成长", "家庭", "教育"],
    "zhangxuefeng": ["高考", "考研", "志愿", "升学", "专业", "学历", "院校", "教育", "就业"],
    "senior_engineer": ["程序", "开发", "工程", "系统", "算法", "代码", "架构", "技术", "ai", "人工智能", "it", "运维", "上线", "故障", "服务器"],
    "product_manager": ["产品", "用户", "需求", "体验", "增长", "运营", "商业化", "市场", "it系统", "内部工具", "流程优化"],
    "hr_evaluator": ["面试", "简历", "招聘", "求职", "薪资", "职场", "人力", "hr", "offer"],
    "investor": ["投资", "创业", "融资", "估值", "赛道", "商业", "利润", "市场", "公司"],
    "phoenix_riser": ["逆袭", "底层", "普通人", "奋斗", "自我提升", "转型", "翻身", "成长"],
    "lawyer_public_policy": ["法律", "合规", "监管", "政策", "权益", "公平", "劳动法", "合同", "司法"],
    "factory_worker": ["工厂", "制造", "产线", "蓝领", "工时", "加班", "安全生产", "一线", "车间"],
    "small_business_owner": ["个体户", "门店", "创业", "现金流", "成本", "利润", "经营", "小微企业"],
    "doctor_public_health": ["医疗", "健康", "公共卫生", "医院", "疾病", "防疫", "心理健康", "慢病"],
    "journalist_observer": ["媒体", "舆论", "新闻", "真相", "信息", "传播", "公信力", "调查"],
    "civil_servant": ["政府", "治理", "公共服务", "民生", "政策执行", "基层", "行政", "社会稳定"],
    "it_ops_manager": ["it运维", "运维", "值班", "故障", "恢复", "监控", "告警", "稳定性", "变更窗口", "sla", "mttr"],
    "platform_engineer": ["devops", "ci", "cd", "流水线", "发布", "自动化", "容器", "部署", "配置管理", "灰度发布"],
    "security_engineer": ["安全", "漏洞", "权限", "审计", "合规", "最小权限", "零信任", "风险控制", "攻防", "数据安全"],
    "qa_test_engineer": ["测试", "回归", "质量", "验收", "用例", "测试覆盖", "发布质量", "质量门禁", "qa"],
    "it_project_manager": ["项目管理", "里程碑", "排期", "交付", "owner", "deadline", "协同", "资源", "优先级"],
}


IT_DECISION_HINTS: List[str] = [
    "it", "it部门", "运维", "服务台", "工单", "网络", "权限", "账号", "vpn",
    "监控", "告警", "日志", "服务器", "故障", "上线", "发布", "内网", "邮件系统",
]


def is_it_decision_topic(topic: str) -> bool:
    text = (topic or "").strip().lower()
    return any(x in text for x in IT_DECISION_HINTS)


def recommend_debaters_for_topic(
    topic: str,
    min_count: int = 3,
    preferred_scenario: str | None = None,
) -> List[Dict[str, Any]]:
    debaters = load_debaters()
    topic_text = (topic or "").strip().lower()
    it_mode = is_it_decision_topic(topic_text)
    scenario_mode = (preferred_scenario or "").strip().lower()
    if scenario_mode in {"", "all"}:
        scenario_mode = ""
    it_agents = {"it_ops_manager", "platform_engineer", "security_engineer", "qa_test_engineer", "it_project_manager", "senior_engineer", "product_manager"}
    scenario_agents = {aid for aid, sc in AGENT_SCENARIOS.items() if sc == scenario_mode} if scenario_mode else set()
    if not debaters:
        return []

    scored: List[Dict[str, Any]] = []
    for item in debaters:
        debater_id = item.get("id", "")
        keywords = DEBATER_TOPIC_HINTS.get(debater_id, [])
        role_text = " ".join(
            [
                item.get("name", ""),
                item.get("display_name", ""),
                item.get("role", ""),
                item.get("description", ""),
            ]
        ).lower()
        score = 0
        for kw in keywords:
            kw_l = kw.lower()
            if kw_l and kw_l in topic_text:
                score += 4
            if kw_l and kw_l in role_text:
                score += 1
        if it_mode:
            if debater_id in it_agents:
                score += 8
            else:
                score -= 3
        if scenario_agents:
            if debater_id in scenario_agents:
                score += 6
            else:
                score -= 2
        # 无关键词命中时，使用角色文本与主题做基础相似兜底
        if not keywords and topic_text and any(ch in role_text for ch in topic_text[:8]):
            score += 1
        scored.append(
            {
                **item,
                "match_score": score,
                "match_reason": "关键词匹配" if score > 0 else "通用辩手兜底",
            }
        )

    scored.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    if it_mode:
        it_ranked = [x for x in scored if x.get("id") in it_agents]
        selected = [x for x in it_ranked if x.get("match_score", 0) >= 0][: max(min_count, 3)]
    elif scenario_agents:
        scenario_ranked = [x for x in scored if x.get("id") in scenario_agents]
        selected = [x for x in scenario_ranked if x.get("match_score", 0) >= 0][: max(min_count, 3)]
    else:
        selected = [x for x in scored if x.get("match_score", 0) > 0][: max(min_count, 3)]

    if len(selected) < min_count:
        selected_ids = {x.get("id") for x in selected}
        pool = scored
        if it_mode:
            pool = [x for x in scored if x.get("id") in it_agents] + [x for x in scored if x.get("id") not in it_agents]
        elif scenario_agents:
            # 场景模式下严格限制为同场景，不再引入跨场景辩手
            pool = [x for x in scored if x.get("id") in scenario_agents]
        for item in pool:
            if item.get("id") not in selected_ids:
                selected.append(item)
            if len(selected) >= min_count:
                break

    return selected[:4]


def llm_recommend_debaters(
    *,
    topic: str,
    candidates: List[Dict[str, Any]],
    preferred_scenario: str,
    min_count: int,
) -> List[Dict[str, str]]:
    if not candidates:
        return []
    candidate_lines = []
    for c in candidates:
        candidate_lines.append(
            f"- id={c.get('id')} | name={c.get('name')} | role={c.get('role')} | scenario={c.get('scenario')} | desc={c.get('description')}"
        )
    prompt = f"""你是企业决策系统中的“辩手选择器”。

任务：根据辩题与场景，从候选辩手中选择最合适的 {min_count} 位辩手。

辩题：{topic}
场景偏好：{preferred_scenario or "all"}

候选辩手：
{chr(10).join(candidate_lines)}

要求：
1) 只从候选列表中选，不允许虚构 id；
2) 优先匹配场景，其次匹配专业角色；
3) 选择数量至少 {min_count} 个；
4) 输出必须是 JSON：
{{
  "selected": [
    {{"id":"id1","reason":"为什么选他，1句话"}},
    {{"id":"id2","reason":"为什么选他，1句话"}}
  ],
  "reason": "一句话说明选择逻辑"
}}
"""
    raw = llm_chat(
        [
            {"role": "system", "content": "你是精准的角色匹配助手，输出必须是 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    selected_items: List[Dict[str, str]] = []
    try:
        data = parse_json_object(raw)
        items = data.get("selected", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    selected_items.append(
                        {
                            "id": item.get("id"),
                            "reason": (item.get("reason") or "").strip(),
                        }
                    )
    except Exception:
        # 模型偶尔不按 JSON 输出，兜底从原文抓取 id
        pass

    if not selected_items:
        id_pattern = r"[a-z][a-z0-9_]{2,40}"
        candidates_in_text = re.findall(id_pattern, raw.lower())
        selected_items = [{"id": x, "reason": ""} for x in candidates_in_text]

    valid_ids = {c.get("id") for c in candidates}
    cleaned = [x for x in selected_items if isinstance(x.get("id"), str) and x.get("id") in valid_ids]
    deduped = []
    seen = set()
    for x in cleaned:
        xid = x.get("id")
        if xid not in seen:
            deduped.append({"id": xid, "reason": x.get("reason", "")})
            seen.add(xid)
    return deduped


def get_session_or_404(session_id: str) -> Dict[str, Any]:
    if session_id in debate_sessions:
        return debate_sessions[session_id]
    file_path = session_file(session_id)
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            session = json.load(f)
        debate_sessions[session_id] = session
        return session
    raise HTTPException(status_code=404, detail="Session not found")


def llm_chat(messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def parse_json_object(raw_text: str) -> Dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start : end + 1])
    raise HTTPException(status_code=500, detail="模型返回格式解析失败，请重试。")


def load_custom_positions() -> List[Dict[str, Any]]:
    if not CUSTOM_POSITIONS_FILE.exists():
        return []
    with CUSTOM_POSITIONS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_custom_positions(items: List[Dict[str, Any]]) -> None:
    with CUSTOM_POSITIONS_FILE.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def normalize_lines(raw: str) -> List[str]:
    lines = [x.strip() for x in raw.replace("\r", "\n").split("\n")]
    lines = [x for x in lines if x]
    return lines


def upsert_custom_position(item: Dict[str, Any]) -> Dict[str, Any]:
    custom_positions = load_custom_positions()
    title = (item.get("title") or "").strip()
    company = (item.get("company") or "").strip()
    for existing in custom_positions:
        if (existing.get("title", "").strip() == title) and (existing.get("company", "").strip() == company):
            existing["responsibilities"] = item.get("responsibilities", [])
            existing["must_have"] = item.get("must_have", [])
            existing["plus"] = item.get("plus", [])
            existing["is_custom"] = True
            save_custom_positions(custom_positions)
            return existing
    created = {
        "id": f"custom_{uuid.uuid4().hex[:12]}",
        "title": title or "自定义岗位",
        "company": company or "自定义岗位",
        "responsibilities": item.get("responsibilities", []),
        "must_have": item.get("must_have", []),
        "plus": item.get("plus", []),
        "is_custom": True,
    }
    custom_positions.insert(0, created)
    save_custom_positions(custom_positions)
    return created


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = [(page.extract_text() or "") for page in reader.pages]
        content = "\n".join(text_parts).strip()
        if not content:
            raise HTTPException(status_code=400, detail="PDF 未提取到可读文本，请尝试可复制文本版本。")
        return content
    if suffix == ".docx":
        doc = Document(io.BytesIO(file_bytes))
        content = "\n".join([p.text for p in doc.paragraphs]).strip()
        if not content:
            raise HTTPException(status_code=400, detail="Word 未提取到可读文本，请检查文档内容。")
        return content
    if suffix in {".txt", ".md"}:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    if suffix == ".doc":
        raise HTTPException(status_code=400, detail="暂不支持 .doc，请转为 .docx 或 PDF 后上传。")
    raise HTTPException(status_code=400, detail="仅支持 PDF / DOCX / TXT / MD 文件。")


def generate_resume_review(
    *,
    reviewer: Dict[str, str],
    position: Dict[str, Any],
    resume_text: str,
) -> Dict[str, Any]:
    prompt = f"""你是{reviewer['name']}，正在评估候选人是否适合岗位。

公司：{position['company']}
岗位：{position['title']}
岗位必备能力：
{chr(10).join([f"- {x}" for x in position['must_have']])}
岗位加分项：
{chr(10).join([f"- {x}" for x in position['plus']])}

评审关注点：{reviewer['focus']}

候选人简历文本：
{resume_text[:9000]}

请只输出 JSON（不要额外文本）：
{{
  "score": 0-100,
  "decision": "强烈推荐/推荐/有条件推荐/不推荐",
  "summary": "80-150字结论",
  "strengths": ["亮点1","亮点2","亮点3"],
  "risks": ["风险1","风险2"],
  "missing": ["缺失能力1","缺失能力2"],
  "questions": ["面试追问1","面试追问2"],
  "advice": ["改进建议1","改进建议2"]
}}
"""
    raw = llm_chat(
        [
            {"role": "system", "content": "你是半导体行业招聘评审专家，输出必须是 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return parse_json_object(raw)


def aggregate_resume_reviews(reviews: List[Dict[str, Any]], position: Dict[str, Any]) -> Dict[str, Any]:
    score_values = [int(r.get("result", {}).get("score", 0)) for r in reviews]
    avg_score = round(sum(score_values) / max(1, len(score_values)), 1)
    recommendations = [r.get("result", {}).get("decision", "") for r in reviews]
    final_decision = "推荐"
    if avg_score >= 80:
        final_decision = "强烈推荐"
    elif avg_score < 60:
        final_decision = "不推荐"
    elif avg_score < 70:
        final_decision = "有条件推荐"

    return {
        "position": position,
        "average_score": avg_score,
        "final_decision": final_decision,
        "reviewer_decisions": recommendations,
        "updated_at": now_iso(),
    }


def format_recent_context(session: Dict[str, Any], max_items: int = 16) -> str:
    recent = session["messages"][-max_items:]
    if not recent:
        return "暂无历史发言，这是开场轮次。"
    lines = []
    for item in recent:
        lines.append(
            f"[第{item['round']}轮][{item['speaker']}][{item['type']}]: {item['content']}"
        )
    return "\n".join(lines)


def append_message(
    session: Dict[str, Any],
    *,
    speaker: str,
    content: str,
    message_type: str,
    round_number: int,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    item = {
        "speaker": speaker,
        "content": content,
        "type": message_type,
        "round": round_number,
        "timestamp": now_iso(),
        "meta": meta or {},
    }
    session["messages"].append(item)
    return item


def generate_debater_message(
    session: Dict[str, Any], agent_name: str, round_number: int
) -> str:
    config = load_agent_config(agent_name)
    other_debaters = [x for x in session["debaters"] if x != agent_name]
    participant_line = "、".join(other_debaters) if other_debaters else "无"
    prior_round_speakers = [
        x.get("speaker")
        for x in session.get("messages", [])
        if x.get("round") == round_number and x.get("type") == "debater" and x.get("speaker")
    ]
    is_first_debater_this_round = len(prior_round_speakers) == 0
    interaction_instruction = """
2. 本轮你是首位发言辩手：禁止写“回应某某上一条观点”，因为本轮尚无人先发言；
3. 你可以主动点名其他辩手并提出追问或预判分歧，但不要伪造“对方已经说过”的内容；
4. 若要回应用户，只能作为部分内容，不能超过全文 40%；
""" if is_first_debater_this_round else """
2. 本轮必须至少点名回应 1 位其他辩手（可使用“@辩手ID”或“回应某某”），禁止整段只对用户说话；
3. 若要回应用户，只能作为部分内容，不能超过全文 40%；
"""
    it_mode = is_it_decision_topic(session.get("topic", ""))
    it_mode_instruction = """
8. 当前是 IT 部门决策场景：请优先给出可执行方案，包含：负责人角色、完成时限、上线/变更风险、回滚或兜底预案。
9. 如涉及系统变更，请明确“先小范围试点再全量”的策略，以及至少 1 条可量化验收指标（例如：故障恢复时长、告警误报率、交付时长）。
""" if it_mode else ""
    prompt = f"""你将扮演以下角色参与辩论，必须严格保持人设、认知、表达风格：

角色名：{config.get("display_name", config.get("name", agent_name))}
角色身份：{config.get("identity", {}).get("role", "辩手")}
关键经历：{config.get("identity", {}).get("experience", "")}
背景：{config.get("identity", {}).get("background", "")}
思维方式：{config.get("cognitive_style", {}).get("thinking", "")}
评估标准：{config.get("cognitive_style", {}).get("evaluation_criteria", "")}
优势：{"；".join(config.get("strengths", []))}
盲点：{"；".join(config.get("blind_spots", []))}
核心信念：{"；".join(config.get("core_beliefs", []))}
辩论风格：{config.get("debate_style", "")}
说话风格：{config.get("speech_pattern", "")}

辩题：{session["topic"]}
当前轮次：第{round_number}轮
当前发言人：{agent_name}
其他辩手：{participant_line}
可互动对象：其他辩手 + 用户
最近上下文：
{format_recent_context(session)}

要求：
1. 你是独立辩手，不是用户专属助手；可以与任意辩手对话、质疑、支持或补充；
{interaction_instruction}
5. 允许出现“与某辩手同立场但理由不同”或“与其对立”的表达，体现真实立场互动；
6. 观点真实、细节具体，不说空话；保持该身份的认知偏好和语言风格；
7. 人物表达要像真实职场角色：优先给出岗位职责边界、资源约束、失败代价，不要“鸡汤式鼓励”；
8. 如果引用数据，使用“约/大约/通常范围”表达，避免编造精确且无法验证的数字；
9. 输出必须是 Markdown，使用下面结构（标题名称可微调，但必须保留分段与列表）：
## 立场
- 用 1-2 句给出本轮立场

## 交锋回应
- @某辩手：回应点 1
- @某辩手：回应点 2

## 我的补充
- 证据/案例/推演 1
- 可执行建议或风险提醒 1

10. 输出 180-320 字，直接输出 Markdown 正文，不要输出“说明”或代码块围栏。
{it_mode_instruction}
"""
    return llm_chat(
        [
            {"role": "system", "content": "你是严谨的多方辩论参与者。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )


def generate_moderator_summary(session: Dict[str, Any], round_number: int) -> str:
    moderator = load_agent_config("debate_moderator")
    prompt = f"""你是{moderator['identity']['role']}。请总结第{round_number}轮辩论。

辩题：{session["topic"]}
最近发言：
{format_recent_context(session)}

请输出：
1) 各方核心观点（按人分点）
2) 当前最关键冲突
3) 下一轮必须回答的问题（2-3条）
控制在 220 字以内。
"""
    return llm_chat(
        [
            {"role": "system", "content": "你是中立主持人，擅长抽取冲突焦点。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )


def parse_judge_json(raw_text: str) -> Dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start : end + 1])
    raise HTTPException(status_code=500, detail="裁判输出解析失败，请重试。")


def generate_judge_result(session: Dict[str, Any], round_number: int) -> Dict[str, Any]:
    judge = load_agent_config("final_judge")
    it_mode = is_it_decision_topic(session.get("topic", ""))
    it_mode_json_schema = """
  "decision_type": "go/no_go/pilot_first",
  "owner": "建议负责人角色（如：运维负责人）",
  "deadline": "建议完成时限（如：48小时内）",
  "rollback_plan": "若方案失败的回滚/兜底策略",
  "acceptance_metrics": ["指标1","指标2"],
  "next_actions": ["行动1","行动2","行动3"],
""" if it_mode else ""
    it_mode_rules = """
- 当前是 IT 部门决策场景：必须给出 owner、deadline、rollback_plan、acceptance_metrics。
- 优先给出“小范围试点”方案，再决定是否全量。
""" if it_mode else ""
    prompt = f"""你是{judge['identity']['role']}，请基于当前辩论给出阶段裁决。

辩题：{session["topic"]}
最近发言：
{format_recent_context(session)}

必须仅输出 JSON，不允许额外文本，结构如下：
{{
  "consensus": ["共识1", "共识2"],
  "disagreements": ["分歧1", "分歧2"],
  "proposed_conclusion": "当前最优结论（具体可执行）",
  "confidence": 0-100 的整数,
  "continue_debate": true/false,
  "reasoning": "裁判理由，80-160字",
{it_mode_json_schema}
}}

判定规则：
- 若关键分歧仍未闭环，continue_debate=true
- 只有在证据链完整、冲突基本收敛时，continue_debate=false
{it_mode_rules}
"""
    raw = llm_chat(
        [
            {"role": "system", "content": "你是严谨裁判，输出必须是 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    result = parse_judge_json(raw)
    result["round"] = round_number
    result["timestamp"] = now_iso()
    return result


def execute_full_round(session: Dict[str, Any]) -> Dict[str, Any]:
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="该辩题已结束")

    round_number = session["round"]
    new_messages = []

    for agent_name in session["debaters"]:
        content = generate_debater_message(session, agent_name, round_number)
        message = append_message(
            session,
            speaker=agent_name,
            content=content,
            message_type="debater",
            round_number=round_number,
        )
        new_messages.append(message)

    summary = generate_moderator_summary(session, round_number)
    summary_message = append_message(
        session,
        speaker="主持人",
        content=summary,
        message_type="moderator_summary",
        round_number=round_number,
    )
    new_messages.append(summary_message)
    session["summaries"].append(
        {"round": round_number, "content": summary, "timestamp": summary_message["timestamp"]}
    )

    judgment = generate_judge_result(session, round_number)
    judge_message = append_message(
        session,
        speaker="裁判",
        content=judgment["proposed_conclusion"],
        message_type="judge",
        round_number=round_number,
        meta=judgment,
    )
    new_messages.append(judge_message)
    session["judgments"].append(judgment)
    session["latest_judgment"] = judgment
    session["status"] = (
        "awaiting_user_judgment"
        if (not judgment.get("continue_debate", True) and int(judgment.get("confidence", 0)) >= 70)
        else "ongoing"
    )
    persist_session(session)
    return {
        "round": round_number,
        "messages": new_messages,
        "summary": summary,
        "judgment": judgment,
        "status": session["status"],
    }


@app.get("/")
def api_root():
    return {
        "name": "Multi Agent Debate API",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def api_health():
    return {"status": "ok", "time": now_iso()}


@app.get("/api/debaters")
def get_debaters():
    return {"debaters": load_debaters()}


@app.get("/api/debaters/recommend")
def recommend_debaters(topic: str = "", scenario: str = ""):
    scenario_mode = (scenario or "").strip().lower()
    strict_scenario = scenario_mode not in {"", "all"}
    rule_picks = recommend_debaters_for_topic(topic=topic, min_count=3, preferred_scenario=scenario_mode or None)
    picks = rule_picks
    selector_source = "rule_fallback"
    selector_reason = "默认规则推荐"
    llm_error = ""
    recommendation_items = [
        {"id": x.get("id"), "source": "rule_fallback", "reason": ""}
        for x in picks
    ]
    try:
        all_debaters = load_debaters()
        if strict_scenario:
            all_debaters = [x for x in all_debaters if x.get("scenario") == scenario_mode]
        llm_selected_items = llm_recommend_debaters(
            topic=topic,
            candidates=all_debaters,
            preferred_scenario=scenario_mode or "all",
            min_count=3,
        )
        if llm_selected_items:
            id_map = {x.get("id"): x for x in all_debaters}
            llm_picks = [id_map[item["id"]] for item in llm_selected_items if item.get("id") in id_map]
            if len(llm_picks) >= 2:
                picks = llm_picks[:4]
                selector_source = "llm"
                selector_reason = "LLM 根据辩题和场景完成推荐"
                llm_reason_map = {x.get("id"): x.get("reason", "") for x in llm_selected_items}
                recommendation_items = [
                    {"id": x.get("id"), "source": "llm", "reason": llm_reason_map.get(x.get("id"), "")}
                    for x in picks
                ]
            else:
                selector_source = "rule_fallback"
                selector_reason = "LLM 返回人数不足，回退规则推荐"
                recommendation_items = [
                    {"id": x.get("id"), "source": "rule_fallback", "reason": ""}
                    for x in picks
                ]
        else:
            selector_source = "rule_fallback"
            selector_reason = "LLM 未返回有效 ID，回退规则推荐"
            recommendation_items = [
                {"id": x.get("id"), "source": "rule_fallback", "reason": ""}
                for x in picks
            ]
    except Exception as e:
        # LLM 失败时自动回退到规则推荐，确保可用性
        picks = rule_picks
        selector_source = "rule_fallback"
        llm_error = str(e)
        selector_reason = "LLM 调用失败，使用规则推荐"
        recommendation_items = [
            {"id": x.get("id"), "source": "rule_fallback", "reason": ""}
            for x in picks
        ]
    return {
        "topic": topic,
        "scenario": scenario or "all",
        "recommended": picks,
        "debater_ids": [x.get("id") for x in picks],
        "recommendation_items": recommendation_items,
        "selector_source": selector_source,
        "selector_reason": selector_reason,
        "llm_error": llm_error,
    }


@app.get("/api/recruit/positions")
def list_recruit_positions():
    custom_items = load_custom_positions()
    merged = list(POSITION_PROFILES.values()) + custom_items
    return {"positions": merged}


@app.post("/api/recruit/positions")
def create_custom_position(payload: CustomPositionRequest):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="岗位名称不能为空。")
    must_have = [x.strip() for x in payload.must_have if x.strip()]
    responsibilities = [x.strip() for x in payload.responsibilities if x.strip()]
    plus = [x.strip() for x in payload.plus if x.strip()]
    if not must_have:
        raise HTTPException(status_code=400, detail="至少填写 1 条核心要求。")

    item = upsert_custom_position(
        {
        "title": title,
        "company": payload.company.strip() or "自定义岗位",
        "responsibilities": responsibilities,
        "must_have": must_have,
        "plus": plus,
        }
    )
    return item


@app.post("/api/recruit/parse")
async def parse_resume_only(resume_file: UploadFile = File(...)):
    file_bytes = await resume_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空。")
    raw_filename = resume_file.filename or f"resume_{uuid.uuid4().hex}.bin"
    resume_text = extract_resume_text(raw_filename, file_bytes)
    lines = [x.strip() for x in resume_text.splitlines() if x.strip()]
    return {
        "file_name": raw_filename,
        "char_count": len(resume_text),
        "line_count": len(lines),
        "parsed_text": resume_text,
    }


@app.post("/api/recruit/evaluate")
async def evaluate_resume(
    position_id: str = Form(""),
    custom_position_title: str = Form(""),
    custom_position_company: str = Form(""),
    custom_position_responsibilities: str = Form(""),
    custom_position_must_have: str = Form(""),
    custom_position_plus: str = Form(""),
    custom_position_save: str = Form("1"),
    resume_file: UploadFile = File(...),
):
    custom_positions = {x.get("id"): x for x in load_custom_positions() if x.get("id")}
    selected_position = None
    selected_position_id = ""
    use_custom_input = bool(custom_position_title.strip() or custom_position_must_have.strip())
    if use_custom_input:
        must_have = normalize_lines(custom_position_must_have)
        if not must_have:
            raise HTTPException(status_code=400, detail="自定义岗位至少填写 1 条核心要求。")
        custom_payload = {
            "title": custom_position_title.strip() or "自定义岗位",
            "company": custom_position_company.strip() or "自定义岗位",
            "responsibilities": normalize_lines(custom_position_responsibilities),
            "must_have": must_have,
            "plus": normalize_lines(custom_position_plus),
        }
        should_save = custom_position_save.strip().lower() not in {"0", "false", "no"}
        if should_save:
            selected_position = upsert_custom_position(custom_payload)
            selected_position_id = selected_position["id"]
        else:
            selected_position_id = f"custom_runtime_{uuid.uuid4().hex[:8]}"
            selected_position = {
                "id": selected_position_id,
                **custom_payload,
                "is_custom_runtime": True,
            }
    else:
        if not position_id:
            raise HTTPException(status_code=400, detail="请选择岗位或填写自定义岗位信息。")
        if position_id in POSITION_PROFILES:
            selected_position = POSITION_PROFILES[position_id]
        elif position_id in custom_positions:
            selected_position = custom_positions[position_id]
        else:
            raise HTTPException(status_code=400, detail="无效的岗位 ID。")
        selected_position_id = position_id

    file_bytes = await resume_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空。")

    raw_filename = resume_file.filename or f"resume_{uuid.uuid4().hex}.bin"
    saved_filename = f"{uuid.uuid4().hex}_{Path(raw_filename).name}"
    saved_path = RESUME_DIR / saved_filename
    saved_path.write_bytes(file_bytes)

    resume_text = extract_resume_text(raw_filename, file_bytes)
    resume_lines = [x.strip() for x in resume_text.splitlines() if x.strip()]
    position = selected_position

    review_items = []
    for reviewer in RESUME_REVIEWERS:
        result = generate_resume_review(
            reviewer=reviewer,
            position=position,
            resume_text=resume_text,
        )
        review_items.append(
            {
                "reviewer": reviewer,
                "result": result,
                "timestamp": now_iso(),
            }
        )

    summary = aggregate_resume_reviews(review_items, position)
    eval_id = str(uuid.uuid4())
    payload = {
        "evaluation_id": eval_id,
        "created_at": now_iso(),
        "resume_file": {
            "original_name": raw_filename,
            "saved_path": str(saved_path),
        },
        "position_id": selected_position_id,
        "position": position,
        "parsed_text": resume_text,
        "char_count": len(resume_text),
        "line_count": len(resume_lines),
        "reviews": review_items,
        "summary": summary,
    }
    with (RESUME_EVAL_DIR / f"{eval_id}.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload


@app.get("/api/recruit/evaluations")
def list_resume_evaluations():
    items = []
    for fp in sorted(RESUME_EVAL_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        with fp.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items.append(
            {
                "evaluation_id": data.get("evaluation_id"),
                "created_at": data.get("created_at"),
                "position": data.get("position"),
                "resume_file": data.get("resume_file", {}).get("original_name"),
                "char_count": data.get("char_count", 0),
                "line_count": data.get("line_count", 0),
                "has_parsed_text": bool(data.get("parsed_text")),
                "summary": data.get("summary", {}),
            }
        )
    return {"evaluations": items}


@app.get("/api/recruit/evaluations/{evaluation_id}")
def get_resume_evaluation(evaluation_id: str):
    fp = RESUME_EVAL_DIR / f"{evaluation_id}.json"
    if not fp.exists():
        raise HTTPException(status_code=404, detail="未找到该评审记录。")
    with fp.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/debate/start")
def start_debate(request: DebateStartRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="辩题不能为空")
    selected_debaters = request.debaters or []
    if len(selected_debaters) < 2:
        auto_picks = recommend_debaters_for_topic(request.topic.strip(), min_count=3)
        selected_debaters = [x.get("id") for x in auto_picks if x.get("id")]
    if len(selected_debaters) < 2:
        raise HTTPException(status_code=400, detail="未能匹配足够辩手，请更换辩题或手动选择。")

    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "topic": request.topic.strip(),
        "debaters": selected_debaters,
        "round": 1,
        "status": "ongoing",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "messages": [],
        "summaries": [],
        "judgments": [],
        "latest_judgment": None,
        "final_conclusion": None,
        "user_decisions": [],
        "execution_status": "pending",
        "execution_note": "",
    }
    debate_sessions[session_id] = session
    persist_session(session)
    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "status": session["status"],
    }


@app.post("/api/debate/round")
def run_round(request: DebateRoundRequest):
    session = get_session_or_404(request.session_id)
    return execute_full_round(session)


@app.post("/api/debate/next-round")
def next_round(request: NextRoundRequest):
    session = get_session_or_404(request.session_id)
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="该辩题已结束")
    session["round"] += 1
    persist_session(session)
    return {"round": session["round"], "status": session["status"]}


@app.post("/api/debate/moderate")
def moderate(request: ModerateRequest):
    session = get_session_or_404(request.session_id)
    if not session["summaries"]:
        summary = generate_moderator_summary(session, session["round"])
        return {"summary": summary}
    return {"summary": session["summaries"][-1]["content"]}


@app.post("/api/debate/judge")
def judge(request: JudgeRequest):
    session = get_session_or_404(request.session_id)
    if not session["judgments"]:
        result = generate_judge_result(session, session["round"])
        return {"judgment": result["proposed_conclusion"], "detail": result}
    latest = session["judgments"][-1]
    return {"judgment": latest["proposed_conclusion"], "detail": latest}


@app.post("/api/debate/user-message")
def user_message(request: UserMessageRequest):
    session = get_session_or_404(request.session_id)
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="该辩题已结束")

    append_message(
        session,
        speaker="用户",
        content=request.message,
        message_type="user_message",
        round_number=session["round"],
    )
    responses = []
    for agent_name in session["debaters"]:
        content = generate_debater_message(session, agent_name, session["round"])
        item = append_message(
            session,
            speaker=agent_name,
            content=content,
            message_type="debater_response",
            round_number=session["round"],
        )
        responses.append(item)
    persist_session(session)
    return {"responses": responses, "round": session["round"], "status": session["status"]}


@app.post("/api/debate/decision")
def debate_decision(request: DecisionRequest):
    session = get_session_or_404(request.session_id)
    decision = request.decision.strip().lower()
    if decision not in {"accept", "reject"}:
        raise HTTPException(status_code=400, detail="decision 只能是 accept 或 reject")

    decision_record = {
        "decision": decision,
        "user_conclusion": request.user_conclusion or "",
        "timestamp": now_iso(),
        "round": session["round"],
    }
    session["user_decisions"].append(decision_record)

    if decision == "accept":
        session["status"] = "completed"
        session["final_conclusion"] = (
            request.user_conclusion
            or (session.get("latest_judgment") or {}).get("proposed_conclusion")
            or "用户接受当前结论。"
        )
        append_message(
            session,
            speaker="用户裁决",
            content=f"我接受当前结论。最终结论：{session['final_conclusion']}",
            message_type="user_decision_accept",
            round_number=session["round"],
        )
    else:
        session["status"] = "ongoing"
        user_note = request.user_conclusion or "我否认当前结论，请继续辩论并补充证据。"
        append_message(
            session,
            speaker="用户裁决",
            content=user_note,
            message_type="user_decision_reject",
            round_number=session["round"],
        )
        session["round"] += 1

    persist_session(session)
    return {
        "status": session["status"],
        "round": session["round"],
        "final_conclusion": session["final_conclusion"],
    }


@app.post("/api/debate/execution-status")
def update_execution_status(request: ExecutionStatusRequest):
    session = get_session_or_404(request.session_id)
    normalized = request.status.strip().lower()
    allowed = {"pending", "in_progress", "completed", "blocked"}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="status 只能是 pending/in_progress/completed/blocked")
    session["execution_status"] = normalized
    session["execution_note"] = (request.note or "").strip()
    persist_session(session)
    return {
        "session_id": session["session_id"],
        "execution_status": session["execution_status"],
        "execution_note": session["execution_note"],
        "updated_at": session["updated_at"],
    }


@app.post("/api/debate/auto-debate")
def auto_debate(request: AutoDebateRequest):
    session = get_session_or_404(request.session_id)
    rounds_run = 0
    collected = []
    max_rounds = max(1, min(request.max_rounds, 10))
    while rounds_run < max_rounds and session["status"] == "ongoing":
        result = execute_full_round(session)
        collected.append(result)
        rounds_run += 1
        if session["status"] == "ongoing":
            session["round"] += 1
            persist_session(session)
    return {
        "executed_rounds": rounds_run,
        "status": session["status"],
        "results": collected,
        "latest_judgment": session.get("latest_judgment"),
    }


@app.get("/api/debate/history/{session_id}")
def get_history(session_id: str):
    return get_session_or_404(session_id)


@app.get("/api/debate/sessions")
def list_sessions():
    items = []
    for file_path in sorted(RESULTS_DIR.glob("session_*.json"), key=os.path.getmtime, reverse=True):
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items.append(
            {
                "session_id": data.get("session_id"),
                "topic": data.get("topic"),
                "status": data.get("status"),
                "round": data.get("round"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "debaters": data.get("debaters", []),
                "final_conclusion": data.get("final_conclusion"),
                "execution_status": data.get("execution_status", "pending"),
                "execution_note": data.get("execution_note", ""),
            }
        )
    return {"sessions": items}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

from datetime import datetime
import io
import json
import os
from pathlib import Path
import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from docx import Document
from pypdf import PdfReader

load_dotenv()

BASE_DIR = Path(__file__).parent
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
    debaters: list[str]


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
            }
        )
    return results


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
最近上下文：
{format_recent_context(session)}

要求：
1. 观点真实、细节具体，不说空话；
2. 对他人观点进行点对点回应；
3. 保持该身份的认知偏好和语言风格；
4. 输出 180-320 字，直接输出发言正文。
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
  "reasoning": "裁判理由，80-160字"
}}

判定规则：
- 若关键分歧仍未闭环，continue_debate=true
- 只有在证据链完整、冲突基本收敛时，continue_debate=false
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


@app.get("/api/debaters")
def get_debaters():
    return {"debaters": load_debaters()}


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
    preview = "\n".join(lines[:60])
    return {
        "file_name": raw_filename,
        "char_count": len(resume_text),
        "line_count": len(lines),
        "preview_text": preview,
        "full_text": resume_text,
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
    if len(request.debaters) < 2:
        raise HTTPException(status_code=400, detail="至少选择 2 位辩手")

    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "topic": request.topic.strip(),
        "debaters": request.debaters,
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
            }
        )
    return {"sessions": items}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
FastAPI后端 - 为前端提供API服务
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from pathlib import Path
from datetime import datetime
from main import DebateSession, get_client, load_agent_config, list_debater_agents, call_debater, call_moderator, call_judge

app = FastAPI(title="辩论竞技场 API", version="1.0.0")

# 启用CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储活跃的辩论会话
active_sessions = {}


class DebateRequest(BaseModel):
    topic: str
    debaters: List[str]


class UserMessageRequest(BaseModel):
    session_id: str
    message: str


class DebateResponse(BaseModel):
    session_id: str
    message: dict


@app.get("/api/debaters")
async def get_debaters():
    """获取所有可用的辩手列表"""
    debaters = list_debater_agents()
    result = []
    for debater_id in debaters:
        try:
            config = load_agent_config(debater_id)
            result.append({
                "id": debater_id,
                "name": debater_id,
                "role": config["identity"]["role"],
                "description": config.get("description", ""),
                "avatar": get_avatar_for_debater(debater_id),
                "color": get_color_for_debater(debater_id),
            })
        except Exception as e:
            print(f"Error loading {debater_id}: {e}")
    return result


def get_avatar_for_debater(debater_id: str) -> str:
    """为辩手分配emoji头像"""
    avatars = {
        "subencai": "🎓",
        "zhangxuefeng": "🎤",
        "counselor": "🤝",
        "hr_evaluator": "💼",
        "investor": "💰",
        "product_manager": "📱",
        "senior_engineer": "💻",
    }
    return avatars.get(debater_id, "🤖")


def get_color_for_debater(debater_id: str) -> str:
    """为辩手分配颜色"""
    colors = {
        "subencai": "from-blue-500 to-cyan-400",
        "zhangxuefeng": "from-red-500 to-orange-400",
        "counselor": "from-green-500 to-emerald-400",
        "hr_evaluator": "from-purple-500 to-violet-400",
        "investor": "from-yellow-500 to-amber-400",
        "product_manager": "from-pink-500 to-rose-400",
        "senior_engineer": "from-indigo-500 to-blue-400",
    }
    return colors.get(debater_id, "from-gray-500 to-gray-400")


@app.post("/api/debate/start")
async def start_debate(request: DebateRequest):
    """开始一场新的辩论"""
    import uuid
    session_id = str(uuid.uuid4())
    
    session = DebateSession(request.topic, request.debaters)
    active_sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "topic": request.topic,
        "debaters": request.debaters,
        "round": 1,
    }


class SessionRequest(BaseModel):
    session_id: str


@app.post("/api/debate/round")
async def run_debate_round(request: SessionRequest):
    """运行一轮辩论"""
    session_id = request.session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    client = get_client()
    
    messages = []
    
    # 检查是否需要生成摘要
    if session.should_generate_summary():
        summary = session.generate_summary(client)
        messages.append({
            "type": "summary",
            "content": summary,
            "round": session.round_num,
        })
    
    # 辩手发言
    for debater_id in session.debaters:
        config = load_agent_config(debater_id)
        context = session.get_context_for_debater(debater_id)
        
        result = call_debater(client, debater_id, session.topic, context, session.round_num)
        
        message = {
            "id": len(session.conversation_history),
            "speaker": debater_id,
            "speaker_name": config["identity"]["role"],
            "text": result,
            "type": "debater",
            "round": session.round_num,
            "timestamp": datetime.now().isoformat(),
        }
        
        session.add_message(config["identity"]["role"], result, "debater")
        messages.append(message)
    
    return {
        "session_id": session_id,
        "messages": messages,
        "round": session.round_num,
    }


@app.post("/api/debate/moderate")
async def moderate_debate(request: SessionRequest):
    """主持人总结"""
    session_id = request.session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    client = get_client()
    
    moderator_result = call_moderator(client, session)
    
    return {
        "session_id": session_id,
        "message": {
            "speaker": "moderator",
            "speaker_name": "主持人",
            "text": moderator_result,
            "type": "moderator",
            "round": session.round_num,
        }
    }


@app.post("/api/debate/judge")
async def judge_debate(request: SessionRequest):
    """裁判裁决"""
    session_id = request.session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    client = get_client()
    
    judge_result = call_judge(client, session)
    
    # 保存结果
    result_file = save_session_result(session, judge_result)
    
    return {
        "session_id": session_id,
        "message": {
            "speaker": "judge",
            "speaker_name": "裁判",
            "text": judge_result,
            "type": "judge",
            "round": session.round_num,
        },
        "result_file": str(result_file),
    }


@app.post("/api/debate/user-message")
async def user_message(request: UserMessageRequest):
    """用户发言"""
    session_id = request.session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session.add_message("用户", request.message, "user")
    
    # 辩手回应
    client = get_client()
    messages = []
    
    for debater_id in session.debaters:
        config = load_agent_config(debater_id)
        context = session.get_context_for_debater(debater_id)
        
        result = call_debater(client, debater_id, session.topic, context, session.round_num)
        
        message = {
            "id": len(session.conversation_history),
            "speaker": debater_id,
            "speaker_name": config["identity"]["role"],
            "text": result,
            "type": "debater",
            "round": session.round_num,
        }
        
        session.add_message(config["identity"]["role"], result, "debater")
        messages.append(message)
    
    return {
        "session_id": session_id,
        "messages": messages,
    }


@app.post("/api/debate/next-round")
async def next_round(request: SessionRequest):
    """进入下一轮"""
    session_id = request.session_id
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session.next_round()
    
    return {
        "session_id": session_id,
        "round": session.round_num,
    }


@app.get("/api/debate/history/{session_id}")
async def get_history(session_id: str):
    """获取辩论历史"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "topic": session.topic,
        "round": session.round_num,
        "debaters": session.debaters,
        "conversation_history": session.conversation_history,
        "summaries": session.summaries,
    }


from datetime import datetime

def save_session_result(session: DebateSession, judge_result: str):
    """保存辩论结果"""
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"api_debate_result_{timestamp}.json"
    
    result = {
        "topic": session.topic,
        "timestamp": datetime.now().isoformat(),
        "round": session.round_num,
        "debaters": session.debaters,
        "conversation_history": session.conversation_history,
        "summaries": session.summaries,
        "judge": judge_result,
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result_file


# WebSocket支持实时通信
@app.websocket("/ws/debate/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "user_message":
                # 处理用户消息并广播回应
                pass
            elif action == "next_round":
                # 进入下一轮
                pass
            
            await websocket.send_json({"status": "ok"})
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

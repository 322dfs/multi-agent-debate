# Multi-Agent Debate v2

基于 DeepSeek API 的多智能体辩论系统（最新版本），支持：

- 可选辩手多轮自动辩论（带人设与风格）
- 主持总结 + 裁判阶段结论
- 用户接受/否决结论并继续辩论
- 前端历史记录点击回看与内容预览
- 本机私有历史自动保存（不同用户互不共享）

## Quick Start

### Backend

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8001
```

### Frontend

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

## Environment

复制 `.env.example` 为 `.env` 并填写：

- `DEEPSEEK_API_KEY`
- `LLM_BASE_URL` (可选)
- `DEBATE_MODEL` (可选)

## Local History Storage

默认保存到用户目录：

- `~/.multi-agent-debate-v2/results`

可通过 `DEBATE_APP_DATA_DIR` 覆盖。


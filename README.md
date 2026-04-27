# Multi-Agent Debate v2

基于 DeepSeek API 的多智能体辩论与简历评审系统。

## 功能总览

- 多辩手自动辩论（人设驱动、逐轮发言）
- 主持总结 + 裁判阶段结论
- 用户可接受/否决结论并继续辩论
- 历史记录自动保存（每台机器独立）
- 历史记录可点击回看与内容预览
- 简历评审模式（PDF / DOCX / TXT / MD 上传）
  - 根据岗位画像触发多评审 Agent 打分
  - 按顺序展示评审意见
  - 评审历史可回看

## 技术栈

- Backend: FastAPI
- Frontend: React + Vite + Tailwind
- LLM: DeepSeek (OpenAI Compatible API)

## 目录结构

```text
multi-agent-debate-v2/
├─ agents/                    # 辩手画像配置
├─ api.py                     # 后端主服务
├─ requirements.txt
├─ frontend/
│  ├─ src/components/
│  │  ├─ DebateArena.jsx
│  │  ├─ DebaterSelection.jsx
│  │  ├─ ResumeEvaluation.jsx
│  │  └─ ...
│  └─ package.json
└─ .gitignore
```

## 环境变量

复制 `.env.example` 为 `.env`（或直接设置系统环境变量）：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
DEBATE_MODEL=deepseek-chat
# 可选：覆盖本机数据目录
# DEBATE_APP_DATA_DIR=D:\debate-data
```

## 本地启动

### 1) 后端

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8001
```

### 2) 前端

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

## 数据持久化策略

- 辩论会话与简历评审默认保存到用户目录：
  - `~/.multi-agent-debate-v2/results`
  - `~/.multi-agent-debate-v2/resume_evaluations`
- 这意味着每个开发者只会看到自己本机的数据，不会自动拿到他人的历史记录。

## 简历评审接口

- `GET /api/recruit/positions` 获取岗位画像
- `POST /api/recruit/evaluate` 上传简历并评审
  - form-data:
    - `position_id`
    - `resume_file`
- `GET /api/recruit/evaluations` 评审历史列表
- `GET /api/recruit/evaluations/{evaluation_id}` 评审详情

## 说明

- `.doc` 在本地 MVP 中默认不支持，建议转为 `.docx` 或 `.pdf`。
- 推荐优先使用可复制文本 PDF，扫描件 OCR 质量会影响评审效果。


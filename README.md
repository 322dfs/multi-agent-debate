# Multi-Agent Debate v2

基于 DeepSeek API 的多智能体辩论与简历评审系统。  
这个仓库已经是你在本地维护的 `multi-agent-debate-v2` 对应主仓库。

## 你能用它做什么

- 多智能体自动辩论（主持人/裁判/用户可参与裁决）
- 辩论历史自动保存并可回看
- 简历上传评审（支持 PDF / DOCX / TXT / MD）
- 简历“仅解析文本”模式（先看解析结果再决定评审）
- 岗位模板（预置 + 自定义 + 自动保存）

---

## 0. 环境要求

- Python 3.10+
- Node.js 18+
- npm 9+
- 可用的 DeepSeek API Key

---

## 1. 从零启动（最清晰版本）

### 1.1 获取 API Key（DeepSeek）

1. 打开 [DeepSeek Platform](https://platform.deepseek.com/)
2. 登录后进入 API Key 管理页
3. 创建 Key 并复制保存

> Key 只显示一次，丢失后请重新生成。  
> 不要把真实 Key 提交到 GitHub。

### 1.2 配置 `.env`

在项目根目录创建 `.env` 文件（可由 `.env.example` 复制）：

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_real_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
DEBATE_MODEL=deepseek-chat
# 可选：自定义本机数据目录
# DEBATE_APP_DATA_DIR=D:\debate-data
```

### 1.3 启动后端

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8011
```

看到 `Uvicorn running on http://127.0.0.1:8011` 说明后端成功。

### 1.4 启动前端（新开一个终端）

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

浏览器打开：`http://127.0.0.1:3000`

---

## 2. 3 分钟自测（确认系统正常）

1. 首页点击“开始新辩论”
2. 输入辩题，选择辩手，点击“开始辩论”
3. 能看到逐条发言、裁判阶段结论、下一轮按钮
4. 回到首页进入“简历多Agent评审”
5. 拖入一份简历，先点“仅解析简历（先看内容）”
6. 再选择岗位点“开始评审”

如果这 6 步都通，说明你的环境配置正确。

---

## 3. Docker 部署（可选）

### 3.1 先准备 `.env`

根目录必须有 `.env`，至少填入：

```env
DEEPSEEK_API_KEY=your_real_key_here
```

### 3.2 启动

```bash
docker compose up --build
```

访问：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`

### 3.3 停止

```bash
docker compose down
```

---

## 4. 核心功能说明

### 辩论模式

- 发起辩题 -> 多智能体轮流发言
- 主持人总结、裁判判断是否继续辩论
- 用户可接受结论或否决并继续
- 历史记录可直接点开查看内容

### 简历评审模式

- 文件上传方式：点击选择 + 拖拽上传
- 支持“仅解析文本”
- 支持岗位模板管理（预置岗位 + 自定义岗位）
- 自定义岗位可自动保存，后续直接复用

---

## 5. API 速查

### 辩论相关

- `GET /api/debaters`
- `POST /api/debate/start`
- `POST /api/debate/round`
- `POST /api/debate/decision`
- `GET /api/debate/sessions`
- `GET /api/debate/history/{session_id}`

### 招聘评审相关

- `GET /api/recruit/positions`
- `POST /api/recruit/positions`
- `POST /api/recruit/parse`
- `POST /api/recruit/evaluate`
- `GET /api/recruit/evaluations`
- `GET /api/recruit/evaluations/{evaluation_id}`

---

## 6. 数据存储与隐私

默认存储目录（每台机器独立）：

- `~/.multi-agent-debate-v2/results`
- `~/.multi-agent-debate-v2/resume_evaluations`
- `~/.multi-agent-debate-v2/custom_positions.json`

结论：

- 你只能看到你自己机器的数据
- 克隆仓库不会带走他人的历史记录

---

## 7. 常见问题（必看）

### Q1：页面没变化，像旧版本

- 浏览器强刷 `Ctrl + F5`
- 确认前端地址是 `127.0.0.1:3000`
- 确认后端地址是 `127.0.0.1:8011`（本地开发）

### Q2：提示缺少 API Key

- 检查根目录是否有 `.env`
- 检查 `DEEPSEEK_API_KEY` 是否有值
- 改完 `.env` 后重启后端

### Q3：`.doc` 文件失败

- `.doc` 不支持，请转成 `.docx` 或 `.pdf`

### Q4：端口被占用

- 改用新端口重启，或关闭旧进程后重启

---

## 8. 安全规范

- 禁止硬编码真实 API Key
- 禁止把 `.env` 提交到 GitHub
- 使用 `.env.example` 作为配置模板分发


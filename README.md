# Multi-Agent Debate v2（小白友好版）

这是一个「能直接跑」的多智能体系统，核心有两块：

- **智能辩论**：多角色自动发言 + 主持 + 裁判 + 用户裁决
- **简历评审**：上传简历 -> 解析 -> 多 Agent 评估 -> 结论

如果你是第一次接触这类项目，按下面步骤来，基本不会踩坑。

---

## 0. 先看效果（你会得到什么）

- 可运行的辩论系统（支持历史记录）
- 可运行的简历评审系统（支持拖拽上传、仅解析）
- 可保存岗位模板（写一次，后续直接选）
- 本机独立数据（不会和别人混）

---

## 1. 运行前准备（3 项）

### 1.1 安装环境

- Python 3.10+
- Node.js 18+
- npm 9+

### 1.2 准备 DeepSeek API Key

1. 打开 [DeepSeek Platform](https://platform.deepseek.com/)
2. 登录后进入 API Key 页面
3. 创建并复制 Key

> 重要：不要把真实 Key 写到代码里，也不要上传到 GitHub。

### 1.3 创建 `.env`

在项目根目录执行：

**Windows PowerShell**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

编辑 `.env`（最少填第一行）：

```env
DEEPSEEK_API_KEY=your_real_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
DEBATE_MODEL=deepseek-chat
# 可选：自定义本机数据目录
# DEBATE_APP_DATA_DIR=D:\debate-data
```

---

## 2. 本地启动（推荐）

### 2.1 启动后端

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8011
```

看到这行说明后端成功：

```text
Uvicorn running on http://127.0.0.1:8011
```

### 2.2 启动前端（另开一个终端）

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

浏览器打开：

```text
http://127.0.0.1:3000
```

---

## 3. 2 分钟自测（判断是否跑通）

### A. 辩论功能

1. 点击“开始新辩论”
2. 输入辩题 + 选辩手
3. 点击“开始辩论”
4. 观察是否有逐条发言 + 裁判结论

### B. 简历评审功能

1. 点击“简历多Agent评审”
2. 拖入一个 PDF/DOCX
3. 先点“仅解析简历（先看内容）”
4. 再点“开始评审”

这两部分都通，就说明你的配置正确。

---

## 4. Docker 启动（可选）

### 4.1 准备 `.env`

根目录必须有 `.env`，至少包含：

```env
DEEPSEEK_API_KEY=your_real_key_here
```

### 4.2 启动

```bash
docker compose up --build
```

访问地址：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`

### 4.3 停止

```bash
docker compose down
```

---

## 5. 功能说明

### 5.1 辩论模式

- 多辩手自动发言
- 主持人总结 + 裁判阶段结论
- 用户可“接受结论并结束”或“否决并继续”
- 历史记录可点击回看
- 支持主题切换（简约商务 / 年轻活力）

### 5.2 简历评审模式

- 支持上传：`.pdf` / `.docx` / `.txt` / `.md`
- 支持拖拽上传
- 支持仅解析文本
- 支持自定义岗位模板并保存
- 支持评审历史回看

---

## 6. API 快速索引

### 辩论

- `GET /api/debaters`
- `POST /api/debate/start`
- `POST /api/debate/round`
- `POST /api/debate/decision`
- `GET /api/debate/sessions`
- `GET /api/debate/history/{session_id}`

### 招聘评审

- `GET /api/recruit/positions`
- `POST /api/recruit/positions`
- `POST /api/recruit/parse`
- `POST /api/recruit/evaluate`
- `GET /api/recruit/evaluations`
- `GET /api/recruit/evaluations/{evaluation_id}`

---

## 7. 数据存储与隐私

默认存储路径（每台机器独立）：

- `~/.multi-agent-debate-v2/results`
- `~/.multi-agent-debate-v2/resume_evaluations`
- `~/.multi-agent-debate-v2/custom_positions.json`

也就是说：每个人只看到自己本机数据，不会自动拿到别人的历史。

---

## 8. 常见问题（高频）

### Q1：页面没变化，像旧版本

- 浏览器强刷：`Ctrl + F5`
- 确认前端是 `127.0.0.1:3000`
- 确认后端是 `127.0.0.1:8011`

### Q2：提示缺少 API Key

- 检查 `.env` 是否存在
- 检查 `DEEPSEEK_API_KEY` 是否有值
- 改完 `.env` 记得重启后端

### Q3：`.doc` 文件解析失败

- 目前不支持 `.doc`，请转为 `.docx` 或 `.pdf`

### Q4：端口被占用

- 先关闭旧进程，或换端口启动

---

## 9. 安全规范（务必遵守）

- 不要硬编码真实 API Key
- 不要提交 `.env` 到仓库
- 用 `.env.example` 做模板


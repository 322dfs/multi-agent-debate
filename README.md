# Multi-Agent Debate v2

基于 DeepSeek 的多智能体辩论与简历评审系统，支持：

- 多辩手自动辩论（真实 LLM 调用）
- 主持人总结、裁判结论、用户接受/否决
- 本机独立历史记录（不会共享给其他克隆用户）
- 简历上传评审（PDF / DOCX / TXT / MD）
- 自定义岗位模板（保存后可长期复用）

---

## 1) 新手快速开始（5 分钟）

### 第一步：获取 DeepSeek API Key

1. 打开 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册/登录账号
3. 在 API Key 页面创建新密钥
4. 复制密钥（只会完整显示一次）

> 安全提醒：不要把 API Key 写进代码，也不要提交到 GitHub。

### 第二步：配置环境变量

在项目根目录复制一份配置文件：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_real_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
DEBATE_MODEL=deepseek-chat
# 可选：自定义本机数据存储目录
# DEBATE_APP_DATA_DIR=D:\debate-data
```

### 第三步：启动后端

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8011
```

### 第四步：启动前端

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

浏览器打开：`http://127.0.0.1:3000`

---

## 2) Docker 部署（推荐给新手）

### 2.1 准备 `.env`

仍然先创建并填写根目录 `.env`（至少要有 `DEEPSEEK_API_KEY`）。

### 2.2 启动

```bash
docker compose up --build
```

访问：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`

### 2.3 停止

```bash
docker compose down
```

---

## 3) 功能说明

### 3.1 辩论模式

- 选择辩题与辩手后开始辩论
- 支持多轮自动发言
- 裁判会给出阶段结论
- 用户可“接受结论并结束”或“否决并继续辩论”

### 3.2 简历评审模式

- 支持拖拽/选择简历文件
- 支持“仅解析简历（先看文本）”
- 支持按岗位触发多 Agent 评审
- 自定义岗位可保存为模板，下次直接选

---

## 4) API 一览（核心）

- `GET /api/debaters`：辩手列表
- `POST /api/debate/start`：创建辩论
- `POST /api/debate/round`：执行一轮
- `POST /api/debate/decision`：用户接受/否决结论
- `GET /api/debate/sessions`：历史会话列表
- `GET /api/debate/history/{session_id}`：会话详情

- `GET /api/recruit/positions`：岗位列表（预设 + 自定义）
- `POST /api/recruit/positions`：新增自定义岗位模板
- `POST /api/recruit/parse`：仅解析简历文本
- `POST /api/recruit/evaluate`：简历评审
- `GET /api/recruit/evaluations`：评审历史
- `GET /api/recruit/evaluations/{evaluation_id}`：评审详情

---

## 5) 数据与隐私

默认数据保存到当前用户目录（本机私有）：

- `~/.multi-agent-debate-v2/results`
- `~/.multi-agent-debate-v2/resume_evaluations`
- `~/.multi-agent-debate-v2/custom_positions.json`

这意味着：

- 每个人只看到自己机器的数据
- 克隆仓库不会带走他人历史记录

---

## 6) 常见问题

### Q1：页面没变化 / 功能像旧版本？

- 强刷浏览器：`Ctrl + F5`
- 确认前端连接的是正确后端端口（本项目默认本地开发 `8011`）
- 若端口冲突，先关闭旧进程再重启

### Q2：报 “缺少 API Key”？

- 检查 `.env` 是否存在
- 检查 `DEEPSEEK_API_KEY` 是否填写
- 重启后端使新环境变量生效

### Q3：`.doc` 无法解析？

- `.doc` 默认不支持，请先转成 `.docx` 或 `.pdf`
- 优先使用可复制文本 PDF（扫描件质量会影响效果）

---

## 7) 安全规范（务必遵守）

- 不要把真实 `DEEPSEEK_API_KEY` 写入代码
- 不要提交 `.env` 到 GitHub
- 建议使用 `.env.example` 作为模板分发给团队


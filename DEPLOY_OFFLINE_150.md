# 离线服务器部署手册（新手版）

本文档用于在公司内网离线服务器部署 `multi-agent-debate`。  
适用目标机：`192.168.108.150`（已配置 SSH 免密）。

---

## 1. 先理解部署思路

这台服务器不能稳定访问外网镜像源，所以**不要**直接在服务器执行：

```bash
docker compose up --build
```

正确流程是：

1. 在本地（有 Docker Desktop、可联网）构建镜像
2. 导出镜像为 tar
3. 把 tar 传到服务器
4. 服务器 `docker load` 导入镜像
5. 用离线 compose 文件启动容器

---

## 2. 前置条件（本地）

- Windows + Docker Desktop 可用
- 本地已拉取项目代码
- 可以 SSH 到服务器（免密）
- 服务器已有 Ollama，并可访问 `127.0.0.1:11434`

---

## 3. 本地构建镜像

在项目根目录执行：

```bash
docker build -t multi-agent-debate_backend:offline .
docker build -t multi-agent-debate_frontend:offline ./frontend
```

导出镜像：

```bash
docker save -o multi-agent-debate-offline-images.tar multi-agent-debate_backend:offline multi-agent-debate_frontend:offline
```

---

## 4. 传输到服务器

如果服务器支持 `scp`，可直接传：

```bash
scp multi-agent-debate-offline-images.tar beeplux-ai-2080ti@192.168.108.150:~/apps/multi-agent-debate/
```

如果 `scp` 不可用，可用 SSH 流式传输：

```bash
ssh beeplux-ai-2080ti@192.168.108.150 "cat > ~/apps/multi-agent-debate/multi-agent-debate-offline-images.tar" < multi-agent-debate-offline-images.tar
```

---

## 5. 服务器准备目录与代码

登录服务器后：

```bash
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/322dfs/multi-agent-debate.git
cd multi-agent-debate
```

若目录已存在，直接：

```bash
cd ~/apps/multi-agent-debate
git fetch origin
git checkout master
git reset --hard origin/master
```

---

## 6. 导入离线镜像

```bash
cd ~/apps/multi-agent-debate
sudo docker load -i multi-agent-debate-offline-images.tar
```

---

## 7. 创建离线部署配置（端口避让 + Ollama）

新建 `docker-compose.offline.yml`：

```yaml
version: "3.8"
services:
  backend:
    image: multi-agent-debate_backend:offline
    container_name: mad-backend
    environment:
      - DEEPSEEK_API_KEY=ollama-local
      - LLM_BASE_URL=http://host.docker.internal:11434/v1
      - DEBATE_MODEL=deepseek-r1:32b
      - DEBATE_APP_DATA_DIR=/app/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "48011:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    image: multi-agent-debate_frontend:offline
    container_name: mad-frontend
    depends_on:
      - backend
    ports:
      - "43000:3000"
    restart: unless-stopped
```

说明：

- `48011` / `43000` 是专门避让现有服务的端口
- 模型走服务器本机 Ollama：`host.docker.internal:11434`

---

## 8. 启动与验证

启动：

```bash
cd ~/apps/multi-agent-debate
sudo docker-compose -f docker-compose.offline.yml up -d
```

看状态：

```bash
sudo docker ps | grep -E "mad-backend|mad-frontend"
```

健康检查：

```bash
curl http://127.0.0.1:48011/api/health
```

访问地址：

- 前端：`http://192.168.108.150:43000`
- 后端：`http://192.168.108.150:48011`

---

## 9. 常见问题

### Q1：后端启动就报错 `python-multipart` 缺失

说明镜像没包含新依赖。先确认 `requirements.txt` 包含：

```text
python-multipart
```

然后重新执行第 3~8 步。

### Q2：服务器构建时拉镜像失败（EOF / timeout）

这是离线服务器典型问题，必须使用本地构建 + 离线导入流程。

### Q3：端口冲突

修改 `docker-compose.offline.yml` 的主机端口映射，例如：

- 后端：`49011:8000`
- 前端：`44000:3000`

然后重启：

```bash
sudo docker-compose -f docker-compose.offline.yml up -d --force-recreate
```

---

## 10. 日常运维命令

```bash
# 查看日志
sudo docker logs -f mad-backend
sudo docker logs -f mad-frontend

# 重启服务
sudo docker-compose -f docker-compose.offline.yml restart

# 停止服务
sudo docker-compose -f docker-compose.offline.yml down
```


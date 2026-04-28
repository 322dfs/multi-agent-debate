# 服务器操作手册（新手可用）

适用环境：`192.168.108.150`  
部署形态：离线 Docker 容器（`mad-frontend` + `mad-backend`）

本文档不是“如何部署”，而是“部署完成后如何日常使用和运维”。

---

## 1. 访问地址

- 前端（用户使用）：`http://192.168.108.150:43000`
- 后端（接口与健康检查）：`http://192.168.108.150:48011`
- 后端健康检查：`http://192.168.108.150:48011/api/health`

---

## 2. 正常使用流程（给业务同事）

### 2.1 智能辩论

1. 进入首页，选择“开始新辩论”
2. 输入辩题
3. 选择场景（IT/商业/人才等）
4. 选择辩手方式：
   - 手动勾选，或
   - 点击“智能推荐”（触发模型推荐）
5. 点击“开始辩论”
6. 观察逐条发言、主持总结和裁判结论

### 2.2 简历评审

1. 进入“简历多 Agent 评审”
2. 选择岗位模板或自定义岗位
3. 上传简历文件（PDF/DOCX/TXT/MD）
4. 可先点“仅解析简历（先看内容）”
5. 再点“开始评审”
6. 在“历史评审”查看过往评审结果

---

## 3. 服务启停（运维）

登录服务器后：

```bash
cd ~/apps/multi-agent-debate
```

### 启动

```bash
sudo docker-compose -f docker-compose.offline.yml up -d
```

### 停止

```bash
sudo docker-compose -f docker-compose.offline.yml down
```

### 重启

```bash
sudo docker-compose -f docker-compose.offline.yml restart
```

### 查看状态

```bash
sudo docker ps | grep -E "mad-frontend|mad-backend"
```

---

## 4. 日常巡检（建议）

### 4.1 健康检查

```bash
curl http://127.0.0.1:48011/api/health
```

返回包含 `"status":"ok"` 说明后端正常。

### 4.2 查看日志

```bash
sudo docker logs --tail 200 mad-backend
sudo docker logs --tail 200 mad-frontend
```

实时跟踪：

```bash
sudo docker logs -f mad-backend
```

### 4.3 端口占用核查

```bash
ss -ltn | grep -E "43000|48011"
```

---

## 5. 模型配置说明（当前已接本地 Ollama）

当前后端使用本机 Ollama，不走外网 API：

- `LLM_BASE_URL=http://host.docker.internal:11434/v1`
- `DEBATE_MODEL=deepseek-r1:32b`

如需切换模型：

1. 编辑 `docker-compose.offline.yml` 里的 `DEBATE_MODEL`
2. 重启后端容器：

```bash
sudo docker-compose -f docker-compose.offline.yml up -d --force-recreate backend
```

---

## 6. 数据位置与备份

### 6.1 业务数据位置

容器内路径：`/app/data`  
宿主机映射路径：`~/apps/multi-agent-debate/data`

包含：

- 辩论历史
- 简历评审历史
- 自定义岗位模板

### 6.2 备份

```bash
cd ~/apps/multi-agent-debate
tar -czf backup-data-$(date +%F).tar.gz data
```

### 6.3 恢复

```bash
cd ~/apps/multi-agent-debate
tar -xzf backup-data-YYYY-MM-DD.tar.gz
sudo docker-compose -f docker-compose.offline.yml restart
```

---

## 7. 常见问题处理

### Q1：页面能打开但功能报错

优先看后端日志：

```bash
sudo docker logs --tail 200 mad-backend
```

### Q2：简历上传时报依赖问题

如果出现 `python-multipart` 相关报错，说明镜像版本过旧，需要更新镜像。

### Q3：模型超时或响应慢

- 先确认 Ollama 服务存活：`curl http://127.0.0.1:11434/api/tags`
- 检查服务器资源（CPU/内存/GPU）
- 评估是否切换更轻量模型

### Q4：同事反馈无法访问

检查：

1. 容器是否运行（`docker ps`）
2. 端口是否监听（`ss -ltn`）
3. 防火墙策略是否放行 `43000/48011`

---

## 8. 升级发布（简版）

1. 更新代码到新版本
2. 构建新离线镜像（本地）
3. 导入服务器（`docker load`）
4. 重建容器：

```bash
sudo docker-compose -f docker-compose.offline.yml up -d --force-recreate
```

升级前建议先备份 `data` 目录。


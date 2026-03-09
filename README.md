# CircuitAI - AI电路图辅助工具

## 项目简介

CircuitAI 是一个 AI 驱动的电路图辅助工具，专注于电路图识别、解释、错误检查。上传电路图即可获得元件识别、原理解释、BOM 表和错误检测报告。

## 核心功能

1. **电路图识别与解释** — 上传 PNG/JPG 电路图，AI 自动识别元件并生成拓扑说明
2. **BOM 表自动生成** — 提取元件列表，支持 CSV 导出
3. **电路错误检测** — 检测电源接地、反接、去耦电容缺失等常见问题
4. **分析报告导出** — Markdown / CSV 格式下载

## 技术栈

- **前端**：React + Vite，支持中英文切换（i18n）
- **后端**：FastAPI（Python 3.12）
- **AI**：NVIDIA API（GLM-4V 视觉模型）
- **部署**：Docker Compose（nginx 反代 + uvicorn）

## 快速开始

### 本地开发

```bash
# 后端
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # 填入 NVIDIA_API_KEY
uvicorn main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

### Docker 部署

```bash
cp .env.example .env  # 填入 NVIDIA_API_KEY
docker compose up -d --build
# 访问 http://localhost
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/analyze` | 同步分析电路图 |
| POST | `/api/v1/analyze-async` | 异步分析（推荐） |
| GET  | `/api/v1/task/{id}` | 查询异步任务状态 |
| POST | `/api/v1/bom` | 生成 BOM 表 |
| POST | `/api/v1/detect-errors` | 错误检测 |
| POST | `/api/v1/full-analysis` | 完整分析（识别+BOM+错误） |
| GET  | `/api/v1/task/{id}/export-bom` | 导出 BOM CSV |
| GET  | `/api/v1/task/{id}/export-markdown` | 导出分析报告 |

## 测试

```bash
cd backend && source venv/bin/activate && cd ..
pytest tests/ -v  # 42 tests
```

## 文档

- [产品需求文档](./docs/PRD.md)
- [Week1 技术验证报告](./docs/WEEK1_SUMMARY.md)

## 项目状态

🚧 开发中 — MVP 阶段

---

**创建时间**：2026-03-02  
**维护**：码农 Agent & stone

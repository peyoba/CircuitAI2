# CircuitAI 项目结构说明

## 快速开始

### 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 一键启动（开发环境）
```bash
bash start-dev.sh
```

## 访问地址

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 项目结构

```
CircuitAI/
├── backend/               # 后端服务
│   ├── main.py           # FastAPI 主应用
│   ├── requirements.txt  # Python 依赖
│   └── services/         # 业务服务
│       ├── circuit_analyzer.py
│       ├── nvidia_analyzer.py
│       ├── bom_generator.py
│       └── error_detector.py
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── App.jsx       # 主组件
│   │   ├── App.css       # 样式
│   │   └── main.jsx      # 入口
│   ├── index.html
│   └── package.json
├── tests/                 # 测试文件
│   ├── test_services.py
│   └── images/           # 测试电路图
└── docs/                  # 文档
    ├── PRD.md
    └── CHANGELOG.md
```

## API 端点

- `GET /` - 服务状态
- `GET /health` - 健康检查
- `POST /api/v1/analyze` - 电路图识别
- `POST /api/v1/bom` - BOM 表生成
- `POST /api/v1/detect-errors` - 错误检测
- `POST /api/v1/full-analysis` - 完整分析

## 测试

```bash
# 运行所有测试
python3 tests/test_services.py

# 运行 API 测试
python3 tests/test_nvidia_api.py
```

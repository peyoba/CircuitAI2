#!/bin/bash

echo "🚀 启动 CircuitAI 开发环境"

# 启动后端
echo "📦 启动后端 API..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端..."
cd ../frontend
npm install -q
npm run dev &
FRONTEND_PID=$!

echo "✅ 服务已启动"
echo "   后端: http://localhost:8000"
echo "   前端: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待
wait $BACKEND_PID $FRONTEND_PID

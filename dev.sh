#!/bin/bash
# CircuitAI 开发环境启动脚本

echo "🚀 启动 CircuitAI 开发环境..."

# 启动后端
echo "📦 启动后端服务..."
cd backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 检查后端健康
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

echo ""
echo "================================"
echo "🚀 CircuitAI 开发环境已启动"
echo "================================"
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待子进程
wait

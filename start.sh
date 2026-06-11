#!/bin/bash
# ASMR Media Manager 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "  ASMR Media Manager 启动脚本"
echo "=========================================="
echo ""
echo "请选择启动模式:"
echo "  1) 开发模式 (后端 + 前端分离)"
echo "  2) Docker 模式"
echo "  3) 仅后端"
echo "  4) 仅前端"
echo "  5) 安装依赖"
echo ""
read -p "请输入选项 [1-5]: " choice

case $choice in
  1)
    echo ""
    echo "[1/2] 启动后端..."
    cd "$SCRIPT_DIR/backend"
    if [ ! -d "venv" ]; then
      echo "未找到虚拟环境，请先运行选项 5 安装依赖"
      exit 1
    fi
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    echo "后端已启动 (PID: $BACKEND_PID), 地址: http://localhost:8080"
    echo "Swagger UI: http://localhost:8080/docs"

    echo ""
    echo "[2/2] 启动前端..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
    echo "前端已启动 (PID: $FRONTEND_PID), 地址: http://localhost:5173"

    echo ""
    echo "=========================================="
    echo "  开发模式已启动"
    echo "  前端: http://localhost:5173"
    echo "  后端: http://localhost:8080"
    echo "  API 文档: http://localhost:8080/docs"
    echo "  按 Ctrl+C 停止所有服务"
    echo "=========================================="

    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    wait
    ;;

  2)
    echo ""
    echo "启动 Docker 模式..."
    cd "$SCRIPT_DIR"
    docker compose up -d
    echo ""
    echo "=========================================="
    echo "  Docker 模式已启动"
    echo "  访问地址: http://localhost:3000"
    echo "  查看日志: docker compose logs -f"
    echo "  停止服务: docker compose down"
    echo "=========================================="
    ;;

  3)
    echo ""
    echo "启动后端..."
    cd "$SCRIPT_DIR/backend"
    if [ ! -d "venv" ]; then
      echo "未找到虚拟环境，请先运行选项 5 安装依赖"
      exit 1
    fi
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
    ;;

  4)
    echo ""
    echo "启动前端..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev
    ;;

  5)
    echo ""
    echo "[1/2] 安装后端依赖..."
    cd "$SCRIPT_DIR/backend"
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "后端依赖安装完成"

    echo ""
    echo "初始化数据库..."
    python migrate.py

    echo ""
    echo "[2/2] 安装前端依赖..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    echo "前端依赖安装完成"

    echo ""
    echo "=========================================="
    echo "  依赖安装完成！"
    echo "  运行选项 1 启动开发模式"
    echo "=========================================="
    ;;

  *)
    echo "无效选项"
    exit 1
    ;;
esac

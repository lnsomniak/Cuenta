#!/bin/bash
#local test runner 
echo ""
echo "============================"
echo "🛒 FIT-ECON MVP - Local Test"
echo "============================"
echo ""

# wpopsie
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# checks if dependencies are installed
echo "📦 Checking dependencies..."
pip3 install fastapi uvicorn pulp requests --quiet 2>/dev/null

# run it chat
echo ""
echo "🧪 Running optimization test..."
echo ""
cd "$(dirname "$0")"
python3 test_optimizer.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " To start the full web app:"
echo ""
echo "   Terminal 1 (API):"
echo "   cd api && python server.py"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   cd web && npm install && npm run dev"
echo ""
echo "   Then open: http://localhost:3000 in that order!!!!!!! I cannot stress this enough."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

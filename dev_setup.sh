#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/atome-bot/backend"
FRONTEND_DIR="$ROOT_DIR/atome-bot/frontend"
ENV_FILE="$BACKEND_DIR/.env"
VENV_DIR="$BACKEND_DIR/venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required (3.10+)."
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")')"
case "$PYTHON_VERSION" in
  3.10|3.11|3.12) ;;
  *)
    echo "Unsupported python version: $PYTHON_VERSION"
    echo "Please use Python 3.10, 3.11, or 3.12 for local setup."
    exit 1
    ;;
esac

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required (Node.js 18+)."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

cd "$FRONTEND_DIR"
npm install

if [ ! -f "$ENV_FILE" ]; then
  cat <<EOF > "$ENV_FILE"
OPENAI_API_KEY=
EOF
fi

echo
echo "Setup complete."
echo "1) Add API key in: $ENV_FILE"
echo "   OPENAI_API_KEY=sk-..."
echo
echo "2) Run backend:"
echo "   cd $BACKEND_DIR && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo
echo "3) Run frontend (new terminal):"
echo "   cd $FRONTEND_DIR && npm run dev -- --host 0.0.0.0 --port 5173"

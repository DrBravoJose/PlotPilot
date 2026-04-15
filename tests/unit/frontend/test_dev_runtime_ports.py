from pathlib import Path


ROOT = Path("/Users/mac/Desktop/codex/复刻/PlotPilot-upstream")


def test_direct_backend_entrypoint_uses_port_8005():
    source = (ROOT / "interfaces/main.py").read_text(encoding="utf-8")

    assert 'uvicorn.run(app, host="0.0.0.0", port=8005)' in source


def test_vite_dev_server_uses_port_3003_with_strict_port():
    source = (ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")

    assert "port: 3003" in source
    assert "strictPort: true" in source
    assert "target: 'http://127.0.0.1:8005'" in source
    assert "host: '127.0.0.1'" in source


def test_readme_documents_8005_backend_and_3003_frontend():
    source = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "uvicorn interfaces.main:app --host 127.0.0.1 --port 8005 --reload" in source
    assert "前端运行在 http://localhost:3003" in source


def test_backend_dev_cors_allows_3003_frontend():
    source = (ROOT / "interfaces/main.py").read_text(encoding="utf-8")

    assert "http://localhost:3003" in source
    assert "http://127.0.0.1:3003" in source

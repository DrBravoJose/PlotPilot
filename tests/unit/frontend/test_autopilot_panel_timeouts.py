from pathlib import Path


def test_autopilot_panel_uses_fetch_timeout_for_control_actions():
    source = Path(
        "/Users/mac/Desktop/codex/复刻/PlotPilot-upstream/frontend/src/components/autopilot/AutopilotPanel.vue"
    ).read_text(encoding="utf-8")

    assert "const REQUEST_TIMEOUT_MS = 10000" in source
    assert "async function fetchWithTimeout(" in source
    assert "const res = await fetchWithTimeout(`${base()}/resume`, { method: 'POST' })" in source
    assert "const res = await fetchWithTimeout(`${base()}/start`, {" in source
    assert "await fetchWithTimeout(`${base()}/stop`, { method: 'POST' })" in source
    assert "const res = await fetchWithTimeout(`${base()}/circuit-breaker/reset`, { method: 'POST' })" in source

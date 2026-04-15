from pathlib import Path


def test_macro_plan_modal_recovers_quick_plan_after_timeout_by_refreshing_structure():
    source = Path(
        "/Users/mac/Desktop/codex/复刻/PlotPilot-upstream/frontend/src/components/workbench/MacroPlanModal.vue"
    ).read_text(encoding="utf-8")

    assert "const QUICK_PLAN_TIMEOUT_MS = 150000" in source
    assert "planningApi.getStructure(props.novelId)" in source
    assert "结构已在后台生成并写入，正在刷新..." in source
    assert "AbortController" in source
    assert "signal: controller.signal" in source

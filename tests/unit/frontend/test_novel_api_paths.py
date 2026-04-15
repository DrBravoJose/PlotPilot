from pathlib import Path


def test_novel_collection_endpoints_use_trailing_slash():
    source = Path(
        "/Users/mac/Desktop/codex/复刻/PlotPilot-upstream/frontend/src/api/novel.ts"
    ).read_text(encoding="utf-8")

    assert "listNovels: () => apiClient.get<NovelDTO[]>('/novels/')" in source
    assert "}) => apiClient.post<NovelDTO>('/novels/', data)" in source

from application.blueprint.services.continuous_planning_service import ContinuousPlanningService
from application.blueprint.services.story_structure_service import StoryStructureService
from interfaces.api.v1.blueprint import continuous_planning_routes
from interfaces.api.v1.blueprint import story_structure


class _StubBibleRepository:
    pass


class _StubBibeService:
    def __init__(self, repository):
        self.repository = repository


class _StubLlmService:
    pass


def test_get_planning_service_uses_shared_llm_dependency(monkeypatch):
    sentinel_llm = _StubLlmService()
    sentinel_chapter_repository = object()

    monkeypatch.setattr(story_structure, "BIBLE_SERVICE_CLS", _StubBibeService, raising=False)
    monkeypatch.setattr(
        story_structure,
        "get_bible_repository",
        lambda: _StubBibleRepository(),
        raising=False,
    )
    monkeypatch.setattr(
        story_structure,
        "get_llm_service",
        lambda: sentinel_llm,
        raising=False,
    )
    monkeypatch.setattr(
        story_structure,
        "get_chapter_repository",
        lambda: sentinel_chapter_repository,
        raising=False,
    )

    service = story_structure.get_planning_service()

    assert isinstance(service, ContinuousPlanningService)
    assert service.llm_service is sentinel_llm
    assert service.chapter_repository is sentinel_chapter_repository


def test_story_structure_get_service_uses_shared_chapter_repository(monkeypatch):
    sentinel_planning = object()
    sentinel_chapter_repository = object()

    monkeypatch.setattr(
        story_structure,
        "get_chapter_repository",
        lambda: sentinel_chapter_repository,
        raising=False,
    )

    service = story_structure.get_service(planning_service=sentinel_planning)

    assert isinstance(service, StoryStructureService)
    assert service._planning_service is sentinel_planning
    assert service._chapter_repository is sentinel_chapter_repository


def test_continuous_planning_get_service_uses_shared_llm_dependency(monkeypatch):
    sentinel_llm = _StubLlmService()
    sentinel_chapter_repository = object()

    monkeypatch.setattr(continuous_planning_routes, "BIBLE_SERVICE_CLS", _StubBibeService, raising=False)
    monkeypatch.setattr(
        continuous_planning_routes,
        "get_bible_repository",
        lambda: _StubBibleRepository(),
        raising=False,
    )
    monkeypatch.setattr(
        continuous_planning_routes,
        "get_llm_service",
        lambda: sentinel_llm,
        raising=False,
    )
    monkeypatch.setattr(
        continuous_planning_routes,
        "get_chapter_repository",
        lambda: sentinel_chapter_repository,
        raising=False,
    )

    service = continuous_planning_routes.get_service()

    assert isinstance(service, ContinuousPlanningService)
    assert service.llm_service is sentinel_llm
    assert service.chapter_repository is sentinel_chapter_repository

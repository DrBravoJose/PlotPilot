"""Novel 应用服务"""
from typing import List, Optional, Dict, Any
from domain.novel.entities.novel import Novel, NovelStage
from domain.novel.entities.chapter import Chapter
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.word_count import WordCount
from domain.novel.repositories.novel_repository import NovelRepository
from domain.shared.exceptions import EntityNotFoundError
from application.dtos.novel_dto import NovelDTO


class NovelService:
    """Novel 应用服务

    协调领域对象和基础设施，实现应用用例。
    """

    def __init__(self, novel_repository: NovelRepository):
        """初始化服务

        Args:
            novel_repository: Novel 仓储
        """
        self.novel_repository = novel_repository

    def create_novel(
        self,
        novel_id: str,
        title: str,
        author: str,
        target_chapters: int
    ) -> NovelDTO:
        """创建新小说

        Args:
            novel_id: 小说 ID
            title: 标题
            author: 作者
            target_chapters: 目标章节数

        Returns:
            NovelDTO
        """
        novel = Novel(
            id=NovelId(novel_id),
            title=title,
            author=author,
            target_chapters=target_chapters,
            stage=NovelStage.PLANNING
        )

        self.novel_repository.save(novel)

        return NovelDTO.from_domain(novel)

    def get_novel(self, novel_id: str) -> Optional[NovelDTO]:
        """获取小说

        Args:
            novel_id: 小说 ID

        Returns:
            NovelDTO 或 None
        """
        novel = self.novel_repository.get_by_id(NovelId(novel_id))

        if novel is None:
            return None

        dto = NovelDTO.from_domain(novel)

        # Check for metadata files
        dto.has_bible = self.novel_repository.storage.exists(f"novels/{novel_id}/bible.json")
        dto.has_outline = self.novel_repository.storage.exists(f"novels/{novel_id}/outline.json")

        return dto

    def list_novels(self) -> List[NovelDTO]:
        """列出所有小说

        Returns:
            NovelDTO 列表
        """
        novels = self.novel_repository.list_all()
        return [NovelDTO.from_domain(novel) for novel in novels]

    def delete_novel(self, novel_id: str) -> None:
        """删除小说

        Args:
            novel_id: 小说 ID
        """
        self.novel_repository.delete(NovelId(novel_id))

    def add_chapter(
        self,
        novel_id: str,
        chapter_id: str,
        number: int,
        title: str,
        content: str
    ) -> NovelDTO:
        """添加章节

        Args:
            novel_id: 小说 ID
            chapter_id: 章节 ID
            number: 章节编号
            title: 章节标题
            content: 章节内容

        Returns:
            更新后的 NovelDTO

        Raises:
            ValueError: 如果小说不存在
        """
        novel = self.novel_repository.get_by_id(NovelId(novel_id))

        if novel is None:
            raise ValueError(f"Novel not found: {novel_id}")

        chapter = Chapter(
            id=chapter_id,
            novel_id=NovelId(novel_id),
            number=number,
            title=title,
            content=content
        )

        novel.add_chapter(chapter)
        self.novel_repository.save(novel)

        return NovelDTO.from_domain(novel)

    def update_novel_stage(self, novel_id: str, stage: str) -> NovelDTO:
        """更新小说阶段

        Args:
            novel_id: 小说 ID
            stage: 阶段

        Returns:
            更新后的 NovelDTO

        Raises:
            EntityNotFoundError: 如果小说不存在
        """
        novel = self.novel_repository.get_by_id(NovelId(novel_id))
        if novel is None:
            raise EntityNotFoundError("Novel", novel_id)

        novel.stage = NovelStage(stage)
        self.novel_repository.save(novel)

        return NovelDTO.from_domain(novel)

    def get_novel_statistics(self, novel_id: str) -> Dict[str, Any]:
        """获取小说统计信息

        Args:
            novel_id: 小说 ID

        Returns:
            统计信息字典

        Raises:
            EntityNotFoundError: 如果小说不存在
        """
        novel = self.novel_repository.get_by_id(NovelId(novel_id))
        if novel is None:
            raise EntityNotFoundError("Novel", novel_id)

        return {
            "total_chapters": len(novel.chapters),
            "total_words": novel.get_total_word_count().value,
            "completed_chapters": len([c for c in novel.chapters if c.word_count.value > 0]),
            "stage": novel.stage.value
        }

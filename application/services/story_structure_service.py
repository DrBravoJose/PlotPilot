"""
故事结构服务
"""

import uuid
from typing import List, Optional, Dict, Any

from domain.structure.story_node import StoryNode, StoryTree, NodeType
from infrastructure.persistence.database.story_node_repository import StoryNodeRepository


class StoryStructureService:
    """故事结构服务"""

    def __init__(self, repository: StoryNodeRepository):
        self.repository = repository

    def get_tree(self, novel_id: str) -> Dict[str, Any]:
        """获取小说的完整结构树"""
        tree = self.repository.get_tree(novel_id)
        return {
            "novel_id": novel_id,
            "tree": tree.to_tree_dict()
        }

    def get_children(self, novel_id: str, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取子节点（用于渐进式加载）"""
        nodes = self.repository.get_children(parent_id, novel_id)
        return [node.to_dict() for node in nodes]

    def create_node(
        self,
        novel_id: str,
        node_type: str,
        number: int,
        title: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        order_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建节点"""
        # 验证节点类型
        try:
            node_type_enum = NodeType(node_type)
        except ValueError:
            raise ValueError(f"Invalid node_type: {node_type}")

        # 如果未指定 order_index，自动计算
        if order_index is None:
            siblings = self.repository.get_children(parent_id, novel_id)
            order_index = len(siblings)

        # 创建节点
        node = StoryNode(
            id=f"node-{uuid.uuid4().hex[:12]}",
            novel_id=novel_id,
            parent_id=parent_id,
            node_type=node_type_enum,
            number=number,
            title=title,
            description=description,
            order_index=order_index
        )

        saved_node = self.repository.save(node)
        return saved_node.to_dict()

    def update_node(
        self,
        node_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        number: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新节点"""
        node = self.repository.get_by_id(node_id)
        if not node:
            raise ValueError(f"Node not found: {node_id}")

        if title is not None:
            node.title = title
        if description is not None:
            node.description = description
        if number is not None:
            node.number = number

        saved_node = self.repository.save(node)
        return saved_node.to_dict()

    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        return self.repository.delete(node_id)

    def reorder_nodes(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        """重新排序节点"""
        nodes = []
        for idx, node_id in enumerate(node_ids):
            node = self.repository.get_by_id(node_id)
            if node:
                node.order_index = idx
                nodes.append(node)

        saved_nodes = self.repository.save_batch(nodes)
        return [node.to_dict() for node in saved_nodes]

    def update_chapter_ranges(self, novel_id: str):
        """更新章节范围"""
        self.repository.update_chapter_ranges(novel_id)

    def create_default_structure(self, novel_id: str, total_chapters: int = 100) -> Dict[str, Any]:
        """创建默认结构（示例：3部，每部3卷，每卷若干幕）"""
        nodes = []
        order_idx = 0
        chapter_idx = 1

        chapters_per_part = total_chapters // 3
        chapters_per_volume = chapters_per_part // 3
        chapters_per_act = 5  # 每幕约5章

        for part_num in range(1, 4):
            # 创建部
            part = StoryNode(
                id=f"node-part-{part_num}",
                novel_id=novel_id,
                node_type=NodeType.PART,
                number=part_num,
                title=f"第{part_num}部",
                order_index=order_idx
            )
            nodes.append(part)
            order_idx += 1

            for vol_num in range(1, 4):
                # 创建卷
                volume = StoryNode(
                    id=f"node-vol-{part_num}-{vol_num}",
                    novel_id=novel_id,
                    parent_id=part.id,
                    node_type=NodeType.VOLUME,
                    number=vol_num,
                    title=f"第{vol_num}卷",
                    order_index=order_idx
                )
                nodes.append(volume)
                order_idx += 1

                # 创建幕
                acts_in_volume = chapters_per_volume // chapters_per_act
                for act_num in range(1, acts_in_volume + 1):
                    act_start = chapter_idx
                    act_end = min(chapter_idx + chapters_per_act - 1, total_chapters)

                    act = StoryNode(
                        id=f"node-act-{part_num}-{vol_num}-{act_num}",
                        novel_id=novel_id,
                        parent_id=volume.id,
                        node_type=NodeType.ACT,
                        number=act_num,
                        title=f"第{act_num}幕",
                        order_index=order_idx,
                        chapter_start=act_start,
                        chapter_end=act_end,
                        chapter_count=act_end - act_start + 1
                    )
                    nodes.append(act)
                    order_idx += 1
                    chapter_idx = act_end + 1

                    if chapter_idx > total_chapters:
                        break

                if chapter_idx > total_chapters:
                    break

            if chapter_idx > total_chapters:
                break

        # 批量保存
        self.repository.save_batch(nodes)

        # 更新章节范围
        self.update_chapter_ranges(novel_id)

        return self.get_tree(novel_id)

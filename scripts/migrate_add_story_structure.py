#!/usr/bin/env python3
"""
数据库迁移：添加四级叙事结构（部-卷-幕-章）

新增 story_nodes 表，支持：
- 部 (Part)
- 卷 (Volume)
- 幕 (Act)
- 章 (Chapter) - 通过 chapters 表的 act_id 关联

运行方式：
    python scripts/migrate_add_story_structure.py
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "data" / "aitext.db"


def migrate():
    """执行迁移"""
    print(f"连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. 创建 story_nodes 表
        print("\n[1/3] 创建 story_nodes 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_nodes (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL,
                parent_id TEXT,
                node_type TEXT NOT NULL CHECK(node_type IN ('part', 'volume', 'act')),
                number INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                order_index INTEGER NOT NULL,

                -- 章节范围（自动计算）
                chapter_start INTEGER,
                chapter_end INTEGER,
                chapter_count INTEGER DEFAULT 0,

                -- 元数据（JSON 格式）
                metadata TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES story_nodes(id) ON DELETE CASCADE
            )
        """)
        print("✓ story_nodes 表创建成功")

        # 2. 创建索引
        print("\n[2/3] 创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_nodes_novel
            ON story_nodes(novel_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_nodes_parent
            ON story_nodes(parent_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_nodes_type
            ON story_nodes(node_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_nodes_order
            ON story_nodes(novel_id, order_index)
        """)
        print("✓ 索引创建成功")

        # 3. 扩展 chapters 表
        print("\n[3/3] 扩展 chapters 表...")

        # 检查 act_id 列是否已存在
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'act_id' not in columns:
            cursor.execute("""
                ALTER TABLE chapters ADD COLUMN act_id TEXT
                REFERENCES story_nodes(id) ON DELETE SET NULL
            """)
            print("✓ 添加 act_id 列")
        else:
            print("✓ act_id 列已存在")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chapters_act
            ON chapters(act_id)
        """)
        print("✓ 章节索引创建成功")

        # 提交事务
        conn.commit()
        print("\n✅ 迁移完成！")
        print("\n数据库结构：")
        print("  📚 部 (Part)")
        print("    📖 卷 (Volume)")
        print("      🎬 幕 (Act)")
        print("        📄 章 (Chapter)")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        conn.close()


def verify():
    """验证迁移结果"""
    print("\n" + "="*50)
    print("验证迁移结果...")
    print("="*50)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 story_nodes 表
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='story_nodes'")
        if cursor.fetchone()[0] == 1:
            print("✓ story_nodes 表存在")
        else:
            print("✗ story_nodes 表不存在")
            return False

        # 检查索引
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_story_nodes%'")
        index_count = cursor.fetchone()[0]
        print(f"✓ story_nodes 索引数量: {index_count}")

        # 检查 chapters 表的 act_id 列
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'act_id' in columns:
            print("✓ chapters.act_id 列存在")
        else:
            print("✗ chapters.act_id 列不存在")
            return False

        print("\n✅ 验证通过！")
        return True

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*50)
    print("数据库迁移：添加四级叙事结构")
    print("="*50)

    migrate()
    verify()

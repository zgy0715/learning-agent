"""
知识库索引构建脚本
将课程文档导入MongoDB并构建向量索引
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_db, get_collection, close_db
from app.services.rag import rag_service


async def index_course(course_file: str):
    """
    索引单个课程

    Args:
        course_file: 课程JSON文件路径
    """
    print(f"正在索引课程: {course_file}")

    # 读取课程数据
    with open(course_file, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    course_id = course_data.get("course_id")
    title = course_data.get("title")

    # 准备文档切片
    chunks = []
    for chapter in course_data.get("chapters", []):
        chapter_title = chapter.get("title", "")
        for content_item in chapter.get("content", []):
            chunks.append({
                "chapter": chapter_title,
                "content": content_item.get("content", ""),
                "metadata": {
                    "source_file": f"{title}.json",
                    "chapter_id": chapter.get("chapter_id"),
                    **content_item.get("metadata", {})
                }
            })

    # 索引到MongoDB
    await rag_service.index_document(course_id, chunks)

    print(f"完成索引: {title} ({len(chunks)} chunks)")


async def main():
    """主函数"""
    # 连接数据库
    await connect_db()
    print("已连接MongoDB")

    # 清空旧索引（旧版本可能是随机向量，必须清掉避免真假向量混用）
    deleted = await get_collection("knowledge_docs").delete_many({})
    print(f"已清空旧索引: {deleted.deleted_count} 条")

    # 索引所有课程（真实 embedding 向量）
    courses_dir = Path(__file__).parent / "courses"
    for course_file in courses_dir.glob("*.json"):
        await index_course(str(course_file))

    # 为关键词检索创建文本索引（混合检索用，失败可忽略）
    try:
        await get_collection("knowledge_docs").create_index([("content", "text")])
        print("已创建 content 文本索引")
    except Exception as e:
        print(f"文本索引创建跳过: {e}")

    # 关闭数据库
    await close_db()
    print("索引完成！")


if __name__ == "__main__":
    asyncio.run(main())

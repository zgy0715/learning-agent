"""
知识库检索工具
MCP风格定义的知识检索工具
"""
from typing import Dict, Any
from pydantic import BaseModel, Field

from app.services.rag import rag_service


class KnowledgeSearchInput(BaseModel):
    """知识检索输入"""
    query: str = Field(description="检索查询")
    top_k: int = Field(default=5, description="返回结果数量")
    course_id: str = Field(default=None, description="课程ID（可选）")


class KnowledgeSearchOutput(BaseModel):
    """知识检索输出"""
    documents: list = Field(description="检索到的文档列表")
    total_results: int = Field(description="总结果数量")


async def knowledge_search(input_data: KnowledgeSearchInput) -> KnowledgeSearchOutput:
    """
    知识库语义检索工具

    在课程知识库中检索与查询相关的文档片段

    Args:
        input_data: 检索输入参数

    Returns:
        KnowledgeSearchOutput: 检索结果
    """
    try:
        results = await rag_service.hybrid_retrieve(
            query=input_data.query,
            top_k=input_data.top_k,
            course_id=input_data.course_id
        )

        documents = [
            {
                "content": r.content,
                "source": r.source,
                "score": r.score,
                "metadata": r.metadata
            }
            for r in results
        ]

        return KnowledgeSearchOutput(
            documents=documents,
            total_results=len(documents)
        )

    except Exception as e:
        return KnowledgeSearchOutput(
            documents=[],
            total_results=0
        )


# 工具定义（MCP风格）
KNOWLEDGE_SEARCH_TOOL = {
    "name": "knowledge_search",
    "description": "在课程知识库中检索与查询相关的文档片段",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索查询"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            },
            "course_id": {
                "type": "string",
                "description": "课程ID（可选）"
            }
        },
        "required": ["query"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "documents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "source": {"type": "string"},
                        "score": {"type": "number"}
                    }
                }
            },
            "total_results": {"type": "integer"}
        }
    }
}

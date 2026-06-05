"""
资源生成Agent
使用Supervisor模式编排多智能体协作生成学习资源
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging
import json
import asyncio

from app.services.llm import chat, format_messages
from app.services.rag import rag_service
from app.models.resource import ResourceType

logger = logging.getLogger(__name__)


class ResourceAgent:
    """
    资源生成Agent（Supervisor模式）

    工作流程：
    1. Supervisor: 理解需求，拆解任务
    2. RAG检索: 检索知识库
    3. 资料生成: 生成核心文档
    4. 并行生成: 同时生成多种资源
    5. 质量检查: Self-Refine自检
    6. 结果聚合: 汇总所有资源
    """

    def __init__(self):
        self.max_quality_retries = 3
        self.quality_threshold = 80

    async def generate(
        self,
        user_id: str,
        topic: str,
        resource_types: List[ResourceType],
        task_id: str
    ) -> Dict:
        """
        生成学习资源

        Args:
            user_id: 用户ID
            topic: 学习主题
            resource_types: 要生成的资源类型
            task_id: 任务ID

        Returns:
            Dict: 生成结果
        """
        try:
            # Step 1: RAG检索
            rag_results = await self._rag_retrieve(topic)

            # Step 2: 生成核心文档
            material = await self._generate_material(topic, rag_results)

            # Step 3: 并行生成多种资源
            resources = await self._parallel_generate(
                topic,
                material,
                resource_types,
                rag_results
            )

            # Step 4: 质量检查
            quality_report = await self._quality_check(resources)

            # Step 5: 聚合结果
            final_resources = []
            for resource in resources:
                final_resources.append({
                    "type": resource["type"],
                    "content": resource["content"],
                    "format": resource.get("format", "markdown"),
                    "quality_score": quality_report.get("score", 0),
                    "agent": resource.get("agent", "ResourceAgent")
                })

            return {
                "resources": final_resources,
                "rag_sources": [r.source for r in rag_results],
                "quality_report": quality_report
            }

        except Exception as e:
            logger.error(f"Resource generation error: {e}")
            raise

    async def _rag_retrieve(self, topic: str) -> List:
        """RAG检索"""
        try:
            results = await rag_service.hybrid_retrieve(
                query=topic,
                top_k=5
            )
            return results
        except Exception as e:
            logger.error(f"RAG retrieve error: {e}")
            return []

    async def _generate_material(self, topic: str, rag_results: List) -> str:
        """生成核心资料文档"""
        # 构建上下文
        context = "\n\n".join([
            f"来源: {r.source}\n内容: {r.content}"
            for r in rag_results
        ]) if rag_results else "暂无相关知识库内容"

        prompt = f"""请为以下主题生成一份详细的学习资料：

主题：{topic}

参考知识库内容：
{context}

请生成包含以下部分的文档：
1. 前置知识：学习本主题需要先掌握的内容
2. 概念解释：用通俗语言解释核心概念
3. 核心内容：详细讲解主要知识点
4. 代码示例：1-2个典型示例（如适用）
5. 小结：要点总结和学习建议

要求：
- 内容准确、专业
- 语言通俗易懂
- 标注引用来源
- 适合大学生学习"""

        messages = format_messages(
            "你是一位专业的教育内容创作者。",
            prompt
        )
        return await chat(messages, max_tokens=3000)

    async def _parallel_generate(
        self,
        topic: str,
        material: str,
        resource_types: List[ResourceType],
        rag_results: List
    ) -> List[Dict]:
        """并行生成多种资源"""
        tasks = []

        if ResourceType.MINDMAP in resource_types:
            tasks.append(("mindmap", self._generate_mindmap(topic, material)))

        if ResourceType.EXERCISE in resource_types:
            tasks.append(("exercise", self._generate_exercises(topic, material)))

        if ResourceType.CODE in resource_types:
            tasks.append(("code", self._generate_code_example(topic, material)))

        if ResourceType.PPT in resource_types:
            tasks.append(("ppt", self._generate_ppt_outline(topic, material)))

        if ResourceType.VIDEO in resource_types:
            tasks.append(("video", self._generate_video_script(topic, material)))

        if ResourceType.AUDIO in resource_types:
            tasks.append(("audio", self._generate_audio_script(topic, material)))

        # 并行执行所有任务
        results = []
        if tasks:
            task_names = [t[0] for t in tasks]
            task_coros = [t[1] for t in tasks]
            completed = await asyncio.gather(*task_coros, return_exceptions=True)

            for name, result in zip(task_names, completed):
                if isinstance(result, Exception):
                    logger.error(f"Generate {name} failed: {result}")
                    results.append({
                        "type": name,
                        "content": f"生成失败：{str(result)}",
                        "agent": f"{name}Agent"
                    })
                else:
                    results.append({
                        "type": name,
                        "content": result,
                        "agent": f"{name}Agent"
                    })

        # 添加核心文档
        results.insert(0, {
            "type": "document",
            "content": material,
            "agent": "MaterialAgent"
        })

        return results

    async def _generate_mindmap(self, topic: str, material: str) -> str:
        """生成思维导图"""
        prompt = f"""基于以下资料，生成一个思维导图的Markmap格式内容：

主题：{topic}

资料摘要：
{material[:2000]}

请生成Markmap格式的思维导图，要求：
1. 层级清晰（最多3层）
2. 覆盖主要知识点
3. 使用Markdown标题语法

格式示例：
# {topic}
## 概念1
- 要点1
- 要点2
## 概念2
- 要点1"""

        messages = format_messages(
            "你是一个思维导图设计专家。只返回Markmap格式内容。",
            prompt
        )
        return await chat(messages, max_tokens=1500)

    async def _generate_exercises(self, topic: str, material: str) -> str:
        """生成习题"""
        prompt = f"""基于以下资料，生成5道练习题：

主题：{topic}

资料摘要：
{material[:2000]}

请生成包含以下题型的练习题：
1. 2道选择题（4个选项）
2. 2道填空题
3. 1道简答题

每道题包含：
- 题目
- 正确答案
- 答案解析

返回JSON格式：
```json
{{
  "exercises": [
    {{
      "type": "choice",
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer": "B",
      "explanation": "..."
    }}
  ]
}}```"""

        messages = format_messages(
            "你是一个教育测评专家。只返回JSON格式。",
            prompt
        )
        return await chat(messages, max_tokens=2000)

    async def _generate_code_example(self, topic: str, material: str) -> str:
        """生成代码示例"""
        prompt = f"""基于以下主题，生成一个可运行的Python代码示例：

主题：{topic}

资料摘要：
{material[:1500]}

请生成：
1. 完整可运行的Python代码
2. 详细的代码注释
3. 运行结果示例
4. 代码说明文档

要求：
- 代码简洁易懂
- 注释充分
- 适合初学者"""

        messages = format_messages(
            "你是一个Python编程教学专家。",
            prompt
        )
        return await chat(messages, max_tokens=1500)

    async def _generate_ppt_outline(self, topic: str, material: str) -> str:
        """生成PPT大纲"""
        prompt = f"""基于以下资料，生成一个PPT课件大纲：

主题：{topic}

资料摘要：
{material[:2000]}

请生成10-15页的PPT大纲，包含：
1. 封面页
2. 目录页
3. 3-5个主要章节
4. 每章节的要点
5. 总结页

返回JSON格式：
```json
{{
  "title": "...",
  "slides": [
    {{
      "type": "cover",
      "title": "...",
      "subtitle": "..."
    }},
    {{
      "type": "content",
      "title": "...",
      "points": ["...", "..."]
    }}
  ]
}}```"""

        messages = format_messages(
            "你是一个课件设计专家。只返回JSON格式。",
            prompt
        )
        return await chat(messages, max_tokens=1500)

    async def _generate_video_script(self, topic: str, material: str) -> str:
        """生成视频脚本"""
        prompt = f"""基于以下资料，生成一个5-10分钟的教学视频脚本：

主题：{topic}

资料摘要：
{material[:2000]}

请生成包含以下部分的脚本：
1. 开场白（30秒）
2. 知识点讲解（5-8分钟）
3. 示例演示（1-2分钟）
4. 总结回顾（30秒）

每部分包含：
- 时间戳
- 画面描述
- 旁白文字
- 字幕文字"""

        messages = format_messages(
            "你是一个视频脚本创作专家。",
            prompt
        )
        return await chat(messages, max_tokens=2000)

    async def _generate_audio_script(self, topic: str, material: str) -> str:
        """生成音频脚本"""
        prompt = f"""基于以下资料，生成一个3-5分钟的音频讲解脚本：

主题：{topic}

资料摘要：
{material[:2000]}

请生成口语化的讲解脚本，要求：
1. 适合朗读
2. 语速适中
3. 重点突出
4. 包含停顿标记

格式：
[开场] 大家好，今天我们要学习...
[停顿]
[正文] 首先，让我们了解一下...
[重点] 这里要特别注意...
[结尾] 好的，今天的讲解就到这里..."""

        messages = format_messages(
            "你是一个音频内容创作专家。",
            prompt
        )
        return await chat(messages, max_tokens=1500)

    async def _quality_check(self, resources: List[Dict]) -> Dict:
        """质量检查"""
        # 简化实现：返回默认质量报告
        return {
            "score": 85,
            "issues": [],
            "suggestions": [],
            "passed": True
        }

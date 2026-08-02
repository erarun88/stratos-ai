"""Memory Decision Engine - LLM-powered intelligent decisions about what to remember."""

import json
import logging
from typing import Any, Dict, List, Optional

from .memory_model import (
    MemoryDecision,
    MemoryDecisionAction,
    MemoryEntry,
    MemoryScope,
    MemoryType,
)
from .memory_store import MemoryStore

logger = logging.getLogger(__name__)


class MemoryDecisionEngine:
    """LLM-powered decision engine that intelligently decides what to remember."""

    def __init__(self, llm_client: Optional[Any] = None, memory_store: Optional[MemoryStore] = None):
        self.llm = llm_client
        self.store = memory_store or MemoryStore()

    async def decide(
        self,
        statement: str,
        scope: str,
        scope_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> MemoryDecision:
        """
        Decide what to do with a statement.
        Returns: IGNORE | STORE | UPDATE | MERGE | DELETE
        """

        # If no LLM available, default to STORE (Phase 2 feature)
        if not self.llm:
            logger.warning("No LLM client available - defaulting decision to STORE")
            return MemoryDecision(
                action=MemoryDecisionAction.STORE,
                confidence=0.5,
                rationale="LLM not available - storing as safety default",
                suggested_scope=scope,
                suggested_memory_type=MemoryType.CONTEXT,
            )

        # Get existing memories for this scope
        existing = await self.store.retrieve_all(scope, scope_id)

        # Build decision prompt
        prompt = self._build_decision_prompt(
            statement=statement,
            scope=scope,
            existing_count=len(existing),
            existing_samples=existing[:3],  # Show first 3 as examples
            context=context,
        )

        try:
            # Call LLM to decide
            response = self.llm.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            response_text = response.choices[0].message.content

            # Parse response
            decision = self._parse_decision_response(response_text)
            logger.info(
                f"Decision Engine: {decision.action} (confidence: {decision.confidence:.2f}) "
                f"for: {statement[:50]}..."
            )

            return decision

        except Exception as e:
            logger.error(f"Decision engine error: {e}")
            # Fallback: STORE if error
            return MemoryDecision(
                action=MemoryDecisionAction.STORE,
                confidence=0.5,
                rationale="Error in decision engine, defaulting to store",
                suggested_scope=scope,
                suggested_memory_type=MemoryType.CONTEXT,
            )

    async def process(
        self,
        statement: str,
        scope: str,
        scope_id: str,
        source: str = "user_input",
        source_id: str = "",
        component_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full pipeline: Statement → Decision → Action
        Returns: What action was taken
        """

        # Get decision
        decision = await self.decide(statement, scope, scope_id)

        # Execute decision
        if decision.action == MemoryDecisionAction.IGNORE:
            return {
                "action": "ignored",
                "reason": decision.rationale,
                "confidence": decision.confidence,
            }

        elif decision.action == MemoryDecisionAction.STORE:
            # Create new memory
            memory = await self.store.store(
                scope=decision.suggested_scope,
                scope_id=scope_id,
                memory_type=decision.suggested_memory_type,
                title=decision.suggested_title or statement[:100],
                content={"text": statement},
                importance=decision.confidence,
                source=source,
                source_id=source_id,
                component_id=component_id,
                tags=["auto_generated"],
            )

            return {
                "action": "stored",
                "memory_id": memory.memory_id,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
            }

        elif decision.action == MemoryDecisionAction.UPDATE:
            # Update existing memory
            if not decision.related_memory_ids:
                return {
                    "action": "error",
                    "reason": "UPDATE decided but no related memory",
                }

            related_id = decision.related_memory_ids[0]
            updated = await self.store.update(
                memory_id=related_id,
                updates={"content": {"text": statement}, "importance": decision.confidence},
            )

            return {
                "action": "updated",
                "memory_id": updated.memory_id if updated else related_id,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
            }

        elif decision.action == MemoryDecisionAction.MERGE:
            # Merge multiple memories
            if not decision.related_memory_ids:
                return {
                    "action": "error",
                    "reason": "MERGE decided but no related memories",
                }

            merged = await self._merge_memories(
                decision.related_memory_ids, statement, scope, scope_id
            )

            return {
                "action": "merged",
                "memory_id": merged.memory_id if merged else None,
                "merged_count": len(decision.related_memory_ids),
                "confidence": decision.confidence,
            }

        elif decision.action == MemoryDecisionAction.DELETE:
            # Delete related obsolete memories
            deleted_ids = []
            for mid in decision.related_memory_ids:
                if await self.store.forget(mid, reason="superseded_by_new_info"):
                    deleted_ids.append(mid)

            return {
                "action": "deleted",
                "deleted_ids": deleted_ids,
                "count": len(deleted_ids),
                "confidence": decision.confidence,
            }

        return {"action": "unknown", "confidence": 0.0}

    def _build_decision_prompt(
        self,
        statement: str,
        scope: str,
        existing_count: int,
        existing_samples: List[MemoryEntry],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build prompt for decision engine."""

        existing_text = ""
        if existing_samples:
            existing_text = "EXISTING MEMORIES:\n"
            for mem in existing_samples:
                existing_text += f"  - [{mem.memory_type}] {mem.title}\n"
                existing_text += f"    Content: {json.dumps(mem.content)[:100]}...\n"

        context_text = ""
        if context:
            context_text = f"CONTEXT: {json.dumps(context)}\n"

        prompt = f"""You are a Memory Decision Engine. Analyze this statement and decide how to handle it.

STATEMENT: "{statement}"
SCOPE: {scope}
EXISTING MEMORIES IN THIS SCOPE: {existing_count}
{existing_text}
{context_text}

Your task: Decide if and how to store this statement.

POSSIBLE DECISIONS:
1. IGNORE - Statement is trivial, subjective, or contains no actionable information
2. STORE - Statement is new, important, and worth remembering
3. UPDATE - Statement refines/updates an existing memory
4. MERGE - Statement is related to existing memories that should be consolidated
5. DELETE - Statement makes existing memories obsolete

RESPOND WITH VALID JSON (no markdown, just raw JSON):
{{
    "decision": "IGNORE" | "STORE" | "UPDATE" | "MERGE" | "DELETE",
    "confidence": <0-1>,
    "rationale": "<why this decision>",
    "related_memory_ids": [<ids if applicable>],
    "suggested_memory_type": "context" | "preference" | "practice" | "summary",
    "suggested_title": "<title if STORE>"
}}

RULES:
- IGNORE if the statement is greeting, filler, or lacks specific information
- STORE if the statement contains new, concrete, actionable information
- UPDATE if the statement clarifies or changes an existing memory
- MERGE if related memories would be stronger together
- DELETE if the statement makes other memories irrelevant

Be strict about what deserves to be remembered. Prefer IGNORE over STORE."""

        return prompt

    def _parse_decision_response(self, response: str) -> MemoryDecision:
        """Parse LLM response into MemoryDecision."""

        try:
            # Extract JSON from response
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            return MemoryDecision(
                action=MemoryDecisionAction(data.get("decision", "ignore").lower()),
                confidence=float(data.get("confidence", 0.5)),
                rationale=data.get("rationale", "No rationale provided"),
                related_memory_ids=data.get("related_memory_ids", []),
                suggested_memory_type=data.get("suggested_memory_type", MemoryType.CONTEXT),
                suggested_title=data.get("suggested_title"),
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse decision response: {e}")
            # Fallback
            return MemoryDecision(
                action=MemoryDecisionAction.STORE,
                confidence=0.3,
                rationale="Failed to parse decision, defaulting to store",
            )

    async def _merge_memories(
        self,
        memory_ids: List[str],
        new_statement: str,
        scope: str,
        scope_id: str,
    ) -> Optional[MemoryEntry]:
        """Merge multiple memories into one."""

        if not memory_ids:
            return None

        # Get memories to merge
        memories = []
        for mid in memory_ids:
            mem = await self.store.get(mid)
            if mem:
                memories.append(mem)

        if not memories:
            return None

        # Keep first, merge others
        primary = memories[0]
        merged_content = {"text": new_statement}

        # Merge content from others
        for mem in memories[1:]:
            if "text" in mem.content:
                merged_content["text"] += f" | {mem.content['text']}"

            # Merge other fields
            for key, value in mem.content.items():
                if key != "text" and key not in merged_content:
                    merged_content[key] = value

        # Update primary with merged content
        updated = await self.store.update(
            primary.memory_id,
            updates={
                "content": merged_content,
                "related_memories": primary.related_memories
                + [m.memory_id for m in memories[1:] if m.memory_id != primary.memory_id],
            },
        )

        # Delete merged memories
        for mem in memories[1:]:
            await self.store.forget(mem.memory_id, reason="merged")

        logger.info(f"Merged {len(memories)} memories into {primary.memory_id}")
        return updated

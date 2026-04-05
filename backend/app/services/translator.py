"""AI 번역 서비스 — PydanticAI + Gemini Flash (run_sync)"""

import logging
import os

from pydantic_ai import Agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "너는 한국의 피부관리실 원장님과 외국인 고객 사이의 통역사야. "
    "고객의 말을 한국어로 번역할 때 절대 다른 말(예: '번역해 드리겠습니다' 등)은 덧붙이지 말고 "
    "오직 번역된 결과물만 출력해. 전문 피부 미용 용어를 사용해."
)

_agent = None


def _get_agent() -> Agent:
    global _agent
    if _agent is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        # PydanticAI google provider는 GEMINI_API_KEY 환경변수를 자동 인식
        _agent = Agent(
            model="google-gla:gemini-2.0-flash",
            system_prompt=SYSTEM_PROMPT,
        )
    return _agent


def is_available() -> bool:
    """번역 서비스 사용 가능 여부 확인."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def translate_to_korean(text: str) -> str | None:
    """외국어 텍스트를 한국어로 번역. 실패 시 None 반환."""
    if not text or not text.strip():
        return None

    try:
        agent = _get_agent()
        result = agent.run_sync(text)
        translated = result.output.strip()
        if translated:
            return translated
        return None
    except Exception:
        logger.exception("Translation failed for text: %s", text[:100])
        return None

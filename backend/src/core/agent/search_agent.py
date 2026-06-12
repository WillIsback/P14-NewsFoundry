"""Définition de l'agent de chat principal NewsFoundry.

Configuration importante :
- `OpenAIChatCompletionsModel` cible `/v1/chat/completions` (vLLM ne supporte
  pas `/v1/responses` utilisé par défaut dans le SDK).
- Les instructions sont une **callable** pour injecter la date courante à chaque
  appel — évite que le LLM croie que des dates passées sont dans le futur.
- Le thinking mode (Qwen3) est désactivé via `extra_body` — incompatible avec
  les tool calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

from openai import AsyncOpenAI
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel

from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from core.agent.tools import get_top_news, search_news


def generate_instructions() -> str:
    """Génère les instructions de l'agent avec la date du jour.

    Appelable indépendamment pour stocker le prompt au moment de la création
    du chat — garantit la continuité des conversations d'un jour à l'autre.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "You are NewsFoundry, an AI assistant specialized in press review analysis. "
        "You are factual, concise, and always cite your sources.\n\n"
        f"Today's date is: {today}. Use this as reference for all time-related questions. "
        "Do not refuse requests about past dates — use the appropriate tool to fetch them.\n\n"
        "## Tool selection rules\n\n"
        "Use `get_top_news` when the user asks for:\n"
        "- General daily news ('quelles sont les actus du jour?', 'what's in the news?')\n"
        "- Top headlines for a country\n"
        "- News from a specific past date ('les actus du 4 mai 2026') — pass the date param\n\n"
        "Use `search_news` when the user asks for:\n"
        "- More details on a specific topic ('parle moi du conflit en Iran')\n"
        "- A deep dive into a subject mentioned in the conversation\n"
        "- Articles about a named person, event, or theme\n\n"
        "Always cite article titles and URLs in your response when you call a tool."
    )


def _build_instructions(ctx, agent) -> str:
    """Callable pour le SDK — délègue à generate_instructions()."""
    return generate_instructions()


_openai_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

chat_agent = Agent(
    name="newsfoundry_chat_agent",
    instructions=_build_instructions,
    tools=[get_top_news, search_news],
    model=OpenAIChatCompletionsModel(
        model=LLM_MODEL,
        openai_client=_openai_client,
    ),
    model_settings=ModelSettings(
        temperature=0.4,
        # Désactive le thinking mode (Qwen3) — incompatible avec les tool calls.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    ),
)

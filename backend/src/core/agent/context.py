from dataclasses import dataclass, field


@dataclass
class ChatRunContext:
    chat_id: int
    loaded_articles: list[dict] = field(default_factory=list)

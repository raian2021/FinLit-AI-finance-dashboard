"""
Switchable AI client.

Default: Claude Haiku 3.5 (~$0.25/1M input, $1.25/1M output — cheapest option)
Swap to: Claude Sonnet, GPT-4o-mini, GPT-4o via AI_PROVIDER + model env vars.

SECURITY: Only send aggregated summaries. Never raw transactions.
"""

from abc import ABC, abstractmethod
from app.core.config import settings


class AIClient(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> str:
        pass


class ClaudeClient(AIClient):
    def __init__(self):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def generate(self, system_prompt: str, user_message: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


class OpenAIClient(AIClient):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate(self, system_prompt: str, user_message: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content


def get_ai_client() -> AIClient:
    if settings.AI_PROVIDER == "openai":
        return OpenAIClient()
    return ClaudeClient()


# ── System prompts ──

FINANCIAL_EDUCATOR_PROMPT = """You are a financial education assistant for a UK-based personal finance app.
Your role is to explain financial concepts clearly and help users understand their spending patterns.

CRITICAL RULES:
- You provide EDUCATION, never ADVICE. You are not FCA-authorised.
- Never say "you should invest in X" or "put your money into Y".
- Use hypothetical framing: "If someone were to...", "Historically, X has..."
- Always note "past performance is not a guide to future performance" when discussing returns.
- Present multiple scenarios, not single recommendations.
- Use plain English. No jargon without explanation.
- Be warm, encouraging, non-judgmental about spending habits.
- Focus on building understanding, not prescribing actions.
- Never mention specific fund names or providers as recommendations.
- When discussing investment returns, always state your assumptions explicitly.

You receive AGGREGATED spending summaries (category totals, percentages, trends).
You NEVER receive raw transaction details, merchant names, or personal identifiers."""

"""Costruzione del provider AI scelto tramite configurazione."""

from app.ai.configuration import AIProvider, AISettings, load_ai_settings
from app.ai.contracts import AIModel, AIUnavailableError, ResponseModelT
from app.ai.gemini import GeminiAIModel
from app.ai.usage_limits import AIUsageLimiter, get_ai_usage_limiter


class DisabledAIModel:
    """Mantiene l'app avviabile quando l'integrazione AI è disattivata."""

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[ResponseModelT],
        system_instruction: str | None = None,
    ) -> ResponseModelT:
        del prompt, response_schema, system_instruction
        raise AIUnavailableError("Il modello AI non è configurato")


def build_ai_model(
    settings: AISettings | None = None,
    *,
    usage_limiter: AIUsageLimiter | None = None,
) -> AIModel:
    """Restituisce il provider configurato dietro il contratto comune."""

    configured = settings or load_ai_settings()
    if configured.provider is AIProvider.GEMINI:
        return GeminiAIModel(
            configured,
            usage_limiter=usage_limiter or get_ai_usage_limiter(),
        )
    return DisabledAIModel()

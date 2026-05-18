import logging
from dataclasses import dataclass

MODEL_FAST = "gemini-2.5-flash-lite"
MODEL_SMART = "gemini-3-flash-preview"

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ModelChoice:
    model_name: str
    reason: str
    text_length: int
    text_density: float


class ModelRouter:
    def __init__(
        self,
        *,
        high_text_len: int = 320,
        high_density: float = 0.38,
        ambiguous_density_low: float = 0.25,
        ambiguous_density_high: float = 0.38,
        ambiguous_text_len: int = 140,
    ) -> None:
        self.high_text_len = high_text_len
        self.high_density = high_density
        self.ambiguous_density_low = ambiguous_density_low
        self.ambiguous_density_high = ambiguous_density_high
        self.ambiguous_text_len = ambiguous_text_len

    def select_model(
        self,
        text: str | None,
        *,
        prefer_high_accuracy: bool = False,
    ) -> ModelChoice:
        cleaned = " ".join(text.split()) if text else ""
        if prefer_high_accuracy:
            choice = ModelChoice(
                model_name=MODEL_SMART,
                reason="prefer_high_accuracy",
                text_length=len(cleaned),
                text_density=self._text_density(cleaned) if cleaned else 0.0,
            )
        elif not cleaned:
            choice = ModelChoice(
                model_name=MODEL_SMART,
                reason="no_text",
                text_length=0,
                text_density=0.0,
            )
        else:
            density = self._text_density(cleaned)
            length = len(cleaned)

            if length >= self.high_text_len or density >= self.high_density:
                choice = ModelChoice(
                    model_name=MODEL_FAST,
                    reason="high_text_density",
                    text_length=length,
                    text_density=density,
                )
            elif density <= self.ambiguous_density_low or length < self.ambiguous_text_len:
                choice = ModelChoice(
                    model_name=MODEL_SMART,
                    reason="low_text_signal",
                    text_length=length,
                    text_density=density,
                )
            elif self.ambiguous_density_low < density < self.ambiguous_density_high:
                choice = ModelChoice(
                    model_name=MODEL_SMART,
                    reason="ambiguous_density",
                    text_length=length,
                    text_density=density,
                )
            else:
                choice = ModelChoice(
                    model_name=MODEL_FAST,
                    reason="default_fast",
                    text_length=length,
                    text_density=density,
                )

        logger.info(
            "model_choice",
            extra={
                "event": "model_choice",
                "model_name": choice.model_name,
                "reason": choice.reason,
                "text_length": choice.text_length,
                "text_density": round(choice.text_density, 3),
                "prefer_high_accuracy": prefer_high_accuracy,
            },
        )
        return choice

    @staticmethod
    def _text_density(text: str) -> float:
        alnum_count = sum(1 for ch in text if ch.isalnum())
        return alnum_count / max(len(text), 1)

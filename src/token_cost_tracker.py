"""Token usage and cost tracking for LLM calls."""

import json
import logging
from typing import Any, Dict, Optional


LOGGER = logging.getLogger("token_tracker")


# Pricing per million tokens (2024 rates - adjust as needed)
# Source: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
PRICING_MODELS = {
    # Azure OpenAI models
    "gpt-4o": {"input": 5.00, "output": 15.00},  # $/1M tokens
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-35-turbo": {"input": 0.50, "output": 1.50},
    "gpt-35-turbo-16k": {"input": 3.00, "output": 4.00},
    
    # Fallback for unknown models
    "default": {"input": 1.00, "output": 2.00},
}


class TokenUsageMetrics:
    """Encapsulates token and cost metrics from an LLM response."""
    
    def __init__(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "default",
        answer_length: Optional[int] = None,
        question_length: Optional[int] = None,
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.model = model
        self.answer_length = answer_length or 0
        self.question_length = question_length or 0
    
    def cost(self) -> Dict[str, float]:
        """Calculate cost in USD based on token usage."""
        pricing = PRICING_MODELS.get(self.model, PRICING_MODELS["default"])
        
        input_cost = (self.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.completion_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON response."""
        return {
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
                "total": self.total_tokens,
            },
            "cost": self.cost(),
            "efficiency": self._efficiency_metrics(),
            "model": self.model,
        }
    
    def _efficiency_metrics(self) -> Dict[str, Any]:
        """Calculate efficiency metrics: tokens per insight unit."""
        metrics = {}
        
        # Tokens per character of answer (lower is better)
        if self.answer_length > 0:
            metrics["tokens_per_answer_char"] = round(
                self.completion_tokens / self.answer_length, 3
            )
        
        # Tokens per character of question (lower = more efficient)
        if self.question_length > 0:
            metrics["answer_to_question_ratio"] = round(
                self.answer_length / self.question_length, 2
            )
        
        # Compression ratio: how much input was needed per output token
        if self.completion_tokens > 0:
            metrics["input_output_ratio"] = round(
                self.prompt_tokens / self.completion_tokens, 2
            )
        
        return metrics
    
    def to_log(self) -> str:
        """Format as structured log entry."""
        return json.dumps(
            {
                "event": "token_usage",
                "metrics": self.to_dict(),
            },
            default=str,
        )


def extract_token_usage(response: Any, model: str = "default") -> Optional[TokenUsageMetrics]:
    """
    Extract token usage from various LLM response types.
    
    Supports:
    - OpenAI ChatCompletion responses (with .usage)
    - Azure OpenAI responses (with .usage)
    - Foundry responses (with various payload shapes)
    """
    try:
        # Standard OpenAI / Azure OpenAI response with .usage object
        if hasattr(response, "usage"):
            usage = response.usage
            return TokenUsageMetrics(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                model=model,
            )
        
        # Fallback: try to extract from response dict
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return TokenUsageMetrics(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                model=model,
            )
        
        # No usage info available
        LOGGER.debug("No token usage info in response for model %s", model)
        return None
    except Exception as exc:
        LOGGER.warning("Failed to extract token usage: %s", exc)
        return None


def format_cost_human_readable(cost_usd: float) -> str:
    """Format cost in human-readable format (e.g., '0.000234 USD', '2.3 kilobuck')."""
    if cost_usd == 0:
        return "~$0"
    
    if cost_usd < 0.001:
        microusd = cost_usd * 1_000_000
        return f"{microusd:.1f}µ$"
    elif cost_usd < 1:
        millimsd = cost_usd * 1000
        return f"{millimsd:.2f}m$"
    else:
        return f"${cost_usd:.2f}"


def format_efficiency_grade(metrics: Dict[str, Any]) -> Dict[str, str]:
    """Grade efficiency on A-F scale based on metrics."""
    grades = {}
    
    # Grade based on tokens per answer character (lower is better)
    if "tokens_per_answer_char" in metrics:
        ratio = metrics["tokens_per_answer_char"]
        if ratio < 0.05:
            grades["efficiency"] = "A (excellent)"
        elif ratio < 0.10:
            grades["efficiency"] = "B (good)"
        elif ratio < 0.15:
            grades["efficiency"] = "C (fair)"
        elif ratio < 0.25:
            grades["efficiency"] = "D (poor)"
        else:
            grades["efficiency"] = "F (very poor)"
    
    # Grade based on input/output ratio (ideal ~1-2)
    if "input_output_ratio" in metrics:
        ratio = metrics["input_output_ratio"]
        if 1 <= ratio <= 2:
            grades["context_balance"] = "optimal"
        elif ratio < 1:
            grades["context_balance"] = "answer-heavy"
        else:
            grades["context_balance"] = "context-heavy"
    
    return grades

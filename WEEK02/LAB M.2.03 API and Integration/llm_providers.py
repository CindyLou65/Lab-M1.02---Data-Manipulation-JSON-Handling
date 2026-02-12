"""LLM provider integration with fallback support (OpenAI + Cohere)."""

import time
from typing import Any, Dict, Optional, Tuple

import cohere
import tiktoken
from openai import OpenAI

from config import Config

# Pricing (per million tokens) - best-effort estimates for lab cost tracking
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    # Cohere model used in Config; adjust if you switch models
    "command-r-plus-08-2024": {"input": 2.50, "output": 10.00},
}


class CostTracker:
    """Track API costs."""

    def __init__(self) -> None:
        self.total_cost: float = 0.0
        self.requests: list[dict] = []

    def track_request(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = PRICING.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        cost = input_cost + output_cost

        self.total_cost += cost
        self.requests.append(
            {
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
            }
        )
        return cost

    def get_summary(self) -> dict:
        total_input = sum(r["input_tokens"] for r in self.requests)
        total_output = sum(r["output_tokens"] for r in self.requests)
        return {
            "total_requests": len(self.requests),
            "total_cost": self.total_cost,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "average_cost": self.total_cost / max(len(self.requests), 1),
        }

    def check_budget(self, daily_budget: float) -> None:
        if self.total_cost >= daily_budget:
            raise Exception(
                f"Daily budget of ${daily_budget:.2f} exceeded! Current: ${self.total_cost:.2f}"
            )

        percent_used = (self.total_cost / daily_budget) * 100
        if percent_used >= 90:
            print(f"⚠️  Warning: {percent_used:.1f}% of daily budget used")


def count_tokens_openai(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens for OpenAI models using tiktoken (best effort)."""
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def rough_token_estimate(text: str) -> int:
    """Fallback estimate: ~4 characters per token."""
    return max(1, len(text) // 4)


def _safe_getattr(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


def extract_cohere_token_usage(res: Any) -> Tuple[Optional[int], Optional[int]]:
    """
    Cohere SDK versions differ in where usage/billing info is stored.
    We try multiple likely locations and field names, and return (input_tokens, output_tokens) or (None, None).
    """
    # Places where usage might exist (depending on SDK version)
    candidate_objs = []

    # e.g. res.meta.billed_units
    meta = _safe_getattr(res, "meta")
    if meta is not None:
        candidate_objs.append(_safe_getattr(meta, "billed_units"))
        candidate_objs.append(_safe_getattr(meta, "usage"))

    # e.g. res.billed_units / res.usage
    candidate_objs.append(_safe_getattr(res, "billed_units"))
    candidate_objs.append(_safe_getattr(res, "usage"))

    # Filter Nones
    candidate_objs = [c for c in candidate_objs if c is not None]

    # Field names we might see
    in_fields = ["input_tokens", "prompt_tokens", "input", "prompt"]
    out_fields = ["output_tokens", "completion_tokens", "output", "completion"]

    for obj in candidate_objs:
        input_tokens = None
        output_tokens = None

        for f in in_fields:
            v = _safe_getattr(obj, f)
            if isinstance(v, int):
                input_tokens = v
                break

        for f in out_fields:
            v = _safe_getattr(obj, f)
            if isinstance(v, int):
                output_tokens = v
                break

        if input_tokens is not None or output_tokens is not None:
            return input_tokens, output_tokens

    return None, None


class LLMProviders:
    """Manage OpenAI + Cohere with fallback."""

    def __init__(self) -> None:
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.cohere_client = cohere.ClientV2(api_key=Config.COHERE_API_KEY)

        self.cost_tracker = CostTracker()

        # Rate limiting
        self.openai_last_call = 0.0
        self.cohere_last_call = 0.0
        self.openai_interval = 60.0 / Config.OPENAI_RPM
        self.cohere_interval = 60.0 / Config.COHERE_RPM

    def _wait_openai(self) -> None:
        elapsed = time.time() - self.openai_last_call
        if elapsed < self.openai_interval:
            time.sleep(self.openai_interval - elapsed)
        self.openai_last_call = time.time()

    def _wait_cohere(self) -> None:
        elapsed = time.time() - self.cohere_last_call
        if elapsed < self.cohere_interval:
            time.sleep(self.cohere_interval - elapsed)
        self.cohere_last_call = time.time()

    def ask_openai(self, prompt: str, model: Optional[str] = None, max_tokens: int = 300) -> str:
        """Ask OpenAI."""
        if model is None:
            model = Config.OPENAI_MODEL

        self._wait_openai()

        # Estimate input tokens (in case usage is not returned)
        input_tokens_est = count_tokens_openai(prompt, model)

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

        output_text = response.choices[0].message.content or ""

        usage = getattr(response, "usage", None)
        if usage and getattr(usage, "prompt_tokens", None) is not None:
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens or 0
        else:
            input_tokens = input_tokens_est
            output_tokens = count_tokens_openai(output_text, model)

        self.cost_tracker.track_request("openai", model, input_tokens, output_tokens)
        self.cost_tracker.check_budget(Config.DAILY_BUDGET)

        return output_text

    def ask_cohere(self, prompt: str, model: Optional[str] = None, max_tokens: int = 300) -> str:
        """Ask Cohere via Chat API."""
        if model is None:
            model = Config.COHERE_MODEL

        self._wait_cohere()

        res = self.cohere_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

        # Cohere response text (typical shape): res.message.content[0].text
        # (If this ever errors, paste the response shape and we’ll adapt.)
        output_text = res.message.content[0].text

        # Token usage: try to extract; otherwise fall back to rough estimate
        input_tokens, output_tokens = extract_cohere_token_usage(res)

        if input_tokens is None:
            input_tokens = rough_token_estimate(prompt)
        if output_tokens is None:
            output_tokens = rough_token_estimate(output_text)

        self.cost_tracker.track_request("cohere", model, input_tokens, output_tokens)
        self.cost_tracker.check_budget(Config.DAILY_BUDGET)

        return output_text

    def ask_with_fallback(self, prompt: str, primary: str = "openai") -> Dict[str, str]:
        """
        Ask with fallback to the other provider.

        primary: "openai" or "cohere"
        Returns: {"provider": <provider_used>, "response": <text>}
        """
        try:
            if primary == "openai":
                print("Trying OpenAI (primary)...")
                response = self.ask_openai(prompt)
                return {"provider": "openai", "response": response}

            print("Trying Cohere (primary)...")
            response = self.ask_cohere(prompt)
            return {"provider": "cohere", "response": response}

        except Exception as e:
            print(f"✗ Primary provider failed: {e}")
            print("Falling back to secondary provider...")

            if primary == "openai":
                response = self.ask_cohere(prompt)
                return {"provider": "cohere", "response": response}

            response = self.ask_openai(prompt)
            return {"provider": "openai", "response": response}


# Test the module
if __name__ == "__main__":
    providers = LLMProviders()

    print("Testing OpenAI:")
    r1 = providers.ask_openai("What is Python? Answer in one sentence.")
    print(f"Response: {r1}\n")

    print("Testing Cohere:")
    r2 = providers.ask_cohere("What is Python? Answer in one sentence.")
    print(f"Response: {r2}\n")

    print("Testing fallback:")
    result = providers.ask_with_fallback("What is machine learning? Answer in one sentence.")
    print(f"Provider used: {result['provider']}")
    print(f"Response: {result['response']}\n")

    summary = providers.cost_tracker.get_summary()
    print(f"Total cost: ${summary['total_cost']:.4f}")
    print(f"Total requests: {summary['total_requests']}")

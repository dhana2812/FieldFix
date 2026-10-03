import os
import json
import time
import requests
from src.config import Config

class LLMClient:
    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or Config.LLM_PROVIDER
        self.model = model
        
        if self.provider == "openrouter":
            self.api_key = Config.OPENROUTER_API_KEY
            self.model = self.model or Config.OPENROUTER_MODEL
        elif self.provider == "openai":
            self.api_key = Config.OPENAI_API_KEY
            self.model = self.model or Config.OPENAI_MODEL
        elif self.provider == "gemini":
            self.api_key = Config.GEMINI_API_KEY
            self.model = self.model or Config.GEMINI_MODEL
        elif self.provider == "anthropic":
            self.api_key = Config.ANTHROPIC_API_KEY
            self.model = self.model or Config.ANTHROPIC_MODEL
        else:
            self.api_key = None

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> dict:
        """
        Sends a request to the configured LLM provider.
        """
        start_time = time.time()
        
        # 1. OpenRouter (OpenAI-compatible)
        if self.provider == "openrouter" and self.api_key:
            try:
                from openai import OpenAI
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                latency = (time.time() - start_time) * 1000
                choice = response.choices[0]
                usage = response.usage
                return {
                    "text": choice.message.content.strip(),
                    "prompt_tokens": usage.prompt_tokens if usage else len(system_prompt + user_prompt) // 4,
                    "completion_tokens": usage.completion_tokens if usage else len(choice.message.content) // 4,
                    "total_tokens": usage.total_tokens if usage else (len(system_prompt + user_prompt + choice.message.content) // 4),
                    "latency_ms": round(latency, 2),
                    "model": self.model,
                    "provider": "openrouter"
                }
            except Exception as e:
                return self._error_or_fallback(f"OpenRouter API error: {str(e)}", system_prompt, user_prompt, start_time)

        # 2. OpenAI
        if self.provider == "openai" and self.api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                latency = (time.time() - start_time) * 1000
                choice = response.choices[0]
                usage = response.usage
                return {
                    "text": choice.message.content.strip(),
                    "prompt_tokens": usage.prompt_tokens if usage else len(system_prompt + user_prompt) // 4,
                    "completion_tokens": usage.completion_tokens if usage else len(choice.message.content) // 4,
                    "total_tokens": usage.total_tokens if usage else (len(system_prompt + user_prompt + choice.message.content) // 4),
                    "latency_ms": round(latency, 2),
                    "model": self.model,
                    "provider": "openai"
                }
            except Exception as e:
                return self._error_or_fallback(f"OpenAI API error: {str(e)}", system_prompt, user_prompt, start_time)

        # 2. Google Gemini REST API
        elif self.provider == "gemini" and self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {"temperature": temperature}
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                latency = (time.time() - start_time) * 1000
                usage = data.get("usageMetadata", {})
                prompt_toks = usage.get("promptTokenCount", len(system_prompt + user_prompt) // 4)
                comp_toks = usage.get("candidatesTokenCount", len(text) // 4)
                return {
                    "text": text,
                    "prompt_tokens": prompt_toks,
                    "completion_tokens": comp_toks,
                    "total_tokens": prompt_toks + comp_toks,
                    "latency_ms": round(latency, 2),
                    "model": self.model,
                    "provider": "gemini"
                }
            except Exception as e:
                return self._error_or_fallback(f"Gemini API error: {str(e)}", system_prompt, user_prompt, start_time)

        # 3. Anthropic REST API
        elif self.provider == "anthropic" and self.api_key:
            try:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "temperature": temperature
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                data = res.json()
                text = data["content"][0]["text"].strip()
                latency = (time.time() - start_time) * 1000
                usage = data.get("usage", {})
                prompt_toks = usage.get("input_tokens", len(system_prompt + user_prompt) // 4)
                comp_toks = usage.get("output_tokens", len(text) // 4)
                return {
                    "text": text,
                    "prompt_tokens": prompt_toks,
                    "completion_tokens": comp_toks,
                    "total_tokens": prompt_toks + comp_toks,
                    "latency_ms": round(latency, 2),
                    "model": self.model,
                    "provider": "anthropic"
                }
            except Exception as e:
                return self._error_or_fallback(f"Anthropic API error: {str(e)}", system_prompt, user_prompt, start_time)

        # 4. Fallback / Baseline simulation mode when no API keys are configured
        else:
            return self._baseline_zero_context_response(user_prompt, start_time)

    def _baseline_zero_context_response(self, user_prompt: str, start_time: float) -> dict:
        """
        Simulates standard un-grounded generic LLM behavior without private Amperia documents.
        Demonstrates the exact hallucination / guessing pattern of general LLMs when un-augmented.
        """
        prompt_lower = user_prompt.lower()
        if "e-217" in prompt_lower or ("pune" in prompt_lower and "firmware" in prompt_lower):
            text = (
                "Based on standard EV fast charger telemetry, an E-217 error code typically indicates "
                "an unexpected DC output contactor feedback mismatch or high voltage isolation warning. "
                "Since you recently performed a firmware update, it could potentially be either a controller "
                "communication glitch or a hardware contactor weld fault. As a general troubleshooting step, "
                "I recommend power cycling the cabinet for 5 minutes, checking the 24V auxiliary power rail, "
                "and replacing the secondary contactor assembly if the error persists. (Note: Specific Amperia "
                "service history and patch release records are not available)."
            )
        elif "warranty" in prompt_lower or "power module" in prompt_lower or "cable" in prompt_lower:
            text = (
                "Standard commercial EV charger warranties generally cover core power electronics for "
                "approximately 2 to 3 years, while high-wear components like charging cables and connectors "
                "usually carry a 1-year limited warranty. Please check your specific Amperia vendor contract "
                "and SLA terms for exact coverage durations."
            )
        elif "insulation" in prompt_lower or "dc150-03" in prompt_lower or "inspection" in prompt_lower:
            text = (
                "For DC fast charging stations, insulation resistance readings should typically exceed 100 Megaohms "
                "at 1000V DC according to standard IEC 61851 safety guidelines. However, specific recorded field "
                "values and physical test sheets for Charger Unit DC150-03 at the Pune Expressway site are not "
                "present in my general training data."
            )
        else:
            text = (
                "I am FieldFix, your assistant for Amperia charging networks. Without direct access to Amperia's "
                "private manuals, firmware logs, or site inspection database, I can only provide general EVSE "
                "troubleshooting recommendations."
            )
            
        latency = (time.time() - start_time) * 1000
        prompt_tokens = (len(user_prompt) + 50) // 4
        completion_tokens = len(text) // 4
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": round(latency + 150, 2),
            "model": "baseline-generic-llm (no-context)",
            "provider": "simulated/generic"
        }

    def _error_or_fallback(self, err_msg: str, system_prompt: str, user_prompt: str, start_time: float) -> dict:
        print(f"[Warning] {err_msg}. Falling back to baseline simulation.")
        return self._baseline_zero_context_response(user_prompt, start_time)

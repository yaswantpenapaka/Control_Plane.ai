import logging
from typing import Optional, Dict, Any
from groq import Groq
from config.settings import Settings
from .schemas import ChatRequest, ChatResponse, ToolCall

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        self.is_initialized = False

        if settings.is_live_mode:
            valid, msg = settings.validate_for_live_mode()
            if not valid:
                logger.warning(f"Live mode validation failed: {msg}")
                return

            try:
                self.client = Groq(api_key=settings.groq_api_key)
                self.is_initialized = True
                logger.info(f"Groq client initialized with model: {settings.groq_model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.info(f"Groq client in {settings.controlplane_mode.upper()} mode - not connecting to Groq")
            self.is_initialized = True

    def chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[list[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> tuple[Optional[ChatResponse], Dict[str, int], float]:
        if not self.is_initialized or (self.settings.is_live_mode and not self.client):
            return None, {}, 0.0

        try:
            kwargs = {
                "model": self.settings.groq_model,
                "messages": messages,
                "temperature": temperature,
            }

            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

            response = self.client.chat.completions.create(**kwargs)

            tokens_used = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            message = response.choices[0].message

            chat_response = ChatResponse(
                content=message.content,
                tool_call=None,
                role="assistant",
            )

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                chat_response.tool_call = ToolCall(
                    name=tool_call.function.name,
                    arguments=eval(tool_call.function.arguments),
                )

            estimated_cost = self._estimate_cost(tokens_used)

            return chat_response, tokens_used, estimated_cost

        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return None, {}, 0.0

    def structured_output(
        self,
        messages: list[Dict[str, str]],
        response_format: Dict[str, Any],
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        if not self.is_initialized or (self.settings.is_live_mode and not self.client):
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )

            import json

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Structured output call failed: {e}")
            return None

    def _estimate_cost(self, tokens_used: Dict[str, int]) -> float:
        input_price_per_1k = 0.05 / 1000
        output_price_per_1k = 0.15 / 1000

        input_cost = tokens_used.get("input_tokens", 0) * input_price_per_1k
        output_cost = tokens_used.get("output_tokens", 0) * output_price_per_1k

        return input_cost + output_cost

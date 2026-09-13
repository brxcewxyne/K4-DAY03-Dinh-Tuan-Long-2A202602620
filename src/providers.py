"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        student_match = re.search(r"\bSV\d+\b", prompt, re.IGNORECASE)
        student_id = student_match.group(0).upper() if student_match else "SV2026001"
        datetime_match = re.search(r"(\d{1,2}:\d{2})(?:\s+ngày)?\s+(\d{2}/\d{2}/\d{4})", prompt, re.IGNORECASE)
        datetime_str = (
            f"{datetime_match.group(1)} {datetime_match.group(2)}"
            if datetime_match else "14:00 15/09/2026"
        )
        has_history = "lịch sử tool call và observation" in prompt_lower
        booking_requested = "đặt lịch" in prompt_lower

        # Khi đã có kết quả đặt lịch, Mock trả Final Answer.
        if has_history and '"booking_id"' in prompt:
            messages = re.findall(r'"message":\s*"([^"]+)"', prompt)
            return {
                "type": "text",
                "content": messages[-1] if messages else "Đặt lịch tư vấn học vụ thành công.",
                "thought": "Observation xác nhận lịch đã được đặt nên có thể kết thúc."
            }

        # Khi tra cứu không tìm thấy sinh viên, Mock không bịa dữ liệu.
        if has_history and '"status": "NOT_FOUND"' in prompt:
            return {
                "type": "text",
                "content": f"Không tìm thấy dữ liệu sinh viên có mã {student_id}.",
                "thought": "Observation trả về NOT_FOUND nên dừng và thông báo chính xác."
            }

        # Tác vụ nhiều bước: dùng advisor từ Observation để đặt lịch.
        if has_history and booking_requested and '"advisor"' in prompt:
            advisor_matches = re.findall(r'"advisor":\s*"([^"]+)"', prompt)
            advisor_name = advisor_matches[-1] if advisor_matches else "PGS.TS Nguyễn Văn A"
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {
                    "student_id": student_id,
                    "datetime_str": datetime_str,
                    "advisor_name": advisor_name
                },
                "thought": "Đã có tên cố vấn từ Observation; tiếp tục gọi schedule_appointment."
            }

        # Sau một tra cứu đơn, Mock tổng hợp câu trả lời.
        if has_history and '"data"' in prompt:
            return {
                "type": "text",
                "content": "Đã tra cứu thành công thông tin học vụ của sinh viên từ MCP Server.",
                "thought": "Observation đã đủ để hoàn thành yêu cầu tra cứu."
            }

        # Yêu cầu đặt lịch trực tiếp, đã có đủ thông tin.
        if booking_requested and "tra cứu" not in prompt_lower:
            advisor_name = "TS. Lê Thị B" if student_id == "SV2026002" else "PGS.TS Nguyễn Văn A"
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {
                    "student_id": student_id,
                    "datetime_str": datetime_str,
                    "advisor_name": advisor_name
                },
                "thought": f"Yêu cầu đã có đủ thông tin để đặt lịch cho {student_id}."
            }

        if student_match or "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu thông tin học vụ của {student_id}."
            }

        return {
            "type": "text",
            "content": "[Mock Agent Response]: Đây là câu hỏi chung về quy chế học vụ VinUni.",
            "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return {
                "type": "error",
                "content": "Chưa cấu hình GEMINI_API_KEY hợp lệ.",
                "thought": "Không thể gọi Gemini API thật do thiếu API key."
            }
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            return {
                "type": "error",
                "content": str(e),
                "thought": "Gemini API thật trả về lỗi; không fallback sang Mock để bảo toàn tính xác thực của trace."
            }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return {
                "type": "error",
                "content": "Chưa cấu hình OPENAI_API_KEY hợp lệ.",
                "thought": "Không thể gọi OpenAI API thật do thiếu API key."
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            return {
                "type": "error",
                "content": str(e),
                "thought": "OpenAI API thật trả về lỗi; không fallback sang Mock để bảo toàn tính xác thực của trace."
            }


def get_llm_provider(provider_type: str = None) -> BaseLLMProvider:
    """Khởi tạo Provider được chỉ định hoặc đọc lựa chọn từ biến môi trường."""
    provider_type = (provider_type or os.getenv("LLM_PROVIDER", "gemini")).lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()


PROVIDER_HIERARCHY = [
    {
        "id": "gemini",
        "display_name": "Gemini",
        "default_model": "gemini-3.5-flash-lite",
        "cost_tier": 1,
        "capability_tier": 1
    },
    {
        "id": "openai",
        "display_name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "cost_tier": 2,
        "capability_tier": 2
    }
]

COMPLEXITY_START_TIER = {
    "low": 0,
    "medium": 0,
    "high": 1
}


class ProviderStatusTracker:
    """Theo dõi trạng thái API trong suốt một lần chạy chương trình."""
    def __init__(self):
        self._statuses: Dict[str, Dict[str, Any]] = {}

    def register(self, provider_id: str, provider: BaseLLMProvider):
        api_key = getattr(provider, "api_key", None)
        configured = bool(api_key and not str(api_key).startswith("your_"))
        current = self._statuses.setdefault(provider_id, {
            "provider": provider.__class__.__name__,
            "model": getattr(provider, "model_name", "unknown-model"),
            "configured": configured,
            "state": "NOT_TESTED" if configured else "UNCONFIGURED",
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "last_error": None
        })
        current["model"] = getattr(provider, "model_name", current["model"])
        current["configured"] = configured
        if not configured:
            current["state"] = "UNCONFIGURED"

    def record_attempt(self, provider_id: str):
        self._statuses[provider_id]["attempts"] += 1

    def record_success(self, provider_id: str):
        status = self._statuses[provider_id]
        status["successes"] += 1
        status["state"] = "HEALTHY"
        status["last_error"] = None

    def record_failure(self, provider_id: str, error: str):
        status = self._statuses[provider_id]
        status["failures"] += 1
        status["state"] = "ERROR" if status["configured"] else "UNCONFIGURED"
        status["last_error"] = error

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            provider_id: dict(status)
            for provider_id, status in self._statuses.items()
        }


API_PROVIDER_STATUS = ProviderStatusTracker()


def _create_live_provider(provider_id: str) -> BaseLLMProvider:
    """Tạo provider thật; việc thiếu key sẽ được router ghi nhận là lỗi cấu hình."""
    if provider_id == "gemini":
        return GeminiProvider()
    if provider_id == "openai":
        return OpenAIProvider()
    raise ValueError(f"Provider chưa được hỗ trợ: {provider_id}")


def _build_fallback_order(start_index: int) -> List[int]:
    """
    Tạo thứ tự fallback theo từng bậc gần nhất.
    Ưu tiên bậc rẻ hơn liền kề trước khi thử bậc mạnh/đắt hơn tiếp theo.
    """
    order = [start_index]
    distance = 1
    while len(order) < len(PROVIDER_HIERARCHY):
        lower_index = start_index - distance
        upper_index = start_index + distance
        if lower_index >= 0:
            order.append(lower_index)
        if upper_index < len(PROVIDER_HIERARCHY):
            order.append(upper_index)
        distance += 1
    return order


class HierarchicalLLMProvider(BaseLLMProvider):
    """Provider tổng hợp có theo dõi trạng thái và fallback theo hierarchy."""
    def __init__(self, complexity: str):
        normalized_complexity = complexity.strip().lower()
        start_index = COMPLEXITY_START_TIER.get(normalized_complexity, 0)
        self.complexity = normalized_complexity
        self.route = []
        self.providers = []
        self.failed_provider_ids = set()
        self.active_provider_name = "none"
        self.model_name = "none"

        for index in _build_fallback_order(start_index):
            spec = PROVIDER_HIERARCHY[index]
            provider = _create_live_provider(spec["id"])
            API_PROVIDER_STATUS.register(spec["id"], provider)
            self.route.append(spec)
            self.providers.append((spec, provider))

    def route_description(self) -> str:
        route_names = [
            f"{spec['display_name']} ({provider.model_name})"
            for spec, provider in self.providers
        ]
        return " → ".join(route_names)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        errors = []
        for spec, provider in self.providers:
            if spec["id"] in self.failed_provider_ids:
                continue
            API_PROVIDER_STATUS.record_attempt(spec["id"])
            response = provider.generate(prompt, system_prompt)
            if " Exception]:" not in response and " Error]:" not in response:
                API_PROVIDER_STATUS.record_success(spec["id"])
                self.active_provider_name = provider.__class__.__name__
                self.model_name = provider.model_name
                return response
            API_PROVIDER_STATUS.record_failure(spec["id"], response)
            self.failed_provider_ids.add(spec["id"])
            errors.append(f"{spec['display_name']}: {response}")
        return " | ".join(errors)

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        attempts = []
        errors = []

        for spec, provider in self.providers:
            provider_id = spec["id"]
            if provider_id in self.failed_provider_ids:
                attempts.append({
                    "provider": provider.__class__.__name__,
                    "model": provider.model_name,
                    "result": "SKIPPED_UNHEALTHY"
                })
                continue

            API_PROVIDER_STATUS.record_attempt(provider_id)
            result = provider.generate_with_tools(prompt, tools_schema, system_prompt)
            attempts.append({
                "provider": provider.__class__.__name__,
                "model": provider.model_name,
                "result": "ERROR" if result.get("type") == "error" else "SUCCESS"
            })

            if result.get("type") != "error":
                API_PROVIDER_STATUS.record_success(provider_id)
                self.active_provider_name = provider.__class__.__name__
                self.model_name = provider.model_name
                result["_provider"] = self.active_provider_name
                result["_model"] = self.model_name
                result["_fallback_path"] = attempts
                result["_provider_status"] = API_PROVIDER_STATUS.snapshot()
                return result

            error_message = result.get("content", "Lỗi provider không xác định.")
            API_PROVIDER_STATUS.record_failure(provider_id, error_message)
            self.failed_provider_ids.add(provider_id)
            errors.append(f"{spec['display_name']}: {error_message}")

        return {
            "type": "error",
            "content": "Tất cả API Provider trong hierarchy đều thất bại. " + " | ".join(errors),
            "thought": "Không còn provider khả dụng để tiếp tục ReAct Loop.",
            "_provider": "none",
            "_model": "none",
            "_fallback_path": attempts,
            "_provider_status": API_PROVIDER_STATUS.snapshot()
        }


def get_provider_for_complexity(complexity: str) -> BaseLLMProvider:
    """
    Định tuyến tác vụ theo độ khó:
    - Low/Medium: Gemini Flash để tiết kiệm chi phí.
    - High: OpenAI GPT-4o-mini cho suy luận nhiều bước.
    """
    return HierarchicalLLMProvider(complexity)


def format_provider_status() -> str:
    """Tạo báo cáo trạng thái API ngắn gọn để in ra terminal."""
    statuses = API_PROVIDER_STATUS.snapshot()
    if not statuses:
        return "Chưa có API Provider nào được khởi tạo."

    lines = ["📡 [API PROVIDER STATUS]"]
    for provider_id, status in statuses.items():
        lines.append(
            f"  - {provider_id}: {status['state']} | model={status['model']} | "
            f"attempts={status['attempts']} | successes={status['successes']} | "
            f"failures={status['failures']}"
        )
        if status["last_error"]:
            lines.append(f"    last_error={status['last_error']}")
    return "\n".join(lines)

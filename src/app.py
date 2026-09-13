"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_provider_for_complexity, format_provider_status

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def build_react_prompt(user_query: str, interaction_history: list) -> str:
    """Ghép yêu cầu gốc và các Observation để LLM quyết định bước tiếp theo."""
    if not interaction_history:
        return user_query

    history_json = json.dumps(interaction_history, ensure_ascii=False, indent=2)
    return f"""
YÊU CẦU GỐC:
{user_query}

LỊCH SỬ TOOL CALL VÀ OBSERVATION:
{history_json}

Hãy tiếp tục hoàn thành YÊU CẦU GỐC dựa trên lịch sử trên.
- Không gọi lại cùng một công cụ với cùng tham số.
- Nếu còn hành động chưa hoàn thành, hãy gọi công cụ tiếp theo.
- Nếu mục tiêu đã hoàn thành hoặc Observation báo lỗi/NOT_FOUND, hãy trả lời kết luận bằng văn bản.
""".strip()


def infer_query_complexity(user_query: str) -> str:
    """Nhận diện nhanh yêu cầu nhiều bước trong chế độ interactive."""
    query = user_query.lower()
    multi_step_markers = ["sau đó", "tiếp theo", "rồi đặt", "tra cứu và đặt"]
    if any(marker in query for marker in multi_step_markers):
        return "High"
    if "tra cứu" in query and "đặt lịch" in query:
        return "High"
    return "Medium"


def describe_provider(provider) -> str:
    """Tên provider và model để hiển thị và ghi trace."""
    if hasattr(provider, "route_description"):
        return provider.route_description()
    model_name = getattr(provider, "model_name", "unknown-model")
    return f"{provider.__class__.__name__} ({model_name})"


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    interaction_history = []
    executed_calls = set()
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Sau mỗi Tool Call, prompt mới chứa toàn bộ Observation để LLM tiếp tục suy luận.
        react_prompt = build_react_prompt(user_query, interaction_history)
        llm_response = provider.generate_with_tools(
            react_prompt,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )

        provider_name = llm_response.get(
            "_provider",
            getattr(provider, "active_provider_name", provider.__class__.__name__)
        )
        model_name = llm_response.get(
            "_model",
            getattr(provider, "model_name", "unknown-model")
        )
        fallback_path = llm_response.get("_fallback_path", [])
        provider_status = llm_response.get("_provider_status", {})

        print(f"☁️ [API ACTIVE]: {provider_name} ({model_name})")
        if len(fallback_path) > 1:
            route_used = " → ".join(
                f"{attempt['provider']}[{attempt['result']}]"
                for attempt in fallback_path
            )
            print(f"🪜 [PROVIDER FALLBACK]: {route_used}")
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            latency_ms = round((time.time() - step_start_time) * 1000, 2)
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "provider": provider_name,
                "model": model_name,
                "fallback_path": fallback_path,
                "api_provider_status": provider_status,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            call_signature = json.dumps(
                {"tool_name": tool_name, "arguments": arguments},
                ensure_ascii=False,
                sort_keys=True
            )
            if call_signature in executed_calls:
                latency_ms = round((time.time() - step_start_time) * 1000, 2)
                duplicate_observation = {
                    "status": "DUPLICATE_TOOL_CALL",
                    "message": "Công cụ này đã được gọi với cùng tham số. Hãy dùng Observation cũ để kết luận."
                }
                interaction_history.append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": duplicate_observation
                })
                print(f"🛡️ [Loop Guard]: Đã chặn Tool Call trùng lặp.")
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "LOOP_GUARD",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": duplicate_observation,
                    "provider": provider_name,
                    "model": model_name,
                    "fallback_path": fallback_path,
                    "api_provider_status": provider_status,
                    "latency_ms": latency_ms
                })
                continue

            executed_calls.add(call_signature)
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            latency_ms = round((time.time() - step_start_time) * 1000, 2)
            
            obs_str = json.dumps(obs_data, ensure_ascii=False)
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "provider": provider_name,
                "model": model_name,
                "fallback_path": fallback_path,
                "api_provider_status": provider_status,
                "latency_ms": latency_ms
            })
            
            interaction_history.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data
            })

            # Không dừng ở đây: Observation được đưa lại cho LLM ở vòng kế tiếp.
            continue

        elif llm_response.get("type") == "error":
            latency_ms = round((time.time() - step_start_time) * 1000, 2)
            error_message = llm_response.get("content", "LLM Provider trả về lỗi không xác định.")
            print(f"❌ [Agent Error]: {error_message}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "ERROR",
                "output": error_message,
                "provider": provider_name,
                "model": model_name,
                "fallback_path": fallback_path,
                "api_provider_status": provider_status,
                "latency_ms": latency_ms
            })
            break

        else:
            latency_ms = round((time.time() - step_start_time) * 1000, 2)
            error_message = f"LLM trả về kiểu phản hồi không hợp lệ: {llm_response.get('type')}"
            print(f"❌ [Agent Error]: {error_message}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "ERROR",
                "output": error_message,
                "provider": provider_name,
                "model": model_name,
                "fallback_path": fallback_path,
                "api_provider_status": provider_status,
                "latency_ms": latency_ms
            })
            break
    else:
        timeout_message = f"Agent đã dừng sau {MAX_ITERATIONS} bước để tránh vòng lặp vô hạn."
        print(f"⚠️ [Max Iterations]: {timeout_message}")
        trace_logs.append({
            "step": MAX_ITERATIONS,
            "query": user_query,
            "action_type": "MAX_ITERATIONS_REACHED",
            "output": timeout_message,
            "provider": getattr(provider, "active_provider_name", "none"),
            "model": getattr(provider, "model_name", "none"),
            "latency_ms": 0.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    mcp_server = MCPAcademicServer()
    
    print("🔀 LLM Routing: Low/Medium → Gemini | High → OpenAI GPT-4o-mini")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                complexity = infer_query_complexity(user_input)
                provider = get_provider_for_complexity(complexity)
                print(f"🔌 [MODEL ROUTING]: {complexity} → {describe_provider(provider)}")
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
                print(format_provider_status())
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                provider = get_provider_for_complexity(tc.get("complexity", "Medium"))
                print(f"🔌 [MODEL ROUTING]: {tc.get('complexity', 'Medium')} → {describe_provider(provider)}")
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(format_provider_status())
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        provider = get_provider_for_complexity(tests[1].get("complexity", "Medium"))
        print(f"🔌 [MODEL ROUTING]: {tests[1].get('complexity', 'Medium')} → {describe_provider(provider)}")
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print(format_provider_status())
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")

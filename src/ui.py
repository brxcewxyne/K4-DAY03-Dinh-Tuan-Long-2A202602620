"""
Giao diện Streamlit tối giản cho VinUni Academic ReAct Agent.

Chạy từ thư mục gốc:
    streamlit run src/ui.py
"""

import json
import sys
from pathlib import Path

import streamlit as st

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import infer_query_complexity, run_react_agent, save_waterfall_trace
from mcp_server import MCPAcademicServer
from providers import get_provider_for_complexity, get_provider_status

TRACE_PATH = SRC_DIR.parent / "docs" / "trace_waterfall.json"


st.set_page_config(
    page_title="VinUni Academic Agent",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --vin-red: #c8102e;
        --vin-red-dark: #8f0b22;
        --vin-red-soft: #fff1f3;
        --ink: #231f20;
        --muted: #6b6466;
        --line: #ecd8dc;
    }

    .stApp {
        background:
            radial-gradient(circle at 90% 0%, #ffe5e9 0, transparent 26rem),
            #fffafa;
        color: var(--ink);
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }

    .hero {
        padding: 1.6rem 1.7rem;
        border-radius: 22px;
        color: white;
        background: linear-gradient(135deg, var(--vin-red-dark), var(--vin-red));
        box-shadow: 0 14px 34px rgba(143, 11, 34, 0.18);
        margin-bottom: 1.1rem;
    }

    .hero-kicker {
        margin: 0 0 .45rem 0;
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        opacity: .82;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(1.8rem, 5vw, 2.65rem);
        line-height: 1.05;
        color: white;
    }

    .hero p {
        margin: .75rem 0 0;
        max-width: 42rem;
        line-height: 1.55;
        opacity: .9;
    }

    .flow {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: .65rem;
        margin: 1rem 0 1.25rem;
    }

    .flow-step {
        background: white;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: .85rem;
        min-height: 92px;
    }

    .flow-number {
        display: inline-grid;
        place-items: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: var(--vin-red-soft);
        color: var(--vin-red);
        font-weight: 800;
    }

    .flow-title {
        display: block;
        margin-top: .5rem;
        font-weight: 750;
        color: var(--ink);
    }

    .flow-copy {
        display: block;
        margin-top: .2rem;
        color: var(--muted);
        font-size: .82rem;
        line-height: 1.35;
    }

    [data-testid="stChatMessage"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: .35rem .55rem;
        box-shadow: 0 5px 18px rgba(70, 15, 25, .04);
    }

    .provider-pill {
        display: inline-block;
        padding: .25rem .58rem;
        margin: .2rem .3rem .2rem 0;
        border-radius: 999px;
        color: var(--vin-red-dark);
        background: var(--vin-red-soft);
        border: 1px solid #f1c3cc;
        font-size: .76rem;
        font-weight: 700;
    }

    .api-card {
        padding: .8rem .85rem;
        margin: .55rem 0;
        background: white;
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 5px 15px rgba(70, 15, 25, .04);
    }

    .api-card-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: .5rem;
    }

    .api-name {
        color: var(--ink);
        font-weight: 800;
    }

    .api-model {
        display: block;
        margin-top: .18rem;
        color: var(--muted);
        font-size: .74rem;
    }

    .api-state {
        padding: .18rem .46rem;
        border-radius: 999px;
        font-size: .67rem;
        font-weight: 850;
        letter-spacing: .04em;
    }

    .state-healthy { color: #166534; background: #dcfce7; }
    .state-error { color: #991b1b; background: #fee2e2; }
    .state-unconfigured { color: #92400e; background: #fef3c7; }
    .state-not-tested { color: #475569; background: #f1f5f9; }

    .api-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: .35rem;
        margin-top: .65rem;
        color: var(--muted);
        font-size: .7rem;
    }

    .api-stats strong {
        display: block;
        color: var(--ink);
        font-size: .88rem;
    }

    .trace-panel {
        padding: .75rem .9rem;
        margin: .8rem 0;
        border-left: 4px solid var(--vin-red);
        border-radius: 4px 12px 12px 4px;
        background: white;
        color: var(--muted);
        font-size: .84rem;
    }

    .stButton > button,
    [data-testid="stChatInput"] button {
        border-color: var(--vin-red) !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--vin-red);
        color: white;
    }

    @media (max-width: 640px) {
        .flow { grid-template-columns: 1fr; }
        .flow-step { min-height: auto; }
        .hero { padding: 1.3rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def resolve_complexity(query: str, routing_mode: str) -> str:
    if routing_mode == "Tác vụ nhiều bước":
        return "High"
    if routing_mode == "Tác vụ đơn giản":
        return "Medium"
    return infer_query_complexity(query)


def get_final_answer(trace: list) -> str:
    for event in reversed(trace):
        if event.get("action_type") == "FINAL_ANSWER":
            return event.get("output", "")
    for event in reversed(trace):
        if event.get("action_type") in {"ERROR", "MAX_ITERATIONS_REACHED"}:
            return event.get("output", "Không thể hoàn thành yêu cầu.")
    return "Không nhận được câu trả lời cuối cùng."


def provider_badges(trace: list) -> str:
    providers = []
    for event in trace:
        label = f"{event.get('provider', 'Unknown')} · {event.get('model', 'unknown-model')}"
        if label not in providers:
            providers.append(label)
    return "".join(f'<span class="provider-pill">{label}</span>' for label in providers)


def render_provider_status():
    statuses = get_provider_status()
    defaults = {
        "gemini": {
            "provider": "Gemini",
            "model": "gemini-3.5-flash-lite",
            "state": "NOT_TESTED",
            "attempts": 0,
            "successes": 0,
            "failures": 0,
        },
        "openai": {
            "provider": "OpenAI",
            "model": "gpt-4o-mini",
            "state": "NOT_TESTED",
            "attempts": 0,
            "successes": 0,
            "failures": 0,
        },
    }

    for provider_id, default in defaults.items():
        status = statuses.get(provider_id, default)
        state = status.get("state", "NOT_TESTED")
        state_class = state.lower().replace("_", "-")
        st.markdown(
            f"""
            <div class="api-card">
                <div class="api-card-top">
                    <div>
                        <span class="api-name">{default['provider']}</span>
                        <span class="api-model">{status.get('model', default['model'])}</span>
                    </div>
                    <span class="api-state state-{state_class}">{state}</span>
                </div>
                <div class="api-stats">
                    <span><strong>{status.get('attempts', 0)}</strong>Lượt gọi</span>
                    <span><strong>{status.get('successes', 0)}</strong>Thành công</span>
                    <span><strong>{status.get('failures', 0)}</strong>Thất bại</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if status.get("last_error"):
            st.caption(f"Lỗi gần nhất: {status['last_error']}")


def load_saved_trace() -> list:
    if not TRACE_PATH.exists():
        return []
    try:
        with TRACE_PATH.open("r", encoding="utf-8") as trace_file:
            return json.load(trace_file)
    except (OSError, json.JSONDecodeError):
        return []


if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.markdown("### 🎓 Academic Agent")
    st.caption("Trợ lý học vụ sử dụng ReAct, MCP và định tuyến nhiều LLM.")

    routing_mode = st.radio(
        "Chế độ định tuyến",
        ["Tự động", "Tác vụ đơn giản", "Tác vụ nhiều bước"],
        help="Tự động dùng Gemini cho yêu cầu đơn giản và OpenAI cho yêu cầu nhiều bước.",
    )

    st.markdown("#### Model hierarchy")
    st.markdown("🔴 **Tier 1:** Gemini Flash-Lite")
    st.markdown("⚪ **Tier 2:** OpenAI GPT-4o-mini")

    if st.button("Xóa hội thoại", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.markdown("#### Trạng thái API")
    render_provider_status()

st.markdown(
    """
    <section class="hero">
        <p class="hero-kicker">VinUni · ReAct + MCP</p>
        <h1>Trợ lý Học vụ Thông minh</h1>
        <p>Tra cứu hồ sơ, tìm cố vấn và đặt lịch trong một luồng hội thoại ngắn gọn.</p>
    </section>
    <section class="flow" aria-label="Luồng sử dụng">
        <div class="flow-step">
            <span class="flow-number">1</span>
            <span class="flow-title">Nhập yêu cầu</span>
            <span class="flow-copy">Hỏi thông tin hoặc yêu cầu đặt lịch.</span>
        </div>
        <div class="flow-step">
            <span class="flow-number">2</span>
            <span class="flow-title">Agent xử lý</span>
            <span class="flow-copy">Tự chọn model và công cụ MCP phù hợp.</span>
        </div>
        <div class="flow-step">
            <span class="flow-number">3</span>
            <span class="flow-title">Nhận kết quả</span>
            <span class="flow-copy">Xem câu trả lời và trace khi cần.</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown("##### Thử nhanh")
sample_columns = st.columns(3)
sample_query = None
with sample_columns[0]:
    if st.button("Tra cứu sinh viên", use_container_width=True):
        sample_query = "Hãy tra cứu thông tin học vụ của sinh viên SV2026001."
with sample_columns[1]:
    if st.button("Đặt lịch tư vấn", use_container_width=True):
        sample_query = (
            "Hãy đặt lịch tư vấn học vụ cho sinh viên SV2026001 với "
            "PGS.TS Nguyễn Văn A vào lúc 14:00 ngày 15/09/2026."
        )
with sample_columns[2]:
    if st.button("Tra cứu rồi đặt lịch", use_container_width=True):
        sample_query = (
            "Hãy tra cứu cố vấn học tập của sinh viên SV2026002, sau đó đặt lịch "
            "tư vấn với đúng cố vấn đó vào lúc 09:00 ngày 16/09/2026."
        )

for index, item in enumerate(st.session_state.history):
    with st.chat_message("user", avatar="👤"):
        st.markdown(item["query"])
    with st.chat_message("assistant", avatar="🎓"):
        st.markdown(provider_badges(item["trace"]), unsafe_allow_html=True)
        st.markdown(item["answer"])
        tool_calls = sum(
            event.get("action_type") == "TOOL_EXECUTION"
            for event in item["trace"]
        )
        st.caption(
            f"Độ phức tạp: {item['complexity']} · "
            f"{len(item['trace'])} bước trace · {tool_calls} tool call"
        )
        request_trace_json = json.dumps(
            item["trace"],
            ensure_ascii=False,
            indent=2,
        )
        with st.expander("Xem trace của yêu cầu này", expanded=False):
            st.code(request_trace_json, language="json")
        st.download_button(
            "⬇️ Tải trace của yêu cầu này",
            data=request_trace_json.encode("utf-8"),
            file_name=f"request_trace_{index + 1}.json",
            mime="application/json",
            use_container_width=True,
            key=f"download-request-trace-{index}",
        )
        if any(event.get("action_type") == "ERROR" for event in item["trace"]):
            st.error("Yêu cầu kết thúc với lỗi. Hãy mở Waterfall Trace để xem chi tiết.")

saved_trace = load_saved_trace()
if saved_trace:
    saved_tool_calls = sum(
        event.get("action_type") == "TOOL_EXECUTION"
        for event in saved_trace
    )
    st.markdown(
        f"""
        <div class="trace-panel">
            Waterfall tổng đang lưu <strong>{len(saved_trace)} sự kiện</strong> ·
            <strong>{saved_tool_calls} tool call</strong> trong
            <code>docs/trace_waterfall.json</code>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("Chưa có Waterfall Trace. Hãy gửi yêu cầu đầu tiên.")

typed_query = st.chat_input("Ví dụ: Tra cứu SV2026002 rồi đặt lịch với cố vấn...")
query = typed_query or sample_query

if query:
    complexity = resolve_complexity(query, routing_mode)
    provider = get_provider_for_complexity(complexity)
    mcp_server = MCPAcademicServer()

    with st.spinner("Agent đang suy luận và kết nối MCP..."):
        trace = run_react_agent(query, provider, mcp_server)
        accumulated_trace = load_saved_trace() + trace
        save_waterfall_trace(accumulated_trace)

    st.session_state.history.append({
        "query": query,
        "answer": get_final_answer(trace),
        "complexity": complexity,
        "trace": trace,
    })
    st.rerun()

st.caption(
    "UI chỉ hiển thị trace theo từng yêu cầu. Tất cả sự kiện vẫn được nối thêm "
    "vào docs/trace_waterfall.json."
)

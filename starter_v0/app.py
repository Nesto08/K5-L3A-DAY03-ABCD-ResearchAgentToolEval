import streamlit as st

from chat import ARTIFACTS_DIR, run_model_tool_loop
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

st.title("🔎 Research Agent")

# Thanh bên: chỉ có 2 thứ
provider_name = st.sidebar.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
if st.sidebar.button("Cuộc trò chuyện mới"):
    st.session_state.chat = []
    st.rerun()

# Lịch sử chat: mỗi phần tử là {"role": ..., "content": ..., "events": [các tool đã gọi]}
if "chat" not in st.session_state:
    st.session_state.chat = []


for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        events = msg.get("events", [])
        if events:
            with st.expander(f"🔧 Agent đã gọi {len(events)} tool"):
                for e in events:
                    st.write(f"**{e['tool']}**")
                    st.code(str(e["args"]), language="json")  # tham số model truyền vào
                    st.json(e["result"], expanded=False)  # kết quả tool trả về


question = st.chat_input("Nhập yêu cầu cho agent...")
if question:
    st.session_state.chat.append({"role": "user", "content": question})
    with st.spinner("Agent đang làm việc..."):
        try:
            # Đọc lại prompt và tools mỗi lần gửi: sửa file xong là thử được ngay
            system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
            tools = to_openai_tools(load_tool_declarations(ARTIFACTS_DIR / "tools.yaml"))
            recent = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat[-10:]]
            result = run_model_tool_loop(
                provider=make_provider(provider_name),
                messages=[{"role": "system", "content": system_prompt}, *recent],
                tools=tools,
                model=None,
                max_tool_rounds=4,
            )
            answer, events = result["assistant_text"], result["tool_events"]
        except Exception as exc:
            answer, events = f"❌ Lỗi: {exc}\n\nKiểm tra lại file .env (API key) rồi thử lại.", []
    st.session_state.chat.append({"role": "assistant", "content": answer, "events": events})
    st.rerun()

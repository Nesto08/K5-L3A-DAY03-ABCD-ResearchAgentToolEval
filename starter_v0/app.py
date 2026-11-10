
import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from chat import ARTIFACTS_DIR, run_model_tool_loop
from providers import (
    AllProvidersFailed,
    auto_order,
    available_providers,
    default_provider,
    make_provider,
    provider_problem,
)
from tools import load_tool_declarations, to_openai_tools


# ==========================================
# 1. CẤU HÌNH GIAO DIỆN
# ==========================================

st.set_page_config(
    page_title="Research Agent",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Research Agent")
st.caption("AI Research Assistant - Chat with your research agent")


# ==========================================
# 2. KHỞI TẠO SESSION STATE
# ==========================================

if "chat" not in st.session_state:
    st.session_state.chat = []

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

if "transcript_created_at" not in st.session_state:
    st.session_state.transcript_created_at = datetime.now().isoformat()


# ==========================================
# 3. CẤU HÌNH SYSTEM PROMPT
# ==========================================

# Liệt kê các file prompt đang có trong artifacts/, để dropdown không trỏ
# tới file không tồn tại. Thêm system_prompt_v3.md là tự hiện ra.
prompt_versions = {
    path.stem: path.name
    for path in sorted(ARTIFACTS_DIR.glob("system_prompt*.md"))
}


# ==========================================
# 4. HÀM LƯU TRANSCRIPT
# ==========================================

def build_transcript():

    return {
        "created_at": st.session_state.transcript_created_at,
        "exported_at": datetime.now().isoformat(),
        "provider": provider_name,
        "prompt_version": selected_prompt,
        "prompt_file": prompt_versions[selected_prompt],
        "messages": st.session_state.chat
    }


def save_transcript():

    transcript = build_transcript()

    transcript_path = Path("transcript.json")

    with open(
        transcript_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            transcript,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==========================================
# 5. SIDEBAR - CẤU HÌNH AGENT
# ==========================================

st.sidebar.title("⚙️ Agent Settings")


# ------------------------------------------
# 5.1. Chọn Provider
# ------------------------------------------

st.sidebar.subheader("🤖 Model Provider")

# Chỉ hiện provider có key trong .env và đã cài SDK, nên mỗi người trong team
# chạy được với key mình đang có. `auto` thử lần lượt các provider đó.
ready_providers = available_providers()
provider_options = ["auto", *ready_providers]
preferred = default_provider()

provider_name = st.sidebar.selectbox(
    "Chọn Provider",
    provider_options,
    index=provider_options.index(preferred) if preferred in provider_options else 0,
    help=(
        "auto: thử lần lượt " + " → ".join(ready_providers or ["(chưa có)"])
        + ". Provider đầu lỗi hoặc hết quota thì chuyển sang provider sau. "
        "Đổi thứ tự bằng LAB_PROVIDER_ORDER trong .env."
    )
)

if not ready_providers:
    st.sidebar.error(
        "Thêm ít nhất một API key vào starter_v0/.env rồi chạy lại.",
        title="Chưa có provider nào dùng được",
    )

unready = [
    (name, provider_problem(name))
    for name in auto_order()
    if name not in ready_providers
]

if unready:
    with st.sidebar.expander("Provider chưa dùng được"):
        for name, problem in unready:
            st.caption(f"**{name}**: {problem}")


# ------------------------------------------
# 5.2. Chọn System Prompt
# ------------------------------------------

st.sidebar.divider()

st.sidebar.subheader("🧠 System Prompt")

selected_prompt = st.sidebar.selectbox(
    "Chọn phiên bản Prompt",
    options=list(prompt_versions.keys()),
    index=0
)

prompt_filename = prompt_versions[selected_prompt]

prompt_file = ARTIFACTS_DIR / prompt_filename

st.sidebar.caption(
    f"📄 Đang sử dụng: {prompt_filename}"
)


# ------------------------------------------
# 5.3. Quản lý cuộc trò chuyện
# ------------------------------------------

st.sidebar.divider()

st.sidebar.subheader("💬 Chat Management")

if st.sidebar.button(
    "➕ Cuộc trò chuyện mới",
    width="stretch"
):

    st.session_state.chat = []
    st.session_state.transcript_created_at = datetime.now().isoformat()
    st.session_state.confirm_clear = False

    st.rerun()


# Xóa lịch sử
if st.sidebar.button(
    "🗑️ Xóa lịch sử trò chuyện",
    width="stretch"
):

    st.session_state.confirm_clear = True


# Xác nhận xóa
if st.session_state.confirm_clear:

    st.sidebar.warning(
        "Bạn có chắc chắn muốn xóa toàn bộ lịch sử không?"
    )

    col1, col2 = st.sidebar.columns(2)

    with col1:

        if st.button(
            "Xóa",
            key="confirm_delete"
        ):

            st.session_state.chat = []
            st.session_state.transcript_created_at = datetime.now().isoformat()
            st.session_state.confirm_clear = False

            st.rerun()

    with col2:

        if st.button(
            "Hủy",
            key="cancel_delete"
        ):

            st.session_state.confirm_clear = False

            st.rerun()


# ------------------------------------------
# 5.4. Thông tin trạng thái
# ------------------------------------------

st.sidebar.divider()

st.sidebar.caption(
    f"💬 Số tin nhắn: {len(st.session_state.chat)}"
)

st.sidebar.caption(
    f"🤖 Provider: {provider_name}"
)

st.sidebar.caption(
    f"🧠 Prompt: {selected_prompt}"
)


# ------------------------------------------
# 5.5. Tải Transcript
# ------------------------------------------

transcript_json = json.dumps(
    build_transcript(),
    ensure_ascii=False,
    indent=4
)

st.sidebar.divider()

st.sidebar.subheader("📁 Lab Output")

st.sidebar.download_button(
    label="📥 Download transcript.json",
    data=transcript_json,
    file_name="transcript.json",
    mime="application/json",
    width="stretch"
)


# ==========================================
# 6. HIỂN THỊ LỊCH SỬ CHAT
# ==========================================

if not st.session_state.chat:

    st.info(
        "👋 Xin chào! Hãy nhập yêu cầu bên dưới "
        "để bắt đầu trò chuyện với Research Agent."
    )


for msg in st.session_state.chat:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        # Provider nào đã trả lời (auto có thể đổi giữa các lượt)
        if msg.get("provider"):
            st.caption(f"🤖 {msg['provider']}")

        # Hiển thị Tool Events
        events = msg.get("events", [])

        if events:

            with st.expander(
                f"🔧 Agent đã gọi {len(events)} tool"
            ):

                for index, event in enumerate(events):

                    st.markdown(
                        f"**{index + 1}. "
                        f"{event.get('tool', 'Unknown Tool')}**"
                    )

                    st.markdown("Tham số đầu vào:")

                    st.code(
                        json.dumps(
                            event.get("args", {}),
                            ensure_ascii=False,
                            indent=2
                        ),
                        language="json"
                    )

                    st.markdown("Kết quả trả về:")

                    st.json(
                        event.get("result", {})
                    )


# ==========================================
# 7. NHẬN CÂU HỎI TỪ NGƯỜI DÙNG
# ==========================================

question = st.chat_input(
    "Nhập yêu cầu cho Research Agent..."
)


if question:

    # --------------------------------------
    # 7.1. Lưu câu hỏi
    # --------------------------------------

    st.session_state.chat.append({
        "role": "user",
        "content": question
    })


    # --------------------------------------
    # 7.2. Chạy Research Agent
    # --------------------------------------

    provider_label = None

    with st.spinner("🤖 Agent đang nghiên cứu..."):

        try:

            provider = make_provider(provider_name)

            # Kiểm tra file Prompt
            if not prompt_file.exists():

                raise FileNotFoundError(
                    f"Không tìm thấy file: {prompt_filename}"
                )


            # Đọc System Prompt đã chọn
            system_prompt = prompt_file.read_text(
                encoding="utf-8"
            )


            # Đọc danh sách Tool
            tools = to_openai_tools(
                load_tool_declarations(
                    ARTIFACTS_DIR / "tools.yaml"
                )
            )


            # Lấy 10 tin nhắn gần nhất
            recent_messages = [
                {
                    "role": message["role"],
                    "content": message["content"]
                }
                for message in st.session_state.chat[-10:]
            ]


            # Khởi tạo Provider và chạy Agent
            result = run_model_tool_loop(
                provider=provider,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    *recent_messages
                ],

                tools=tools,
                model=None,
                max_tool_rounds=4,
            )


            # Lấy câu trả lời
            answer = result.get(
                "assistant_text",
                "Agent không trả về nội dung."
            )

            events = result.get(
                "tool_events",
                []
            )

            # Ghi lại provider và model đã trả lời, cùng provider bị bỏ qua
            used = getattr(provider, "last_provider", None) or provider_name
            model_name = (
                getattr(provider, "last_model", None)
                or getattr(provider, "default_model", None)
            )
            provider_label = f"{used} · {model_name}" if model_name else used
            skipped = [
                error.split(":", 1)[0]
                for error in getattr(provider, "last_errors", [])
            ]
            if skipped:
                provider_label += f" (đã bỏ qua {', '.join(skipped)} vì lỗi)"


        except AllProvidersFailed as exc:

            # auto: mọi provider đều lỗi, hiện lỗi của từng provider
            answer = (
                "❌ Không provider nào trả lời được.\n\n"
                f"```\n{exc}\n```\n\n"
                "Xem mục *Provider chưa dùng được* ở sidebar, "
                "hoặc thử lại sau."
            )

            events = []


        except Exception as exc:

            error_message = str(exc)

            if "503" in error_message or "UNAVAILABLE" in error_message:

                answer = (
                    "⚠️ Model hiện đang quá tải hoặc tạm thời "
                    "không khả dụng.\n\n"
                    "Bạn hãy thử lại sau hoặc chuyển sang Provider khác."
                )

            elif "429" in error_message:

                answer = (
                    "⚠️ Đã vượt giới hạn request hoặc quota API.\n\n"
                    "Hãy kiểm tra hạn mức API hoặc thử lại sau."
                )

            elif "401" in error_message:

                answer = (
                    "❌ API Key không hợp lệ.\n\n"
                    "Hãy kiểm tra lại API Key trong file .env."
                )

            elif "403" in error_message:

                answer = (
                    "❌ Provider từ chối quyền truy cập.\n\n"
                    "Hãy kiểm tra quyền sử dụng API."
                )

            else:

                answer = (
                    f"❌ Đã xảy ra lỗi: {error_message}"
                )

            events = []


    # --------------------------------------
    # 7.3. Lưu câu trả lời Agent
    # --------------------------------------

    st.session_state.chat.append({
        "role": "assistant",
        "content": answer,
        "events": events,
        "provider": provider_label
    })


    # --------------------------------------
    # 7.4. Lưu transcript.json
    # --------------------------------------

    save_transcript()


    # --------------------------------------
    # 7.5. Cập nhật giao diện
    # --------------------------------------

    st.rerun()

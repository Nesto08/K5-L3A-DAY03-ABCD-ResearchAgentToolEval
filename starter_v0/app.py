
import streamlit as st
import json
import sqlite3

from chat import ARTIFACTS_DIR, run_model_tool_loop
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

st.set_page_config(
    page_title="Research Agent",
    layout="wide"
)

st.title("🔎 Research Agent")
st.caption("AI Research Assistant - Chat with your research agent")

# Database được tạo tại thư mục chạy app.py
DB_PATH = "research_agent.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                events TEXT,
                FOREIGN KEY (chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            )
        """)


def create_chat(title="Cuộc trò chuyện mới"):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO chats (title) VALUES (?)",
            (title,)
        )
        return cursor.lastrowid


def get_recent_chats():
    with get_db() as conn:
        return conn.execute("""
            SELECT id, title, updated_at
            FROM chats
            ORDER BY updated_at DESC
        """).fetchall()


def load_chat(chat_id):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT role, content, events
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
        """, (chat_id,)).fetchall()

    messages = []

    for role, content, events in rows:
        messages.append({
            "role": role,
            "content": content,
            "events": json.loads(events) if events else []
        })

    return messages


def save_message(chat_id, role, content, events=None):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO messages (chat_id, role, content, events)
            VALUES (?, ?, ?, ?)
        """, (
            chat_id,
            role,
            content,
            json.dumps(events or [], ensure_ascii=False)
        ))

        conn.execute("""
            UPDATE chats
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (chat_id,))


def update_chat_title(chat_id, title):
    with get_db() as conn:
        conn.execute("""
            UPDATE chats
            SET title = ?
            WHERE id = ? AND title = 'Cuộc trò chuyện mới'
        """, (title[:50], chat_id))


def delete_all_chats():
    with get_db() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM chats")

init_db()

if "chat" not in st.session_state:
    st.session_state.chat = []

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

st.sidebar.title("⚙️ Cài đặt")

provider_name = st.sidebar.selectbox(
    "Provider",
    ["openrouter", "openai", "anthropic", "gemini", "ollama"]
)

st.sidebar.divider()

if st.sidebar.button("➕ Cuộc trò chuyện mới", use_container_width=True):
    st.session_state.chat = []
    st.session_state.current_chat_id = None
    st.session_state.confirm_clear = False
    st.rerun()

st.sidebar.subheader("🕘 Recent Chats")

recent_chats = get_recent_chats()

if not recent_chats:
    st.sidebar.caption("Chưa có cuộc trò chuyện nào.")

for chat_id, title, updated_at in recent_chats:

    if st.sidebar.button(
        f"💬 {title}",
        key=f"chat_{chat_id}",
        use_container_width=True,
        type="primary" if chat_id == st.session_state.current_chat_id else "secondary"
    ):
        st.session_state.current_chat_id = chat_id
        st.session_state.chat = load_chat(chat_id)
        st.rerun()


st.sidebar.divider()

if st.sidebar.button(
    "🗑️ Xóa lịch sử trò chuyện",
    use_container_width=True
):
    st.session_state.confirm_clear = True


if st.session_state.confirm_clear:

    st.sidebar.warning("Bạn có chắc chắn muốn xóa toàn bộ lịch sử?")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Xóa", key="confirm_delete"):
            delete_all_chats()
            st.session_state.chat = []
            st.session_state.current_chat_id = None
            st.session_state.confirm_clear = False
            st.rerun()

    with col2:
        if st.button("Hủy", key="cancel_delete"):
            st.session_state.confirm_clear = False
            st.rerun()


st.sidebar.divider()

st.sidebar.caption(
    f"💬 Số tin nhắn: {len(st.session_state.chat)}"
)

if not st.session_state.chat:
    st.info(
        "👋 Xin chào! Hãy nhập yêu cầu bên dưới để bắt đầu "
        "trò chuyện với Research Agent."
    )


for msg in st.session_state.chat:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        events = msg.get("events", [])

        if events:

            with st.expander(
                f"🔧 Agent đã gọi {len(events)} tool"
            ):

                for index, event in enumerate(events):

                    st.markdown(
                        f"**{index + 1}. {event.get('tool', 'Unknown Tool')}**"
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
                    st.json(event.get("result", {}))

question = st.chat_input(
    "Nhập yêu cầu cho Research Agent..."
)


if question:

    if st.session_state.current_chat_id is None:

        st.session_state.current_chat_id = create_chat(
            question[:50]
        )

    else:
        update_chat_title(
            st.session_state.current_chat_id,
            question
        )

    chat_id = st.session_state.current_chat_id

    user_message = {
        "role": "user",
        "content": question
    }

    st.session_state.chat.append(user_message)

    save_message(
        chat_id,
        "user",
        question
    )

    with st.spinner("🤖 Agent đang nghiên cứu..."):

        try:

            system_prompt = (
                ARTIFACTS_DIR / "system_prompt.md"
            ).read_text(encoding="utf-8")

            # Đọc Tools
            tools = to_openai_tools(
                load_tool_declarations(
                    ARTIFACTS_DIR / "tools.yaml"
                )
            )

            recent_messages = [
                {
                    "role": message["role"],
                    "content": message["content"]
                }
                for message in st.session_state.chat[-10:]
            ]

            # Chạy Agent
            result = run_model_tool_loop(
                provider=make_provider(provider_name),
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

            answer = result.get(
                "assistant_text",
                "Agent không trả về nội dung."
            )

            events = result.get("tool_events", [])

        except Exception as exc:

            answer = (
                f"❌ Đã xảy ra lỗi: {exc}\n\n"
                "Kiểm tra lại API key trong file .env "
                "và cấu hình Provider."
            )

            events = []

    assistant_message = {
        "role": "assistant",
        "content": answer,
        "events": events
    }

    st.session_state.chat.append(assistant_message)

    save_message(
        chat_id,
        "assistant",
        answer,
        events
    )

    st.rerun()

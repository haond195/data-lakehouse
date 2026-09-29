import os
import re
import streamlit as st
import pandas as pd
import requests
import altair as alt
from trino.dbapi import connect

def detect_chart_type(prompt_text: str) -> str:
    p = prompt_text.lower()
    if any(k in p for k in ["tròn", "pie", "donut", "bánh", "tỷ lệ", "tỷ trọng", "phần trăm", "cơ cấu"]):
        return "pie"
    elif any(k in p for k in ["đường", "line", "xu hướng", "trend", "biến thiên", "thời gian", "theo tháng", "theo năm"]):
        return "line"
    return "bar"

def render_chart(df: pd.DataFrame, chart_type: str, col_x: str, col_y: str):
    if chart_type == "pie":
        pie = alt.Chart(df).mark_arc(innerRadius=45, outerRadius=120).encode(
            theta=alt.Theta(field=col_y, type="quantitative"),
            color=alt.Color(field=col_x, type="nominal", legend=alt.Legend(title=col_x)),
            tooltip=[col_x, col_y]
        ).properties(height=360)
        st.altair_chart(pie, use_container_width=True)
    elif chart_type == "line":
        st.line_chart(df.set_index(col_x)[col_y])
    else:
        st.bar_chart(df.set_index(col_x)[col_y])

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

st.set_page_config(
    page_title="AI Data Analyst (Trino + Iceberg)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Font chuẩn Inter - không đè lên Material Icons của Streamlit
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, p, h1, h2, h3, input, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# Kết nối Trino
@st.cache_resource
def get_trino_conn(catalog: str = "iceberg_stg", schema: str = "stg_gold"):
    return connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=8080,
        user="ai_analyst",
        catalog=catalog,
        schema=schema
    )

@st.cache_data(ttl=60)
def get_available_catalogs():
    try:
        conn = get_trino_conn("iceberg_stg", "stg_gold")
        cur = conn.cursor()
        cur.execute("SHOW CATALOGS")
        cats = [r[0] for r in cur.fetchall() if r[0] not in ['system', 'information_schema', 'lakehouse']]
        order = {"iceberg_stg": 0, "iceberg": 1, "tpcds": 2}
        cats.sort(key=lambda x: order.get(x, 99))
        return cats if cats else ["iceberg_stg", "iceberg"]
    except Exception:
        return ["iceberg_stg", "iceberg", "tpcds"]

@st.cache_data(ttl=60)
def get_available_schemas(catalog_name: str):
    try:
        conn = get_trino_conn(catalog_name, "information_schema")
        cur = conn.cursor()
        cur.execute(f"SHOW SCHEMAS FROM {catalog_name}")
        schemas = [r[0] for r in cur.fetchall() if r[0] not in ['information_schema', 'system'] and not r[0].startswith('retail_gold_')]
        order = {"stg_gold": 0, "retail_gold": 1, "stg_silver": 2, "retail_silver": 3, "stg_bronze": 4, "retail_bronze": 5, "demo_scd": 6, "sf1": 7}
        schemas.sort(key=lambda x: order.get(x, 99))
        return schemas if schemas else ["default"]
    except Exception:
        return ["stg_gold", "stg_silver", "stg_bronze", "demo_scd"] if catalog_name == "iceberg_stg" else ["retail_gold", "retail_silver", "retail_bronze"]

st.title("🤖 AI Data Analyst Chatbot")
st.markdown("Trợ lý phân tích dữ liệu tự động truy vấn vào **Trino**, **Apache Iceberg Lakehouse**.")

# Bộ chọn Catalog & Schema hiển thị trực tiếp ngay đầu trang
st.markdown("##### 🎯 Chọn Nguồn Dữ Liệu Phân Tích:")
col_cat, col_sch = st.columns(2)

catalogs = get_available_catalogs()
with col_cat:
    selected_catalog = st.selectbox(
        "🗄️ Catalog",
        catalogs,
        index=0,
        help="Chọn catalog từ Trino (iceberg_stg, iceberg, tpcds,...)"
    )

schemas = get_available_schemas(selected_catalog)
with col_sch:
    selected_schema = st.selectbox(
        "📁 Schema",
        schemas,
        index=0,
        help=f"Chọn schema thuộc catalog '{selected_catalog}'"
    )

with st.expander(f"📋 Bảng khả dụng trong `{selected_catalog}.{selected_schema}`", expanded=False):
    try:
        conn = get_trino_conn(selected_catalog, selected_schema)
        cur = conn.cursor()
        cur.execute(f"SHOW TABLES FROM {selected_catalog}.{selected_schema}")
        tbl_list = [r[0] for r in cur.fetchall()]
        if tbl_list:
            st.write(", ".join([f"`{t}`" for t in tbl_list]))
        else:
            st.write("*(Chưa có bảng nào)*")
    except Exception as e:
        st.write(f"Lỗi: {e}")

# Sidebar cấu hình Nhà cung cấp AI
st.sidebar.header("⚙️ Cấu hình Nhà Cung Cấp AI")
provider = st.sidebar.selectbox(
    "Nền tảng AI",
    ["FPT AI / DeepSeek (OpenAI Compatible)", "Google Gemini"],
    index=0
)

if provider == "FPT AI / DeepSeek (OpenAI Compatible)":
    api_key = st.sidebar.text_input(
        "🔑 FPT / DeepSeek API Key",
        value=os.getenv("LLM_API_KEY", ""),
        type="password",
        help="Lấy API Key từ trang FPT AI Console"
    )
    base_url = st.sidebar.text_input(
        "🌐 Base URL / Endpoint",
        value=os.getenv("LLM_BASE_URL", "https://mkp-api.fptcloud.com/v1"),
        help="Xem mục API Reference của FPT AI (mặc định: https://mkp-api.fptcloud.com/v1)"
    )
    model_name = st.sidebar.text_input(
        "🤖 Model Name",
        value=os.getenv("LLM_MODEL", "DeepSeek-V4-Flash"),
        help="Ví dụ: DeepSeek-V4-Flash, Saola-Small-32B"
    )
    if api_key:
        st.sidebar.success(f"🟢 Kích hoạt: {model_name}")
    else:
        st.sidebar.info("⚪ Nhập API Key bên trên để bật AI LLM")
else:
    api_key = st.sidebar.text_input(
        "🔑 Google Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password"
    )
    base_url = ""
    model_name = st.sidebar.selectbox(
        "Mô hình Gemini",
        ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0
    )
    if api_key:
        st.sidebar.success(f"🟢 Kích hoạt: {model_name}")
    else:
        st.sidebar.info("⚪ Nhập API Key bên trên để bật AI LLM")

@st.cache_data(ttl=120)
def get_dynamic_schema(target_catalog: str, target_schema: str) -> str:
    try:
        conn = get_trino_conn(target_catalog, target_schema)
        cur = conn.cursor()
        cur.execute(f"SHOW TABLES FROM {target_catalog}.{target_schema}")
        tables = [r[0] for r in cur.fetchall()]
        parts = []
        for tbl in tables:
            try:
                cur.execute(f"DESCRIBE {target_catalog}.{target_schema}.{tbl}")
                cols = [f"{r[0]} ({r[1]})" for r in cur.fetchall()]
                parts.append(f"Table: {target_catalog}.{target_schema}.{tbl}\nColumns: {', '.join(cols)}")
            except Exception:
                pass
        return "\n\n".join(parts) if parts else f"Schema: {target_catalog}.{target_schema}"
    except Exception as e:
        return f"Schema: {target_catalog}.{target_schema} (Lỗi quét schema: {e})"

def build_system_prompt(target_catalog: str, target_schema: str) -> str:
    schema_info = get_dynamic_schema(target_catalog, target_schema)
    return f"""You are an expert Trino SQL Data Analyst for an Apache Iceberg Lakehouse.
Generate ONLY valid Trino SQL. Think concisely and output the SQL query directly.

Real-time Database Schema for {target_catalog}.{target_schema} (quét trực tiếp từ Lakehouse):
{schema_info}

Rules:
- Output ONLY the executable SQL query starting with SELECT or WITH. No explanation, no markdown text outside code.
- STRICT: Use ONLY the exact column names provided in the schema above. Do NOT invent columns that do not exist.
- Always use full table names: {target_catalog}.{target_schema}.<table_name>
- Use ROUND(..., 2) for currency, averages, or profit amounts.
- Limit top/bottom queries with LIMIT N (default 10).
- Do not add semicolons at the end of the query.
- Do NOT truncate or leave clauses unclosed.
"""

def clean_generated_sql(raw_text: str) -> str:
    if not raw_text:
        return ""
    match_code = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", raw_text, flags=re.IGNORECASE)
    if match_code:
        sql = match_code.group(1).strip()
    else:
        match_query = re.search(r"((?:WITH|SELECT|SHOW|DESCRIBE)[\s\S]+)", raw_text, flags=re.IGNORECASE)
        if match_query:
            sql = match_query.group(1).strip()
        else:
            sql = raw_text.strip()
    
    sql = re.sub(r"^```(sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.rstrip("; \t\n")
    return sql

def generate_sql_with_openai_compatible(user_prompt: str, key: str, url: str, model: str, target_catalog: str, target_schema: str) -> str:
    endpoint = url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    sys_prompt = build_system_prompt(target_catalog, target_schema)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"User question: {user_prompt}\nGenerate Trino SQL query:"}
        ],
        "max_tokens": 4000,
        "temperature": 0.1
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=75)
    resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    raw_content = message.get("content") or ""
    if not raw_content.strip():
        raw_content = message.get("reasoning_content") or ""
    return clean_generated_sql(str(raw_content).strip())

def generate_sql_with_gemini(user_prompt: str, key: str, model: str, target_catalog: str, target_schema: str) -> str:
    if not HAS_GENAI:
        raise RuntimeError("Thư viện google-generativeai chưa được cài đặt")
    genai.configure(api_key=key)
    m = genai.GenerativeModel(model)
    full_prompt = f"""{build_system_prompt(target_catalog, target_schema)}
Question: {user_prompt}
Trino SQL:"""
    resp = m.generate_content(full_prompt)
    raw_content = resp.text.strip()
    return clean_generated_sql(raw_content)

# Lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "df" in msg:
            st.dataframe(msg["df"], use_container_width=True)
        if msg.get("chart"):
            c_info = msg["chart"]
            if isinstance(c_info, dict):
                render_chart(msg["df"], c_info.get("type", "bar"), c_info["cols"][0], c_info["cols"][1])
            elif isinstance(c_info, (tuple, list)) and len(c_info) == 2:
                render_chart(msg["df"], "bar", c_info[0], c_info[1])

user_input = st.chat_input(f"Nhập câu hỏi phân tích cho {selected_catalog}.{selected_schema} hoặc nhập trực tiếp câu SQL...")
prompt = st.session_state.pop("prompt_input", None) or user_input

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    sql = None
    engine_used = ""
    is_direct_sql = prompt.strip().upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE"))

    if is_direct_sql:
        sql = clean_generated_sql(prompt)
        engine_used = "Truy vấn trực tiếp (Direct SQL)"
    elif api_key:
        try:
            with st.spinner(f"🤖 {model_name} đang phân tích cấu trúc {selected_catalog}.{selected_schema} để sinh SQL..."):
                if provider.startswith("FPT AI"):
                    sql = generate_sql_with_openai_compatible(prompt, api_key, base_url, model_name, selected_catalog, selected_schema)
                else:
                    sql = generate_sql_with_gemini(prompt, api_key, model_name, selected_catalog, selected_schema)
                engine_used = f"{model_name} ({provider})"
        except Exception as err:
            err_msg = f"⚠️ Lỗi khi gọi AI ({err}). Vui lòng kiểm tra API Key hoặc nhập trực tiếp câu lệnh SQL."
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
    else:
        warn_msg = "⚠️ Vui lòng cấu hình API Key ở Sidebar để AI tự sinh SQL, hoặc nhập trực tiếp câu lệnh SQL bắt đầu bằng SELECT/WITH."
        st.warning(warn_msg)
        st.session_state.messages.append({"role": "assistant", "content": warn_msg})

    if sql:
        with st.chat_message("assistant"):
            st.markdown(f"**Câu lệnh SQL do {engine_used} thực thi:**")
            st.code(sql, language="sql")

            try:
                conn = get_trino_conn(selected_catalog, selected_schema)
                cursor = conn.cursor()
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=columns)

                st.dataframe(df, use_container_width=True)

                chart_data = None
                for col in df.columns[1:]:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except Exception:
                        pass

                if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                    col_x, col_y = df.columns[0], df.columns[1]
                    ctype = detect_chart_type(prompt)
                    render_chart(df, ctype, col_x, col_y)
                    chart_data = {"type": ctype, "cols": (col_x, col_y)}

                res_payload = {
                    "role": "assistant",
                    "content": f"Kết quả phân tích từ Lakehouse ({engine_used}):",
                    "sql": sql,
                    "df": df
                }
                if chart_data:
                    res_payload["chart"] = chart_data
                st.session_state.messages.append(res_payload)

            except Exception as e:
                err_msg = f"Lỗi truy vấn Trino: {e}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

import os
import re
import streamlit as st
import pandas as pd
import requests
from trino.dbapi import connect

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

st.set_page_config(page_title="AI Data Analyst (Trino + Iceberg)", page_icon="🤖", layout="wide")

# CSS Font chuẩn Inter và giao diện tinh tế
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, span, h1, h2, h3, button, input {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Data Analyst Chatbot")
st.markdown("Trợ lý phân tích dữ liệu tự động truy vấn vào **Trino**, **Apache Iceberg** và **MinIO (S3)**.")

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

# Kết nối Trino
@st.cache_resource
def get_trino_conn():
    return connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=8080,
        user="ai_analyst",
        catalog="iceberg",
        schema="retail_gold"
    )

@st.cache_data(ttl=300)
def get_dynamic_schema() -> str:
    try:
        conn = get_trino_conn()
        cur = conn.cursor()
        tables = [
            ("iceberg.retail_gold.semantic_sales_mart", "Sales Mart (Doanh số, Đơn hàng, Cửa hàng)"),
            ("iceberg.retail_gold.mart_monthly_store_performance", "Store Performance (Hiệu suất cửa hàng theo tháng)"),
            ("iceberg.retail_gold.customer_gold", "Customer Dimension (Khách hàng)")
        ]
        parts = []
        for tbl, desc in tables:
            try:
                cur.execute(f"DESCRIBE {tbl}")
                cols = [f"{r[0]} ({r[1]})" for r in cur.fetchall()]
                parts.append(f"Table: {tbl} - {desc}\nColumns: {', '.join(cols)}")
            except Exception:
                pass
        return "\n\n".join(parts) if parts else "Table: iceberg.retail_gold.semantic_sales_mart (sales_year, sales_month, store_id, store_name, net_revenue, gross_revenue, net_profit)"
    except Exception:
        return "Table: iceberg.retail_gold.semantic_sales_mart (sales_year, sales_month, store_id, store_name, net_revenue, gross_revenue, net_profit)"

def build_system_prompt() -> str:
    schema = get_dynamic_schema()
    return f"""You are an expert Trino SQL Data Analyst for an Apache Iceberg Lakehouse.
Generate ONLY valid Trino SQL. Think concisely and output the SQL query directly.

Real-time Database Schema (quét trực tiếp từ cơ sở dữ liệu hiện tại):
{schema}

Rules:
- Output ONLY the executable SQL query starting with SELECT. No explanation, no markdown text outside code.
- STRICT: Use ONLY the exact column names provided in the schema above. Do NOT invent columns that do not exist.
- Always use full table names: iceberg.retail_gold.semantic_sales_mart or iceberg.retail_gold.customer_gold.
- Use ROUND(..., 2) for currency/profit.
- Use COUNT(DISTINCT order_id) for order count.
- Limit top/bottom queries with LIMIT N (default 10).
- Do not add semicolons at the end of the query.
"""

def clean_generated_sql(raw_text: str) -> str:
    if not raw_text:
        return ""
    # 1. Tìm khối ```sql ... ```
    match_code = re.search(r"```(?:sql)?\s*(SELECT[\s\S]*?)\s*```", raw_text, flags=re.IGNORECASE)
    if match_code:
        sql = match_code.group(1).strip()
    else:
        # 2. Tìm khối bắt đầu bằng SELECT
        match_select = re.search(r"(SELECT[\s\S]+)", raw_text, flags=re.IGNORECASE)
        if match_select:
            sql = match_select.group(1).strip()
        else:
            sql = raw_text.strip()
    
    # 3. Làm sạch ký tự thừa và dấu chấm phẩy cuối dòng (Trino không cho phép ;)
    sql = re.sub(r"^```(sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.rstrip("; \t\n")
    return sql

def generate_sql_with_openai_compatible(user_prompt: str, key: str, url: str, model: str) -> str:
    endpoint = url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    sys_prompt = build_system_prompt()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"""User question: {user_prompt}
Generate Trino SQL query:"""}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=75)
    resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0].get("message", {})
    raw_content = choice.get("content") or choice.get("reasoning_content") or ""
    return clean_generated_sql(str(raw_content).strip())

def generate_sql_with_gemini(user_prompt: str, key: str, model: str) -> str:
    if not HAS_GENAI:
        raise RuntimeError("Thư viện google-generativeai chưa được cài đặt")
    genai.configure(api_key=key)
    m = genai.GenerativeModel(model)
    full_prompt = f"""{build_system_prompt()}
Question: {user_prompt}
Trino SQL:"""
    resp = m.generate_content(full_prompt)
    raw_content = resp.text.strip()
    return clean_generated_sql(raw_content)

def parse_natural_language_to_sql(user_prompt: str) -> str:
    p = user_prompt.lower()
    
    if p.strip().upper().startswith("SELECT"):
        return user_prompt.strip()

    limit = 5
    match_limit = re.search(r"top\s*(\d+)", p)
    if match_limit:
        limit = int(match_limit.group(1))
    elif "10" in p:
        limit = 10

    order_dir = "DESC"
    if any(k in p for k in ["thấp nhất", "ít nhất", "kém nhất", "bottom", "lowest"]):
        order_dir = "ASC"

    if any(k in p for k in ["lợi nhuận", "profit", "lãi"]):
        metric_col = "ROUND(SUM(net_profit), 2)"
        metric_alias = "total_profit"
    elif any(k in p for k in ["số đơn", "đơn hàng", "lượt mua", "order"]):
        metric_col = "COUNT(DISTINCT order_id)"
        metric_alias = "total_orders"
    elif any(k in p for k in ["số lượng", "chiếc", "cái", "quantity"]):
        metric_col = "SUM(quantity_sold)"
        metric_alias = "total_quantity"
    else:
        metric_col = "ROUND(SUM(net_revenue), 2)"
        metric_alias = "total_revenue"

    if any(k in p for k in ["cửa hàng", "store", "chi nhánh", "shop"]):
        dim_col = "store_name"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE store_name IS NOT NULL"
    elif any(k in p for k in ["danh mục", "ngành hàng", "loại", "category"]):
        dim_col = "category"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE category IS NOT NULL"
    elif any(k in p for k in ["thương hiệu", "hãng", "brand"]):
        dim_col = "brand"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE brand IS NOT NULL"
    elif any(k in p for k in ["khu vực", "bang", "tiểu bang", "state"]):
        dim_col = "store_state"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE store_state IS NOT NULL"
    elif any(k in p for k in ["năm", "year"]):
        dim_col = "sales_year"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE sales_year IS NOT NULL"
    elif any(k in p for k in ["tháng", "month"]):
        dim_col = "sales_month"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE sales_month IS NOT NULL"
    elif any(k in p for k in ["quốc gia", "country"]) or ("khách hàng" in p and "bán chạy" not in p):
        return f"""SELECT country, COUNT(*) AS total_customers 
FROM iceberg.retail_gold.customer_gold 
GROUP BY country 
ORDER BY total_customers {order_dir} 
LIMIT {limit}"""
    else:
        dim_col = "product_name"
        table = "iceberg.retail_gold.semantic_sales_mart"
        where_clause = "WHERE product_name IS NOT NULL"

    sql = f"""SELECT {dim_col}, {metric_col} AS {metric_alias}
FROM {table}
{where_clause}
GROUP BY {dim_col}
ORDER BY {metric_alias} {order_dir}
LIMIT {limit}"""
    return sql.strip()

# Gợi ý nhanh
st.subheader("💡 Câu hỏi mẫu:")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏪 Top cửa hàng bán chạy"):
        st.session_state["prompt_input"] = "top cửa hàng bán chạy nhất"
with col2:
    if st.button("🏆 Top 5 sản phẩm doanh thu cao"):
        st.session_state["prompt_input"] = "top 5 sản phẩm bán chạy nhất"
with col3:
    if st.button("📊 Doanh thu theo danh mục"):
        st.session_state["prompt_input"] = "doanh thu theo danh mục"
with col4:
    if st.button("👥 Khách hàng theo quốc gia"):
        st.session_state["prompt_input"] = "khách hàng theo quốc gia"

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
            col_x, col_y = msg["chart"]
            st.bar_chart(msg["df"].set_index(col_x)[col_y])

user_input = st.chat_input("Nhập câu hỏi phân tích bằng tiếng Việt hoặc SQL...")
prompt = st.session_state.pop("prompt_input", None) or user_input

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    sql = None
    engine_used = ""
    if api_key:
        try:
            with st.spinner(f"🤖 {model_name} đang sinh câu lệnh SQL..."):
                if provider.startswith("FPT AI"):
                    sql = generate_sql_with_openai_compatible(prompt, api_key, base_url, model_name)
                else:
                    sql = generate_sql_with_gemini(prompt, api_key, model_name)
                engine_used = f"{model_name} ({provider})"
        except Exception as err:
            st.warning(f"⚠️ Không thể gọi API LLM ({err}). Tự động chuyển về Smart Rule Parser.")
            sql = parse_natural_language_to_sql(prompt)
            engine_used = "Smart Rule Parser (Fallback)"
    else:
        sql = parse_natural_language_to_sql(prompt)
        engine_used = "Smart Rule Parser"

    with st.chat_message("assistant"):
        st.markdown(f"**Câu lệnh SQL do {engine_used} sinh:**")
        st.code(sql, language="sql")

        try:
            conn = get_trino_conn()
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)

            st.dataframe(df, use_container_width=True)

            chart_cols = None
            for col in df.columns[1:]:
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    pass

            if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                st.bar_chart(df.set_index(df.columns[0])[df.columns[1]])
                chart_cols = (df.columns[0], df.columns[1])

            res_payload = {
                "role": "assistant",
                "content": f"Kết quả phân tích từ Lakehouse ({engine_used}):",
                "sql": sql,
                "df": df
            }
            if chart_cols:
                res_payload["chart"] = chart_cols
            st.session_state.messages.append(res_payload)

        except Exception as e:
            err_msg = f"Lỗi truy vấn Trino: {e}"
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})

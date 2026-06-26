import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from reportlab.pdfgen import canvas
import io

#CONFIG 

WEBHOOK_URL = "http://localhost:5678/webhook/analyze-data"

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide"
)

#LOAD CSS

def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# AI FUNCTION 

def ask_ai(question, dataset):
    try:
        r = requests.post(
            WEBHOOK_URL,
            json={
                "question": question,
                "dataset": dataset
            },
            timeout=120
        )

        try:
            return r.json().get("output", r.text)
        except:
            return r.text

    except Exception as e:
        return f"Error: {e}"

# PDF

def make_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    y = 800
    for line in text.split("\n"):
        c.drawString(30, y, line[:100])
        y -= 15

        if y < 50:
            c.showPage()
            y = 800

    c.save()
    buffer.seek(0)
    return buffer

#  UI 

st.title("📊 AI Data Analyst Dashboard")

file = st.file_uploader("Upload CSV / Excel File", type=["csv", "xlsx"])

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.success("Dataset Loaded Successfully!")

    dataset = df.head(50).to_csv(index=False)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "📈 Dashboard",
        "🤖 AI Analysis",
        "💬 Chat"
    ])

    # OVERVIEW 

    with tab1:
        st.subheader("Dataset Overview")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])
        c3.metric("Missing", df.isnull().sum().sum())
        c4.metric("Duplicates", df.duplicated().sum())

        st.dataframe(df.head(10), use_container_width=True)

    # DASHBOARD

    with tab2:

        num_cols = df.select_dtypes(include="number").columns

        if len(num_cols) > 0:
            col = st.selectbox("Select Numeric Column", num_cols)
            st.plotly_chart(px.histogram(df, x=col), use_container_width=True)

        if len(num_cols) > 1:
            st.plotly_chart(px.imshow(df[num_cols].corr(), text_auto=True), use_container_width=True)

        cat_cols = df.select_dtypes(include="object").columns

        if len(cat_cols) > 0:
            col2 = st.selectbox("Select Category Column", cat_cols)

            pie_df = df[col2].value_counts().reset_index()
            pie_df.columns = [col2, "count"]

            fig = px.pie(pie_df, names=col2, values="count")
            st.plotly_chart(fig, use_container_width=True)

    # AI ANALYSIS

    with tab3:

        if st.button("Generate AI Analysis"):

            with st.spinner("Analyzing data..."):
                result = ask_ai(
                    "Analyze dataset and give insights, anomalies, recommendations",
                    dataset
                )

                st.session_state["ai_result"] = result

        if "ai_result" in st.session_state:

            st.success("AI Analysis Completed")
            st.write(st.session_state["ai_result"])

            pdf = make_pdf(st.session_state["ai_result"])

            st.download_button(
                "📄 Download PDF Report",
                pdf,
                file_name="ai_report.pdf"
            )

    # CHAT

    with tab4:

        if "chat" not in st.session_state:
            st.session_state.chat = []

        for m in st.session_state.chat:
            with st.chat_message(m["role"]):
                st.write(m["msg"])

        q = st.chat_input("Ask anything about your dataset")

        if q:
            st.chat_message("user").write(q)

            ans = ask_ai(q, dataset)

            st.chat_message("assistant").write(ans)

            st.session_state.chat.append({"role": "user", "msg": q})
            st.session_state.chat.append({"role": "assistant", "msg": ans})

else:
    st.info("Upload a file to start analysis")
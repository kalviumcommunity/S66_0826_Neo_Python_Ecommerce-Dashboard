import streamlit as st

st.set_page_config(page_title="Analytics Dashboard", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Trends", "Data Explorer"]
)

if page == "Overview":
    st.title("Business Overview")
    st.write("KPI summary cards and key metrics will appear here.")

    # KPI row using columns
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Revenue", "$5.2M", "+12.5%")
    with col2:
        st.metric("Users", "2,500", "+5.2%")
    with col3:
        st.metric("AOV", "$45", "+2.1%")
    with col4:
        st.metric("Churn", "5.2%", "-2.8%", delta_color="inverse")
    with col5:
        st.metric("NPS", "72", "+4")

    # Expander for methodology notes
    with st.expander("About These Metrics"):
        st.write("Revenue is calculated as sum of all order amounts "
                 "for the current month. Churn is the percentage of "
                 "customers who did not return within 30 days.")

elif page == "Trends":
    st.title("Trend Analysis")
    st.write("Time-series charts and comparisons will appear here.")

elif page == "Data Explorer":
    st.title("Data Explorer")
    st.write("Filters, data tables, and export options will appear here.")





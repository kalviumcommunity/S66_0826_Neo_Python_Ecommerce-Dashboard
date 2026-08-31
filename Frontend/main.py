import streamlit as st

from components.upload import (
    display_exploration,
    display_preview,
    display_statistics,
    upload_dataset,
)


st.set_page_config(page_title="Analytics Dashboard", layout="wide")

# "selected_segment" stores the user's confirmed segment from Step 1.
# It survives reruns caused by interactions with other widgets.
if "selected_segment" not in st.session_state:
    st.session_state["selected_segment"] = "All"

# "workflow_step" tracks which workflow step the user has completed.
# It prevents Step 2 from displaying before Step 1 is confirmed.
if "workflow_step" not in st.session_state:
    st.session_state["workflow_step"] = 1

# "analysis_result" caches the Step 2 result so unrelated reruns do not
# replace the result for the selected segment.
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# "filter_date_start" stores the Step 2 date filter independently of the
# selected segment, so changing the date never resets workflow progress.
if "filter_date_start" not in st.session_state:
    st.session_state["filter_date_start"] = None

st.sidebar.title("Navigation")
if st.sidebar.button("Reset Workflow"):
    for key in [
        "selected_segment",
        "workflow_step",
        "analysis_result",
        "filter_date_start",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

page = st.sidebar.radio("Go to", ["Overview", "Trends", "Data Explorer"])

if page == "Overview":
    st.title("Business Overview")

    st.header("Step 1: Select Segment")
    segment = st.selectbox(
        "Segment",
        ["All", "Enterprise", "Mid-Market", "SMB"],
        index=["All", "Enterprise", "Mid-Market", "SMB"].index(
            st.session_state["selected_segment"]
        ),
    )
    if st.button("Confirm Segment"):
        st.session_state["selected_segment"] = segment
        st.session_state["workflow_step"] = 2
        st.session_state["analysis_result"] = None
        st.rerun()

    if st.session_state["workflow_step"] >= 2:
        st.header("Step 2: Analysis")
        st.write(f"Analysing: {st.session_state['selected_segment']}")
        filter_date = st.date_input(
            "Filter analysis from date",
            value=st.session_state["filter_date_start"],
            key="filter_date_start",
        )
        st.session_state["analysis_result"] = (
            f"Analysis ready for {st.session_state['selected_segment']}"
            f" from {filter_date}."
        )
        st.success(st.session_state["analysis_result"])

    st.write("KPI summary cards and key metrics will appear here.")
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
    with st.expander("About These Metrics"):
        st.write("Revenue is calculated as the sum of all order amounts for the current month. Churn is the percentage of customers who did not return within 30 days.")

elif page == "Trends":
    st.title("Trend Analysis")
    st.write("Time-series charts and comparisons will appear here.")

elif page == "Data Explorer":
    st.title("Data Explorer")
    dataframe = upload_dataset()
    if dataframe is not None:
        display_preview(dataframe)
        display_statistics(dataframe)
        display_exploration(dataframe)

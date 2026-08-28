import pandas as pd
import streamlit as st


def upload_dataset():
    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "json"],
    )

    if uploaded_file is None:
        st.info("Upload a CSV or JSON file to begin.")
        return None

    try:
        filename = uploaded_file.name.lower()
        if filename.endswith(".csv"):
            dataframe = pd.read_csv(uploaded_file)
        elif filename.endswith(".json"):
            dataframe = pd.read_json(uploaded_file)
        else:
            st.error("Unsupported file type.")
            return None

        if dataframe.empty:
            st.warning("Uploaded file is empty.")
            return None
    except Exception:
        st.error("Could not read this file. Check the format and try again.")
        return None

    st.success(
        f"Loaded: {uploaded_file.name} "
        f"({len(dataframe)} rows, {len(dataframe.columns)} columns)"
    )
    return dataframe


def display_preview(dataframe: pd.DataFrame):
    st.header("Dataset Preview")
    total_cells = dataframe.shape[0] * dataframe.shape[1]
    null_percentage = (
        dataframe.isnull().sum().sum() / total_cells * 100
        if total_cells else 0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(dataframe):,}")
    with col2:
        st.metric("Columns", len(dataframe.columns))
    with col3:
        st.metric("Null %", f"{null_percentage:.1f}%")

    st.subheader("First 10 Rows")
    st.dataframe(dataframe.head(10), use_container_width=True)

    st.subheader("Column Summary")
    summary = pd.DataFrame({
        "Column": dataframe.columns,
        "Type": dataframe.dtypes.astype(str).values,
        "Non-Null": dataframe.notnull().sum().values,
        "Null Count": dataframe.isnull().sum().values,
        "Null %": (dataframe.isnull().sum() / len(dataframe) * 100).round(1).values,
    })
    st.dataframe(summary, use_container_width=True)


def display_statistics(dataframe: pd.DataFrame):
    st.subheader("Descriptive Statistics")
    numeric_data = dataframe.select_dtypes(include="number")
    if numeric_data.empty:
        st.info("No numeric columns are available for statistics.")
        return
    st.dataframe(numeric_data.describe(), use_container_width=True)


def display_exploration(dataframe: pd.DataFrame):
    st.subheader("Quick Exploration")
    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
    if not numeric_columns:
        st.info("No numeric columns are available for visualisation.")
        return
    selected_column = st.selectbox("Select a column to visualise", numeric_columns)
    st.bar_chart(dataframe[selected_column].value_counts().head(20))

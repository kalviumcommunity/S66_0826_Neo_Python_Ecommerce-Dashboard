import pandas as pd
import streamlit as st


def apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar controls and return the filtered DataFrame."""
    st.sidebar.header("Filters")
    filtered_df = dataframe.copy()

    date_columns = [
        column for column in dataframe.columns
        if "date" in column.lower()
    ]
    if date_columns:
        date_column = date_columns[0]
        parsed_dates = pd.to_datetime(
            filtered_df[date_column], errors="coerce"
        )
        valid_dates = parsed_dates.dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_range = st.sidebar.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if len(date_range) == 2:
                filtered_df = filtered_df[
                    (parsed_dates >= pd.Timestamp(date_range[0]))
                    & (parsed_dates <= pd.Timestamp(date_range[1]))
                ]

    segment_columns = [
        column for column in dataframe.columns
        if column.lower() == "segment"
    ]
    if segment_columns:
        segment_column = segment_columns[0]
        segments = sorted(
            filtered_df[segment_column].dropna().unique().tolist()
        )
        selected_segments = st.sidebar.multiselect(
            "Segments",
            options=segments,
            default=segments,
        )
        filtered_df = filtered_df[
            filtered_df[segment_column].isin(selected_segments)
        ]

    revenue_columns = [
        column for column in dataframe.columns
        if column.lower() in {"revenue", "sales", "amount"}
    ]
    if revenue_columns:
        revenue_column = revenue_columns[0]
        revenue_values = pd.to_numeric(
            filtered_df[revenue_column], errors="coerce"
        ).dropna()
        if not revenue_values.empty:
            min_revenue = int(revenue_values.min())
            max_revenue = int(revenue_values.max())
            if min_revenue < max_revenue:
                revenue_range = st.sidebar.slider(
                    "Revenue Range",
                    min_value=min_revenue,
                    max_value=max_revenue,
                    value=(min_revenue, max_revenue),
                )
                numeric_revenue = pd.to_numeric(
                    filtered_df[revenue_column], errors="coerce"
                )
                filtered_df = filtered_df[
                    numeric_revenue.between(
                        revenue_range[0], revenue_range[1]
                    )
                ]
            else:
                st.sidebar.caption(f"Revenue: {min_revenue}")

    if st.sidebar.button("Reset Filters"):
        st.rerun()

    return filtered_df

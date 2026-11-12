import sqlite3

import pandas as pd
import streamlit as st
import plotly.express as px

from database import (
    init_db,
    add_application,
    get_applications,
    update_application_status,
    delete_application,
)
st.set_page_config(
    page_title="Placement Tracker",
    page_icon="📋",
    layout="wide",
)

init_db()

st.title("Placement & Internship Tracker")
st.write("Track your applications, interviews, and offers in one place.")

# Successful save ka message rerun ke baad bhi dikhayenge.
if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))

applications = get_applications()

col1, col2, col3 = st.columns(3)

col1.metric("Total Applications", len(applications))
col2.metric(
    "Interviews",
    sum(app["status"] == "Interview" for app in applications),
)
col3.metric(
    "Offers",
    sum(app["status"] == "Offer" for app in applications),
)

st.divider()
st.subheader("Add an Application")

with st.form("application_form", clear_on_submit=False):
    company = st.text_input("Company Name", max_chars=100)
    role = st.text_input("Job / Internship Role", max_chars=150)

    status = st.selectbox(
        "Application Status",
        ["Applied", "Online Test", "Interview", "Offer", "Rejected"],
    )

    deadline = st.date_input("Application Deadline")
    submitted = st.form_submit_button("Add Application")

if submitted:
    if not company.strip() or not role.strip():
        st.error("Please enter both the company name and role.")
    else:
        try:
            add_application(
                company.strip(),
                role.strip(),
                status,
                deadline.isoformat(),
            )
        except sqlite3.Error:
            st.error("Could not save the application. Please try again.")
        else:
            st.session_state["success_message"] = (
                f"Application saved: {role.strip()} at {company.strip()}"
            )
            st.rerun()

st.divider()
st.subheader("Saved Applications")

if applications:
    df = pd.DataFrame(applications)
    df = df.rename(columns={
        "id": "ID",
        "company": "Company",
        "role": "Role",
        "status": "Status",
        "deadline": "Deadline",
        "created_at": "Created At",
    })

    st.dataframe(df, hide_index=True, width="stretch")
    st.caption(
        "Form values stay filled after saving. "
        "Change them before adding another application."
    )
else:
    st.info("No applications yet. Add your first one above.")
    st.divider()
st.subheader("Manage an Application")

if applications:
    application_map = {app["id"]: app for app in applications}

    selected_id = st.selectbox(
        "Choose an application",
        options=list(application_map),
        format_func=lambda app_id: (
            f"#{app_id} | {application_map[app_id]['company']} | "
            f"{application_map[app_id]['role']} | "
            f"{application_map[app_id]['status']}"
        ),
    )

    selected_app = application_map[selected_id]
    statuses = ["Applied", "Online Test", "Interview", "Offer", "Rejected"]

    with st.form(f"update_status_{selected_id}"):
        new_status = st.selectbox(
            "New Status",
            options=statuses,
            index=statuses.index(selected_app["status"]),
        )
        update_clicked = st.form_submit_button("Update Status")

    if update_clicked:
        try:
            changed = update_application_status(selected_id, new_status)
        except sqlite3.Error:
            st.error("Could not update the status. Please try again.")
        else:
            if changed:
                st.session_state["success_message"] = (
                    f"Application #{selected_id} updated to {new_status}."
                )
                st.rerun()
            else:
                st.warning("This application no longer exists. Refresh the page.")

    with st.expander("Delete selected application"):
        st.warning(
            f"You are deleting #{selected_id}: "
            f"{selected_app['role']} at {selected_app['company']}. "
            "This cannot be undone."
        )

        confirmed = st.checkbox(
            "I confirm I want to delete this application.",
            key=f"confirm_delete_{selected_id}",
        )

        if st.button(
            "Delete Application",
            disabled=not confirmed,
            key=f"delete_{selected_id}",
        ):
            try:
                deleted = delete_application(selected_id)
            except sqlite3.Error:
                st.error("Could not delete the application. Please try again.")
            else:
                if deleted:
                    st.session_state["success_message"] = (
                        f"Application #{selected_id} deleted."
                    )
                    st.rerun()
                else:
                    st.warning(
                        "This application no longer exists. Refresh the page."
                    )
else:
    st.info("Add an application first to manage it.")
st.divider()
st.subheader("Application Insights")

if applications:
    insights_df = pd.DataFrame(applications)

    search_col, filter_col = st.columns(2)

    with search_col:
        search_text = st.text_input(
            "Search company or role",
            placeholder="Example: Infosys or Python",
        )

    with filter_col:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Applied", "Online Test", "Interview", "Offer", "Rejected"],
        )

    filtered_df = insights_df.copy()

    # literal search: special characters are treated as normal text.
    if search_text.strip():
        query = search_text.strip()
        matches = (
            filtered_df["company"].str.contains(
                query, case=False, regex=False, na=False
            )
            | filtered_df["role"].str.contains(
                query, case=False, regex=False, na=False
            )
        )
        filtered_df = filtered_df[matches]

    if status_filter != "All":
        filtered_df = filtered_df[
            filtered_df["status"] == status_filter
        ]

    st.caption(
        f"Showing {len(filtered_df)} of {len(insights_df)} applications. "
        "The top counters always show all applications."
    )

    if filtered_df.empty:
        st.info("No applications match your search and filter.")
    else:
        st.dataframe(
            filtered_df[["id", "company", "role", "status", "deadline"]],
            hide_index=True,
            width="stretch",
        )

        status_counts = (
            filtered_df.groupby("status")
            .size()
            .reset_index(name="Applications")
        )

        chart = px.bar(
            status_counts,
            x="status",
            y="Applications",
            color="status",
            text="Applications",
            title="Applications by Current Status",
        )

        chart.update_layout(
            xaxis_title="Status",
            yaxis_title="Number of Applications",
            showlegend=False,
        )
        chart.update_yaxes(dtick=1)

        st.plotly_chart(chart, width="stretch")
else:
    st.info("Add an application to see insights.")
st.divider()
st.subheader("Upcoming Application Deadlines")
st.caption(
    "Deadlines for Applied applications only. "
    "These are application deadlines, not interview dates."
)

if applications:
    deadline_df = pd.DataFrame(applications)

    deadline_df["deadline"] = pd.to_datetime(
        deadline_df["deadline"], errors="coerce"
    )

    today = pd.Timestamp.today().normalize()

    deadline_df["days_left"] = (
        deadline_df["deadline"] - today
    ).dt.days

    upcoming = deadline_df[
        (deadline_df["status"] == "Applied")
        & (deadline_df["days_left"] >= 0)
        & (deadline_df["days_left"] <= 7)
    ].sort_values("deadline")

    if upcoming.empty:
        st.info("No Applied applications have deadlines in the next 7 days.")
    else:
        st.warning(
            f"{len(upcoming)} application(s) have deadlines "
            "today or within the next 7 days."
        )

        display_df = upcoming[
            ["company", "role", "deadline", "days_left"]
        ].copy()

        display_df["deadline"] = (
            display_df["deadline"].dt.strftime("%d %b %Y")
        )

        display_df = display_df.rename(columns={
            "company": "Company",
            "role": "Role",
            "deadline": "Deadline",
            "days_left": "Days Left",
        })

        st.dataframe(
            display_df,
            hide_index=True,
            width="stretch",
        )
else:
    st.info("Add an application to track deadlines.")        
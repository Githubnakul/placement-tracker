from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Placement Tracker Demo", layout="wide")

STATUSES = ["Applied", "Online Test", "Interview", "Offer", "Rejected"]

# Session State is separate for each browser session.
if "demo_applications" not in st.session_state:
    st.session_state.demo_applications = [
        {
            "id": 1,
            "company": "DemoTech",
            "role": "Python Intern",
            "status": "Applied",
            "deadline": (date.today() + timedelta(days=3)).isoformat(),
        },
        {
            "id": 2,
            "company": "Example Labs",
            "role": "Backend Intern",
            "status": "Interview",
            "deadline": (date.today() + timedelta(days=5)).isoformat(),
        },
        {
            "id": 3,
            "company": "SampleSoft",
            "role": "Developer Intern",
            "status": "Offer",
            "deadline": (date.today() + timedelta(days=7)).isoformat(),
        },
    ]
    st.session_state.demo_next_id = 4

apps = st.session_state.demo_applications

st.title("Placement & Internship Tracker")
st.info(
    "Interactive demo with fictional data. Changes stay in this browser "
    "session, not in a shared database. Do not enter personal information."
)

if "demo_message" in st.session_state:
    st.success(st.session_state.pop("demo_message"))

a, b, c = st.columns(3)
a.metric("Applications", len(apps))
b.metric("Interviews", sum(x["status"] == "Interview" for x in apps))
c.metric("Offers", sum(x["status"] == "Offer" for x in apps))

st.subheader("Add an Application")

with st.form("demo_add", clear_on_submit=True):
    company = st.text_input("Company", max_chars=100)
    role = st.text_input("Role", max_chars=150)
    status = st.selectbox("Status", STATUSES)
    deadline = st.date_input("Application Deadline")
    submitted = st.form_submit_button("Add Application")

if submitted:
    if not company.strip() or not role.strip():
        st.error("Company and role are required.")
    elif len(apps) >= 100:
        st.warning("This demo allows up to 100 entries per session.")
    else:
        apps.append({
            "id": st.session_state.demo_next_id,
            "company": company.strip(),
            "role": role.strip(),
            "status": status,
            "deadline": deadline.isoformat(),
        })
        st.session_state.demo_next_id += 1
        st.session_state.demo_message = "Application added."
        st.rerun()

st.subheader("Search and Insights")
search = st.text_input("Search company or role")
status_filter = st.selectbox("Filter by status", ["All"] + STATUSES)

visible = [
    x for x in apps
    if (
        search.strip().lower() in x["company"].lower()
        or search.strip().lower() in x["role"].lower()
    )
    and (status_filter == "All" or x["status"] == status_filter)
]

st.caption(f"Showing {len(visible)} of {len(apps)} applications.")

if visible:
    df = pd.DataFrame(visible)
    st.dataframe(df, hide_index=True, width="stretch")
    counts = df.groupby("status").size().reset_index(name="Applications")
    chart = px.bar(
        counts, x="status", y="Applications", color="status",
        text="Applications", title="Applications by Current Status",
    )
    chart.update_yaxes(dtick=1)
    st.plotly_chart(chart, width="stretch")
else:
    st.info("No matching applications.")

st.subheader("Manage an Application")

if apps:
    by_id = {x["id"]: x for x in apps}
    selected_id = st.selectbox(
        "Select application",
        options=list(by_id),
        format_func=lambda i: (
            f"#{i} | {by_id[i]['company']} | {by_id[i]['role']}"
        ),
    )
    selected = by_id[selected_id]

    with st.form(f"demo_update_{selected_id}"):
        new_status = st.selectbox(
            "New Status", STATUSES,
            index=STATUSES.index(selected["status"]),
        )
        if st.form_submit_button("Update Status"):
            selected["status"] = new_status
            st.session_state.demo_message = "Status updated."
            st.rerun()

    with st.expander("Delete selected application"):
        st.warning(
            f"Delete #{selected_id}: {selected['company']} "
            f"— {selected['role']}?"
        )
        confirm = st.checkbox(
            "Confirm deletion", key=f"demo_confirm_{selected_id}"
        )
        if st.button("Delete", disabled=not confirm):
            st.session_state.demo_applications = [
                x for x in apps if x["id"] != selected_id
            ]
            st.session_state.demo_message = "Application deleted."
            st.rerun()

st.subheader("Upcoming Application Deadlines")
upcoming = []

for app in apps:
    days_left = (date.fromisoformat(app["deadline"]) - date.today()).days
    if app["status"] == "Applied" and 0 <= days_left <= 7:
        upcoming.append({**app, "days_left": days_left})

if upcoming:
    st.dataframe(
        pd.DataFrame(upcoming).sort_values("days_left"),
        hide_index=True,
        width="stretch",
    )
else:
    st.info("No Applied applications have deadlines in the next 7 days.")
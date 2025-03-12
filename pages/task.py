import datetime
import json
import os

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set up authentication with Google Tasks API
SCOPES = ["https://www.googleapis.com/auth/tasks.readonly"]


def authenticate_google_api():
    """Authenticate with Google API and return the service."""
    creds = None

    # Check if token.json exists (for stored credentials)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_info(
            json.loads(open("token.json").read()), SCOPES
        )

    # If credentials don't exist or are invalid, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build and return the service
    return build("tasks", "v1", credentials=creds)


def get_task_lists(service):
    """Get all task lists."""
    results = service.tasklists().list().execute()
    return results.get("items", [])


def get_tasks(service, task_list_id):
    """Get all tasks from a task list."""
    results = (
        service.tasks()
        .list(tasklist=task_list_id, showCompleted=True, showHidden=True)
        .execute()
    )
    return results.get("items", [])


def process_tasks(all_tasks, all_lists):
    """Process tasks into a pandas DataFrame."""
    # Create a mapping of list IDs to names
    list_names = {lst["id"]: lst["title"] for lst in all_lists}

    data = []
    for list_id, tasks in all_tasks.items():
        list_name = list_names.get(list_id, "Unknown")

        for task in tasks:
            # Skip tasks without titles (sometimes happens with deleted tasks)
            if "title" not in task:
                continue

            # Process dates
            due_date = None
            if "due" in task:
                due_date = task["due"].split("T")[0]  # Extract just the date part

            completed_date = None
            if "completed" in task:
                completed_date = task["completed"].split("T")[0]

            # Calculate task status
            if "completed" in task and task.get("completed"):
                status = "Completed"
            elif (
                "due" in task
                and datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                < datetime.date.today()
            ):
                status = "Overdue"
            else:
                status = "Active"

            # Add to data
            data.append(
                {
                    "task_id": task.get("id", ""),
                    "title": task.get("title", ""),
                    "list_name": list_name,
                    "list_id": list_id,
                    "status": status,
                    "due_date": due_date,
                    "completed_date": completed_date,
                    "notes": task.get("notes", ""),
                    "created": task.get("updated", ""),
                }
            )

    return pd.DataFrame(data)


def create_dashboard(df):
    """Create a Streamlit dashboard to visualize task data."""
    st.set_page_config(page_title="Google Tasks Dashboard", layout="wide")

    st.title("Google Tasks Dashboard")

    # Sidebar filters
    st.sidebar.header("Filters")

    # Filter by task list
    lists = ["All"] + sorted(df["list_name"].unique().tolist())
    selected_list = st.sidebar.selectbox("Select Task List", lists)

    # Filter by status
    statuses = ["All"] + sorted(df["status"].unique().tolist())
    selected_status = st.sidebar.selectbox("Select Status", statuses)

    # Apply filters
    filtered_df = df.copy()
    if selected_list != "All":
        filtered_df = filtered_df[filtered_df["list_name"] == selected_list]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

    # Create dashboard sections
    col1, col2 = st.columns(2)

    # Tasks by status
    with col1:
        st.subheader("Tasks by Status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig = px.pie(
            status_counts,
            values="Count",
            names="Status",
            title="Task Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig)

    # Tasks by list
    with col2:
        st.subheader("Tasks by List")
        list_counts = df["list_name"].value_counts().reset_index()
        list_counts.columns = ["List", "Count"]

        fig = px.bar(
            list_counts,
            x="List",
            y="Count",
            title="Tasks per List",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig)

    # Task completion over time
    st.subheader("Task Completion Over Time")

    # Convert date columns to datetime
    df_time = df.copy()
    df_time["completed_date"] = pd.to_datetime(df_time["completed_date"])
    df_time["due_date"] = pd.to_datetime(df_time["due_date"])

    # Group by completion date and count
    completed_over_time = df_time.dropna(subset=["completed_date"])
    completed_over_time = (
        completed_over_time.groupby(completed_over_time["completed_date"].dt.date)
        .size()
        .reset_index()
    )
    completed_over_time.columns = ["Date", "Completed Tasks"]

    # Create the line chart
    if not completed_over_time.empty:
        fig = px.line(
            completed_over_time,
            x="Date",
            y="Completed Tasks",
            title="Tasks Completed Over Time",
            markers=True,
        )
        st.plotly_chart(fig)
    else:
        st.write("No completion data available")

    # Upcoming tasks
    st.subheader("Upcoming Tasks")
    upcoming_tasks = df[
        (df["status"] == "Active") & (df["due_date"].notna())
    ].sort_values("due_date")

    if not upcoming_tasks.empty:
        upcoming_tasks_display = upcoming_tasks[
            ["title", "list_name", "due_date"]
        ].head(10)
        st.table(upcoming_tasks_display)
    else:
        st.write("No upcoming tasks with due dates")

    # Tasks table
    st.subheader("Task List")
    if not filtered_df.empty:
        # Select and reorder columns for display
        display_cols = ["title", "list_name", "status", "due_date", "completed_date"]
        st.dataframe(filtered_df[display_cols])
    else:
        st.write("No tasks match the selected filters")


def main():
    try:
        # Authenticate and get service
        service = authenticate_google_api()

        # Get all task lists
        task_lists = get_task_lists(service)

        if not task_lists:
            st.error("No task lists found!")
            return

        # Get tasks from each task list
        all_tasks = {}
        for task_list in task_lists:
            tasks = get_tasks(service, task_list["id"])
            all_tasks[task_list["id"]] = tasks

        # Process tasks into DataFrame
        df = process_tasks(all_tasks, task_lists)

        # Create dashboard
        create_dashboard(df)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()

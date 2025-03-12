import datetime
import os
from typing import Any

import dotenv
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from todoist_api_python.api import TodoistAPI

from components.page_config import PageConfig

dotenv.load_dotenv()

PageConfig().get_config()

TODOIST_API_TOKEN: str | None = os.getenv("TODOIST_API_TOKEN")


def authenticate_todoist_api() -> TodoistAPI | None:
    """Authenticate with Todoist API and return the API client."""
    # Get API token from secrets or let user input it
    if "todoist_api_token" in st.session_state:
        api_token = st.session_state["todoist_api_token"]
    elif TODOIST_API_TOKEN:
        api_token = TODOIST_API_TOKEN
    else:
        api_token = st.text_input(
            "Enter your Todoist API token (find it in Todoist Settings > Integrations)",
            type="password",
        )
        if api_token:
            st.session_state["todoist_api_token"] = api_token
        else:
            st.warning("Please enter your Todoist API token to continue.")
            return None

    # Create and return the API client
    return TodoistAPI(api_token)


def get_projects(api: TodoistAPI) -> list[Any]:
    """Get all projects."""
    try:
        return api.get_projects()
    except Exception as e:
        st.error(f"Error fetching projects: {str(e)}")
        return []


def get_tasks(api: TodoistAPI, project_id: str | None = None) -> list[Any]:
    """Get all tasks, optionally filtered by project_id."""
    try:
        if project_id:
            return api.get_tasks(project_id=project_id)
        else:
            return api.get_tasks()
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return []


@st.cache_data
def process_tasks(all_tasks: list[Any], all_projects: list[Any]) -> pd.DataFrame:
    """Process tasks into a pandas DataFrame."""

    # Create a mapping of project IDs to names.
    project_names = {project.id: project.name for project in all_projects}

    data: list[dict[str, Any]] = []
    for task in all_tasks:

        # Process dates.
        due_date: str | None = None
        if task.due:
            due_date = task.due.date

        completed_date = None
        if hasattr(task, "completed_at") and task.completed_at:
            completed_date = task.completed_at.split("T")[0]

        # Calculate task status.
        if task.is_completed:
            status = "Completed"
        elif (
            due_date
            and datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
            < datetime.date.today()
        ):
            status = "Overdue"
        else:
            status = "Active"

        # Add to data.
        data.append(
            {
                "task_id": task.id,
                "title": task.content,
                "project_name": project_names.get(task.project_id, "Unknown"),
                "project_id": task.project_id,
                "status": status,
                "due_date": due_date,
                "completed_date": completed_date,
                "description": task.description if hasattr(task, "description") else "",
                "priority": task.priority,
                "created": task.created_at if hasattr(task, "created_at") else "",
            }
        )

    return pd.DataFrame(data)


def create_dashboard(df: pd.DataFrame) -> None:
    """Create a Streamlit dashboard to visualize task data."""
    st.title("Todoist tasks")

    # Sidebar filters.
    st.sidebar.header("Filters")

    # Filter by project.
    projects = ["All"] + sorted(df["project_name"].unique().tolist())
    selected_project = st.sidebar.selectbox("Select Project", projects)

    # Filter by status.
    statuses = ["All"] + sorted(df["status"].unique().tolist())
    selected_status = st.sidebar.selectbox("Select Status", statuses)

    # Filter by priority.
    priorities = ["All", "1 (Highest)", "2 (High)", "3 (Medium)", "4 (Low)"]
    selected_priority = st.sidebar.selectbox("Select Priority", priorities)

    # Apply filters.
    filtered_df = df.copy()
    if selected_project != "All":
        filtered_df = filtered_df[filtered_df["project_name"] == selected_project]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]
    if selected_priority != "All":
        priority_value = 5 - priorities.index(
            selected_priority
        )  # Convert to Todoist priority (4=p1, 3=p2, 2=p3, 1=p4)
        filtered_df = filtered_df[filtered_df["priority"] == priority_value]

    # Create dashboard sections.
    col1, col2 = st.columns(2)

    # Tasks by status.
    with col1:
        st.subheader("Tasks by status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig = px.pie(
            status_counts,
            values="Count",
            names="Status",
            title="Task status distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig)

    # Tasks by project.
    with col2:
        st.subheader("Tasks by project")
        project_counts = df["project_name"].value_counts().reset_index()
        project_counts.columns = ["Project", "Count"]

        fig = px.bar(
            project_counts,
            x="Project",
            y="Count",
            title="Tasks per Project",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig)

    # Tasks by priority.
    st.subheader("Tasks by priority")
    priority_map = {4: "1 (Highest)", 3: "2 (High)", 2: "3 (Medium)", 1: "4 (Low)"}
    df_priority = df.copy()
    df_priority["priority_label"] = df_priority["priority"].map(priority_map)
    priority_counts = df_priority["priority_label"].value_counts().reset_index()
    priority_counts.columns = ["Priority", "Count"]

    # Sort by priority.
    priority_order = ["1 (Highest)", "2 (High)", "3 (Medium)", "4 (Low)"]
    priority_counts["Priority"] = pd.Categorical(
        priority_counts["Priority"], categories=priority_order, ordered=True
    )
    priority_counts = priority_counts.sort_values("Priority")

    fig = px.bar(
        priority_counts,
        x="Priority",
        y="Count",
        title="Tasks by Priority",
        color="Priority",
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    st.plotly_chart(fig)

    # Task completion over time (if data available)
    st.subheader("Task Completion Over Time")

    # Convert date columns to datetime
    df_time = df.copy()
    df_time["completed_date"] = pd.to_datetime(df_time["completed_date"])
    df_time["due_date"] = pd.to_datetime(df_time["due_date"])

    # Group by completion date and count
    completed_over_time = df_time.dropna(subset=["completed_date"])
    if not completed_over_time.empty:
        completed_over_time = (
            completed_over_time.groupby(completed_over_time["completed_date"].dt.date)
            .size()
            .reset_index()
        )
        completed_over_time.columns = ["Date", "Completed Tasks"]

        # Create the line chart
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
            ["title", "project_name", "due_date", "priority"]
        ].head(10)
        # Convert priority to readable format
        upcoming_tasks_display["priority"] = upcoming_tasks_display["priority"].map(
            priority_map
        )
        st.table(upcoming_tasks_display)
    else:
        st.write("No upcoming tasks with due dates")

    # Tasks table
    st.subheader("Task List")
    if not filtered_df.empty:
        # Select and reorder columns for display
        display_cols = ["title", "project_name", "status", "due_date", "priority"]
        display_df = filtered_df[display_cols].copy()
        display_df["priority"] = display_df["priority"].map(priority_map)
        st.dataframe(display_df)
    else:
        st.write("No tasks match the selected filters")


def main() -> None:
    try:
        # Authenticate and get API client.
        api = authenticate_todoist_api()

        if api:
            # Get all projects.
            projects = get_projects(api)

            if not projects:
                st.warning("No projects found in your Todoist account.")
                return

            # Get all tasks.
            tasks = get_tasks(api)

            if not tasks:
                st.warning("No tasks found in your Todoist account.")
                return

            # Process tasks into DataFrame.
            df = process_tasks(tasks, projects)

            # Create dashboard
            create_dashboard(df)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()

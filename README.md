# Streamlit template

## Start locally

1. Clone this repo

   ```shell
   git clone https://github.com/xcollantes/streamlit-template
   ```

1. Download dependencies:

   ```shell
   python3 -m venv env
   env/bin/pip install -r requirements.txt
   ```

1. Create `.streamlit/secrets.toml` file with API keys

1. Start locally:

   ```shell
   env/bin/streamlit run Home.py
   ```

## Adding a new page

The Home page is `Home.py` which is accessed at `http://localhost`.

Subsequent pages can be nested under the `pages/` directory and accessed:

`pages/drops.py` -> `http://localhost/drops`

1. Add page as file in `pages/`.
1. Add page name and title to `deps/Home.py`.

## Todoist Dashboard

This application includes a Todoist task visualization dashboard that allows you
to:

1. View your Todoist tasks in an interactive dashboard
2. Filter tasks by project, status, and priority
3. See visualizations of task distribution by status, project, and priority
4. Track task completion over time
5. View upcoming tasks with due dates

### Setup for Todoist Integration

To use the Todoist dashboard:

1. You'll need a Todoist account and API token
2. Get your API token from Todoist: Settings > Integrations > Developer > API
   token 
3. When you open the Todoist Dashboard page, you'll be prompted to enter your
   API token
4. Your token will be stored in the session state (not permanently saved)

### Privacy Note

Your Todoist API token is only stored in your browser's session and is not saved
on any server. The application only reads your Todoist data and does not modify
any tasks.

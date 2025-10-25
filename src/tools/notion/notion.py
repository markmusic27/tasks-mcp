import logging
import os
from typing import Literal
from notion_client import Client
from auth import load_env_from_file
from .utils import build_date_filter, retrieve_course_info, retrieve_project_info, retrieve_task_info

def get_notion_client():
    # Try to read from environment first
    token = os.environ.get("NOTION_AUTH_TOKEN")
    if not token:
        # Attempt to load from .env lazily if not already loaded
        load_env_from_file()
        token = os.environ.get("NOTION_AUTH_TOKEN")
    if not token:
        raise RuntimeError("NOTION_AUTH_TOKEN is not set. Add it to your environment or .env")
    return Client(auth=token, log_level=logging.WARNING)

def get_databases() -> dict[str, str]:
    """
    Load and return all required Notion database IDs.
    
    Returns:
        A dict with keys: 'tasks', 'projects', 'courses'
        
    Raises:
        RuntimeError: If any required database ID is not set
    """
    # Try to read from environment first, then load .env if needed
    task_db = os.environ.get("TASK_DATABASE")
    project_db = os.environ.get("PROJECT_DATABASE")
    course_db = os.environ.get("COURSE_DATABASE")
    
    if not task_db or not project_db or not course_db:
        load_env_from_file()
        task_db = os.environ.get("TASK_DATABASE")
        project_db = os.environ.get("PROJECT_DATABASE")
        course_db = os.environ.get("COURSE_DATABASE")
    
    # Collect missing database IDs
    missing = []
    if not task_db:
        missing.append("TASK_DATABASE")
    if not project_db:
        missing.append("PROJECT_DATABASE")
    if not course_db:
        missing.append("COURSE_DATABASE")
    
    if missing:
        raise RuntimeError(
            f"Missing required database IDs: {', '.join(missing)}. "
            "Add them to your environment or .env file"
        )
    
    return {
        "tasks": task_db,
        "projects": project_db,
        "courses": course_db
    }

def get_tasks_data_source_id():
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["tasks"]
    
    try:
        dbs = client.databases.retrieve(database_id)
        
        db = dbs["data_sources"][0]
        
        return db["id"]
    except Exception as e:
        print(f"An error occurred while retrieving database information: {e}")
        # raise TODO: handle this

def get_projects_data_source_id():
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["projects"]
    
    try:
        dbs = client.databases.retrieve(database_id)
        
        db = dbs["data_sources"][0]
        
        return db["id"]
    except Exception as e:
        print(f"An error occurred while retrieving database information: {e}")
        # raise TODO: handle this

def get_courses_data_source_id():
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["courses"]
    
    try:
        dbs = client.databases.retrieve(database_id)
        
        db = dbs["data_sources"][0]
        
        return db["id"]
    except Exception as e:
        print(f"An error occurred while retrieving database information: {e}")
        # raise TODO: handle this


def get_tasks(time_range: str):
    """
    Get tasks for the specified time range with "Not Started" status.
    
    Args:
        time_range: One of "today", "tomorrow", or "this week". Defaults to "today".
        
    Returns:
        Query results from Notion API
    """
    client = get_notion_client()
    id = get_tasks_data_source_id()
    
    # Build date filter for the specified time range
    date_filter = build_date_filter(time_range)
    
    # Combine status filter with date filter
    filter_conditions = {
        "and": [
            {
                "property": "Status",
                "status": {
                    "equals": "Not Started"
                }
            },
            *date_filter["and"]  # Unpack the date filter conditions
        ]
    }
    
    res = client.data_sources.query(id, filter=filter_conditions)
    
    list = res["results"]
    
    if len(list) == 0:
        return []
    
    return [retrieve_task_info(task) for task in list]
    
def get_projects():
    client = get_notion_client()
    id = get_projects_data_source_id()
    
    res = client.data_sources.query(
        id,
        filter={
            "property": "Status",
            "status": {
                "equals": "Active"
            }
        }
    )
    
    return [retrieve_project_info(project) for project in res["results"]]

def get_courses():
    client = get_notion_client()
    id = get_courses_data_source_id()
    
    res = client.data_sources.query(
        id,
        filter={
            "property": "Status",
            "status": {
                "equals": "In progress"
            }
        }
    )
    
    return [retrieve_course_info(course) for course in res["results"]]
    
    


def register_all() -> None:
    # register_tool(get_alerts_spec, get_alerts_handler)
    # register_tool(get_forecast_spec, get_forecast_handler)
    pass
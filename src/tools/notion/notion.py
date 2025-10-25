import logging
import os
from typing import Literal, TypedDict, Optional
from notion_client import Client
from auth import load_env_from_file
from .utils import build_date_filter, check_if_projects_or_courses_exist, get_priority_name, retrieve_course_info, retrieve_project_info, retrieve_task_info

class CreateTaskParams(TypedDict, total=False):
    """Parameters for creating a task in Notion."""
    title: str  # Required
    due_date: str  # Required
    priority: int  # Required
    body: Optional[str]
    project_id: Optional[str]
    course_id: Optional[str]

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
    
    if len(res["results"]) == 0:
        return []
    
    tasks = [retrieve_task_info(task) for task in res["results"]]
    
    # add project and course to tasks
    if not check_if_projects_or_courses_exist(tasks):
        return tasks
    
    projects = get_projects()
    courses = get_courses()
    
    for task in tasks:
        if task["project"] is not None:
            task["project"] = next((p for p in projects if p["id"] == task["project"]), None)
        if task["course"] is not None:
            task["course"] = next((c for c in courses if c["id"] == task["course"]), None)
    
    return tasks

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

def create_task(params: CreateTaskParams):
    """
    Create a task in Notion.
    
    Args:
        params: Dictionary containing task parameters:
    
    Returns:
        The created page response from Notion API
    """
    client = get_notion_client()
    database_id = get_databases()["tasks"]
    
    # Extract parameters
    title = params["title"]
    due_date = params["due_date"]
    priority = get_priority_name(params["priority"])
    body = params.get("body")
    project_id = params.get("project_id")
    course_id = params.get("course_id")
    
    # Build properties for the page
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        },
        "Priority": {
            "select": {
                "name": priority
            }
        },
        "Due Date": {
            "date": {
                "start": due_date
            }
        }
    }
    
    # Add project relation if provided
    if project_id:
        properties["Project"] = {
            "relation": [{"id": project_id}]
        }
    
    # Add course relation if provided
    if course_id:
        properties["Course"] = {
            "relation": [{"id": course_id}]
        }
    
    # Build the page object
    page_data = {
        "parent": {"database_id": database_id},
        "icon": {
            "type": "external",
            "external": {
                "url": "https://www.notion.so/icons/circle_gray.svg?mode=dark"
            }
        },
        "properties": properties
        
    }
    
    res = client.pages.create(**page_data)
    
    return res

def register_all() -> None:
    # register_tool(get_alerts_spec, get_alerts_handler)
    # register_tool(get_forecast_spec, get_forecast_handler)
    pass
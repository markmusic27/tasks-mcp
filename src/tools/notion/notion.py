import logging
import os
from typing import Any, TypedDict, Optional
from notion_client import Client
import mcp.types as types
from auth import load_env_from_file
from tools.registry import register_tool
from .utils import build_date_filter, check_if_projects_or_courses_exist, get_priority_name, retrieve_course_info, retrieve_project_info, retrieve_task_info

logger = logging.getLogger(__name__)

class CreateTaskParams(TypedDict, total=False):
    """Parameters for creating a task in Notion."""
    title: str  # Required
    due_date: str  # Required
    priority: int  # Required
    project_id: Optional[str]
    course_id: Optional[str]

def get_notion_client() -> Client:
    """Create and return a configured Notion client.

    Raises:
        RuntimeError: When the Notion auth token is not present
    """
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

def get_tasks_data_source_id() -> str:
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["tasks"]

    try:
        dbs = client.databases.retrieve(database_id)
        data_sources = dbs.get("data_sources")
        if not data_sources or not isinstance(data_sources, list):
            raise RuntimeError("Tasks database has no data_sources in Notion response")
        first = data_sources[0]
        ds_id = first.get("id")
        if not ds_id:
            raise RuntimeError("Tasks data source id missing from Notion response")
        return ds_id
    except Exception as e:
        logger.exception("Failed to retrieve tasks data source id")
        raise RuntimeError(f"Failed to retrieve tasks data source id: {e}")

def get_projects_data_source_id() -> str:
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["projects"]

    try:
        dbs = client.databases.retrieve(database_id)
        data_sources = dbs.get("data_sources")
        if not data_sources or not isinstance(data_sources, list):
            raise RuntimeError("Projects database has no data_sources in Notion response")
        first = data_sources[0]
        ds_id = first.get("id")
        if not ds_id:
            raise RuntimeError("Projects data source id missing from Notion response")
        return ds_id
    except Exception as e:
        logger.exception("Failed to retrieve projects data source id")
        raise RuntimeError(f"Failed to retrieve projects data source id: {e}")

def get_courses_data_source_id() -> str:
    client = get_notion_client()
    databases = get_databases()
    database_id = databases["courses"]

    try:
        dbs = client.databases.retrieve(database_id)
        data_sources = dbs.get("data_sources")
        if not data_sources or not isinstance(data_sources, list):
            raise RuntimeError("Courses database has no data_sources in Notion response")
        first = data_sources[0]
        ds_id = first.get("id")
        if not ds_id:
            raise RuntimeError("Courses data source id missing from Notion response")
        return ds_id
    except Exception as e:
        logger.exception("Failed to retrieve courses data source id")
        raise RuntimeError(f"Failed to retrieve courses data source id: {e}")


def get_tasks(time_range: str) -> list[dict]:
    """
    Get tasks for the specified time range with "Not Started" status.
    
    Args:
        time_range: One of "today", "tomorrow", or "week_from_today" (synonyms like "this week" are accepted).
        
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
            *date_filter["and"]
        ]
    }

    try:
        res = client.data_sources.query(id, filter=filter_conditions)
    except Exception as e:
        logger.exception("Failed to query tasks from Notion")
        raise RuntimeError(f"Failed to query tasks: {e}")

    results = res.get("results")
    if results is None:
        raise RuntimeError("Malformed Notion response: missing 'results' for tasks query")
    if len(results) == 0:
        return []

    tasks = [retrieve_task_info(task) for task in results]

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

def get_projects() -> list[dict]:
    client = get_notion_client()
    id = get_projects_data_source_id()

    try:
        res = client.data_sources.query(
            id,
            filter={
                "property": "Status",
                "status": {
                    "equals": "Active"
                }
            }
        )
    except Exception as e:
        logger.exception("Failed to query projects from Notion")
        raise RuntimeError(f"Failed to query projects: {e}")

    results = res.get("results")
    if results is None:
        raise RuntimeError("Malformed Notion response: missing 'results' for projects query")

    return [retrieve_project_info(project) for project in results]

def get_courses() -> list[dict]:
    client = get_notion_client()
    id = get_courses_data_source_id()

    try:
        res = client.data_sources.query(
            id,
            filter={
                "property": "Status",
                "status": {
                    "equals": "In progress"
                }
            }
        )
    except Exception as e:
        logger.exception("Failed to query courses from Notion")
        raise RuntimeError(f"Failed to query courses: {e}")

    results = res.get("results")
    if results is None:
        raise RuntimeError("Malformed Notion response: missing 'results' for courses query")

    return [retrieve_course_info(course) for course in results]

def create_task(params: CreateTaskParams) -> str:
    """
    Create a task in Notion.
    
    Args:
        params: Dictionary containing task parameters:
    
    Returns:
        The created page response from Notion API
    """
    client = get_notion_client()
    database_id = get_databases()["tasks"]

    # Validate and extract parameters
    if "title" not in params or not isinstance(params["title"], str) or not params["title"].strip():
        raise ValueError("'title' is required and must be a non-empty string")
    if "due_date" not in params or not isinstance(params["due_date"], str) or not params["due_date"].strip():
        raise ValueError("'due_date' is required and must be a non-empty ISO date string")
    if "priority" not in params or not isinstance(params["priority"], int):
        raise ValueError("'priority' is required and must be an integer (1..3)")

    title = params["title"].strip()
    due_date = params["due_date"].strip()
    try:
        priority = get_priority_name(params["priority"])
    except ValueError as e:
        raise ValueError(str(e))
    project_id = params.get("project_id")
    course_id = params.get("course_id")

    if project_id is not None and not isinstance(project_id, str):
        raise TypeError("'project_id' must be a string if provided")
    if course_id is not None and not isinstance(course_id, str):
        raise TypeError("'course_id' must be a string if provided")
    
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
    
    try:
        res = client.pages.create(**page_data)
    except Exception as e:
        logger.exception("Failed to create task page in Notion")
        raise RuntimeError(f"Failed to create task: {e}")
    
    url = res.get("url")
    
    if not url:
        raise RuntimeError("Failed to create task: No URL returned from Notion API")
    
    return url

get_tasks_spec = types.Tool(
    name="get-tasks",
    description="Fetches tasks from my Notion based on filtering criteria",
    inputSchema={
        "type": "object",
        "required": ["time_range"],
        "properties": {
            "time_range": {
                "type": "string",
                "description": "The time range to get tasks for. One of 'today', 'tomorrow', or 'week_from_today'",
                "enum": ["today", "tomorrow", "week_from_today"]
            }
        }
        
    }
)

async def get_tasks_handler(arguments: dict[str, Any], ctx: Any) -> list[types.ContentBlock]:
    time_range = arguments["time_range"]
    if not isinstance(time_range, str):
        raise TypeError("'query' must be a string.")
    
    try:
        tasks = get_tasks(time_range)
    except Exception as e:
        logger.exception("Failed to get tasks")
        raise RuntimeError(f"Failed to get tasks: {e}")
    
    
    
    if len(tasks) == 0:
        return [types.TextContent(type="text", text=f"There are no pending tasks in the specified time range of '{time_range}'.")]
    
    returned_string = f"\nPending Tasks for Time Range '{time_range}':\n\n"
    
    for i in range(len(tasks)):
        task =  tasks[i]
        pre = "\n" if i > 0 else ""
        returned_string += pre + f"{task['title']}\n- Due Date: {task['due_date']}"
        if task["project"] is not None:
            returned_string += f"\n- Associated Project: {task['project']['title']}"
        if task["course"] is not None:
            returned_string += f"\n- Associated Course: {task['course']['title']}"
            
        returned_string += "\n"
            
    return [types.TextContent(type="text", text=returned_string)]
            
            

get_projects_spec = types.Tool(
    name="get-projects",
    description="Fetches active projects from my Notion (for creating tasks associated with projects)",
    inputSchema={
        "type": "object",
        "properties": {}
    }
)

async def get_projects_handler(arguments: dict[str, Any], ctx: Any) -> list[types.ContentBlock]:
    try:
        projects = get_projects()
    except Exception as e:
        logger.exception("Failed to get projects")
        raise RuntimeError(f"Failed to get projects: {e}")
    
    returned_string = "\nActive Projects:\n\n"
    if len(projects) == 0:
        returned_string += "No active projects found."
        return [types.TextContent(type="text", text=returned_string)]
    
    for i in range(len(projects)):
        project = projects[i]
        pre = "\n" if i > 0 else ""
        returned_string += pre + f"{project['title']}\n- ID: {project['id']}\n"
    
    return [types.TextContent(type="text", text=returned_string)]


get_courses_spec = types.Tool(
    name="get-courses",
    description="Fetches active courses from my Notion (for creating tasks associated with courses)",
    inputSchema={
        "type": "object",
        "properties": {}
    }
)

async def get_courses_handler(arguments: dict[str, Any], ctx: Any) -> list[types.ContentBlock]:
    try:
        courses = get_courses()
    except Exception as e:
        logger.exception("Failed to get courses")
        raise RuntimeError(f"Failed to get courses: {e}")
    
    returned_string = "\nActive Courses:\n\n"
    if len(courses) == 0:
        returned_string += "No active courses found."
        return [types.TextContent(type="text", text=returned_string)]
    
    for i in range(len(courses)):
        course = courses[i]
        pre = "\n" if i > 0 else ""
        returned_string += pre + f"{course['title']}\n- Description: {course['description']}\n- ID: {course['id']}\n"
    
    return [types.TextContent(type="text", text=returned_string)]


create_task_spec = types.Tool(
    name="create-task",
    description="Creates a new task in my Notion Tasks database",
    inputSchema={
        "type": "object",
        "required": ["title", "due_date", "priority"],
        "properties": {
            "title": {
                "type": "string",
                "description": "Task description (what needs to be done. Example: 'Complete the project report')"
            },
            "due_date": {
                "type": "string",
                "description": "Task due date in ISO format (YYYY-MM-DD). Example: '2025-10-25'"
            },
            "priority": {
                "type": "integer",
                "description": "Task priority: 1 (highest) .. 3 (lowest)",
                "minimum": 1,
                "maximum": 3
            },
            "project_id": {
                "type": "string",
                "description": "Optional related project page ID (fetch using the 'get-projects' tool)"
            },
            "course_id": {
                "type": "string",
                "description": "Optional related course page ID (fetch using the 'get-courses' tool)"
            }
        }
    }
)

async def create_task_handler(arguments: dict[str, Any], ctx: Any) -> list[types.ContentBlock]:
    try:
        params: CreateTaskParams = {
            "title": arguments.get("title"),
            "due_date": arguments.get("due_date"),
            "priority": arguments.get("priority"),
            "project_id": arguments.get("project_id"),
            "course_id": arguments.get("course_id"),
        }
        url = create_task(params)
    except Exception as e:
        logger.exception("Failed to create task")
        raise RuntimeError(f"Failed to create task: {e}")
    
    returned_string = f"Task created: {url}"
    return [types.TextContent(type="text", text=returned_string)]

def register_all() -> None:
    register_tool(get_tasks_spec, get_tasks_handler)
    register_tool(get_projects_spec, get_projects_handler)
    register_tool(get_courses_spec, get_courses_handler)
    register_tool(create_task_spec, create_task_handler)
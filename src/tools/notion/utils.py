from datetime import datetime, timezone, timedelta
from pydoc import describe
from typing import Literal


def build_date_filter(time_range: str) -> dict:
    """
    Build a Notion date filter for the specified time range.
    
    Args:
        time_range: One of "today", "tomorrow", or "week_from_today"
        
    Returns:
        A dict containing the date filter conditions for Notion API
    """
    now = datetime.now(timezone.utc)
    
    if time_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == "tomorrow":
        tomorrow = now + timedelta(days=1)
        start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == "week_from_today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        raise ValueError(f"Invalid time_range: {time_range}. Must be 'today', 'tomorrow', or 'week_from_today'")
    
    # Format dates as ISO 8601 strings
    start_str = start.date().isoformat()
    end_str = end.date().isoformat()
    
    return {
        "and": [
            {
                "property": "Due Date",
                "date": {
                    "on_or_after": start_str
                }
            },
            {
                "property": "Due Date",
                "date": {
                    "on_or_before": end_str
                }
            }
        ]
    }

def retrieve_task_info(task: dict) -> dict:
    props = task["properties"]
    title = props["Name"]["title"][0]["plain_text"]
    due_date = props["Due Date"]["date"]["start"]
    project = props["Project"]["relation"][0]["id"] if len(props["Project"]["relation"]) > 0 else None
    course = props["Course"]["relation"][0]["id"] if len(props["Course"]["relation"]) > 0 else None
    
    return {
        "title": title,
        "due_date": due_date,
        "project": project,
        "course": course
    }
    
def retrieve_project_info(project: dict) -> dict:
    title = project["properties"]["Name"]["title"][0]["plain_text"]
    id = project["id"]
    
    return {"title": title, "id": id}

def retrieve_course_info(course: dict) -> dict:
    title = course["properties"]["Name"]["title"][0]["plain_text"]
    description = course["properties"]["Description"]["rich_text"][0]["plain_text"]
    id = course["id"]
    
    return {"title": title, "description": description, "id": id}
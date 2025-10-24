import logging
import os
from typing import Literal
from notion_client import Client
from auth import load_env_from_file
from .utils import build_date_filter, retrieve_task_info

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

def get_database_id() -> str:
    database_id = os.environ.get("DATABASE_ID")
    if not database_id:
        load_env_from_file()
        database_id = os.environ.get("DATABASE_ID")
    if not database_id:
        raise RuntimeError("DATABASE_ID is not set. Add it to your environment or .env")
    return database_id

def get_tasks_data_source_id():
    client = get_notion_client()
    database_id = get_database_id()
    
    try:
        dbs = client.databases.retrieve(database_id)
        
        db = dbs["data_sources"][0]
        
        return db["id"]
    except Exception as e:
        print(f"An error occurred while retrieving database information: {e}")
        #  RAISE EXCEPTION


def get_tasks(time_range: Literal["today", "tomorrow", "week_from_today"]):
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
    

    


def register_all() -> None:
    # register_tool(get_alerts_spec, get_alerts_handler)
    # register_tool(get_forecast_spec, get_forecast_handler)
    pass
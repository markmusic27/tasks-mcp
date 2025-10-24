import os
from notion_client import Client
from auth import load_env_from_file

def get_notion_client():
    # Try to read from environment first
    token = os.environ.get("NOTION_AUTH_TOKEN")
    if not token:
        # Attempt to load from .env lazily if not already loaded
        load_env_from_file()
        token = os.environ.get("NOTION_AUTH_TOKEN")
    if not token:
        raise RuntimeError("NOTION_AUTH_TOKEN is not set. Add it to your environment or .env")
    return Client(auth=token)

def get_database_id() -> str:
    database_id = os.environ.get("DATABASE_ID")
    if not database_id:
        load_env_from_file()
        database_id = os.environ.get("DATABASE_ID")
    if not database_id:
        raise RuntimeError("DATABASE_ID is not set. Add it to your environment or .env")
    return database_id

def get_tasks():
    notion = get_notion_client()
    
    database_id = get_database_id()
    print(database_id)
    
    
    print("Hello world")


def register_all() -> None:
    # register_tool(get_alerts_spec, get_alerts_handler)
    # register_tool(get_forecast_spec, get_forecast_handler)
    pass
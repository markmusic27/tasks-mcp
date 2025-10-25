from app import main
from tools.notion.notion import create_task, get_courses, get_projects, get_tasks

if __name__ == "__main__":
    # import sys
    # sys.exit(main())
    
    project, course = "25cb37de-b65d-8092-8c4b-ffbb983602bf", "276b37de-b65d-8047-9b72-fb4fed8a601d"
    
    task = create_task({
        "title": "Finish the CS229 pset",
        "due_date": "2025-10-26",
        "priority": 1,
        "body": "### hello world",
        "project_id": project,
        "course_id": course
    })
    
    
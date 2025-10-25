from app import main
from tools.notion.notion import get_courses, get_projects

if __name__ == "__main__":
    import sys
    projects = get_projects()
    # sys.exit(main())
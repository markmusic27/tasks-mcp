from app import main
from tools.notion.notion import get_tasks

if __name__ == "__main__":
    import sys
    tasks = get_tasks("week_from_today")
    print(tasks)
    # sys.exit(main())
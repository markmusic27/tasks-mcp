from app import main
from tools.notion.notion import get_tasks

if __name__ == "__main__":
    import sys
    sys.exit(get_tasks())
    # sys.exit(main())
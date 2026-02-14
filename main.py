import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import OpenTouchServer


def main():
    server = OpenTouchServer(port=8000, target_fps=30)
    server.run()


if __name__ == "__main__":
    main()

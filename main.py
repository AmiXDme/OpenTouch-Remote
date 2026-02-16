import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config, setup_logging
from src.server import OpenTouchServer


def main():
    config = Config.from_args()
    logger = setup_logging(config.verbose)
    logger.info(f"OpenTouch-Remote starting with config: {config}")

    server = OpenTouchServer(config)
    server.run()


if __name__ == "__main__":
    main()

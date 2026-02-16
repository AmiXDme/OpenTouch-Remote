import argparse
import logging
from dataclasses import dataclass


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("opentouch")


@dataclass
class Config:
    port: int = 8000
    target_fps: int = 30
    jpeg_quality: float = 0.85
    monitor_idx: int = 0
    verbose: bool = False
    host: str = "0.0.0.0"

    @classmethod
    def from_args(cls) -> "Config":
        parser = argparse.ArgumentParser(
            description="OpenTouch-Remote: High-performance DXGI Windows mirroring engine",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  uv run main.py                        Start with defaults (port 8000, 30fps)
  uv run main.py --port 9000            Use port 9000
  uv run main.py --fps 60 --quality 0.9 High performance mode
  uv run main.py --monitor 1            Use second monitor
  uv run main.py --verbose              Enable debug logging
            """,
        )
        parser.add_argument(
            "--port",
            "-p",
            type=int,
            default=8000,
            help="Server port (default: 8000)",
        )
        parser.add_argument(
            "--fps",
            "-f",
            type=int,
            default=30,
            choices=range(10, 61),
            metavar="10-60",
            help="Target frames per second (default: 30)",
        )
        parser.add_argument(
            "--quality",
            "-q",
            type=float,
            default=0.85,
            help="JPEG quality 0.1-1.0 (default: 0.85)",
        )
        parser.add_argument(
            "--monitor",
            "-m",
            type=int,
            default=0,
            help="Monitor index to capture (default: 0 = primary)",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose debug logging",
        )
        parser.add_argument(
            "--host",
            type=str,
            default="0.0.0.0",
            help="Host to bind (default: 0.0.0.0)",
        )

        args = parser.parse_args()

        quality = max(0.1, min(1.0, args.quality))

        return cls(
            port=args.port,
            target_fps=args.fps,
            jpeg_quality=quality,
            monitor_idx=args.monitor,
            verbose=args.verbose,
            host=args.host,
        )

"""
Entry point for termnotes editor
"""

import sys
import argparse
from .ui import EditorUI
from .config import get_example_config
from . import __version__


def main():
    """Main entry point for the editor"""
    parser = argparse.ArgumentParser(description="A vim-like terminal note-taking application")
    parser.add_argument("--version", action="version", version=f"termnotes {__version__}")
    parser.add_argument("--print-config", action="store_true",
                       help="Print example configuration and exit")

    args = parser.parse_args()

    # Handle --print-config flag
    if args.print_config:
        print(get_example_config())
        sys.exit(0)

    # Create and run the editor
    editor = EditorUI()
    try:
        editor.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass


if __name__ == "__main__":
    main()

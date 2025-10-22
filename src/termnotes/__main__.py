"""
Entry point for termnotes editor
"""

import sys
from .ui import EditorUI


def main():
    """Main entry point for the editor"""
    # Check if a file argument was provided
    initial_text = ""
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                initial_text = f.read()
        except FileNotFoundError:
            # File doesn't exist, start with empty buffer
            pass
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Create and run the editor
    editor = EditorUI(initial_text)
    try:
        editor.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass


if __name__ == "__main__":
    main()

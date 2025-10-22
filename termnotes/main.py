"""Main entry point for termnotes application."""

import argparse
import sys
from .storage import StorageBackend
from .ui import NotesUI


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="A note taker in your terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Backend options:
  memory       In-memory database (default, notes are lost on exit)
  filesystem   Persistent storage in ~/.termnotes/notes.db
  <path>       Custom database file path

Examples:
  termnotes                      # Use in-memory database
  termnotes --backend filesystem # Use persistent storage
  termnotes --backend ~/my-notes.db  # Custom database path
        """
    )
    parser.add_argument(
        "--backend",
        default="memory",
        help="Storage backend: memory, filesystem, or custom path (default: memory)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database
        db = StorageBackend.get_database(args.backend)
        
        # Create and run UI
        ui = NotesUI(db)
        ui.run()
        
        # Cleanup
        db.close()
        
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

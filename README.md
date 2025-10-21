# termnotes
A note taker in your terminal

## Features

- **Terminal UI**: Built with Bubbletea framework for a smooth terminal experience
- **Markdown Support**: Notes are rendered as Markdown in the preview pane
- **SQLite Backend**: Notes are stored in-memory using SQLite for fast access
- **Persistent Storage**: Configurable backend storage (filesystem by default)
- **Mouse Support**: Click to select notes in the sidebar
- **Keyboard Navigation**: Full keyboard support for creating, editing, and deleting notes

## Installation

```bash
# Build from source
make build

# Or install directly
go install github.com/bjia56/termnotes/cmd/termnotes@latest
```

## Usage

```bash
# Run the application
./termnotes

# Or if installed
termnotes
```

## Keyboard Shortcuts

### Normal Mode
- `n` - Create a new note
- `e` - Edit the selected note
- `d` - Delete the selected note
- `↑/k` - Move selection up
- `↓/j` - Move selection down
- `q` - Quit the application

### Edit/Create Mode
- `Tab` - Switch between title and content fields
- `Ctrl+S` - Save the note
- `Esc` - Cancel and return to normal mode
- `Enter` - New line (in content field) or move to content (in title field)

## Mouse Controls

- Click on a note in the left sidebar to select it
- Use keyboard shortcuts for editing and creating notes

## Storage

Notes are stored in `~/.termnotes/notes.json` by default. The application uses an in-memory SQLite database for fast access and syncs to the filesystem backend when changes are made.

## Architecture

- **Storage Layer**: Pluggable backend system supporting different storage mechanisms
  - In-memory SQLite database for fast access
  - Filesystem backend for persistence
  - Easy to add more backends (e.g., cloud storage, databases)
- **UI Layer**: Built with Charmbracelet's Bubbletea framework
  - Split view with note list on the left
  - Markdown rendering in the main content area
  - Full mouse and keyboard support

## Development

```bash
# Format code
make fmt

# Run tests
make test

# Vet code
make vet

# Clean build artifacts
make clean
```

## License

See LICENSE file for details.


# Visual Demonstration of TermNotes

This document shows what the TermNotes application looks like when running.

## Application Startup

When you first launch `./termnotes`, you'll see the main interface with a split-screen layout:

```
┌──────────────────────────────┬─────────────────────────────────────────────────┐
│ Notes                        │ Code Snippet                                    │
│──────────────────────────────│─────────────────────────────────────────────────│
│ ▸ Code Snippet               │                                                 │
│   Meeting Notes              │    Useful Go Code                               │
│   Shopping List              │                                                 │
│   Welcome to TermNotes       │     func main() {                               │
│                              │         fmt.Println("Hello, World!")            │
│──────────────────────────────│     }                                           │
│ n:new e:edit d:delete        │                                                 │
│ ↑/k ↓/j q:quit               │   Remember to run  go fmt  before committing!   │
└──────────────────────────────┴─────────────────────────────────────────────────┘
```

**Left Panel**: Shows a list of all your notes
- The selected note is highlighted with `▸`
- Notes are sorted by last update time
- Help text at the bottom shows available commands

**Right Panel**: Shows the markdown-rendered content of the selected note
- Full markdown support with syntax highlighting
- Code blocks, headers, lists, bold/italic text
- Auto-word wrapping

## Creating a New Note

Press `n` to create a new note:

```
Create New Note
────────────────────────────────────────────────────────────────────────────────

Title (Tab to switch fields):
> My Shopping List█

Content:
  

────────────────────────────────────────────────────────────────────────────────
Ctrl+S: Save  |  Esc: Cancel  |  Tab: Switch field
```

- Type the title in the first field
- Press `Tab` to move to the content field
- Type your note content (supports markdown)
- Press `Ctrl+S` to save
- Press `Esc` to cancel

## Editing an Existing Note

Select a note with arrow keys or mouse, then press `e`:

```
Edit Note
────────────────────────────────────────────────────────────────────────────────

Title (Tab to switch fields):
  Shopping List

Content:
> # My Shopping List

- [ ] Milk
- [ ] Eggs
- [ ] Bread█

────────────────────────────────────────────────────────────────────────────────
Ctrl+S: Save  |  Esc: Cancel  |  Tab: Switch field
```

## Viewing a Note with Rich Markdown

When you select the "Meeting Notes" entry:

```
┌──────────────────────────────┬─────────────────────────────────────────────────┐
│ Notes                        │ Meeting Notes                                   │
│──────────────────────────────│─────────────────────────────────────────────────│
│   Code Snippet               │                                                 │
│ ▸ Meeting Notes              │ Team Meeting - Oct 21, 2025                     │
│   Shopping List              │                                                 │
│   Welcome to TermNotes       │ Attendees                                       │
│                              │ • Alice                                         │
│──────────────────────────────│ • Bob                                           │
│ n:new e:edit d:delete        │ • Charlie                                       │
│ ↑/k ↓/j q:quit               │                                                 │
│                              │ Agenda                                          │
│                              │ 1. Project status update                        │
│                              │ 2. Q4 planning                                  │
│                              │ 3. Open discussion                              │
│                              │                                                 │
│                              │ Action Items                                    │
│                              │ • [ ] Alice: Update documentation               │
│                              │ • [ ] Bob: Review pull requests                 │
│                              │ • [ ] Charlie: Deploy to staging                │
└──────────────────────────────┴─────────────────────────────────────────────────┘
```

## Mouse Support

You can use your mouse to:
- **Click on notes** in the left sidebar to select them
- The application will instantly display the selected note's content

## Features Summary

✅ **Create** - Press `n` to create a new note
✅ **Edit** - Press `e` to edit the selected note  
✅ **Delete** - Press `d` to delete the selected note
✅ **Navigate** - Use `↑/k` and `↓/j` or mouse clicks
✅ **Markdown** - Full markdown rendering with syntax highlighting
✅ **Persistence** - All notes automatically saved to `~/.termnotes/notes.json`
✅ **Fast** - In-memory SQLite for instant access
✅ **Mouse** - Click to select notes

## Technical Details

- **Backend**: Pluggable storage system
- **Current**: Filesystem backend (`~/.termnotes/notes.json`)
- **Future**: Easy to add cloud storage, databases, etc.
- **Database**: SQLite in-memory for fast operations
- **UI**: Bubbletea framework with lipgloss styling
- **Rendering**: Glamour for beautiful markdown

## Running the Demo

```bash
# Create some demo notes
go run ./cmd/demo

# Launch the application
./termnotes

# Verify all features work
go run ./cmd/verify
```

Enjoy taking notes in your terminal! 📝

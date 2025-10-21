# TermNotes Application Screenshots

## Main View (Normal Mode)

When you first launch the application with demo notes, you'll see:

```
Notes                         │ Code Snippet                                    
──────────────────────────────│ ────────────────────────────────────────────────
▸ Code Snippet                │ 
  Meeting Notes               │    Useful Go Code                             
  Shopping List               │                                               
  Welcome to TermNotes        │     func main() {                             
                              │         fmt.Println("Hello, World!")          
──────────────────────────────│     }                                         
n:new e:edit d:delete         │                                               
↑/k ↓/j q:quit                │   Remember to run  go fmt  before committing! 
```

### Features Visible:
- **Left Sidebar**: List of all notes with the selected note highlighted (▸)
- **Right Panel**: Markdown-rendered content of the selected note
- **Bottom Bar**: Keyboard shortcuts for quick reference

## Empty State

When no notes exist:

```
Notes                         │ No note selected
──────────────────────────────│ 
No notes yet.                 │ 
Press 'n' to create one.      │ 
──────────────────────────────│ 
n:new e:edit d:delete         │ 
↑/k ↓/j q:quit                │ 
```

## Edit Mode

When creating or editing a note (press 'n' or 'e'):

```
Create New Note
────────────────────────────────────────────────────────────────────────────────

Title (Tab to switch fields):
> My New Note█

Content:
  Write your note content here...

────────────────────────────────────────────────────────────────────────────────
Ctrl+S: Save  |  Esc: Cancel  |  Tab: Switch field
```

### Edit Mode Features:
- Separate fields for title and content
- Visual cursor indicator (█)
- Tab to switch between fields
- Ctrl+S to save
- Esc to cancel

## Navigation

### Keyboard Controls:
- `n` - Create a new note
- `e` - Edit the selected note
- `d` - Delete the selected note
- `↑/k` - Move selection up
- `↓/j` - Move selection down
- `q` - Quit the application

### Mouse Controls:
- Click on any note in the left sidebar to select it

## Markdown Rendering

The application supports full markdown rendering including:
- Headers (# ## ###)
- **Bold** and *italic* text
- Code blocks with syntax highlighting
- Lists (ordered and unordered)
- Checkboxes [ ] and [x]
- And more!

## Storage

Notes are automatically persisted to `~/.termnotes/notes.json` after any changes (create, update, delete).

The application uses an in-memory SQLite database for fast access during runtime, with automatic synchronization to the filesystem backend.

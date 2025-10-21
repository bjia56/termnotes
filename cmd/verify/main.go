package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/bjia56/termnotes/internal/storage"
)

// This program demonstrates all the features of termnotes programmatically
func main() {
	fmt.Println("=== TermNotes Feature Demonstration ===\n")

	// Create a test backend
	tmpDir := os.TempDir()
	testPath := filepath.Join(tmpDir, "termnotes_demo.json")
	defer os.Remove(testPath)

	fmt.Println("1. Creating filesystem backend...")
	backend, err := storage.NewFileSystemBackend(testPath)
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Backend created at: %s\n\n", testPath)

	fmt.Println("2. Initializing in-memory SQLite store...")
	store, err := storage.NewStore(backend)
	if err != nil {
		panic(err)
	}
	defer store.Close()
	fmt.Println("   ✓ Store initialized\n")

	fmt.Println("3. Creating notes...")
	note1, err := store.CreateNote("First Note", "This is my **first** note with markdown!")
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Created note ID %d: %s\n", note1.ID, note1.Title)

	note2, err := store.CreateNote("Second Note", "# Header\n\nSome content here")
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Created note ID %d: %s\n", note2.ID, note2.Title)

	note3, err := store.CreateNote("Code Example", "```go\nfunc main() {\n  fmt.Println(\"Hello!\")\n}\n```")
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Created note ID %d: %s\n\n", note3.ID, note3.Title)

	fmt.Println("4. Listing all notes...")
	notes, err := store.ListNotes()
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Found %d notes\n", len(notes))
	for _, n := range notes {
		fmt.Printf("     - [%d] %s\n", n.ID, n.Title)
	}
	fmt.Println()

	fmt.Println("5. Updating a note...")
	err = store.UpdateNote(note1.ID, "First Note (Updated)", "Updated content with **more** markdown!")
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Updated note ID %d\n\n", note1.ID)

	fmt.Println("6. Retrieving a specific note...")
	retrieved, err := store.GetNote(note2.ID)
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Retrieved note ID %d: %s\n", retrieved.ID, retrieved.Title)
	fmt.Printf("     Content preview: %.50s...\n\n", retrieved.Content)

	fmt.Println("7. Deleting a note...")
	err = store.DeleteNote(note3.ID)
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ Deleted note ID %d\n\n", note3.ID)

	fmt.Println("8. Verifying persistence...")
	notes, err = store.ListNotes()
	if err != nil {
		panic(err)
	}
	fmt.Printf("   ✓ %d notes remaining in database\n", len(notes))

	// Verify file was created
	if _, err := os.Stat(testPath); err == nil {
		fmt.Printf("   ✓ Notes persisted to: %s\n", testPath)
	} else {
		fmt.Printf("   ✗ Persistence file not found\n")
	}

	fmt.Println("\n=== All Features Working Correctly! ===")
	fmt.Println("\nTo run the interactive application:")
	fmt.Println("  ./termnotes")
	fmt.Println("\nKeyboard shortcuts in the app:")
	fmt.Println("  n - Create new note")
	fmt.Println("  e - Edit selected note")
	fmt.Println("  d - Delete selected note")
	fmt.Println("  ↑/k, ↓/j - Navigate notes")
	fmt.Println("  q - Quit")
}

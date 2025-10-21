package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/bjia56/termnotes/internal/storage"
)

func main() {
	// Create a demo notes file
	homeDir, _ := os.UserHomeDir()
	demoPath := filepath.Join(homeDir, ".termnotes", "notes.json")
	
	backend, err := storage.NewFileSystemBackend(demoPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	store, err := storage.NewStore(backend)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	defer store.Close()

	// Create some demo notes
	notes := []struct {
		title   string
		content string
	}{
		{
			"Welcome to TermNotes",
			`# Welcome!

This is a terminal-based note taking application built with Go and Bubbletea.

## Features

- **Markdown Support**: All notes are rendered with beautiful markdown formatting
- **Fast**: Uses SQLite in-memory for instant access
- **Persistent**: Automatically saves to filesystem

Try creating a new note with **n**!`,
		},
		{
			"Shopping List",
			`# Shopping List

- [ ] Milk
- [ ] Eggs
- [ ] Bread
- [x] Coffee
- [ ] Butter

Don't forget to check the pantry first!`,
		},
		{
			"Meeting Notes",
			`# Team Meeting - Oct 21, 2025

## Attendees
- Alice
- Bob
- Charlie

## Agenda
1. Project status update
2. Q4 planning
3. Open discussion

## Action Items
- [ ] Alice: Update documentation
- [ ] Bob: Review pull requests
- [ ] Charlie: Deploy to staging`,
		},
		{
			"Code Snippet",
			"# Useful Go Code\n\n```go\nfunc main() {\n    fmt.Println(\"Hello, World!\")\n}\n```\n\nRemember to run `go fmt` before committing!",
		},
	}

	for _, note := range notes {
		_, err := store.CreateNote(note.title, note.content)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error creating note: %v\n", err)
		}
	}

	fmt.Println("Demo notes created successfully!")
	fmt.Println("Run ./termnotes to see them in action")
}

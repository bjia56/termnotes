package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/bjia56/termnotes/internal/storage"
	"github.com/bjia56/termnotes/internal/ui"
	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	// Get home directory for storing notes
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return fmt.Errorf("failed to get home directory: %w", err)
	}

	// Create filesystem backend
	notesPath := filepath.Join(homeDir, ".termnotes", "notes.json")
	backend, err := storage.NewFileSystemBackend(notesPath)
	if err != nil {
		return fmt.Errorf("failed to create backend: %w", err)
	}

	// Create store with filesystem backend
	store, err := storage.NewStore(backend)
	if err != nil {
		return fmt.Errorf("failed to create store: %w", err)
	}
	defer store.Close()

	// Create UI model
	model, err := ui.NewModel(store)
	if err != nil {
		return fmt.Errorf("failed to create model: %w", err)
	}

	// Create program with mouse support
	p := tea.NewProgram(model, tea.WithAltScreen(), tea.WithMouseCellMotion())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("failed to run program: %w", err)
	}

	return nil
}

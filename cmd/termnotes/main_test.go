package main

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/bjia56/termnotes/internal/storage"
	"github.com/bjia56/termnotes/internal/ui"
)

// TestEndToEnd performs an end-to-end test of the application
func TestEndToEnd(t *testing.T) {
	tmpDir := t.TempDir()
	backendPath := filepath.Join(tmpDir, "test_notes.json")

	backend, err := storage.NewFileSystemBackend(backendPath)
	if err != nil {
		t.Fatalf("Failed to create backend: %v", err)
	}

	store, err := storage.NewStore(backend)
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create a note
	note1, err := store.CreateNote("Test Note 1", "# Header\n\nThis is content")
	if err != nil {
		t.Fatalf("Failed to create note 1: %v", err)
	}

	note2, err := store.CreateNote("Test Note 2", "Another note")
	if err != nil {
		t.Fatalf("Failed to create note 2: %v", err)
	}

	// Create UI model
	model, err := ui.NewModel(store)
	if err != nil {
		t.Fatalf("Failed to create model: %v", err)
	}

	// Verify initial state
	if len(model.View()) == 0 {
		t.Error("View should not be empty")
	}

	t.Logf("Note 1 ID: %d", note1.ID)
	t.Logf("Note 2 ID: %d", note2.ID)
	t.Log("End-to-end test completed successfully")
}

func TestMain(m *testing.M) {
	fmt.Println("Running termnotes tests...")
	code := m.Run()
	os.Exit(code)
}

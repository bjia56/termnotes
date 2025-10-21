package storage

import (
	"os"
	"path/filepath"
	"testing"
)

func TestStore(t *testing.T) {
	// Create a temporary backend
	tmpDir := t.TempDir()
	backendPath := filepath.Join(tmpDir, "test_notes.json")
	backend, err := NewFileSystemBackend(backendPath)
	if err != nil {
		t.Fatalf("Failed to create backend: %v", err)
	}

	// Create store
	store, err := NewStore(backend)
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	defer store.Close()

	// Create a note
	note, err := store.CreateNote("Test Note", "This is a test note with **markdown**")
	if err != nil {
		t.Fatalf("Failed to create note: %v", err)
	}

	if note.Title != "Test Note" {
		t.Errorf("Expected title 'Test Note', got '%s'", note.Title)
	}

	// List notes
	notes, err := store.ListNotes()
	if err != nil {
		t.Fatalf("Failed to list notes: %v", err)
	}

	if len(notes) != 1 {
		t.Errorf("Expected 1 note, got %d", len(notes))
	}

	// Update note
	err = store.UpdateNote(note.ID, "Updated Note", "Updated content")
	if err != nil {
		t.Fatalf("Failed to update note: %v", err)
	}

	// Get updated note
	updatedNote, err := store.GetNote(note.ID)
	if err != nil {
		t.Fatalf("Failed to get note: %v", err)
	}

	if updatedNote.Title != "Updated Note" {
		t.Errorf("Expected title 'Updated Note', got '%s'", updatedNote.Title)
	}

	// Delete note
	err = store.DeleteNote(note.ID)
	if err != nil {
		t.Fatalf("Failed to delete note: %v", err)
	}

	// Verify deletion
	notes, err = store.ListNotes()
	if err != nil {
		t.Fatalf("Failed to list notes: %v", err)
	}

	if len(notes) != 0 {
		t.Errorf("Expected 0 notes, got %d", len(notes))
	}
}

func TestPersistence(t *testing.T) {
	tmpDir := t.TempDir()
	backendPath := filepath.Join(tmpDir, "persistent_notes.json")

	// Create and populate store
	backend1, err := NewFileSystemBackend(backendPath)
	if err != nil {
		t.Fatalf("Failed to create backend: %v", err)
	}

	store1, err := NewStore(backend1)
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}

	_, err = store1.CreateNote("Persistent Note", "This should persist")
	if err != nil {
		t.Fatalf("Failed to create note: %v", err)
	}

	store1.Close()

	// Verify file exists
	if _, err := os.Stat(backendPath); os.IsNotExist(err) {
		t.Fatalf("Backend file was not created")
	}

	// Load from same backend
	backend2, err := NewFileSystemBackend(backendPath)
	if err != nil {
		t.Fatalf("Failed to create second backend: %v", err)
	}

	store2, err := NewStore(backend2)
	if err != nil {
		t.Fatalf("Failed to create second store: %v", err)
	}
	defer store2.Close()

	notes, err := store2.ListNotes()
	if err != nil {
		t.Fatalf("Failed to list notes: %v", err)
	}

	if len(notes) != 1 {
		t.Errorf("Expected 1 persisted note, got %d", len(notes))
	}

	if len(notes) > 0 && notes[0].Title != "Persistent Note" {
		t.Errorf("Expected title 'Persistent Note', got '%s'", notes[0].Title)
	}
}

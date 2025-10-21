package storage

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/bjia56/termnotes/internal/models"
)

// FileSystemBackend implements Backend interface using filesystem
type FileSystemBackend struct {
	filepath string
}

// NewFileSystemBackend creates a new filesystem backend
func NewFileSystemBackend(path string) (*FileSystemBackend, error) {
	// Create directory if it doesn't exist
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory: %w", err)
	}

	return &FileSystemBackend{
		filepath: path,
	}, nil
}

// SaveAll saves all notes to the filesystem
func (f *FileSystemBackend) SaveAll(notes []models.Note) error {
	data, err := json.MarshalIndent(notes, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal notes: %w", err)
	}

	if err := os.WriteFile(f.filepath, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

// LoadAll loads all notes from the filesystem
func (f *FileSystemBackend) LoadAll() ([]models.Note, error) {
	data, err := os.ReadFile(f.filepath)
	if err != nil {
		if os.IsNotExist(err) {
			return []models.Note{}, nil
		}
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var notes []models.Note
	if err := json.Unmarshal(data, &notes); err != nil {
		return nil, fmt.Errorf("failed to unmarshal notes: %w", err)
	}

	return notes, nil
}

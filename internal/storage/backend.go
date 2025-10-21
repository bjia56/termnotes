package storage

import "github.com/bjia56/termnotes/internal/models"

// Backend defines the interface for persistent storage
type Backend interface {
	// SaveAll saves all notes to the backend
	SaveAll(notes []models.Note) error
	// LoadAll loads all notes from the backend
	LoadAll() ([]models.Note, error)
}

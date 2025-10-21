package storage

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/bjia56/termnotes/internal/models"
	_ "github.com/mattn/go-sqlite3"
)

// Store manages notes in an in-memory SQLite database
type Store struct {
	db      *sql.DB
	backend Backend
}

// NewStore creates a new Store with the given backend
func NewStore(backend Backend) (*Store, error) {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	store := &Store{
		db:      db,
		backend: backend,
	}

	if err := store.initDB(); err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	// Load notes from backend if available
	if backend != nil {
		notes, err := backend.LoadAll()
		if err != nil {
			return nil, fmt.Errorf("failed to load notes from backend: %w", err)
		}
		for _, note := range notes {
			if err := store.insertNote(note); err != nil {
				return nil, fmt.Errorf("failed to insert note: %w", err)
			}
		}
	}

	return store, nil
}

func (s *Store) initDB() error {
	query := `
		CREATE TABLE IF NOT EXISTS notes (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL,
			content TEXT NOT NULL,
			created_at DATETIME NOT NULL,
			updated_at DATETIME NOT NULL
		)
	`
	_, err := s.db.Exec(query)
	return err
}

func (s *Store) insertNote(note models.Note) error {
	query := `INSERT INTO notes (id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)`
	_, err := s.db.Exec(query, note.ID, note.Title, note.Content, note.CreatedAt, note.UpdatedAt)
	return err
}

// CreateNote creates a new note
func (s *Store) CreateNote(title, content string) (*models.Note, error) {
	now := time.Now()
	query := `INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)`
	result, err := s.db.Exec(query, title, content, now, now)
	if err != nil {
		return nil, fmt.Errorf("failed to create note: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("failed to get last insert id: %w", err)
	}

	note := &models.Note{
		ID:        id,
		Title:     title,
		Content:   content,
		CreatedAt: now,
		UpdatedAt: now,
	}

	s.syncToBackend()
	return note, nil
}

// UpdateNote updates an existing note
func (s *Store) UpdateNote(id int64, title, content string) error {
	now := time.Now()
	query := `UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?`
	_, err := s.db.Exec(query, title, content, now, id)
	if err != nil {
		return fmt.Errorf("failed to update note: %w", err)
	}

	s.syncToBackend()
	return nil
}

// DeleteNote deletes a note by ID
func (s *Store) DeleteNote(id int64) error {
	query := `DELETE FROM notes WHERE id = ?`
	_, err := s.db.Exec(query, id)
	if err != nil {
		return fmt.Errorf("failed to delete note: %w", err)
	}

	s.syncToBackend()
	return nil
}

// GetNote retrieves a note by ID
func (s *Store) GetNote(id int64) (*models.Note, error) {
	query := `SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?`
	row := s.db.QueryRow(query, id)

	var note models.Note
	err := row.Scan(&note.ID, &note.Title, &note.Content, &note.CreatedAt, &note.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to get note: %w", err)
	}

	return &note, nil
}

// ListNotes retrieves all notes
func (s *Store) ListNotes() ([]models.Note, error) {
	query := `SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC`
	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to list notes: %w", err)
	}
	defer rows.Close()

	var notes []models.Note
	for rows.Next() {
		var note models.Note
		err := rows.Scan(&note.ID, &note.Title, &note.Content, &note.CreatedAt, &note.UpdatedAt)
		if err != nil {
			return nil, fmt.Errorf("failed to scan note: %w", err)
		}
		notes = append(notes, note)
	}

	return notes, nil
}

// syncToBackend persists all notes to the backend
func (s *Store) syncToBackend() {
	if s.backend == nil {
		return
	}

	notes, err := s.ListNotes()
	if err != nil {
		return
	}

	_ = s.backend.SaveAll(notes)
}

// Close closes the database connection
func (s *Store) Close() error {
	return s.db.Close()
}

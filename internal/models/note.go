package models

import "time"

// Note represents a single note
type Note struct {
	ID        int64
	Title     string
	Content   string
	CreatedAt time.Time
	UpdatedAt time.Time
}

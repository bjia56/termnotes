package ui

import (
	"fmt"
	"strings"

	"github.com/bjia56/termnotes/internal/models"
	"github.com/bjia56/termnotes/internal/storage"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss"
)

type mode int

const (
	modeNormal mode = iota
	modeEdit
	modeCreate
)

// Model represents the application state
type Model struct {
	store         *storage.Store
	notes         []models.Note
	selectedIndex int
	mode          mode
	editTitle     string
	editContent   string
	cursorPos     int
	editingTitle  bool
	width         int
	height        int
	err           error
}

// NewModel creates a new application model
func NewModel(store *storage.Store) (*Model, error) {
	notes, err := store.ListNotes()
	if err != nil {
		return nil, fmt.Errorf("failed to list notes: %w", err)
	}

	return &Model{
		store:         store,
		notes:         notes,
		selectedIndex: 0,
		mode:          modeNormal,
		width:         80,
		height:        24,
	}, nil
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	return nil
}

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case tea.KeyMsg:
		return m.handleKeyPress(msg)

	case tea.MouseMsg:
		return m.handleMouse(msg)
	}

	return m, nil
}

func (m Model) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch m.mode {
	case modeNormal:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "n":
			m.mode = modeCreate
			m.editTitle = ""
			m.editContent = ""
			m.editingTitle = true
			m.cursorPos = 0
		case "e":
			if len(m.notes) > 0 && m.selectedIndex < len(m.notes) {
				note := m.notes[m.selectedIndex]
				m.mode = modeEdit
				m.editTitle = note.Title
				m.editContent = note.Content
				m.editingTitle = true
				m.cursorPos = len(note.Title)
			}
		case "d":
			if len(m.notes) > 0 && m.selectedIndex < len(m.notes) {
				note := m.notes[m.selectedIndex]
				if err := m.store.DeleteNote(note.ID); err != nil {
					m.err = err
					return m, nil
				}
				notes, err := m.store.ListNotes()
				if err != nil {
					m.err = err
					return m, nil
				}
				m.notes = notes
				if m.selectedIndex >= len(m.notes) && len(m.notes) > 0 {
					m.selectedIndex = len(m.notes) - 1
				}
			}
		case "up", "k":
			if m.selectedIndex > 0 {
				m.selectedIndex--
			}
		case "down", "j":
			if m.selectedIndex < len(m.notes)-1 {
				m.selectedIndex++
			}
		}

	case modeEdit, modeCreate:
		switch msg.String() {
		case "esc":
			m.mode = modeNormal
		case "ctrl+s":
			if err := m.saveNote(); err != nil {
				m.err = err
			} else {
				m.mode = modeNormal
			}
		case "tab":
			m.editingTitle = !m.editingTitle
			if m.editingTitle {
				m.cursorPos = len(m.editTitle)
			} else {
				m.cursorPos = len(m.editContent)
			}
		case "backspace":
			if m.editingTitle {
				if m.cursorPos > 0 {
					m.editTitle = m.editTitle[:m.cursorPos-1] + m.editTitle[m.cursorPos:]
					m.cursorPos--
				}
			} else {
				if m.cursorPos > 0 {
					m.editContent = m.editContent[:m.cursorPos-1] + m.editContent[m.cursorPos:]
					m.cursorPos--
				}
			}
		case "left":
			if m.cursorPos > 0 {
				m.cursorPos--
			}
		case "right":
			maxPos := len(m.editTitle)
			if !m.editingTitle {
				maxPos = len(m.editContent)
			}
			if m.cursorPos < maxPos {
				m.cursorPos++
			}
		case "enter":
			if m.editingTitle {
				m.editingTitle = false
				m.cursorPos = len(m.editContent)
			} else {
				m.editContent = m.editContent[:m.cursorPos] + "\n" + m.editContent[m.cursorPos:]
				m.cursorPos++
			}
		default:
			if len(msg.String()) == 1 {
				if m.editingTitle {
					m.editTitle = m.editTitle[:m.cursorPos] + msg.String() + m.editTitle[m.cursorPos:]
					m.cursorPos++
				} else {
					m.editContent = m.editContent[:m.cursorPos] + msg.String() + m.editContent[m.cursorPos:]
					m.cursorPos++
				}
			}
		}
	}

	return m, nil
}

func (m Model) handleMouse(msg tea.MouseMsg) (tea.Model, tea.Cmd) {
	if m.mode != modeNormal {
		return m, nil
	}

	if msg.Type == tea.MouseLeft {
		// Check if click is in the left sidebar (first 30 columns)
		if msg.X < 30 {
			// Calculate which note was clicked based on Y position
			// Account for header (3 lines) and each note taking 2 lines
			noteIndex := (msg.Y - 3) / 2
			if noteIndex >= 0 && noteIndex < len(m.notes) {
				m.selectedIndex = noteIndex
			}
		}
	}

	return m, nil
}

func (m *Model) saveNote() error {
	if m.editTitle == "" {
		m.editTitle = "Untitled"
	}

	if m.mode == modeCreate {
		_, err := m.store.CreateNote(m.editTitle, m.editContent)
		if err != nil {
			return err
		}
	} else if m.mode == modeEdit && m.selectedIndex < len(m.notes) {
		note := m.notes[m.selectedIndex]
		if err := m.store.UpdateNote(note.ID, m.editTitle, m.editContent); err != nil {
			return err
		}
	}

	notes, err := m.store.ListNotes()
	if err != nil {
		return err
	}
	m.notes = notes

	return nil
}

// View renders the UI
func (m Model) View() string {
	if m.width < 40 || m.height < 10 {
		return "Terminal too small. Please resize."
	}

	switch m.mode {
	case modeEdit, modeCreate:
		return m.renderEditView()
	default:
		return m.renderNormalView()
	}
}

func (m Model) renderNormalView() string {
	sidebarWidth := 30
	contentWidth := m.width - sidebarWidth - 2

	// Render sidebar
	sidebar := m.renderSidebar(sidebarWidth, m.height)

	// Render content
	content := m.renderContent(contentWidth, m.height)

	// Combine sidebar and content
	sidebarLines := strings.Split(sidebar, "\n")
	contentLines := strings.Split(content, "\n")

	var lines []string
	maxLines := max(len(sidebarLines), len(contentLines))
	for i := 0; i < maxLines; i++ {
		sidebarLine := ""
		if i < len(sidebarLines) {
			sidebarLine = sidebarLines[i]
		}
		contentLine := ""
		if i < len(contentLines) {
			contentLine = contentLines[i]
		}

		// Pad sidebar to exact width
		if len(sidebarLine) < sidebarWidth {
			sidebarLine += strings.Repeat(" ", sidebarWidth-len(sidebarLine))
		}

		lines = append(lines, sidebarLine+"│ "+contentLine)
	}

	return strings.Join(lines, "\n")
}

func (m Model) renderSidebar(width, height int) string {
	var sb strings.Builder

	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("69"))
	sb.WriteString(titleStyle.Render("Notes"))
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", width))
	sb.WriteString("\n")

	if len(m.notes) == 0 {
		sb.WriteString("No notes yet.\n")
		sb.WriteString("Press 'n' to create one.")
	} else {
		for i, note := range m.notes {
			if i >= height-5 {
				break
			}

			title := note.Title
			if len(title) > width-4 {
				title = title[:width-7] + "..."
			}

			if i == m.selectedIndex {
				selectedStyle := lipgloss.NewStyle().
					Bold(true).
					Foreground(lipgloss.Color("15")).
					Background(lipgloss.Color("69"))
				sb.WriteString(selectedStyle.Render(fmt.Sprintf("▸ %-*s", width-2, title)))
			} else {
				sb.WriteString(fmt.Sprintf("  %-*s", width-2, title))
			}
			sb.WriteString("\n")
		}
	}

	// Add help text at bottom
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", width))
	sb.WriteString("\n")
	helpStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	sb.WriteString(helpStyle.Render("n:new e:edit d:delete"))
	sb.WriteString("\n")
	sb.WriteString(helpStyle.Render("↑/k ↓/j q:quit"))

	return sb.String()
}

func (m Model) renderContent(width, height int) string {
	if len(m.notes) == 0 || m.selectedIndex >= len(m.notes) {
		emptyStyle := lipgloss.NewStyle().
			Foreground(lipgloss.Color("241")).
			Italic(true)
		return emptyStyle.Render("No note selected")
	}

	note := m.notes[m.selectedIndex]

	var sb strings.Builder

	// Render title
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("69")).
		Width(width)
	sb.WriteString(titleStyle.Render(note.Title))
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", min(width, 80)))
	sb.WriteString("\n\n")

	// Render markdown content
	renderer, err := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(width),
	)
	if err != nil {
		sb.WriteString(note.Content)
	} else {
		rendered, err := renderer.Render(note.Content)
		if err != nil {
			sb.WriteString(note.Content)
		} else {
			sb.WriteString(rendered)
		}
	}

	return sb.String()
}

func (m Model) renderEditView() string {
	var sb strings.Builder

	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("69"))
	if m.mode == modeCreate {
		sb.WriteString(titleStyle.Render("Create New Note"))
	} else {
		sb.WriteString(titleStyle.Render("Edit Note"))
	}
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", min(m.width, 80)))
	sb.WriteString("\n\n")

	// Title field
	fieldStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	sb.WriteString(fieldStyle.Render("Title (Tab to switch fields):"))
	sb.WriteString("\n")

	if m.editingTitle {
		sb.WriteString("> " + m.editTitle + "█")
	} else {
		sb.WriteString("  " + m.editTitle)
	}
	sb.WriteString("\n\n")

	// Content field
	sb.WriteString(fieldStyle.Render("Content:"))
	sb.WriteString("\n")

	if m.editingTitle {
		sb.WriteString("  " + m.editContent)
	} else {
		lines := strings.Split(m.editContent, "\n")
		for i, line := range lines {
			if i == 0 {
				sb.WriteString("> " + line + "█\n")
			} else {
				sb.WriteString("  " + line + "\n")
			}
		}
	}

	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", min(m.width, 80)))
	sb.WriteString("\n")
	helpStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	sb.WriteString(helpStyle.Render("Ctrl+S: Save  |  Esc: Cancel  |  Tab: Switch field"))

	if m.err != nil {
		sb.WriteString("\n\n")
		errorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("196"))
		sb.WriteString(errorStyle.Render(fmt.Sprintf("Error: %v", m.err)))
	}

	return sb.String()
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

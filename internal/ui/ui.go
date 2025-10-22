package ui

import (
	"fmt"
	"strings"

	"github.com/bjia56/termnotes/internal/models"
	"github.com/bjia56/termnotes/internal/storage"
	"github.com/charmbracelet/bubbles/list"
	"github.com/charmbracelet/bubbles/viewport"
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

// noteItem implements list.Item interface
type noteItem struct {
	note models.Note
}

func (i noteItem) FilterValue() string { return i.note.Title }
func (i noteItem) Title() string       { return i.note.Title }
func (i noteItem) Description() string {
	// Show a preview of the content (first line, truncated)
	lines := strings.Split(i.note.Content, "\n")
	if len(lines) > 0 && lines[0] != "" {
		preview := lines[0]
		if len(preview) > 50 {
			preview = preview[:50] + "..."
		}
		return preview
	}
	return "No content"
}

// Model represents the application state
type Model struct {
	store        *storage.Store
	notes        []models.Note
	list         list.Model
	viewport     viewport.Model
	mode         mode
	editTitle    string
	editContent  string
	cursorPos    int
	editingTitle bool
	width        int
	height       int
	ready        bool
	err          error
}

// NewModel creates a new application model
func NewModel(store *storage.Store) (*Model, error) {
	notes, err := store.ListNotes()
	if err != nil {
		return nil, fmt.Errorf("failed to list notes: %w", err)
	}

	// Create list items from notes
	items := make([]list.Item, len(notes))
	for i, note := range notes {
		items[i] = noteItem{note: note}
	}

	// Create the list
	delegate := list.NewDefaultDelegate()
	delegate.ShowDescription = true
	notesList := list.New(items, delegate, 0, 0)
	notesList.Title = "Notes"
	notesList.SetShowStatusBar(false)
	notesList.SetFilteringEnabled(false)
	notesList.SetShowHelp(true)

	// Create the viewport
	vp := viewport.New(0, 0)

	return &Model{
		store:    store,
		notes:    notes,
		list:     notesList,
		viewport: vp,
		mode:     modeNormal,
		width:    80,
		height:   24,
		ready:    false,
	}, nil
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	return nil
}

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var (
		cmd  tea.Cmd
		cmds []tea.Cmd
	)

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

		if !m.ready {
			m.ready = true
		}

		// Calculate sizes for list and viewport
		// List takes 1/3 of width, viewport takes the rest
		listWidth := m.width / 3
		viewportWidth := m.width - listWidth - 1 // -1 for divider

		m.list.SetSize(listWidth, m.height)
		m.viewport.Width = viewportWidth
		m.viewport.Height = m.height

		// Update viewport content if we have a selected note
		m.updateViewportContent()

		return m, nil

	case tea.KeyMsg:
		if m.mode == modeNormal {
			// Handle our custom keys first
			switch msg.String() {
			case "ctrl+c", "q":
				return m, tea.Quit
			case "n":
				m.mode = modeCreate
				m.editTitle = ""
				m.editContent = ""
				m.editingTitle = true
				m.cursorPos = 0
				return m, nil
			case "e":
				if len(m.notes) > 0 && m.list.Index() < len(m.notes) {
					note := m.notes[m.list.Index()]
					m.mode = modeEdit
					m.editTitle = note.Title
					m.editContent = note.Content
					m.editingTitle = true
					m.cursorPos = len(note.Title)
				}
				return m, nil
			case "d":
				if len(m.notes) > 0 && m.list.Index() < len(m.notes) {
					note := m.notes[m.list.Index()]
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
					m.updateList()
					m.updateViewportContent()
				}
				return m, nil
			}

			// Let the list handle other keys (up/down navigation)
			m.list, cmd = m.list.Update(msg)
			cmds = append(cmds, cmd)

			// Update viewport when selection changes
			m.updateViewportContent()

			// Also update the viewport for scrolling
			m.viewport, cmd = m.viewport.Update(msg)
			cmds = append(cmds, cmd)

			return m, tea.Batch(cmds...)
		} else {
			// Edit mode key handling
			return m.handleEditKeys(msg)
		}

	case tea.MouseMsg:
		if m.mode == modeNormal {
			// Let list handle mouse events
			m.list, cmd = m.list.Update(msg)
			cmds = append(cmds, cmd)

			// Update viewport when selection changes
			m.updateViewportContent()

			// Also let viewport handle mouse
			m.viewport, cmd = m.viewport.Update(msg)
			cmds = append(cmds, cmd)

			return m, tea.Batch(cmds...)
		}
	}

	return m, nil
}

func (m *Model) updateList() {
	items := make([]list.Item, len(m.notes))
	for i, note := range m.notes {
		items[i] = noteItem{note: note}
	}
	m.list.SetItems(items)
}

func (m *Model) updateViewportContent() {
	if len(m.notes) == 0 || m.list.Index() >= len(m.notes) {
		m.viewport.SetContent("No note selected")
		return
	}

	note := m.notes[m.list.Index()]

	var sb strings.Builder

	// Render title
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("69"))
	sb.WriteString(titleStyle.Render(note.Title))
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("─", min(m.viewport.Width, 80)))
	sb.WriteString("\n\n")

	// Render markdown content
	renderer, err := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(m.viewport.Width),
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

	m.viewport.SetContent(sb.String())
}

func (m Model) handleEditKeys(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "esc":
		m.mode = modeNormal
	case "ctrl+s":
		if err := m.saveNote(); err != nil {
			m.err = err
		} else {
			m.mode = modeNormal
			m.updateList()
			m.updateViewportContent()
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

	return m, nil
}

func (m Model) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	// This function is now replaced by the logic in Update
	return m, nil
}

func (m Model) handleMouse(msg tea.MouseMsg) (tea.Model, tea.Cmd) {
	// This function is now replaced by the logic in Update
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
	} else if m.mode == modeEdit && m.list.Index() < len(m.notes) {
		note := m.notes[m.list.Index()]
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
	if !m.ready {
		return "Initializing..."
	}

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
	// Render list and viewport side by side
	listView := m.list.View()
	viewportView := m.viewport.View()

	// Use lipgloss to join them horizontally
	return lipgloss.JoinHorizontal(
		lipgloss.Top,
		listView,
		lipgloss.NewStyle().
			BorderStyle(lipgloss.NormalBorder()).
			BorderLeft(true).
			BorderForeground(lipgloss.Color("240")).
			Render(viewportView),
	)
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

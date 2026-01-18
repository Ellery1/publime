# Text Editor

A Sublime Text alternative built with Python and PySide6.

## Project Structure

```
text-editor/
├── ui/              # UI components (main window, editor pane, dialogs)
├── core/            # Core functionality (syntax highlighter, search engine, file manager)
├── themes/          # Theme management and definitions
├── utils/           # Utility functions (language detector, text utils)
├── main.py          # Application entry point
└── requirements.txt # Python dependencies
```

## Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

### Installation

1. Create a virtual environment (optional but recommended):
```bash
python -m venv .venv
```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

## Dependencies

- **PySide6**: Qt for Python UI framework
- **pytest**: Testing framework
- **pytest-qt**: Qt testing support
- **pytest-cov**: Code coverage reporting
- **pytest-benchmark**: Performance benchmarking
- **hypothesis**: Property-based testing
- **black**: Code formatter
- **flake8**: Code linter

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run property-based tests
pytest -m hypothesis
```

### Code Formatting

```bash
# Format code
black .

# Check code style
flake8 .
```

## Features (Planned)

- [x] Project structure and dependencies
- [ ] Basic text editing (copy, paste, undo, redo)
- [ ] Multi-tab file management
- [ ] Syntax highlighting (Python, Java, SQL, JSON, JavaScript, Kotlin)
- [ ] Code folding
- [ ] Line numbers
- [ ] Font zoom
- [ ] File operations (open, save, drag & drop)
- [ ] Find and replace
- [ ] Cross-file search
- [ ] Multi-cursor editing
- [ ] Code completion
- [ ] Theme switching (dark/light)
- [ ] Large file handling (50MB+)
- [ ] Recent files history

## License

MIT License

# Contributing to Langfuse Samples

Thank you for your interest in contributing to langfuse-samples! This document provides guidelines for maintaining code quality and consistency.

## Getting Started

### 1. Development Setup
```bash
# Clone and setup the repository
git clone https://github.com/retroryan/langfuse-samples
cd langfuse-samples

# Run setup script
python setup.py

# Install development dependencies
make install-dev
# or: pip install -r requirements-dev.txt
```

### 2. Validate Your Environment
```bash
# Check setup
make check

# Validate code syntax
make validate

# Run integration tests (if services available)
make test
```

## Development Guidelines

### Code Quality Standards

1. **Python Code Style**
   - Follow PEP 8 guidelines
   - Line length: 100 characters (configured in `.flake8`)
   - Use descriptive variable names
   - Add docstrings to functions and classes

2. **File Organization**
   - Keep component-specific code in respective directories
   - Utility scripts go in `utils/` directory
   - Common configuration files at repository root

3. **Documentation**
   - Update relevant README files when adding features
   - Include clear setup instructions
   - Provide usage examples
   - Document prerequisites and dependencies

### Before Submitting

Run these commands to ensure quality:

```bash
# Validate Python syntax
make validate

# Check code style (if flake8 installed)
make lint

# Format code (if black installed)  
make format

# Clean up temporary files
make clean
```

## Adding New Components

### Directory Structure
```
new-component/
├── README.md              # Component-specific documentation
├── .env.example          # Environment template
├── requirements.txt      # Dependencies
├── *_demo.py            # Demo scripts
├── run_and_validate.py  # Validation script
└── view_traces.py       # Trace viewing utility
```

### Required Files

1. **README.md** - Include:
   - Quick start instructions
   - Prerequisites
   - Configuration steps
   - Usage examples
   - Troubleshooting

2. **.env.example** - Template with:
   - Required environment variables
   - Example values (non-sensitive)
   - Clear comments

3. **requirements.txt** - Pin versions for:
   - Core dependencies
   - Compatible with existing components
   - Follow semantic versioning

### Integration Patterns

All components should follow these patterns:

1. **Environment Setup**
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. **Error Handling**
   - Provide clear error messages
   - Check prerequisites before running
   - Graceful failure with helpful suggestions

3. **Validation Scripts**
   - Include `run_and_validate.py`
   - Check service connectivity
   - Verify trace creation
   - Provide detailed feedback

## Quality Checklist

Before submitting a PR, ensure:

- [ ] Code passes `make validate`
- [ ] All Python files have valid syntax
- [ ] Environment template (`.env.example`) provided
- [ ] Documentation updated (README files)
- [ ] Dependencies specified in `requirements.txt`
- [ ] Integration follows established patterns
- [ ] Error handling implemented
- [ ] Validation script included

## Common Issues

### Import Errors
- Ensure all required packages in `requirements.txt`
- Use specific version pinning
- Test with fresh virtual environment

### Documentation
- Keep README format consistent with existing components
- Include all necessary setup steps
- Test instructions with fresh setup

### Environment Variables
- Always provide `.env.example`
- Don't commit actual credentials
- Use descriptive variable names

## Repository Structure

```
langfuse-samples/
├── README.md                    # Main documentation
├── setup.py                     # Setup and validation script
├── Makefile                     # Common development commands
├── pyproject.toml              # Project configuration
├── requirements-dev.txt        # Development dependencies
├── utils/                      # Utility scripts
│   ├── README.md
│   ├── delete_metrics.py
│   └── validate_code.py
├── ollama-langfuse/            # Ollama integration
├── strands-langfuse/           # Strands integration  
└── langfuse-aws/               # AWS deployment
```

## Getting Help

- Check existing documentation in component directories
- Run `make help` to see available commands
- Use `python setup.py --check` to validate setup
- Review similar components for patterns

## Questions?

Open an issue or discussion on the GitHub repository for questions about:
- Integration patterns
- Development setup
- Code quality standards
- Documentation requirements
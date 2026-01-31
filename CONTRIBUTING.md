# Contributing to Job Scraper for Visa Sponsorship

Thank you for your interest in contributing! This project welcomes contributions from everyone.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in the [Issues](../../issues) section
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages: `git commit -m "Add: description of change"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Update documentation if needed

### Areas for Contribution

- Adding support for new job boards
- Improving filtering algorithms
- Adding new visa sponsorship keywords
- Fixing bugs and improving performance
- Improving documentation
- Adding tests

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/visa-sponsorship-jobs.git
cd visa-sponsorship-jobs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run a test search
python job_scraper.py --config config.test.yaml
```

## Questions?

Feel free to open an issue for any questions about contributing.

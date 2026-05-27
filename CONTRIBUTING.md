# Contributing to StreamTranslation

Thank you for your interest in contributing! 🎉

## How to Contribute

### 1. Report Bugs

If you find a bug, please open an issue with:
- **Title:** Brief description of the bug
- **Description:** What happens vs what should happen
- **Steps to reproduce:** Exact steps to trigger the bug
- **Environment:** OS, Python version, which language you're using
- **Error message:** Full traceback if applicable

### 2. Suggest Features

Have an idea? Open an issue with:
- **Title:** Feature name
- **Description:** What problem does it solve?
- **Examples:** How would you use it?

### 3. Submit Code Changes

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/StreamTranslation.git
   cd StreamTranslation
   ```

3. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make changes:**
   - Follow existing code style
   - Add comments for complex logic
   - Test thoroughly

5. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub with:
   - Description of changes
   - Why this change is useful
   - Any related issues (#123)

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write comments for non-obvious logic
- Keep functions focused and modular
- Maximum line length: 100 characters

## Testing

Before submitting:
1. Test with French input
2. Test with Chinese input
3. Test with low microphone input
4. Test with high background noise
5. Verify OBS integration works

## Documentation

- Update README.md if changing functionality
- Add docstrings to new functions
- Update CHANGELOG.md with changes
- Include examples for new features

## Development Setup

```powershell
# Clone and setup
git clone https://github.com/YOUR-USERNAME/StreamTranslation.git
cd StreamTranslation

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dev dependencies
pip install -r requirements.txt

# Make changes
# Test thoroughly
```

## Areas for Contribution

- 🌍 **Language support** - add more languages
- 🎯 **VAD improvement** - better speech detection
- 🎨 **UI/Dashboard** - web interface
- 📊 **Performance** - optimize audio processing
- 📖 **Documentation** - translate docs, clarify guides
- 🐛 **Bug fixes** - any reported issues
- ✅ **Tests** - improve test coverage

## Communication

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and general help
- Code comments: Explain complex logic

## License

By contributing, you agree your code will be licensed under MIT.

---

## Quick Start for Contributors

```bash
# 1. Fork on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/StreamTranslation.git

# 3. Create feature branch
git checkout -b feature/amazing-feature

# 4. Make changes
# 5. Test thoroughly
# 6. Commit
git commit -m "Add amazing feature"

# 7. Push
git push origin feature/amazing-feature

# 8. Open Pull Request on GitHub
```

---

## Questions?

Open an issue or start a discussion. We're here to help!

**Thank you for contributing! 🚀**

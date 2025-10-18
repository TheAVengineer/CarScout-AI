# Contributing to CarScout AI

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up your development environment** (see below)
4. **Create a branch** for your changes
5. **Make your changes** with tests
6. **Submit a pull request**

## Development Environment Setup

1. **Install Python 3.11+**

2. **Install dependencies:**
```bash
make dev-install
```

3. **Set up pre-commit hooks:**
```bash
pre-commit install
```

4. **Start services:**
```bash
make docker-up
```

5. **Run migrations:**
```bash
make migrate
```

## Code Style

We use automated formatting and linting tools:

### Format code:
```bash
make format
```

This runs:
- `black` for code formatting
- `ruff` for import sorting and linting

### Lint code:
```bash
make lint
```

This runs:
- `ruff` for style checks
- `mypy` for type checking

### Code Standards:
- Use type hints for all functions
- Write docstrings for public APIs
- Follow PEP 8 style guide
- Keep functions focused and small
- Prefer composition over inheritance

## Testing

### Run all tests:
```bash
make test
```

### Run specific tests:
```bash
pytest tests/unit/test_scoring.py -v
pytest tests/integration/ -v
```

### Test Coverage:
Aim for >80% test coverage for new code.

```bash
pytest --cov=apps --cov=workers --cov=libs --cov-report=html
```

### Writing Tests:

**Unit tests** should:
- Test a single function/method
- Use mocks for external dependencies
- Be fast (<100ms per test)
- Be independent of other tests

**Integration tests** should:
- Test multiple components together
- Use test database/Redis
- Clean up after themselves
- Test real scenarios

Example:
```python
def test_calculate_score():
    """Test scoring calculation"""
    engine = ScoringEngine()
    result = engine.calculate_score(
        discount_pct=15.0,
        comp_sample_size=50,
        comp_confidence=0.8,
        risk_level="low",
        freshness_hours=2.0,
    )
    
    assert result["score"] > 7.0
    assert result["is_approved"] is True
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
```
feat(scraping): add Cars.bg spider

Implement new spider for Cars.bg marketplace with
Playwright support for JavaScript rendering.

Closes #123
```

```
fix(pricing): handle missing comparables gracefully

When comp_sample_size is 0, return None instead of
throwing division by zero error.
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** (if applicable)
5. **Create pull request** with clear description

### PR Description Template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code passes linting
- [ ] All tests pass
```

## Project Structure

```
CarScout-AI/
├── apps/           # FastAPI and Telegram bot applications
├── workers/        # Celery workers and scrapers
├── libs/           # Shared libraries
│   ├── domain/    # Business logic
│   ├── schemas/   # Pydantic models
│   └── ml/        # Machine learning models
├── configs/        # Configuration
├── migrations/     # Database migrations
├── infra/         # Infrastructure (Docker, CI/CD)
├── tests/         # Test suite
└── docs/          # Documentation
```

## Adding New Features

### Adding a New Scraper:
1. Create spider in `workers/scrape/spiders/`
2. Implement parsing logic
3. Add tests in `tests/unit/scrapers/`
4. Add scheduler task in `workers/pipeline/celery_app.py`

### Adding a New API Endpoint:
1. Add route in `apps/api/routers/`
2. Add Pydantic models for request/response
3. Implement business logic in `libs/domain/`
4. Add tests
5. Update API documentation

### Adding a New Celery Task:
1. Create task in `workers/pipeline/tasks/`
2. Add queue routing in `celery_app.py`
3. Add tests
4. Update documentation

## Database Changes

1. **Modify models** (if using ORM)
2. **Create migration:**
```bash
alembic revision --autogenerate -m "Description"
```
3. **Review migration** file
4. **Test migration:**
```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```
5. **Commit migration** file

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/API.md` for API changes
- Update `docs/DEPLOYMENT.md` for infrastructure changes
- Add inline code comments for complex logic
- Write docstrings for public APIs

## Code Review

All submissions require code review. We look for:

- **Correctness** - Does it work as intended?
- **Tests** - Are there adequate tests?
- **Style** - Does it follow our standards?
- **Documentation** - Is it well documented?
- **Performance** - Is it efficient?
- **Security** - Are there security implications?

## Getting Help

- **GitHub Issues** - Report bugs or request features
- **Discussions** - Ask questions
- **Discord** - Real-time chat (if available)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

# Contributing to Kanoa

We welcome contributions! Please follow these guidelines to ensure a smooth process.

## Getting Started

1.  **Fork the repository** and clone it locally.
2.  **Install dependencies**:
    ```bash
    pip install -e ".[dev]"
    ```
3.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/my-awesome-feature
    ```

## Code Style

- We use **black** for formatting and **isort** for import sorting.
- Run linting before committing:
    ```bash
    black .
    isort .
    flake8
    ```
- Type hints are required for all function signatures.

## Testing

- Run the full test suite:
    ```bash
    pytest tests/
    ```
- Ensure coverage remains above 85%:
    ```bash
    pytest --cov=kanoa
    ```
- Add new tests for any new features or bug fixes.

## Pull Requests

1.  Ensure all tests pass.
2.  Update documentation if necessary.
3.  Describe your changes clearly in the PR description.
4.  Link to any relevant issues.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

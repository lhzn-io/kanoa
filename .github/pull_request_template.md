# Pull Request

## Description

<!-- Provide a clear and concise description of the changes -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test coverage improvement
- [ ] Other (please describe):

## Related Issues

<!-- Link to related issues using #issue_number -->

Closes #
Related to #

## Changes Made

<!-- List the key changes made in this PR -->

-
-
-

## Backend Impact

<!-- Mark all backends this PR affects -->

- [ ] gemini
- [ ] claude
- [ ] openai
- [ ] vllm
- [ ] All backends
- [ ] Not backend-specific

## Testing

<!-- Describe the tests you ran to verify your changes -->

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass (`make test`)
- [ ] Test coverage maintained or improved

### Manual Testing

<!-- Describe any manual testing performed -->

**Environment:**

- Python version:
- OS:
- Backend(s) tested:

**Test steps:**

1.
2.
3.

**Results:**

- [ ] Works as expected
- [ ] Edge cases considered

## Code Quality Checklist

<!-- Ensure all items are checked before requesting review -->

- [ ] Code follows the style guide in `CONTRIBUTING.md`
- [ ] All function signatures have type hints
- [ ] Docstrings added/updated (Google style)
- [ ] Linting passes (`make lint`)
  - [ ] ruff check passes
  - [ ] mypy passes with zero errors
- [ ] Code formatted (`make format`)
- [ ] No new lint warnings introduced
- [ ] Imports are clean and sorted
- [ ] Line length ≤ 88 characters

## Documentation

- [ ] Documentation updated (if applicable)
- [ ] API changes documented in docstrings
- [ ] Examples updated (if applicable)
- [ ] CHANGELOG updated (if this is a notable change)
- [ ] Emoji policy followed (see `CONTRIBUTING.md#emoji-policy`)

## Breaking Changes

<!-- If this is a breaking change, describe the migration path -->

**Is this a breaking change?**

- [ ] Yes
- [ ] No

**If yes, describe the impact and migration path:**

## Screenshots/Examples

<!-- If applicable, add screenshots or code examples showing the changes -->

```python
# Example usage
```

## Performance Impact

<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance regression (justified by):

## Security Considerations

<!-- Describe any security implications -->

- [ ] No security implications
- [ ] Security improved
- [ ] Requires security review

## Additional Notes

<!-- Any additional information reviewers should know -->

## Pre-submission Checklist

<!-- Final checks before requesting review -->

- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have run all tests locally and they pass
- [ ] I have checked for similar PRs to avoid duplication
- [ ] I have updated the documentation accordingly
- [ ] My commit messages follow conventional commit format (if applicable)

## Reviewers

<!-- Tag specific reviewers if needed -->

@<!-- username -->

---

**For Maintainers:**

- [ ] Version bump needed (if breaking change or new feature)
- [ ] Release notes updated

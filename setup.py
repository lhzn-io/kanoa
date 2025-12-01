from setuptools import find_packages, setup

# Core dependencies - always installed
CORE_DEPS = [
    "matplotlib>=3.5.0",
    "pandas>=1.3.0",
    "pydantic>=2.0.0",
]

# Backend-specific dependencies
GEMINI_DEPS = ["google-genai>=1.0.0"]
CLAUDE_DEPS = ["anthropic>=0.40.0"]
OPENAI_DEPS = ["openai>=1.0.0"]

# Notebook display enhancements (IPython is included via jupyter/ipykernel)
NOTEBOOK_DEPS = ["ipython>=7.0.0"]

# Development dependencies
DEV_DEPS = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "python-dotenv>=1.0.0",
    "ruff>=0.8.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "types-setuptools",
    "detect-secrets>=1.4.0",
]

# Documentation dependencies
DOCS_DEPS = [
    "sphinx>=7.0.0",
    "myst-parser>=2.0.0",
    "sphinx-rtd-theme>=2.0.0",
]

setup(
    name="kanoa",
    version="0.1.0",
    description=(
        "AI-powered interpretation of data science outputs with multi-backend support"
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Daniel Fry",
    author_email="dfry@lhzn.io",
    url="https://github.com/lhzn-io/kanoa",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    python_requires=">=3.11",
    install_requires=CORE_DEPS,
    extras_require={
        # Individual backends
        "gemini": GEMINI_DEPS,
        "claude": CLAUDE_DEPS,
        "openai": OPENAI_DEPS,
        # Notebook enhancements (rich HTML display)
        "notebook": NOTEBOOK_DEPS,
        # Convenience bundles
        "all": GEMINI_DEPS + CLAUDE_DEPS + OPENAI_DEPS + NOTEBOOK_DEPS,
        "backends": GEMINI_DEPS + CLAUDE_DEPS + OPENAI_DEPS,
        # Development
        "dev": DEV_DEPS + GEMINI_DEPS + CLAUDE_DEPS + OPENAI_DEPS + NOTEBOOK_DEPS,
        "docs": DOCS_DEPS,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    keywords="ai llm data-science analytics gemini claude openai jupyter",
)

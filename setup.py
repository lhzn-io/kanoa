import re

from setuptools import find_packages, setup

# Core dependencies - always installed
CORE_DEPS = [
    "matplotlib>=3.5.0",
    "pandas>=1.3.0",
    "pydantic>=2.0.0",
    "PyYAML>=6.0.0",
]

# Backend-specific dependencies
GEMINI_DEPS = ["google-genai>=1.0.0"]
CLAUDE_DEPS = ["anthropic>=0.40.0"]
OPENAI_DEPS = ["openai>=1.0.0"]
GCLOUD_DEPS = ["google-cloud-storage>=2.0.0"]
VERTEXAI_DEPS = ["google-cloud-aiplatform>=1.40.0"]  # For Vertex AI RAG Engine

# Notebook display enhancements (IPython is included via jupyter/ipykernel)
NOTEBOOK_DEPS = ["ipython>=7.0.0"]

# Development dependencies
DEV_DEPS = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "python-dotenv>=1.0.0",
    "ruff~=0.14.0",  # Pin to 0.14.x to match pre-commit
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "types-setuptools",
    "types-PyYAML",
    "types-requests",
    "detect-secrets>=1.4.0",
    "markitdown>=0.0.1",
]

# Documentation dependencies
DOCS_DEPS = [
    "sphinx>=7.0.0",
    "myst-parser>=2.0.0",
    "sphinx-rtd-theme>=2.0.0",
    "sphinx-autodoc-typehints>=1.20.0",
]


def read_long_description():
    with open("README.md", "r", encoding="utf-8") as f:
        text = f.read()

    # Replace relative links with absolute GitHub links
    # Matches [Link Text](./path/to/file) or [Link Text](path/to/file)
    # Excludes http, https, mailto, and # anchors
    base_url = "https://github.com/lhzn-io/kanoa/blob/main/"

    def replace_link(match):
        link = match.group(1)
        # Don't touch absolute paths (rare in READMEs but possible)
        if link.startswith("/"):
            return match.group(0)

        if link.startswith("./"):
            link = link[2:]
        return f"]({base_url}{link})"

    # Pattern matches ](link) where link doesn't start with http, https, mailto, or #
    pattern = r"\]\(((?!http|https|mailto|#)[^)]+)\)"
    return re.sub(pattern, replace_link, text)


setup(
    name="kanoa",
    use_scm_version=True,
    description=(
        "AI-powered interpretation of data science outputs with multi-backend support"
    ),
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="Daniel Fry",
    author_email="dfry@lhzn.io",
    url="https://github.com/lhzn-io/kanoa",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    include_package_data=True,
    package_data={
        "kanoa": ["*.json"],
    },
    python_requires=">=3.11",
    install_requires=CORE_DEPS,
    extras_require={
        # Individual backends
        "gemini": GEMINI_DEPS,
        "claude": CLAUDE_DEPS,
        "openai": OPENAI_DEPS,
        "local": OPENAI_DEPS,  # Alias for vLLM/Ollama users
        "gcloud": GCLOUD_DEPS,
        "vertexai": VERTEXAI_DEPS,
        # Notebook enhancements (rich HTML display)
        "notebook": NOTEBOOK_DEPS,
        # Convenience bundles
        "all": GEMINI_DEPS
        + CLAUDE_DEPS
        + OPENAI_DEPS
        + NOTEBOOK_DEPS
        + GCLOUD_DEPS
        + VERTEXAI_DEPS,
        "backends": GEMINI_DEPS + CLAUDE_DEPS + OPENAI_DEPS,
        # Development
        "dev": DEV_DEPS
        + GEMINI_DEPS
        + CLAUDE_DEPS
        + OPENAI_DEPS
        + NOTEBOOK_DEPS
        + GCLOUD_DEPS
        + VERTEXAI_DEPS,
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
    entry_points={
        "console_scripts": [
            "kanoa=kanoa.cli:main",
        ],
    },
)

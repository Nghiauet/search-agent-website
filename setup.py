from setuptools import setup, find_packages

with open('requirements.txt', 'r') as f:
    required_packages = [line.strip() for line in f.readlines() if not line.startswith('-e')]

setup(
    name="mcp-agent-example",
    version="0.1.0",
    description="Example project demonstrating an AI agent using MCP for tools",
    author="nghiauet",
    author_email="nghiauet@local",
    packages=find_packages(where="src"),
    package_dir={"": "."},
    python_requires=">=3.8",
    install_requires=required_packages,
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
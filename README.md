# autoclean-eeg2source

A minimal Python package example.

## Installation

### Install from source

```bash
pip install .
```

### Install in development mode

```bash
pip install -e .
```

### Install with development dependencies

```bash
pip install -e ".[dev]"
```

## Building and Publishing

### Build the package

```bash
python -m build
```

### Upload to TestPyPI

First, make sure you have an account on [TestPyPI](https://test.pypi.org/) and have configured your credentials.

```bash
python -m twine upload --repository testpypi dist/*
```

### Install from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps autoclean-eeg2source
```

## Usage

```python
import autoclean_eeg2source

print(autoclean_eeg2source.__version__)

# Use the example function
from autoclean_eeg2source.example import hello_world
print(hello_world())
```

## License

MIT License


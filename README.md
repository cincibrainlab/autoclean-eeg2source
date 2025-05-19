# AutoClean EEG2Source

EEG source localization with Desikan-Killiany (DK) atlas regions. This package converts EEG epochs to source-localized data using the DK brain atlas.

## Features

- Convert EEG epochs to source-localized data with DK atlas regions
- Memory-efficient processing with monitoring
- Support for EEGLAB .set file format
- Batch processing capabilities
- Command-line interface

## Installation

### Requirements

- Python >= 3.8
- MNE-Python 1.6.0
- nibabel
- numpy
- pandas
- loguru
- psutil

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

## Command-Line Usage

The package provides a command-line interface for processing EEG files.

### Process EEG files

Convert EEG epochs to source-localized data:

```bash
autoclean-eeg2source process input.set --output-dir ./results
```

Process multiple files in a directory:

```bash
autoclean-eeg2source process ./data --output-dir ./results --recursive
```

### Validate files

Check if EEG files are valid:

```bash
autoclean-eeg2source validate ./data
```

### Get file information

Display information about an EEG file:

```bash
autoclean-eeg2source info input.set
```

### Advanced options

```bash
autoclean-eeg2source process input.set \
    --output-dir ./results \
    --montage "GSN-HydroCel-129" \
    --resample-freq 250 \
    --lambda2 0.1111 \
    --max-memory 4.0 \
    --log-level INFO
```

## Python API Usage

```python
from autoclean_eeg2source import SequentialProcessor, MemoryManager

# Initialize components
memory_manager = MemoryManager(max_memory_gb=4)
processor = SequentialProcessor(
    memory_manager=memory_manager,
    montage="GSN-HydroCel-129",
    resample_freq=250
)

# Process a file
result = processor.process_file("input.set", "./output")

if result['status'] == 'success':
    print(f"Output saved to: {result['output_file']}")
else:
    print(f"Processing failed: {result['error']}")
```

## Output Format

The package outputs:
- `.set` files with DK atlas regions as channels (68 regions)
- `_region_info.csv` with region metadata (names, hemispheres, positions)

## Building and Publishing

### Build the package

```bash
python -m build
```

### Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

### Install from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps autoclean-eeg2source
```

## License

MIT License
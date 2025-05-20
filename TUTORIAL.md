# AutoClean EEG2Source Tutorial

This tutorial will guide you through using AutoClean EEG2Source, a powerful tool for EEG source localization using the Desikan-Killiany (DK) atlas regions.

## Installation

Install from PyPI using:

```bash
pip install autoclean-eeg2source
```

For development:

```bash
git clone https://github.com/your-username/autoclean-eeg2source.git
cd autoclean-eeg2source
pip install -e ".[dev]"
```

## Basic Usage

AutoClean EEG2Source provides a command-line interface with several commands:

```bash
# Basic command pattern
autoclean-eeg2source [command] [arguments] [options]
```

### Checking File Information

Before processing, it's useful to check information about your EEG files:

```bash
# Display information about a single file
autoclean-eeg2source info path/to/your/eegfile.set
```

This provides details about channels, epochs, sampling rate, and estimated memory requirements.

### Validating Input Files

To ensure files are suitable for processing:

```bash
# Validate a single file or directory of files
autoclean-eeg2source validate path/to/eeg/files --check-montage
```

This checks for proper formatting, montage compatibility, and data quality.

### Basic Processing

To process an EEG file or directory:

```bash
# Process a single file
autoclean-eeg2source process path/to/your/eegfile.set --output-dir ./output
```

```bash
# Process all files in a directory
autoclean-eeg2source process path/to/eeg/directory --output-dir ./output
```

## Advanced Processing Options

### Robust Processing

For enhanced error recovery and handling:

```bash
autoclean-eeg2source process path/to/eeg/files --robust --error-dir ./errors
```

This enables automatic recovery strategies for common issues:
- File format problems
- Montage compatibility
- Data quality issues
- Memory constraints

### Performance Enhancements

#### Parallel Processing

To leverage multiple CPU cores:

```bash
autoclean-eeg2source process path/to/eeg/files --parallel --n-jobs 4
```

For batch processing:

```bash
autoclean-eeg2source process path/to/eeg/directory --parallel --batch-processing
```

#### Memory Optimization

For handling large datasets:

```bash
autoclean-eeg2source process path/to/eeg/files --optimized-memory --max-memory 8.0
```

With disk offloading:

```bash
autoclean-eeg2source process path/to/eeg/files --optimized-memory --disk-offload
```

#### Caching

To reuse intermediate computations:

```bash
autoclean-eeg2source process path/to/eeg/files --enable-cache
```

#### GPU Acceleration

For systems with supported GPUs:

```bash
autoclean-eeg2source process path/to/eeg/files --gpu
```

With specific backend:

```bash
autoclean-eeg2source process path/to/eeg/files --gpu --gpu-backend pytorch
```

## Benchmarking

To evaluate performance across different processing methods:

```bash
autoclean-eeg2source benchmark path/to/eeg/files --test-parallel --test-cached --test-gpu
```

To test all available processors:

```bash
autoclean-eeg2source benchmark path/to/eeg/files --test-all
```

## Example Workflows

### Basic Workflow

```bash
# 1. Check file information
autoclean-eeg2source info path/to/your/eegfile.set

# 2. Validate the file
autoclean-eeg2source validate path/to/your/eegfile.set --check-montage

# 3. Process the file
autoclean-eeg2source process path/to/your/eegfile.set --output-dir ./output
```

### Performance-Optimized Workflow

```bash
# 1. Benchmark to find the best processor for your system
autoclean-eeg2source benchmark path/to/eeg/sample --test-all

# 2. Process files with the best method (example: GPU)
autoclean-eeg2source process path/to/eeg/directory --gpu --enable-cache --batch-processing
```

### Large Dataset Workflow

```bash
# Process a large dataset with memory optimization and error recovery
autoclean-eeg2source process path/to/eeg/dataset --robust \
  --parallel --n-jobs -1 \
  --optimized-memory --disk-offload \
  --enable-cache \
  --error-dir ./errors \
  --save-summary
```

## Output Files

After processing, look for these files in your output directory:

- `*_dk_regions.set` - Source-localized EEG data with DK atlas regions
- `*_region_info.csv` - Metadata for brain regions
- Processing summaries and error reports (if requested)

## Tips for Best Performance

1. **Start Small**: Test with a few files before processing entire datasets
2. **Benchmark First**: Use `benchmark` to find the best processor for your system
3. **Memory Management**: For large files, use `--optimized-memory` and `--disk-offload`
4. **Use Caching**: Enable caching (`--enable-cache`) when processing multiple similar files
5. **Parallel Processing**: Use `--parallel --n-jobs -1` to utilize all available cores
6. **Batch Processing**: Use `--batch-processing` for processing multiple files
7. **Error Handling**: Enable `--robust` for automatic error recovery

## Troubleshooting

If you encounter issues:

1. Check error reports in the error directory (if specified with `--error-dir`)
2. Try using the `--robust` flag for automatic recovery
3. For memory issues, increase `--max-memory` or enable `--disk-offload`
4. For performance issues, use the `benchmark` command to find the best processing strategy

## Further Reading

- [API Documentation](https://autoclean-eeg2source.readthedocs.io/)
- [MNE-Python Documentation](https://mne.tools/stable/index.html)
- [Desikan-Killiany Atlas Reference](https://surfer.nmr.mgh.harvard.edu/fswiki/CorticalParcellation)
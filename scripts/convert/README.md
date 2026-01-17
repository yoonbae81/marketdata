# Data Converter Scripts

Standalone scripts to convert text data files to Parquet format.

## Requirements

Install required Python packages:

```bash
pip install pandas pyarrow numpy
```

Or install all project dependencies:

```bash
pip install -r ../../requirements.txt
```

## Scripts

### kr1m_to_parquet.py

Convert Korean 1-minute market data from text to Parquet format.

**Usage:**
```bash
python kr1m_to_parquet.py <directory>
```

**Example:**
```bash
python kr1m_to_parquet.py data/KR-1m/
```

**Input format:** Tab-separated text files with columns:
- `symbol` (str): Stock symbol
- `price` (int): Price
- `volume` (int): Volume
- `time` (str): Time (HH:MM format)

**Output format:** Parquet files with columns:
- `symbol` (str): Stock symbol
- `dt` (datetime): Datetime
- `price` (int): Price
- `volume` (int): Volume

---

### kr1d_to_parquet.py

Convert Korean daily market data from text to Parquet format.

**Usage:**
```bash
python kr1d_to_parquet.py <directory>
```

**Example:**
```bash
python kr1d_to_parquet.py data/KR-1d/
```

**Input format:** Tab-separated text files with columns:
- `symbol` (str): Stock symbol
- `open` (int): Open price
- `high` (int): High price
- `low` (int): Low price
- `close` (int): Close price
- `volume` (int): Volume

**Output format:** Parquet files with columns:
- `symbol` (str): Stock symbol
- `date` (datetime): Date
- `open` (int): Open price
- `high` (int): High price
- `low` (int): Low price
- `close` (int): Close price
- `volume` (int): Volume

---

### us5m_to_parquet.py

Convert US 5-minute market data from text to Parquet format.

**Usage:**
```bash
python us5m_to_parquet.py <directory>
```

**Example:**
```bash
python us5m_to_parquet.py data/US-5m/
```

**Input format:** Tab-separated text files with columns:
- `symbol` (str): Stock symbol
- `price` (float): Price
- `volume` (int): Volume
- `time` (str): Time (HH:MM format)

**Output format:** Parquet files with columns:
- `symbol` (str): Stock symbol
- `dt` (datetime): Datetime
- `price` (float): Price
- `volume` (int): Volume

## Features

### Automatic Validation

All scripts include built-in validation that:
- Checks if a Parquet file already exists
- Validates the existing Parquet matches the text file
- Skips conversion if valid Parquet exists
- Reconverts if validation fails

**Example output:**
```
[INFO] Found 10 text files to convert
[OK] 2024-01-01.txt -> 2024-01-01.parquet (691696 records)
[SKIP] 2024-01-02.parquet already exists and is valid
[WARN] 2024-01-03.parquet exists but validation failed, reconverting...
[OK] 2024-01-03.txt -> 2024-01-03.parquet (689234 records)
```

### Compression

All Parquet files are created with Snappy compression for optimal:
- Storage efficiency (typically 50-80% size reduction)
- Query performance
- Compatibility

### Error Handling

Scripts handle common errors gracefully:
- Missing input files
- Invalid data formats
- Corrupted Parquet files
- Permission issues

## File Naming Convention

Scripts expect text files to be named with dates in the filename stem (e.g., `2024-01-01.txt`). The date is extracted and used to create datetime columns in the output.

For aggregated files without dates in the filename, the conversion will still work but datetime parsing may fail.

## Standalone Usage

These scripts are fully standalone and can be:
- Copied to any location
- Run without the parent project
- Used independently of other project components

**Minimal setup:**
```bash
# 1. Copy script
cp kr1m_to_parquet.py /path/to/destination/

# 2. Install dependencies
pip install pandas pyarrow numpy

# 3. Run
python kr1m_to_parquet.py /path/to/data/
```

## Performance

Conversion performance depends on:
- File size
- Number of records
- Available memory
- Disk I/O speed

Typical performance:
- **Small files** (< 1MB): < 1 second
- **Medium files** (1-10MB): 1-5 seconds
- **Large files** (> 10MB): 5-30 seconds

## Troubleshooting

### Missing packages
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution:** Install required packages:
```bash
pip install pandas pyarrow numpy
```

### No directory argument
```
error: the following arguments are required: directory
```
**Solution:** Provide directory path:
```bash
python kr1m_to_parquet.py data/KR-1m/
```

### No text files found
```
[WARN] No .txt files found in /path/to/directory
```
**Solution:** Verify the directory contains `.txt` files

### Validation failed
```
[WARN] file.parquet exists but validation failed, reconverting...
```
**Solution:** This is normal - the script will automatically reconvert the file

## License

See parent project LICENSE file.

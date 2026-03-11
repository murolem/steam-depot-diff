# steam-depot-diff
A CLI diff utility for Steam depots.

## Usage

> [!NOTE]
> This is a CLI utility, so to interact with the it you will need to use a terminal.

Grab the [latest release](https://github.com/murolem/steam-depot-diff/releases/latest) matching your OS.

If on Linux, grant the execute permission first:
```bash
chmod +x ./depot-diff-linux-x86_64
```

Assuming the name of the binary is `depot-diff`.
To see available commands, run:
```bash
./depot-diff --help
```

Example output for the latest version:
```bash
%PROGRAM_HELP_OUTPUT
```

## Development

### Requirements
Python 3.9+

### Setup

> [!NOTE]
> All commands are only tested on Linux.

Install dependencies

```bash
pip install -r requirements.txt
```

### Running

To run the script, run:

```bash
python ./main.py
```

### Building

To build for current platform, run:
```bash
pyinstaller -F main.py
```
# steam-depot-diff
A CLI diff utility for Steam depots.

## Usage

> [!NOTE]
> This is a CLI utility, so to interact with the it you will need to use a terminal.

Grab the [latest release](https://github.com/murolem/steam-depot-diff/releases/latest) matching your OS.

Create a folder and put the binary/executable in there since it will create some files. 

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
```text
%PROGRAM_HELP_OUTPUT
```

### Depot downloading
#### Using plain format

Let's take https://steamdb.info/depot/799603/manifests/

Format:
```bash
./depot-diff app depot manifest_top manifest_base
```

Example:
```bash
./depot-diff 799600 799603 2424067790439047639 2424067790439047639
```

If we want a particular branch, a `--branch argument` can be provided. For example, taking https://steamdb.info/depot/1022982/manifests/

**Result:**
```bash
./depot-diff 1022980 1022982 4145694655358607165 7534689703142416349  --branch arena_mode
```

#### Using _Steam console_ format

Let's take https://steamdb.info/depot/1022982/manifests/

> [!WARNING]
> _Steam console_ format **does not** support branches, so to specify a branch use `--branch` argument.

When using custom formats, each formatted string **must be** enclosed in quotes.

Format:
```bash
./depot-diff "download_depot app depot manifest-top" "download_depot app depot manifest-base"
```

Example using the copy button on SteamDB with _Steam console_ as chosen format. 
First let's copy the first manifest (top) and add it to the command, enclosed in quotes:
```bash
./depot-diff "download_depot 1022980 1022982 4145694655358607165"
```

Then let's copy the second manifest (base) and add it to the end, also enclosed in quotes.
Additionaly, let's manually specify the branch since the format doesn't support it.

**Result:**
```bash
./depot-diff "download_depot 1022980 1022982 4145694655358607165" "download_depot 1022980 1022982 7534689703142416349" --branch arena_mode
```

#### Using _DepotDownloader_ format

Let's take https://steamdb.info/depot/1022982/manifests/

When using custom formats, each formatted string **must be** enclosed in quotes.

Format:
```bash
./depot-diff "-app app -depot depot -manifest manifest" "-app app -depot depot -manifest manifest"
```

Example using the copy button on SteamDB with _DepotDownloader_ as chosen format.
First let's copy the first manifest (top) and add it to the command, enclosed in quotes:
```bash
./depot-diff "-app 1022980 -depot 1022982 -manifest 4145694655358607165 -beta arena_mode"
```

Then let's copy the second manifest (base) and add it to the end, also enclosed in quotes.
Additionaly, let's manually specify the branch since the format doesn't support it.

**Result:**
```bash
./depot-diff "-app 1022980 -depot 1022982 -manifest 4145694655358607165 -beta arena_mode" "-app 1022980 -depot 1022982 -manifest 7534689703142416349 -beta arena_mode"
```


### Diffing

The diff is automatically created after depots are downloaded.

To view the diff, use any tool that supports Git diffing. Something like VS Code will do.

See `--help` for options such as enabling commiting the top depot changes.

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
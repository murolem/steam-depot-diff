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
usage: Steam Depot Differ [-h] [--version] [--branch BRANCH]
                          [--dd-args DD_ARGS] [--depots-path DEPOTS_PATH]
                          [--dd-path DD_PATH] [--redownload-dd]
                          [--diff-path DIFF_PATH] [--commit-diff] [--relogin]
                          [--creds-path CREDS_PATH]
                          app_or_depot_string_top [depot_or_depot_string_base]
                          [manifest_top] [manifest_base]

Downloads app depots and diffs changes between them.

positional arguments:
  app_or_depot_string_top
                        Application ID or TOP depot string. 
                        
                        If used as application ID, other positional arguments must be provided. 
                        Example: 722730
                        
                        If used as a depot string, a string enclosed in quotes containing information about the TOP app & depot & manifest must be provided in this singular argument.
                        TOP meaning the depot will be applied on TOP of another depot. 
                        BASE string is expected as the next positional argument.
                        This is useful for when copying depot strings straight from SteamDB.
                        
                        Examples:
                        NOTE: If using Steam console format and a branch depot, the branch MUST be specified with --branch
                        +-----------------+----------------------------------------------------------------------------------------------------------------------------------+
                        | Format          | Command                                                                                                                          |
                        +=================+==================================================================================================================================+
                        | Steam console   | ./depot-diff "download_depot 329130 329133 1446294067501623196" "download_depot 329130 329133 5541496194205663540"               |
                        |                 |                              ^app   ^depot ^manifest from                                     ^manifest to                       |
                        +-----------------+----------------------------------------------------------------------------------------------------------------------------------+
                        | DepotDownloader | ./depot-diff "-app 329130 -depot 329133 -manifest 1446294067501623196" "-app 329130 -depot 329133 -manifest 5541496194205663540" |
                        |                 |                    ^app          ^depot           ^manifest from                                            ^manifest to         |
                        +-----------------+----------------------------------------------------------------------------------------------------------------------------------+
  depot_or_depot_string_base
                        Depot ID or BASE depot string.
                        
                        If used as a depot ID, other positional arguments must be provided.
                        Example: 799601
                        
                        If used as a depot string, a string enclosed in quotes containing information about the BASE app & depot & manifest must be provided in this singular argument.
                        BASE meaning the other depot will be applied on TOP of this one. 
                        See first positional argument help for examples.
                         (default: None)
  manifest_top          Manifest ID of manifest to diff with. Example: 5090889475431819364 (default: None)
  manifest_base         Manifest ID of manifest to base the diff at. Example: 4892202388027804689 (default: None)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

DEPOTS:
  --branch BRANCH       Download from specified branch if available. Public by default. Takes precedence over branch specified in depot string, if any. (default: None)
  --dd-args DD_ARGS     Additional args to pass to DepotDownloader for each depot download. (default: None)
  --depots-path DEPOTS_PATH
                        Directory path for storing depots. (default: depot-diff/depots)

DEPOT DOWNLOADER:
  --dd-path DD_PATH     DepotDownloader binary directory. Created and downloaded automatically from the official repo if missing. (default: depot-diff/DepotDownloader)
  --redownload-dd       Deletes existing DepotDownloader binary (if any) and downloads it again. (default: False)

DIFF:
  --diff-path DIFF_PATH
                        Directory path for diff process. This is where the diff will happen and can be viewed. (default: depot-diff/diff)
  --commit-diff         Commits the diff. May be preferred if viewing the commited changes vs uncommited is more convenient. (default: False)

CREDENTIALS:
  --relogin             Removes any saved Steam credentials. Useful if entered wrong. (default: False)
  --creds-path CREDS_PATH
                        Path to the file containing credentials. (default: depot-diff/.env)

Source code: https://github.com/murolem/steam-depot-diff

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
# vtoes-tattoo-merger
This merges V—Toes toenail polish with tattoo mods so that users can use both of them on their OC. It is meant for PRIVATE USE ONLY.

## Requirements

- Python 3.10+ installed and added to your system PATH.
- WolvenKit.CLI installed globally via .NET tools.

## Installation

### 1. Install Python
Download Python 3.10+ from: https://www.python.org/downloads/

During installation, make sure to check "Add Python to PATH".

### 2. Install WolvenKit CLI
run this in powershell cli

```bash
dotnet tool install --global WolvenKit.CLI --version 8.16.1
```

If you get an error like:

```
error NU1301: Unable to load the service index for source https://api.nuget.org/v3/index.json.
error NU1101: Unable to find package WolvenKit.CLI. No packages exist with this id in source(s): nuget.org
```

Fix it with:

```bash
dotnet nuget add source https://api.nuget.org/v3/index.json -n nuget.org
```

Then rerun the install command.

## How to Use

1. cick:
```bash
run.bat
```
3. Follow the prompts to select the archive and desired overlay color.
4. The modified archive will be saved in the same directory with `_V-Toes_<color>.archive` suffix.

## Notes

- This script uses `WolvenKit.CLI` commands `uncook`, `import`, and `pack`.
- If errors occur, check that WolvenKit CLI is installed correctly and in your system path.


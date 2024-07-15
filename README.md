# Git Hook

This repository provides pre-commit scripts that can be used to enforce coding standards and add copyright header
comments to your C++ (cpp/h) files. By using this repository as a submodule in your project, you can easily integrate
these scripts into your development workflow.

## Features

The provided scripts support the following functionalities:

- Format C++ (cpp/h) source files according to Google style guidelines.
- Add copyright header comments to C++ (cpp/h) source files.

## Directory Structure

```
git_hook
│
├── one-shot-script
│   ├── add-header-to-all-files.sh
│   ├── add-header-to-changed-files.sh
│   ├── format-all-files.sh
│   └── format-changed-files.sh
│
├── python
│   └── tools.py
│
├── README.md
└── setup.sh
```

- `python/tools.py`: A utility script containing the core functions used by the other scripts.
- `one-shot-script/`: Contains one-shot scripts that can be run independently or be hooked to the pre-commit process.
  - `add-header-to-all-files.sh`: Adds a copyright header to all C++ source files in the repository.
  - `add-header-to-changed-files.sh`: Adds a copyright header only to changed C++ source files.
  - `format-all-files.sh`: Formats all C++ source files according to Google style guidelines.
  - `format-changed-files.sh`: Formats only changed C++ source files according to Google style guidelines.
- `setup.sh`: A setup script to integrate the one-shot scripts into the pre-commit process.

## Usage

To integrate this repository into your project, follow these steps:

### Step 1: Add as a Submodule

Add this repository as a submodule to your project.

```bash
git submodule add -b master ssh://git@192.168.4.94:2200/toolchain/git_hook.git
git submodule update --init --recursive
```

### Step 2: Run the Setup Script

Run the `setup.sh` script located in the root directory of the submodule to set up the pre-commit hooks.

```bash
bash git_hook/setup.sh
```

This script will append the necessary commands to your project's `.git/hooks/pre-commit` file.

### Step 3: Verify Pre-commit Hooks

After running the setup script, the following commands will be appended to your `.git/hooks/pre-commit` file:

- Format changed C++ files using Google style guidelines.
- Add copyright headers to changed C++ files.

## One-shot Scripts

You can also run the one-shot scripts independently if needed. Below are the commands to run each script:

### Format All Files

Format all C++ source files in the repository.

```bash
./git_hook/one-shot-script/format-all-files.sh
```

### Format Changed Files

Format only the changed C++ source files.

```bash
./git_hook/one-shot-script/format-changed-files.sh
```

### Add Header to All Files

Add copyright header comments to all C++ source files.

```bash
./git_hook/one-shot-script/add-header-to-all-files.sh
```

### Add Header to Changed Files

Add copyright header comments only to the changed C++ source files.

```bash
./git_hook/one-shot-script/add-header-to-changed-files.sh
```

## Conclusion

By integrating this repository as a submodule and running the setup script, you can easily enforce coding standards and
copyright policies in your project. The one-shot scripts provide additional flexibility to perform these operations
manually if needed.

Feel free to contribute and enhance the functionalities as per your project's requirements.
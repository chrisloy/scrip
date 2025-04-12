# scrip
A simple command-line tool for flattening directory structures into a single text file, and restoring them with ease. It’s like zip, but instead of compressing your files into a binary format, it concatenates everything into a readable, copy-paste-friendly text file. Perfect for quick deployments via clipboard, LLM contexts, or just when you need to keep things simple.

## Installation
To install scrip, just download the script or use your preferred package manager once it's available.

```bash
brew install scrip
```

Or use pip for the Python version:

```bash
pip install scrip
```

## Usage
### Command
- `scrip <directory>`: Flatten a directory structure into a single text file
- `unscrip <file>`: Restore the directory structure and files from a scrip-created text file

### Examples

#### 1. Flatten a directory:

```bash
scrip my_project_folder
```

This will output a single text file containing all the files from my_project_folder in their original order.

#### 2. Restore the directory:

```bash
unscrip my_project.scrip
```

This will recreate the original folder structure and its contents, just like it was before.

## Why Use scrip?
- **Clipboard-friendly**: Copy-paste your entire directory structure to and from your terminal with ease.

- **LLM-friendly**: Handy for supplying your codebase or data to a large language model in a single text block without losing structure.

- **Simplicity**: While zip focuses on binary compression, scrip focuses on human-readable simplicity.

- **Emergency recovery**: When all you need is plain text and simple structure, scrip is your fallback.

## Development
Clone the repo, install dependencies, and start contributing!

## License
Scrip is open-source and available under the MIT License. See LICENSE for more details.

## Contributing
Feel free to fork the project and submit a pull request! Contributions, issues, and bug reports are always welcome.

# oneshot

`oneshot` is a small command-line tool for sending **single, stateless requests** to large language models. It is built for cases where you do not want an ongoing chat session—just a prompt, a response, and optionally a CSV file with the results.

At the moment, `oneshot` supports:

- **Ollama**
- **OpenAI Responses API**
- **Text-only** and **image + text** prompts
- **Single requests** and **batch processing**
- **Terminal output** or **CSV output**

## What “one shot” means

In this project, *one shot* means there is **no stored conversation history**. Each request is assembled from the configuration file, sent to the chosen provider, and handled independently.

That makes `oneshot` useful for tasks like:

- running the same prompt over many images
- evaluating a CSV of text prompts
- extracting text from scanned images
- quick ad-hoc model calls from the command line

## Features

- Simple CLI: `oneshot -c <config.toml>`
- TOML-based configuration
- Batch image processing from a directory
- Batch text processing from a CSV file
- Structured CSV output with query id, provider, timestamp, model name, response text, elapsed time, and usage information
- Compatible with local models through Ollama and hosted models through OpenAI

## Requirements

- Python **3.13+**
- Access to **either**:
  - an **Ollama** server, or
  - an **OpenAI API key**
- For image workflows: `.png`, `.jpg`, or `.jpeg` files

## Installation

### Install from GitHub

```bash
uv pip install git+https://github.com/joheli/oneshot.git
```

This installs the `oneshot` command-line application.

### Install from a local clone

```bash
git clone https://github.com/joheli/oneshot.git
cd oneshot
uv venv --python 3.13
uv pip install .
```

## Quickstart

The repository ships with example configuration files.

### Example 1: batch image queries

```bash
oneshot -c oneshot_images.toml
```

This runs a prompt over the sample images in `demo/input` and writes the results to a CSV file.

### Example 2: OCR / text extraction from images

```bash
oneshot -c oneshot_text_from_images.toml
```

### Example 3: batch text queries from CSV

```bash
oneshot -c oneshot_batch_text.toml
```

## CLI usage

```bash
oneshot --help
oneshot -c path/to/config.toml
```

The only CLI option is the config file:

- `-c`, `--config`: path to the TOML configuration file

If omitted, `oneshot` looks for a file named `oneshot.toml` in the current directory.

## Configuration overview

`oneshot` is controlled entirely through a TOML file with three top-level sections:

- `[vendor]`
- `[query]`
- `[out]`

### 1. `[vendor]`

Choose and configure at least one provider.

#### Ollama

```toml
[vendor.ollama]
host = "http://localhost:11434"
```

#### OpenAI

```toml
[vendor.openai]
api_key = "sk-..."
```

Your `[query].target` must match a configured provider.

### 2. `[query]`

This section defines what gets sent to the model.

Supported query types:

- `singleton-text`
- `singleton-image`
- `batch-text`
- `batch-image`

Common fields:

```toml
[query]
type = "batch-text"
target = "ollama"
model_name = "gemma3:4b"
temperature = 0
```

### 3. `[out]`

Controls where results go.

```toml
[out]
mode = "file"
csv_file = "demo/output/out.csv"
csv_file_separator = ";"
# further optional parameters:
response_to_file_length_threshold = 300               # default = 300, answers over 300 characters are written to separate file `response_to_file_filename`
response_to_file_filename = "~qid~_llm_response.txt"  # `~qid~` is a placeholder and will be replaced by query id 
```

Output modes:

- `standard` → print responses to the terminal
- `file` → save responses to CSV and optionally long responses to text files

## Query types in detail

### `singleton-text`

Send one text prompt.

Expected fields under `[query.details]`:

- `instructions`
- `context`
- `question`

Example:

```toml
[query]
type = "singleton-text"
target = "openai"
model_name = "gpt-4o-mini"
temperature = 0

[query.details]
instructions = "Answer briefly and accurately."
context = "Paris is the capital of France."
question = "What is the capital of France?"
```

### `singleton-image`

Send one image plus a text prompt.

Expected fields:

- `instructions`
- `question`
- `image`

Example:

```toml
[query]
type = "singleton-image"
target = "ollama"
model_name = "gemma3:4b"
temperature = 0.2

[query.details]
instructions = "Answer briefly."
question = "Do you see raspberries?"
image = "demo/input/berries.png"
```

### `batch-text`

Read prompts from a CSV file and send one request per row.

Expected fields:

- `csv_file`
- `csv_file_separator`
- `colname_query_id`
- `colname_instructions`
- `colname_questions`
- optionally `colname_contexts`

Example:

```toml
[query]
type = "batch-text"
target = "ollama"
model_name = "gemma3:4b"
temperature = 0

[query.details]
csv_file = "demo/input/queries.csv"
csv_file_separator = ","
colname_query_id = "qid"
colname_instructions = "instructions"
colname_questions = "questions"
colname_contexts = "contexts"
```

#### Expected CSV structure

A minimal CSV for `batch-text` should look like this:

```csv
qid,instructions,questions,contexts
q1,"Answer briefly.","What is 2 + 2?",""
q2,"Use the context.","Who is the daughter?","Dragan and Yasmina have a daughter called Sohar."
```

### `batch-image`

Run the same prompt over all images in a directory.

Expected fields:

- `instructions`
- `question`
- `img_dir`
- optionally `img_dir_glob`: specifies which files to match in `img_dir`
- optionally `img_qid`: "filename" as default, i.e. the whole filename is used as the query id (qid) in the output csv file
- optionally `img_qid_regex`: if `img_qid` is set to 'filename-regex', a regex pattern extracting a character sequence of interest from the filename is used as qid

Example:

```toml
[query]
type = "batch-image"
target = "ollama"
model_name = "gemma3:4b"
temperature = 0.2

[query.details]
instructions = "Describe the image in one sentence."
question = "What is shown here?"
img_dir = "demo/input"
img_dir_glob = "*.png"
```

## Notes and gotchas

- At least one provider must be configured in `[vendor]`.
- The selected provider in `[query].target` must also be configured.
- For file output, if the output CSV exists the filename is appended an integer.
- For `batch-text`, the input CSV must contain the configured column names.
- For `batch-image`, each matching file becomes one request.
- The example files in the repository are a good starting point:
  - `oneshot_images.toml`
  - `oneshot_text_from_images.toml`
  - `oneshot_batch_text.toml`

## When to use `oneshot`

`oneshot` is a good fit when you want a lightweight, scriptable interface for LLM calls without building a chat app or workflow engine.

It is especially handy for:

- local experimentation with Ollama
- quick model benchmarking on repeated prompts
- image labeling or extraction jobs
- generating CSV outputs for downstream analysis

## Project structure

```text
src/oneshot/
├── cli.py
├── config.py
├── llm_request.py
├── llm_response.py
├── tables.py
└── utils.py
```

## Acknowledgements

Thanks to the creators of:

- NumPy
- Polars
- Pydantic
- Rich
- Typer
- uv

## License

MIT

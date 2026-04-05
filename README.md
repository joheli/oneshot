# oneshot

`oneshot` is a library to issue "one shot" calls to large language models (LLMs). 

## one shot?

'One shot' means that the chat history is not stored. Actually, there is no 'chat' at all! Just questions and (hopefully) helpful answers from the LLM of your choosing.

## Quickstart (1 minute)

```bash
git clone https://github.com/joheli/oneshot.git
cd oneshot

uv venv --python 3.13
uv pip install .

oneshot -c oneshot_images.toml
```

This processes the sample images in `demo/input` and writes results to `demo/output/out1.csv`. 

---

### further demos (2 minutes)

Try also

```bash
oneshot -c oneshot_text_from_images.toml
```

for a demo on text extraction, and

```bash
oneshot -c oneshot_batch_text.toml
```

for a demo on oneshot text-only calls to LLMs.

## Requirements

- Python 3.13+
- Images in .png, .jpg, or .jpeg
- Access to either
  - a ollama server, or 
  - an active OpenAI API key

---

## Install

Type `uv pip install https://github.com/joheli/oneshot.git` to install, preferably into a fresh environment. This makes application `oneshot` available from the command line.

## Usage

After successful installation in a fresh environment you should have access to the command line executable `oneshot`. To verify, type 
`oneshot --help` to get a help message. There is only one optional argument to be passed with the `-c` flag (alternatively
use `--config`), which specifies the configuration file in toml format. Have a look at [oneshot.toml](oneshot.toml), 
which contains helpful comments, to get a lay of the land. 

### Configuration

`oneshot` is entirely controlled by the configuration file. Please familiarize yourself with it by perusing [oneshot.toml](oneshot.toml).

#### Vendor

This section allows the specification of the LLM provider. Currently, you can only select `ollama` or `openai`.

#### Query

There are four different _query types_, namely `singleton-text`, `singleton-image`, `batch-text`, and `batch-image`.

The `singleton` variants are meant for debugging. I do not expect you to find them useful.

The `batch` variants, on the other hand, can pass a number of queries to an LLM and save the responses in a csv file (see table `out` in the toml config file for specifying the output file).

The `batch-text` variant currently allows you to store "contexts" in a column of a csv file. I am aware that this is presently of limited use, so please regard it as proof-of-concept. I plan to have context searches implemented soon. So hang on to your hats!

#### Out

In this section you can specify if LLM responses are 
  * output to the command line (default), or
  * saved to a csv file (`mode = "file"`)

## Acknowledgements

I would like to thank the creators of [NumPy](https://numpy.org/), [Polars](https://pola.rs/), [Pydantic](https://docs.pydantic.dev/latest/), [Rich](https://rich.readthedocs.io), [Typer](https://typer.tiangolo.com/), and [uv](https://docs.astral.sh). They bring light into darkness. 




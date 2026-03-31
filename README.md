# oneshot

`oneshot` is a library to issue "one shot" calls to large language models (LLMs). 

## one shot?

'One shot' means that the chat history is not stored. Actually, there is no 'chat' at all! Just questions and (hopefully) helpful answers from the LLM of your choosing.

## Install

Type `pip install https://github.com/joheli/oneshot.git` to install (optionally prepend with `uv`). You should execute the command in a fresh virtual environment, preferably created with [uv](https://docs.astral.sh/uv/) (i.e. after installation of uv type `uv venv`, then activate the environment with `source .venv/bin/activate`).

## Usage

After successful installation in a fresh environment you should have access to the command line executable `oneshot`. To verify, type 
`oneshot --help` to get a help message. There is only one optional argument to be passed with the `-c` flag (alternatively
use `--config`.), which specifies the configuration file in toml format. Have a look at [oneshot.toml](oneshot.toml), 
which contains helpful comments, to get a lay of the land. 

### Hints

There are four different _query types_, namely `singleton-text`, `singleton-image`, `batch-text`, and `batch-image`.

The `singleton` variants are meant for debugging. I do not expect you to find them useful.

The `batch` variants, on the other hand, can pass a number of queries to an LLM and save the responses in a csv file (see table `out` in the toml config file for specifying the output file).

The `batch-text` variant currently allows you to store "contexts" in a column of a csv file. I am aware that this is presently of limited use, so please regard it as proof-of-concept. I plan to have context searches implemented soon. So hang on to your hats.




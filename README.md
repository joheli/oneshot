# oneshot

`oneshot` is a library to issue "one shot" calls to large language models (LLMs). 

## one shot?

'One shot' means that the chat history is not stored. Actually, there is no 'chat' at all! Just a question and (hopefully) a helpful answer from the LLM.

## Install

Type `pip install https://github.com/joheli/oneshot.git` to install. You should execute the command in a fresh virtual environment, preferably created with [uv](https://docs.astral.sh/uv/) (after installation of uv type `uv venv` then activate the environment).

## Usage

After successful installation in a fresh environment you should have access to the command line executable `oneshot`. Type 
`oneshot --help` to get a help message. There really is only an optional argument to be passed using the `-c` flag (alternatively
with `--config`.), specifying the config toml file. Have a look at [oneshot.toml](oneshot.toml) to get a lay of the land. 
It should be fairly self-explanatory. 

### Hints

There are four different _query types_, namely `singleton-text`, `singleton-image`, `batch-text`, and `batch-image`.

The `singleton` variants are really just for debugging. I do not expect you to find them useful.

The `batch` variants, on the other hand, can pass a number of queries to an LLM and extract their responses to subsequently be stored in a csv file (see table `out` in the toml config file).

The `batch-text` variant currently allows you to store "contexts" and i am aware that this is of limited use, so regard it as proof-of-concept. I plan to have these columns replaced by a context searches based on the question. So hang on to your hats.




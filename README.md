Development Requirements
------------------------

1. Python 3.x
2. Make


Optional, But Convenient to Have During Development
---------------------------------------------------

While you can use `virtualenv` to manage your virtual environment by hand,
using the following will make your life easier since you won't have to
remember to activate and de-activate the virtualenv whenever you enter this
project directory in the CLI.

1. [Pyenv](https://github.com/pyenv/pyenv)
2. [Pyenv Virtualenv Plugin](https://github.com/pyenv/pyenv-virtualenv)

Ensure that you've created the terminus virtualenv using the
`pyenv-virtualenv` plugin by running the following in this project dir.

```
pyenv virtualenv <PREFERRED-PYTHON-3-VERSION> $(cat ./.python-version)
```


Development Getting Started
---------------------------

Install all development dependencies

```
make dev-dependencies
```

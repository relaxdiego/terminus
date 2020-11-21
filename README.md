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
make devdeps
```


Learning Journal
----------------

2020-11-21T19:50:00+0800

I've implemented the notes that I wrote down in my previous entry. This
new set up does offer better flexibility. I would like to get to a point
where I only have to declare group data and host data in a single file
but that can be the next step.

There's the tricky bit where pyinfra (or Jinja2?) does not fail when a
reference host data or fact is not present. We need to ensure that it
fails loudly if the data is not defined otherwise we may end up with
templates that are mis-rendered.


2020-11-21T17:30:00+0800

Running the following allows us to print host facts and data. Make sure
to run the following against sha `501458b`.
 
```
pyinfra sample-data/main.py blueprints/10-machines/kvm/main.py
```

It looks like pyinfra doesn't support supplying arbitrary data files via
the CLI so we cannot define group vars outside of the deploy tree. It
might be better to use packaged deploys instead. The initial plan is:

1) Convert the `blueprints/` subdir into a tree of
   [packaged deploys](https://docs.pyinfra.com/en/1.x/api/deploys.html).
   They can all be installed using a common `setup.py` in the root dir.
   Also have requirements-dev.txt (or whichever appropriate file) install
   them as editable modules.

2) Get rid of the `sample-data/` subdir as its name and purpose will be
   obsolete after this change.

3) Create `sample-deploys/` which will then contain an example deploy
   layout. Use the example from [pyinfra-etcd](https://github.com/Fizzadar/pyinfra-etcd/tree/develop/example)
   as reference.



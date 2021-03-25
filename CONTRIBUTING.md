# Contributing

Contributions are welcome.
When contributing to this repository, please first discuss the change you wish to make via issue. 
Exceptions to this are fixed typos or small bugfixes, for which obviously no issue is required.
Please make sure that all your additions to the code are covered by unit tests.

You can also contribute without committing code: 
Bug reports, feature requests, documentation are highly beneficial to any open source software project!

Please note we have a code of conduct, please follow it in all your interactions with the project.


### Tips for contributors

To install locally, run:

```bash
pip install -e .
```

You will need to install the development dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[test,lint]"
```

To run the test suite, simply execute 

```bash
pytest
```

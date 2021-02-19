![docstr-coverage](https://github.com/HunterMcGushion/docstr_coverage/raw/master/docs/logo_wide.png)

<p align="center">
    <a href="https://choosealicense.com/licenses/mit/" alt="License: MIT">
        <img src="https://img.shields.io/badge/license-MIT-green.svg" /></a>
    <img src="https://github.com/HunterMcGushion/docstr_coverage/workflows/Python%20package/badge.svg" />
    <a href='https://docstr-coverage.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/docstr-coverage/badge/?version=latest' alt='Documentation Status' />
    </a>
    <a href="https://pypi.org/project/docstr-coverage/">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/docstr-coverage">
    </a>
    <a href="https://img.shields.io/pypi/pyversions/docstr-coverage">
        <img alt="Python Version" src="https://img.shields.io/pypi/pyversions/docstr-coverage">
    </a>
    <a href="https://pepy.tech/project/docstr-coverage">
        <img alt="Download count" src="https://static.pepy.tech/personalized-badge/docstr-coverage?period=total&units=international_system&left_color=gray&right_color=orange&left_text=downloads">
    </a>
    <a href="https://black.readthedocs.io/en/stable/" alt="Code Style: Black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" />
    </a>
</p>

`docstr-coverage` is a simple tool that lets you measure your Python source code's
[docstring](http://www.python.org/dev/peps/pep-0257/#what-is-a-docstring) coverage. 
It shows which of your functions, classes, methods, and modules don't have docstrings. 
It also provide statistics about overall docstring coverage for individual files, and for your entire project.

- [Source](https://github.com/HunterMcGushion/docstr_coverage)
- [Documentation](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html)

## Example

```bash
>>> HunterMcGushion$ docstr-coverage /docstr_coverage/

File: "docstr_coverage/setup.py"
 - No module docstring
 - No docstring for `readme`
 Needed: 2; Found: 0; Missing: 2; Coverage: 0.0%

File: "docstr_coverage/docstr_coverage/__init__.py"
 - No module docstring
 Needed: 1; Found: 0; Missing: 1; Coverage: 0.0%

File: "docstr_coverage/docstr_coverage/coverage.py"
 - No docstring for `DocStringCoverageVisitor.__init__`
 Needed: 11; Found: 10; Missing: 1; Coverage: 90.9%


Overall statistics for 3 files:
Docstrings needed: 14; Docstrings found: 10; Docstrings missing: 4
Total docstring coverage: 71.4%;  Grade: Very good
```

## How Do I Use It

### Command-line Tool

General usage is: `docstr-coverage <path to dir or module> [options]`

To test a single module, named `some_module.py`, run:

```bash
docstr-coverage some_module.py
```

To test a directory (recursively), just supply the directory `some_project/src` instead:

```bash
docstr-coverage some_project/src
```

#### Options

- _--skip-magic, -m_ - Ignore all magic methods (except `__init__`)
- _--skip-init, -i_ - Ignore all `__init__` methods
- _--skip-file-doc, -f_ - Ignore module docstrings (at the top of files)
- _--skip-private, -P_ - Ignore private functions (starting with a single underscore)
- _--skip-class-def, -c_ - Ignore docstrings of class definitions
- _--accept-empty, -a_ - Exit with code 0 if no Python files are found (default: exit code 1)
- _--exclude=\<regex\>, -e \<regex\>_ - Filepath pattern to exclude from analysis
  - To exclude the contents of a virtual environment `env` and your `tests` directory, run:
  ```docstr-coverage some_project/ -e ".*/(env|tests)"```
- _--verbose=\<level\>, -v \<level\>_ - Set verbosity level (0-3, default: 3)
  - 0 - Silence
  - 1 - Print overall statistics
  - 2 - Also print individual statistics for each file
  - 3 - Also print missing docstrings (function names, class names, etc.)
- _--fail-under=<int|float>, -F <int|float>_ - Fail if under a certain percentage of coverage (default: 100.0)
- _--docstr-ignore-file=\<filepath\>, -d \<filepath\>_ - Filepath containing list of patterns to ignore. Patterns are (file-pattern, name-pattern) pairs
  - File content example:

  ```
  SomeFile method_to_ignore1 method_to_ignore2 method_to_ignore3
  FileWhereWeWantToIgnoreAllSpecialMethods __.+__
  .* method_to_ignore_in_all_files
  a_very_important_view_file ^get$ ^set$ ^post$
  detect_.* get_val.*
  ```
- _--badge=\<filepath\>, -b \<filepath\>_ - Generate a docstring coverage percent badge as an SVG saved to a given filepath
  - Include the badge in a repo's README using 
  ```[![docstr_coverage](<filepath/of/your/saved/badge.svg>)](https://github.com/HunterMcGushion/docstr_coverage)```,
  where `<filepath/of/your/saved/badge.svg>` is the path provided to the `--badge` option
- _--follow-links, -l_ - Follow symlinks
- _--percentage-only, -p_ - Output only the overall coverage percentage as a float, silencing all other logging
- _--help, -h_ - Display CLI options

#### Config File
All options can be saved in a config file named `.docstr.yaml`
example:
```yaml
paths: # list or string
  - docstr_coverage
badge: docs # Path
exclude: .*/test # regex
verbose: 1 # int (0-3)
skip_magic: True # Boolean
skip_file_doc: True # Boolean
skip_init: True # Boolean
skip_class_def: True # Boolean
skip_private: True # Boolean
follow_links: True # Boolean
accept_empty: True # Boolean
ignore_names_file: .*/test # regex
fail_under: 90 # int 
percentage_only: True # Boolean
ignore_patterns: # Dict with key/value pairs of file-pattern/node-pattern
  .*: method_to_ignore_in_all_files
  FileWhereWeWantToIgnoreAllSpecialMethods: "__.+__"
  SomeFile:
    - method_to_ignore1
    - method_to_ignore2
    - method_to_ignore3
  a_very_important_view_file:
    - "^get$"
    - "^set$"
    - "^post$"
  detect_.*:
    - "get_val.*"
```
equivalent to
```
docstr-coverage docstr_coverage -e ".*/test" --skip-magic --skip-init --badge="docs" --skip-class-def etc...
```

Note that options passed as command line arguments have precedence over options 
configured in a config file.
Exception: If a `--docstr-ignore-file` is present and the yml config contains `ignore_patterns`,
a `ValueError` is raised.

#### Overriding by Comments
Note that `docstr-coverage` can not parse 
dynamically added documentation (e.g. through class extension).
Thus, some of your code which deliberately has no docstring might be counted as uncovered.

You can override this by adding either ```#docstr_coverage:inherited``` 
(intended for use if a docstring is provided in the corresponding superclass method)
or a generic excuse with a reason, like ```#docstr_coverage:excused `My probably bad excuse` ```.
These have to be stated right above any class or function definition 
(or above the functions annotations, if applicable).
Such class or function would then be counted as if they had a docstring.

```python
# docstr-coverage:excused `no one is reading this anyways`
class FooBarChild(FooBar):

    # docstr-coverage:inherited
    def function(self):
        pass
```

#### Package in Your Project

You can also use `docstr-coverage` as a part of your project by importing it thusly:

```python
from docstr_coverage import get_docstring_coverage
my_coverage = get_docstring_coverage(['some_dir/file_0.py', 'some_dir/file_1.py'])
```

##### Arguments

- Required arg: `filenames` \<list of string filenames\>
- Optional kwargs: `skip_magic` \<bool\>, `skip_file_docstring` \<bool\>, `skip_private` \<bool\>, `verbose` \<int (0-3)\> \* For more info on `get_docstring_coverage` and its parameters, please see its [documentation](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html#get-docstring-coverage)

##### Results

`get_docstring_coverage` returns two dicts: 1) stats for each file, and 2) total stats.
For more info, please see the `get_docstring_coverage` [documentation](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html#get-docstring-coverage)

## Why Should I Use It

- Thorough documentation is important to help others (and even yourself) understand your code
- As a developer, improve your code's maintainability for when you need to make updates and fix bugs
- As a user, instantly know how easy it's going to be to understand a new library \* If its documentation coverage is low, you may need to figure a lot out for yourself

## Installation

```bash
pip install docstr-coverage
```

If you like being on the cutting-edge, and you want all the latest developments, run:

```bash
pip install git+https://github.com/HunterMcGushion/docstr_coverage.git
```

## Contributing

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

Make sure to run tests:

```bash
pytest
```

Be nice.

## Special Thanks

Thank you to Alexey "DataGreed" Strelkov, and James Harlow for doing all the hard work.
`docstr-coverage` simply revives and brings their efforts to Python 3. See 'THANKS.txt' for more information.

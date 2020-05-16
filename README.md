Docstr-Coverage
===============

If the health of your documentation is in dire straits, `docstr-coverage` will see you now.

`docstr-coverage` is a simple tool that lets you measure your Python source code's
[docstring](http://www.python.org/dev/peps/pep-0257/#what-is-a-docstring) coverage. It can show you which of your functions,
classes, methods, and modules don't have docstrings. It also provide statistics about overall docstring coverage for individual
files, and for your entire project.

* **Source:** https://github.com/HunterMcGushion/docstr_coverage
* **Documentation:** [https://docstr-coverage.readthedocs.io](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html)

Example
-------

```
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

How Do I Use It?
----------------

#### Command-line Tool
General usage is: `docstr-coverage <path to dir or module> [options]`

To test a single module, named `some_module.py`, run:

```
$ docstr-coverage some_module.py
```

To test a directory (recursively), just supply the directory `some_project/src` instead:

```
$ docstr-coverage some_project/src
```

##### Options:
* *--skipmagic, -m* - Ignore all magic methods (like `__init__`, and `__str__`)
* *--skipfiledoc, -f* - Ignore module docstrings (at the top of files)
* *--exclude=\<regex\>, -e \<regex\>* - Filepath pattern to exclude from analysis
	* To exclude the contents of a virtual environment `env` and your `tests` directory, run:
	<br>```$ docstr-coverage some_project/ -e "env/*|tests/*"```
* *--verbose=\<level\>, -v \<level\>* - Set verbosity level (0-3)
	* 0 - Silence
	* 1 - Print overall statistics
	* 2 - Also print individual statistics for each file
	* 3 - Also print missing docstrings (function names, class names, etc.)
* *--docstr-ignore-file=<filepath>, -d <filepath>* - Filepath containing list of patterns to ignore. Patterns are (file-pattern, name-pattern) pairs
* *--failunder=<int|float>, -F <int|float>* - Fail if under a certain percentage of coverage (default: 100.0)
       
    * File content example:
    ```
    SomeFile method_to_ignore1 method_to_ignore2 method_to_ignore3
    FileWhereWeWantToIgnoreAllSpecialMethods __.+__
    .* method_to_ignore_in_all_files
    a_very_important_view_file ^get$ ^set$ ^post$
    detect_.* get_val.*
    ```

#### Package in Your Project
You can also use `docstr-coverage` as a part of your project by importing it thusly:

```python
from docstr_coverage import get_docstring_coverage
my_coverage = get_docstring_coverage(['some_dir/file_0.py', 'some_dir/file_1.py'])
```

##### Arguments:
* Required arg: `filenames` \<list of string filenames\>
* Optional kwargs: `skip_magic` \<bool\>, `skip_file_docstring` \<bool\>, `verbose` \<int (0-3)\>
	* For more info on `get_docstring_coverage` and its parameters, please see its [documentation](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html#get-docstring-coverage)

##### Results:
```get_docstring_coverage``` returns two dicts: 1) stats for each file, and 2) total stats.
For more info, please see the `get_docstring_coverage` [documentation](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html#get-docstring-coverage)

Why Should I Use It?
--------------------
* Thorough documentation is important to help others (and even yourself) understand your code
* As a developer, improve your code's maintainability for when you need to make updates and fix bugs
* As a user, instantly know how easy it's going to be to understand a new library
	* If its documentation coverage is low, you may need to figure a lot out for yourself

Installation
------------

```
pip install docstr-coverage
```

If you like being on the cutting-edge, and you want all the latest developments, run:

```
pip install git+https://github.com/HunterMcGushion/docstr_coverage.git
```

Special Thanks
--------------
Thank you to Alexey "DataGreed" Strelkov, and James Harlow for doing all the hard work.
`docstr-coverage` simply revives and brings their efforts to Python 3. See 'THANKS.txt' for more information.

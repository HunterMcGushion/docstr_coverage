<a name="Unreleased"></a>
## [Unreleased]

...


<a name="2.1.0"></a>
## [2.1.0] (2021-06-25)

### Features
- Add pre-commit hook. [#78] by [bjornconstructors]
- *Experimental:* Expose new `analyze` method, which returns fine-grained coverage reports. [#67] by [MiWeiss]

### Bug Fixes
- Remove a false AssertionError which was raised for long docstrings. [#82] by [MiWeiss]


<a name="2.0.1"></a>
## [2.0.1] (2021-03-03)

### Bug Fixes
- Fix `--help`/`-h` flag. [#57] by [MiWeiss].


<a name="2.0.0"></a>
## [2.0.0] (2021-01-11)

### Features
- Add `.docstr.yaml` config file. [#39] by [mBouamama].
    - Save docstr-coverage CLI options in `.docstr.yaml` to be used as the default configuration
    - For more details, see the [README's "Config File" section](https://github.com/HunterMcGushion/docstr_coverage#config-file) 
- Allow `ignore_patterns` to be defined in the `.docstr.yaml` config file. [#46] by [MiWeiss]. 
    - This is an alternative to the `--docstr-ignore-file` CLI option. Do not use both at the same time
- Add `--accept-empty`/`-a` flag to exit with code 0 if no `.py` files are found. [#48] by [MiWeiss].
    - Helpful for using `docstr_coverage` in GitHub Actions as described in [#47] by [epassaro]

### Deprecations
- Convert all CLI options to kebab-case. [#38] by [cthoyt].
    
    | New                | Deprecated       |
    |--------------------|------------------|
    | `--fail-under`     | `--failunder`    |
    | `--follow-links`   | `--followlinks`  |
    | `--skip-class-def` | `--skipclassdef` |
    | `--skip-file-doc`  | `--skipfiledoc`  |
    | `--skip-init`      | `--skipinit`     |
    | `--skip-magic`     | `--skipmagic`    |
    
    - :exclamation: **Deprecated option names will be removed in v3.0.0** :exclamation:

### Bug Fixes
- Fix Windows compatibility issues and upgrade CI suite. [#45] by [MiWeiss].


<a name="1.4.0"></a>
## [1.4.0] (2020-12-05)

### Features
* Excuse missing docstrings by marking classes/functions with special comments. [#34] by [MiWeiss].
    * `# docstr_coverage: inherited` to mark subclass methods as being documented by their parent
    * ```# docstr_coverage: excused `My bad excuse` ``` to arbitrarily excuse missing docstrings
    * Find examples and more information [here](https://github.com/HunterMcGushion/docstr_coverage#overriding-by-comments)


<a name="1.3.0"></a>
## [1.3.0] (2020-11-17)

### Features
* Add ability to skip private functions. [#32] by [cthoyt].


<a name="1.2.0"></a>
## [1.2.0] (2020-07-21)

### Features
* Added ability to pass multiple paths to CLI for docstring inspection. [#24] by [HunterMcGushion].
* Added `--badge`/`-b` option to generate a docstring coverage percent badge as an SVG image saved 
  to a given filepath. [#22] by [HunterMcGushion].

### Bug Fixes
* Fixed bug where a total coverage of 0 would break everything. [#16] by [killthekitten].
* Fixed bug where the `-d`/`--docstr-ignore-file` CLI option to provide an `ignore_names_file` 
  would not work with `-v 3`/`--verbose=3`. [#19] by [HunterMcGushion].

### Changes
* Added testing safety net. [#16] by [killthekitten].


<a name="1.1.0"></a>
## [1.1.0] (2020-05-20)

### Features
* Added `--failunder`/`-F` option to fail if coverage is below a given percentage. [#11] by [econchick].
    * Default=100.0


<a name="1.0.5"></a>
## [1.0.5] (2019-11-18)

### Features
* Added `--docstr-ignore-file`/`-d` option to provide a file, containing a list of patterns to 
  ignore during coverage calculation. [#4] by [Redysz].
* Added support for raising the exit code to be used with CI pipelines. [#6] by [sim0nx].


<a name="1.0.4"></a>
## [1.0.4] (2019-04-17)

### Features
* Added support for non-ASCII characters. [#3] by [Redysz].


<a name="1.0.3"></a>
## [1.0.3] (2019-01-28)

### Bug Fixes
* Fixed bug preventing `docstr-coverage` from being properly installed via tox. [#2] by [asergeant01].


<a name="0.1.0"></a>
## 0.1.0 (2018-08-01)

### Features
* Initial release


[Unreleased]: https://github.com/HunterMcGushion/docstr_coverage/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/HunterMcGushion/docstr_coverage/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.4.0...v2.0.0
[1.4.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.5...v1.1.0
[1.0.5]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.2...v1.0.3


[asergeant01]: https://github.com/asergeant01
[bjornconstructors]: https://github.com/bjornconstructors
[cthoyt]: https://github.com/cthoyt
[econchick]: https://github.com/econchick
[epassaro]: https://github.com/epassaro
[HunterMcGushion]: https://github.com/HunterMcGushion
[killthekitten]: https://github.com/killthekitten
[mBouamama]: https://github.com/mBouamama
[MiWeiss]: https://github.com/MiWeiss
[Redysz]: https://github.com/Redysz
[sim0nx]: https://github.com/sim0nx


[#2]: https://github.com/HunterMcGushion/docstr_coverage/pull/2
[#3]: https://github.com/HunterMcGushion/docstr_coverage/pull/3
[#4]: https://github.com/HunterMcGushion/docstr_coverage/pull/4
[#6]: https://github.com/HunterMcGushion/docstr_coverage/pull/6
[#11]: https://github.com/HunterMcGushion/docstr_coverage/pull/11
[#16]: https://github.com/HunterMcGushion/docstr_coverage/pull/16
[#19]: https://github.com/HunterMcGushion/docstr_coverage/pull/19
[#22]: https://github.com/HunterMcGushion/docstr_coverage/pull/22
[#24]: https://github.com/HunterMcGushion/docstr_coverage/pull/24
[#32]: https://github.com/HunterMcGushion/docstr_coverage/pull/32
[#34]: https://github.com/HunterMcGushion/docstr_coverage/pull/34
[#38]: https://github.com/HunterMcGushion/docstr_coverage/pull/38
[#39]: https://github.com/HunterMcGushion/docstr_coverage/pull/39
[#45]: https://github.com/HunterMcGushion/docstr_coverage/pull/45
[#46]: https://github.com/HunterMcGushion/docstr_coverage/pull/46
[#47]: https://github.com/HunterMcGushion/docstr_coverage/issues/47
[#48]: https://github.com/HunterMcGushion/docstr_coverage/pull/48
[#57]: https://github.com/HunterMcGushion/docstr_coverage/pull/57
[#67]: https://github.com/HunterMcGushion/docstr_coverage/pull/67
[#78]: https://github.com/HunterMcGushion/docstr_coverage/pull/78
[#82]: https://github.com/HunterMcGushion/docstr_coverage/pull/82
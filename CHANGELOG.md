<a name="Unreleased"></a>
## [Unreleased]

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


[Unreleased]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.5...v1.1.0
[1.0.5]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/HunterMcGushion/docstr_coverage/compare/v1.0.2...v1.0.3


[asergeant01]: https://github.com/asergeant01
[econchick]: https://github.com/econchick
[HunterMcGushion]: https://github.com/HunterMcGushion
[killthekitten]: https://github.com/killthekitten
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
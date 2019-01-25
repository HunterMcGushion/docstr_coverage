from setuptools import setup, find_packages


def readme():
    with open("README.md") as f:
        return f.read()


MAJOR, MINOR, MICRO = 1, 0, 2
__VERSION__ = "{}.{}.{}".format(MAJOR, MINOR, MICRO)

setup(
    name="docstr_coverage",
    version=__VERSION__,
    description=" ".join(
        [
            "Utility for examining python source files to ensure proper documentation.",
            "Lists missing docstrings, and calculates overall docstring coverage percentage rating",
        ]
    ),
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="docstring coverage documentation audit source code statistics report",
    url="https://github.com/HunterMcGushion/docstr_coverage",
    author="Hunter McGushion",
    author_email="hunter@mcgushion.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    test_suite="nose.collector",
    tests_require=["nose"],
    entry_points=dict(console_scripts=["docstr-coverage=docstr_coverage.coverage:_execute"]),
    classifiers=(
        # TODO: Check Python 2 compatibility
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities",
    ),
)

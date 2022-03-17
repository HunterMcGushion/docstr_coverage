from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


MAJOR, MINOR, MICRO = 2, 2, 0
__VERSION__ = "{}.{}.{}".format(MAJOR, MINOR, MICRO)

setup(
    name="docstr-coverage",
    version=__VERSION__,
    description=(
        "Utility for examining python source files to ensure proper documentation. "
        "Lists missing docstrings, and calculates overall docstring coverage "
        "percentage rating."
    ),
    long_description_content_type="text/markdown",
    long_description=readme(),
    keywords="docstring coverage documentation audit source code statistics report",
    url="https://github.com/HunterMcGushion/docstr_coverage",
    author="Hunter McGushion",
    author_email="hunter@mcgushion.com",
    license="MIT",
    packages=["docstr_coverage"],
    install_requires=["click", "PyYAML"],
    extras_require={
        "lint": ["flake8==3.9.2", "black==21.5b2", "isort==5.9.0"],
        "test": ["pytest==6.2.5", "pytest-mock==3.4.0"],
    },
    include_package_data=True,
    zip_safe=False,
    entry_points=dict(console_scripts=["docstr-coverage=docstr_coverage.cli:execute"]),
    classifiers=[
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
    ],
)

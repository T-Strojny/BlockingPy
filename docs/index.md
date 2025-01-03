# Welcome to BlockingPy's Documentation

[![License](https://img.shields.io/github/license/T-Strojny/BlockingPy)](https://github.com/T-Strojny/BlockingPy/blob/main/LICENSE) 
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Python version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/codecov/c/github/T-Strojny/BlockingPy)](https://codecov.io/gh/T-Strojny/BlockingPy)\
[![PyPI version](https://img.shields.io/pypi/v/blockingpy.svg)](https://pypi.org/project/blockingpy/) 
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://github.com/T-Strojny/BlockingPy/actions/workflows/run_tests.yml/badge.svg)](https://github.com/T-Strojny/BlockingPy/actions/workflows/run_tests.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/T-Strojny/BlockingPy)](https://github.com/T-Strojny/BlockingPy/commits/main)

```{toctree}
:maxdepth: 2
:caption: Contents

getting_started/index
user_guide/index
examples/index
api/index
changelog
```

```{include} ../README.md
:start-after: "# BlockingPy"
:end-before: "## Installation"
```
## Key Features

- **Multiple ANN Algorithms**: Supports FAISS, HNSW, Voyager, Annoy, MLPack, and NND
- **Flexible Input**: Works with text data, sparse matrices, or dense feature vectors
- **Customizable Processing**: Configurable text processing and algorithm parameters
- **Performance Focused**: Optimized for both accuracy and computational efficiency
- **Easy Integration**: Simple API that works with pandas DataFrames
- **Quality Assessment**: Built-in evaluation metrics when true matches are known

If you're new to BlockingPy, we recommend following these steps:

1. Start with the {ref}`getting-started` guide to set up BlockingPy
2. Try the {ref}`quickstart` guide to see basic usage examples
3. Look at {ref}`examples` to understand more about BlockingPy
4. Explore the {ref}`user-guide` for detailed usage instructions
5. Obtain more information via {ref}`api`

## License

BlockingPy is released under [MIT license](https://github.com/T-Strojny/BlockingPy/blob/main/LICENSE).

## Issues

Feel free to report any issues, bugs, suggestions with github issues [here](https://github.com/T-Strojny/BlockingPy/issues).

## Contributing

Please see [CONTRIBUTING.md](https://github.com/T-Strojny/BlockingPy/blob/main/CONTRIBUTING.md) for more information.

## Acknowledgements

This package is based on the R [blocking](https://github.com/ncn-foreigners/blocking/tree/main) package developed by [BERENZ](https://github.com/BERENZ). Special thanks to the original author for his foundational work in this area.

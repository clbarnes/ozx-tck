# ozx-tck

A Technology Compatibility Toolkit for the .ozx format,
described in [RFC-9 of the OME-Zarr specification](https://ngff.openmicroscopy.org/rfc/9/index.html).

## Features

- [x] generate valid, warning, and error test cases
- [x] validate existing .ozx files

Implementors of .ozx should use these files to check that their own implementations can correctly validate the resulting data,
and that the .ozx files they produce are valid and standards-compliant.

## Usage

This package provides a CLI, `ozx-tck`.
Use it with `uvx` or by installing with `uv tool install`.

`pipx` or `pip` may work as well.

`ozx-tck` provides two subcommands, `generate` and `validate`.
Get usage information with

- `ozx-tck --help`
- `ozx-tck generate --help`
- `ozx-tck validate --help`

Use [`fetch_data.sh`](./fetch_data.sh) to fetch a small test OME-Zarr dataset.

## Limitations

- `validate` cannot detect whether ZIP64 is used in all cases, because [zipfile](https://docs.python.org/3/library/zipfile.html) does not provide easy access to that information

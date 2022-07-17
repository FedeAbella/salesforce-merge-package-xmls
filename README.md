# Salesforce: Merge several package.xml files into one

When working with `sfdx` and/or change sets, you may come to a point when you need to get multiple `package.xml` files (e.g.: for migrating metadata between environments, or pushing them to some external VCS). In those cases, retrieving the metadata using `sfdx:source:retrieve` would require multiple calls to the API, and more importantly, for some metadata types, later calls might overwrite the metadata retrieved by earlier ones. This is particularly the case when different members of a single metadata type are not saved to separate files, but only those retrieved for are saved to one single file.
The same can happen if you're trying to merge the unzipped data that already came when you might have used `sfdx:mdapi:retrieve` to say, get the package files in the first place.

In such situations, you might want to go through the entire set of `package.xml` files, and just create a single one that aggregates the entire metadata requests. This is where this script comes in.

This is a *very simple* python script which looks for all `package.xml` files recursively within a directory, and then create a single file containing all metadata types and members.

## Requirements

The script requires Python 3 to run, and the modules `xmltodict os argparse`. You can get them if missing using `pip`, or your OS repositories (e.g.: Ubuntu using `apt`)

## Usage

```
usage: merge_packages.py [-h] [-v] [-o OUTPUT] source

Merge all package.xml files found in tree with root at
SOURCE into a single package.xml file. Makes the package version the greatest version amongst those found in
source files. The package is written to STDOUT unless -o
is included.

positional arguments:
  source                source directory where to get
                        package.xml files from

options:
  -h, --help            show this help message and exit
  -v, --verbose         make program more verbose
  -o OUTPUT, --output OUTPUT
                        output directory to write the
                        merged package to. If not
                        present, package is written to
                        STDOUT.
```

## Contributions and critique

At time of writing, this is the first passable version I came up with when trying to solve for this issue, and I'm definitely not an expert in Python, which I code in mostly as a hobby or to try and make simple stuff like this. Any constructive criticism is welcome, and freel free to comment how this could be improved.

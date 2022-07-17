'''
merge_packages.py: Looks for all files named package.xml in subdirectory tree
rooted at SOURCE, then merges all of them into a single package.xml files
containing the entire metadata types and members from those packages. The
result is output to STDOUT unless the -o flag is used to write to a directory.
In that case, the result is written to OUTPUT/package.xml. The resuling package
uses the greatest version number from all included packages, and metadata types
and members are returned sorted alphabetically
'''
from xmltodict import parse, unparse
import argparse
import os

def parse_arguments():
    '''
    Creates the argument parser so SOURCE can be passed as argument, the -o
    flag can be used to optionally pass an OUTPUT directory, and -v to request
    more information on the program running
    '''
    parser = argparse.ArgumentParser(
        description='Merge all package.xml files found in tree with root at '\
            + 'SOURCE into a single package.xml file. '\
            + 'Makes the package version the greatest version '\
            + ' amongst those found in source files. The package is written '\
            + ' to STDOUT unless -o is included.'
    )
    parser.add_argument('-v', '--verbose', 
        help='make program more verbose', action='store_true'
    )
    parser.add_argument('source',
        help='source directory where to get package.xml files from'
    )
    parser.add_argument('-o', '--output', 
        help='output directory to write the merged package to. '\
            + 'If not present, package is written to STDOUT.'
    )
    
    return parser.parse_args()

def validate_paths(args):
    '''
    Validates that the argument SOURCE and the optional argument OUTPUT, if
    passed, are valid existing directories, so they can be read from and
    written to. Raises an error if either directory is invalid.
    '''

    # Get the absolute path to SOURCE, expanding the ~ hoeme var if necessary
    sourcepath = os.path.abspath(
        os.path.expanduser(
            args.source
        )
    )

    # Raise an error if the path to source does not exist, or is a file
    if (not os.path.exists(sourcepath)) or os.path.isfile(sourcepath):
        raise ValueError(f'SOURCE not a valid directory: {sourcepath}')

    # Build the absolute path to OUTPUT, if the -o flag was included
    outpath = os.path.abspath(
        os.path.expanduser(
            args.output
        )
    ) if args.output else None

    # Raise an error if the path to OUTPUT does not exist (and is not STDOUT)
    # of if it exists but points to a file
    if outpath and (
        (not os.path.exists(outpath)) or\
        os.path.isfile(sourcepath)
    ):
        raise ValueError(f'OUTPUT is not a valid directory: {outpath}')

    return sourcepath, outpath

def merge(packages, outpath, verbose):
    '''
    Takes all found package.xml files, converts each to a dictionary, then
    aggregates metadata types and members in a separate dict. At the end,
    re-writes into a template of an SFDC package, replacing it with the 
    aggregated metadata. The result is printed to STDOUT or to a file in the 
    OUTPUT directory
    '''

    if verbose: print('\n//// MERGING PACKAGES\n')

    types_dict = {} # Initialize the dictionary of metadata types
    package_names = [] # Initialize the list of package names
    max_version = None # Initialize the max version number
    template = None # Initialize the package template to use as format

    for filepath in packages:
        with open(filepath, 'r') as package: 
            # Read the package.xml file and parse into a dict
            xml_data = package.read()
            package_dict = parse(xml_data)

            # Check the xml file is a valid SFDC package, or skip it.
            if 'Package' not in package_dict or\
                'version' not in package_dict['Package'] or\
                'types' not in package_dict['Package']:

                if verbose:    
                    print(f'{filepath} is not a valid SFDC package. Skipping.')

                break

            if verbose: print(f'Processing {filepath}')

            # Add the package name to the ones used for the merged file
            package_names.append(package_dict['Package']['fullName'])

            # Update the max package version number
            if not max_version:
                max_version = float(package_dict['Package']['version'])
            max_version = max(
                max_version, 
                float(package_dict['Package']['version'])
            )

            # Create the template from the first processed file
            if not template:
                template = package_dict
            
            # Get all the types tag, and make into list if there's only one
            mdt_types = package_dict['Package']['types']
            if type(mdt_types) == dict:
                mdt_types = [mdt_types]

            # Add the types to the dict if not there, then add members
            for mdt_type in mdt_types:
                if mdt_type['name'] not in types_dict.keys():
                    types_dict[mdt_type['name']] = set()

                members = mdt_type['members']
                # If there's only one member, put it into list form
                if type(members) == str:
                    members = [members]
                types_dict[mdt_type['name']].update(members)

    package_names.sort() # Sort the package names (not paths) alphabetically
    # Replace the template's name
    template['Package']['fullName'] = 'Merged_Package'
    # Replace the temaplte's description, include used package names
    template['Package']['description'] = 'This package.xml was created by ' +\
        'merging the following packages:\n' + '\n'.join(package_names)
    # Replace template's version by max version
    template['Package']['version'] = f'{max_version:.1f}'
    # Empty the template's types tags
    template['Package']['types'] = []
    # Get the metadata types names and order them alphabetically
    ordered_names = list(types_dict.keys())
    ordered_names.sort()

    # Get the members of each metadata type, and add them to the package in
    # alphabetical order, then add the name tag inside the types tag
    for mdt_name in ordered_names:
        members = list(types_dict[mdt_name])
        members.sort()
        template['Package']['types'].append(
            {
                'members': members,
                'name': mdt_name
            }
        )
    
    if verbose:
        print('\nMerging complete. package.xml created from packages:')
        print('\n'.join(package_names))

    # If there's no -o flag, print the merged package to STDOUT, then return
    if not outpath:
        print('\n//// MERGED PACKAGE:\n')
        print(
            unparse(template, pretty=True)
        )
        return
    
    # Write the merged package to the OUTPUT path
    with open(outpath + '/package.xml', 'w') as file:
        file.write(
            unparse(template, pretty=True)
        )

    if verbose: print(f'\npackage.xml written to {outpath}')

def main():
    '''
    Parses input arguments, validates that SOURCE and OUTPUT are valid
    directories. If they are, gets all files named package.xml in a
    tree rooted at SOURCE, and merges them into a single package.xml file
    '''

    args = parse_arguments() # Get the arguments from the parser

    # Validate that SOURCE and OUTPUT are actual directories
    sourcepath, outpath = validate_paths(args)

    # Get all package.xml files in subdirectory tree with root at sourcepath
    packages = [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(sourcepath)
        for filename in (
            f for f in filenames if f == 'package.xml'
        )
    ]

    if packages: packages.sort() # Sort package paths alphabetically

    if args.verbose: # Inform found packages if verbose flag is on
        if not packages:
            print('No packages found in subdirectory tree with root at SOURCE'\
                +f'({sourcepath})')
            return
        print('//// FOUND PACKAGES\n')
        print(f'{len(packages)} package files found:')
        for package in packages:
            print(package)

    if not packages: return # If no package files found, exit

    merge(packages, outpath, args.verbose) # Merge the found packages

if __name__ == '__main__':
    main()
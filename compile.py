#!/usr/bin/env python3
"""
Simple preprocessor/compiler for Ezalia.
Compiles all source files into a self-contained Python file for easy distribution.
"""

def compile_file(src, dst):
    """
    Preprocess/compile a file, and write the result to a different file.
    
    :param src: Source path
    :param dst: Destination path or file-like object
    """
    import io
    import re
    # read in the entire source
    with open(src, 'r') as file:
        src_raw = file.read()
    # split into lines to work on it
    src_lines = src_raw.splitlines()
    # build up the result
    dst_blobs = []
    for src_line in src_lines:
        # check for import macro
        match = re.match(r'\s*#\s*EZALIA-IMPORT\s+(\w+)', src_line)
        if match is not None:
            import_name, = match.groups()
            import_path = src.parent / (import_name + '.py')
            imported_buffer = io.StringIO()
            compile_file(import_path, imported_buffer)
            imported_raw = imported_buffer.getvalue()
            dst_blobs.append(imported_raw)
            continue
        # nothing special to do
        dst_blobs.append(src_line)
    # join the blobs
    dst_raw = '\n'.join(dst_blobs)
    # write the final result
    if not isinstance(dst, io.TextIOBase):
        dst = open(dst, 'w')
    with dst as file:
        file.write(dst_raw)

def main():
    """
    Main function for the Ezalia compiler.
    """
    import pathlib
    main_src = pathlib.Path('src') / 'ezalia.py'
    main_dst = pathlib.Path('ezalia.py')
    compile_file(main_src, main_dst)

if __name__ == '__main__':
    main()

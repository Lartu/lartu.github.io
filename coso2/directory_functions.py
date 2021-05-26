import os
from config import *
from message_functions import *


def delete_old_build_directory():
    '''Deletes the old existing docs (build) directory.
    '''
    show(f"Cleaning build directory.")
    os.system(f"rm -rf \"{get_docs_dir()}\" && mkdir \"{get_docs_dir()}\"")


def copy_styles_file():
    '''Copies the styles file to the build directory.
    '''
    show(f"Copying styles file.")
    os.system(f"cp \"{get_styles_file()}\" \"{get_docs_dir()}/styles.css\"")


def copy_CNAME_file():
    '''Copies the CNAME file to the build directory.
    '''
    show(f"Copying CNAME file.")
    os.system(f"cp \"{get_CNAME_file()}\" \"{get_docs_dir()}/CNAME\"")


def create_images_directory():
    '''Creates the images directory inside the build directory.
    '''
    show(f"Creating images directory.")
    os.system(f"mkdir \"{get_docs_dir()}/images\"")
    os.system(f'''cp "{get_images_dir()}/{get_favicon_name()}" "{get_docs_dir()}/images/{get_favicon_name()}"''')
    os.system(f'''cp -R "{get_images_dir()}/analisis" "{get_docs_dir()}/images/analisis"''')  # Imagenes de analisis
    os.system(f'''echo "forbidden" > "{get_docs_dir()}/images/index.html"''')
    os.system(f'''echo "forbidden" > "{get_docs_dir()}/images/analisis/index.html"''')


def create_files_directory():
    '''Creates the files directory inside the build directory.
    '''
    show(f"Creating files directory.")
    os.system(f'''cp -R "{get_files_dir()}" "{get_docs_dir()}/files"''')
    os.system(f'''echo "forbidden" > "{get_docs_dir()}/files/index.html"''')


def get_files_to_be_compiled():
    '''Returns a list of all the files to be compiled.
    '''
    files_to_be_compiled = []
    directory = os.fsencode(get_sources_dir())
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".coso") and filename[0] != "_" and filename != "sitemap.coso" and filename != "changelog.coso":
            files_to_be_compiled.append(filename)
    show(f"Found {len(files_to_be_compiled)} files to be compiled.")
    return files_to_be_compiled


def load_file_contents(filename):
    '''Loads the contents of a text file.
    '''
    show(f"Loading file «{filename}».")
    with open(get_sources_dir() + "/" + filename, "r") as f:
        return f.read()


def save_compiled_file(filename, file_contents):
    '''Saved a compiled file.
    '''
    compiled_filename = get_compiled_filename(filename)
    show(f"Saving compiled {filename} as «{compiled_filename}».")
    with open(get_docs_dir() + "/" + compiled_filename, "w+") as f:
        f.write(file_contents)


def get_compiled_filename(source_name):
    '''Returns the compiled filename of a source file. Fails if the
    passed filename is not that of a source file.
    '''
    if ".coso" not in source_name:
        error(f"The file {source_name} is not a source file.")
    return source_name.replace(".coso", ".html")
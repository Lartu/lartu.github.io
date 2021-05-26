#   ___
#  / __|___ ___ ___
# | (__/ _ (_-</ _ \ 2.0
#  \___\___/__/\___/ Future Proofed
# by Lartu, www.lartu.net - 2021-05-26

from message_functions import *
from changelog_manager import *
from directory_functions import *
from compile_functions import *

if __name__ == "__main__":
    # Say hi
    show("Coso 2.0 (Future Proofed) - by Lartu.")
    show("www.lartu.net")
    show("Compilation started.")

    # Load changelogs from previous compilations
    load_changelog()

    # Create and set up destination directory
    delete_old_build_directory()
    copy_styles_file()
    copy_CNAME_file()
    create_images_directory()
    create_files_directory()

    # Get all files to be compiled
    files_to_be_compiled = get_files_to_be_compiled()
    for filename in files_to_be_compiled:
        file_contents = load_file_contents(filename)
        html_page = compile_source_and_rss(file_contents, filename)
        save_compiled_file(filename, html_page)

    # Generate RSS feed
    generate_rss_file()

    # Compile changelog

    # Compile sitemap
    filename = "sitemap.coso"
    file_contents = load_file_contents(filename)
    html_page = compile_source_and_rss(file_contents, filename)
    save_compiled_file(filename, html_page)

    # Announce that the compilation is complete
    show("Compilation complete.")
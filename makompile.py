#    _____          __                        .__.__          
#   /     \ _____  |  | ______   _____ ______ |__|  |   ____  
#  /  \ /  \\__  \ |  |/ /  _ \ /     \\____ \|  |  | _/ __ \ 
# /    Y    \/ __ \|    <  <_> )  Y Y  \  |_> >  |  |_\  ___/ 
# \____|__  (____  /__|_ \____/|__|_|  /   __/|__|____/\___  >
#         \/     \/     \/           \/|__|                \/ 
# A static website / personal wiki generator based on txt files.
# 24L25
# TO-DO:
# - If the file is a local link and is not found (relative), become red and crossed.
# - If the file is external, add an arrow or something.

from typing import List, Dict, Any, Tuple
from enum import Enum
import re
import sys
from pathlib import Path
from datetime import datetime
import os
import shutil
import subprocess


SOURCE_DIRECTORY = "source"
RESULT_DIRECTORY = "docs"
INCLUDED_FOLDER = "include"


class SCSET(Enum):  # "Section Compilation Settings"
    NO_TITLES = 1
    NO_LISTS = 2
    LIST_DEPTH = 3
    NO_PARAGRAPH = 4
    NO_RESTORE_CODE = 5


def error(message: str):
    print("+------------------+")
    print("| Makompile Error! |")
    print("+------------------+")
    print("Makompile couldn't compile <CURRENT FILE>. The error was:")
    print(message)
    sys.exit(1)


def make_link(text: str, destination: str) -> str:
    if destination.lower().strip() in document_names:
        # Local Makompile Links
        destination = translate_page_name(Path(destination.lower().strip()))
        return f"<a href=\"{destination}\">{text}</a>"
    elif ("https://" or "http://" not in destination) and (".html" in destination):
        # Local HTML Links
        return f"<a href=\"{destination}\">{text}</a>"
    else:
        # External Links
        return f"<a href=\"{destination}\" target=_blank>{text}</a>"


def compile_section(section: str, settings: Dict[SCSET, Any] = {}, code_match_replacements = []) -> str:
    if not section:
        return ""

    # +-----------------------------+
    # | Title and subtitle sections |
    # +-----------------------------+
    if SCSET.NO_TITLES not in settings:
        # -- Title --
        if len(section) > 1 and section[0] == "#" and section[1] != "#":
            return "<h1>" + compile_section(
                section[1:].strip(),
                {
                    SCSET.NO_TITLES: True,
                    SCSET.NO_LISTS: True,
                    SCSET.NO_PARAGRAPH: True,
                }
            ) + "</h1>"

        # -- Subtitle --
        if len(section) > 2 and section[0:2] == "##" and section[2] != "#":
            return "<h2>" + compile_section(
                section[2:].strip(), 
                {
                    SCSET.NO_TITLES: True,
                    SCSET.NO_LISTS: True,
                    SCSET.NO_PARAGRAPH: True,
                }
            ) + "</h2>"

        # -- Subsubtitle --
        if len(section) > 3 and section[0:3] == "###" and section[3] != "#":
            return "<h3>" + compile_section(
                section[3:].strip(), 
                {
                    SCSET.NO_TITLES: True,
                    SCSET.NO_LISTS: True,
                    SCSET.NO_PARAGRAPH: True,
                }
            ) + "</h3>"

    # +------+
    # | Code |
    # +------+
    code_matches = re.findall(r'`.*?`', section, re.DOTALL)
    for code_match in code_matches:
        tag_contents = code_match[1:-1].strip()
        code_match_replacements.append(tag_contents)
        section = section.replace(code_match, f"<CODE:{len(code_match_replacements) - 1}>")

    # +-----------+
    # | Bold Text |
    # +-----------+
    code_matches = re.findall(r'\*\*.*?\*\*', section, re.DOTALL)
    for code_match in code_matches:
        tag_contents = code_match[2:-2].strip()
        section = section.replace(code_match, f"<b>{tag_contents}</b>")

    # +------------+
    # | Small Text |
    # +------------+
    code_matches = re.findall(r'_\*.*?\*_', section, re.DOTALL)
    for code_match in code_matches:
        tag_contents = code_match[2:-2].strip()
        section = section.replace(code_match, f"<small>{tag_contents}</small>")

    # +------------+
    # | List Items |
    # +------------+
    if SCSET.NO_LISTS not in settings:
        if section[0] == "*" or section[0] == "%":
            list_bullet = section[0]
            section_lines = section.split("\n")
            list_items = []
            for line in section_lines:
                if line[0] == list_bullet:
                    list_items.append(line)
                else:
                    list_items[-1] += f"\n{line}"
            if list_bullet == "*":
                list_html = "<ul>"
            else:
                list_html = "<ol>"
            for list_item in list_items:
                content = list_item[1:].strip()
                content_lines = content.split("\n")
                list_html += "\n<li>"
                sublist_parts = [""]
                depth = 2 if SCSET.LIST_DEPTH not in settings else settings[SCSET.LIST_DEPTH] + 2
                for content_line in content_lines:
                    if len(content_line) >= depth + 1 and content_line[0:depth+1] == f"{depth * ' '}{list_bullet}":
                        content_line = content_line[depth:]
                        sublist_parts.append(content_line)
                    else:
                        sublist_parts[-1] += f"\n{content_line}"
                for sublist_part in sublist_parts:
                    list_html += "\n" + compile_section(
                        sublist_part, 
                        {
                            SCSET.NO_TITLES: True,
                            SCSET.LIST_DEPTH: depth,
                            SCSET.NO_PARAGRAPH: True,
                            SCSET.NO_RESTORE_CODE: True,
                        }
                    )
                list_html += "\n</li>"
            if list_bullet == "*":
                list_html += "\n</ul>"
            else:
                list_html += "\n</ol>"
            return compile_section(
                list_html,
                {
                    SCSET.NO_TITLES: True,
                    SCSET.NO_LISTS: True,
                    SCSET.NO_PARAGRAPH: True,
                },
                code_match_replacements
            )

    # +--------+
    # | Images |
    # +--------+
    image_matches = re.findall(r'\[\[.*?\]\]', section, re.DOTALL)
    for image_match in image_matches:
        tag_contents = image_match[2:-2].strip()
        if not tag_contents:
            error(f"The image tag '{image_match}' is empty.")
        tokens = tag_contents.split("|")
        image_info = {
            "img": "",
            "alt": "",
            "link": "",
            "class": ""
        }
        for token in tokens:
            token = token.strip()
            parts = token.split(" ", 1)
            if len(parts) != 2:
                error(f"The image tag '{image_match}' has an invalid parameter: '{token}'.")
            command = parts[0].lower()
            if command in image_info:
                if image_info[command]:
                    error(f"The image tag '{image_match}' has duplicated too many '{command}' parameters.")
                else:
                    image_info[command] = parts[1]
        if not image_info["img"]:
            error(f"The image tag '{image_match}' is missing the image path.")
        html_image_tag = f"<img src=\"{image_info['img']}\""
        if image_info["alt"]:
            html_image_tag += f" alt=\"{image_info['alt']}\""
        if image_info["class"]:
            html_image_tag += f" class=\"{image_info['class']}\""
        html_image_tag += ">"
        if image_info["link"]:
            html_image_tag = make_link(html_image_tag, image_info["link"])
        section = section.replace(image_match, html_image_tag)

    # +-------+
    # | Links |
    # +-------+
    link_matches = re.findall(r'\[.*?\]', section, re.DOTALL)
    for link_match in link_matches:
        tag_contents = link_match[1:-1].strip()
        if not tag_contents:
            error(f"The link tag '{link_match}' is empty.")
        tokens = tag_contents.split("|")
        if len(tokens) > 2:
            error(f"The link tag '{link_match}' has has too many arguments.")
        if len(tokens) == 1:
            section = section.replace(link_match, make_link(tag_contents, tag_contents))
        else:
            text = tokens[0].strip()
            destination = tokens[1].strip()
            section = section.replace(link_match, make_link(text, destination))

    # +---------+
    # | Italics |
    # +---------+
    code_matches = re.findall(r'__.*?__', section, re.DOTALL)
    for code_match in code_matches:
        tag_contents = code_match[2:-2].strip()
        section = section.replace(code_match, f"<i>{tag_contents}</i>")

    # +-----------------------+
    # | Restore Code Sections |
    # +-----------------------+
    if SCSET.NO_RESTORE_CODE not in settings:
        for i in range(0, len(code_match_replacements)):
            section = section.replace(f"<CODE:{i}>", f"<code>{code_match_replacements[i]}</code>")

    if SCSET.NO_PARAGRAPH not in settings:
        section = f"<p>{section}</p>"

    return section


def turn_file_into_sections(file_contents: str) -> List[str]:
    sections = []
    # +--------------------------+
    # | Split file into sections |
    # +--------------------------+
    code_mode = False
    current_section = ""
    file_contents += "\n\n"
    lines = file_contents.split("\n")
    for line in lines:
        if not code_mode:
            if line.strip() == "":  # Empty Line
                if current_section:
                    sections.append(current_section)
                    current_section = ""
            elif line.strip() == "```":
                if current_section:
                    sections.append(current_section)
                current_section = "<pre>"
                code_mode = True
            else:
                current_section += line + "\n"
        else:
            if line.strip() == "```":
                if current_section:
                    current_section += "</pre>"
                    sections.append(current_section)
                current_section = ""
                code_mode = False
            else:
                if current_section:
                    current_section += "\n"
                current_section += line

    # +-------------------+
    # | Sanitize Sections |
    # +-------------------+
    for i in range(0, len(sections)):
        sections[i] = sections[i].strip()
    return sections


def save_page(filename_stem, title, page_html, previous_doc, next_doc, page_number="", link_home=False):
    now = datetime.now()
    compiled_date = now.strftime("%a %b %d %H:%M:%S %z %Y")
    home_link = ""
    if link_home:
        home_link = "<a href=\"index.html\">Home</a> |"
    page_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <style>
    {css}
    </style>
    <body>
        <div>
        <marquee>
        Welcome to the Lartunet: Lartu's corner of the internet!
        Visit the <a href="changelog.html">changelog</a> to see the latest updates to this website.
        Also try <a href="https://www.eterspire.com" target=_blank>Eterspire</a>, the greatest on-line adventure!
        If you want to make your own website like this one, check <a href="https://github.com/lartu/makompile" target=_blank>Makompile</a>.
        </marquee>
        </div>
    <hr>

    <div class="header-div">
        {home_link}
        <a href=sitemap.html>Contents</a> |
        <a href=changelog.html>Changes</a> |
        <a href="{previous_doc}">←</a> |
        <a href="{next_doc}">→</a> |
        <span id="page-number">{page_number}</span>
    </div>

    <hr>

    <!-- CONTENT -->
    {page_html}
    <!-- CONTENT END -->

    <hr>

    <div class="header-div">
        {home_link}
        <a href=sitemap.html>Contents</a> |
        <a href=changelog.html>Changes</a> |
        <a href="{previous_doc}">←</a> |
        <a href="{next_doc}">→</a> |
        <span id="page-number">{page_number}</span>
    </div>

    <hr>

    <div id="footer">
        <a href="https://github.com/lartu/makompile" target=_blank><img src="images/makompile_badge.png"></a>
        Page compiled using <a href="https://github.com/lartu/makompile" target=_blank>Makompile</a> on <i>{compiled_date}</i>.
    </div>
    </body>
    </html>
    """
    Path(RESULT_DIRECTORY).mkdir(parents=True, exist_ok=True)
    with open(Path(RESULT_DIRECTORY) / translate_page_name(Path(filename_stem)), "w") as f:
        f.write(page_html)


def sanitize_url_string(text):
    return re.sub(r'[^A-Za-z0-9\-._~]', '_', text)


def translate_page_name(filename):
    if str(filename) == "home":
        return "index.html"
    return sanitize_url_string(str(filename.with_suffix(".html")))


def copy_included():
    # Ensure RESULT_DIRECTORY exists
    if not os.path.exists(RESULT_DIRECTORY):
        os.makedirs(RESULT_DIRECTORY)
    else:
        # Delete all contents inside RESULT_DIRECTORY
        for item in os.listdir(RESULT_DIRECTORY):
            item_path = os.path.join(RESULT_DIRECTORY, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    # Ensure INCLUDED_FOLDER exists
    if os.path.exists(INCLUDED_FOLDER):
        # Copy contents from INCLUDED_FOLDER to RESULT_DIRECTORY
        for item in os.listdir(INCLUDED_FOLDER):
            src_path = os.path.join(INCLUDED_FOLDER, item)
            dest_path = os.path.join(RESULT_DIRECTORY, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)


def get_changed_files_in_git(commit_offset: int = 0) -> List[str]:
    """
    Returns a list of file paths in the SOURCE_DIRECTORY that have changed 
    according to Git.
    
    commit_offset:
        0  => changes in working directory vs HEAD (unstaged/staged changes)
       -1 => changes between HEAD and HEAD~1
       -2 => changes between HEAD~1 and HEAD~2, etc.
    """
    source_path = Path(SOURCE_DIRECTORY).resolve()

    if not source_path.is_dir():
        error(f"{SOURCE_DIRECTORY} is not a valid directory")

    try:
        changed_files = []

        if commit_offset == 0:
            # Use git status for working directory changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=source_path
            )
            if result.returncode != 0:
                error(f"Git error: {result.stderr.strip()}")
            
        elif commit_offset < 0:
            # Compare commit pairs: e.g. HEAD~1 vs HEAD, or HEAD~2 vs HEAD~1
            commit_offset -= 1
            newer_commit = f"HEAD~{-commit_offset - 1}" if commit_offset < -1 else "HEAD"
            older_commit = f"HEAD~{-commit_offset}"

            result = subprocess.run(
                ["git", "diff", "--name-only", older_commit, newer_commit],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=source_path
            )
            if result.returncode != 0:
                error(f"Git error: {result.stderr.strip()}")

        for line in result.stdout.strip().splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) < 2:
                raw_path = parts[0]
            else:
                raw_path = parts[1]
            if raw_path.startswith('"') and raw_path.endswith('"'):
                raw_path = raw_path[1:-1].replace('\\"', '"')
            full_path = Path(raw_path).resolve()
            if full_path.exists() and full_path.is_file() and str(full_path).startswith(str(source_path)):
                changed_files.append(str(full_path))

        return changed_files

    except Exception as e:
        return []


def get_commit_date(offset: int = 0, repo_path: str = ".") -> str:
    """
    Returns the date (YYYY-MM-DD) of the Git commit at the given offset.
    
    offset:
        0  => HEAD (current commit)
       -1 => HEAD~1 (previous commit)
       -2 => HEAD~2 (and so on)
    """
    try:
        commit_ref = "HEAD" if offset == 0 else f"HEAD~{-offset}"
        result = subprocess.run(
            ["git", "show", "-s", "--date=short", "--format=%cd", commit_ref],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""
    

def get_git_last_modified_dates(directory: str) -> List[Tuple[str, str]]:
    """
    Returns a list of (file_path, last_modified_date) tuples for all files in the directory,
    where last_modified_date is the most recent Git commit date in YYYY-MM-DD format.
    The list is sorted by date descending (newest first).
    """
    directory_path = Path(directory).resolve()

    if not directory_path.is_dir():
        raise ValueError(f"{directory} is not a valid directory")

    results = []

    for file_path in directory_path.rglob("*"):
        if not file_path.is_file():
            continue

        rel_path = file_path.relative_to(directory_path)
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cd", "--date=short", "--", str(rel_path)],
                cwd=directory_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            date = result.stdout.strip()
            if date:
                results.append((str(file_path), date))
        except subprocess.CalledProcessError:
            continue  # Skip files not tracked by Git

    # Sort descending by date
    results.sort(key=lambda x: x[1], reverse=True)
    return results


if __name__ == "__main__":
    try:
        with open('styles.css', 'r') as f:
            css = f.read()
    except FileNotFoundError:
        error("CSS file 'styles.css' not found.")

    docs_path = Path(SOURCE_DIRECTORY)
    if not docs_path.exists() or not docs_path.is_dir():
        error(f"Source directory at '{SOURCE_DIRECTORY}' not found.")

    files = docs_path.glob("*.txt")
    files = sorted(files)
    document_names = []
    for file in files:
        document_names.append(file.stem.lower())
    document_titles = {}

    if not files:
        error(f"Source directory at '{SOURCE_DIRECTORY}' doesn't contain any .txt files.")

    has_home = "home" in document_names

    if "index" in document_names:
        error(f"You cannot have a file called 'index.txt' in your '{SOURCE_DIRECTORY}' source directory.")

    copy_included()
    
    for i in range(0, len(files)):
        file = files[i]
        page_html = ""
        title = ""
        filename = Path(file)
        if str(filename) != str(filename).lower():
            error(f"The filename '{file}' is not in lowercase.")
        with open(filename) as f:
            sections = turn_file_into_sections(f.read())
            for section in sections:
                if section[0:5] == "<pre>":
                    section_html = section
                else:
                    section_html = compile_section(section)
                if section_html[0:4] == "<h1>" and not title:
                    title = section_html[4:-5]
                page_html += "\n" + section_html
        if not title:
            title = str(file.stem).title()
        document_titles[filename.name] = title
        previous_doc = "sitemap.html"
        if i > 0:
            previous_doc = translate_page_name(Path(files[i - 1].stem))
        next_doc = "sitemap.html"
        if i < len(files) - 1:
            next_doc = translate_page_name(Path(files[i + 1].stem))
        page_number = f"{i + 1} / {len(files)}"
        if file.stem != "home":
            page_number += f" – {title}"
        else:
            page_number += f" – Homepage"
        save_page(filename.stem, title, page_html, previous_doc, next_doc, page_number, has_home)

    # Create table of contents
    page_html = """
    <h1>Table of Contents</h1>
    <p>
        <img src="images/sail.png">
    </p>
    <ol id=\"table-of-contents\">
    """
    for file in files:
        page_path = translate_page_name(Path(file.stem))
        page_title = document_titles[file.name]
        if file.stem == "home":
            page_title += " <i><small>(Homepage)</small></i>"
        page_html += f"\n<li><a href=\"{page_path}\">{page_title}</a></li>"
    page_html += "\n</ol>"
    previous_doc = translate_page_name(Path(files[- 1].stem))
    # next_doc = translate_page_name(Path(files[0].stem))
    next_doc = "changelog.html"
    pager_text = "Table of Contents"
    if len(document_names) != 1:
        pager_text += f" ({len(document_names)} pages)"
    else:
        pager_text += f" ({len(document_names)} page)"
    save_page("sitemap", "Table of Contents", page_html, previous_doc, next_doc, pager_text, has_home)

    # Generate Changelog
    file_count = 15
    modified_files_and_dates = get_git_last_modified_dates(SOURCE_DIRECTORY)[0:file_count]
    page_html = f"""
    <h1>List of Changes</h1>
    <p>
        <img src="images/spaceship.png">
    </p>
    <p>
        This changelog is not a standard part of Makompile because it depends on my particular stack.
    </p>
    """
        
    last_date = ""

    links_added = 0
    for file_date in modified_files_and_dates:
        file, date = file_date
        filename = Path(file).name
        page_path = translate_page_name(Path(Path(file).stem))
        if filename in document_titles:
            if date != last_date:
                if last_date:
                    page_html += f"\n</ul>"
                last_date = date
                page_html += f"\n<p>Last updated on {date}</p><ul>"
            page_html += f"\n<li><a href=\"{page_path}\">{document_titles[filename]}</a></li>"
            links_added += 1
            if links_added >= file_count:
                break
    if last_date:
        page_html += f"\n</ul>"
    page_html += f"\n<p>Only the {links_added} most recently updated files are listed.</p>"
    previous_doc = "sitemap.html"
    next_doc = translate_page_name(Path(files[0].stem))
    save_page("changelog", "List of Changes", page_html, previous_doc, next_doc, "List of Changes", has_home)
# Coso - Lartu's Website Compiler
# 2021-05-02

# TODO:
# - Que se suba solo al servidor
# - Changelog automático

import os
import re
from datetime import date
import hashlib
from PIL import Image
import PIL
import glob
from math import ceil
import pickle
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCES_DIR = BASE_DIR + "/source"
DEST_DIR = BASE_DIR + "/docs"
IMAGES_DIR = BASE_DIR + "/images"
FILES_DIR = BASE_DIR + "/files"
STYLE_FILE = BASE_DIR + "/styles.css"
CNAME_FILE = BASE_DIR + "/CNAME"
MAIN_TITLE = "lartu.net"
FAVICON = "favicon.png"
DESCRIPTION = "Lartu's personal website, welcome to Lartu.net."
SITEMAP_FILENAME = "sitemap.coso"
CHANGELOG_FILENAME = "changelog.coso"
MAX_IMG_WIDTH = 800

sitemap = {}
linkedpages = {}

filesizes = {}
changelog = []
files = []
old_changelogs = []


def save_changelog():
    global filesizes, old_changelogs
    pickle.dump(filesizes, open(BASE_DIR + "/filesizes.p", "wb"))
    pickle.dump(old_changelogs, open(BASE_DIR + "/oldchangelogs.p", "wb"))


def load_changelog():
    global filesizes, old_changelogs
    try:
        filesizes = pickle.load(open(BASE_DIR + "/filesizes.p", "rb"))
        show("Loaded file sizes from previous version.")
    except:
        filesizes = {}
    try:
        old_changelogs = pickle.load(open(BASE_DIR + "/oldchangelogs.p", "rb"))
        show("Loaded old changelogs.")
    except:
        old_changelogs = []


def get_image_hash_name(original_name):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = str(int(hashlib.sha1(original_name.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
    while len(numbers) < 8:
        numbers += "0"
    final_name = letters[int(numbers[0:2]) % len(
        letters)] + numbers[2:4] + letters[int(numbers[4:6]) % len(letters)] + numbers[6:8]
    return final_name


def show(message):
    print("\033[93m->\033[0m", message)


def error(message):
    print("\033[91m->\033[0m", message)


def get_file_name(current_name):
    return current_name.replace(".coso", ".html")


def get_head(page_title=None, favicon=None, description=None):
    if page_title is None:
        page_title = MAIN_TITLE
    if favicon is None:
        favicon = FAVICON
    if description is None:
        description = DESCRIPTION
    head = "<head>"
    head += f'''\n<title>{page_title}</title>'''
    head += '''\n<link rel="stylesheet" href="styles.css">'''
    head += '''\n<meta charset="utf-8">'''
    head += '''\n<meta name="viewport" content="width=device-width, initial-scale=1">'''
    head += f'''\n<link rel="shortcut icon" type="image/png" href="images/{favicon}" />'''
    head += f'''\n<meta name="description" content="{description}">'''
    head += '''\n</head>'''
    head += '''<!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=UA-130871915-2"></script>
            <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'UA-130871915-2');
            </script>
            '''
    return head


def load_and_compile(filename, with_head=True):
    global changelog, filesizes, files
    show(f"Compiling {filename}")
    linkedpages[filename] = True
    source = ""
    with open(SOURCES_DIR + "/" + filename, "r") as f:
        source = f.read()
    if get_file_name(filename) not in files:
        files.append(get_file_name(filename))
    if get_file_name(filename) not in filesizes:
        filesizes[get_file_name(filename)] = len(source)
        changelog.append((get_file_name(filename), filesizes[get_file_name(filename)]))
    else:
        if filesizes[get_file_name(filename)] != len(source):
            changelog.append((get_file_name(filename), len(source) - filesizes[get_file_name(filename)]))
    compiled_source = compile(source, with_head, filename=filename)
    return compiled_source


def get_sitemap():
    global sitemap
    sitemap_source = "<ul>"
    for key in sitemap:
        sitemap_source += f'\n<li><a href="{key}">{sitemap[key]}</a></li>'
    sitemap_source += "\n</ul>"
    return sitemap_source


def get_changelog():
    global changelog, filesizes, files, sitemap, old_changelogs
    for key in list(filesizes):
        if key not in files:
            changelog.append((key, -filesizes[key]))
            del filesizes[key]
    changelog_source = ""
    chlogclass = '''class="bytesnochange"'''
    for changes in changelog:
        key = changes[0]
        if key not in sitemap:
            continue
        diff = changes[1]
        if diff > 0:
            diff = f"+{diff}"
            chlogclass = '''class="bytespositive"'''
        elif diff < 0:
            chlogclass = '''class="bytesnegative"'''
        changelog_source += f'\n<tr><td class="changelogtablefntd"><a href="{key}">{sitemap[key]}</a></td><td class="changelogtablesizetd"><span {chlogclass}>{diff}</span></td><td class="changelogtabletimetd">' + '{{date}} {{time}}</td></tr>'
    changelog_source = compile(changelog_source, False)
    old_changelogs.append(changelog_source)
    old_changelogs = old_changelogs[0:100]
    source = ""
    for chlog in old_changelogs:
        source = f"{chlog}\n{source}"
    return "<table class=\"changelogtable\">" + source + "\n</table>"


def compile(source, with_head=True, do_multiple_passes=True, filename=""):
    source = f"\n{source}\n"
    source = re.sub(r"(?<=\n)--(?: *?)(?=\n)", "<div class=\"split\"></div>", source)
    source = re.sub(r"(?<=\n)-(?: *?)(?=\n)", "<br>", source)
    source = re.sub(r"/\*(?:(?:.|\s|\r|\n)*?)\*/", "", source)
    tags = re.findall(r"{{[^{}]*?}}", source)
    page_title = MAIN_TITLE
    favicon = FAVICON
    description = DESCRIPTION
    include_count = 0
    includes = []
    footnotes = []
    for tag in tags:
        tag_content = tag.strip("{} \r\n\t")
        # Non command tags
        if "=>" in tag_content:
            tokens = tag_content.split("=>")
            message = tokens[0].strip()
            destination = tokens[1].strip()
            source = source.replace(tag, f'<a href="{destination}" class="external" target=_blank>{message}</a>')
        elif "->" in tag_content:
            tokens = tag_content.split("->")
            message = tokens[0].strip()
            realfilename = tokens[1].strip()
            anchor = ""
            if len(tokens) > 2:
                anchor = tokens[2].strip()
            if realfilename not in linkedpages:
                linkedpages[realfilename] = False
            destination = get_file_name(realfilename)
            if anchor:
                destination += "#" + anchor
            source = source.replace(tag, f'<a href="{destination}">{message}</a>')
        elif "~>" in tag_content:
            tokens = tag_content.split("~>")
            message = tokens[0].strip()
            realfilename = tokens[1].strip()
            anchor = ""
            if len(tokens) > 2:
                anchor = tokens[2].strip()
            if realfilename not in linkedpages:
                linkedpages[realfilename] = False
            destination = get_file_name(realfilename)
            if anchor:
                destination += "#" + anchor
            source = source.replace(tag, f'<a href="{destination}" target=_blank>{message}</a>')
        else:
            tag_content = re.sub(r"\s+", " ", tag_content)
            tokens = tag_content.split(" ", 1)
            if tokens[0] == "date":
                today = date.today()
                date_text = today.strftime("%B %d, %Y")
                source = source.replace(tag, date_text)
            if tokens[0] == "time":
                hour_text = time.strftime("%H:%M:%S")
                source = source.replace(tag, hour_text)
            if tokens[0] == "year":
                today = date.today()
                date_text = today.strftime("%Y")
                source = source.replace(tag, date_text)
            elif tokens[0] == "title":
                source = source.replace(tag, f"<h1>{tokens[1].strip()}</h1>")
            elif tokens[0] == "subtitle":
                source = source.replace(tag, f"<h2>{tokens[1].strip()}</h2>")
            elif tokens[0] == "pagetitle":
                page_title = tokens[1].strip()
                source = source.replace(tag, "")
            elif tokens[0] == "include":
                page_to_include = tokens[1].strip()
                source = source.replace(tag, f"<INCLUDE_{include_count}>")
                includes.append(page_to_include)
            elif tokens[0] == "favicon":
                favicon = tokens[1].strip()
                source = source.replace(tag, "")
            elif tokens[0] == "descr":
                description = tokens[1].strip()
                source = source.replace(tag, "")
            elif tokens[0] == "anchor":
                anchorname = tokens[1].strip()
                source = source.replace(tag, f"<div style='display: hidden' id='{anchorname}'></div>")
            elif tokens[0] in ["bigimg", "img", "midimg"]:
                # Bigimg es imagen comprimida ancho 100% con epígrafe
                # Midimg es imagen comprimida ancho 50% con epígrafe
                # img es imagen comprimida max ancho 100% sin epígrafe.
                # Img no da opción de view original.
                image_filename = tokens[1].strip()
                img_file = IMAGES_DIR + "/" + image_filename
                picture = Image.open(img_file)
                width = picture.size[0]
                height = picture.size[1]
                imgname = get_image_hash_name(tokens[1].strip())
                os.system(f'''cp "{img_file}" "{DEST_DIR}/images/{imgname}.png"''')  # Save original image
                show(f"Copied {image_filename} to the images directory as {imgname}.png.")
                image_filename = f"{imgname}.png"
                max_width = MAX_IMG_WIDTH
                if tokens[0] == "midimg":
                    max_width = int(max_width / 2)
                if width > max_width:
                    show(f"Optimizing {image_filename}.")
                    picture = picture.resize((max_width, int(height*max_width/width)))
                    compressed_filename = DEST_DIR + "/images/c_" + imgname + ".png"
                    picture.save(compressed_filename, optimize=True, quality=75)
                    show(f"Saved {compressed_filename}.")
                    filesize = os.path.getsize(img_file)
                    vieworiginal = "{{ view original ~> images/" + image_filename + " }} " + \
                        f"({ceil(filesize / 1024)} KiB)"
                    if tokens[0] == "img":
                        source = source.replace(
                            tag,
                            f"<img src =\"images/c_{image_filename}\" title=\"{imgname}\" alt=\"Image: {imgname}\">")
                    else:
                        source = source.replace(
                            tag,
                            f"<div class=\"{tokens[0]}\"><img src =\"images/c_{image_filename}\" title=\"{imgname}\" alt=\"Image: {imgname}\">"
                            + f"— {imgname} - {vieworiginal}</div>")
                else:
                    source=source.replace(
                        tag,
                        f"<div class=\"{tokens[0]}\"><img src =\"images/{image_filename}\" title=\"{imgname}\" alt=\"Image: {imgname}\"></div>")
            elif tokens[0] == "sitemap":
                # Add to sitemap
                if with_head:
                    sitemap[get_file_name(filename)]=page_title
                source=source.replace(tag, get_sitemap())
            elif tokens[0] == "changelog":
                # Add to changelog
                if with_head:
                    sitemap[get_file_name(filename)]=page_title
                source=source.replace(tag, get_changelog())
            elif tokens[0] == "footnote":
                footnotes.append(tokens[1].strip())
                source=source.replace(tag, f"<sup>{len(footnotes)}</sup>")
    # Add footnotes
    if len(footnotes) > 0:
        source=source + "{{subtitle footnotes}}"
        fnindex=0
        for footnote in footnotes:
            fnindex += 1
            source=source + f"<small>({fnindex}) {footnote}</small>"
            if fnindex < len(footnotes):
                source=source + "\n--\n"
    # Formatted text
    bolds=re.findall(r"\*\*(?:.|\n)*?\*\*", source)
    for text in bolds:
        source=source.replace(text, "<b>" + text.strip("* ") + "</b>")
    italics=re.findall(r"__(?:.|\n)*?__", source)
    for text in italics:
        source=source.replace(text, "<i>" + text.strip("_ ") + "</i>")
    code=re.findall(r"(```(?:.|\n)*?```)", source)
    for text in code:
        source=source.replace(text, "<pre>" + text[3:-3].strip() + "</pre>")
    code=re.findall(r"``(?:.|\n)*?``", source)
    for text in code:
        source=source.replace(text, "<code>" + text.strip("` ") + "</code>")
    listitems=re.findall(r"(?<=\n)::::.+?[\r\n]", source)
    for text in listitems:
        source=source.replace(
            text, "<div class='listitem2'><span class='listmark'>※</span> " + text[4:].strip() + "</div>\n")
    listitems=re.findall(r"(?<=\n)::.+?[\r\n]", source)
    for text in listitems:
        source=source.replace(
            text, "<div class='listitem'><span class='listmark'>※</span> " + text[2:].strip() + "</div>\n")
    # Include includes
    index=0
    for include in includes:
        source=source.replace(f"<INCLUDE_{index}>", load_and_compile(include, False))
        index += 1
    # Parse a few more times for nested things
    while True and do_multiple_passes:
        new_source=compile(source, False, False)
        if new_source != source:
            source=new_source
        else:
            break
    # Add boilerplate
    if with_head:
        head=get_head(page_title, favicon, description)
        source=f"<!DOCTYPE html>\n<html>\n{head}\n<body>\n{source}\n</body>\n</html>"
    # Add to sitemap
    if with_head:
        sitemap[get_file_name(filename)]=page_title
    return source.strip()


show("Compilation started.")
load_changelog()

# Clear build directory
show(f"Cleaning build directory ({DEST_DIR})")
os.system(f"rm -rf \"{DEST_DIR}\" && mkdir \"{DEST_DIR}\"")

# Copy styles file
os.system(f"cp \"{STYLE_FILE}\" \"{DEST_DIR}/styles.css\"")

# Copy CNAME
os.system(f"cp \"{CNAME_FILE}\" \"{DEST_DIR}/CNAME\"")

# Create images directory
os.system(f"mkdir \"{DEST_DIR}/images\"")
os.system(f'''cp "{IMAGES_DIR}/{FAVICON}" "{DEST_DIR}/images/{FAVICON}"''')
os.system(f'''cp -R "{IMAGES_DIR}/analisis" "{DEST_DIR}/images/analisis"''')  # Imagenes de analisis
os.system(f'''echo "forbidden" > "{DEST_DIR}/images/index.html"''')
os.system(f'''echo "forbidden" > "{DEST_DIR}/images/analisis/index.html"''')

# Create files directory
os.system(f'''cp -R "{FILES_DIR}" "{DEST_DIR}/files"''')
os.system(f'''echo "forbidden" > "{DEST_DIR}/files/index.html"''')

# Get source files
directory=os.fsencode(SOURCES_DIR)

want_sitemap=False
want_changelog=False

for file in os.listdir(directory):
    filename=os.fsdecode(file)
    if filename.endswith(".coso") and filename[0] != "_":
        if filename == SITEMAP_FILENAME:
            want_sitemap=True
            continue
        if filename == CHANGELOG_FILENAME:
            want_changelog=True
            continue
        compiled_source=load_and_compile(filename)
        with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
            f.write(compiled_source)

if want_changelog:
    filename=CHANGELOG_FILENAME
    compiled_source=load_and_compile(filename)
    with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
        f.write(compiled_source)

if want_sitemap:
    filename=SITEMAP_FILENAME
    compiled_source=load_and_compile(filename)
    with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
        f.write(compiled_source)

# List linked but not found files
show("All files have been compiled.")

errors=0
for key in linkedpages:
    if not linkedpages[key] and ".coso" in key:
        error(f"The file {key} is linked but not found.")
        errors += 1

error(f"{errors} error(s) found.")

print("Total site size:")
os.system(f"du -sh \"{DEST_DIR}\"")

save_changelog()

# List linked but not found files
show("Compilation complete.")

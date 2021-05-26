# Coso - Lartu's Website Compiler
# 2021-05-02

import os
import re
from datetime import date, datetime
import hashlib
from PIL import Image, ImageOps
import PIL
import glob
from math import ceil
import pickle
import time
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCES_DIR = BASE_DIR + "/source"
DEST_DIR = BASE_DIR + "/docs"
IMAGES_DIR = BASE_DIR + "/images"
FILES_DIR = BASE_DIR + "/files"
STYLE_FILE = BASE_DIR + "/styles.css"
CNAME_FILE = BASE_DIR + "/CNAME"
MAIN_TITLE = "lartu.net"
FAVICON = "fuyukogif2.png"
DESCRIPTION = "Lartu's personal website, welcome to Lartu.net."
SITEMAP_FILENAME = "sitemap.coso"
CHANGELOG_FILENAME = "changelog.coso"
MAX_IMG_WIDTH = 800

RSS_HEADER = '''
<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0' xmlns:dc='http://purl.org/dc/elements/1.1/'>
    <channel>

        <title>Lartunet</title>
        <link>https://lartu.net</link>
        <description>Lartu's Log of Interesting Things</description>
        <image>
            <url>https://lartu.net/files/rss.jpg</url>
            <title>Lartunet</title>
            <link>https://lartu.net</link>
        </image>
'''

RSS_FOOTER = '''
    </channel>
</rss>
'''

RSS_START_TOKEN = "<!--RSS-START-->"
RSS_END_TOKEN = "<!--RSS-END-->"

rss_items = []

sitemap = {}
linkedpages = {}

old_changelogs = []


def generar_rss():
    global rss_items
    validitems = []
    for item in rss_items:
        if item[2] is None:
            error(f"The RSS entry for {item[1]} has no date.")
            continue
        validitems.append(item)
    validitems.sort(key=lambda x: x[2], reverse=True)
    rss_contents = RSS_HEADER
    for item in validitems:
        d = item[2]
        rss_date = d.strftime('%a, %d %b %Y %H:%M:%S -0300')
        item_content = "\t\t<item>\n"
        item_content += f"\t\t\t<title>{item[0]}</title>\n"
        item_content += f"\t\t\t<link>https://lartu.net/{item[1]}</link>\n"
        item_content += f"\t\t\t<guid isPermaLink='false'>{item[1]}</guid>\n"
        item_content += f"\t\t\t<pubDate>{rss_date}</pubDate>\n"
        item_content += "\t\t\t<dc:creator><![CDATA[Lartu]]></dc:creator>\n"
        item_content += f"\t\t\t<description><![CDATA[{item[3]}]]></description>\n"
        item_content += "\t\t</item>\n"
        rss_contents += item_content
    rss_contents += RSS_FOOTER
    with open(f"{DEST_DIR}/files/rss.xml.rss", "w+") as f:
        f.write(rss_contents)


def save_changelog():
    global old_changelogs
    pickle.dump(old_changelogs, open(BASE_DIR + "/oldchangelogs.p", "wb"))


def load_changelog():
    global old_changelogs
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


def load_and_compile(filename, with_head=True, for_rss = False):
    global changelog, filesizes, files
    show(f"Compiling {filename}" + (" for RSS" if for_rss else ""))
    linkedpages[filename] = True
    source = ""
    with open(SOURCES_DIR + "/" + filename, "r") as f:
        source = f.read()
    compiled_source = compile(source, with_head, filename=filename, for_rss=for_rss)
    return compiled_source


def get_sitemap():
    global sitemap
    sitemap_source = "<ul>"
    for key in sitemap:
        sitemap_source += f'\n<li><a href="{key}">{sitemap[key]}</a></li>'
    sitemap_source += "\n</ul>"
    return sitemap_source


def get_changelog():
    global sitemap, old_changelogs

    chlogclass = '''class="bytesnochange"'''
    git_changelog = os.popen('git diff --stat --relative source | grep -E ".*\.coso.*"').read()
    lines = git_changelog.split("\n")
    changelog_lines = []
    for line in lines:
        if "|" not in line:
            continue
        tokens = line.split("|")
        key = get_file_name(tokens[0].strip().split("/")[-1].strip())
        if key[0] == "_":
            continue
        change_count = int(tokens[1].strip().split()[0])
        pos_changes = tokens[1].count('+')
        neg_changes = tokens[1].count('-')
        total_change_signs = pos_changes + neg_changes
        pos_changes = ceil(pos_changes * change_count / total_change_signs)
        neg_changes = ceil(neg_changes * change_count / total_change_signs)
        diftext = ""
        if pos_changes > 0:
            chlogclass = '''class="bytespositive"'''
            diftext += f"<span {chlogclass}>+{pos_changes}</span>"
        if neg_changes > 0:
            chlogclass = '''class="bytespositive"'''
            diftext += f"<span {chlogclass}>-{neg_changes}</span>"
        changelog_lines.append(
            compile(
                f'<tr><td class="changelogtablefntd"><a href="{key}">{sitemap[key]}</a></td><td class="changelogtablesizetd">{diftext}</td><td class="changelogtabletimetd">'
                + '{{date}} {{time}}</td></tr>', False))

    source = ""
    old_changelogs = changelog_lines + old_changelogs
    for line in old_changelogs[0:100]:
        source += f"\n{line}"

    return "<table class=\"changelogtable\">" + source + "\n</table>"


def compile(source, with_head=True, do_multiple_passes=True, filename="", for_rss=False):
    source = f"\n{source}\n"
    if not for_rss:
        source = re.sub(r"(?<=\n)--(?: *?)(?=\n)", "<div class=\"split\"></div>", source)
    else:
        source = re.sub(r"(?<=\n)--(?: *?)(?=\n)", "<br><br>", source)
    source = re.sub(r"(?<=\n)-(?: *?)(?=\n)", "<br>", source)
    source = re.sub(r"/\*(?:(?:.|\s|\r|\n)*?)\*/", "", source)
    tags = re.findall(r"{{[^{}]*?}}", source)
    page_title = MAIN_TITLE
    favicon = FAVICON
    description = DESCRIPTION
    includes = []
    footnotes = []
    requires_rss = False
    rss_date = None
    for tag in tags:
        tag_content = tag.strip("{} \r\n\t")
        # Non command tags
        if "=>" in tag_content:
            tokens = tag_content.split("=>")
            message = tokens[0].strip()
            destination = tokens[1].strip()
            if not for_rss:
                source = source.replace(
                    tag, f'<a href="{destination}" class="external" target=_blank>{message}</a>'.replace("\\}", "}"))
            else:
                source = source.replace(
                    tag, f'<a href="{destination}"" target=_blank>{message}</a>'.replace("\\}", "}"))
        elif "->" in tag_content:
            tokens = tag_content.split("->")
            message = tokens[0].strip()
            realfilename = tokens[1].strip()
            anchor = ""
            if len(tokens) >= 3:
                anchor = tokens[2].strip()
            if realfilename not in linkedpages:
                linkedpages[realfilename] = False
            destination = get_file_name(realfilename)
            if anchor:
                destination += "#" + anchor
            if not for_rss:
                source = source.replace(tag, f'<a href="{destination}">{message}</a>'.replace("\\}", "}"))
            else:
                source = source.replace(
                    tag, f'<a href="https://lartu.net/{destination}">{message}</a>'.replace("\\}", "}"))
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
            if not for_rss:
                source = source.replace(tag, f'<a href="{destination}" target=_blank>{message}</a>'.replace("\\}", "}"))
            else:
                source = source.replace(
                    tag, f'<a href="https://lartu.net/{destination}" target=_blank>{message}</a>'.replace("\\}", "}"))
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
                source = source.replace(tag, f"<INCLUDE_{len(includes)}>")
                includes.append(page_to_include)
            elif tokens[0] == "favicon":
                # DEPRECATED TAG
                # favicon = tokens[1].strip()
                source = source.replace(tag, "")
            elif tokens[0] == "descr":
                description = tokens[1].strip()
                source = source.replace(tag, "")
            elif tokens[0] == "anchor":
                anchorname = tokens[1].strip()
                if not for_rss:
                    source = source.replace(tag, f"<div style='display: hidden' id='{anchorname}'></div>")
                else:
                    source = source.replace(tag, "")
            elif tokens[0] in ["bigimg", "img", "midimg", "mediabutton"]:
                # Bigimg es imagen comprimida ancho 100% con epígrafe
                # Midimg es imagen comprimida ancho 50% con epígrafe
                # img es imagen comprimida max ancho 100% sin epígrafe.
                # Img no da opción de view original.
                if " " in tokens[1]:
                    other_tokens = tokens[1].split()
                    tokens.pop()
                    tokens += other_tokens
                image_filename = tokens[1].strip()
                black_and_white = False
                if len(tokens) >= 3 and tokens[2] == "bw":
                    black_and_white = True
                image_title, file_ext = os.path.splitext(image_filename)
                file_ext = file_ext.strip(".")
                img_file = IMAGES_DIR + "/" + image_filename
                picture = Image.open(img_file)
                picture = ImageOps.exif_transpose(picture)
                width = picture.size[0]
                height = picture.size[1]
                imghash = get_image_hash_name(image_title)
                image_filename = f"{imghash}.{file_ext}"
                os.system(f'''cp "{img_file}" "{DEST_DIR}/images/{image_filename}"''')  # Save original image
                show(f"Copied {image_filename} to the images directory as {image_filename}.")
                compression_format = "JPEG"
                compresed_image_file = imghash + "." + compression_format  # Was gif
                jpeg_note = f" ({compression_format}) "
                max_width = MAX_IMG_WIDTH
                if tokens[0] == "midimg":
                    max_width = int(max_width / 2)
                    compresed_image_file = imghash + ".png"
                    compression_format = "PNG"
                    jpeg_note = ""
                if width > max_width:
                    compressed_filename = DEST_DIR + "/images/c_" + compresed_image_file
                    if not for_rss:
                        show(f"Optimizing {image_filename}.")
                        picture = picture.resize((max_width, int(height*max_width/width)))
                        picture = picture.convert("RGBA")
                        new_image = Image.new("RGBA", picture.size, "WHITE")
                        new_image.paste(picture, (0, 0), picture)
                        if black_and_white:
                            picture = ImageOps.grayscale(new_image)
                        if picture.mode == "P" and compression_format != "GIF":
                            picture = picture.convert("RGB")
                        if compression_format == "JPEG":
                            picture = picture.convert("RGB")
                        picture.save(compressed_filename, optimize=True, quality=90, format=compression_format)
                        show(f"Saved {compressed_filename}.")
                        filesize = os.path.getsize(img_file)
                        vieworiginal = "{{ view original ~> images/" + image_filename + " }} " + \
                            f"({ceil(filesize / 1024)} KiB, {file_ext.upper()})"
                        bwnote = ""
                        if black_and_white:
                            bwnote = "(b&w version) "
                    if tokens[0] == "img":
                        if not for_rss:
                            source = source.replace(
                                tag,
                                f"<img  class=\"{tokens[0]}\" src =\"images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\">")
                        else:
                            source = source.replace(
                                tag,
                                f"<img src =\"https://lartu.net/images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\">")
                    else:
                        if not for_rss:
                            source = source.replace(
                                tag,
                                f"<div class=\"{tokens[0]}\"><img src =\"images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\">"
                                + f"<small>— {imghash} {bwnote}{jpeg_note}- {vieworiginal}</small></div>")
                        else:
                            source = source.replace(
                                tag,
                                f"<a href=\"https://lartu.net/images/{image_filename}\"><img src =\"https://lartu.net/images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\"></a>")
                elif tokens[0] == "mediabutton":
                    # NOTA: Los mediabutton tienen que ser chiquitos, en general 20x20
                    source = source.replace(
                        tag,
                        f"<img src =\"images/{image_filename}\" class=\"{tokens[0]}\" title=\"{imghash}\" alt=\"Image: {imghash}\">")
                else:
                    if not for_rss:
                        source = source.replace(
                            tag,
                            f"<div class=\"{tokens[0]}\"><img src =\"images/{image_filename}\" title=\"{imghash}\" alt=\"Image: {imghash}\"></div>")
                    else:
                        source = source.replace(
                            tag,
                            f"<img src =\"https://lartu.net/images/{image_filename}\" title=\"{imghash}\" alt=\"Image: {imghash}\">")
            elif tokens[0] == "sitemap":
                # Add to sitemap
                if with_head:
                    sitemap[get_file_name(filename)] = page_title
                source = source.replace(tag, get_sitemap())
            elif tokens[0] == "changelog":
                # Add to changelog
                if with_head:
                    sitemap[get_file_name(filename)] = page_title
                source = source.replace(tag, get_changelog())
            elif tokens[0] == "footnote":
                footnotes.append(tokens[1].strip())
                source = source.replace(tag, f"<sup>{len(footnotes)}</sup>")
            elif tokens[0] == "rss_start":
                if for_rss:
                    source = source.replace(tag, RSS_START_TOKEN)
                else:
                    requires_rss = True
                    source = source.replace(tag, "")
            elif tokens[0] == "rss_end":
                if for_rss:
                    source = source.replace(tag, RSS_END_TOKEN)
                else:
                    source = source.replace(tag, "")
            elif tokens[0] == "rss_date":
                if not for_rss:
                    rss_date = datetime.strptime(tokens[1].strip(), "%Y-%m-%d %H:%M")
                source = source.replace(tag, "")
    # Add footnotes
    if len(footnotes) > 0:
        source = source + "{{subtitle footnotes}}"
        fnindex = 0
        for footnote in footnotes:
            fnindex += 1
            source = source + f"<small>({fnindex}) {footnote}</small>"
            if fnindex < len(footnotes):
                source = source + "\n--\n"
    # Formatted text
    bolds = re.findall(r"\*\*(?:.|\n)*?\*\*", source)
    for text in bolds:
        source = source.replace(text, "<b>" + text.strip("* ") + "</b>")
    italics = re.findall(r"__(?:.|\n)*?__", source)
    for text in italics:
        source = source.replace(text, "<i>" + text.strip("_ ") + "</i>")
    code = re.findall(r"(```(?:.|\n)*?```)", source)
    for text in code:
        source = source.replace(text, "<pre>" + text[3:-3].strip() + "</pre>")
    code = re.findall(r"``(?:.|\n)*?``", source)
    for text in code:
        source = source.replace(text, "<code>" + text.strip("` ") + "</code>")
    listitems = re.findall(r"(?<=\n)::::.+?[\r\n]", source)
    for text in listitems:
        if not for_rss:
            source = source.replace(
                text, "<div class='listitem2'><span class='listmark'>&gt;</span> " + text[4:].strip() + "</div>\n")
        else:
            source = source.replace(
                text, "<br>&gt;&gt; " + text[4:].strip() + "<br>\n")
    listitems = re.findall(r"(?<=\n)::.+?[\r\n]", source)
    for text in listitems:
        if not for_rss:
            source = source.replace(
                text, "<div class='listitem'><span class='listmark'>&gt;</span> " + text[2:].strip() + "</div>\n")
        else:
            source = source.replace(
                text, "<br>&gt;&gt;&gt;&gt; " + text[2:].strip() + "<br>\n")
    # Replace double <br> in case there are multiple <br>s
    source = re.sub(r"<br>\s*<br>\s*<br>", "<br><br>", source)
    # Include includes
    index = 0
    for include in includes:
        source = source.replace(f"<INCLUDE_{index}>", load_and_compile(include, False))
        index += 1
    # Add footer
    if with_head:
        source = f"{source}\n\n" + "{{ include _footer.coso }}"
    # Parse a few more times for nested things
    while True and do_multiple_passes:
        new_source = compile(source, False, False)
        if new_source != source:
            source = new_source
        else:
            break
    # Add boilerplate
    if with_head:
        # Si tiene <head>
        head = get_head(page_title, favicon, description)
        source = f"<!DOCTYPE html>\n<html>\n{head}\n<body>\n{source}\n</body>\n</html>"
    # Add to sitemap
    if with_head:
        sitemap[get_file_name(filename)] = page_title
    # Add page to RSS if requested (request from main HTML compilation)
    if requires_rss and with_head:
        rss_source = load_and_compile(filename, False, True)
        rss_start_token_position = rss_source.find(RSS_START_TOKEN)
        rss_end_token_position = rss_source.find(RSS_END_TOKEN)
        rss_description = rss_source[rss_start_token_position:rss_end_token_position].replace(
            RSS_START_TOKEN, "").replace(RSS_END_TOKEN, "").strip()
        rss_title = page_title
        if "Lartunet — " in page_title:
            rss_title = page_title.replace("Lartunet — ", "")
        rss_items.append((rss_title, get_file_name(filename), rss_date, rss_description))
    source = source.strip()
    return source


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
directory = os.fsencode(SOURCES_DIR)

want_sitemap = False
want_changelog = False

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".coso") and filename[0] != "_":
        if filename == SITEMAP_FILENAME:
            want_sitemap = True
            continue
        if filename == CHANGELOG_FILENAME:
            want_changelog = True
            continue
        compiled_source = load_and_compile(filename)
        with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
            f.write(compiled_source)

if want_changelog:
    filename = CHANGELOG_FILENAME
    compiled_source = load_and_compile(filename)
    with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
        f.write(compiled_source)

if want_sitemap:
    filename = SITEMAP_FILENAME
    compiled_source = load_and_compile(filename)
    with open(DEST_DIR + "/" + get_file_name(filename), "w+") as f:
        f.write(compiled_source)

# List linked but not found files
show("All files have been compiled.")

# Generar RSS
generar_rss()

errors = 0
for key in linkedpages:
    if not linkedpages[key] and ".coso" in key:
        error(f"The file {key} is linked but not found.")
        errors += 1

error(f"{errors} error(s) found.")

print("Total site size:")
os.system(f"du -sh \"{DEST_DIR}\"")

if len(sys.argv) > 1 and sys.argv[1] == "--save-changelog":
    show("Saving changelog!")
    save_changelog()

# List linked but not found files
show("Compilation complete.")

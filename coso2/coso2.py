# Coso 2.0 - Lartu's Website Compiler
# v2 2021-05-26

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

SITEMAP_FILENAME = "sitemap.coso"
CHANGELOG_FILENAME = "changelog.coso"
MAX_IMG_WIDTH = 800

RSS_HEADER = 

RSS_FOOTER = '''
    </channel>
</rss>
'''

RSS_START_TOKEN = "<!--RSS-START-->"
RSS_END_TOKEN = "<!--RSS-END-->"

sitemap = {}
linkedpages = {}


def save_changelog():
    global old_changelogs
    pickle.dump(old_changelogs, open(BASE_DIR + "/oldchangelogs.p", "wb"))


def get_image_hash_name(original_name):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = str(int(hashlib.sha1(original_name.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
    while len(numbers) < 8:
        numbers += "0"
    final_name = letters[int(numbers[0:2]) % len(
        letters)] + numbers[2:4] + letters[int(numbers[4:6]) % len(letters)] + numbers[6:8]
    return final_name


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
    source = re.sub(r"/\*(?:(?:.|\s|\r|\n)*?)\*/", "", source) # Remove comments /* ... */
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
                                f"<br><br><img src =\"https://lartu.net/images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\"><br><br>")
                    else:
                        if not for_rss:
                            source = source.replace(
                                tag,
                                f"<div class=\"{tokens[0]}\"><img src =\"images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\">"
                                + f"<small>— {imghash} {bwnote}{jpeg_note}- {vieworiginal}</small></div>")
                        else:
                            source = source.replace(
                                tag,
                                f"<br><br><a href=\"https://lartu.net/images/{image_filename}\"><img src =\"https://lartu.net/images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\"></a><br><br>")
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
                            f"<br><br><img src =\"https://lartu.net/images/{image_filename}\" title=\"{imghash}\" alt=\"Image: {imghash}\"><br><br>")
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
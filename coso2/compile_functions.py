import re
import time
from datetime import date, datetime
import os
from PIL import Image, ImageOps
from math import ceil
import hashlib

from config import *
from message_functions import *
from directory_functions import *

RSS_TAG = "<!-- RSS ARTICLE STARTS HERE -->"

rss_items = []
document_title = None
document_favicon = None
document_descr = None
rss_date = None
document_footnotes = None
sitemap = {}


def generate_rss_file():
    '''This function generates the RSS file.
    '''
    global rss_items
    rss_items.sort(key=lambda x: x[2], reverse=True)
    rss_contents = get_rss_header()
    for item in rss_items:
        d = item[1]
        rss_date_str = d.strftime('%a, %d %b %Y %H:%M:%S -0300')
        item_content = "\t\t<item>\n"
        item_content += f"\t\t\t<title>{document_title}</title>\n"
        item_content += f"\t\t\t<link>https://lartu.net/{item[0]}</link>\n"
        item_content += f"\t\t\t<guid isPermaLink='false'>{item[0]}</guid>\n"
        item_content += f"\t\t\t<pubDate>{rss_date_str}</pubDate>\n"
        item_content += "\t\t\t<dc:creator><![CDATA[Lartu]]></dc:creator>\n"
        item_content += f"\t\t\t<description><![CDATA[{item[2]}]]></description>\n"
        item_content += "\t\t</item>\n"
        rss_contents += item_content
    rss_contents += get_rss_footer()
    with open(f"{get_docs_dir()}/files/rss.xml.rss", "w+") as f:
        f.write(rss_contents.strip())


def reset_global_document_flags():
    '''Resets global variables used for compilation of the full document,
    such as the document title.
    '''
    global document_title, document_favicon, document_descr, rss_date
    document_title = get_default_page_title()
    document_favicon = f"images/{get_favicon_name()}"
    document_descr = get_default_page_description()
    rss_date = None


def reset_global_body_flags():
    '''Resets global variables used for compilation of the document body,
    such as footnotes.
    '''
    global document_footnotes
    document_footnotes = []


def set_global_page_title(title):
    '''Sets the global variable for the document title.
    '''
    global document_title
    document_title = title


def set_global_page_favicon(favicon_filename):
    '''Sets the global variable for the document favicon.
    '''
    global document_favicon
    document_favicon = favicon_filename


def set_global_page_description(descr):
    '''Sets the global variable for the document description.
    '''
    global document_descr
    document_descr = descr


def add_footnote(note):
    '''Adds a footnote to the page and returns a number for that footnote.
    '''
    global document_footnotes
    document_footnotes.append(note.strip())
    return len(document_footnotes)


def compile_source_and_rss(source_code, filename):
    '''Compiles coso source code into and HTML page. If the coso source code
    included an rss tag, it also generates the RSS rendering and adds it
    to the RSS items list.
    '''
    global sitemap
    html_source = compile_source(source_code)
    if rss_date is not None:
        rss_body = compile_source_body(source_code, for_rss=True)
        rss_items.append((
            get_compiled_filename(filename),
            rss_date,
            rss_body,
        ))
    # Add page to sitemap
    sitemap[get_compiled_filename(filename)] = document_title
    return html_source


def compile_source(source_code):
    '''Takes coso source code and turns it into a full HTML page, with
    headers.
    '''
    # Reset compilation flags for page
    reset_global_document_flags()
    page_head = get_document_head(document_title, document_favicon, document_descr)
    page_body = compile_source_body(source_code)
    page_footer = compile_source_body("{{include _footer.coso}}")
    return f"{page_head}\n{page_body}\n{page_footer}"


def compile_source_body(source_code, for_rss=False):
    '''Takes coso source code and turns it into HTML (without headers).
    By default the source is compiled as a full HTML page. It may be
    compiled without css classes for RSS.
    '''
    # Reset compilation flags for body
    reset_global_body_flags()

    # Remove source code comments /* ... */
    result = re.sub(r"/\*(?:(?:.|\s|\r|\n)*?)\*/", "", source_code)

    # Compile the source until there are no more tags left.
    while True:
        # Get coso source tags {{ ... }}
        tags = re.findall(r"{{[^{}]*?}}", result)
        if len(tags) == 0:
            break

        # Compile every tag we've found so far.
        for tag in tags:
            # Compile and replace tag. This should be referentially transparent
            # as far as results go. If two tags are the same, they should be
            # compiled the same.
            result = result.replace(tag, compile_tag(tag, use_custom_classes=not for_rss))

    # Add footnotes
    if len(document_footnotes) > 0:
        footnotes_part = "{{subtitle footnotes}}"
        fnindex = 0
        for footnote in document_footnotes:
            fnindex += 1
            footnotes_part += f"<p><small>({fnindex}) {footnote}</small></p>\n"
        result += f"\n{compile_source_body(footnotes_part, for_rss)}"

    # Replace bold text
    bolds = re.findall(r"\*\*(?:.|\n)*?\*\*", result)
    for text in bolds:
        result = result.replace(text, "<b>" + text.strip("* ") + "</b>")

    # Replace italic text
    italics = re.findall(r"__(?:.|\n)*?__", result)
    for text in italics:
        result = result.replace(text, "<i>" + text.strip("_ ") + "</i>")

    # Replace multine (<pre>) code areas (```)
    code = re.findall(r"(```(?:.|\n)*?```)", result)
    for text in code:
        result = result.replace(text, "<pre>" + text[3:-3].strip() + "</pre>")

    # Replace inline (<code>) code areas (``)
    code = re.findall(r"``(?:.|\n)*?``", result)
    for text in code:
        result = result.replace(text, "<code>" + text.strip("` ") + "</code>")

    # If the compilation was requested for RSS, remove everything before the RSS tag
    if for_rss:
        result = result[result.find(RSS_TAG):]

    # Remove empty lines that may result from tag deletion (such as {{title}})
    result = re.sub(r"(\n( *)\n( *)\n)+", "\n\n", result).strip()

    return result


def compile_tag(tag, use_custom_classes=True):
    '''Compiles a tag into HTML code. Takes must be passed with {{ }}.
    By default it's prepared to use custom css classes. This might be
    deactivated for RSS if desired.
    '''
    # Remove external braces
    tag = tag[2:-2].strip()

    # Replace escaped braces
    tag = tag.replace("\\}", "}")

    # Remove multiple spaces in tag
    tag = re.sub(r"\s+", " ", tag)

    # Check if it's a link tag
    link_types = [
        ("=>", "target=_blank", "class=external", False),
        ("->", "", "", True),
        ("~>", "target=_blank", "", True),
    ]
    for link_type in link_types:
        arrow = link_type[0]
        target_type = link_type[1]
        css_class = link_type[2] if use_custom_classes else ""
        is_local = link_type[3]
        if arrow in tag:
            tokens = tag.split(arrow, 1)
            message = tokens[0].strip()
            destination_tokens = tokens[1].split("->")
            destination = destination_tokens[0].strip()
            if is_local and ".coso" in destination:
                destination = get_compiled_filename(destination)
            if len(destination_tokens) > 1:
                destination_anchor = destination_tokens[1].strip()
                destination = f"{destination}#{destination_anchor}"
            return f'<a href="{destination}" {css_class} {target_type}>{message}</a>'

    # Otherwise, it has to have a command. Get the command and parse the tag.
    tokens = tag.split(" ", 1)
    command = tokens[0]
    body = ""
    if len(tokens) > 1:
        body = tokens[1].strip()

    if command == "date":
        today = date.today()
        return today.strftime("%B %d, %Y")

    elif command == "time":
        return time.strftime("%H:%M:%S")

    elif command == "year":
        today = date.today()
        return today.strftime("%Y")

    elif command == "title":
        return f"<h1>{body}</h1>"

    elif command == "subtitle":
        return f"<h2>{body}</h2>"

    elif command == "pagetitle":
        set_global_page_title(body)
        return ""

    elif command == "include":
        return load_file_contents(body)

    elif command == "favicon":
        set_global_page_favicon(body)
        return ""

    elif command == "descr":
        set_global_page_description(body)
        return ""

    elif command == "p":
        return f"<p>{body}</p>"

    elif command == "anchor":
        return f"<span id='{body}'></span>"

    elif command == "footnote":
        return f"<sup>{add_footnote(body)}</sup>"

    elif command == "rss":
        global rss_date
        rss_date = datetime.strptime(tokens[1].strip(), "%Y-%m-%d %H:%M")
        return RSS_TAG

    elif command == "mediabutton":
        image_filename = body
        os.system(f'''cp "{get_images_dir()}/{image_filename}" "{get_docs_dir()}/images/{image_filename}"''')
        show(f"Copied {image_filename} to the images directory.")
        return f"<img src =\"images/{image_filename}\" class=\"mediabutton\">"

    elif command == "img":
        image_filename, grayscale = parse_image_tag(body)
        return get_image_tag(image_filename, epigrafe=False, grayscale=grayscale, use_custom_classes=use_custom_classes)

    elif command == "midimg":
        image_filename, grayscale = parse_image_tag(body)
        return get_image_tag(image_filename, grayscale=grayscale, half_width=True,
                             use_custom_classes=use_custom_classes)

    elif command == "bigimg":
        image_filename, grayscale = parse_image_tag(body)
        return get_image_tag(image_filename, grayscale=grayscale, use_custom_classes=use_custom_classes)

    elif command == "logo":
        image_filename = body
        os.system(f'''cp "{get_images_dir()}/{image_filename}" "{get_docs_dir()}/images/{image_filename}"''')
        show(f"Copied {image_filename} to the images directory.")
        return f"<img src =\"images/{image_filename}\" class=\"logo\">"

    elif command == "sitemap":
        return get_sitemap()

    elif command == "l":
        body = re.sub(r"(\n( *)\n)+", "\n", body).strip() + "\n"
        body = body.replace("\n", "</li>")
        body = body.replace("::", "<li>")
        return f"<ul>\n{body}\n</ul>"

    # If we didn't return by this point, the tag was not recognized.
    warning(f"The tag {tag} was not recognized.")
    return tag


def get_sitemap():
    global sitemap
    sitemap_source = "<ul>"
    for key in sitemap:
        sitemap_source += f'\n<li><a href="{key}">{sitemap[key]}</a></li>'
    sitemap_source += "\n</ul>"
    return sitemap_source


def parse_image_tag(tag_body):
    '''Returns tag info for an image: filename, grayscale.
    '''
    img_tokens = tag_body.split()
    image_filename = img_tokens[0]
    grayscale = False
    if "bw" in img_tokens:
        grayscale = True
    return image_filename, grayscale


def get_image_tag(filename, compress=True, epigrafe=True, half_width=False, grayscale=False, use_custom_classes=True):
    '''Takes an image and returns a tag according to the requested type of image.
    '''
    MAX_IMG_WIDTH = 800
    image_title, file_ext = os.path.splitext(filename)
    file_ext = file_ext.strip(".")
    img_file = get_images_dir() + "/" + filename
    picture = ImageOps.exif_transpose(Image.open(img_file))
    width, height = picture.size
    imghash = get_image_hash_name(image_title)
    image_filename = f"{imghash}.{file_ext}"
    os.system(f'''cp "{img_file}" "{get_docs_dir()}/images/{image_filename}"''')  # Save original image
    show(f"Copied {filename} to the images directory as {image_filename}.")
    compression_format = "JPEG"
    compresed_image_file = imghash + "." + compression_format
    jpeg_note = f" ({compression_format}) "
    max_width = MAX_IMG_WIDTH
    if half_width:
        max_width = int(max_width / 2)
        compresed_image_file = imghash + ".png"
        compression_format = "PNG"
        jpeg_note = ""
    if width > max_width:
        compressed_filename = get_docs_dir() + "/images/c_" + compresed_image_file
        if compress:
            show(f"Optimizing {image_filename}.")
            picture = picture.resize((max_width, int(height*max_width/width)))
            picture = picture.convert("RGBA")
            new_image = Image.new("RGBA", picture.size, "WHITE")
            new_image.paste(picture, (0, 0), picture)
            if grayscale:
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
            if grayscale:
                bwnote = "(b&w version) "
        if not epigrafe:
            return f"<p><img src =\"images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\"></p>"
        else:
            class_tag = ""
            if half_width and use_custom_classes:
                class_tag = "class=\"midimg\""
            return f"<p><img {class_tag} src =\"images/c_{compresed_image_file}\" title=\"{imghash}\" alt=\"Image: {imghash}\"><small>— {imghash} {bwnote}{jpeg_note}- {vieworiginal}</small></p>"
    else:
        return f"<p><img src =\"images/{image_filename}\" title=\"{imghash}\" alt=\"Image: {imghash}\"></p>"


def get_image_hash_name(original_name):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = str(int(hashlib.sha1(original_name.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
    while len(numbers) < 8:
        numbers += "0"
    final_name = letters[int(numbers[0:2]) % len(
        letters)] + numbers[2:4] + letters[int(numbers[4:6]) % len(letters)] + numbers[6:8]
    return final_name

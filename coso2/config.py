import os


def get_base_dir():
    '''Gets the base directory for this script.
    '''
    return os.path.abspath(os.path.dirname(__file__)) + "/.."


def get_sources_dir():
    '''Gets the sources directory.
    '''
    return get_base_dir() + "/source"


def get_docs_dir():
    '''Gets the build directory.
    '''
    return get_base_dir() + "/docs"


def get_images_dir():
    '''Gets the images directory.
    '''
    return get_base_dir() + "/images"


def get_files_dir():
    '''Gets the files directory.
    '''
    return get_base_dir() + "/files"


def get_styles_file():
    '''Gets the route for the CSS styles file.
    '''
    return get_base_dir() + "/styles.css"


def get_CNAME_file():
    '''Gets the route for the CNAME file.
    '''
    return get_base_dir() + "/CNAME"


def get_favicon_name():
    '''Returns the filename of the favicon.
    '''
    return "fuyukogif2.png"


def get_default_page_title():
    '''Gets the default page title for pages with no name.
    '''
    return "Lartu.net"


def get_default_page_description():
    '''Gets the default page description for pages with no description.
    '''
    return ""


def get_document_head(page_title=None, favicon=None, description=None):
    '''Gets the HTML <head> tag for an HTML page.
    '''
    if page_title is None:
        page_title = get_default_page_title()
    if favicon is None:
        favicon = get_favicon_name()
    if description is None:
        description = get_default_page_description()
    head = "<head>"
    head += f'''\n\t<title>{page_title}</title>'''
    head += '''\n\t<link rel="stylesheet" href="styles.css">'''
    head += '''\n\t<meta charset="utf-8">'''
    head += '''\n\t<meta name="viewport" content="width=device-width, initial-scale=1">'''
    head += f'''\n\t<link rel="shortcut icon" type="image/png" href="images/{favicon}" />'''
    head += f'''\n\t<link rel="apple-touch-icon" sizes="180x180" href="/files/apple-touch-icon.png">'''
    head += f'''\n\t<link rel="icon" type="image/png" sizes="32x32" href="/files/favicon-32x32.png">'''
    head += f'''\n\t<link rel="icon" type="image/png" sizes="16x16" href="/files/favicon-16x16.png">'''
    head += f'''\n\t<link rel="manifest" href="/files/site.webmanifest">'''
    head += f'''\n\t<link rel="mask-icon" href="/files/safari-pinned-tab.svg" color="#000000">'''
    head += f'''\n\t<link rel="shortcut icon" href="/files/favicon.ico">'''
    head += f'''\n\t<meta name="msapplication-TileColor" content="#da532c">'''
    head += f'''\n\t<meta name="msapplication-config" content="/files/browserconfig.xml">'''
    head += f'''\n\t<meta name="theme-color" content="#ffffff">'''
    head += f'''\n\t<meta name="description" content="{description}">'''
    head += '''\n\t<link rel='alternate' type='application/rss+xml' title='RSS Feed' href='files/rss.xml.rss'/>'''
    head += '''\n</head>'''
    return head


def get_rss_header():
    '''Gets the RSS opening part for the RSS file.
    '''
    return '''
        <?xml version='1.0' encoding='UTF-8'?>
        <rss version='2.0' xmlns:dc="http://purl.org/dc/elements/1.1/">
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


def get_rss_footer():
    '''Gets the RSS closing part for the RSS file.
    '''
    return "</channel></rss>"

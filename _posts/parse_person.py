#!/usr/bin/python
from shutil import copyfile
from PIL import Image
import frontmatter
from bs4 import BeautifulSoup
from math import floor

PATH_TO_SITE = '/Users/kellycaylor/Documents/website/caylor/'
AUTHOR_FILE = PATH_TO_SITE + '_data/authors.yml'
SANDBOX_PATH = '/Users/kellycaylor/Documents/website/sandbox/wordpress_uploads'  # NOQA


def make_author(author):
    author_string = ''
    keys = set(author.keys()) - set(['name'])
    author_string += str('\n\n{author}:'.format(author=author['name']))
    for key in keys:
        author_string += str('\n\t\t{key}{space}: "{value}"'.format(
            key=key,
            space=''.join([' ' for i in range(12-len(key))]),
            value=author[key]))
    return author_string


def parse_post(filename):

    print("Parsing {filename}".format(filename=filename))

    post = frontmatter.load(filename)

    # HEADER RECONSTRUCTION ---------------------------------------------------
    # Step 1: Remove junk we don't need from header.
    header_keys = [
        'id',
        'title',
        'date',
        'author',
        'categories',
        'tags',
        'header'
        'excerpt',
    ]

    # Only keep the header content we want:
    new_meta = {}
    for key in header_keys:
        new_meta[key] = post.metadata.get(key, None)

    # CONTENT RECONSTRUCTION ------------------------------------------------------
    # There are more ways to skin this cat.
    # Most commonly, we end up with a <figure> tag in the content.
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(post.content, 'html.parser')

    # grab any figure html tags:
    imgs = soup.find_all('imgs')
    if imgs:
        img = imgs[0]
        soup.figure.extract()
    else:
        img = ''

    if img:
        # Grab caption text out of this figure:
        header = {}
        caption = figure.find_all('figcaption')
        if caption:
            header['caption'] = caption[0].text
        header['old_image'] = figure.find_all('img')[0].attrs['data-src']
        # copy header_image to assets and rename:
        a = ['assets']
        a.extend(header['old_image'].split('/')[2:])
        src = '/'.join(a)
        ext = src.split('.')[1]  # jpg or png.
        dst = 'assets/images/people/{LastName}_header.{ext}'.format(
            LastName=LastName,
            ext=ext)
        header['image'] = dst
        src = PATH_TO_SITE + src
        dst = PATH_TO_SITE + dst
        try:
            copyfile(src, dst)
        except:
            a = ['']
            a.extend(header['old_image'].split('/')[1:])
            src = '/'.join(a)
            ext = src.split('.')[1]  # jpg or png.
            src = SANDBOX_PATH + src
            copyfile(src, dst)
        header_im = Image.open(dst)
        # check for landscape orientation:
        [width, height] = header_im.size
        if width/height > 1.5 and width > 500:
            new_meta['header'] = {
                'image': header['image'],
                'caption': header['caption']
            }

    # Check for a button. This would be a link to a personal website.
    buttons = soup.find_all('button')
    # remove any buttons from content:
    if buttons:
        button = buttons[0]
        soup.button.extract()
    else:
        button = ''

    # AUTHOR CONSTRUCTION ------------------------------------------------------
    if input('Add {name} as an author?:'.format(name=new_meta['author'])):
        author = {}
        author['name'] = new_meta['author']
        if button:
            author['uri'] = button.attrs['data-href']
        author['avatar'] = new_meta['avatar']
        author_attrs = {
            'bio': 'job title',
            'twitter': 'twitter handle',
            'linkedin': 'linkedin username',
            'github': 'github username',
            'skype': 'skype id',
            'location': 'current location'
        }

        for key in author_attrs:
            key_value = input('Enter the {attribute} of {person}: '.format(
                attribute=author_attrs[key],
                person=author['name']))
            if key_value:
                author[key] = key_value

        print(make_author(author))
        with open(AUTHOR_FILE, "a") as myfile:
            myfile.write(make_author(author))

    # FILE RE-WRITE:
    post.metadata = new_meta
    post.content = str(soup)

    POST_FILE = PATH_TO_SITE + '_people/' + LastName.lower() + '.md'
    with open(POST_FILE, "w") as postfile:
        postfile.write(frontmatter.dumps(post))

    print(frontmatter.dumps(post))

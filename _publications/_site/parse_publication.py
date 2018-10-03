#!/usr/bin/python
from shutil import copyfile
from PIL import Image
import frontmatter
from bs4 import BeautifulSoup
import re

PATH_TO_SITE = '/Users/kellycaylor/Documents/website/caylor/'
AUTHOR_FILE = PATH_TO_SITE + '_data/authors.yml'
SANDBOX_PATH = '/Users/kellycaylor/Documents/website/sandbox/wordpress_uploads'  # NOQA


def strip_tags(soup, invalid_tags):
    for tag in invalid_tags:
        for match in soup.findAll(tag):
            match.replaceWithChildren()
    return soup


def parse_publication(filename):

    print("Parsing {filename}".format(filename=filename))

    post = frontmatter.load(filename)

    # HEADER RECONSTRUCTION ---------------------------------------------------
    # Step 1: Remove junk we don't need from header.
    header_keys = [
        'id',
        'title',
        'date',
        'author',
        'excerpt',
        'portfolio-item-category',
        'portfolio-item-tag',
    ]

    # Only keep the header content we want:
    new_meta = {}
    for key in header_keys:
        new_meta[key] = post.metadata.get(key, None)

    # Step 2:
    # Use the excerpt to determine new author name (watch out for characters):
    print('------\n\n{citation}\n\n'.format(
        citation=new_meta['excerpt']))
    author = input(
        'Author is currently {author}. Replace or [Enter] to keep.'.format(
            author=new_meta['author']))
    if author:
        new_meta['author'] = author
    [*FirstNames, LastName] = new_meta['author'].split(' ')  # Handle names.

    # Define year of publication
    obj = re.search(r'\((20[0-9][0-9])\)', new_meta['excerpt'])
    new_meta['year'] = obj.group(1)

    # CONTENT RECONSTRUCTION --------------------------------------------------
    # There are more ways to skin this cat.
    # Most commonly, we end up with a <figure> tag in the content.
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(post.content, 'html.parser')

    # Pull out any spans and p tags:
    soup = strip_tags(soup, ['p', 'span'])

    # grab the image:
    images = soup.find_all('img')
    if images:
        image = images[0]
    if image:
        header = {}
        # Grab caption text out of this figure:
        # copy header_image to assets and rename:
        a = ['assets']
        try:
            a.extend(image.attrs['data-src'].split('/')[2:])
        except:
            a.extend(image.attrs['src'].split('/')[4:])
        src = '/'.join(a)
        ext = src.split('.')[-1]  # jpg, png, or gif.
        dst = 'assets/images/publications/{LastName}{year}_{id}.{ext}'.format(
            LastName=LastName,
            year=new_meta['year'],
            id=post.metadata['id'],
            ext=ext)
        header['teaser'] = dst
        src = PATH_TO_SITE + src
        dst = PATH_TO_SITE + dst
        try:
            copyfile(src, dst)
        except:
            a = ['']
            a.extend(image.attrs['data-src'].split('/')[1:])
            src = '/'.join(a)
            ext = src.split('.')[-1]  # jpg or png.
            src = SANDBOX_PATH + src
            copyfile(src, dst)
        im = Image.open(dst)
        [width, height] = im.size
        if width > 400:
            print('Adding teaser image ({width} x {height}'.format(
                width=width, height=height))
            new_meta['header'] = header
        else:
            print('Cover image too small to use for teaser image')

    # Replace Figure tag with markdown image reference.
    image_style = '{:class="img-responsive" width="50%" .align-right}'
    image_md = '![first page]( {{{{"{image_location}" | absolute_url}}}} ){image_style}'.format(  # NOQA
        image_location=header['teaser'],
        image_style=image_style)

    figure = soup.find_all('figure')[0]
    figure.replaceWith(image_md)

    # Check for a button. This would be a link to a personal website.
    buttons = soup.find_all('button')
    # replace buttons with markdown:
    if buttons:
        for button in buttons:
            if 'Read' in button.text:
                # Check to see if we are using an eri url:
                if 'caylor.eri' in button.attrs['data-href']:
                    # Copy the file to assets folder and change link
                    a = ['assets']
                    a.extend(button.attrs['data-href'].split('/')[4:])
                    src = '/'.join(a)
                    filename = src.split('/')[-1]
                    dst = 'assets/pdfs/publications/' + filename
                    link = '{{{{ "{dst}" | absolute_url }}}}'.format(
                        dst=dst)
                    src = PATH_TO_SITE + src
                    dst = PATH_TO_SITE + dst
                    try:
                        copyfile(src, dst)
                    except:
                        a = ['']
                        a.extend(button.attrs['data-href'].split('/')[4:])
                        src = '/'.join(a)
                        ext = src.split('.')[-1]  # jpg or png.
                        src = SANDBOX_PATH + src
                        copyfile(src, dst)
                else:
                    link = button.attrs['data-href']
                button_md = '\n[{text}]({link}){{: .btn .btn--success}}'.format(
                    link=link,
                    text=button.text)
            else:
                button_md = '\n[{text}]({link}){{: .btn .btn--success}}'.format(
                    link=button.attrs['data-href'],
                    text=button.text)
            button.replaceWith(button_md)

    # FILE RE-WRITE:
    post.metadata = new_meta
    post.content = str(soup.prettify(formatter=None))

    out_file = '{LastName}{year}_{id}.md'.format(
        LastName=LastName,
        year=new_meta['year'],
        id=post.metadata['id'])
    POST_FILE = PATH_TO_SITE + '_publications/' + out_file
    with open(POST_FILE, "w") as postfile:
        postfile.write(frontmatter.dumps(post))

    print(frontmatter.dumps(post))

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


def parse_person(filename):

    print("Parsing {filename}".format(filename=filename))

    post = frontmatter.load(filename)

    # HEADER RECONSTRUCTION ---------------------------------------------------
    # Step 1: Remove junk we don't need from header.
    header_keys = [
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
    # Use the title to guess at person's name (watch out for characters):
    new_meta['author'] = new_meta['title'].split(',')[0]
    [*FirstNames, LastName] = new_meta['author'].split(' ')  # Handle names.

    # Step 3:
    # Define the avatar file and copy the avatar file to the assets directory.
    # We assume that the image: file will be the avatar file.
    a = ['assets']
    a.extend(post.metadata['image'].split('/')[2:])
    src = '/'.join(a)
    ext = src.split('.')[1]  # jpg or png.
    dst = 'assets/images/people/{LastName}.{ext}'.format(
        LastName=LastName,
        ext=ext)
    new_meta['avatar'] = dst
    src = PATH_TO_SITE + src
    dst = PATH_TO_SITE + dst
    try:
        copyfile(src, dst)
    except:
        # Look for the src file in our sandbox folder.
        a = ['']
        a.extend(post.metadata['image'].split('/')[2:])
        src = '/'.join(a)
        ext = src.split('.')[1]  # jpg or png.
        src = SANDBOX_PATH + src
        copyfile(src, dst)

    # Step 4:
    # Resize the avatar image so it is a square.
    #  - Load image using Pillow (PIL)
    im = Image.open(dst)
    #  - Get image size (Image.size)
    [width, height] = im.size
    #  - Use image size to determine square cropping box
    # (it's the smaller of the 2 dimensions)
    if width is not height:  # Square images are our friend.
        #  - Calculate the cropping box, centered on middle of image (optimistic)
        if width < height:  # We will trim from image top and bottom to square
            # box = [ (left, upper, right, lower)]
            trim = floor((height - width)/2)
            box = [0, trim, width, height-trim]
        if width > height:  # We will trim from the image left and right to square
            trim = floor((width-height)/2)
            box = [trim, 0, width-trim, height]
    #  - Crop the image.
        cropped_im = im.crop(box=box)
    #  - Save the image (keep the old in case of off-center faces)
        cropped_im.save(dst)
        im.save(dst.split('.')[0] + '_backup.' + ext)

    # CONTENT RECONSTRUCTION ------------------------------------------------------
    # There are more ways to skin this cat.
    # Most commonly, we end up with a <figure> tag in the content.
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(post.content, 'html.parser')

    # grab any figure html tags:
    figures = soup.find_all('figure')
    if figures:
        figure = figures[0]
        soup.figure.extract()
    else:
        figure = ''

    if figure:
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

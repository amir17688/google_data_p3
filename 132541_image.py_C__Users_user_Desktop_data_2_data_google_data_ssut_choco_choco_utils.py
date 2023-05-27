import urllib
import io
from PIL import Image
from StringIO import StringIO

def get_image_size(url):
    try:
        if url.startswith('http'):
            fd = urllib.urlopen(url)
            url = io.BytesIO(fd.read())

        im = Image.open(url)
        return im.size
    except Exception, e:
        return None
import os
import re
import sys
import json
import time
import click
import socket
import shutil
import hashlib
import tempfile
import requests
import subprocess
from requests.exceptions import RequestException, SSLError

try:
    from selenium import webdriver
    from PIL import Image
    browser_available = True
except ImportError:
    browser_available = False

if sys.platform.startswith('linux'):
    from pyvirtualdisplay import Display
    needs_display = True
else:
    needs_display = False

from werkzeug.urls import url_parse
from werkzeug.datastructures import Headers


_kv_re = re.compile(r'^(.*?)\s*:\s*(.*?)$')

CAPTURE_SIZE = (1280, 720)
THUMBNAIL_SIZES = (
    ('m', 720, 405),
    ('s', 540, 304),
    ('xs', 320, 180),
)
WZ_405_HASH = '01b1df0ce8e76f49129f112be3fb0cdfef696818'
MAX_STALE_CACHE = 60 * 60 * 24 * 7


class ProbeResult(object):

    def __init__(self, site_exists=True, werkzeug_405=False,
                 responds_to_head=False):
        self.site_exists = site_exists
        self.werkzeug_405 = werkzeug_405
        self.responds_to_head = responds_to_head

    def to_dict(self):
        return dict(self.__dict__)

    def __repr__(self):
        return 'ProbseResult(%s)' % ', '.join(
            '%s=%r' % (k, v)
            for k, v in sorted(self.__dict__.items()),
        )


class FlaskProbeCrawler(object):

    def __init__(self):
        self.session = requests.session()
        self.closed = False

    def close(self):
        if self.closed:
            return
        self.session.close()
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def test_website(self, url):
        site_exists = self.session.get(url).ok

        # Assuming nobody actually uses this.
        rv = self.session.request('CONNECT', url)
        werkzeug_405 = False
        responds_to_head = False

        if rv.status_code == 405 and \
           hashlib.sha1(rv.content).hexdigest() == WZ_405_HASH and \
           'allow' in rv.headers:
            werkzeug_405 = True

        if site_exists:
            rv = self.session.request('HEAD', url)
            if rv.status_code == 200 and not rv.content:
                responds_to_head = True

        return ProbeResult(
            site_exists=site_exists,
            werkzeug_405=werkzeug_405,
            responds_to_head=responds_to_head,
        )


class ImageCrawler(object):

    def __init__(self, target_dir, capture_size=None, thumbnail_sizes=None):
        self.target_dir = target_dir
        if capture_size is None:
            capture_size = CAPTURE_SIZE
        if needs_display:
            self.display = Display(visible=0, size=capture_size)
            self.display.start()
        else:
            self.display = None
        self._browser = None
        self.closed = False
        self.working_dir = tempfile.mkdtemp()
        self.capture_size = capture_size
        if thumbnail_sizes is None:
            thumbnail_sizes = THUMBNAIL_SIZES
        self.thumbnail_sizes = thumbnail_sizes

    def get_browser(self):
        if self._browser is not None:
            return self._browser
        self._browser = webdriver.Firefox()
        self._browser.set_window_size(*self.capture_size)
        return self._browser

    def close(self):
        try:
            shutil.rmtree(self.working_dir)
        except (IOError, OSError):
            pass
        if not self.closed:
            if self._browser is not None:
                self._browser.quit()
            if self.display is not None:
                self.display.stop()
        self.closed = True

    def get_filename(self, short_name, thumb_name):
        return os.path.join(self.target_dir, '%s/%s.png' % (
            short_name,
            thumb_name,
        ))

    def iter_thumbnail_sizes(self):
        yield ('l',) + self.capture_size
        for item in self.thumbnail_sizes:
            yield item

    def take_screenshot(self, url, short_name=None):
        if short_name is None:
            url_info = url_parse(url)
            short_name = url_info.ascii_host
            url_path = (url_info.path or '/').strip('/')
            if url_path:
                short_name += '.' + url_path

        fn = tempfile.mktemp('.png', prefix='capture', dir=self.working_dir)
        browser = self.get_browser()
        browser.get(url)
        browser.save_screenshot(fn)
        im = Image.open(fn)

        for thumb_name, width, height in self.iter_thumbnail_sizes():
            small = im.crop((0, 0, im.size[0],
                             min(im.size[1], self.capture_size[1])))
            small.thumbnail((width, height), Image.ANTIALIAS)
            fn = self.get_filename(short_name, thumb_name)
            try:
                os.makedirs(os.path.dirname(fn))
            except OSError:
                pass
            small.save(fn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()


def read_mime(f):
    headers = []
    h = hashlib.sha1()

    def _readline():
        line = f.readline()
        h.update(line)
        if not line.strip():
            return u''
        return line.rstrip('\r\n').decode('utf-8')

    while 1:
        line = _readline()
        if not line:
            break
        match = _kv_re.match(line)
        if match is not None:
            headers.append(match.groups())
            continue
        elif line[:1].isspace():
            old_key, old_value = headers[-1]
            headers[-1] = (old_key, old_value + u' ' + line[1:])
        else:
            raise ValueError('Invalid mime data')

    payload = f.read()
    h.update(payload)
    return Headers(headers), payload, h.hexdigest()


class RepoProcessor(object):

    def __init__(self, repo, log=False):
        self.log = log
        self.repo = repo
        self.cache = {}
        self.cache_filename = os.path.join(self.repo, 'cache', 'websites.json')

        image_path = os.path.join(self.repo, 'cache', 'images')
        try:
            os.makedirs(image_path)
        except OSError:
            pass
        self.probe_crawler = FlaskProbeCrawler()
        self.image_crawler = ImageCrawler(image_path)

        if os.path.isfile(self.cache_filename):
            with open(self.cache_filename, 'rb') as f:
                self.cache.update(json.load(f))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def close(self):
        self.image_crawler.close()
        self.probe_crawler.close()

    def process_website(self, domain):
        if self.log:
            click.echo('Processing %s' % click.style(domain, fg='cyan'))
        filename = os.path.join(self.repo, 'websites', domain)
        cache_entry = self.cache.get(domain)

        with open(filename, 'rb') as f:
            headers, payload, checksum = read_mime(f)

        if not (cache_entry is None or
                cache_entry['checksum'] != checksum or
                cache_entry['last_update'] < time.time() - MAX_STALE_CACHE):
            if self.log:
                click.secho('  not modified', fg='yellow')
            return False

        url = headers.get('url')
        if not url:
            url = 'http://%s/' % domain

        try:
            test_result = self.probe_crawler.test_website(url)
        except (socket.error, SSLError, RequestException):
            if self.log:
                click.secho('  request exception, not modified', fg='yellow')
            return False

        if test_result.site_exists:
            self.image_crawler.take_screenshot(url, short_name=domain)

        self.cache[domain] = {
            'checksum': checksum,
            'last_update': int(time.time()),
            'probe': test_result.to_dict(),
            'url': url,
            'name': headers.get('name'),
            'source': headers.get('source'),
            'description': payload,
        }
        if self.log:
            click.secho('  updated', fg='green')
        return True

    def process_all(self):
        updated = []
        p = os.path.join(self.repo, 'websites')
        for filename in os.listdir(p):
            if os.path.isfile(os.path.join(p, filename)) and \
               not filename.startswith(('.', '_')):
                if self.process_website(filename):
                    updated.append(filename)
        return updated

    def write_cache(self):
        if self.log:
            click.secho('Writing cache', fg='green')
        with open(self.cache_filename, 'wb') as f:
            body = json.dumps(self.cache, indent=2, sort_keys=True)
            for line in body.splitlines():
                f.write(line.rstrip() + '\n')

    def commit(self, changes):
        if not changes:
            return

        if self.log:
            click.secho('Committing changes', fg='green')

        msg = 'Updated website cache\n\nUpdated sites:\n\n%s' % \
            '\n'.join('- %s' % x for x in changes)

        self.git('add', 'cache')
        self.git('commit', '-am', msg)

    def pull(self, reset=True):
        if self.log:
            click.secho('Pulling changes', fg='green')
        if reset:
            self.git('reset', '--hard')
        self.git('pull', '--rebase')

    def push(self):
        if self.log:
            click.secho('Pushing changes', fg='green')
        self.git('pull', '--rebase')
        self.git('push')

    def git(self, *args, **extra):
        """Runs a git command."""
        extra.setdefault('cwd', self.repo)
        return subprocess.Popen(['git'] + list(args), **extra).wait()


def run_processor(repo, log=False, commit=False, push=False):
    with RepoProcessor(repo, log=log) as processor:
        processor.pull()
        changes = processor.process_all()
        if changes:
            processor.write_cache()
            if commit:
                processor.commit(changes)
                if push:
                    processor.push()


@click.command()
@click.option('--repo', help='The path to the repo',
              default='./repo', type=click.Path())
@click.option('--commit/--no-commit', help='Instructs the crawler to '
              'commit to the repo or not.  Default is to commit.',
              default=True)
@click.option('--push/--no-push', help='Instructs the crawler to '
              'push to the origin or not.  Defaults to push.',
              default=True)
def cli(repo, commit, push):
    """Crawls the websites from the powered-by-repo"""
    click.echo('Processing %s' % repo)
    run_processor(repo, log=True, commit=commit, push=push)
    click.echo('Done.')

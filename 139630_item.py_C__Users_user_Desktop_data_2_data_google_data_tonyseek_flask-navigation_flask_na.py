import collections

from flask import url_for, request, Markup

from .utils import freeze_dict, join_html_attrs


class Item(object):
    """The navigation item object.

    :param label: the display label of this navigation item.
    :param endpoint: the unique name of this navigation item.
                     If this item point to a internal url, this parameter
                     should be acceptable for ``url_for`` which will generate
                     the target url.
    :param args: optional. If this parameter be provided, it will be passed to
                 the ``url_for`` with ``endpoint`` together.
                 Maybe this arguments need to be decided in the Flask app
                 context, then this parameter could be a function to delay the
                 execution.
    :param url: optional. If this parameter be provided, the target url of
                this navigation will be it. The ``endpoint`` and ``args`` will
                not been used to generate url.
    :param html_attrs: optional. This :class:`dict` will be used for
                       representing html.

    The ``endpoint`` is the identity name of this navigation item. It will be
    unique in whole application. In mostly situation, it should be a endpoint
    name of a Flask view function.
    """

    def __init__(self, label, endpoint, args=None, url=None, html_attrs=None,
                 items=None):
        self.label = label
        self.endpoint = endpoint
        self._args = args
        self._url = url
        self.html_attrs = {} if html_attrs is None else html_attrs
        self.items = ItemCollection(items or None)

    def __html__(self):
        attrs = dict(self.html_attrs)

        # adds ``active`` to class list
        html_class = attrs.get('class', [])
        if self.is_active:
            html_class.append('active')

        # joins class list
        attrs['class'] = ' '.join(html_class)
        if not attrs['class']:
            del attrs['class']
        attrs['href'] = self.url
        attrs_template, attrs_values = join_html_attrs(attrs)

        return Markup('<a %s>{label}</a>' % attrs_template).format(
            *attrs_values, label=self.label)

    def __html_format__(self, format_spec):
        if format_spec == 'li':
            li_attrs = Markup(' class="active"') if self.is_active else ''
            return Markup('<li{0}>{1}</li>').format(li_attrs, self.__html__())
        elif format_spec:
            raise ValueError('Invalid format spec')
        return self.__html__()

    @property
    def args(self):
        """The arguments which will be passed to ``url_for``.

        :type: :class:`dict`
        """
        if self._args is None:
            return {}
        if callable(self._args):
            return dict(self._args())
        return dict(self._args)

    @property
    def url(self):
        """The final url of this navigation item.

        By default, the value is generated by the :attr:`self.endpoint` and
        :attr:`self.args`.

        .. note::

           The :attr:`url` property require the app context without a provided
           config value :const:`SERVER_NAME`, because of :func:`flask.url_for`.

        :type: :class:`str`
        """
        if self.is_internal:
            return url_for(self.endpoint, **self.args)
        return self._url

    @property
    def is_active(self):
        """``True`` if the item should be presented as active, and ``False``
        always if the request context is not bound.
        """
        return bool(request and self.is_current)

    @property
    def is_internal(self):
        """``True`` if the target url is internal of current app."""
        return self._url is None

    @property
    def is_current(self):
        """``True`` if current request has same endpoint with the item.

        The property should be used in a bound request context, or the
        :class:`RuntimeError` may be raised.
        """
        if not self.is_internal:
            return False  # always false for external url
        has_same_endpoint = (request.endpoint == self.endpoint)
        has_same_args = (request.view_args == self.args)
        return has_same_endpoint and has_same_args  # matches the endpoint

    @property
    def ident(self):
        """The identity of this item.

        :type: :class:`~flask.ext.navigation.Navigation.ItemReference`
        """
        return ItemReference(self.endpoint, self.args)


class ItemCollection(collections.MutableSequence,
                     collections.Iterable):
    """The collection of navigation items.

    This collection is a mutable sequence. All items have order index, and
    could be found by its endpoint name. e.g.::

        c = ItemCollection()
        c.append(Item(endpoint='doge'))

        print(c['doge'])  # output: Item(endpoint='doge')
        print(c[0])       # output: Item(endpoint='doge')
        print(c)          # output: ItemCollection([Item(endpoint='doge')])
        print(len(c))     # output: 1

        c.append(Item(endpoint='lumpy', args={'num': 4}))

        print(c[1])       # output: Item(endpoint='lumpy', args={'num': 4})
        assert c['lumpy', {'num': 4}] is c[1]
    """

    def __init__(self, iterable=None):
        #: the item collection
        self._items = []
        #: the mapping collection of endpoint -> item
        self._items_mapping = {}
        #: initial extending
        self.extend(iterable or [])

    def __repr__(self):
        return 'ItemCollection(%r)' % self._items

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._items[index]

        if isinstance(index, tuple):
            endpoint, args = index
        else:
            endpoint, args = index, {}
        ident = ItemReference(endpoint, args)
        return self._items_mapping[ident]

    def __setitem__(self, index, item):
        # remove the old reference
        old_item = self._items[index]
        del self._items_mapping[old_item.ident]

        self._items[index] = item
        self._items_mapping[item.ident] = item

    def __delitem__(self, index):
        item = self[index]
        del self._items[index]
        del self._items_mapping[item.ident]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def insert(self, index, item):
        self._items.insert(index, item)
        self._items_mapping[item.ident] = item


class ItemReference(collections.namedtuple('ItemReference', 'endpoint args')):
    """The identity tuple of navigation item.

    :param endpoint: the endpoint of view function.
    :type endpoint: ``str``
    :param args: the arguments of view function.
    :type args: ``dict``
    """

    def __new__(cls, endpoint, args=()):
        if isinstance(args, dict):
            args = freeze_dict(args)
        return super(cls, ItemReference).__new__(cls, endpoint, args)
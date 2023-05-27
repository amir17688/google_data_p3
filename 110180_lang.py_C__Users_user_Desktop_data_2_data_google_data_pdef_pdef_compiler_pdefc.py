# encoding: utf-8
import logging
import os
import re
import collections


class Node(object):
    doc = None
    location = None

    def __init__(self):
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        return child

    def walk(self):
        q = collections.deque()
        q.append(self)
        
        while q:
            node = q.popleft()
            if node.children:
                children = list(node.children)
                children.reverse()
                q.extendleft(children)
            
            yield node
            

    def link(self, errors, scope):
        '''Link this node.'''
        pass

    def validate(self, errors):
        '''Validate this node.'''
        pass


class Package(Node):
    def __init__(self, files=None):
        super(Package, self).__init__()

        self.files = []
        for file in files or ():
            self.add_file(file)

    def add_file(self, file):
        if file.package:
            raise ValueError('Cannot add a file to %s, the file is already in a package, %s',
                             self, file)

        self.files.append(file)
        self.add_child(file)
        file.package = self

    def compile(self, errors=None):
        '''Compile this package and return errors.'''
        errors = errors or Errors()

        # Prevent duplicate types.
        if self._has_duplicate_types(errors):
            return errors

        # Link.
        for node in self.walk():
            node.link(errors, self)
        if errors:
            return errors

        # Validate.
        for node in self.walk():
            node.validate(errors)

        return errors

    def find(self, name):
        for file in self.files:
            if name in file.type_map:
                return file.type_map[name]

        return None

    def _has_duplicate_types(self, errors):
        names = set()
        for file in self.files:
            for type0 in file.types:
                errors.assert_that(type0.name not in names, type0.location,
                                   'Duplicate type "%s"', type0.name)
                names.add(type0.name)
        return errors


class File(Node):
    name_pattern = re.compile(r'^[a-zA-Z]{1}[a-zA-Z0-9_]*(\.[a-zA-Z]{1}[a-zA-Z0-9_]*)*$')

    def __init__(self, path, types=None):
        super(File, self).__init__()

        self.path = path
        self.package = None

        self.types = []
        self.type_map = {}

        for def0 in types or ():
            self.add_type(def0)

    def __str__(self):
        return self.path

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.path, hex(id(self)))

    @property
    def dotname(self):
        '''Returns a pdef file name without an extension with dots instead of separators.'''
        path = os.path.normpath(self.path)
        path = os.path.splitext(path)[0]
        return path.replace(os.path.sep, '.')

    def add_type(self, type0):
        '''Add a new type to this file.'''
        if type0.file:
            raise ValueError('Cannot add a type to %s, the type is already in an file, %s',
                             self, type0)

        self.types.append(type0)
        self.type_map[type0.name] = type0
        self.add_child(type0)
        type0.file = self

        return type0

    def validate(self, errors):
        errors.assert_that(
            self.name_pattern.match(self.dotname), self.location,
            'Wrong file name "%s". File and directory names must contain only latin letters, '
            'digits and underscores, and must start with a letter."' % self.path)


class Reference(Node):
    '''Type reference.'''

    @classmethod
    def empty(cls):
        return Reference()

    def __init__(self, name=None):
        super(Reference, self).__init__()

        self.name = name
        self.type = None

    @property
    def is_empty(self):
        return self.name is None

    def __str__(self):
        if self.is_empty:
            return '<empty>'

        return self.name or str(self.type)

    def __repr__(self):
        if self.is_empty:
            return '<EmptyReference at %s>' % hex(id(self))

        name = self.name
        type = self.type
        return '<Reference name=%s, type=%s at %s>' % (name, type, hex(id(self)))

    def dereference(self):
        '''Return a type this references points to or raise ValueError when not linked.'''
        if self.is_empty:
            return None

        if self.type:
            return self.type

        logging.warn('Accessing a not linked reference %r at %s', self, self.location)
        return self

    def link(self, errors, scope):
        '''Link this reference in a scope.'''
        if self.is_empty or self.type:
            return

        logging.debug('Linking %s: %s', self.location, self)
        self.type = scope.find(self.name)
        errors.assert_that(self.type is not None, self.location, 'Symbol not found "%s"', self.name)


class ReferenceProperty(object):
    '''Stores a reference or a type as a property, breaks cycles in AST via references to types.'''
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        ref = getattr(instance, self.name)
        return ref.dereference() if isinstance(ref, Reference) else ref

    def __set__(self, instance, value):
        if isinstance(value, Reference) or isinstance(value, (List, Set, Map)):
            child = value
        else:
            # Break cycles in AST.
            child = Reference(value.name)
            child.type = value
        
        setattr(instance, self.name, child)
        instance.add_child(child)


class Type(Node):
    def __init__(self, name):
        super(Type, self).__init__()
        self.name = name
        self.file = None
        self.is_exception = False

        self.is_bool = name == 'bool'
        self.is_int16 = name == 'int16'
        self.is_int32 = name == 'int32'
        self.is_int64 = name == 'int64'
        self.is_float = name == 'float'
        self.is_double = name == 'double'
        self.is_string = name == 'string'
        self.is_datetime = name == 'datetime'
        self.is_void = name == 'void'

        self.is_enum = isinstance(self, Enum)
        self.is_struct = isinstance(self, Struct)
        self.is_interface = isinstance(self, Interface)

        self.is_list = isinstance(self, List)
        self.is_set = isinstance(self, Set)
        self.is_map = isinstance(self, Map)
        self.is_collection = isinstance(self, (List, Set, Map))

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.name, hex(id(self)))

    @property
    def is_number(self):
        return self in (INT16, INT32, INT64, FLOAT, DOUBLE)

    @property
    def is_datatype(self):
        return not self.is_interface and not self.is_void

    @property
    def referenced_types(self):
        '''Return a set of all types referenced in this type (in fields, methods, etc).'''
        types = set()
        for node in self.walk():
            if isinstance(node, Reference):
                types.add(node.dereference())

            elif isinstance(node, Type):
                types.add(node)

        types.discard(self)
        return types


class List(Type):
    element = ReferenceProperty('_element')
    
    def __init__(self, element):
        super(List, self).__init__('list')
        self.element = element

    def __repr__(self):
        return '<List %r>' % self.element

    def __str__(self):
        return 'list<%s>' % self.element

    def validate(self, errors):
        errors.assert_that(self.element.is_datatype, self.location,
                           'List element must be a data type')


class Set(Type):
    element = ReferenceProperty('_element')
    
    def __init__(self, element):
        super(Set, self).__init__('set')
        self.element = element

    def __repr__(self):
        return '<Set %r>' % self.element

    def __str__(self):
        return 'set<%s>' % self.element

    def validate(self, errors):
        errors.assert_that(self.element.is_datatype, self.location,
                           'Set element must be a data type')


class Map(Type):
    key = ReferenceProperty('_key')
    value = ReferenceProperty('_value')
    
    def __init__(self, key, value):
        super(Map, self).__init__('map')
        self.key = key
        self.value = value

    def __repr__(self):
        return '<Map %r, %r>' % (self.key, self.value)

    def __str__(self):
        return 'map<%s, %s>' % (self.key, self.value)

    def validate(self, errors):
        errors.assert_that(self.key.is_number or self.key.is_string,
                           self.location, 'Map key must be a number or a string')
        errors.assert_that(self.value.is_datatype, self.location, 'Map value must be a data type')


class Enum(Type):
    def __init__(self, name, values=None):
        super(Enum, self).__init__(name)
        self.values = []

        for value in values or ():
            self.create_value(value)

    def add_value(self, value):
        '''Add a value to this enum.'''
        if value.enum:
            raise ValueError('Cannot add an enum value to %s, the value is already in an enum, %s',
                             self, value)

        self.values.append(value)
        self.add_child(value)
        value.enum = self

        return value

    def create_value(self, value_or_name):
        '''Create a new enum value by its name, add it to this enum, and return it.'''
        if isinstance(value_or_name, EnumValue):
            return self.add_value(value_or_name)

        return self.add_value(EnumValue(value_or_name))

    def validate(self, errors):
        names = set()
        for value in self.values:
            if value.name in names:
                errors.add_error(value.location, 'Duplicate enum value "%s"', value.name)
                continue

            names.add(value.name)


class EnumValue(Node):
    def __init__(self, name):
        super(EnumValue, self).__init__()
        self.name = name
        self.enum = None


class Struct(Type):
    def __init__(self, name, fields=None, is_exception=False):
        super(Struct, self).__init__(name)

        self.fields = []
        self.is_exception = is_exception

        for field in fields or ():
            self.add_field(field)

    def add_field(self, field):
        '''Add a new field to this message and return the field.'''
        if field.struct:
            raise ValueError('Cannot add a field to %s, the field is already in another '
                             'struct, %s', self, field)

        self.fields.append(field)
        self.add_child(field)
        field.struct = self

        return field

    def create_field(self, name, type0):
        '''Create a new field, add it to struct message and return.'''
        field = Field(name, type0)
        return self.add_field(field)

    def validate(self, errors):
        # Prevent duplicate field names.
        names = set()
        for field in self.fields:
            if field.name in names:
                errors.add_error(field.location, 'Duplicate field "%s"', field.name)
                continue
            names.add(field.name)


class Field(Node):
    type = ReferenceProperty('_type')
    
    def __init__(self, name, type0, location=None):
        super(Field, self).__init__()
        self.name = name
        self.type = type0
        self.struct = None
        self.location = location

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.name, hex(id(self)))

    def validate(self, errors):
        errors.assert_that(self.type.is_datatype, self.location, 'Field type must be a data type')


class Interface(Type):
    def __init__(self, name, methods=None):
        super(Interface, self).__init__(name)
        self.methods = []

        for method in methods or ():
            self.add_method(method)

    def add_method(self, method):
        '''Add a method to this interface.'''
        if method.interface:
            raise ValueError('Cannot add a method to %s, the method is already in '
                             'an interface: %s', self, method)

        self.methods.append(method)
        self.add_child(method)
        method.interface = self

        return method

    def create_method(self, name, type='GET', result=None, args=None):
        '''Add a new method to this interface and return the method.'''
        method = Method(name, type=type, result=result, args=args)
        return self.add_method(method)

    def validate(self, errors):
        # Prevent duplicate methods.
        names = set()
        for method in self.methods:
            if method.name in names:
                errors.add_error(method.location, 'Duplicate method "%s"', method.name)

            names.add(method.name)


class Method(Node):
    result = ReferenceProperty('_result')
    
    def __init__(self, name, type=None, result=None, args=None, is_request=None):
        super(Method, self).__init__()
        self.name = name
        self.type = type or MethodType.GET
        self.result = result or VOID
        
        self.is_request = is_request
        self.interface = None

        self.args = []
        for arg in args or ():
            self.add_arg(arg)

        if is_request and len(args) != 1:
            raise ValueError('Method must have only one request argument')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.name, hex(id(self)))

    @property
    def is_get(self):
        return self.type == MethodType.GET

    @property
    def is_post(self):
        return self.type == MethodType.POST

    @property
    def is_last(self):
        return self.result.is_datatype or self.result.is_void

    def add_arg(self, arg):
        '''Append an argument to this method.'''
        if arg.method:
            raise ValueError('Argument is already in a method, %s' % arg)

        self.args.append(arg)
        self.add_child(arg)
        arg.method = self

        return arg

    def create_arg(self, name, type):
        '''Create a new arg and add it to this method.'''
        arg = Argument(name, type)
        return self.add_arg(arg)

    def validate(self, errors):
        # Assert post methods have data type results.
        errors.assert_that(self.type in (MethodType.GET, MethodType.POST), self.location,
                           'Unknown method type "%s"', self.type)

        if self.is_post:
            errors.assert_that(self.is_last, self.location,
                               'POST method must have a data type result or be void')

        # Prevent duplicate arguments.
        names = set()
        for arg in self.args:
            if arg.name in names:
                errors.add_error(arg.location, 'Duplicate method argument "%s"', arg.name)
            names.add(arg.name)


class MethodType(object):
    GET = 'GET'
    POST = 'POST'


class Argument(Node):
    type = ReferenceProperty('_type')
    
    def __init__(self, name, type0):
        super(Argument, self).__init__()
        self.name = name
        self.type = type0
        self.method = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.name, hex(id(self)))

    def validate(self, errors):
        errors.assert_that(self.type.is_datatype, self.location,
                           '"%s" argument must be a data type', self.name)


class Location(object):
    def __init__(self, path=None, lineno=0):
        self.path = path
        self.lineno = lineno

    def __str__(self):
        if not self.path:
            return 'Line %s' % (self.lineno)
        if not self.lineno:
            return self.path
        return '%s, line %s' % (self.path, self.lineno)

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__, self.lineno, hex(id(self)))


class Errors(object):
    def __init__(self):
        self.errors = []

    def __bool__(self):
        return bool(self.errors)

    def __nonzero__(self):
        return bool(self.errors)

    def __getitem__(self, item):
        return self.errors[item]

    def __iter__(self):
        return iter(self.errors)

    def __len__(self):
        return len(self.errors)

    def __str__(self):
        return '\n'.join(self.errors)

    def assert_that(self, expression, location, message, *args):
        if expression:
            return

        self.add_error(location, message, *args)

    def add_error(self, location, message, *args):
        error = message % args
        if location:
            error = '%s: %s' % (location, error)
        self.errors.append(error)

    def add_errors(self, iterable):
        self.errors.extend(iterable)


BOOL = Type('bool')
INT16 = Type('int16')
INT32 = Type('int32')
INT64 = Type('int64')
FLOAT = Type('float')
DOUBLE = Type('double')
STRING = Type('string')
DATETIME = Type('datetime')
VOID = Type('void')

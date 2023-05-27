import sys

OrderedDict = None

if sys.version_info >= (3, 0):
    import collections
    OrderedDict = collections.OrderedDict
else:
    import provision.ordered_dict
    OrderedDict = provision.ordered_dict.OrderedDict

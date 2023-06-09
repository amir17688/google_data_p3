"""ResourceSync Change Dump object

A Change Dump is a set of content dump package resources
with some metadata for each resource. 

The Change Dump may also contain metadata and links like
other ResourceSync documents.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#ChangeDump
"""

from .resource_list import ResourceList

class ChangeDump(ResourceList):
    """Class representing an Change Dump

    A ChangeDump comprises a set of content dump packages that
    are the resources listed. Properties similar to a ResourceList
    and implemented as a sub-class of ResourceList.
    """

    def __init__(self, resources=None, md=None, ln=None, uri=None, allow_multifile=None, mapper=None):
        super(ChangeDump, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                         mapper=mapper)
        self.capability_name='changedump' 

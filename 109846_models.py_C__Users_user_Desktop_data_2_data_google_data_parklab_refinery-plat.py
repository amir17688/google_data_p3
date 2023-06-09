'''
Created on May 10, 2012

@author: nils
'''

from datetime import datetime
import logging
import requests

from django.conf import settings
from django.db import models
from django_extensions.db.fields import UUIDField

from data_set_manager.genomes import map_species_id_to_default_genome_build


logger = logging.getLogger(__name__)


"""
General:
- xyz_term = accession number of an ontology term
- xyz_source = reference to the ontology where xyz_term originates (defined in
    the investigation)
"""


class NodeCollection(models.Model):
    """Base class for Investigation and Study
    """
    uuid = UUIDField(unique=True, auto=True)
    identifier = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        # change dates from empty string to None (to pass validation)
        if "submission_date" in kwargs:
            if kwargs["submission_date"] == "":
                kwargs["submission_date"] = None
            else:
                kwargs["submission_date"] = self.normalize_date(
                    kwargs["submission_date"]
                )

        if "release_date" in kwargs:
            if kwargs["release_date"] == "":
                kwargs["release_date"] = None
            else:
                kwargs["release_date"] = self.normalize_date(
                    kwargs["release_date"]
                )

        super(NodeCollection, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return (
            unicode(self.identifier) +
            (
                ": " +
                unicode(self.title) if unicode(self.title) != "" else ""
            ) +
            ": " +
            unicode(self.id)
        )

    def normalize_date(self, dateString):
        """Normalizes date strings in dd/mm/yyyy format to yyyy-mm-dd.
        Returns normalized date string if in expected unnormalized format or
        unnormalized date string.
        """
        logger.info("Converting date " + str(dateString) + " ...")
        try:
            # try reformatting incorrect date format used by Nature Scientific
            # Data
            return str(
                datetime.strftime(
                    datetime.strptime(
                        dateString,
                        "%d/%m/%Y"
                    ),
                    "%Y-%m-%d"
                )
            )
        except ValueError:
            # ignore - date either in correct format or in format not supported
            # (will cause a validation error handled separately)
            logger.info("Failed to convert date " + str(dateString) + "!")
            return dateString


class Publication(models.Model):
    """Investigation or Study Publication (ISA-Tab Spec 4.1.2.2, 4.1.3.3)"""
    collection = models.ForeignKey(NodeCollection)
    title = models.TextField(blank=True, null=True)
    authors = models.TextField(blank=True, null=True)
    pubmed_id = models.TextField(blank=True, null=True)
    doi = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    # TODO: do we really want to store ontology information for this?
    status_accession = models.TextField(blank=True, null=True)
    status_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.authors) + ": " + unicode(self.title)


class Contact(models.Model):
    """Investigation or Study Contact (ISA-Tab Spec 4.1.2.3, 4.1.3.7)"""
    collection = models.ForeignKey(NodeCollection)
    last_name = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    middle_initials = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    fax = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    affiliation = models.TextField(blank=True, null=True)
    # TODO: split on semicolon
    roles = models.TextField(blank=True, null=True)
    # TODO: do we really want to store ontology information for this?
    roles_accession = models.TextField(blank=True, null=True)
    roles_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return (
            unicode(self.first_name) +
            " " +
            unicode(self.last_name) +
            " (" +
            unicode(self.email) +
            ")"
        )


class Investigation(NodeCollection):
    isarchive_file = UUIDField(blank=True, null=True, auto=False)
    pre_isarchive_file = UUIDField(blank=True, null=True, auto=False)

    """easily retrieves the proper NodeCollection fields"""
    def get_identifier(self):
        print type(self.identifier)
        if (self.identifier is None) or (self.identifier.strip() == ""):
            # if there's no investigation identifier, then there's only 1 study
            study = self.study_set.all()[0]
            return study.identifier
        return self.identifier

    def get_title(self):
        if self.title == '' or self.title is None:
            study = self.study_set.all()[0]
            return study.title
        return self.title

    def get_description(self):
        if self.description is None or self.description == '':
            study = self.study_set.all()[0]
            return study.description
        return self.description

    def get_study_count(self):
        return self.study_set.count()

    def get_assay_count(self):
        studies = self.study_set.all()
        assay_count = 0
        for study in studies:
            assay_count += study.assay_set.count()

        return assay_count


class Ontology(models.Model):
    """Ontology Source Reference (ISA-Tab Spec 4.1.1)"""
    investigation = models.ForeignKey(Investigation)
    name = models.TextField(blank=True, null=True)
    file_name = models.TextField(blank=True, null=True)
    version = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name) + " (" + unicode(self.file_name) + ")"


class Study(NodeCollection):
    investigation = models.ForeignKey(Investigation)
    # TODO: should we support an archive file here? (see ISA-Tab Spec 4.1.3.2)
    file_name = models.TextField()

    def assay_nodes(self):
        self.node_set(type=Node.ASSAY)

    def __unicode__(self):
        return unicode(self.identifier) + ": " + unicode(self.title)


class Design(models.Model):
    """Study Design Descriptor (ISA-Tab Spec 4.1.3.2)"""
    study = models.ForeignKey(Study)
    type = models.TextField(blank=True, null=True)
    type_accession = models.TextField(blank=True, null=True)
    type_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.type)


class Factor(models.Model):
    """Study Factor (ISA-Tab Spec 4.1.3.4)"""
    study = models.ForeignKey(Study)
    name = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    type_accession = models.TextField(blank=True, null=True)
    type_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name) + ": " + unicode(self.type)


class Assay(models.Model):
    """Study Assay (ISA-Tab Spec 4.1.3.5)"""
    uuid = UUIDField(unique=True, auto=True)
    study = models.ForeignKey(Study)
    measurement = models.TextField(blank=True, null=True)
    measurement_accession = models.TextField(blank=True, null=True)
    measurement_source = models.TextField(blank=True, null=True)
    technology = models.TextField(blank=True, null=True)
    technology_accession = models.TextField(blank=True, null=True)
    technology_source = models.TextField(blank=True, null=True)
    platform = models.TextField(blank=True, null=True)
    file_name = models.TextField()

    def __unicode__(self):
        retstr = ""
        if self.measurement:
            retstr += "Measurement: %s; " % unicode(self.measurement)

        if self.technology:
            retstr += "Technology: %s; " % unicode(self.technology)

        if self.platform:
            retstr += "Platform: %s; " % unicode(self.platform)

        retstr += "File: %s" % unicode(self.file_name)
        return retstr


class Protocol(models.Model):
    """Study Protocol (ISA-Tab Spec 4.1.3.6)"""
    study = models.ForeignKey(Study)
    uuid = UUIDField(unique=True, auto=True)
    # workflow_uuid can be used to associate the protocol with a workflow
    # TODO: should this be the analysis uuid? (problem: technically an analysis
    # is the execution of a protocol)
    workflow_uuid = UUIDField(unique=True, auto=True)
    version = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    name_accession = models.TextField(blank=True, null=True)
    name_source = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    type_accession = models.TextField(blank=True, null=True)
    type_source = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    uri = models.TextField(blank=True, null=True)
    # protocol parameters: via FK
    # protocol components: via FK

    def __unicode__(self):
        return unicode(self.name) + ": " + unicode(self.type)

    class Meta:
        ordering = ['id']


class ProtocolParameter(models.Model):
    study = models.ForeignKey(Study)
    protocol = models.ForeignKey(Protocol)
    name = models.TextField(blank=True, null=True)
    name_accession = models.TextField(blank=True, null=True)
    name_source = models.TextField(blank=True, null=True)


class ProtocolComponent(models.Model):
    study = models.ForeignKey(Study)
    protocol = models.ForeignKey(Protocol)
    name = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    type_accession = models.TextField(blank=True, null=True)
    type_source = models.TextField(blank=True, null=True)


class NodeManager(models.Manager):
    def genome_builds_for_files(self, file_uuids, default_fallback=True):
        """Returns a dictionary that groups file nodes based on their genome
        build information
        """
        file_list = Node.objects.filter(file_uuid__in=file_uuids).values(
            "species", "genome_build", "file_uuid")
        result = {}
        for item in file_list:
            if (item["genome_build"] is None and
                    item["species"] is not None and
                    default_fallback is True):
                item["genome_build"] = map_species_id_to_default_genome_build(
                    item["species"])
            if item["genome_build"] not in result:
                result[item["genome_build"]] = []
            result[item["genome_build"]].append(item["file_uuid"])
        return result


class Node(models.Model):
    # allowed node types
    SOURCE = "Source Name"
    SAMPLE = "Sample Name"
    EXTRACT = "Extract Name"
    LABELED_EXTRACT = "Labeled Extract Name"

    SCAN = "Scan Name"
    NORMALIZATION = "Normalization Name"
    DATA_TRANSFORMATION = "Data Transformation Name"

    ASSAY = "Assay Name"
    HYBRIDIZATION_ASSAY = "Hybridization Assay Name"
    GEL_ELECTROPHORESIS_ASSAY = "Gel Electrophoresis Assay Name"
    NMR_ASSAY = "NMR Assay Name"
    MS_ASSAY = "MS Assay Name"

    ARRAY_DESIGN_FILE = "Array Design File"
    ARRAY_DESIGN_FILE_REF = "Array Design File REF"
    IMAGE_FILE = "Image File"
    RAW_DATA_FILE = "Raw Data File"
    DERIVED_DATA_FILE = "Derived Data File"
    ARRAY_DATA_FILE = "Array Data File"
    DERIVED_ARRAY_DATA_FILE = "Derived Array Data File"
    ARRAY_DATA_MATRIX_FILE = "Array Data Matrix File"
    DERIVED_ARRAY_DATA_MATRIX_FILE = "Derived Array Data Matrix File"
    SPOT_PICKING_FILE = "Spot Picking File"
    RAW_SPECTRAL_DATA_FILE = "Raw Spectral Data File"
    DERIVED_SPECTRAL_DATA_FILE = "Derived Spectral Data File"
    PEPTIDE_ASSIGNMENT_FILE = "Peptide Assignment File"
    PROTEIN_ASSIGNMENT_FILE = "Protein Assignment File"
    PTM_ASSIGNMENT_FILE = "Post Translational Modification Assignment File"
    FREE_INDUCTION_DECAY_DATA_FILE = "Free Induction Decay Data File"
    ACQUISITION_PARAMETER_DATA_FILE = "Aquisition Parameter Data File"

    ASSAYS = {
        ASSAY,
        HYBRIDIZATION_ASSAY,
        MS_ASSAY,
        NMR_ASSAY,
        GEL_ELECTROPHORESIS_ASSAY
    }

    FILES = {
        ARRAY_DESIGN_FILE,
        ARRAY_DESIGN_FILE_REF,
        IMAGE_FILE,
        RAW_DATA_FILE,
        DERIVED_DATA_FILE,
        ARRAY_DATA_FILE,
        DERIVED_ARRAY_DATA_FILE,
        ARRAY_DATA_MATRIX_FILE,
        DERIVED_ARRAY_DATA_MATRIX_FILE,
        SPOT_PICKING_FILE,
        RAW_SPECTRAL_DATA_FILE,
        DERIVED_SPECTRAL_DATA_FILE,
        PEPTIDE_ASSIGNMENT_FILE,
        PROTEIN_ASSIGNMENT_FILE,
        PTM_ASSIGNMENT_FILE,
        FREE_INDUCTION_DECAY_DATA_FILE,
        ACQUISITION_PARAMETER_DATA_FILE
    }

    TYPES = ASSAYS | FILES | {
        SOURCE, SAMPLE, EXTRACT, LABELED_EXTRACT, SCAN, NORMALIZATION,
        DATA_TRANSFORMATION}

    # replace default manager
    objects = NodeManager()

    uuid = UUIDField(unique=True, auto=True)
    study = models.ForeignKey(Study, db_index=True)
    assay = models.ForeignKey(Assay, db_index=True, blank=True, null=True)
    children = models.ManyToManyField(
        "self", symmetrical=False, related_name="parents_set")
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children_set")
    type = models.TextField(db_index=True)
    name = models.TextField(db_index=True)
    # only used for nodes representing files
    file_uuid = UUIDField(default=None, blank=True, null=True, auto=False)
    # Refinery internal "attributes" (exported as comment attributes)
    genome_build = models.TextField(db_index=True, null=True)
    species = models.IntegerField(db_index=True, null=True)
    is_annotation = models.BooleanField(default=False)
    analysis_uuid = UUIDField(default=None, blank=True, null=True, auto=False)
    subanalysis = models.IntegerField(null=True, blank=False)
    workflow_output = models.CharField(null=True, blank=False, max_length=100)

    def __unicode__(self):
        return unicode(self.type) + ": " + unicode(self.name) + " (" +\
               unicode(self.parents.count()) + " parents, " +\
               unicode(self.children.count()) + " children " + "| " +\
               "species: " + unicode(self.species) +\
               ", genome build: " + unicode(self.genome_build) + ")"

    def add_child(self, node):
        if node is None:
            return None
        self.children.add(node)
        self.save()
        node.parents.add(self)
        node.save()
        return self


class Attribute(models.Model):
    # allowed attribute types
    MATERIAL_TYPE = "Material Type"
    CHARACTERISTICS = "Characteristics"
    FACTOR_VALUE = "Factor Value"
    LABEL = "Label"
    COMMENT = "Comment"

    TYPES = {MATERIAL_TYPE, CHARACTERISTICS, FACTOR_VALUE, LABEL, COMMENT}

    ALL_FIELDS = [
        "id",
        "type",
        "subtype",
        "value",
        "value_unit",
        "value_accession",
        "value_source",
        "node"
    ]
    NON_ONTOLOGY_FIELDS = [
        "id",
        "type",
        "subtype",
        "value",
        "value_unit",
        "node"
    ]

    def is_attribute(self, string):
        return string.split("[")[0].strip() in self.TYPES

    node = models.ForeignKey(Node, db_index=True)
    type = models.TextField(db_index=True)
    # subtype further qualifies the attribute type, e.g. type = factor value
    # and subtype = age
    subtype = models.TextField(blank=True, null=True, db_index=True)
    value = models.TextField(blank=True, null=True, db_index=True)
    value_unit = models.TextField(blank=True, null=True)
    # if value_unit is not null value is numeric and value_accession and
    # value_source refer to value_unit (rather than value)
    value_accession = models.TextField(blank=True, null=True)
    value_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return (
            unicode(self.type) + (
                "" if self.subtype is None else " (" + unicode(
                    self.subtype
                ) + ")"
            ) +
            " = " +
            unicode(self.value)
        )


# non-ISA Tab
class AttributeDefinition(models.Model):
    study = models.ForeignKey(Study, db_index=True)
    assay = models.ForeignKey(Assay, db_index=True, blank=True, null=True)

    type = models.TextField(db_index=True)
    subtype = models.TextField(blank=True, null=True, db_index=True)

    # attribute value to match on
    value = models.TextField(blank=True, null=True, db_index=True)

    # definition of the attribute value
    definition = models.TextField(blank=True, null=True, db_index=True)

    value_accession = models.TextField(blank=True, null=True)
    value_source = models.TextField(blank=True, null=True)


# non-ISA Tab
class AttributeOrder(models.Model):
    study = models.ForeignKey(Study, db_index=True)
    assay = models.ForeignKey(Assay, db_index=True, blank=True, null=True)
    solr_field = models.TextField(db_index=True)
    # position of the attribute in the facet list and table
    rank = models.IntegerField(blank=True, null=True)
    # should this attribute be exposed to the user? if false the attribute will
    # never be shown to non-owner users
    is_exposed = models.BooleanField(default=True)
    # should this attribute be used as a facet?
    is_facet = models.BooleanField(default=True)
    # should be shown in the table by default?
    is_active = models.BooleanField(default=True)
    # is this an internal attribute? (retrieved by solr by never exposed to any
    # user)
    is_internal = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(
            self.solr_field +
            " [facet = " +
            str(self.is_facet) +
            " exp = " +
            str(self.is_exposed) +
            " act = " +
            str(self.is_active) +
            " int = " + str(self.is_internal) + "] = "
        ) + str(self.rank)


class AnnotatedNodeRegistry(models.Model):
    study = models.ForeignKey(Study, db_index=True)
    assay = models.ForeignKey(Assay, db_index=True, blank=True, null=True)
    node_type = models.TextField(db_index=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)


class AnnotatedNode(models.Model):
    node = models.ForeignKey(Node, db_index=True)
    attribute = models.ForeignKey(Attribute, db_index=True)
    study = models.ForeignKey(Study, db_index=True)
    assay = models.ForeignKey(Assay, db_index=True, blank=True, null=True)
    node_uuid = UUIDField()
    node_file_uuid = UUIDField(blank=True, null=True)
    node_type = models.TextField(db_index=True)
    node_name = models.TextField(db_index=True)
    attribute_type = models.TextField(db_index=True)
    # subtype further qualifies the attribute type, e.g. type = factor value
    # and subtype = age
    attribute_subtype = models.TextField(blank=True, null=True, db_index=True)
    attribute_value = models.TextField(blank=True, null=True, db_index=True)
    attribute_value_unit = models.TextField(blank=True, null=True)
    # genome information
    node_species = models.IntegerField(db_index=True, null=True)
    node_genome_build = models.TextField(db_index=True, null=True)
    node_analysis_uuid = UUIDField(
        default=None,
        blank=True,
        null=True,
        auto=False
    )
    node_subanalysis = models.IntegerField(null=True, blank=False)
    node_workflow_output = models.CharField(
        null=True,
        blank=False,
        max_length=100
    )
    # other information
    is_annotation = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.node_uuid)


def _is_internal_attribute(attribute):
    return attribute in ["uuid",
                         "study_uuid",
                         "assay_uuid",
                         "file_uuid",
                         "type",
                         "is_annotation",
                         "species",
                         "genome_build",
                         "name",
                         "analysis_uuid",
                         "subanalysis",
                         "output_type"]


def _is_active_attribute(attribute):
    return (not _is_internal_attribute(attribute) and attribute not in [])


def _is_exposed_attribute(attribute):
    return True


def _is_ignored_attribute(attribute):
    """Ignore Django internal Solr fields"""
    return attribute in ["django_ct", "django_id", "id"]


def _is_facet_attribute(attribute, study, assay):
    """Tests if a an attribute should be used as a facet by default.
    :param attribute: The name of the attribute.
    :type attribute: string
    :returns: True if the ratio between items in the data set and the number of
    facet attribute values is smaller than
    settings.DEFAULT_FACET_ATTRIBUTE_VALUES_RATIO, false otherwise.
    """
    ratio = 0.5

    types = ' OR '.join(
        '"{0}"'.format(type) for type in Node.FILES
    )

    url = '{base_url}data_set_manager/select'.format(
        base_url=settings.REFINERY_SOLR_BASE_URL
    )

    params = {
        'facet': 'true',
        'facet.field': attribute,
        'facet.sort': 'count',
        'facet.limit': '-1',
        'fq': 'study_uuid:{study_uuid} AND '
              'assay_uuid: {assay_uuid} AND '
              'is_annotation:false AND '
              'type:({types})'.format(
                  study_uuid=study.uuid,
                  assay_uuid=assay.uuid,
                  types=types
              ),
        'q': 'django_ct:data_set_manager.node',
        'rows': 1,
        'start': 0,
        'wt': 'json'
    }

    logger.debug('Query parameters: %s', params)

    headers = {'Accept': 'application/json'}

    response = requests.get(url, params=params, headers=headers)

    results = response.json()

    logger.debug('Query results: %s', results)

    if results['response']['numFound'] == 0:
        raise ValueError('No facets found.')

    items = results['response']['numFound']
    attributeValues = len(
        results['facet_counts']['facet_fields'][attribute]
    ) / 2

    return (attributeValues / items) < ratio


def initialize_attribute_order(study, assay):
    """Initializes the AttributeOrder table after all nodes for the given study
    and assay have been indexed by Solr.
    :param study: Study object to query for in AnnotatedNode.
    :type study: Study
    :param assay: Assay object to query for in AnnotatedNode.
    :type assay: Assay
    :returns: Number of attributes that were indexed.
    """

    types = ' OR '.join(
        '"{0}"'.format(type) for type in Node.FILES
    )

    url = '{base_url}data_set_manager/select'.format(
        base_url=settings.REFINERY_SOLR_BASE_URL
    )

    params = {
        'fq': 'study_uuid:{study_uuid} AND '
              'assay_uuid: {assay_uuid} AND '
              'is_annotation:false AND '
              'type:({types})'.format(
                  study_uuid=study.uuid,
                  assay_uuid=assay.uuid,
                  types=types
              ),
        'q': 'django_ct:data_set_manager.node',
        'rows': 1,
        'start': 0,
        'wt': 'json'
    }

    logger.debug('Query parameters: %s', params)

    headers = {'Accept': 'application/json'}

    response = requests.get(url, params=params, headers=headers)

    results = response.json()

    logger.debug('Query results: %s', results)

    if results['response']['numFound'] == 0:
        raise ValueError(
            'Assay node type is not supported. Please consult the official '
            'release candidate.'
        )

    attribute_order_objects = []
    rank = 0
    for key in results['response']['docs'][0]:
        is_facet = _is_facet_attribute(key, study, assay)
        is_exposed = _is_exposed_attribute(key)
        is_internal = _is_internal_attribute(key)
        is_active = _is_active_attribute(key)
        if not _is_ignored_attribute(key):
            attribute_order_objects.append(
                AttributeOrder(
                    study=study,
                    assay=assay,
                    solr_field=key,
                    rank=++rank,
                    is_facet=is_facet,
                    is_exposed=is_exposed,
                    is_internal=is_internal,
                    is_active=is_active
                )
            )
    # insert AttributeOrder objects into database
    AttributeOrder.objects.bulk_create(attribute_order_objects)

    return len(attribute_order_objects)


class ProtocolReference(models.Model):
    node = models.ForeignKey(Node)
    protocol = models.ForeignKey(Protocol)
    performer = models.TextField(blank=True, null=True)
    # performer_uuid can be used to associate the execution with a user account
    performer_uuid = UUIDField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.protocol) + " (reference)"


class ProtocolReferenceParameter(models.Model):
    protocol_reference = models.ForeignKey(ProtocolReference)
    name = models.TextField(blank=True, null=True)
    value = models.TextField(blank=True, null=True)
    value_unit = models.TextField(blank=True, null=True)
    # if value_unit is not null value is numeric and value_accession and
    # value_source refer to value_unit (rather than value)
    value_accession = models.TextField(blank=True, null=True)
    value_source = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name) + " = " + unicode(self.value)

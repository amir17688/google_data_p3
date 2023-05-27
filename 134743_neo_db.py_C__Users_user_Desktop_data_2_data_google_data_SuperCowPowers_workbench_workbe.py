"""NeoDB class for WorkBench."""

class NeoDB(object):
    """NeoDB indexer for Workbench."""

    def __init__(self, uri='http://localhost:7474/db/data'):
        """Initialization for NeoDB indexer.

        Args:
            uri: The uri to connect NeoDB.
        
        Raises:
            RuntimeError: When connection to NeoDB failed.
        """

        # Get connection to Neo4j
        try:
            # Open the Neo4j DB and get version (just testing Neo connection)
            self.graph_db = neo4j.GraphDatabaseService(uri)
            version = self.graph_db.neo4j_version
            print '\t- Neo4j GraphDB connected: %s %s' % (str(uri), version)
        except packages.httpstream.http.SocketError:
            print '\t- Neo4j connection failed! Is your Neo4j server running? $ neo4j start'
            raise RuntimeError('Could not connect to Neo4j')

    def add_node(self, node_id, name, labels):
        """Add the node with name and labels.

        Args:
            node_id: Id for the node.
            name: Name for the node.
            labels: Label for the node.

        Raises:
            NotImplementedError: When adding labels is not supported.
        """
        node = self.graph_db.get_or_create_indexed_node('Node', 'node_id', node_id, {'node_id': node_id, 'name': name})
        try:
            node.add_labels(*labels)
        except NotImplementedError:
            pass
            # Fixme: print 'Got a NotImplementedError when adding labels. Upgrade your Neo4j DB!'

    def has_node(self, node_id):
        """Checks if the node is present.

        Args:
            node_id: Id for the node.

        Returns:
            True if node with node_id is present, else False.
        """
        return True if self.graph_db.get_indexed_node('Node', 'node_id', node_id) else False

    def add_rel(self, source_node_id, target_node_id, rel):
        """Add a relationship between nodes.

        Args:
            source_node_id: Node Id for the source node.
            target_node_id: Node Id for the target node.
            rel: Name of the relationship 'contains'
        """

        # Add the relationship
        n1_ref = self.graph_db.get_indexed_node('Node', 'node_id', source_node_id)
        n2_ref = self.graph_db.get_indexed_node('Node', 'node_id', target_node_id)

        # Sanity check
        if not n1_ref or not n2_ref:
            print 'Cannot add relationship between unfound nodes: %s --> %s' % (source_node_id, target_node_id)
            return
        path = neo4j.Path(n1_ref, rel, n2_ref)
        path.get_or_create(self.graph_db)

    def clear_db(self):
        """Clear the Graph Database of all nodes and edges."""
        self.graph_db.clear()


class NeoDBStub(object):
    """NeoDB Stub."""

    def __init__(self, uri='http://localhost:7474/db/data'):
        """NeoDB Stub."""
        print 'NeoDB Stub connected: %s' % (str(uri))
        print 'Install Neo4j and python bindings for Neo4j. See README.md'

    def add_node(self, node_id, name, labels):
        """NeoDB Stub."""
        print 'NeoDB Stub getting called...'
        print '%s %s %s %s' % (self, node_id, name, labels)

    def has_node(self, node_id):
        """NeoDB Stub."""
        print 'NeoDB Stub getting called...'
        print '%s %s' % (self, node_id)

    def add_rel(self, source_node_id, target_node_id, rel):
        """NeoDB Stub."""
        print 'NeoDB Stub getting called...'
        print '%s %s %s %s' % (self, source_node_id, target_node_id, rel)

    def clear_db(self):
        """NeoDB Stub."""
        print 'NeoDB Stub getting called...'
        print '%s' % (self)

try:
    from py2neo import neo4j
    from py2neo import packages
    NeoDB = NeoDB
except (ImportError, RuntimeError):
    NeoDB = NeoDBStub

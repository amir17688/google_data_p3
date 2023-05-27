"""This client pushes PE Files -> ELS Indexer."""
import zerorpc
import os
import pprint
import client_helper

def run():
    """This client pushes PE Files -> ELS Indexer."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out PEFile -> strings -> indexer -> search
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/bad')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)][:20]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: 
            continue

        with open(filename, 'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'exe')

            # Index the strings and features output (notice we can ask for any worker output)
            # Also (super important) it all happens on the server side.
            workbench.index_worker_output('strings', md5, 'strings', None)
            print '\n<<< Strings for PE: %s Indexed>>>' % (base_name)
            workbench.index_worker_output('pe_features', md5, 'pe_features', None)
            print '<<< Features for PE: %s Indexed>>>' % (base_name)

    # Well we should execute some queries against ElasticSearch at this point but as of
    # version 1.2+ the dynamic scripting disabled by default, see
    # 'http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/modules-scripting.html#_enabling_dynamic_scripting

    # Now actually do something interesing with our ELS index
    # ES Facets are kewl (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-facets.html)
    facet_query = '{"facets" : {"tag" : {"terms" : {"field" : "string_list"}}}}'
    results = workbench.search_index('strings', facet_query)
    try:
        print '\nQuery: %s' % facet_query
        print 'Number of hits: %d' % results['hits']['total']
        print 'Max Score: %f' % results['hits']['max_score']
        pprint.pprint(results['facets'])
    except TypeError:
        print 'Probably using a Stub Indexer, if you want an ELS Indexer see the readme'

    # Fuzzy is kewl (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-fuzzy-query.html)
    fuzzy_query = '{"fields":["md5","sparse_features.imported_symbols"],' \
        '"query": {"fuzzy" : {"sparse_features.imported_symbols" : "loadlibrary"}}}'
    results = workbench.search_index('pe_features', fuzzy_query)
    try:
        print '\nQuery: %s' % fuzzy_query
        print 'Number of hits: %d' % results['hits']['total']
        print 'Max Score: %f' % results['hits']['max_score']
        pprint.pprint([(hit['fields']['md5'], hit['fields']['sparse_features.imported_symbols']) 
                       for hit in results['hits']['hits']])
    except TypeError:
        print 'Probably using a Stub Indexer, if you want an ELS Indexer see the readme'


def test():
    """Executes pe_strings_indexer test."""
    run()

if __name__ == '__main__':
    run()

"""DataStore class for WorkBench."""

import pymongo
import gridfs
import hashlib
import datetime
import bson
import time

class DataStore(object):
    """DataStore for Workbench. 

    Currently tied to MongoDB but making this class 'abstract'  should be 
    straightforward and we could think about using another backend.

    """

    def __init__(self, uri='mongodb://localhost/workbench', database='workbench', worker_cap=0, samples_cap=0):
        """ Initialization for the Workbench data store class.

        Args:
            uri: Connection String for DataStore backend.
            database: Name of database.
            worker_cap: MBs in the capped collection.
            samples_cap: MBs of sample to be stored.
        """
        
        self.sample_collection = 'samples'
        self.worker_cap = worker_cap
        self.samples_cap = samples_cap

        # Get connection to mongo
        self.database_name = database
        self.uri = 'mongodb://'+uri+'/'+self.database_name
        self.mongo = pymongo.MongoClient(self.uri, use_greenlets=True)
        self.database = self.mongo.get_default_database()

        # Get the gridfs handle
        self.gridfs_handle = gridfs.GridFS(self.database)

        # Run the periodic operations
        self.last_ops_run = time.time()
        self.periodic_ops()

        print '\t- WorkBench DataStore connected: %s:%s' % (self.uri, self.database_name)

    def get_uri(self):
        """ Return the uri of the data store."""
        return self.uri

    def store_sample(self, sample_bytes, filename, type_tag):
        """Store a sample into the datastore.

        Args:
            filename: Name of the file.
            sample_bytes: Actual bytes of sample. 
            type_tag: Type of sample ('exe','pcap','pdf','json','swf', or ...)

        Returns:
            md5 digest of the sample.
        """

        # Temp sanity check for old clients
        if len(filename) > 1000:
            print 'switched bytes/filename... %s %s' % (sample_bytes[:100], filename[:100])
            exit(1)

        sample_info = {}

        # Compute the MD5 hash
        sample_info['md5'] = hashlib.md5(sample_bytes).hexdigest()

        # Check if sample already exists
        if self.has_sample(sample_info['md5']):
            return sample_info['md5']

        # Run the periodic operations
        self.periodic_ops()

        # Check if we need to expire anything
        self.expire_data()

        # Okay start populating the sample for adding to the data store
        # Filename, length, import time and type_tag
        sample_info['filename'] = filename
        sample_info['length'] = len(sample_bytes)
        sample_info['import_time'] = datetime.datetime.utcnow()
        sample_info['type_tag'] = type_tag

        # Random customer for now
        import random
        sample_info['customer'] = random.choice(['Mega Corp', 'Huge Inc', 'BearTron', 'Dorseys Mom'])

        # Push the file into the MongoDB GridFS
        sample_info['__grid_fs'] = self.gridfs_handle.put(sample_bytes)
        self.database[self.sample_collection].insert(sample_info)

        # Print info
        print 'Sample Storage: %.2f out of %.2f MB' % (self.sample_storage_size(), self.samples_cap)

        # Return the sample md5
        return sample_info['md5']

    def sample_storage_size(self):
        """Get the storage size of the samples storage collection."""

        try:
            coll_stats = self.database.command('collStats', 'fs.chunks')
            sample_storage_size = coll_stats['size']/1024.0/1024.0
            return sample_storage_size
        except pymongo.errors.OperationFailure:
            return 0

    def expire_data(self):
        """Expire data within the samples collection."""

        # Do we need to start deleting stuff?
        while self.sample_storage_size() > self.samples_cap:

            # This should return the 'oldest' record in samples
            record = self.database[self.sample_collection].find().sort('import_time',pymongo.ASCENDING).limit(1)[0]
            self.remove_sample(record['md5'])

    def remove_sample(self, md5):
        """Delete a specific sample"""

        # Grab the sample
        record = self.database[self.sample_collection].find_one({'md5': md5})
        if not record:
            return

        # Delete it
        print 'Deleting sample: %s (%.2f MB)...' % (record['md5'], record['length']/1024.0/1024.0)
        self.database[self.sample_collection].remove({'md5': record['md5']})
        self.gridfs_handle.delete(record['__grid_fs'])

        # Print info
        print 'Sample Storage: %.2f out of %.2f MB' % (self.sample_storage_size(), self.samples_cap)

    def clean_for_serialization(self, data):
        """Clean data in preparation for serialization.

        Deletes items having key either a BSON, datetime, dict or a list instance, or
        starting with __.

        Args:
            data: Sample data to be serialized.

        Returns:
            Cleaned data dictionary.
        """

        if isinstance(data, dict):
            for k in data.keys():
                if (k.startswith('__')): 
                    del data[k]
                elif isinstance(data[k], bson.objectid.ObjectId): 
                    del data[k]
                elif isinstance(data[k], datetime.datetime):
                    data[k] = data[k].isoformat()+'Z'
                elif isinstance(data[k], dict):
                    data[k] = self.clean_for_serialization(data[k])
                elif isinstance(data[k], list):
                    data[k] = [self.clean_for_serialization(item) for item in data[k]]
        return data

    def clean_for_storage(self, data):
        """Clean data in preparation for storage.

        Deletes items with key having a '.' or is '_id'. Also deletes those items
        whose value is a dictionary or a list.

        Args:
            data: Sample data dictionary to be cleaned.

        Returns:
            Cleaned data dictionary.
        """
        data = self.data_to_unicode(data)
        if isinstance(data, dict):
            for k in dict(data).keys():
                if k == '_id':
                    del data[k]
                    continue
                if '.' in k:
                    new_k = k.replace('.', '_')
                    data[new_k] = data[k]
                    del data[k]
                    k = new_k
                if isinstance(data[k], dict):
                    data[k] = self.clean_for_storage(data[k])
                elif isinstance(data[k], list):
                    data[k] = [self.clean_for_storage(item) for item in data[k]]
        return data

    def get_full_md5(self, partial_md5, collection):
        """Support partial/short md5s, return the full md5 with this method"""
        print 'Notice: Performing slow md5 search...'
        starts_with = '%s.*' % partial_md5
        sample_info = self.database[collection].find_one({'md5': {'$regex' : starts_with}},{'md5':1})
        return sample_info['md5'] if sample_info else None

    def get_sample(self, md5):
        """Get the sample from the data store.

        This method first fetches the data from datastore, then cleans it for serialization
        and then updates it with 'raw_bytes' item.
        
        Args:
            md5: The md5 digest of the sample to be fetched from datastore.

        Returns:
            The sample dictionary or None
        """

        # Support 'short' md5s but don't waste performance if the full md5 is provided
        if len(md5) < 32:
            md5 = self.get_full_md5(md5, self.sample_collection)

        # Grab the sample
        sample_info = self.database[self.sample_collection].find_one({'md5': md5})
        if not sample_info:
            return None

        # Get the raw bytes from GridFS (note: this could fail)
        try:
            grid_fs_id = sample_info['__grid_fs']
            sample_info = self.clean_for_serialization(sample_info)
            sample_info.update({'raw_bytes':self.gridfs_handle.get(grid_fs_id).read()})
            return sample_info
        except gridfs.errors.CorruptGridFile:
            # If we don't have the gridfs files, delete the entry from samples
            self.database[self.sample_collection].update({'md5': md5}, {'md5': None})
            return None

    def get_sample_window(self, type_tag, size=10):
        """Get a window of samples not to exceed size (in MB).

        Args:
            type_tag: Type of sample ('exe','pcap','pdf','json','swf', or ...).
            size: Size of samples in MBs.

        Returns:
            a list of md5s.
        """

        # Convert size to MB
        size = size * 1024 * 1024

        # Grab all the samples of type=type_tag, sort by import_time (newest to oldest)
        cursor = self.database[self.sample_collection].find({'type_tag': type_tag},
            {'md5': 1,'length': 1}).sort('import_time',pymongo.DESCENDING)
        total_size = 0
        md5_list = []
        for item in cursor:
            if total_size > size:
                return md5_list
            md5_list.append(item['md5'])
            total_size += item['length']

        # If you get this far you don't have 'size' amount of data
        # so just return what you've got
        return md5_list

    def has_sample(self, md5):
        """Checks if data store has this sample.

        Args:
            md5: The md5 digest of the required sample.

        Returns:
            True if sample with this md5 is present, else False.
        """

        # The easiest thing is to simply get the sample and if that
        # succeeds than return True, else return False
        sample = self.get_sample(md5)
        return True if sample else False

    def _list_samples(self, predicate=None):
        """List all samples that meet the predicate or all if predicate is not specified.

        Args:
            predicate: Match samples against this predicate (or all if not specified)

        Returns:
            List of the md5s for the matching samples
        """
        cursor = self.database[self.sample_collection].find(predicate, {'_id':0, 'md5':1})
        return [item['md5'] for item in cursor]

    def tag_match(self, tags=None):
        """List all samples that match the tags or all if tags are not specified.

        Args:
            tags: Match samples against these tags (or all if not specified)

        Returns:
            List of the md5s for the matching samples
        """
        if 'tags' not in self.database.collection_names():
            print 'Warning: Searching on non-existance tags collection'
            return None
        if not tags:
            cursor = self.database['tags'].find({}, {'_id':0, 'md5':1})
        else:
            cursor = self.database['tags'].find({'tags': {'$in': tags}}, {'_id':0, 'md5':1})

        # We have the tags, now make sure we only return those md5 which 
        # also exist in the samples collection
        tag_md5s = set([item['md5'] for item in cursor])
        sample_md5s = set(item['md5'] for item in self.database['samples'].find({}, {'_id':0, 'md5':1}))
        return list(tag_md5s.intersection(sample_md5s))

    def tags_all(self):
        """List of the tags and md5s for all samples
        Args:
            None

        Returns:
            List of the tags and md5s for all samples
        """
        if 'tags' not in self.database.collection_names():
            print 'Warning: Searching on non-existance tags collection'
            return None

        cursor = self.database['tags'].find({}, {'_id':0, 'md5':1, 'tags':1})
        return [item for item in cursor]

    def store_work_results(self, results, collection, md5):
        """Store the output results of the worker.

        Args:
            results: a dictionary.
            collection: the database collection to store the results in.
            md5: the md5 of sample data to be updated.

        """

        # Make sure the md5 and time stamp is on the data before storing
        results['md5'] = md5
        results['__time_stamp'] = datetime.datetime.utcnow()

        # If the data doesn't have a 'mod_time' field add one now
        if 'mod_time' not in results:
            results['mod_time'] = results['__time_stamp']

        # Fixme: Occasionally a capped collection will not let you update with a 
        #        larger object, if you have MongoDB 2.6 or above this shouldn't
        #        really happen, so for now just kinda punting and giving a message.
        try:
            self.database[collection].update({'md5':md5}, self.clean_for_storage(results), True)
        except pymongo.errors.OperationFailure:
            #self.database[collection].insert({'md5':md5}, self.clean_for_storage(results), True)
            print 'Could not update exising object in capped collection, punting...'
            print 'collection: %s md5:%s' % (collection, md5)

    def get_work_results(self, collection, md5):
        """Get the results of the worker.

        Args:
            collection: the database collection storing the results.
            md5: the md5 digest of the data.

        Returns:
            Dictionary of the worker result.
        """
        return self.database[collection].find_one({'md5':md5})

    def all_sample_md5s(self, type_tag=None):
        """Return a list of all md5 matching the type_tag ('exe','pdf', etc).

        Args:
            type_tag: the type of sample.

        Returns:
            a list of matching samples.
        """

        if type_tag:
            cursor = self.database[self.sample_collection].find({'type_tag': type_tag}, {'md5': 1, '_id': 0})
        else:
            cursor = self.database[self.sample_collection].find({}, {'md5': 1, '_id': 0})
        return [match.values()[0] for match in cursor]

    def clear_worker_output(self):
        """Drops all of the worker output collections"""
        
        print 'Dropping all of the worker output collections... Whee!'
        # Get all the collections in the workbench database
        all_c = self.database.collection_names()

        # Remove collections that we don't want to cap
        try:
            all_c.remove('system.indexes')
            all_c.remove('fs.chunks')
            all_c.remove('fs.files')
            all_c.remove('sample_set')
            all_c.remove('tags')
            all_c.remove(self.sample_collection)
        except ValueError:
            print 'Catching a benign exception thats expected...'

        for collection in all_c:
            self.database.drop_collection(collection)

    def clear_db(self):
        """Drops the entire workbench database."""
        
        print 'Dropping the entire workbench database... Whee!'
        self.mongo.drop_database(self.database_name)

    def periodic_ops(self):
        """Run periodic operations on the the data store.
        
        Operations like making sure collections are capped and indexes are set up.
        """

        # Only run every 30 seconds
        if (time.time() - self.last_ops_run) < 30:
            return

        try:

            # Reset last ops run
            self.last_ops_run = time.time()
            print 'Running Periodic Ops'

            # Get all the collections in the workbench database
            all_c = self.database.collection_names()

            # Remove collections that we don't want to cap
            try:
                all_c.remove('system.indexes')
                all_c.remove('fs.chunks')
                all_c.remove('fs.files')
                all_c.remove('info')
                all_c.remove('tags')
                all_c.remove(self.sample_collection)
            except ValueError:
                print 'Catching a benign exception thats expected...'

            # Convert collections to capped if desired
            if self.worker_cap:
                size = self.worker_cap * pow(1024, 2)  # MegaBytes per collection
                for collection in all_c:
                    self.database.command('convertToCapped', collection, size=size)

            # Loop through all collections ensuring they have an index on MD5s
            for collection in all_c:
                self.database[collection].ensure_index('md5')

            # Add required indexes for samples collection
            self.database[self.sample_collection].create_index('import_time')

            # Create an index on tags
            self.database['tags'].create_index('tags')

    
        # Mongo may throw an autoreconnect exception so catch it and just return
        # the autoreconnect means that some operations didn't get executed but
        # because this method gets called every 30 seconds no biggy...
        except pymongo.errors.AutoReconnect as e:
            print 'Warning: MongoDB raised an AutoReconnect...' % e
            return
        except Exception as e:
            print 'Critical: MongoDB raised an exception' % e
            return

    # Helper functions
    def to_unicode(self, s):
        """Convert an elementary datatype to unicode.

        Args:
            s: the datatype to be unicoded.

        Returns:
            Unicoded data.
        """

        # Fixme: This is total horseshit
        if isinstance(s, unicode):
            return s
        if isinstance(s, str):
            return unicode(s, errors='ignore')

        # Just return the original object
        return s

    def data_to_unicode(self, data):
        """Recursively convert a list or dictionary to unicode.

        Args:
            data: The data to be unicoded.

        Returns:
            Unicoded data.
        """
        if isinstance(data, dict):
            return {self.to_unicode(k): self.to_unicode(v) for k, v in data.iteritems()}
        if isinstance(data, list):
            return [self.to_unicode(l) for l in data]
        else:
            return self.to_unicode(data)

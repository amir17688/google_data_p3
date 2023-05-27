# Glacier
# Copyright 2012 Paul Engstler
# See LICENSE for details.

import os, utils, math

class Archive(object):
	""" Archive API """

	def __init__(self, inp):
		"""
            Creates an archive instance
            
            Archives can either represent a local file instance or
			a remote id. As soon as the archive gets uploaded the 
			instance will transform.
            
			:param inp: local file name or archive id
            :type inp: string

		"""

		# Within Amazon Glacier files use their names and get ID labels.
		# If you want to keep the interface the same it should take
		# either a file name or an ID within Glacier.
		# That's why the input is undefinied at first.

		# As stated here (http://docs.amazonwebservices.com/amazonglacier/
		# latest/dev/working-with-archives.html) archive IDs are 138 bytes long.
		# If there is the coincidence that the file name is 138 bytes long
		# the result will still be interpreted as file if it exists.
	
		# If you run into trouble opening files on Mac: If you drag and drop
		# files into the editor/terminal the escaped strings wil look like
		# this: "\ ". This doesn't work for Python. Remove each backslash
		# and you will running again.

		if len(inp) == 138 and not os.path.isfile(inp):
			self.id = inp
		else:
			try:
				self.file = open(inp,"r")
				self.path = inp
				self.size = os.fstat(self.file.fileno()).st_size
				self.hash = utils.sha256(self.file)
				self.treehash = self.get_tree_hash()
			except IOError:
				raise IOError("file " + inp + " does not exist.")

	def get_tree_hash(self):
		"""
            Returns the tree hash of the archive

			.. note:: only works with a local archive
        """
        # This process takes some time for bigger files, please be patient
		# "The progress bar is moving but the remaining time is going up!"
		# - CollegeHumor, Matrix runs on WinXP
        
		chunk_size = 1024*1024 # 1 MB chunks
		chunk_count = int(math.ceil(float(self.size)/float(chunk_size)))

		chunk_hashes = []

		self.file.seek(0)

		for _ in range(chunk_count):
			# Read and immediately hash the chunk portion, we just need
			# 32 bytes stored for each 1 MB chunk. Now that's reducing
			# the memory footprint!
			chunk_hashes.append(utils.sha256_digest(self.file.read(chunk_size)))
    
		return utils.get_tree_hash(chunk_hashes)

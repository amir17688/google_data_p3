# Glacier
# Copyright 2012 Paul Engstler
# See LICENSE for details.

import json
from request import Request

class Vault(object):
	""" Vault API """
	
	def __init__(self, name, connection):
		"""
            Creates a vault instance
            
			:param name: name of the vault
            		:parm connection: Connection instance connected to the vault's
			region
        """
		self.connection = connection
		self.name = name
		self.region = self.connection.region

	def describe(self):
		"""
            Returns a description of the vault by requesting it
			from Amazon Glacier
            
			:return: Parsed answer from Amazon Glacier
			:rtype: dictionary
        """
		req = Request(self.connection, self.region, "GET",
		"/-/vaults/"+self.name)
		resp = req.send_request()
		return json.loads(resp.read())

	def upload(self, archive, description=""):
		"""
            Uploads an archive to this vault
            
			:param archive: An archive initialized with a file name
			:param description: Description of the archive (optional)

			:rtype: archive
        """
		header = 	{ 	
							"Content-Length":str(archive.size), 
							"x-amz-sha256-tree-hash":archive.treehash, 
							"x-amz-content-sha256":archive.hash
					}

		if description:
			header["x-amz-archive-description"] = description

		req = self.connection.make_request(	"POST",
							"/-/vaults/"+self.name+"/archives",
							signed=["x-amz-content-sha256"],
							header=header,
							body=archive.file)
											
		resp = req.send_request()

		if resp.status != 201:
			raise Exception("archive could not be created", resp)

		# assign the id to the archive
		archive.id = resp.getheader("x-amz-archive-id")

		return archive

	def delete(self, archive):
		"""
            Deletes an archive in this vault
            
			:param archive: An archive initialized with an id
        """
		req = self.connection.make_request(	"DELETE",
							"/-/vaults/"+self.name+\
							"/archives/"+archive.id)
		resp = req.send_request()

		if resp.status != 204:
			raise Exception("could not delete " + archive.id, resp)

	# Notifications

	def set_notifications(self, snstopic, events):
		"""
            Sets the notification topic and events for the vault
            
			:param snstopic: The SNS topic to which the selected events should
			be reported to
			:param events: The events that trigger a notification sent to the
			SNS topic
			:type snstopic: string
			:type events: list, tuple
        """
		config = { "SNSTopic":snstopic, "Events":events }
		req = self.connection.make_request(	"PUT",
											"/-/vaults/"+self.name
											+"/notification-configuration",
											body=json.dumps(config))
		resp = req.send_request()

		if resp.status != 204:
			raise Exception("could not set notifications", resp)

	def get_notifications(self):
		"""
            Gets the notification topic and events for the vault
            
			:return: Parsed answer from Amazon Glacier
			:rtype: dictionary
        """
		req = self.connection.make_request(	"GET",
											"/-/vaults/"+self.name
											+"/notification-configuration")
		resp = req.send_request()
	
		if resp.status != 200:
			raise Exception("could not get notifications", resp)

		return json.loads(resp.read())

	def delete_notifications(self):
		"""
            Deletes the notification topic and events for the vault
        """
		req = self.connection.make_request(	"DELETE",
											"/-/vaults/"+self.name
											+"/notification-configuration")
		resp = req.send_request()

		if resp.status != 204:
			raise Exception("could not delete notifications", resp)

	# Jobs 

	def initiate_job(self, jtype, description="", archive=None, snstopic=""):
		"""
            Initiates a job executed in the vault
            
			:param jtype: Type of job (``archive-retrieval`` or 
			``inventory-retrieval``)
 			:param description: Description of the job (optional)
			:param archive: An archive instance (required for
			``archive-retrieval``)
			:param snstopic: SNS topic where a notification is sent to on
			completion
			
			:type jtype: string
			:type description: string
			:type archive: string
			:type snstopic: string

			:return: job id
			:rtype: string
        """
		if jtype == "archive-retrieval" and not archive:
			raise Exception("""no archive was passed for job type 
			'archive-retrieval'""")
		
		jobr = { 'Type':jtype }
		if description:
			jobr["Description"] = description
		if snstopic:
			jobr["SNSTopic"] = snstopic
		if jtype == "archive-retrieval":
			jobr["ArchiveId"] = archive.id
		req = self.connection.make_request(	"POST",
											"/-/vaults/"+self.name+"/jobs",
											body=json.dumps(jobr))
		resp = req.send_request()

		if resp.status != 202:
			raise Exception("could not initiate job", resp)

		return resp.getheader("x-amz-job-id")
			
	def describe_job(self, jid):
		"""
            Returns a description of the job by requesting it from 
			Amazon Glacier
            
			:param jid: The job id
			:type jid: string

			:return: Parsed answer from Amazon Glacier
			:rtype: dictionary
        """
		req = self.connection.make_request(	"GET",
											"/-/vaults/"+self.name+"/jobs/"+jid)
		resp = req.send_request()
		if resp.status != 201 or resp.status!=200:
			pass
		else:
			raise Exception("could not describe job", resp)
		return json.loads(resp.read())

	def get_job_output(self, jid, byte_range="-1", output="json"):
		"""
            Gets the job output
            
			:param jid: The job id
			:param byte_range: Byte range to get (optional)
			:type jid: string
			:type byte_range: string

			:return: Parsed answer from Amazon Glacier
			:rtype: dictionary
        """
		header = {}
		if byte_range != "-1":
			header["Range"] = byte_range

		req = self.connection.make_request(	"GET",
											"/-/vaults/"+self.name+"/jobs/"
											+jid+"/output",
											header=header)
		resp = req.send_request()
		
		if resp.status != 200:
			raise Exception("could not get job output", resp)
		if output == 'json':
			return json.loads(resp.read())
		elif output == 'raw':
			return resp.read()
		else:
			raise Exception("invalid output format", output)

	def list_jobs(self):
		"""
            Lists all jobs for this vault

			:return: Parsed answer from Amazon Glacier
			:rtype: dictionary
        """
		req = self.connection.make_request(	"GET",
											"/-/vaults/"+self.name+"/jobs")
		resp = req.send_request()

		if resp.status != 200:
			raise Exception("could not get list jobs", resp)

		return json.loads(resp.read())

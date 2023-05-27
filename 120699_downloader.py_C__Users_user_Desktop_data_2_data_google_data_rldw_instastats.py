# rldw 04/03/15
# https://github.com/rldw
#
# DESCRIPTION:
# class to download images from Instagram
#
# IMPORTANT!
# you have to use your own instagram client id

import sys, requests, json, urllib, shutil, datetime, os

class Downloader:
	def __init__(self, clientid):
		if not clientid:
			print "Error: no instagram client id provided for Downloader class"
			raise SystemExit

		self.clientid     = clientid
		self.postsPerCall = 40


	def getGeoCoordinates(self, location):
		# get lat and lng values from google maps
		location = urllib.pathname2url(location)
		maps_url = 'https://maps.googleapis.com/maps/api/geocode/json?address=' + location
		r = requests.get(maps_url)
		temp = json.dumps(r.json())
		js = json.loads(temp)

		lat = js['results'][0]['geometry']['location']['lat']
		lng = js['results'][0]['geometry']['location']['lng']

		self.lat = lat
		self.lng = lng
		return lat, lng


	def callAPI(self, postsRequested, maxtimestamp=0):
		# sends one or more requests to the instagram API and returns the json
		# returns as many posts as requested (in contrast to callAPIuntilTimestamp)
		# maxtimestamp is a unix timestamp used to set the time point to start
		# the search; 0 means 'start at current time'
		print "##################\n>> CALLING API\n##################\n"

		posts = []
		postCount = 0
		while postCount < postsRequested:
			url = 'https://api.instagram.com/v1/media/search?lat={0}&lng={1}&count={2}&client_id={3}'.format(self.lat,self.lng,self.postsPerCall,self.clientid)

			if maxtimestamp > 0:
				url += '&max_timestamp=' + str(maxtimestamp)

			print 'got {0}/{1} posts, now using URL: .../{2}'.format(len(posts), postsRequested, url.split('/')[-1])

			r = requests.get(url)
			current = json.dumps(r.json())
			current = json.loads(current)
			maxtimestamp = current['data'][-1]['created_time']

			postsInCall = len(current['data'])
			stillNeeded = postsRequested - len(posts)
			if (stillNeeded - postsInCall) < 0:
				posts.extend(current['data'][:stillNeeded])
			else:
				posts.extend(current['data'])

			postCount += postsInCall

		print "got all posts from Instagram API\n\n"
		return posts


	def callAPIuntilTimestamp(self, mintimestamp, maxtimestamp=sys.maxint):
		# sends one or more requests to the instagram API and returns the json
		# returns all posts for the interval [mintimestamp..maxtimestamp]
		# a maxtimestamp of maxint means 'current time'
		print "##################\n>> CALLING API\n##################\n"

		posts        = []
		postCount    = 0
		mintimestamp = int(mintimestamp)

		while mintimestamp < maxtimestamp:
			url = 'https://api.instagram.com/v1/media/search?lat={0}&lng={1}&count={2}&client_id={3}'.format(self.lat,self.lng,self.postsPerCall,self.clientid)

			if maxtimestamp < sys.maxint:
				url += '&max_timestamp=' + str(maxtimestamp)
				datestring = datetime.datetime.fromtimestamp(maxtimestamp)
			else:
				datestring = 'today'

			print 'got {0} posts until {1}, now using URL: .../{2}'.format(len(posts), datestring, url.split('/')[-1])

			r = requests.get(url)
			current = json.dumps(r.json())
			current = json.loads(current)
			maxtimestamp = int(current['data'][-1]['created_time'])

			if mintimestamp < maxtimestamp:
				# add all posts
				posts.extend(current['data'])
			else:
				# only add posts till mintimestamp is reached
				for post in current['data']:
					maxtimestamp = int(post['created_time'])
					if mintimestamp < maxtimestamp:
						posts.append(post)
					else:
						break

		print "got all posts from Instagram API\n\n"
		return posts


	def getImageURLsAndTimestamps(self, posts):
		# extracts img urls and timestamps from array of posts
		output = []
		for post in posts:
			imageURL  = post['images']['standard_resolution']['url']
			timestamp = post['created_time']
			output.append([imageURL, timestamp])
		return output


	def downloadImage(self, url, filename):
		# downloads an image from url and saves it to filename
		# returns True is download was successful
		r = requests.get(url, stream=True)
		if r.status_code == 200:
			with open(filename, 'wb') as f:
				r.raw.decode_content = True
				shutil.copyfileobj(r.raw, f)
				return True
		else:
			print "Bad status code for: " + filename
			return False


if __name__ == "__main__":
	# !!!
	# enter client id here for test runs
	# !!!
	clientid = ''

	outdir    	 = 'test/'
	location  	 = 'east lansing,mi'
	numberOfImgs = 50

	if not os.path.exists(outdir):
		os.makedirs(outdir)

	client = Downloader(clientid)
	client.getGeoCoordinates(location)
	posts = client.callAPI(numberOfImgs)
	posts = client.getImageURLsAndTimestamps(posts)

	print "\n##################\n>> DOWNLOADING IMG\n##################\n"

	for i in range(len(posts)):
		url   = posts[i][0]
		stamp = posts[i][1]
		filename = outdir + stamp + "_" + url.split('/')[-1]
		if client.downloadImage(url, filename):
			print ">> downloaded img {0} of {1} {2}".format(i+1, len(posts), filename)
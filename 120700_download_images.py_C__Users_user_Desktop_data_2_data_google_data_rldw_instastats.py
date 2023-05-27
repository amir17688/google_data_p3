# rldw 04/03/15
# https://github.com/rldw
#
# IMPORTANT!
# you have to use your own instagram client id
#
# USAGE:
# python download_images.py
# -r flag: retrieve images in date range
# -n flag (default): retrieve given number of images

import downloader, argparse, time, os, datetime
clientid = ''

# parse command line arguments
parser = argparse.ArgumentParser(description='Downloads images from Instagram. Use your own API cliend it!')
parser.add_argument('-r','--range', action='store_true',
	help='download images in date range')
parser.add_argument('-n','--number', action='store_true',
	help='download given number of images')
args = parser.parse_args()

if args.range:
	mode = 'range'
else:
	mode = 'number'


# get input from user
outdir    	 = raw_input('Outdir:   ')
location  	 = raw_input('Location: ')

if outdir[-1] != '/':
	outdir += '/'

if mode == 'range':
	print "Enter dates in dd.mm.yyyy format or 0 for now"
	startdate = raw_input('Start date: ')
	enddate   = raw_input('End date:   ')

	# turn input dates to timestamps
	if enddate == '0':
		endstamp = int(time.time())
	else:
		endstamp = int(time.mktime(datetime.datetime.strptime(enddate, "%d.%m.%Y").timetuple()))

	startstamp  = int(time.mktime(datetime.datetime.strptime(startdate, "%d.%m.%Y").timetuple()))
else:
	numberOfImgs = int(raw_input('Number of images: '))


# create outdir
if not os.path.exists(outdir):
	os.makedirs(outdir)

# get URLs via Downloader class
client = downloader.Downloader(clientid)
client.getGeoCoordinates(location)

if mode == 'range':
	posts = client.callAPIuntilTimestamp(startstamp, endstamp)
else:
	posts = client.callAPI(numberOfImgs)

posts = client.getImageURLsAndTimestamps(posts)


# download images
print "\n##################\n>> DOWNLOADING IMG\n##################\n"

for i in range(len(posts)):
	url   = posts[i][0]
	stamp = posts[i][1]
	filename = outdir + stamp + "_" + url.split('/')[-1]
	if client.downloadImage(url, filename):
		print ">> downloaded img {0} of {1} {2}".format(i+1, len(posts), filename)


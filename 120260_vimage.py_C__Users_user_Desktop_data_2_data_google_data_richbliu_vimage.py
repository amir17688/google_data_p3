#!/usr/bin/env python

import SimpleCV as cv

def main():
  cam = cv.Camera(0)
  disp = cv.Display()

  while disp.isNotDone():

    # exit if you ctrl-click
    if disp.mouseLeft:
      print 'Bye bye!'
      break

    img = cam.getImage()

    # get just the yellow channel (ppears as greyscale)
    img = img.colorDistance(cv.Color.YELLOW)

    # flip it (white <> black)
    # img = img.invert()

    img *= 1.5

    # get the blobs (can customize the threshholds)
    blobs = img.findBlobs()

    # sort blobs by size
    blobs.sort(key=lambda b: -b.mArea)

    # draw the biggest one
    blobs[0].draw()

    # draw to display
    print 'about to display image'
    img.save(disp)

if __name__ == '__main__':
  main()
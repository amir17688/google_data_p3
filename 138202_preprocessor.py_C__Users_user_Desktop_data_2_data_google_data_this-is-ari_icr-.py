'''
###################################################################################################
Title: ICR Preprocessor
Purpose: Prepare an image of a single hand written character for OCR recognition by applying OpenCV-based filters
Initial version written by: Hasan SHEIKH FARIDUL / Ari Shomair
v0.1 - 5 Mar 2013----

Usage: 
----------
>python preprocessor.py -o original.png-d ~path_for_output\filename.png

Input:
----------
image = An scan image of a single handwritten character

Output:
----------
result.png = a post-processed image which is better suited for the needs of the OCR engine

Dependencies: 
Python 2.7
OpenCV2
scipy
numpy
math
zhangsuen python module

################################################################################################### 
'''

import cv2
from sys import argv
from scipy import stats
import numpy as np
import sys
import os
import math
import argparse
import zhangsuen

# border removal by inpainting
def border_removal(box_bw,top,bottom,right,left):    
    box_bw[0:top,:]=255   # first "top"  number of rows
    box_bw[-bottom:,]=255 # last "bottom" number of rows
    box_bw[:,0:left]=255  # first "left" number of columns
    box_bw[:,-right:]=255 # last "right" number of columns
    # last two rows a[-2:,]
    return box_bw

def remove_line(box_bw,line_thickness):
    edges = cv2.Canny(box_bw, 80, 120)

    # dilate: it will fill holes between line segments 
    (r,c)=np.shape(box_bw)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS,(1,1))
    edges=cv2.dilate(edges,element)
    min=np.minimum(r,c)
    lines = cv2.HoughLinesP(edges, 1, math.pi/2, 2, None, min*0.75, 1);
        
    r_low_lim=r*0.1
    r_high_lim=r-r_low_lim

    c_low_lim=c*0.1
    c_high_lim=c-c_low_lim

    if lines!=None:
        for line in lines[0]:
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])                 
            theta_radian2 = np.arctan2(line[2]-line[0],line[3]-line[1]) #calculating the slope and the result returned in radian!
            theta_deg2 = (180/math.pi)*theta_radian2 # converting radian into degrees!
            if (theta_deg2>85 and theta_deg2<95): # horizontal line                
                # if starting of line is below or above 30% of box, remove it
                if (line[1]<=r_low_lim or line[1]>=r_high_lim) and (line[3]<=r_low_lim or line[3]>=r_high_lim):
                    cv2.line(box_bw, pt1, pt2, 255, line_thickness)        
            if(theta_deg2>175 and theta_deg2<185):# vertical line
                if (line[0]<=c_low_lim or line[0]>=c_high_lim) and (line[2]<=c_low_lim or line[2]>=c_high_lim):
                    cv2.line(box_bw, pt1, pt2, 255, line_thickness)                    
    return box_bw

# Function that will do the main job
def preprocessor(original, destination, noise_removal,remove_border_size):
    original_image = cv2.imread(original, cv2.CV_LOAD_IMAGE_GRAYSCALE)    #reading captured (scanned image)
    if original_image==None:
        print 'original image file = ',original,'  cant be read!!! Check File name.'
        return_value=None
        return return_value
    else:
        print 'original file = ',original,'  is read'
    

    #image thresholding to make binary image of the box
    (thresh, box_bw) = cv2.threshold(original_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    #border removal
    top=remove_border_size
    bottom=remove_border_size
    right=remove_border_size
    left=remove_border_size
    box_bw_border_free=border_removal(box_bw,top,bottom,right,left)

    # MEDIAN FILTERING : (e.g. Salt and pepper type noise will be removed) 
    if noise_removal.startswith('Y') or noise_removal.startswith('y'):
        box_bw_border_free=cv2.medianBlur(box_bw_border_free,3)

    # auto-crop out whitespace
    (thresh, In_bw) = cv2.threshold(box_bw_border_free,128, 255, cv2.THRESH_BINARY) # thresholding
    inverted_In_bw=np.invert(In_bw) # inverted so that black becomes white and white becomes black since we will check for nonzero values
    (i,j)=np.nonzero(inverted_In_bw) # finding indexes of nonzero values
    if np.size(i)!=0: # in case the box contains no BLACK pixel(i.e. the box is empty such as checkbox)
        Out_cropped = box_bw_border_free[np.min(i):np.max(i),np.min(j):np.max(j)] # row column operation to extract the non
    else: # no need to do cropping since its an empty box
         Out_cropped = box_bw_border_free

    #------RESIZE-------
    # uses 8x8 neighborhood to interpolate
    width = 35
    height =  35
    Ithin_resized=cv2.resize(Out_cropped,(width,height),None,0,0,cv2.INTER_LANCZOS4) 

    #-------PRE-THIN THRESHOLDING----------
    #image thresholding to make binary image of the thinned image
    (thresh, Ithin_resized_thresh) = cv2.threshold(Ithin_resized,200, 255, cv2.THRESH_BINARY)
    # for debugging
    #cv2.imwrite(fname_box+'.Ithin_resized_thresh.png', Ithin_resized_thresh)

    #-------ZHANG-SUEN-THINNING------------
    box_bw_thinned=zhangsuen.thin(Ithin_resized_thresh, False, False, False) 
    # For debugging
    #cv2.imwrite(fname_box+'.box-bw-thinned-no-erosion.png', box_bw_thinned)

    #------ADD SPACING BORDER---------------------------
    # To create space for line expansion via erosion
    border_width = 0.10 # as a % of the total image dimensions
    box_bw_thinned_bordered = cv2.copyMakeBorder(box_bw_thinned, int(height*border_width), int(height*border_width), int(width*border_width), int(width*border_width), cv2.BORDER_CONSTANT, value=255)  

    #-----------EROSION--------------------------
    #apply some erosion to join the gaps
    struc_element = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
    Output=cv2.erode(box_bw_thinned_bordered,struc_element)

    cv2.imwrite(destination,Output) # writing the box in a file.
    
if __name__ == '__main__':
        
    # Argument Parsing starts........................................................................
    parser = argparse.ArgumentParser()    
    parser.add_argument('-o', action='store', dest='original', help='Original File Name',required=True)
    parser.add_argument('-d', action='store', dest='destination', help='Destination File Name',required=True)
    parser.add_argument('-n', action='store', dest='noise_removal', help='noise remove?(Y/N)',default='Y',required=False)
    parser.add_argument('-b', action='store', dest='remove_border_size', help='border removal size in pixel',default=5,required=False)
    results = parser.parse_args() 
    # Argument Parsing ENDS........................................................................

    print 'Original Image =', results.original
    print 'Destination Image =', results.destination
    print 'noise remove?= ', results.noise_removal
    print 'Border removal size= ', results.remove_border_size

    # we will write the extracted boxes in the following directory
    #directory='boxes'
    print results.destination+'!!!\n'
    #if not os.path.exists(os.path.dirname(results.destinaton)):
    #    os.makedirs(os.path.dirname(results.destinaton))

    # calling the function that does the job!
    preprocessor(results.original,results.destination,results.noise_removal,int(results.remove_border_size))
'''
Created on 29.05.2017

@author: Michael Scharf
@email: mitschen@gmail.com
'''

#imports
import sys
import os
import math

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from moviepy.editor import VideoFileClip
from IPython.display import HTML
import numpy as np
import cv2

class LaneFinder(object):
    def __init__(self, mpimage):
        self.img = mpimage;
        self.laneImg = mpimage
        self.imgDepth = None
    
    def show(self):
        plt.imshow(self.img)
        plt.show()
        
    def convertToGrayScale(self):
        self.laneImg = cv2.cvtColor(self.img, cv2.COLOR_RGB2GRAY)
        self.imgDepth = 'gray'
        
    def stripViewport(self):
        mask = np.zeros_like(self.laneImg)
        xsize = mask.shape[1]
        ysize = mask.shape[0]
        polyPtr = np.array(
            [ 
                [[xsize / 100 * 4, ysize], [xsize / 100 * 46, ysize /10*6],
                 [xsize / 100 * 54, ysize/10*6], [xsize / 100 * 96, ysize]
                ]
            ], dtype=np.int32)
        cv2.fillPoly(mask, polyPtr, 255)
        self.laneImg = cv2.bitwise_and(self.laneImg, mask)  
        
    def applyCannyEdgeDetection(self):
        # Define a kernel size and apply Gaussian smoothing
        kernel_size = 5
        blur_gray = cv2.GaussianBlur(self.laneImg,(kernel_size, kernel_size),0)
        # Define our parameters for Canny and apply
        low_threshold = 50
        high_threshold = 150
        self.laneImg = cv2.Canny(blur_gray, low_threshold, high_threshold)
        
    def __applyAngleFiltering(self, lines):
        angle = 35
        threshold = 15
        
        lowerThresh = math.radians(angle-threshold)
        upperThresh = math.radians(angle+threshold ) 
        resultingLines = []
        for line in lines:
            for x1, y1, x2, y2 in line:
                alpha = math.fabs(math.atan((y2-y1)/(x2-x1)))
                if(lowerThresh <= alpha and alpha <= upperThresh):
                    resultingLines.append( [x1, y1, x2, y2] )
        return np.array(resultingLines).reshape(-1,1,4)
    
    def __mapStretchesOnVector(self, lines):
        m1 = []
        m2 = []
        b1 = []
        b2 = []
        for line in lines:
            for x1, y1, x2, y2 in line:
                m = (y2-y1)/(x2-x1)
                print (m)
                if m<0:
                    m1.append(m)
                    b1.append(y1-m*x1)
                else:
                    m2.append(m)
                    b2.append(y1-m*x1)
        #chosen the median instead of average to be more
        #safe against spikes
        m1 = np.median(m1)
        m2 = np.median(m2)
        b1 = np.median(b1)
        b2 = np.median(b2)
        #make sure that we do not report invalid data
        lines = []
        ysize = self.img.shape[0]
        if(not np.isnan(m1)):
            lines.append( [(ysize-b1)/m1, ysize, (ysize/10*6-b1)/m1, ysize/10*6] )
        else:
            print("KACKE", m1)
        if( not np.isnan(m2)):
            lines.append([(ysize-b2)/m2, ysize, (ysize/10*6-b2)/m2, ysize/10*6])
        else:
            print("KACKE", m2)
            
        #bring it into format    
        lines = np.array(lines, dtype=np.int32).reshape(-1,1,4);
        
        return lines
        
    def applyHughTransformation(self):
        rho = 2 # distance resolution in pixels of the Hough grid
        theta = 1 * np.pi/180 # angular resolution in radians of the Hough grid
        threshold = 15     # minimum number of votes (intersections in Hough grid cell)
        min_line_length = 20 #minimum number of pixels making up a line
        max_line_gap = 20    # maximum gap in pixels between connectable line segments
        
        lines = cv2.HoughLinesP(self.laneImg, rho, theta, threshold, np.array([]),
                            min_line_length, max_line_gap)
        
        lines = self.__applyAngleFiltering(lines)
        lines = self.__mapStretchesOnVector(lines)
        #copy the 
        lineSpace = np.zeros_like(self.laneImg)#np.copy(self.img)*0
        for line in lines:
            for x1,y1,x2,y2 in line:
                cv2.line(lineSpace,(x1,y1),(x2,y2),(255,0,0),8)
        self.laneImg = lineSpace

    def highlightLanes(self):
        colorLineSpace = np.dstack((self.laneImg, self.laneImg*0, self.laneImg*0)) 
        self.img = cv2.addWeighted(self.img, 0.8, colorLineSpace, 1.0, 0)                 
        
        
        
    #static create
    def createFromImage(str_path):
        img = mpimg.imread(str_path)
        return LaneFinder(img)
    def findLanes(image):
        finder = LaneFinder(image)
        finder.convertToGrayScale()
        finder.applyCannyEdgeDetection()
        finder.stripViewport()
        #contains a angle based filtering 
        #as well as a mapping from all line-stretches to a single line
        finder.applyHughTransformation()
        finder.highlightLanes()
        return finder.img

    #declaration of statics
    createFromImage = staticmethod(createFromImage)
    findLanes = staticmethod(findLanes)

if __name__ == '__main__':

    #for movies    
#     for filename in os.listdir(str(os.getcwd() + "/../test_videos/")):
#         if filename.endswith(".mp4"):
#             output = (os.getcwd() + "/../test_video_result/"+filename)
#             input =  (os.getcwd() + "/../test_videos/"+filename)
#             test_clip = VideoFileClip(input)
#             prevLane = []
#             test_clip2 = test_clip.fl_image(lambda x: LaneFinder.findLanes(x))
#             test_clip2.write_videofile(output, audio=False)
#     
    #for image processing
    imageDir = str(os.getcwd()) + "/../test_images"
    for filename in os.listdir(imageDir):
        if filename.endswith(".jpg"):
#             fqp = str(os.getcwd()) + '/../test_images/solidWhiteRight.jpg'
            fqp = imageDir + "/" + filename
            plt.imshow(LaneFinder.findLanes(mpimg.imread(fqp)))
            plt.show()
         
    

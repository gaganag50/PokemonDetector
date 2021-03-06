from skimage import exposure
import numpy as np
import argparse
import imutils
import cv2
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-q", "--query", required = True,
	help = "Path to the query image")
args = vars(ap.parse_args())

image = cv2.imread(args['query'])
ratio = image.shape[0] / 300.0
orig = image.copy()
image = imutils.resize(image, height = 300)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.bilateralFilter(gray, 11, 17, 17)
edged = cv2.Canny(gray, 30, 200)

cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
screenCnt = None
for cnt in cnts:
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.01*peri, True)
    print(len(approx))
    if(len(approx) == 4):
        screenCnt = approx
        break

pts = screenCnt.reshape(4, 2)
rect = np.zeros((4, 2), dtype = "float32")

s = pts.sum(axis = 1)
rect[0] = pts[np.argmin(s)]
rect[2] = pts[np.argmax(s)]

diff = np.diff(pts, axis = 1)
rect[1] = pts[np.argmin(diff)]
rect[3] = pts[np.argmax(diff)]

rect *= ratio

(tl,tr,br,bl) = rect
widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
# ...and now for the height of our new image
heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

maxWidth = max(int(widthA), int(widthB))
maxHeight = max(int(heightA), int(heightB))
# construct our destination points which will be used to
# map the screen to a top-down, "birds eye" view
dst = np.array([
	[0, 0],
	[maxWidth - 1, 0],
	[maxWidth - 1, maxHeight - 1],
	[0, maxHeight - 1]], dtype = "float32")

M = cv2.getPerspectiveTransform(rect, dst)

warp = cv2.warpPerspective(orig,M,(maxWidth,maxHeight))

warp = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)

warp = exposure.rescale_intensity(warp)
(h,w) = warp.shape
(dX, dY) = (int(w*0.4), int(h*0.45))

crop = warp[10:dY, w - dX:w - 10]
# save the cropped image to file
cv2.imwrite("cropped.png", crop)
# cv2.imshow("warp", imutils.resize(warp, height = 300))
cv2.imshow("crop", imutils.resize(crop, height = 300))
cv2.waitKey(0) & 0xFF == 'q'
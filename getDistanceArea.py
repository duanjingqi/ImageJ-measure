import os
import glob
import math
import time
from ij import IJ, WindowManager, ImagePlus
from ij.gui import PointRoi, GenericDialog
from ij.plugin.frame import RoiManager
from ij.measure import Measurements, ResultsTable
    
# glob var
imagepath = "E:\data\YG0_class"
imageprefix = "class"
imagesuffix = ".tiff"
pixelsize = float(698.74/(2048*0.64444))
result = "YG0_class_measurement.csv"

def ImageLoader(imagepath,prefix,suffix):
    """Create an iterator to load image."""
    imagewildcard = prefix + '*' + suffix
    return glob.iglob(os.path.join(imagepath, imagewildcard))

def PolygonToPoints(polygonroi):
    """Collect the coordinates of a Polygon in a dictionary."""
    Xpoints = polygonroi.getPolygon().xpoints
    Ypoints = polygonroi.getPolygon().ypoints
    if len(Xpoints) != len(Ypoints): 
        raise Exception("Polygon is not correct!")
    PointDict = {}
    for i in range(len(Xpoints)):
        pointname = 'Point%02d' % (i+1)
        coordinate = (Xpoints[i], Ypoints[i])
        PointDict[pointname] = coordinate
    return PointDict

def GetConsecutivePair(alist):
    """Compute the consecutive distance"""
    ConsecutivePair = []
    # Add the tail-head pair first
    ConsecutivePair.append((alist[-1],alist[0]))
    # Loop throught the list
    for i in range(len(alist)-1):
        if (alist[i],alist[i+1]) not in ConsecutivePair: 
            ConsecutivePair.append((alist[i],alist[i+1]))

    return ConsecutivePair

def GetNonConsecutivePair(alist):
    """Compute the nonconsecutive distance"""
    consecutivelist = GetConsecutivePair(alist)
    # Duplicate the alist
    copylist = alist
    # Loop through the list
    NonConsecutiveDist = [] 
    for x in alist: 
        for y in copylist: 
            if x == y: 
                continue
            elif (x,y) in consecutivelist: 
                continue
            elif (y,x) in consecutivelist:
                continue
            elif (y,x) in NonConsecutiveDist:
                continue
            else:
                NonConsecutiveDist.append((x,y))

    return NonConsecutiveDist

def PolygonArea(imp, polygon): 
    """Measure the area of the polygon on the image."""
    ip = imp.getProcessor()
    ip.setRoi(polygon)
    istats = ip.getStatistics()
    return istats.area

def ResizeCanvas(imp,): 
    """Resize the image canvas to facilitate processing."""
    from ij.plugin import CanvasResizer
    
    ip = imp.getProcessor()
    bigip = CanvasResizer().expandImage(ip, ip.getWidth(), ip.getHeight + 100, 0, 0)
    ImagePlus("resized", bigip).show()

def CsvOutput(resultfile, adict):
    """Write the results to a local file."""
    if adict is not None: 
        data = "{},{},{},{}\n".format(adict['type'],adict['Image Name'],adict['Label'],adict['Value'])
        resultfile.write(data)
    else:
        print "Error: data empty!"

def main():
    # 1. I/O
    images = ImageLoader(imagepath, imageprefix, imagesuffix)
    resultfile = open(os.path.join(imagepath, result), 'w')
    columnFlag = {'type':'Type','Image Name':'Image Name','Label':'Label','Value':'Value'}
    CsvOutput(resultfile, columnFlag)
    # Process image
    for image in images: 
        # Open image in ImageJ
        imp = IJ.openImage(image)
        imp.show()
        imagename = imp.getTitle()
        # Set scale
        IJ.run("Set Scale...", "distance=1 known=%f unit=nm" % pixelsize)
        # Create a polygon Roi by using mouse and set a checker for the Roi created.
        rm = RoiManager()
        roins = rm.getInstance()
        while not roins.getRoisAsArray():
            time.sleep(1)
        # Check if a polygon
        polygon= roins.getRoisAsArray()[0] # [0] because I just have one polygon object
        if polygon.getType() != 2: 
            raise Exception("Not a Polygon!")
        # Save the roi.zip
        zipname = imagename.split(".")[0] + ".zip"
        roizip = os.path.join(imagepath, zipname)
        roins.runCommand("save selected", roizip)
        # The number of MBP ball
        number = polygon.getNCoordinates()
        ballNumber = {'type': 'ball', 'Image Name': imagename, 'Label': 'Ball Count', 'Value': number}
        CsvOutput(resultfile,ballNumber)
        # Measure the area of the polygon
        area = PolygonArea(imp, polygon)
        polygonArea = {'type': 'area', 'Image Name': imagename, 'Label': 'Polygon'}
        polygonArea['Value'] = area
        CsvOutput(resultfile, polygonArea)
        # Create point dictionary
        pointdict = PolygonToPoints(polygon)
        pointlist = [key for key in pointdict.keys()]
        pointlist.sort()
        # Measure the consecutive distance
        consecutivepair = GetConsecutivePair(pointlist)
        for pointA,pointB in consecutivepair: 
            consecutiveDist = {'type': 'line', 'Image Name': imagename}
            label = 'Consecutive: ' + pointA + '-' + pointB
            consecutiveDist['Label'] = label
            dx = abs(int(pointdict[pointA][0]) - int(pointdict[pointB][0]))
            dy = abs(int(pointdict[pointA][1]) - int(pointdict[pointB][1]))
            distance = math.sqrt(dx*dx + dy*dy) * pixelsize
            consecutiveDist['Value'] = distance
            CsvOutput(resultfile, consecutiveDist)
        # Measure the nonconsecutive distance
        nonconsecutivepair = GetNonConsecutivePair(pointlist)
        for pointA,pointB in nonconsecutivepair: 
            nonconsecutiveDist = {'type': 'line', 'Image Name': imagename}
            label = 'Nonconsecutive: ' + pointA + '-' + pointB
            nonconsecutiveDist['Label'] = label
            dx = abs(int(pointdict[pointA][0]) - int(pointdict[pointB][0]))
            dy = abs(int(pointdict[pointA][1]) - int(pointdict[pointB][1]))
            distance = math.sqrt(dx*dx + dy*dy) * pixelsize
            nonconsecutiveDist['Value'] = distance
            CsvOutput(resultfile, nonconsecutiveDist)
        # Close the image and the polygon roi
        roins.runCommand('reset')
        imp.close()
    resultfile.close()

main()
#----EOF----

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
imageprefix = "YG0_class"
imagesuffix = ".tif"
pixelsize = float(698.74/2048)

def imageloader(imagepath,prefix,suffix):
    """Create an iterator to load image."""
    imagewildcard = prefix + '*' + suffix
    return glob.iglob(os.path.join(imagepath, imagewildcard))

def roipoints(roi):
    """Collect the point coordinates contained in the Roi."""
    points = roi.getContainedPoints()
    coordinates = {"PointCount": len(points)}
    for i in range(len(points)):
        name = "point%02d" %(i+1)
        coordinate = (points[i].getX(), points[i].getY())
        coordinates[name] = coordinate
    return coordinates

def roiferets(roi):
    """Return the Feret values in a dictionary."""
    feretdict = {}
#    if roi.getTypeAsString() != "Traced": 
#        raise Exception("Roi type error! A traced contour is required here.")
    ferets = roi.getFeretValues()
    feretdict["Feret"] = ferets[0]      # Feret's diameter
    feretdict["FeretAngle"] = ferets[1] # Feret's angle
    feretdict["MinFeret"] = ferets[2]   # Feret's min value
    feretdict["FeretX"] = ferets[3]     # 
    feretdict["FeretY"] = ferets[4]     #
    return feretdict

def roiareas(imp, roi): 
    """Return the area values in a dictionary."""
    areadict = {}
#    if roi.getTypeAsString() != "Traced": 
#        raise Exception("Roi type error! A traced contour is required here.")
    ip = imp.getProcessor()
    ip.setRoi(roi)
    istats = ip.getStatistics()
    areadict["Area"] = istats.area
    areadict["Centroid"] = (istats.xCentroid, istats.yCentroid)
    areadict["CenterOfMass"] = (istats.xCenterOfMass, istats.yCenterOfMass)
    return areadict

def distance(tuple1, tuple2): 
    """Measure the distance between two points."""
    dx = abs(float(tuple1[0] - tuple2[0]))
    dy = abs(float(tuple1[1] - tuple2[1]))
    distance = math.sqrt(dx*dx + dy*dy) * pixelsize
    return distance

def angle(ori, tuple1, tuple2): 
    """Measure the angle of ori as the ventice in the triangle formed by ori, tuple1 and tuple2."""
    a = distance(ori, tuple1)       # Side 1
    b = distance(ori, tuple2)       # Side 2
    c = distance(tuple1, tuple2)    # The side opposite to the angle
    alpha = math.degrees(math.acos((a*a + b*b - c*c)/(2*a*b)))
    return alpha

def consecutivepair(iterable):
    """Generate a iterator producing 2 consecutive items from iterable."""
    from itertools import tee, izip
    iterable.sort()
    iterable.append(iterable[0])
    v, w = tee(iterable)
    next(w, None)
    return izip(v, w)
    
def main():

    images = imageloader(imagepath, imageprefix, imagesuffix)
    for image in images: 
        # I/O
        imp = IJ.openImage(image)
        measure = {}
        measure["Name"] = imp.getTitle()
        measure["PixelSize"] = pixelsize

        # Check if csv file exist
        csvfile = measure["Name"].split(".")[0] + ".csv"
        if not os.path.isfile(os.path.join(imagepath,csvfile)):
            imp.show()
        
            # Set scale
            IJ.run("Set Scale...", "distance=1 known=%f unit=nm" % pixelsize)
    
            # Zoom in
            # This does not work, only produces a enlarged black picture. 
            #IJ.run("Set...", "zoom=400 x=0 y=0") 
    
            # Create Rois manually 
            rm = RoiManager()
            ROIinstance = rm.getInstance()
            while ROIinstance.getCount() < 2:    # Wait until all rois become ready
#                print "Waiting for Rois to be completed..."
                time.sleep(1)
            rois = ROIinstance.getRoisAsArray()
    
            # Check if point and traced rois in rois
            roitypes = [roi.getTypeAsString() for roi in rois]
#            if "Point" not in roitypes and \
#               "Traced" not in roitypes: 
#                raise Exception("Error: point and traced rois are missing!")
    
            # Save the Rois created
            zipname = measure["Name"].split(".")[0] + ".zip"
            roizip = os.path.join(imagepath, zipname)
            ROIinstance.runCommand("Deselect")
            ROIinstance.runCommand("save", roizip)
    
            # Collect info from Roi instances
            for roi in rois: 
                if roi.getTypeAsString() == "Point":    # Point Roi
                    points = roipoints(roi)
                else:                                   # Contour Roi
                    measure.update(roiferets(roi))
                    measure.update(roiareas(imp, roi))           

            # Check if Center of Mass is there
            if measure.has_key("CenterOfMass"):
                ori = measure["CenterOfMass"]   # Center of Mass 
            else: 
                raise Exception("Error: No CenterOfMass in the Traced Roi.")
    
            # Measure the distance from the CenterOfMass to each point
            pointslist = points.keys()
            pointslist.remove('PointCount')
            for point in pointslist:
                pointDist = distance(ori, points[point])
                measure["ori-"+point] = pointDist
    
            # Measure the angle of Point01-Ori-Point02
            for pointA, pointB in consecutivepair(pointslist): 
                angleName = "%s-Ori-%s" %(pointA, pointB)
                degree = angle(ori, points[pointA], points[pointB])
                measure[angleName] = degree
    
            # Write out
            filename = measure["Name"].split(".")[0] + ".csv"   # The Name of output file
            outputfile = open(os.path.join(imagepath, filename), 'a') 
            outputfile.write('{}\t{}\n'.format('PointCount', points['PointCount']))
            for label, value in measure.items(): 
                outputfile.write('{}\t{}\n'.format(label, str(value)))
            outputfile.close()
    
            # Close the image and the Rois
            ROIinstance.runCommand('reset')
            imp.close()

main()
#----EOF----

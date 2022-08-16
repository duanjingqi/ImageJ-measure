import os
import sys
import csv
import io
import math
import glob
import re
import SIFT_Align as SA
from    ij  import IJ
from    ij  import WindowManager as WM 
from    ij  import ImagePlus as IP
from    ij.gui          import      GenericDialog   as GD
from    ij.plugin.frame import      RoiManager      as RM
from    ij.gui          import      ShapeRoi
from    ij.process      import      ImageConverter  as IC

def GetRawMeta(imgpath) : 
    """ Parse image OME-XML metadata """
    from loci.formats import ImageReader
    from loci.formats import MetadataTools

    reader = ImageReader()
    OMEMeta = MetadataTools.createOMEXMLMetadata()
    reader.setMetadataStore(OMEMeta)
    reader.setId(imgpath)
    metadict = {}
    metadict['ImageCount']  =   int(OMEMeta.getImageCount())
    metadict['PixelSize']   =   float(OMEMeta.getPixelsPhysicalSizeX(0).value())
    metadict['PixelSizeUnit']   =   OMEMeta.getPixelsPhysicalSizeX(0).unit().getSymbol()
    metadict['ChannelCount']    =   int(OMEMeta.getChannelCount(0))

    return metadict

def ImageBioFormatsImporter(imgpath) : 
    """ Import raw data with Bio-formats plugin """
    from loci.plugins import BF
    from loci.plugins.in import ImporterOptions as IO

    opt = IO()
    opt.setOpenAllSeries(True)  # Open all series
    opt.setColorMode(IO.COLOR_MODE_COLORIZED)   # Open as colorized
    opt.setShowOMEXML(False)
    opt.setStitchTiles(False)
    opt.setId(imgpath)
    opt.setSplitChannels(True)  # Split channel
    images = BF.openImagePlus(opt)

    return images

def GetLutColor(imp) : 
    """ Get color from image object """
    s = imp.getLuts()[0].toString()
    f = re.search('rgb\[255\]=(\w+)', s)
    if f is not None : 
        color = f.groups()[0]
    else : 
        color = None
    
    return color 

def AreRoisOverlapped(roi1, roi2) : 
    """Check if roi1 and roi2 are overlapped"""
    if len(roi1.containedPoints) >= len(roi2.containedPoints) :
        broi, sroi = roi1, roi2
    else :
        broi, sroi = roi2, roi1
    for pt in sroi.containedPoints :
        if broi.containsPoint(pt.x, pt.y) :
            rslt = True
            break
    else :
        rslt = False
    return rslt

def SeekCsvDialect(fn) :
    """Seek dialect in the file and return the dialect"""
    first100lns = [ln for i, ln in enumerate(io.open(fn, 'r', newline='')) if i < 100]
    dlist = []
    offset = 0
    for ln in first100lns :
        dialect = csv.Sniffer().sniff(ln)
        dlist.append((offset, dialect))
        offset += len(ln)
    target = dlist[-1][1].delimiter
    for offset, dialect in dlist : 
        if dialect.delimiter == target : 
            break 
    return dialect, offset


def main() : 

    # Input images
    gui = GD('Input immunofluorescence images')
    gui.addMessage('Select images')
    gui.addDirectoryField('Image directory : ', os.environ['HOME'], 25)
    gui.addChoice('Image type : ', ['tif', 'tiff', 'czi'], 'czi')
    gui.addStringField('Project title', 'image')
    gui.showDialog() 
    if gui.wasOKed():
        imgdir = gui.getNextString()
        project = gui.getNextString()
        suffix = gui.getChoices().lastElement().getSelectedItem()
    fndict = {} 
    for path, directory, files in os.walk(imgdir) : 
        for fn in files : 
            if fn.endswith(suffix) : 
                fndict[fn] = os.path.join(path, fn)

    # Start process images
    print "%d images will be processed" % len(fndict)

    for fn, fnpath in fndict.items() : 
        
        print "Processing image %s..." % fn

        # Retrieve OME-XML Metadata
        imgmeta = GetRawMeta(fnpath)

        # Import image. If image stack, perform alignment and z-objection
        images = ImageBioFormatsImporter(fnpath)
        imgmeta['Images'] = {}
        for img in images :
            if img.getStackSize() == 1 : 

                if GetLutColor(img) == 'red' : 
                    imgmeta['Images']['Mitochondria'] = img
                elif GetLutColor(img) == 'blue' : 
                    imgmeta['Images']['Dapi'] = img
                elif GetLutColor(img) == 'green' : 
                    imgmeta['Images']['Flag'] = img
                else : 
                    imgmeta['Images']['Unknown'] = img

            else : 
                idang 


        print dir(images[0])
        print images[0].getStackSize()
        print images.getStackSize()

        
        # Define cell boundary
#        IC(imgmeta['Images']['Dapi']).convertToGray8()
#        imgmeta['Images']['Dapi'].show()

## Co-localization analysis
#rm = RoiManager.getInstance()
#rm.runCommand('Reset')
#rm.runCommand('Open', PathToMitoRois)
#mito_list = [roi for roi in rm.getRoisAsArray()]
#rm.runCommand('Reset')
#rm.runCommand('Open', PathToFlagRois)
#flag_list = [roi for roi in rm.getRoisAsArray()]
#rm.runCommand('Reset')
#mito_dict = {}
#flag_dict = dict.fromkeys([roi.getName() for roi in flag_list], None)
#for mitoroi in mito_list : 
#    k = ''.join(mitoroi.getName().split())
#    vlist = []
#    for flagroi in flag_list : 
#        flaglabel = flagroi.getName()
#        if AreRoisOverlapped(mitoroi, flagroi) : 
#            vlist.append(flaglabel)
#            flag_list.remove(flagroi)
#    mito_dict[k] = vlist
#for k, vlist in mito_dict.items() : 
#    for flaglabel in vlist : 
#        flag_dict[flaglabel] = k
#
## Write out
#mitomeasurement = []
#dial, offset = SeekCsvDialect(PathToMitoCSV)
#mitomeasurementfieldnames = []
#with io.open(PathToMitoCSV, 'r', newline='') as mitocsv : 
#    mitocsv.seek(offset)
#    csv.register_dialect('local', dial)
#    dictreader = csv.DictReader(mitocsv, dialect='local')
#    mitomeasurementfieldnames = [name for name in dictreader.fieldnames]
#    for row in dictreader : 
#        k = ''.join(row['Mito #'].split())
#        row.update(ColocalizedRois = len(mito_dict[k]))
#        mitomeasurement.append(row)
#mitomeasurementfieldnames.append('ColocalizedRois')
#
#flagmeasurement = []
#dial, offset = SeekCsvDialect(PathToFlagCSV)
#flagmeasurementfieldnames = []
#with io.open(PathToFlagCSV, 'r', newline='') as flagcsv : 
#    flagcsv.seek(offset)
#    csv.register_dialect('local', dial)
#    dictreader = csv.DictReader(flagcsv, dialect='local')
#    flagmeasurementfieldnames = [name for name in dictreader.fieldnames]
#    for row in dictreader : 
#        row.update(ColocalizedMito = flag_dict[row['Label']])
#        flagmeasurement.append(row)
#flagmeasurementfieldnames.append('ColocalizedMito')
#
#newmitocsvname = os.path.splitext(PathToMitoCSV)[0] + '_proc.csv'
#with open(newmitocsvname, 'w') as out : 
#    writer = csv.DictWriter(out, fieldnames=mitomeasurementfieldnames, dialect='excel')
#    writer.writeheader()
#    for mito in mitomeasurement : 
#        writer.writerow(mito)
#
#newflagcsvname = os.path.splitext(PathToFlagCSV)[0] + '_proc.csv'
#with open(newflagcsvname, 'w') as out : 
#    writer = csv.DictWriter(out, fieldnames=flagmeasurementfieldnames, dialect='excel')
#    writer.writeheader()
#    for flag in flagmeasurement : 
#        writer.writerow(flag)
#print 'All complete! Hope you get a nice result.'
#print '~~~ greeting from Jingqi ~~~'


if __name__ == '__main__' : 
    main()

###----EOF----

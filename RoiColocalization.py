import os, sys, csv, io
from ij import IJ
from ij.gui import ShapeRoi
from fiji.util.gui import GenericDialogPlus
from ij.plugin.frame import RoiManager

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
    D = ','
    with io.open(fn, 'r', newline='') as infile :
        ln = infile.readline()
        dialect = csv.Sniffer().sniff(ln)
        offset = 0
        row = 0
        while dialect.delimiter != D : 
            lastD = dialect.delimiter
            offset += len(ln)
            row += 1
            ln = infile.readline()
            dialect = csv.Sniffer().sniff(ln)
    return dialect, offset

# I/O
workpath = IJ.getImage().getOriginalFileInfo().directory
gui = GenericDialogPlus("Images and Rois")
gui.addMessage("Please define the images to be analyzed and their Roi objects")
gui.addImageChoice("Image1", "Mitochondria tracker")
gui.addFileField("Rois1", workpath, 25)
gui.addFileField("Measurement CSV1", workpath, 25)
gui.addImageChoice("Image2", "Flag signal")
gui.addFileField("Rois2", workpath, 25)
gui.addFileField("Measurement CSV2", workpath, 25)
gui.showDialog() 

if gui.wasOKed():

    ImgMito = gui.getNextImage()
    ImgFlag = gui.getNextImage()
    PathToMitoRois = gui.getNextString()
    PathToMitoCSV = gui.getNextString()
    PathToFlagRois = gui.getNextString()
    PathToFlagCSV = gui.getNextString()

# Co-localization analysis
rm = RoiManager.getInstance()
rm.runCommand('Reset')
rm.runCommand('Open', PathToMitoRois)
mito_list = [roi for roi in rm.getRoisAsArray()]
rm.runCommand('Reset')
rm.runCommand('Open', PathToFlagRois)
flag_list = [roi for roi in rm.getRoisAsArray()]
rm.runCommand('Reset')
mito_dict = {}
flag_dict = dict.fromkeys([roi.getName() for roi in flag_list], None)
for mitoroi in mito_list : 
    k = ''.join(mitoroi.getName().split())
    vlist = []
    for flagroi in flag_list : 
        flaglabel = flagroi.getName()
        if AreRoisOverlapped(mitoroi, flagroi) : 
            vlist.append(flaglabel)
            flag_list.remove(flagroi)
    mito_dict[k] = vlist
for k, vlist in mito_dict.items() : 
    for flaglabel in vlist : 
        flag_dict[flaglabel] = k

# Write out
mitomeasurement = []
dial, offset = SeekCsvDialect(PathToMitoCSV)
mitomeasurementfieldnames = []
with io.open(PathToMitoCSV, 'r', newline='') as mitocsv : 
    mitocsv.seek(offset)
    csv.register_dialect('local', dial)
    dictreader = csv.DictReader(mitocsv, dialect='local')
    mitomeasurementfieldnames = [name for name in dictreader.fieldnames]
    for row in dictreader : 
        k = ''.join(row['Mito #'].split())
        row.update(ColocalizedRois = len(mito_dict[k]))
        mitomeasurement.append(row)
mitomeasurementfieldnames.append('ColocalizedRois')

flagmeasurement = []
dial, offset = SeekCsvDialect(PathToFlagCSV)
flagmeasurementfieldnames = []
with io.open(PathToFlagCSV, 'r', newline='') as flagcsv : 
    flagcsv.seek(offset)
    csv.register_dialect('local', dial)
    dictreader = csv.DictReader(flagcsv, dialect='local')
    flagmeasurementfieldnames = [name for name in dictreader.fieldnames]
    for row in dictreader : 
        row.update(ColocalizedMito = flag_dict[row['Label']])
        flagmeasurement.append(row)
flagmeasurementfieldnames.append('ColocalizedMito')

newmitocsvname = os.path.splitext(PathToMitoCSV)[0] + '_proc.csv'
with open(newmitocsvname, 'w') as out : 
    writer = csv.DictWriter(out, fieldnames=mitomeasurementfieldnames, dialect='excel')
    writer.writeheader()
    for mito in mitomeasurement : 
        writer.writerow(mito)

newflagcsvname = os.path.splitext(PathToFlagCSV)[0] + '_proc.csv'
with open(newflagcsvname, 'w') as out : 
    writer = csv.DictWriter(out, fieldnames=flagmeasurementfieldnames, dialect='excel')
    writer.writeheader()
    for flag in flagmeasurement : 
        writer.writerow(flag)
print 'All complete! Hope you get a nice result.'
print '~~~ greeting from Jingqi ~~~'
##----EOF----

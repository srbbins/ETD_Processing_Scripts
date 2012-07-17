import sys
import os.path
import time
from pdfminer.processETDs import *
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor, TagExtractor2Memory
from pdfminer.converter import TextConverter, XMLConverter
from pdfminer.layout import LAParams

def makeOutfileName():
    timeID=str(time.time())
    name="C:\\Users\\srobbins\\Desktop\\taggedScriptOutput"+timeID+".txt"
    return name
    
def getPDFDir(directory, outfile, thisTrainingData):
    count=0
    misscount=0
    
    for filename in os.listdir(directory):
        if filename.endswith('.pdf') or filename.endswith('.PDF'):
            filepath=directory+'\\'+filename
            result=getPDFInfo(filepath, outfile, thisTrainingData)
    return 


def getPDFInfo(filename, outfile, thisTrainingData):
    # Open a PDF file. SR: add some assignments to use textconverter
    fp = open(filename, 'rb')
    #outfp=file(outfile, 'a')
    #outfp=sys.stdout#use this to print to screen instead of file 
    codec = 'utf-8'
    laparams = LAParams()
    # Create a PDF parser object associated with the file object.
    parser = PDFParser(fp)
    # Create a PDF document object that stores the document structure.
    doc = PDFDocument()
    # Connect the parser and document objects.
    parser.set_document(doc)
    doc.set_parser(parser)
    # Supply the password for initialization.
    # (If no password is set, give an empty string.)
    doc.initialize('')
    # Check if the document allows text extraction. If not, abort.
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    # Create a PDF resource manager object that stores shared resources.
    rsrcmgr = PDFResourceManager()
    # Create a PDF device object.
    # device = PDFDevice(rsrcmgr)
    # SR: I overrode this in hopes that I could use the text
    #device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams)
    device = TagExtractor2Memory(rsrcmgr, codec=codec)
    #device = XMLConverter(rsrcmgr, outfp, codec=codec, laparams=laparams, outdir="C:\\Users\\srobbins\\Desktop\\")
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.
    #outfp.write(filename[-11:-4]+"\n")
    #print filename[-11:-4]+"\n"#uncomment for testing
    
    PDFInfo=''
    for i,page in enumerate(doc.get_pages()):
        #added this line as test
        PDFInfo+=interpreter.process_page_to_mem(page)
        if i==2:
            deptInfo=thisTrainingData.processETDStrings(PDFInfo)
            #outfp.write(deptInfo+'\n')
            #for testing purposes: instead of writing to file, uncomment following line:
            #print deptInfo+'\n'
            fileDict[filename[-11:-4]]=deptInfo
            return
    
    


fileDict={}

outfile=makeOutfileName()
thisTrainingData=TrainingData()
count=getPDFDir(r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro3\Illinois_3_2", outfile, thisTrainingData)
print fileDict
print thisTrainingData.trainingDataDict
fileDict=thisTrainingData.cleanTrainingData(fileDict)
print fileDict

#iteractionTwo=
IterationTwo=metadataFinder(thisTrainingData, r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro3\Illinois_3_2", fileDict)
IterationTwo.checkForAlternateString('doctor of education', 'education')
fileDict=IterationTwo.testString()
print IterationTwo.fileDict
count=0.0
missCount=0.0
for key in fileDict.keys():
    count+=1.0
    if fileDict[key]=="no match":
         missCount+=1.0

print missCount/count 

print IterationTwo.trainingDataDict


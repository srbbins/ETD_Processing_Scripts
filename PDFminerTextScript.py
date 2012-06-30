import sys
import os.path
import time
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams




def makeOutfileName():
    timeID=str(time.time())
    name="C:\\Users\\srobbins\\Desktop\\textScriptOutput"+timeID+".txt"
    return name
    
def getPDFDir(directory, outfile):
    for filename in os.listdir(directory):
        if filename.endswith('.pdf') or filename.endswith('.PDF'):
            filepath=directory+'\\'+filename
            print filename[:-4]
            getPDFInfo(filepath, outfile)
    return

def getPDFInfo(filename, outfile):
    # Open a PDF file. SR: add some assignments to use textconverter
    #fp = open('C:/Users/SDR/Desktop/pdfMiner/pdfminer-20110515/samples/0001388.pdf', 'rb')
    fp = open(filename, 'rb')
    outfp=open(outfile, 'a')
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
    device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams)
    #device = TagExtractor(rsrcmgr, outfp, codec=codec)
    #device = xmlConverter(rsrcmgr, outfp, codec=codec, laparams=laparams, outdir=outdir)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.
    for i,page in enumerate(doc.get_pages()):
        #added this line as test
        if i==1:
            outfp.write(filename[-11:-4]+'\n')
            interpreter.process_page(page)
            #PDFInfo=page
            
            return 

outfile=makeOutfileName()
getPDFDir(r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro1\Illinois_1_2", outfile)


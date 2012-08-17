import csv
import os
import sys
from xml.etree import ElementTree
Etree = None

##file=open(inFileName, 'r')
##reader=csv.DictReader(file)
##for i, row in enumerate(reader):
##    if i==1:
##        print row
##    if row['department name'] not in frequencies.keys():
##        frequencies[row['department name']]=1
##    else:
##        frequencies[row['department name']]+=1
##outFile=open(r"C:\Users\srobbins\Desktop\test.txt", 'w')


def add_one_field(parent, dcField, text):
    """Add a person element to the parent node.

    Give the new element an id attribute and name and interest
    sub-elements.
    """
    tagPlusAttr=dcField.split('.')
    node = Etree.SubElement(parent, 'dcvalue')
    node.set('element', tagPlusAttr[0])
    if len(tagPlusAttr)==2:
        node.set('qualifier', tagPlusAttr[1])
    else:
        node.set('qualifier', 'none')
    node.text=text
    return node

def makeOutFileName(outFileDir, i, name):
    name=outFileDir+name+"_"+str(i)+".xml"
    return name

def add_dc_nodes(root, row):
    """Add several sub-elements to the root element.
    """
    file1=open(r"C:\Users\srobbins\Desktop\MARC2DC_table.csv", 'r')
    lookup=csv.DictReader(file1)
    for theLine in lookup:
        line=theLine
    for key in row.keys():
        if key in line.keys():
            if line[key][:2]=='dc':
                if row[key]!=' ' and row[key]!='' and row[key]!=None:
                    add_one_field(root, line[key][3:], row[key])
        
def add_thesis_nodes(root, row):
    """Add several sub-elements to the root element.
    """
    file1=open(r"C:\Users\srobbins\Desktop\MARC2DC_table.csv", 'r')
    lookup=csv.DictReader(file1)
    for theLine in lookup:
        line=theLine
    for key in row.keys():
        if key in line.keys():
            if line[key][:6]=='thesis':
                if row[key]!=' ' and row[key]!='' and row[key]!=None:
                    add_one_field(root, line[key][7:], row[key])

def test(inFileName, outFileDir):
    global Etree
    Etree = ElementTree
    file=open(inFileName, 'r')
    reader=csv.DictReader(file)
    for i, row in enumerate(reader):
        dcOutFileName=makeOutFileName(outFileDir, i, 'dublin_core')
        thesisOutFileName=makeOutFileName(outFileDir, i, 'metadata_thesis')
        dcRoot=Etree.Element("dublin_core")
        thesisRoot=Etree.Element("dublin_core")
        dcDoc=Etree.ElementTree(dcRoot)
        dcRoot.set('schema', 'dc')
        thesisDoc=Etree.ElementTree(thesisRoot)
        thesisRoot.set('schema', 'thesis')
        add_dc_nodes(dcRoot, row)
        add_thesis_nodes(thesisRoot, row)
        dcDoc.write(dcOutFileName)
        thesisDoc.write(thesisOutFileName)
        if i==10:
            break

def showNode(node):
    if node.nodeType == Node.ELEMENT_NODE:
        print 'Element name: %s' % node.nodeName
        for (name, value) in node.attributes.items():
            print '    Attr -- Name: %s  Value: %s' % (name, value)
        if node.attributes.get('ID') is not None:
            print '    ID: %s' % node.attributes.get('ID').value

def main():
    args = sys.argv[1:]
    if len(args) != 2:
        print 'usage: python test.py infile.csv outfile.xml'
        sys.exit(-1)
    inFileName = args[0]
    outFileName = args[1]
    if inFileName == outFileName:
        print 'error: in-file and out-file names must be different'
        sys.exit(-1)
##    if os.path.exists(outFileName):
##        print 'error: out-file already exists'
##        sys.exit(-1)
    test(inFileName, outFileName)

if __name__ == '__main__':
    main()





def buildIdString(elements):
    #for operations where IdString has been decomposed into a list, this function
    #rebuilds the IdString
    idString=''
    for i, val in enumerate(elements):
        idString+=val
        if i!=(len(elements))-1:
            idString+='-'
    return idString
            
def getFieldInfo(line, index, oldIdString):
    #scrapes marc field info from xml attributes and
    #returns it as either string of form tag-ind1-ind2-seq, tag-ind1-ind2-code-seq
    #or, if just the tag attribute in present the string will
    #only be the tag. If element is from the 'leader' field, tag will be '000'.
    #Seq disambiguates multiple entries.
    elements=[]
    if line[index:index+6]=='leader' and line[index-6]!='/':
        #check for 'leader'
        elements.append('000')
    elif line[index:index+3]=='tag':
        #check for 'tag'
        elements.append(line[index+5:index+8])
        if line[index+10:index+14]=='ind1':
            #if 'tag' found, check for inds
            elements.append(line[index+16:index+17])
            elements.append(line[index+25:index+26])
            if line[index+34:index+42]=='subfield':
                elements.append(line[index+49:index+50])
            else:
                elemtents.append(' ')
            elements.append('0')
    else:
        return oldIdString
    idString=buildIdString(elements)
    return idString
            
def checkCode(line, index, oldIdString):
##if a code element is detected, checks to see if code in current IdString
##matches. If not returns new id string identical to old but with new code.
    if line[index:index+4]=='code':
        oldIdList=oldIdString.split('-')
        if oldIdList[3]!=line[index+6]:
            oldIdList[3]=line[index+6]
        newIdString=buildIdString(oldIdList)
        return newIdString
    return oldIdString

def incrementSeq(oldIdString, xmlDict):
    #increments the seq part of the string
    seqCount=0
    for idString in xmlDict.keys():
        #get current number of identical ids
        if len(idString)==len(oldIdString) and idString[:9]==oldIdString[:9]:
            seqCount+=1
    idList=oldIdString.split('-')
    idList[len(idList)-1]=str(seqCount)
    newIdString=buildIdString(idList)
    return newIdString

def buildDictList(readFile):
    #Builds a list of dictionarys for processing MarcXML.
    #Each individual record becomes a dictionary on the list.
    #Each XML element's content will be mapped to a list containing
    #information contained in the "tag", "ind1," "ind2," and "code"
    #attributes of the datafield and subfield tags, as well as a fifth field to
    #identify multiple entries.
    #Assumes readfile is a valid MarcXML file. 

    readFile=open(readFile, 'r')
    xmlDict={}
    dictList=[]
    for line in readFile:
        writeChar = False
        idString=''
        for i, char in enumerate(line):
            #process one character at a time
            if char=='<':
                if writeChar==True:
                    if idString in xmlDict.keys():
                        oldIdString=idString
                        idString=incrementSeq(oldIdString, xmlDict)
                    xmlDict[idString]=contentVar
                    contentVar=''
                #uses brackets to identify content and tag
                writeChar=False
                if line[i+1:i+13]=='/marc:record':
                #end of record write dictionary to list
                   dictList.append(xmlDict)
                   xmlDict={}
            if writeChar==False:
                if char=='l' or char=='t':
                    newIdString=getFieldInfo(line, i, idString)
                    if newIdString!=idString:
                        idString=newIdString
                        contentVar=''
                elif char=='c':
                    newIdString=checkCode(line, i, idString)
                    if newIdString!=idString:
                        idString=newIdString
                        contentVar=''
            elif writeChar==True and char!='\n':
                contentVar+=char
            if char=='>' and line[i+1]!=('<' or '\n'):
                writeChar=True
    return dictList


def buildHeader(dictList):
    #build header for csv (as list). Header is also used to guide
    #the construction of individual lines.
    header=[]
    for dict in dictList:
        for idString in dict.keys():
            if idString not in header:
                header.append(idString)
    header.sort()
    return header

def buildLines(header, dictList):
    #build lines (excepting the header) to be written to csv and return as a
    #two dimensional array of rows.  
    csvLines=[]
    for dict in dictList:
        rowList=[]
        for idString in header:
            if idString in dict.keys():
                rowList.append(dict[idString])
            else:
                rowList.append(' ')
        csvLines.append(rowList)
##    for line in csvLines:
##        print line
    return csvLines
                

def writeCsvFile(writeFile, csvLines, header):
    #writes csv file
    writeFile=open(writeFile, 'w')
    for i, word in enumerate(header):
        if i==0:
            writeFile.write('"'+word+'","')
        elif i==(len(header)-1):
            writeFile.write(word+'"\n')
        else:
            writeFile.write(word+'","')
    for line in csvLines:
        for i, word in enumerate(line):
            if i==0:
                writeFile.write('"'+word+'","')
            elif i==(len(line)-1):
                writeFile.write(word+'"\n')
            else:
                writeFile.write(word+'","')
            
    

def main():
    #marcData=buildDictList('/home/seth/Desktop/Illinois_Retro1_MARCDATA.xml')
    marcData=buildDictList('C:\Users\srobbins\Desktop\Illinois_Retro3_MARCDATA.xml')
    header=buildHeader(marcData)
    lines=buildLines(header, marcData)
    #writeCsvFile('/home/seth/Desktop/Illinois_Retro1_test_MARCDATA.csv', lines, header)
    writeCsvFile('C:\Users\srobbins\Desktop\Illinois_Retro3_MARCDATA.csv', lines, header)
    

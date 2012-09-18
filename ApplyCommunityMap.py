import sys
import os.path
import csv

def addInfo(outFile):
    mapFile=open(r'C:\Users\srobbins\Desktop\OutPut\ETDmap.csv', 'r')
    outFile=open(outFile, 'r')
    mapDict=csv.DictReader(mapFile)
    fileDict=csv.DictReader(outFile)        
    testOutput=open(r'C:\Users\srobbins\Desktop\OutPut\mapTest.csv', 'w')
    fieldnames=fileDict.fieldnames
    fieldnames.append("collection")
    fieldnames.append("notes")
    print fieldnames
    testDict=csv.DictWriter(testOutput, fieldnames)
    testDict.writeheader()
    for fileRow in fileDict:
        mapFile.seek(0)
        for mapRow in mapDict:
            length=len(fileRow['department name'])
            print mapRow['Discipline']
            if fileRow['department name']==mapRow['Total Records: 3584'][:length]:
                fileRow['collection']=mapRow['Collection Handle']
                print fileRow['collection']+"="+mapRow['Collection Handle']
                fileRow['notes']=mapRow['Notes']
                print "writing "+str(fileRow)
                testDict.writerow(fileRow)

    
    
    
    


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print 'usage: python test.py outfile.xml'
        sys.exit(-1)
    outFileName = args[0]
##    if os.path.exists(outFileName):
##        print 'error: out-file already exists'
##        sys.exit(-1)
    addInfo(outFileName)

if __name__ == '__main__':
    main()

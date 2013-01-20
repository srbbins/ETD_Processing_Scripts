import csv
import sys
import os.path

class MarcTable:
    
    def __init__(self, fileName):
        if fileName[-3:].lower()=="csv":
            self.table=self.makeCsvDict(fileName)
            
            
    def makeCsvDict(self, fileName):
        mapFile=open(fileName, 'rb')
        mapDict=csv.DictReader(mapFile)
        csvList=[]
        for row in mapDict:
            rowDict={}
            for i in mapDict.fieldnames:
                rowDict[i]=row[i]
            csvList.append(rowDict)
        return csvList 
            

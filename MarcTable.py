import csv
import sys
import os.path

class marcTable:
    
    def __init__(self, fileName):
        if fileName[-3:].lower()=csv:
            self.table=makeCsvDict(fileName)
            
            
    def makeCsvDict():
        mapFile=open(r'C:\Users\srobbins\Desktop\OutPut\Illinois_Retro1_MARCDATA.csv', 'rb')
        mapDict=csv.DictReader(mapFile)
        csvList=[]
        for row in mapDict:
            rowDict={}
            for i in mapDict.fieldnames:
                rowDict[i]=row[i]
            csvList.append(rowDict)
            

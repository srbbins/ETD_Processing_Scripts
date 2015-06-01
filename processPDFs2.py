import sys
import os.path
import time
import math
import subprocess
import etd_string_utils

PDFMINER_DIR = "/Users/srobbins/Projects/pdfminer"
PDFMINER_SCRIPT = os.path.join(PDFMINER_DIR, "tools", "pdf2txt.py")

class ProcessETDs(object):
    def __init__(self, directory):
        self.toolBox=etd_string_utils
        self.fileDict={}
        self.trainingDataDict={}
        self.filePath=directory
        self.seedFileDict(directory, seedText='no match')

##    def __init__(self, directory, fileDict, trainingDataDict):#supply premade data for test
##        self.toolbox=StringUtils()
##        self.fileDict=fileDict
##        self.trainingDataDict=TrainingDataDict

    def seedFileDict(self, directory, seedText):
        for filename in os.listdir(directory):
            if filename.endswith('.pdf') or filename.endswith('.PDF'):
                filepath=directory+'/'+filename
                self.fileDict[filename[:-4]]=seedText            
        return 

    def getPDFInfo(self, filename, pageCount=10):
        return subprocess.check_output([PDFMINER_SCRIPT, "-m "+str(pageCount), filename])
        
                
    def getPDFInfoForFile(self):
        print self.filePath
        print self.fileDict.keys()[0]
    	return self.getPDFInfo(os.path.join(self.filePath, self.fileDict.keys()[0]+'.pdf'))
        

    def getTextBetweenTwoStrings(self, beginString, endString, seedText, tolerance=2):#retrieves text between first instance of two strings. Strings do not have to be exact but are matched with a tolerance (based on levenshtein distance)
        tokenCountForBeginString=len(beginString.split())
        tokenCountForEndString=len(endString.split())
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText or seedText==False:
                #print 'testing'+fileKey
                PDFText=self.getPDFInfo(self.filePath+'/'+fileKey+'.pdf')
                tokenList=PDFText.split()
                writeToken=False
                for i, token in enumerate(tokenList):
                    if i+tokenCountForBeginString<len(tokenList) and writeToken==False:
                        testString=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForBeginString]).strip()
                        if self.toolBox.getEditDistance(testString.lower(), beginString.lower())<=tolerance:
                            markOne=i+tokenCountForBeginString
                            writeToken=True
                    if writeToken==True and i>markOne and i+tokenCountForEndString<len(tokenList):
                        endStringTest=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForEndString]).strip()
                        if self.toolBox.getEditDistance(endStringTest.lower(), endString.lower())<=tolerance: 
                            markTwo=i
                            workingTokens=[]
                            workingTokenList=tokenList[markOne:markTwo]
                            for token in workingTokenList:
                                workingTokens.append(token.lower())
                            self.fileDict[fileKey]=self.toolBox.detokenizeString(workingTokens)
                            if self.fileDict[fileKey]!=seedText:
                                if self.fileDict[fileKey] in self.trainingDataDict.keys():
                                    self.trainingDataDict[self.fileDict[fileKey]]+=1
                                else:
                                    self.trainingDataDict[self.fileDict[fileKey]]=1
                            print fileKey+' is '+self.fileDict[fileKey]
                            break

    def checkForAlternateString(self, alternateString, explicitMeaning, seedText='no match', tolerance = 3):#seeks a string that gives away department info and assigns that department name to file.
        print alternateString
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText:
                PDFText=self.getPDFInfo(self.filePath+'/'+fileKey+'.pdf')
                tokenCountForAlternate=len(alternateString.split())
                tokenList=PDFText.split()
                for i, token in enumerate(PDFText):
                    if i+tokenCountForAlternate<len(tokenList):#test for end of PDFtext
                        testString=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForAlternate]).strip()
                        if self.toolBox.getEditDistance(testString.lower(), alternateString.lower())<=tolerance:
                            markOne=i+tokenCountForAlternate
                            self.fileDict[fileKey]=explicitMeaning
                            print fileKey+': '+self.fileDict[fileKey]

    def cleanTrainingData(self, seedText):#cleans fileDict and trainingDataDict; a number of these steps could usefully be factored out.
        for entry in self.trainingDataDict.keys():
            if len(entry.split())>4 and self.trainingDataDict[entry]<2:
                for key in self.trainingDataDict.keys():
                    if self.toolBox.getEditDistance(key, entry[:len(key)])<2:
                        self.trainingDataDict[key]+=self.trainingDataDict[entry]
                        
                        for fileKey in self.fileDict.keys():
                            if self.fileDict[fileKey]==entry:
                               self.fileDict[fileKey]=key 
                        break
                for fileKey in self.fileDict.keys():   
                    if self.fileDict[fileKey]==entry:
                        newEntry=entry.split()
                        newEntryList=[]
                        for i in range(5):
                            newEntryList.append(newEntry[i])
                        self.fileDict[fileKey]=self.toolBox.detokenizeString(newEntryList) 
                del self.trainingDataDict[entry]
                
        for unlikelyKey in self.trainingDataDict.keys():
            if self.trainingDataDict[unlikelyKey]==1:
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.toolBox.getEditDistance(unlikelyKey, likelyKey)
                    if self.trainingDataDict[likelyKey]>1 and distance<=3:
                       candidateDict[likelyKey]=distance
                print 'unlikely key is '+unlikelyKey+'. Candidates are '+str(candidateDict)
                if candidateDict!={}:
                    print 'likely key is '+min(candidateDict, key=candidateDict.get)
                    self.trainingDataDict[min(candidateDict, key=candidateDict.get)]+=1
                    del self.trainingDataDict[unlikelyKey]
        for entry in self.trainingDataDict.keys():
            newTokenList=[]
            for token in entry.split():
                if token.isalpha():
                    newTokenList.append(token)
            #print 'entry is '+entry+'. tokenlist is '+str(newTokenList)
            if newTokenList!=[]:
                newEntry=self.toolBox.detokenizeString(newTokenList)
                if newEntry!=entry:
                    print 'newEntry: '+ newEntry + ' does not equal entry: ' + entry
                    if newEntry not in self.trainingDataDict.keys():
                        self.trainingDataDict[newEntry]=0
                    for key in self.fileDict.keys():
                        if self.fileDict[key]==entry:
                            self.fileDict[key]=newEntry
                            self.trainingDataDict[newEntry]+=1
                            print key + ' changed from ' + entry + ' to ' + newEntry
                    del self.trainingDataDict[entry]
            else:
                del self.trainingDataDict[entry]
        #print str(self.trainingDataDict) + '\n'
        for key in self.fileDict.keys():
            if self.fileDict[key] not in self.trainingDataDict.keys() and self.fileDict[key]!=seedText:
                print self.fileDict[key]+'not found'
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.toolBox.getEditDistance(self.fileDict[key], likelyKey)
                    if distance<=4:
                        candidateDict[likelyKey]=distance
                print 'candidates:'+ str(candidateDict)+'\n'
                if candidateDict!={}:
                    self.fileDict[key]= min(candidateDict, key=candidateDict.get)
                    print key+': '+self.fileDict[key]
                else:
                    wordList=self.fileDict[key].split()
                    isBadCrop=True
                    for i, word in enumerate(wordList):
                        candidateDict={}
                        for entry in self.trainingDataDict.keys():
                            entryList=entry.split()
                            if len(entryList)<=len(wordList)-i:
                                wordString=self.toolBox.detokenizeString(wordList[i:i+len(entryList)])
                                distance=self.toolBox.getEditDistance(wordString, entry)
                                if distance<=3:
                                        candidateDict[entry]=distance
                        if candidateDict!={}:
                            self.fileDict[key]=min(candidateDict, key=candidateDict.get)
                            self.trainingDataDict[self.fileDict[key]]+=1
                            isbBadCrop=False
                    if isBadCrop==True:
                        self.fileDict[key]=seedText
 
def runModuleDirectMatch(filePath):
    fileData=ProcessETDs(filePath)
    #fileData=testProcessETDs(filePath, testFileDict, testTrainingDataDict)
    #fileText = fileData.getPDFInfoForFile()
    #print fileText
    fileData.getTextBetweenTwoStrings('doctor of philosophy in', 'in', 'no match', 0)
    #print fileData.trainingDataDict
    fileData.checkForAlternateString('doctor of education', 'education', 'no match', 0)
    fileData.checkForAlternateString('doctor of musical arts', 'music', 'no match', 0)
    fileData.checkForAlternateString('doctor of education in music education', 'music education', 'no match', 0)
    fileData.cleanTrainingData('no match')
    #fileData.findTrainingTextBetweenTwoStrings('philosophy in', '</page>', 'no match', 3)

    return fileData
    
def runModuleFuzzy(filePath):
    fileData=ProcessETDs(filePath) 
    fileData.getTextBetweenTwoStrings('doctor of philosophy in', 'in', 'no match', 2)
    fileData.checkForAlternateString('doctor of education', 'education', 'no match', 3)
    fileData.checkForAlternateString('doctor of musical arts', 'music', 'no match', 3)
    fileData.checkForAlternateString('doctor of education in music education', 'music education', 'no match', 3)
    fileData.cleanTrainingData('no match')
    return fileData
    
def getStats(fileData, name):
    fileCount=0.0
    badSeedCount=0.0
    for key in fileData.fileDict.keys():
        fileCount+=1.0
        if fileData.fileDict[key]=='no match':
            badSeedCount+=1.0
    recall=badSeedCount/fileCount
    print "Stats for "+name        
    print "File Count: "+str(fileCount)
    print "No Match Count: "+str(badSeedCount)
    #print fileData.trainingDataDict
    print "fake recall equals: "
    print str(recall)
 
print "now processing 2_4"    
fileDictDirect=runModuleDirectMatch(r"/Volumes/IDEALS-1/IDEALS_ETDS (libgrsurya)/ProQuestDigitization/Illinois_Retro2/Illinois_2_4")
fileDictFuzzy=runModuleFuzzy(r"/Volumes/IDEALS-1/IDEALS_ETDS (libgrsurya)/ProQuestDigitization/Illinois_Retro2/Illinois_2_4")
getStats(fileDictDirect, "Direct Match 2_4")
getStats(fileDictFuzzy, "Fuzzy Match 2_4")
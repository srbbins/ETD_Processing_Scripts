import sys
import os.path
import time
import math
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor, TagExtractor2Memory
from pdfminer.converter import TextConverter, XMLConverter
from pdfminer.layout import LAParams

class ProcessETDs(object):
    def __init__(self, directory):
        self.toolBox=StringUtils()
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
                filepath=directory+'\\'+filename
                self.fileDict[filename[:-4]]=seedText            
        return 

    def getPDFInfo(self, filename, pageCount=10):
        fp = open(filename, 'rb') 
        codec = 'utf-8'
        laparams = LAParams()
        parser = PDFParser(fp)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize('')
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        rsrcmgr = PDFResourceManager()
        device = TagExtractor2Memory(rsrcmgr, codec=codec)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        #outfp.write(filename[-11:-4]+"\n")
        #print filename[-11:-4]+"\n"#uncomment for testing
        PDFInfo=''
        for i,page in enumerate(doc.get_pages()):
            PDFInfo+=interpreter.process_page_to_mem(page)
            if i==pageCount:
                return PDFInfo

    def getTextBetweenTwoStrings(self, beginString, endString, seedText, tolerance=2):#retrieves text between first instance of two strings. Strings do not have to be exact but are matched with a tolerance (based on levenshtein distance)
        tokenCountForBeginString=len(beginString.split())
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText or seedText==False:
                print 'testing'+fileKey
                PDFText=self.getPDFInfo(self.filePath+'\\'+fileKey+'.pdf')
                tokenList=PDFText.split()
                writeToken=False
                for i, token in enumerate(tokenList):
                    if i+tokenCountForBeginString<len(tokenList):
                        testString=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForBeginString]).strip()
                        if self.toolBox.getEditDistance(testString.lower(), beginString.lower())<=tolerance:
                            markOne=i+tokenCountForBeginString
                            writeToken=True
                    if writeToken==True and self.toolBox.getEditDistance(token.lower(), endString.lower())<=tolerance and i>markOne:
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

    def checkForAlternateString(self, alternateString, explicitMeaning, seedText):#seeks a string that gives away department info and assigns that department name to file.
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText:
                PDFText=self.getPDFInfoForTestString(self.filePath+'\\'+fileKey+'.pdf')
                tokenCountForAlternate=len(alternateString.split())
                tokenList=PDFText.split()
                for i, token in enumerate(PDFText):
                    if i+tokenCountForAlternate<len(tokenList):#test for end of PDFtext
                        testString=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForAlternate]).strip()
                        if self.wordCalc.getEditDistance(testString.lower(), alternateString.lower())<=3:
                            markOne=i+tokenCountForAlternate
                            self.fileDict[fileKey]=explicitMeaning
                            print fileKey+': '+self.fileDict[fileKey]

    def cleanTrainingData(self, seedText):#cleans fileDict and trainingDataDict; a number of these steps could usefully be factored out.
        for entry in self.trainingDataDict.keys():
            if not entry[0].isalpha():
                count=self.trainingDataDict[entry]
                del self.trainingDataDict[entry]
                entry=entry[1:]
                if entry in self.trainingDataDict.keys():
                    entry+=count
                else:
                    self.trainingDataDict[entry]=count
            if not entry[-1].isalpha():
                count=self.trainingDataDict[entry]
                del self.trainingDataDict[entry]
                entry=entry[:-1]
                if entry in self.trainingDataDict.keys():
                    self.trainingDataDict[entry]+=count
                else:
                    self.trainingDataDict[entry]=count
            if len(entry.split())>3:
                for key in self.trainingDataDict.keys():
                    if key==entry[:len(key)]:
                        self.trainingDataDict[key]+=self.trainingDataDict[entry]
                        break
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
            print 'entry is '+entry+'. tokenlist is '+str(newTokenList)
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
            if self.fileDict[key] not in self.trainingDataDict.keys() and fileDict[key]!=seedText:
                print self.fileDict[key]+'not found'
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.wordCalc.getEditDistance(fileDict[key], likelyKey)
                    if distance<=4:
                        candidateDict[likelyKey]=distance
                print 'candidates:'+ str(candidateDict)+'\n'
                if candidateDict!={}:
                    self.fileDict[key]= min(candidateDict, key=candidateDict.get)
                    print key+': '+self.fileDict[key]

    def testString(self, seedText):
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText:
                candidates={}
                PDFText=self.getPDFInfoForTestString(self.filePath+'\\'+fileKey+'.pdf')
                PDFTextTokens=PDFText.split()
                for i, word in enumerate(PDFTextTokens):
                    if word not in STOPLIST:
                        for key in self.trainingDataDict.keys():
                            trainingString=key.lower().split()
                            if self.wordCalc.getEditDistance(trainingString[0], word)<=4:
                                wordTest=self.toolBox.detokenizeString(PDFTextTokens[i:i+len(trainingString)])
                                distance=self.wordCalc.getEditDistance(wordTest, key)
                                if distance<=5 and self.trainingDataDict[key]>1:
                                    candidateRankVar=0.0
                                    frequency=0.0
                                    if key in candidates.keys():
                                        frequency+=1.0
                                    candidateRankVar=(math.log(float(self.trainingDataDict[key]))-(math.log(float(i)+1.0)))/(distance+1.0)
                                    candidates[key]=candidateRankVar
                print candidates
                if candidates != {}:
                    maxFrequency=max(candidates, key=candidates.get)
                else: maxFrequency='no match'
                
                self.fileDict[fileKey]=maxFrequency+'(best guess)'
                print fileKey+': '+maxFrequency
                if maxFrequency!='no match':
                    self.trainingDataDict[maxFrequency]+=1   


class testProcessETDs(ProcessETDs):
    def __init__(self, directory, fileDict, trainingDataDict):#supply premade data for test
        self.toolbox=StringUtils()
        self.fileDict=fileDict
        self.trainingDataDict=TrainingDataDict
        

class StringUtils(object):
    
    def detokenizeString(self, tokenList):
        detokenizedString=''
        for i, token in enumerate(tokenList):
                if i==len(tokenList)-1:
                    detokenizedString+=token.lower()
                else:
                    detokenizedString+=token.lower()+' '
        return detokenizedString

    def getEditDistance(self, word1, word2):
        distanceMatrix=[]
        for i in range(len(word1)+1):
            distanceMatrix.append([i])
        for j in range(1,(len(word2))+1):
            distanceMatrix[0].append(j)
        for i in range(1, (len(word1))+1):
            for j in range(1,(len(word2))+1):
                if word1[i-1]==word2[j-1]:
                    cost=0
                else:
                    cost=1
                distanceMatrix[i].append(min((distanceMatrix[i-1][j]+1,
                                              distanceMatrix[i][j-1]+1,
                                              distanceMatrix[i-1][j-1]+cost)))            
        return distanceMatrix[len(word1)][len(word2)]


def runModuleForIdeals(filePath):
    fileData=ProcessETDs(filePath)
    fileData.getTextBetweenTwoStrings('doctor of philosophy in', 'in', 'no match')
    fileData.cleanTrainingData('no match')
    fileData.checkForAlternateString('doctor of education', 'education')
    fileData.checkForAlternateString('doctor of musical arts', 'music')
    print fileData.fileDict
    print fileData.trainingDataDict


runModuleForIdeals(r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro5\Illinois_5_2")    
    
    
    
    

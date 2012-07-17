#!/usr/bin/env python2
import math
import sys
import os.path
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor, TagExtractor2Memory
from pdfminer.converter import TextConverter, XMLConverter
from pdfminer.layout import LAParams
STOPLIST=['item', 'login', 'again', '0', '1', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2', '20', '21', '22', '23',
          '24', '25', '25', '26', '27', '3', '30', '31', '32', '33', '34', '35', '36',
          '37', '38', '39', '4', '40', '41', '42', '43', '44', '45', '46', '47', '48',
          '49', '5', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '6', '60', '61',
          '62', '63', '64', '65', '66', '67', '68', '69', '7', '70', '71', '72', '73',
          '74', '75', '76', '77', '78', '79', '8', '80', '81', '82', '83', '84', '85', '86', '87',
          '89', '9', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', 'a', 'a', 'ab', 'about',
          'above', 'ac', 'according', 'across', 'ads', 'ae', 'af', 'after', 'afterwards', 'against', 'albeit', 'all', 'almost',
          'alone', 'along', 'already', 'also', 'although', 'always', 'among', 'amongst', 'an', 'and', 'another', 'any',
          'anybody', 'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'apart', 'are', 'around', 'as', 'ask', 'asp', 'at',
          'author', 'av', 'available', 'b', 'baf', 'be', 'became', 'because', 'become', 'becomes', 'becoming',
          'been', 'before', 'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 'between',
          'beyond', 'bf', 'biz', 'both', 'but', 'by', 'c', 'ca', 'can', 'cannot', 'canst', 'cd', 'cee', 'certain', 'cf', 'cfm',
          'cfrd', 'cgi', 'choose', 'click', 'cm', 'co', 'com', 'conducted', 'considered', 'contrariwise',
          'cos', 'could', 'crd', 'cu', 'cx', 'cx', 'd', 'date', 'day', 'described', 'describes', 'designed', 'determine', 'determined',
          'dfe', 'different', 'discussed', 'do', 'does', 'doesn\'t', 'doing',
          'dont', 'dost', 'doth', 'double', 'down', 'dr', 'dr', 'dual', 'due', 'during',
          'e', 'each', 'eb', 'ec', 'either', 'else', 'elsewhere',
          'enough', 'et', 'etc', 'eu', 'even', 'ever', 'every', 'everybody',
          'everyone', 'everything', 'everywhere', 'except', 'excepted', 'excepting', 'exception',
          'exclude', 'excluding', 'exclusive', 'f', 'fa', 'fa', 'fae', 'far', 'farther', 'farthest',
          'few', 'ff', 'first', 'for', 'formerly', 'forth',
          'forward', 'found', 'free', 'from', 'front',
          'further', 'furthermore', 'furthest', 'g', 'gcn', 'general', 'get', 'gif', 'given', 'gm', 'go', 'h', 'had',
          'halves', 'hardly', 'has', 'hast', 'hath', 'have', 'he', 'hence', 'henceforth', 'her', 'her', 'here', 'hereabouts',
          'hereafter', 'hereby', 'herein', 'hereto', 'hereupon', 'hers', 'herself', 'him', 'him', 'himself', 'hindmost', 'his', 'hither',
          'hitherto', 'how', 'however', 'howsoever', 'hr', 'i', 'I', 'ie', 'if', 'in', 'inasmuch', 'inc', 'include', 'included', 'including',
          'indeed', 'indoors', 'inside', 'insomuch', 'instead', 'into', 'investigated', 'inward',
          'inwards', 'is', 'it', 'it', 'its', 'itself', 'j', 'jpg', 'just', 'k', 'kg', 'kind',
          'km', 'l', 'la', 'last', 'latter', 'latterly', 'less', 'lest', 'let', 'like', 'little', 'low', 'ltd',
          'm', 'made', 'many', 'may', 'maybe', 'me', 'mean', 'meantime', 'meanwhile', 'might', 'more', 'more',
          'moreover', 'most', 'mostly', 'mr', 'mrs', 'ms', 'much', 'must', 'my', 'myself', 'n', 'namely', 'need',
          'neither', 'net', 'never', 'nevertheless', 'new', 'news', 'next', 'no', 'no', 'nobody', 'none', 'nonetheless',
          'noone', 'nope', 'nor', 'not', 'nothing', 'notwithstanding', 'now', 'nowadays', 'nowhere', 'nu', 'o', 'obtained', 'of',
          'of', 'off', 'often', 'oh', 'ok', 'on', 'once', 'one', 'only', 'onto', 'or',
          'org', 'other', 'others', 'otherwise', 'ought', 'our', 'ours', 'ourselves',
          'out', 'outside', 'over', 'own', 'p', 'page', 'per', 'performance', 'performed',
          'perhaps', 'pl', 'plenty', 'possible', 'post', 'present',
          'presented', 'presents', 'provide', 'provided', 'provides', 'q',
          'quite', 'r', 'rather', 'really', 'related', 'report', 'required',
          'results', 'roll', 'round', 's', 'said', 'sake', 'same', 'sang', 'save', 'saw',
          'say', 'see', 'seeing', 'seem', 'seemed', 'seeming', 'seems', 'seen', 'seldom', 'selected',
          'selves', 'sent', 'several', 'sfrd', 'shalt', 'she', 'should', 'show', 'shown', 'sideways',
          'significant', 'since', 'slept', 'slew', 'slung', 'slunk', 'smote',
          'so', 'some', 'somebody', 'somehow', 'someone', 'something', 'sometime', 'sometimes',
          'somewhat', 'somewhere', 'sort', 'spake', 'spat', 'spoke', 'spoken',
          'sprang', 'sprung', 'srd', 'stave', 'staves', 'still', 'studies', 'such', 'supposing', 't', 'ta',
          'take', 'tested', 'than', 'that', 'the', 'thee', 'their', 'them',
          'themselves', 'then', 'thence', 'thenceforth', 'there', 'thereabout',
          'thereabouts', 'thereafter', 'thereby', 'therefore', 'therein',
          'thereof', 'thereon', 'thereto', 'thereupon', 'these', 'they', 'this', 'this',
          'tho', 'those', 'thou', 'though', 'thrice', 'through', 'throughout', 'thru', 'thus',
          'thy', 'thyself', 'till', 'time', 'to', 'to', 'together', 'too', 'toward', 'towards',
          'try', 'types', 'u', 'unable', 'under', 'underneath', 'unless', 'unlike', 'until', 'up',
          'upon', 'upward', 'upwards', 'us', 'use', 'used', 'using', 'v', 'various', 'very', 'via', 'vol', 'vs', 'w',
          'want', 'was', 'we', 'week', 'well', 'were', 'what', 'whatever',
          'whatsoever', 'when', 'whence', 'whenever', 'whensoever', 'where', 'whereabouts',
          'whereafter', 'whereas', 'whereat', 'whereby', 'wherefore', 'wherefrom',
          'wherein', 'whereinto', 'whereof', 'whereon', 'wheresoever', 'whereto', 'whereunto',
          'whereupon', 'wherever', 'wherewith', 'whether', 'whew', 'which', 'whichever',
          'whichsoever', 'while', 'whilst', 'whither', 'who', 'whoa', 'whoever', 'whole',
          'whom', 'whomever', 'whomsoever', 'whose', 'whosoever', 'why', 'will', 'wilt', 'with',
          'within', 'without', 'worse', 'worst', 'would', 'wow', 'www', 'x', 'y',
          'ye', 'year', 'yet', 'yippee', 'you', 'your', 'yours', 'yourself', 'yourselves', 'z', 'graduate', 'college', 'department', 'submitted', 'advisor', 'doctor']

class TrainingData(object):
    def __init__(self):
        self.trainingDataDict={}
        self.fileDict={}
        self.wordCalc=LevenshteinCalculator()
       
    def detokenizeString(self, tokenList):
        detokenizedString=''
        for i, token in enumerate(tokenList):
                if i==len(tokenList)-1:
                    detokenizedString+=token.lower()
                else:
                    detokenizedString+=token.lower()+' '
        return detokenizedString

    def getTextBetweenTwoStrings(self, tokenList, beginString, endString):#endstring needs to handle more than one token
        tokenCountForBeginString=len(beginString.split())
        writeToken=False
        for i, token in enumerate(tokenList):
            if i+tokenCountForBeginString<len(tokenList):
                testString=self.detokenizeString(tokenList[i:i+tokenCountForBeginString]).strip()
                if self.wordCalc.getEditDistance(testString.lower(), beginString.lower())<=2:
                    markOne=i+tokenCountForBeginString
                    writeToken=True
            if writeToken==True and self.wordCalc.getEditDistance(token.lower(), endString.lower())<=2 and i>markOne:
                markTwo=i
                workingTokens=[]
                workingTokenList=tokenList[markOne:markTwo]
                for token in workingTokenList:
                    workingTokens.append(token.lower())
                return workingTokens
        return ''

    def cleanTrainingData(self, fileDict):
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
        for entry in self.trainingDataDict.keys():
            newTokenList=[]
            for token in entry.split():
                if token.isalpha():
                    newTokenList.append(token)
            if newTokenList!=[]:
                newEntry=self.detokenizeString(newTokenList)
                if newEntry!=entry:
                    print 'newEntry: '+ newEntry + ' does not equal entry: ' + entry
                    if newEntry not in self.trainingDataDict.keys():
                            self.trainingDataDict[newEntry]=0
                    for key in fileDict.keys():
                        if fileDict[key]==entry:
                            fileDict[key]=newEntry
                            self.trainingDataDict[newEntry]+=1
                            print key + ' changed from ' + entry + 'to' + newEntry
                    del self.trainingDataDict[newEntry]
                        
                        
                
                
        for unlikelyKey in self.trainingDataDict.keys():
            if self.trainingDataDict[unlikelyKey]==1:
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.wordCalc.getEditDistance(unlikelyKey, likelyKey)
                    if self.trainingDataDict[likelyKey]>1 and distance<=4:
                       candidateDict[likelyKey]=distance
                if candidateDict!={}:
                    self.trainingDataDict[min(candidateDict, key=candidateDict.get)]+=1
                    del self.trainingDataDict[unlikelyKey]
        #print str(self.trainingDataDict) + '\n'
        for key in fileDict.keys():
            if fileDict[key] not in self.trainingDataDict.keys() and fileDict[key]!='no match':
                print fileDict[key]+'not found'
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.wordCalc.getEditDistance(fileDict[key], likelyKey)
                    if distance<4:
                        candidateDict[likelyKey]=distance
                print 'candidates:'+ str(candidateDict)+'\n'
                if candidateDict!={}:
                    fileDict[key]= min(candidateDict, key=candidateDict.get)
                    print key+': '+fileDict[key]
        return fileDict
                    
                    
    #if number of tokens greater than five try to match first words to other word in dict
    #if string contains undesireable characters try to match to dict, if characters occur at ends of tokens simply kick them out

    def addToDataModel(self, workingTokens):
        if workingTokens!='no match':
            if workingTokens in self.trainingDataDict.keys():
                self.trainingDataDict[workingTokens]+=1
            else:
                self.trainingDataDict[workingTokens]=1
        return
        
    def processETDStrings(self, text):
        tokens=text.split()
        workingTokens=self.detokenizeString(self.getTextBetweenTwoStrings(tokens, "doctor of philosophy in", "in"))
        if workingTokens=='':
            workingTokens='no match'
        self.addToDataModel(workingTokens)
        return workingTokens

class FileDictionary(object):
    def __init__(self, fileDict):
        fileDict=self.fileDict

    def cleanFileDictionary(self, cleanTrainingData):pass
        
        
    

class metadataFinder(object):
    def __init__(self, someTrainingData, filePath, fileDict):
        self.trainingDataDict=someTrainingData.trainingDataDict
        self.filePath=filePath
        self.fileDict=fileDict
        self.wordCalc=LevenshteinCalculator()
        self.toolBox=StringUtils()

    def getPDFInfoForTestString(self, filename):
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
        print filename[-11:-4]+"\n"#uncomment for testing
        PDFInfo=''
        for i,page in enumerate(doc.get_pages()):
            PDFInfo+=interpreter.process_page_to_mem(page)
            if i==10:
                return PDFInfo

    def checkForAlternateString(self, alternateString, explicitMeaning):
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]=='no match':
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
        

    
    def testString(self):
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]=='no match':
                candidates={}
                PDFText=self.getPDFInfoForTestString(self.filePath+'\\'+fileKey+'.pdf')
                PDFTextTokens=PDFText.split()
                for i, word in enumerate(PDFTextTokens):
                    if word not in STOPLIST:
                        for key in self.trainingDataDict.keys():
                            trainingString=key.lower().split()
                            if self.wordCalc.getEditDistance(trainingString[0], word)<=5:
                                wordTest=self.toolBox.detokenizeString(PDFTextTokens[i:i+len(trainingString)])
                                distance=self.wordCalc.getEditDistance(wordTest, key)
                                if distance<=6 and self.trainingDataDict[key]>1:
                                    candidateRankVar=0.0
                                    frequency=0.0
                                    if key in candidates.keys():
                                        frequency+=1.0
                                    candidateRankVar=(frequency*math.log(float(self.trainingDataDict[key])))/(distance+1.0)
                                    candidates[key]=candidateRankVar
                print candidates
                if candidates != {}:
                    maxFrequency=max(candidates, key=candidates.get)
                else: maxFrequency='no match'
                
                self.fileDict[fileKey]=maxFrequency+'(best guess)'
                print fileKey+': '+maxFrequency
                if maxFrequency!='no match':
                    self.trainingDataDict[maxFrequency]+=1                                                 
        return self.fileDict
                            


class LevenshteinCalculator(object):
    def __init__(self, word1, word2):
        self.distance=getEditDistance(word1, word2)

    def __init__(self):
        self.distance=None

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


class StringUtils(object):

    def detokenizeString(self, tokenList):
        detokenizedString=''
        for i, token in enumerate(tokenList):
                if i==len(tokenList)-1:
                    detokenizedString+=token.lower()
                else:
                    detokenizedString+=token.lower()+' '
        return detokenizedString

    
   
            
        
                    
                    
                
                
            
        
        
        
        
    
    
   
    

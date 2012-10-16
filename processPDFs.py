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
        tokenCountForEndString=len(endString.split())
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText or seedText==False:
                #print 'testing'+fileKey
                PDFText=self.getPDFInfo(self.filePath+'\\'+fileKey+'.pdf')
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

    def checkForAlternateString(self, alternateString, explicitMeaning, seedText='no match'):#seeks a string that gives away department info and assigns that department name to file.
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText:
                PDFText=self.getPDFInfo(self.filePath+'\\'+fileKey+'.pdf')
                tokenCountForAlternate=len(alternateString.split())
                tokenList=PDFText.split()
                for i, token in enumerate(PDFText):
                    if i+tokenCountForAlternate<len(tokenList):#test for end of PDFtext
                        testString=self.toolBox.detokenizeString(tokenList[i:i+tokenCountForAlternate]).strip()
                        if self.toolBox.getEditDistance(testString.lower(), alternateString.lower())<=3:
                            markOne=i+tokenCountForAlternate
                            self.fileDict[fileKey]=explicitMeaning
                            #print fileKey+': '+self.fileDict[fileKey]

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
                
                
        for unlikelyKey in self.trainingDataDict.keys():
            if self.trainingDataDict[unlikelyKey]==1:
                candidateDict={}
                for likelyKey in self.trainingDataDict.keys():
                    distance=self.toolBox.getEditDistance(unlikelyKey, likelyKey)
                    if self.trainingDataDict[likelyKey]>1 and distance<=3:
                       candidateDict[likelyKey]=distance
                #print 'unlikely key is '+unlikelyKey+'. Candidates are '+str(candidateDict)
                if candidateDict!={}:
                    #print 'likely key is '+min(candidateDict, key=candidateDict.get)
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
                                    
                                
                        

    def findTrainingTextBetweenTwoStrings(self, beginString, endString, seedText, tolerance=2):
        tokenCountForBeginString=len(beginString.split())
        tokenCountForEndString=len(endString.split())
        textDict={}
        for fileKey in self.fileDict.keys():
            if self.fileDict[fileKey]==seedText:
                textDict[fileKey]=''
                PDFText=self.getPDFInfo(self.filePath+'\\'+fileKey+'.pdf')
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
                            textDict[fileKey]=self.toolBox.detokenizeString(workingTokens)
                            break
        for fileName in textDict.keys():
            candidates={}
            text=textDict[fileName].split()
            for i, word in enumerate(text):
                for key in self.trainingDataDict.keys():
                        trainingString=key.lower().split()
                        if self.toolBox.getEditDistance(trainingString[0], word)<=4:
                            if (i+len(trainingString))<=(len(text)):
                                testWord=self.toolBox.detokenizeString(text[i:i+len(trainingString)])
                                distance=self.toolBox.getEditDistance(testWord, key)
                            if distance<=3:
                                candidateRankVar=0.0
                                frequency=0.0
                                if key in candidates.keys():
                                    frequency+=1.0
                                candidateRankVar=(math.log(float(self.trainingDataDict[key])))/(distance+1.0)
                                candidates[key]=candidateRankVar
                
            print 'candidates for '+fileName+' are: '
            print candidates
            if candidates != {}:
                maxFrequency=max(candidates, key=candidates.get)
            else: maxFrequency='no match'
            
            self.fileDict[fileName]=maxFrequency
            print fileName+': '+maxFrequency
            if maxFrequency!='no match':
                self.trainingDataDict[maxFrequency]+=1   


class testProcessETDs(ProcessETDs):#skips training data creation step for testing.
    def __init__(self, directory, fileDict, trainingDataDict):#supply premade data for test
        ProcessETDs.__init__(self, directory)
        self.fileDict=fileDict
        self.trainingDataDict=trainingDataDict
        

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

def addToCSV(CSVfile, fileDict):
    CSVfile=open(CSVfile, 'r')
    lines=[]
    for line in CSVfile:
        lines.append(line.split('","'))
     
    CSVfile.close()
    for i, line in enumerate(lines):
        for j, word in enumerate(line):
            if word[-1]=='\n':
                line[j]=word[:-2]
        if i==0:
            if line[-1]!='department name':
                line.append('department name')
        else:
            CSVid=line[1][3:10]
            if CSVid in fileDict.keys():
                line.append(fileDict[CSVid])
    CSVfile=open(r"C:\Users\srobbins\Desktop\test.csv", 'w')
    for eachLine in lines:
        for i, word in enumerate(eachLine):
            if i==0:
                CSVfile.write(word+'","')
            elif i==(len(eachLine)-1):
                CSVfile.write(word+'"\n')
            else:
                CSVfile.write(word+'","')
    
        
    

def runModuleForIdeals(filePath):
    #test data for retro1
    #testTrainingDataDict={'english the degree of. it? 4- jzedfeiiliku^ in charge of thesis !_/ head of deparnnent recommendation concurred inf (hllcaatz. &amp;\\ %jf^y^t \xe2\x80\xa2iu. t &lt;u/ i olu*x^ * subject to successful final examination': 1, 'botany': 2, 'metallurgical engineering': 2, 'animal nutrition': 4, 'dairy technology': 1, 'economics \xe2\xa3- i \xe2\x80\xa2 ^\\jj&gt;il^r in charge of thesis -^ a*tia\'rt,j**y^*ka oi department %f,@iuu^ committee on final examination! t required for doctor\'s degree but not for master\'s. 5m\xe2\x80\x9411-51\xe2\x80\x9448672 </page> <page id="2" bbox="0.000,0.000,616.800,795.600" rotate="0">oommmm utrau\xe2\xbb cawda aid m wtnam ft*h\xe2\xbb# 19^7 to 1990 fho pojpom of thlf dlmortotlon mo to onolym mvtrpjl toobnionoo for \xe2\x84\xa2poj^opjb\xe2\xbboplof 0)4000^ pjpot wooppop* ^(po* lp70jpop)oaajponb^w4mpnio) npop ppof^popoo ^p/fljphmpvpjpjp obpopo) obnop opnojpp opopvi op\'wooi opappj&quot; ooboflbr tp^p* ^p/ w*aaapap \xe2\x80\xa2to tbolr wotulaom for latoraotiooal ooaparioom*': 1, 'veterinary pathology and hygiene': 2, 'physico-chemical lilology': 1, 'animal science': 3, 'engineering': 5, 'gkrtfan helmut rflhder in charge of thesis head of department committee on final examinationf recommendation concurrexiirrf -^zsv-lun/l &amp;c4i^ / fll&amp;\'libs* tsi-* jvjf^yj. ijtugse^rt4ajea^ t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,612.480,792.240" rotate="0">&quot;melitto-logia&quot; the mythology': 1, "plant pathology -^f-^^^^r **^&gt;7 in charge of thesis {/0'lzz^c--/ &gt;-ig_, '/^7, u head of department cj recommendation concurred inf &gt;?^v * subj ect to successful final examination": 1, 'spanish': 1, 'zoology': 9, 'agronomy': 3, 'education': 8, 'accountancy v ^i&quot; \\j yf\xe2\x84\xa2 charge ot i hesi \' head of departmei department recommendation concurred inf committee on final examination! t required for doctorydegree but not for master\'s 5m\xe2\x80\x9411-51\xe2\x80\x9448672 </page> <page id="1" bbox="0.000,0.000,622.080,799.680" rotate="0">117 continuing now to another asset section, the term &quot;deferred charges&quot; lacks informativeness': 1, 'classical philology': 1, 'enqush': 1, 'geography': 3, 'horticulture': 7, 'ceolooy': 1, 'psychology': 25, 'mechanical engineering': 2, 'husiness': 1, 'geology 0^hm(r^.^^ji^l. jfa^-^nrl^zkjl\xe2\x80\x94 in charge of thesis head of department recommendation concurred inf &lt;*\xe2\xa3 ^. *&gt;&amp;. .*:&lt; committee on final examinationf \xe2\x80\xa2subject to successful final examination': 1, 'charge of thesis . xojsa-jtse) head of department recommendation concurred inf \\ ^^ajl\'m\'is^ ^r. i t required for doctor\'s degree but not for master\'s. committee on final examination! im\xe2\x80\x94h-51\xe2\x80\x9448b72 </page> <page id="1" bbox="0.000,0.000,569.280,768.480" rotate="0">the effect of fat level': 1, 'business': 2, 'physios': 1, 'speech': 5, 'theoretical and applied mechanics': 11, 'plant pathology': 1, 'electrical engineering in charge of thesis tdt*-* head of department recommendation concurred inf p yf huxn. committee on final examinationf t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,618.000,796.560" rotate="0">f natural limitations': 1, 'mathematics': 11, 'physical education': 11, 'food technology': 1, 'accountancy': 12, 'agricultural economics': 15, 'philosophy': 4, 'dairy science': 3, 'geology': 13, 'entomology': 7, 'w^ / in charge of thesis l^yu kju^y head of denartmcnt recommendation concurred inf &lt;$8?%r^ i^m^ (^0 ft . =\xe2\xa3) - (l^^jg p y/~)&lt;\xe2\xb1xzk^v^ committee on final examination^ t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,617.280,796.080" rotate="0">mobilities op ions in collodion membranes by william gates moulton b.s., western illinois state teachers college, 1946 m.s., university of illinois, 1948 thesis submitted in partial fulfillment': 1, 'french': 1, 'mining engineering': 1, "agricultural economics '": 1, 'sociology': 1, 'ohemioal engineering': 1, 'political science': 10, 'sociology charge of thesis recommemfljition concurred inf m^u 5t^7 -&gt;--&gt;-^-^^&gt;l-^ v e^s) t required for doctor\'s degree but not fofmaster\'s. committee on final examination! m440 </page> <page id="2" bbox="0.000,0.000,617.040,795.840" rotate="0">social factors in southern white equalitarianism by donald edwin rasmussen a.b., university of illinois, 1937 a.m., university of illinois, 1938 thesis submitted in partial fulfillment': 1, 'mass communications': 2, 'physiology': 6, 'zoology recommendation concurred inf /^^^^^^t^a^xz^r-^^ j head of department c7?,c7^w$ qycsuva&amp;^c committee on final examination! * subject to successful final examination': 1, 'folitieal soienoe . in charge of thesis ovj. ses3.ofdepartment recommendation concurred inf $(l^ (7. fuul vq^rt- sy^-*k^\xe2\xa3. ft committee on final examination! * subject to successful final examination': 1, 'economics': 25, 'library science': 1, 'physico-chemical biology': 1, 'civil engineering': 3, 'chemical engineering': 6, 'english': 24, 'bacteriology': 8, 'electrical engineering': 15, 'german': 1, 'chemistry': 18, 'physics': 23, 'history': 18}
    #testFileDict={'0001659': 'plant pathology', '0001658': 'no match', '0005978': 'chemical engineering', '0005979': 'no match', '0005970': 'mathematics', '0005971': 'physical education', '0005972': 'economics', '0005973': 'animal science', '0005974': 'chemistry', '0005975': 'ohemioal engineering', '0005976': 'no match', '0005977': 'mathematics', '0004478': 'civil engineering', '0004479': 'economics', '0004472': 'psychology', '0004473': 'dairy science', '0004470': 'psychology', '0004471': 'chemistry', '0004476': 'geography', '0004477': 'veterinary pathology and hygiene', '0004474': 'bacteriology', '0004475': 'physics', '0002057': 'mathematics', '0002058': 'history', '0006021': 'no match', '0004018': 'geology', '0004019': 'theoretical and applied mechanics', '0004010': 'agricultural economics', '0004011': 'political science', '0004013': 'physics', '0004014': 'accountancy', '0004015': 'psychology', '0004016': 'bacteriology', '0004017': 'agricultural economics', '0003129': 'animal nutrition', '0003128': 'economics', '0003123': 'entomology', '0003125': 'physics', '0003124': 'physical education', '0003126': 'english', '0002230': 'physical education', '0002231': 'english', '0002068': 'economics', '0002063': 'no match', '0002062': 'psychology', '0002060': 'animal nutrition', '0002067': 'economics', '0002066': 'history', '0002065': 'zoology', '0002064': 'geology', '0005998': 'botany', '0005239': 'education', '0005233': 'physics', '0005232': 'no match', '0005231': 'animal nutrition', '0005230': 'philosophy', '0005237': 'business', '0005236': 'psychology', '0005235': 'no match', '0005234': 'chemical engineering', '0004443': 'speech', '0004442': 'zoology', '0004441': 'psychology', '0004440': "agricultural economics '", '0004447': 'no match', '0004446': 'geology', '0004445': 'physico-chemical biology', '0004444': 'speech', '0004449': 'physiology', '0004448': 'no match', '0006013': 'ceolooy', '0006010': 'economics', '0006011': 'geology', '0006016': 'chemistry', '0006017': 'mass communications', '0006014': 'food technology', '0006015': 'psychology', '0005941': 'entomology', '0006018': 'no match', '0006019': 'zoology', '0004419': 'physics', '0001389': 'english', '0001388': 'english', '0001544': 'physics', '0001547': 'philosophy', '0001546': 'electrical engineering', '0001549': 'no match', '0001548': 'agricultural economics', '0003989': 'no match', '0003988': 'psychology', '0002742': 'economics', '0002743': 'electrical engineering', '0002740': 'no match', '0002741': 'geology', '0002746': 'geology', '0002744': 'electrical engineering', '0002745': 'agricultural economics', '0006023': 'economics', '0006022': 'chemistry', '0002748': 'agricultural economics', '0006020': 'entomology', '0006027': 'entomology', '0006026': 'chemistry', '0006025': 'physiology', '0001453': 'psychology', '0001452': 'horticulture', '0001451': 'no match', '0001450': 'agronomy', '0002737': 'electrical engineering', '0002736': 'geology', '0002735': 'electrical engineering', '0002734': 'mathematics', '0002733': 'electrical engineering', '0002732': 'accountancy', '0002731': 'mathematics', '0002730': 'geology', '0002739': 'animal nutrition', '0002738': 'history', '0004021': 'accountancy', '0004020': 'no match', '0005945': 'chemistry', '0005944': 'theoretical and applied mechanics', '0005947': 'geography', '0005946': 'accountancy v ^i&quot; \\j yf\xe2\x84\xa2 charge ot i hesi \' head of departmei department recommendation concurred inf committee on final examination! t required for doctorydegree but not for master\'s 5m\xe2\x80\x9411-51\xe2\x80\x9448672 </page> <page id="1" bbox="0.000,0.000,622.080,799.680" rotate="0">117 continuing now to another asset section, the term &quot;deferred charges&quot; lacks informativeness', '0004418': 'electrical engineering', '0005940': 'zoology', '0005943': 'accountancy', '0005942': 'mathematics', '0004414': 'accountancy', '0004415': 'history', '0004416': 'horticulture', '0004417': 'speech', '0005949': 'bacteriology', '0005948': 'geology', '0004412': 'french', '0004413': 'horticulture', '0003136': 'physics', '0003137': 'no match', '0003134': 'mass communications', '0003135': 'economics', '0003132': 'english', '0003133': 'electrical engineering', '0003130': 'speech', '0003131': 'physios', '0003139': 'no match', '0002081': 'english', '0005247': 'engineering', '0002083': 'history', '0002082': 'electrical engineering', '0002085': 'economics', '0005240': 'no match', '0002078': 'physics', '0002079': 'german', '0002070': 'political science', '0002071': 'horticulture', '0002072': 'mathematics', '0002073': 'english', '0002074': 'history', '0002075': 'no match', '0002076': 'economics', '0001670': 'political science', '0005228': 'geology', '0005229': 'physical education', '0005220': 'physics', '0005221': 'accountancy', '0005222': 'accountancy', '0005223': 'spanish', '0005224': 'engineering', '0005225': 'no match', '0005226': 'physiology', '0005227': 'zoology', '0004450': 'theoretical and applied mechanics', '0004451': 'physics', '0004452': 'political science', '0004453': 'chemical engineering', '0004454': 'physics', '0004455': 'history', '0004456': 'education', '0004457': 'physics', '0004458': 'english', '0004459': 'economics', '0005989': 'economics', '0005988': 'psychology', '0005981': 'chemistry', '0005980': 'education', '0005983': 'no match', '0005982': 'no match', '0005985': 'agronomy', '0005984': 'physics', '0005987': 'chemistry', '0005986': 'accountancy', '0001398': 'geology', '0001399': 'horticulture', '0001394': 'physics', '0001395': 'history', '0001396': 'physics', '0001397': 'history', '0001390': 'physics', '0001391': 'history', '0001392': 'psychology', '0001393': 'education', '0006931': 'english', '0006930': 'business', '0006932': 'economics', '0001552': 'physical education', '0001553': 'english', '0001550': 'education', '0001551': 'electrical engineering', '0001556': 'electrical engineering', '0001557': 'history', '0001554': 'english', '0001555': 'physical education', '0001558': 'zoology', '0001559': 'no match', '0006915': 'economics', '0004435': 'physics', '0003998': 'philosophy', '0003999': 'mechanical engineering', '0003994': 'physiology', '0003995': 'agricultural economics', '0003996': 'physics', '0003997': 'agricultural economics', '0003990': 'agricultural economics', '0003991': 'theoretical and applied mechanics', '0003992': 'theoretical and applied mechanics', '0003993': 'mining engineering', '0002210': 'entomology', '0002212': 'agricultural economics', '0002213': 'mathematics', '0002214': 'psychology', '0002216': 'physical education', '0002217': 'physical education', '0002218': 'history', '0002219': 'political science', '0005992': 'political science', '0005251': 'chemical engineering', '0001563': 'metallurgical engineering', '0001562': 'theoretical and applied mechanics', '0001561': 'english', '0001560': 'no match', '0001564': 'zoology', '0002724': 'horticulture', '0002725': 'agricultural economics', '0002726': 'zoology', '0002727': 'geography', '0002720': 'physics', '0002721': 'economics', '0002722': 'history', '0002723': 'no match', '0005999': 'veterinary pathology and hygiene', '0002728': 'economics', '0002729': 'electrical engineering', '0005952': 'mathematics', '0004428': 'no match', '0005950': 'economics', '0005951': 'history', '0005956': 'chemistry', '0005957': 'economics \xe2\xa3- i \xe2\x80\xa2 ^\\jj&gt;il^r in charge of thesis -^ a*tia\'rt,j**y^*ka oi department %f,@iuu^ committee on final examination! t required for doctor\'s degree but not for master\'s. 5m\xe2\x80\x9411-51\xe2\x80\x9448672 </page> <page id="2" bbox="0.000,0.000,616.800,795.600" rotate="0">oommmm utrau\xe2\xbb cawda aid m wtnam ft*h\xe2\xbb# 19^7 to 1990 fho pojpom of thlf dlmortotlon mo to onolym mvtrpjl toobnionoo for \xe2\x84\xa2poj^opjb\xe2\xbboplof 0)4000^ pjpot wooppop* ^(po* lp70jpop)oaajponb^w4mpnio) npop ppof^popoo ^p/fljphmpvpjpjp obpopo) obnop opnojpp opopvi op\'wooi opappj&quot; ooboflbr tp^p* ^p/ w*aaapap \xe2\x80\xa2to tbolr wotulaom for latoraotiooal ooaparioom*', '0005954': 'speech', '0005955': 'chemistry', '0004421': 'agronomy', '0004420': 'economics', '0005958': 'accountancy', '0005959': 'no match', '0004425': 'dairy science', '0004424': 'classical philology', '0004427': 'chemical engineering', '0004426': 'economics', '0002077': 'agricultural economics', '0003143': 'psychology', '0003142': 'sociology', '0003141': "plant pathology -^f-^^^^r **^&gt;7 in charge of thesis {/0'lzz^c--/ &gt;-ig_, '/^7, u head of department cj recommendation concurred inf &gt;?^v * subj ect to successful final examination", '0003140': 'economics', '0003147': 'political science', '0003146': 'psychology', '0003145': 'bacteriology', '0003144': 'dairy science', '0003149': 'electrical engineering', '0003148': 'bacteriology', '0006917': 'horticulture', '0001668': 'zoology recommendation concurred inf /^^^^^^t^a^xz^r-^^ j head of department c7?,c7^w$ qycsuva&amp;^c committee on final examination! * subject to successful final examination', '0001669': 'history', '0006916': 'mathematics', '0001664': 'no match', '0001665': 'folitieal soienoe . in charge of thesis ovj. ses3.ofdepartment recommendation concurred inf $(l^ (7. fuul vq^rt- sy^-*k^\xe2\xa3. ft committee on final examination! * subject to successful final examination', '0001666': 'english the degree of. it? 4- jzedfeiiliku^ in charge of thesis !_/ head of deparnnent recommendation concurred inf (hllcaatz. &amp;\\ %jf^y^t \xe2\x80\xa2iu. t &lt;u/ i olu*x^ * subject to successful final examination', '0001667': 'geology 0^hm(r^.^^ji^l. jfa^-^nrl^zkjl\xe2\x80\x94 in charge of thesis head of department recommendation concurred inf &lt;*\xe2\xa3 ^. *&gt;&amp;. .*:&lt; committee on final examinationf \xe2\x80\xa2subject to successful final examination', '0001660': 'animal science', '0001661': 'enqush', '0001662': 'psychology', '0001663': 'english', '0005219': 'no match', '0005969': 'psychology', '0005968': 'no match', '0005962': 'mathematics', '0005961': 'no match', '0005960': 'no match', '0005966': 'civil engineering', '0005965': 'chemistry', '0005964': 'entomology', '0005996': 'zoology', '0005997': 'accountancy', '0005994': 'no match', '0005995': 'chemistry', '0004469': 'english', '0004468': 'history', '0005990': 'husiness', '0005991': 'psychology', '0004465': 'english', '0004464': 'english', '0004467': 'psychology', '0004466': 'physics', '0004461': 'theoretical and applied mechanics', '0004460': 'chemistry', '0004463': 'bacteriology', '0004462': 'theoretical and applied mechanics', '0004487': 'theoretical and applied mechanics', '0004486': 'dairy technology', '0004485': 'engineering', '0004484': 'no match', '0004483': 'accountancy', '0004482': 'botany', '0004481': 'physico-chemical lilology', '0004480': 'history', '0004489': 'no match', '0004488': 'engineering', '0003594': 'english', '0003595': 'electrical engineering in charge of thesis tdt*-* head of department recommendation concurred inf p yf huxn. committee on final examinationf t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,618.000,796.560" rotate="0">f natural limitations', '0003596': 'w^ / in charge of thesis l^yu kju^y head of denartmcnt recommendation concurred inf &lt;$8?%r^ i^m^ (^0 ft . =\xe2\xa3) - (l^^jg p y/~)&lt;\xe2\xb1xzk^v^ committee on final examination^ t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,617.280,796.080" rotate="0">mobilities op ions in collodion membranes by william gates moulton b.s., western illinois state teachers college, 1946 m.s., university of illinois, 1948 thesis submitted in partial fulfillment', '0003597': 'sociology charge of thesis recommemfljition concurred inf m^u 5t^7 -&gt;--&gt;-^-^^&gt;l-^ v e^s) t required for doctor\'s degree but not fofmaster\'s. committee on final examination! m440 </page> <page id="2" bbox="0.000,0.000,617.040,795.840" rotate="0">social factors in southern white equalitarianism by donald edwin rasmussen a.b., university of illinois, 1937 a.m., university of illinois, 1938 thesis submitted in partial fulfillment', '0003598': 'gkrtfan helmut rflhder in charge of thesis head of department committee on final examinationf recommendation concurrexiirrf -^zsv-lun/l &amp;c4i^ / fll&amp;\'libs* tsi-* jvjf^yj. ijtugse^rt4ajea^ t required for doctor\'s degree but not for master\'s. m440 </page> <page id="2" bbox="0.000,0.000,612.480,792.240" rotate="0">&quot;melitto-logia&quot; the mythology', '0006928': 'agricultural economics', '0006929': 'english', '0006926': 'no match', '0006927': 'chemistry', '0006924': 'psychology', '0006925': 'geology', '0006922': 'chemistry', '0006920': 'accountancy', '0004009': 'physics', '0004008': 'physiology', '0004003': 'english', '0004002': 'political science', '0004001': 'political science', '0004000': 'no match', '0004007': 'theoretical and applied mechanics', '0004006': 'agricultural economics', '0004004': 'physical education', '0002229': 'no match', '0002228': 'physical education', '0002224': 'engineering', '0002227': 'no match', '0002226': 'english', '0002220': 'english', '0002223': 'psychology', '0002222': 'history', '0004429': 'psychology', '0005953': 'philosophy', '0002089': 'geology', '0002088': 'electrical engineering', '0005249': 'chemistry', '0005246': 'civil engineering', '0002080': 'psychology', '0005244': 'no match', '0005245': 'charge of thesis . xojsa-jtse) head of department recommendation concurred inf \\ ^^ajl\'m\'is^ ^r. i t required for doctor\'s degree but not for master\'s. committee on final examination! im\xe2\x80\x94h-51\xe2\x80\x9448b72 </page> <page id="1" bbox="0.000,0.000,569.280,768.480" rotate="0">the effect of fat level', '0005242': 'economics', '0002084': 'physics', '0002087': 'political science', '0005241': 'mechanical engineering', '0005939': 'english', '0002711': 'economics', '0002713': 'metallurgical engineering', '0002712': 'electrical engineering', '0002715': 'theoretical and applied mechanics', '0002714': 'economics', '0002717': 'physics', '0002716': 'education', '0002719': 'economics', '0002718': 'entomology', '0004436': 'psychology', '0004437': 'bacteriology', '0004422': 'chemical engineering', '0004432': 'no match', '0004433': 'agricultural economics', '0004430': 'physiology', '0004438': 'no match', '0004439': 'no match', '0006005': 'physical education', '0006004': 'no match', '0006007': 'education', '0006006': 'chemistry', '0006001': 'chemistry', '0006000': 'no match', '0006002': 'animal science', '0006008': 'education', '0003150': 'bacteriology', '0003151': 'library science', '0003152': 'psychology', '0003154': 'english', '0003155': 'english', '0006919': 'psychology', '0006918': 'agricultural economics'}
    #test data for retro5
    testFileDict={'8324497': 'civil engineering', '8324496': 'education', '8324495': 'education', '8422156': 'labor', '8422151': 'linguistics', '8422099': 'education', '8324558': 'physics', '8422152': 'sla', '8324556': 'electrical engineering', '8324557': 'electrical engineering', '8324554': 'agricultural economics', '8324555': 'chemistry', '8324552': 'comparative literature', '8324553': 'nuclear engineering', '8324499': 'chemistry', '8324551': 'entomology', '8422150': 'genetics', '8422153': 'chemistry', '8422094': 'finance', '8409859': 'nutritional sciences', '8422095': 'metallurgical engineering', '8422096': 'theatre', '8422097': 'plant biology', '8422063': 'entomology', '8422090': 'communications', '8422091': 'no match', '8422021': 'electrical engineering', '8422020': 'psychology', '8422023': 'education', '8422022': 'civil engineering', '8422025': 'education', '8324550': 'comparative literature', '8422027': 'electrical engineering', '8422026': 'electrical engineering', '8422029': 'mathematios', '8422028': 'metallurgical engineering', '8422093': 'labor', '8410037': 'chemistry', '8310021': 'electrical engineering', '8310020': 'chemistry', '8310023': 'physios', '8310022': 'veterinary medical science', '8410020': 'nuclear engineering', '8410021': 'biochemistry', '8410022': 'agricultural engineering', '8410023': 'philosophy', '8410024': 'electrical engineering', '8410025': 'psychology', '8410026': 'chemistry', '8410027': 'education', '8324655': 'education', '8324654': 'electrical engineering', '8324657': 'mathematics', '8324651': 'civil engineering', '8324653': 'education', '8324659': 'business administration', '8324658': 'sociology', '8409868': 'physical education', '8409808': 'mathematics', '8409809': 'biophysics', '8409800': 'electrical engineering', '8409801': 'metallurgical engineering', '8409802': 'chemistry', '8409803': 'education', '8409804': 'chemistry', '8409805': 'accountancy', '8409807': 'agronomy', '8409893': 'accountancy', '8409892': 'agricultural engineering', '8409891': 'education', '8409890': 'metallurgical engineering', '8409897': 'education', '8409896': 'microbiology', '8409895': 'agronomy', '8409894': 'physics', '8409899': 'physiology', '8409861': 'civil engineering', '8422155': 'nutritional sciences', '8409934': 'labor', '8409936': 'biology', '8409937': 'psychology', '8409930': 'electrical engineer', '8409931': 'mechanical engineering', '8409932': 'economics', '8409933': 'biochemistry', '8409938': 'biology', '8409939': 'chemical engineering', '8422154': 'speech communication', '8422157': 'mechanical engineering', '8324589': 'chemistry', '8324588': 'social work', '8324585': 'entomology', '8324584': 'sociology', '8324587': 'history', '8324586': 'biology', '8324581': 'biochemistry', '8324582': 'geography', '8422137': 'nuclear engineering', '8422065': 'electrical engineering', '8324566': 'physical education', '8324565': 'no match', '8324564': 'biochemistry', '8324563': 'chemistry', '8324562': 'library', '8324561': 'musicology', '8324560': 'economxcs', '8324606': 'french', '8324605': 'no match', '8324602': 'physics', '8324603': 'no match', '8324569': 'education', '8324568': 'physics', '8422108': 'psychology', '8422106': 'metallurgical engineering', '8422107': 'microbiology', '8422104': 'agronomy', '8422105': 'nutritional sciences', '8422102': 'chemistry', '8422103': 'chemistry', '8422101': 'physiology', '8324513': 'horticulture', '8324510': 'agronomy', '8324511': 'education', '8324516': 'biochemistry', '8324517': 'horticulture', '8324515': 'education', '8324518': 'chemical engineering', '8324519': 'physics', '8422134': 'mathematics', '8410050': 'english', '8410053': 'education', '8410052': 'animal science', '8410057': 'physics', '8410059': 'business administration', '8410058': 'no match', '8409751': 'physics', '8409753': 'mathematics', '8409754': 'biochemistry', '8409755': 'history', '8409756': 'electrical engineering', '8409758': 'english', '8409759': 'physics', '8409870': 'chemistry', '8409872': 'nutritional', '8409875': 'physics', '8409874': 'physics', '8409877': 'mathematics', '8409876': 'veterinary medical science', '8409879': 'biology', '8409878': 'physical education', '8409972': 'health', '8409973': 'chemistry', '8409974': 'civil engineering', '8409975': 'environmental engineering', '8409976': 'veterinary medical science', '8409977': 'physics', '8422092': 'agricultural economics', '8422131': 'biophysics', '8502064': 'physics', '8502065': 'no match', '8502066': 'chemistry', '8502060': 'entomology', '8502061': 'veterinary medical science', '8502062': 'psychology', '8502063': 'chemistry', '8422130': 'aeronautical', '8409983': 'aeronautical', '8422793': 'biology', '8422792': 'plant pathology', '8422791': 'computer science', '8422797': 'mechanical engineering', '8422796': 'computer science', '8422794': 'genetics', '8422799': 'education', '8422798': 'physics', '8422159': 'geology', '8422142': 'education', '8410028': 'chemical engineering', '8324529': 'education', '8422146': 'health', '8422147': 'chemistry', '8422144': 'electrical engineering', '8410029': 'biochemistry', '8324523': 'education', '8324522': 'genetics', '8324521': 'political science', '8324520': 'agronomy', '8422158': 'chemistry', '8324526': 'horticulture', '8324525': 'economics', '8324524': 'education', '8422783': 'agronomy', '8422111': 'theoretical', '8422110': 'spanish', '8324637': 'nutritional sciences', '8324636': 'communications', '8324634': 'electrical engineering', '8324633': 'education', '8324632': 'metallurgical engineering', '8324630': 'english', '8324639': 'psychology', '8324638': 'geology', '8410015': 'education', '8410014': 'education', '8410017': 'psychology', '8410016': 'chemistry', '8410011': 'education', '8422132': 'food science', '8410013': 'accountancy', '8410012': 'computer science', '8422035': 'computer science', '8410019': 'spanish', '8410018': 'civil engineering', '8422030': 'education', '8422031': 'history', '8324642': 'mechanical engineering', '8324549': 'history', '8324640': 'accountancy', '8324641': 'chemistry', '8324646': 'plant pathology', '8324647': 'agricultural economics', '8324644': 'civil engineering', '8324645': 'physiology', '8324648': 'chemistry', '8324649': 'metallurgical engineering', '8409835': 'chemistry', '8409834': 'computer science', '8409836': 'education', '8409830': 'electrical engineering', '8409833': 'no match', '8409832': 'psychology', '8422083': 'computer science', '8409839': 'nuclear engineering', '8409838': 'chemistry', '8422129': 'chemistry', '8422082': 'education', '8422081': 'education', '8422080': 'aeronautical', '8422139': 'animal science', '8409979': 'physiology', '8409880': 'accountancy', '8409882': 'anthropology', '8409883': 'biophysics', '8409884': 'english', '8409885': 'chemical engineering', '8409886': 'electrical engineering', '8409887': 'human resources', '8409889': 'metallurgical engineering', '8410040': 'education', '8409901': 'agronomy', '8409900': 'physics', '8409903': 'electrical engineering', '8409905': 'health', '8409904': 'animal science', '8409907': 'physical education', '8409906': 'philosophy', '8409909': 'physics', '8409908': 'nuclear engineering', '8422166': 'chemistry', '8324540': 'plant pathology', '8324598': 'computer science', '8324599': 'education', '8324593': 'nuclear engineering', '8324590': 'theoretical', '8324591': 'economics', '8324596': 'nuclear engineering', '8324597': 'chemistry', '8324594': 'computer science', '8324595': 'astronomy', '8324574': 'chemistry', '8324575': 'civil engineering', '8324679': 'chemical engineering', '8324678': 'no match', '8324570': 'psychology', '8422077': 'economics', '8324572': 'plant pathology', '8324573': 'physics', '8324672': 'plant pathology', '8324671': 'education', '8324670': 'electrical engineering', '8324677': 'theoretical', '8324676': 'veterinary medical science', '8324674': 'physics', '8422179': 'dairy science', '8422178': 'chemistry', '8422173': 'biology', '8422171': 'physics', '8422176': 'civil engineering', '8422175': 'education', '8422174': 'computer science', '8422087': 'socx&amp;l work', '8324680': 'mathematics', '8324681': 'electrical engineering', '8410036': 'accountancy', '8422182': 'nuclear engineering', '8422180': 'food science', '8422181': 'electrical engineering', '8310006': 'chemistry', '8310005': 'accountancy', '8310003': 'psychology', '8310002': 'biochemistry', '8310001': 'mechanical engineering', '8310000': 'psychology', '8410047': 'computer science', '8410044': 'economics', '8410045': 'accountancy', '8410042': 'education', '8410043': 'psychology', '8310009': 'civil engineering', '8410041': 'physics', '8422136': 'geography', '8409769': 'philosophy', '8409765': 'education', '8409764': 'veterinary medical science', '8409767': 'no match', '8409766': 'metallurgical engineering', '8409761': 'no match', '8409760': 'botany', '8409763': 'chemistry', '8409762': 'chemistry', '8409945': 'accountancy', '8409944': 'civil engineering', '8409947': 'education', '8409946': 'botany', '8409941': 'physics', '8409940': 'plant pathology', '8409943': 'no match', '8409942': 'no match', '8409949': 'no match', '8409787': 'finance', '8409786': 'plant biology', '8409785': 'no match', '8409784': 'education', '8409782': 'physics', '8409781': 'chemistry', '8409780': 'civil engineering', '8409866': 'library', '8409867': 'eleotrical engineering', '8409864': 'veterinary medical science', '8409865': 'physics', '8409863': 'plant pathology', '8409789': 'computer science', '8409788': 'eleotrical engineering', '8502058': 'human resources', '8502053': 'education', '8502052': 'physiology', '8502055': 'finance', '8502054': 'education', '8502057': 'education', '8502056': 'animal science', '8324548': 'dairy science', '8409898': 'education', '8422784': 'education', '8422785': 'psychology', '8422786': 'sociology', '8422787': 'metallurgical engineering', '8422788': 'chemistry', '8324538': 'accountancy', '8324539': 'spanish', '8324530': 'leisure studies', '8324531': 'computer science', '8324533': 'labor', '8324534': 'speech communication', '8324535': 'electrical engineering', '8324537': 'communications', '8409919': 'philosophy', '8324624': 'philosophy', '8324625': 'speech', '8324626': 'leisure studies', '8324627': 'education', '8324620': 'chemistry', '8324621': 'civil engineering', '8324622': 'education', '8324628': 'chemistry', '8324629': 'chemical engineering', '8410002': 'theatre', '8410003': 'psychology', '8410000': 'chemistry', '8410001': 'psychology', '8410006': 'agronomy', '8410007': 'accountancy', '8410004': 'german', '8410005': 'no match', '8422043': 'civil engineering', '8422042': 'electrical engineering', '8410008': 'mechanical engineering', '8410009': 'agronomy', '8422047': 'economics', '8422046': 'chemistry', '8422044': 'education', '8309993': 'plant pathology', '8309992': 'education', '8309991': 'speech', '8309990': 'chemistry', '8309997': 'business administration', '8309996': 'veterinary medical science', '8309995': 'spanish', '8309994': 'geology', '8309999': 'agricultural economics', '8422049': 'geology', '8410032': 'education', '8422121': 'education', '8409822': 'library', '8409823': 'computer science', '8409820': 'education', '8409821': 'electrical engineering', '8409826': 'animal science', '8409827': 'psychology', '8409824': 'education', '8409825': 'nutritional sciences', '8409453': 'chemistry', '8409980': 'mathematics', '8409828': 'physics', '8409982': 'no match', '8409985': 'veterinary medical science', '8324576': 'chemistry', '8409987': 'accountancy', '8409986': 'slavic languages', '8422071': 'dairy science', '8422076': 'english', '8422041': 'physics', '8410077': 'electrical engineering', '8410076': 'psychology', '8410075': 'mechanical engineering', '8410074': 'chemistry', '8410073': 'physics', '8410072': 'agricultural economici', '8410071': 'physics', '8422128': 'psychology', '8422075': 'nuclear engineering', '8410078': 'microbiology', '8410039': 'horticulture', '8409738': 'psychology', '8409739': 'library', '8422079': 'chemical engineering', '8324578': 'political science', '8422119': 'biology', '8324579': 'chemistry', '8409857': 'electrical engineering', '8409856': 'plant pathology', '8409855': 'eoonomios', '8409854': 'metallurgical engineering', '8409853': 'mechanical engineering', '8409852': 'sociology', '8409851': 'geology', '8409850': 'agronomy', '8409916': 'computer science', '8409917': 'microbiology', '8409914': 'biology', '8409915': 'economics', '8409912': 'electrical engineer', '8409913': 'psychology', '8409910': 'accountancy', '8409858': 'chemical engineering', '8422118': 'food science', '8409968': 'astronomy', '8422143': 'education', '8422140': 'biology', '8409966': 'spanish', '8422148': 'chemistry', '8324541': 'no match', '8324669': 'education', '8324543': 'educati', '8324542': 'physics', '8324545': 'no match', '8324544': 'electrical engineering', '8324547': 'geology', '8324546': 'french', '8324660': 'animal science', '8324661': 'education', '8422085': 'metallurgical engineering', '8324663': 'physics', '8324664': 'physics', '8324665': 'agronomy', '8324666': 'animal science', '8324667': 'computer science', '8422168': 'sociology', '8422169': 'education', '8422074': 'philosophy', '8422160': 'education', '8422161': 'anthropology', '8422162': 'chemistry', '8422163': 'animal science', '8422164': 'social work', '8422040': 'finance', '8422167': 'electrical engineering', '8422062': 'education', '8409819': 'education', '8409989': 'computer science', '8409988': 'psychology', '8422014': 'geography', '8422015': 'plant pathology', '8422017': 'mathematics', '8422010': 'ceramic engineering', '8422011': 'linguistics', '8422012': 'veterinary medical science', '8422013': 'physics', '8422018': 'no match', '8310014': 'biophysics', '8310015': 'atmospheric sciences', '8310016': 'communications', '8410038': 'physics', '8310010': 'musicology', '8310011': 'animal science', '8310012': 'education', '8310013': 'biophysics', '8410033': 'education', '8409798': 'education', '8410031': 'physical education', '8410030': 'physiology', '8310018': 'education', '8310019': 'electrical engineering', '8410035': 'animal science', '8410034': 'physics', '8409981': 'no match', '8409779': 'education', '8422070': 'english', '8409772': 'dairy science', '8409771': 'mathematics', '8409776': 'electrical engineering', '8409777': 'chemistry', '8409774': 'communications', '8409952': 'psychology', '8409953': 'education', '8409950': 'accountancy', '8409951': 'physics', '8409956': 'human resources', '8409954': 'computer science', '8409955': 'geology', '8409958': 'communications', '8409959': 'nuclear engineering', '8409984': 'microbiology', '8409794': 'business administration', '8409795': 'biochemistry', '8409796': 'education', '8409797': 'psychology', '8409790': 'education', '8409791': 'agronomy', '8409792': 'education', '8409793': 'physics', '8409813': 'chemistry', '8409812': 'plant pathology', '8409811': 'computer science', '8409810': 'labor', '8409817': 'nuclear engineering', '8409799': 'electrical engineering', '8409815': 'microbiology', '8409814': 'animal science', '8409927': 'biology', '8409926': 'chemistry', '8409925': 'aeronautical', '8409924': 'chemistry', '8409923': 'microbiology', '8409921': 'biology', '8409920': 'business administration', '8409929': 'computer science', '8409928': 'electrical engineering', '8409860': 'agronomy', '8422124': 'physical education', '8409971': 'education', '8422125': 'aeronautical', '8324611': 'animal science', '8324610': 'veterinary medical science', '8324613': 'physiology', '8324612': 'agricultural economics', '8324615': 'political science', '8324614': 'nuclear engineering', '8324617': 'education', '8324616': 'physics', '8422126': 'physics', '8324618': 'veterinary medical science', '8422058': 'business administration', '8422059': 'business administration', '8422113': 'chemistry', '8422115': 'aeronautical', '8422117': 'physics', '8422116': 'environmental science', '8422050': 'education', '8422051': 'biochemistry', '8422052': 'psychology', '8422053': 'geology', '8422056': 'french', '8422057': 'civil engineering', '8309986': 'plant pathology', '8309987': 'no match', '8309989': 'biochemistry', '8324504': 'speech', '8324507': 'physics', '8324506': 'chemistry', '8324501': 'chemistry', '8324500': 'education', '8324503': 'education', '8324509': 'geology', '8324508': 'no match', '8422123': 'labor', '8410064': 'psychology', '8410065': 'biochemistry', '8410066': 'biochemistry', '8410067': 'physios', '8410060': 'psychology', '8410048': 'veterinary medical science', '8410062': 'mechanical engineering', '8410063': 'business administration', '8410068': 'physics', '8410069': 'mathematics', '8409743': 'physics', '8409742': 'electrical engineering', '8409740': 'communications', '8409746': 'veterinary medical science', '8409745': 'camistry', '8409744': 'chemistry', '8422133': 'physics', '8409749': 'library', '8409748': 'biochemistry', '8422122': 'health', '8422038': 'microbiology', '8422064': 'english', '8422039': 'political science', '8422067': 'education', '8409844': 'chemistry', '8409845': 'german', '8409846': 'no match', '8409847': 'psychology', '8409840': 'economics', '8409841': 'history', '8409842': 'psychology', '8409843': 'mathematics', '8409962': 'slavic languages', '8409960': 'education', '8409967': 'agricultural economics', '8409849': 'nuclear engineering', '8409965': 'education', '8422060': 'agricultural engineering', '8422149': 'sociology', '8324608': 'agronomy', '8422032': 'physical education', '8324609': 'chemical engineering', '8422033': 'agronomy', '8409996': 'education', '8409997': 'acoountanoy', '8409994': 'physics', '8409995': 'labor', '8409992': 'nutritional sciences', '8409993': 'business administration', '8409990': 'physiology', '8409991': 'finance', '8409998': 'food science', '8409999': 'no match', '8422069': 'civil engineering', '8324601': 'agronomy', '8409970': 'history', '8422066': 'ceramic engineering', '8422805': 'agronomy', '8422804': 'computer science', '8422803': 'economics', '8422802': 'mathematics', '8422801': 'horticulture', '8422800': 'theoretical'}
    testTrainingDataDict={'agricultural engineering': 3, 'botany': 2, 'eoonomios': 1, 'political science': 4, 'metallurgical engineering': 12, 'business administration': 9, 'physios': 2, 'human resources': 3, 'economxcs': 1, 'library': 5, 'animal science': 12, 'leisure studies': 2, 'spanish': 5, 'agronomy': 17, 'education': 74, 'veterinary medical science': 14, 'physical education': 7, 'horticulture': 5, 'linguistics': 2, 'agricultural economici': 1, 'sociology': 6, 'genetics': 3, 'psychology': 28, 'mechanical engineering': 9, 'communications': 7, 'biochemistry': 14, 'speech': 3, 'environmental science': 1, 'nuclear engineering': 13, 'microbiology': 8, 'educati': 1, 'labor': 7, 'german': 2, 'health': 4, 'computer science': 20, 'plant pathology': 12, 'mathematics': 12, 'speech communication': 2, 'geography': 3, 'theoretical': 4, 'accountancy': 14, 'agricultural economics': 6, 'biology': 11, 'philosophy': 6, 'camistry': 1, 'finance': 5, 'theatre': 2, 'geology': 9, 'nutritional': 1, 'entomology': 4, 'mathematios': 1, 'french': 3, 'biophysics': 5, 'anthropology': 2, 'chemical engineering': 9, 'comparative literature': 2, 'socx&amp;l work': 1, 'astronomy': 2, 'physiology': 8, 'acoountanoy': 1, 'musicology': 2, 'plant biology': 2, 'atmospheric sciences': 1, 'ceramic engineering': 2, 'english': 7, 'environmental engineering': 1, 'economics': 9, 'nutritional sciences': 6, 'slavic languages': 2, 'food science': 4, 'dairy science': 4, 'civil engineering': 16, 'aeronautical': 6, 'eleotrical engineering': 2, 'social work': 2, 'electrical engineering': 31, 'electrical engineer': 2, 'chemistry': 53, 'physics': 42, 'sla': 1, 'history': 6}
    #fileData=ProcessETDs(filePath)
    fileData=testProcessETDs(filePath, testFileDict, testTrainingDataDict)
    #fileData.getTextBetweenTwoStrings('doctor of philosophy in', 'in the', 'no match')
    print fileData.fileDict
    print fileData.trainingDataDict
    fileData.cleanTrainingData('no match')
    fileData.checkForAlternateString('doctor of education in music education', 'music education', 'no match')
    fileData.checkForAlternateString('doctor of education', 'education', 'no match')
    fileData.checkForAlternateString('doctor of musical arts', 'music', 'no match')
    #fileData.findTrainingTextBetweenTwoStrings('philosophy in', '</page>', 'no match', 3)
    fileCount=0.0
    badSeedCount=0.0
    for key in fileData.fileDict.keys():
        fileCount+=1.0
        if fileData.fileDict[key]=='no match':
            badSeedCount+=1.0
    recall=badSeedCount/fileCount
            
    print fileData.fileDict
    print fileData.trainingDataDict
    print "fake recall equals: "
    print recall
    return fileData.fileDict
    


fileDict=runModuleForIdeals(r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro5\Illinois_5_2")    
addToCSV(r"\\libgrsurya\IDEALS_ETDS\ETD_Metadata_Files\Retro5_Metadata\Illinois_Retro5_MARCDATA.csv", fileDict)
#addToCSV(r"C:\Users\srobbins\Desktop\test.csv", fileDict)
  
    
    

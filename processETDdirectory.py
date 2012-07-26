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
                #print 'testing'+fileKey
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
                        #print fileKey+' is '+self.fileDict[fileKey]
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
        lines.append(line.split(','))
    CSVfile.close()
    for i, line in enumerate(lines):
        for j, word in enumerate(line):
            if word[-1]=='\n':
                line[j]=word[:-1]
                print "changed"+word
                print line
            
        if i==0:
            if line[-1]!='"department name"':
                line.append('"department name"')
        else:
            CSVid=line[1][4:11]
            print CSVid
            if CSVid in fileDict.keys():
                line.append('"'+fileDict[CSVid]+'"')
                print line
    CSVfile=open(r"C:\Users\srobbins\Desktop\test.csv", 'w')
    for line in lines:
        for i, word in enumerate(line):
            if i==0:
                CSVfile.write(word+',')
            elif i==(len(line)-1):
                CSVfile.write(word+'\n')
            else:
                CSVfile.write(word+',')
    
        
    

def runModuleForIdeals(filePath):
    #test data for retro1
    testTrainingDataDict={'botany': 13, 'chhmistlly': 1, 'metallurgical engineering': 3, 'animal nutrition': 10, 'dairy technology': 2, 'agronomy \xe2\x80\xa2': 1, 'physico-chemical biology': 2, 'animal science': 17, 'engineering': 11, 'the department': 1, 'spanish': 6, 'zoology': 14, 'agronomy': 10, 'education': 13, 'classical philology': 3, 'geography': 4, 'horticulture': 1, 'statistics': 2, "dairy' science": 1, 'psychology': 34, 'mechanical engineering': 1, 'electrioal engineering': 1, 'chemical enfilneering': 1, 'business': 2, 'german': 1, 'speech': 14, 'plant pathology': 7, 'mathematics': 13, 'physical education': 2, 'food technology': 15, 'electrical engineeking': 1, 'accountancy': 8, 'agricultural economics': 11, 'entomology': 11, 'dairy science': 5, 'geology': 8, 'philosophy': 3, 'french': 2, 'sociology': 3, 'physiology \xe2\x80\xa2head': 1, 'chemical engineering': 17, 'political science': 8, 'mass communications': 7, 'physiology': 7, 'ceramics': 1, 'sanitary engineering': 1, 'electrical engineeiung': 1, 'ceramic engineering': 2, 'psyohology': 1, 'ohbm1stby': 1, 'economics': 21, 'library science': 2, '.engineering1': 1, 'theoretical': 5, 'civil engineering': 2, 'aguonomy': 1, 'english': 13, 'bacteriology': 10, 'electrical engineering': 25, 'chemistry': 65, 'physics': 39, 'history': 5}
    testFileDict={'0007848': 'political science', '0007849': 'philosophy', '0007846': 'chemistry', '0007847': 'bacteriology', '0007844': 'chemistry', '0007845': 'psychology', '0007842': 'education', '0007843': 'plant pathology', '0007840': 'physics', '0007841': 'electrical engineering', '0010554': 'mass communications', '0010555': 'chemistry', '0010556': 'psychology', '0010557': 'chemistry', '0010550': 'electrical engineering', '0010551': 'classical philology', '0010552': 'chemistry', '0010553': 'dairy science', '0010558': 'mathematics', '0010559': 'animal science', '0011552': 'agricultural economics', '0011498': 'engineering', '0011499': 'accountancy', '0010499': 'chemistry', '0011491': 'food technology', '0011496': 'animal science', '0011497': 'english', '0011494': 'mass communications', '0010498': 'speech', '0009088': 'animal nutrition', '0009089': 'no match', '0009084': 'economics', '0009085': 'chemistry', '0009087': 'education', '0009080': 'accountancy', '0010497': 'chemistry', '0009082': 'economics', '0009083': 'psychology', '0006959': 'psychology', '0006958': 'bacteriology', '0006953': 'food technology', '0006952': 'entomology', '0006951': 'education', '0006950': 'economics', '0006957': 'speech', '0006956': 'animal science', '0006955': 'psychology', '0006954': 'food technology', '0007008': 'electrical engineering', '0009031': 'physics', '0009030': 'physics', '0009033': 'dairy science', '0009032': 'engineering', '0009035': 'economics', '0009034': 'political science', '0009037': 'agricultural economics', '0009036': 'physics', '0009039': 'statistics', '0006939': 'no match', '0011550': 'bacteriology', '0009156': 'physics', '0009157': 'chemistry', '0009154': 'economics', '0009155': 'plant pathology', '0009152': 'english', '0009153': 'no match', '0009150': 'physiology', '0009151': 'botany', '0009158': 'electrical engineering', '0009159': 'chemistry', '0010451': 'no match', '0010450': 'education', '0010453': 'physiology', '0010455': 'botany', '0010457': 'no match', '0010456': 'no match', '0010459': 'physics', '0010511': 'psychology', '0010512': 'spanish', '0010513': 'no match', '0010514': 'education', '0010515': 'education', '0010516': 'agronomy \xe2\x80\xa2', '0010517': 'speech', '0011508': 'theoretical', '0011509': 'food technology', '0011504': 'electrical engineering', '0011505': 'psychology', '0011506': 'zoology', '0011507': 'agronomy', '0011500': 'chemical engineering', '0011501': 'chemical engineering', '0011502': 'food technology', '0011503': 'chemical engineering', '0007877': 'bacteriology', '0007876': 'classical philology', '0007875': 'engineering', '0007873': 'chemistry', '0007872': 'agricultural economics', '0007871': 'psychology', '0007870': 'entomology', '0007879': 'economics', '0007878': 'physics', '0006998': 'psychology', '0006997': 'economics', '0006996': 'chemistry', '0006995': 'bacteriology', '0006994': 'physiology \xe2\x80\xa2head', '0006993': 'engineering', '0006992': 'no match', '0006991': 'chemistry', '0006990': 'animal science', '0013469': 'physics', '0013468': 'geology', '0013461': 'zoology', '0013460': 'electrical engineering', '0013463': 'economics', '0013462': 'electrical engineering', '0013465': 'electrical engineering', '0013464': 'political science', '0013466': 'zoology', '0009075': 'engineering', '0009074': 'english', '0009077': 'agricultural economics', '0009076': 'civil engineering', '0009071': 'english', '0009070': 'physiology', '0009073': 'chemistry', '0009072': 'electrical engineering', '0009079': 'entomology', '0009078': 'animal nutrition', '0010468': 'mechanical engineering', '0007010': 'spanish', '0010469': 'electrical engineering', '0013519': 'mathematics', '0013518': 'ceramics', '0013515': 'no match', '0013514': 'history', '0013516': 'dairy technology', '0013511': 'physics', '0010458': 'electrical engineering', '0013513': 'physics', '0013512': 'mass communications', '0009118': 'no match', '0009119': 'animal science', '0009112': 'physics', '0009113': 'agronomy', '0009110': 'mathematics', '0009111': 'botany', '0009116': 'no match', '0009117': 'engineering', '0009114': 'economics', '0009115': 'physics', '0007839': 'no match', '0007838': 'plant pathology', '0009169': 'accountancy', '0009168': 'mathematics', '0007833': 'speech', '0007832': 'physics', '0007831': 'electrical engineeking', '0007830': 'chemistry', '0007837': 'french', '0007836': 'no match', '0007835': 'physiology', '0009160': 'electrical engineering', '0010561': 'no match', '0010560': 'economics', '0010563': 'spanish', '0010562': 'entomology', '0010565': 'no match', '0010564': 'chemistry', '0010567': 'english', '0010566': 'speech', '0010568': 'plant pathology', '0011523': 'plant pathology', '0011540': 'agronomy', '0011541': 'chemistry', '0011542': 'animal science', '0011543': 'psychology', '0011544': 'physics', '0011545': 'food technology', '0011546': 'chemistry', '0011548': 'agronomy', '0011549': 'electrical engineering', '0011493': 'economics', '0006949': 'bacteriology', '0006940': 'psychology', '0006941': 'speech', '0006943': 'chemistry', '0006944': 'political science', '0006945': 'food technology', '0006946': 'chemical engineering', '0011495': 'chemical engineering', '0007883': 'animal science', '0007880': 'ceramic engineering', '0007881': 'no match', '0007886': 'chemical enfilneering', '0007887': 'economics', '0007884': 'chemistry', '0007885': 'electrical engineering', '0009028': 'chemical engineering', '0009029': 'chemistry', '0009026': 'physics', '0009027': 'economics', '0009024': 'psychology', '0009025': 'chemistry', '0009023': 'speech', '0009123': 'accountancy', '0009122': 'mathematics', '0009121': 'chemistry', '0009120': 'food technology', '0009127': 'entomology', '0009126': 'psychology', '0009125': 'no match', '0009124': 'psychology', '0009129': 'no match', '0009128': 'library science', '0010525': 'physics', '0010524': 'english', '0010527': 'agronomy', '0010526': 'english', '0010521': 'plant pathology', '0010520': 'economics', '0010523': 'physics', '0010522': 'physics', '0010529': 'chemistry', '0010448': 'business', '0010449': 'chemistry', '0010446': 'education', '0010447': 'chemistry', '0010444': 'education', '0010445': 'english', '0010442': 'psychology', '0010443': 'agricultural economics', '0010440': 'no match', '0010441': 'animal science', '0011539': 'accountancy', '0011538': 'philosophy', '0011530': 'animal science', '0011533': 'food technology', '0011532': 'physics', '0011535': 'psychology', '0011534': 'chemistry', '0011537': 'no match', '0011536': 'zoology', '0007864': 'chemical engineering', '0007865': 'no match', '0007866': 'speech', '0007867': 'chemical engineering', '0007860': 'sociology', '0007861': 'geography', '0007862': 'metallurgical engineering', '0007863': 'food technology', '0007868': 'zoology', '0007869': 'chemical engineering', '0009069': 'chemistry', '0006988': 'theoretical', '0006989': 'physical education', '0006984': 'physics', '0006985': 'no match', '0006986': 'chemistry', '0006987': 'political science', '0006981': 'economics', '0006982': 'bacteriology', '0006983': 'english', '0013510': 'agricultural economics', '0009062': 'chemistry', '0009063': 'botany', '0009060': 'mathematics', '0009061': 'chemistry', '0009066': 'chemistry', '0009067': 'education', '0009064': 'psychology', '0009065': 'chemistry', '0010495': 'electrical engineeiung', '0010494': 'speech', '0009068': 'engineering', '0010496': 'geology', '0010491': 'electrical engineering', '0010490': 'speech', '0010493': 'geology', '0010492': 'history', '0006933': 'chemistry', '0007009': 'food technology', '0006935': 'bacteriology', '0006934': 'geography', '0006937': 'economics', '0006936': 'education', '0007002': 'dairy technology', '0006938': 'economics', '0007000': 'accountancy', '0007001': 'bacteriology', '0007006': 'theoretical', '0007007': 'chemical engineering', '0007004': 'electrioal engineering', '0007005': '.engineering1', '0013508': 'agricultural economics', '0013509': 'mathematics', '0013502': 'animal nutrition', '0013503': 'food technology', '0013500': 'chemistry', '0013501': 'agricultural economics', '0013506': 'physics', '0013507': 'accountancy', '0013504': 'chemistry', '0013505': 'chemistry', '0013489': 'english', '0013488': 'electrical engineering', '0013483': 'education', '0013482': 'zoology', '0013481': 'physics', '0013480': 'electrical engineering', '0013487': 'chemistry', '0013486': 'mathematics', '0013485': 'psychology', '0013484': 'history', '0013476': 'no match', '0013477': 'spanish', '0013474': 'no match', '0013475': 'no match', '0013472': 'psychology', '0013473': 'psychology', '0013470': 'speech', '0013471': 'classical philology', '0013478': 'physics', '0013479': 'agronomy', '0007828': 'plant pathology', '0007829': 'chemistry', '0007824': 'metallurgical engineering', '0007825': 'english', '0007826': 'sanitary engineering', '0007827': 'english', '0010475': 'entomology', '0010474': 'animal nutrition', '0010473': 'chemistry', '0010472': 'no match', '0010471': 'english', '0010470': 'chhmistlly', '0010479': 'animal science', '0010478': 'physics', '0006975': 'dairy science', '0006974': 'physics', '0006977': 'geography', '0006976': 'chemical engineering', '0006971': 'accountancy', '0006970': 'psychology', '0006973': 'chemistry', '0006972': 'physics', '0006979': 'zoology', '0006978': 'psychology', '0011522': 'physical education', '0011488': 'agricultural economics', '0013449': 'library science', '0013447': 'business', '0009059': 'physics', '0009058': 'zoology', '0009053': 'chemical engineering', '0009052': 'chemistry', '0009051': 'engineering', '0009050': 'physico-chemical biology', '0009057': 'chemistry', '0009056': 'economics', '0009055': 'chemistry', '0013533': 'french', '0013532': 'physics', '0013531': 'no match', '0013530': 'animal nutrition', '0013534': 'dairy science', '0009130': 'mathematics', '0009132': 'no match', '0009133': 'electrical engineering', '0009134': 'animal nutrition', '0009135': 'electrical engineering', '0009136': 'geology', '0009137': 'german', '0009138': 'entomology', '0009139': 'physics', '0010532': 'agronomy', '0010533': 'no match', '0010530': 'physiology', '0010531': 'botany', '0010536': 'history', '0010537': 'chemical engineering', '0010534': 'physico-chemical biology', '0010535': 'no match', '0010538': 'mathematics', '0010539': 'psyohology', '0010439': 'food technology', '0007851': 'physics', '0007853': 'entomology', '0007852': 'food technology', '0007855': 'no match', '0007854': 'agronomy', '0007857': 'geography', '0007856': 'geology', '0007859': 'electrical engineering', '0007858': 'animal nutrition', '0010547': 'aguonomy', '0010546': 'no match', '0010545': 'chemical engineering', '0010544': 'spanish', '0010543': 'agricultural economics', '0010541': 'psychology', '0010540': 'physics', '0010549': 'geology', '0010548': 'chemical engineering', '0010482': 'speech', '0010483': 'zoology', '0010480': 'botany', '0010481': 'chemistry', '0010486': 'political science', '0010487': 'engineering', '0011526': 'spanish', '0011527': 'chemistry', '0011524': 'geology', '0011525': 'mass communications', '0011489': 'entomology', '0009091': 'chemistry', '0011520': 'horticulture', '0011521': 'mass communications', '0011485': 'animal science', '0011487': 'theoretical', '0011486': 'speech', '0011528': 'bacteriology', '0010488': 'psychology', '0010489': 'botany', '0009099': 'chemistry', '0009098': 'chemical engineering', '0009097': 'dairy science', '0009096': 'chemistry', '0009095': 'mass communications', '0009094': 'no match', '0009093': 'philosophy', '0009092': 'geology', '0010484': 'speech', '0010485': 'chemistry', '0009167': 'chemistry', '0009166': 'engineering', '0009165': 'botany', '0009164': 'psychology', '0009163': 'mathematics', '0009162': 'mathematics', '0013498': "dairy' science", '0013499': 'electrical engineering', '0009161': 'physics', '0013490': 'animal science', '0013491': 'chemistry', '0013492': 'statistics', '0007834': 'no match', '0013494': 'chemistry', '0013495': 'chemistry', '0013496': 'sociology', '0013497': 'animal nutrition', '0009007': 'the department', '0009149': 'no match', '0009148': 'physics', '0009141': 'electrical engineering', '0009140': 'education', '0009143': 'physiology', '0009142': 'animal nutrition', '0009145': 'chemistry', '0009144': 'no match', '0009147': 'psychology', '0009146': 'psychology', '0010464': 'psychology', '0010509': 'chemistry', '0010467': 'chemistry', '0010460': 'botany', '0010461': 'chemistry', '0010462': 'sociology', '0010463': 'chemistry', '0010503': 'psychology', '0010502': 'botany', '0010501': 'agronomy', '0010500': 'botany', '0010507': 'botany', '0010506': 'botany', '0010505': 'physiology', '0010504': 'no match', '0011519': 'zoology', '0011518': 'economics', '0011517': 'physics', '0011516': 'animal science', '0011515': 'zoology', '0011514': 'electrical engineering', '0011513': 'psychology', '0011510': 'animal science', '0010518': 'metallurgical engineering', '0010519': 'mass communications', '0006962': 'physics', '0006963': 'psychology', '0006960': 'chemical engineering', '0006961': 'no match', '0006966': 'psychology', '0006967': 'chemistry', '0006964': 'political science', '0006965': 'no match', '0006968': 'no match', '0006969': 'chemistry', '0013458': 'psychology', '0013459': 'animal science', '0013454': 'animal nutrition', '0013455': 'food technology', '0013456': 'zoology', '0013457': 'animal science', '0013450': 'political science', '0013451': 'engineering', '0013452': 'psychology', '0013453': 'economics', '0009048': 'no match', '0009049': 'physics', '0013493': 'no match', '0009040': 'entomology', '0009041': 'physics', '0009042': 'history', '0009043': 'agricultural economics', '0009044': 'physics', '0009045': 'animal science', '0009046': 'chemistry', '0009047': 'no match', '0013520': 'economics', '0013521': 'mathematics', '0013522': 'no match', '0013523': 'civil engineering', '0013524': 'theoretical', '0013525': 'ohbm1stby', '0013526': 'education', '0013527': 'chemistry', '0013528': 'entomology', '0013529': 'electrical engineering', '0009109': 'electrical engineering', '0009108': 'ceramic engineering', '0009105': 'chemistry', '0009104': 'zoology', '0009107': 'zoology', '0009106': 'physics', '0009103': 'agronomy', '0009102': 'chemistry'}
    #testFileDict={'8324497': 'civil engineering', '8324496': 'education', '8324495': 'education', '8422156': 'labor', '8422151': 'linguistics', '8422099': 'education', '8324558': 'physics', '8422152': 'sla', '8324556': 'electrical engineering', '8324557': 'electrical engineering', '8324554': 'agricultural economics', '8324555': 'chemistry', '8324552': 'comparative literature', '8324553': 'nuclear engineering', '8324499': 'chemistry', '8324551': 'entomology', '8422150': 'genetics', '8422153': 'chemistry', '8422094': 'finance', '8409859': 'nutritional sciences', '8422095': 'metallurgical engineering', '8422096': 'theatre', '8422097': 'plant biology', '8422063': 'entomology', '8422090': 'communications', '8422091': 'no match', '8422021': 'electrical engineering', '8422020': 'psychology', '8422023': 'education', '8422022': 'civil engineering', '8422025': 'education', '8324550': 'comparative literature', '8422027': 'electrical engineering', '8422026': 'electrical engineering', '8422029': 'mathematios', '8422028': 'metallurgical engineering', '8422093': 'labor', '8410037': 'chemistry', '8310021': 'electrical engineering', '8310020': 'chemistry', '8310023': 'physios', '8310022': 'veterinary medical science', '8410020': 'nuclear engineering', '8410021': 'biochemistry', '8410022': 'agricultural engineering', '8410023': 'philosophy', '8410024': 'electrical engineering', '8410025': 'psychology', '8410026': 'chemistry', '8410027': 'education', '8324655': 'education', '8324654': 'electrical engineering', '8324657': 'mathematics', '8324651': 'civil engineering', '8324653': 'education', '8324659': 'business administration', '8324658': 'sociology', '8409868': 'physical education', '8409808': 'mathematics', '8409809': 'biophysics', '8409800': 'electrical engineering', '8409801': 'metallurgical engineering', '8409802': 'chemistry', '8409803': 'education', '8409804': 'chemistry', '8409805': 'accountancy', '8409807': 'agronomy', '8409893': 'accountancy', '8409892': 'agricultural engineering', '8409891': 'education', '8409890': 'metallurgical engineering', '8409897': 'education', '8409896': 'microbiology', '8409895': 'agronomy', '8409894': 'physics', '8409899': 'physiology', '8409861': 'civil engineering', '8422155': 'nutritional sciences', '8409934': 'labor', '8409936': 'biology', '8409937': 'psychology', '8409930': 'electrical engineer', '8409931': 'mechanical engineering', '8409932': 'economics', '8409933': 'biochemistry', '8409938': 'biology', '8409939': 'chemical engineering', '8422154': 'speech communication', '8422157': 'mechanical engineering', '8324589': 'chemistry', '8324588': 'social work', '8324585': 'entomology', '8324584': 'sociology', '8324587': 'history', '8324586': 'biology', '8324581': 'biochemistry', '8324582': 'geography', '8422137': 'nuclear engineering', '8422065': 'electrical engineering', '8324566': 'physical education', '8324565': 'no match', '8324564': 'biochemistry', '8324563': 'chemistry', '8324562': 'library', '8324561': 'musicology', '8324560': 'economxcs', '8324606': 'french', '8324605': 'no match', '8324602': 'physics', '8324603': 'no match', '8324569': 'education', '8324568': 'physics', '8422108': 'psychology', '8422106': 'metallurgical engineering', '8422107': 'microbiology', '8422104': 'agronomy', '8422105': 'nutritional sciences', '8422102': 'chemistry', '8422103': 'chemistry', '8422101': 'physiology', '8324513': 'horticulture', '8324510': 'agronomy', '8324511': 'education', '8324516': 'biochemistry', '8324517': 'horticulture', '8324515': 'education', '8324518': 'chemical engineering', '8324519': 'physics', '8422134': 'mathematics', '8410050': 'english', '8410053': 'education', '8410052': 'animal science', '8410057': 'physics', '8410059': 'business administration', '8410058': 'no match', '8409751': 'physics', '8409753': 'mathematics', '8409754': 'biochemistry', '8409755': 'history', '8409756': 'electrical engineering', '8409758': 'english', '8409759': 'physics', '8409870': 'chemistry', '8409872': 'nutritional', '8409875': 'physics', '8409874': 'physics', '8409877': 'mathematics', '8409876': 'veterinary medical science', '8409879': 'biology', '8409878': 'physical education', '8409972': 'health', '8409973': 'chemistry', '8409974': 'civil engineering', '8409975': 'environmental engineering', '8409976': 'veterinary medical science', '8409977': 'physics', '8422092': 'agricultural economics', '8422131': 'biophysics', '8502064': 'physics', '8502065': 'no match', '8502066': 'chemistry', '8502060': 'entomology', '8502061': 'veterinary medical science', '8502062': 'psychology', '8502063': 'chemistry', '8422130': 'aeronautical', '8409983': 'aeronautical', '8422793': 'biology', '8422792': 'plant pathology', '8422791': 'computer science', '8422797': 'mechanical engineering', '8422796': 'computer science', '8422794': 'genetics', '8422799': 'education', '8422798': 'physics', '8422159': 'geology', '8422142': 'education', '8410028': 'chemical engineering', '8324529': 'education', '8422146': 'health', '8422147': 'chemistry', '8422144': 'electrical engineering', '8410029': 'biochemistry', '8324523': 'education', '8324522': 'genetics', '8324521': 'political science', '8324520': 'agronomy', '8422158': 'chemistry', '8324526': 'horticulture', '8324525': 'economics', '8324524': 'education', '8422783': 'agronomy', '8422111': 'theoretical', '8422110': 'spanish', '8324637': 'nutritional sciences', '8324636': 'communications', '8324634': 'electrical engineering', '8324633': 'education', '8324632': 'metallurgical engineering', '8324630': 'english', '8324639': 'psychology', '8324638': 'geology', '8410015': 'education', '8410014': 'education', '8410017': 'psychology', '8410016': 'chemistry', '8410011': 'education', '8422132': 'food science', '8410013': 'accountancy', '8410012': 'computer science', '8422035': 'computer science', '8410019': 'spanish', '8410018': 'civil engineering', '8422030': 'education', '8422031': 'history', '8324642': 'mechanical engineering', '8324549': 'history', '8324640': 'accountancy', '8324641': 'chemistry', '8324646': 'plant pathology', '8324647': 'agricultural economics', '8324644': 'civil engineering', '8324645': 'physiology', '8324648': 'chemistry', '8324649': 'metallurgical engineering', '8409835': 'chemistry', '8409834': 'computer science', '8409836': 'education', '8409830': 'electrical engineering', '8409833': 'no match', '8409832': 'psychology', '8422083': 'computer science', '8409839': 'nuclear engineering', '8409838': 'chemistry', '8422129': 'chemistry', '8422082': 'education', '8422081': 'education', '8422080': 'aeronautical', '8422139': 'animal science', '8409979': 'physiology', '8409880': 'accountancy', '8409882': 'anthropology', '8409883': 'biophysics', '8409884': 'english', '8409885': 'chemical engineering', '8409886': 'electrical engineering', '8409887': 'human resources', '8409889': 'metallurgical engineering', '8410040': 'education', '8409901': 'agronomy', '8409900': 'physics', '8409903': 'electrical engineering', '8409905': 'health', '8409904': 'animal science', '8409907': 'physical education', '8409906': 'philosophy', '8409909': 'physics', '8409908': 'nuclear engineering', '8422166': 'chemistry', '8324540': 'plant pathology', '8324598': 'computer science', '8324599': 'education', '8324593': 'nuclear engineering', '8324590': 'theoretical', '8324591': 'economics', '8324596': 'nuclear engineering', '8324597': 'chemistry', '8324594': 'computer science', '8324595': 'astronomy', '8324574': 'chemistry', '8324575': 'civil engineering', '8324679': 'chemical engineering', '8324678': 'no match', '8324570': 'psychology', '8422077': 'economics', '8324572': 'plant pathology', '8324573': 'physics', '8324672': 'plant pathology', '8324671': 'education', '8324670': 'electrical engineering', '8324677': 'theoretical', '8324676': 'veterinary medical science', '8324674': 'physics', '8422179': 'dairy science', '8422178': 'chemistry', '8422173': 'biology', '8422171': 'physics', '8422176': 'civil engineering', '8422175': 'education', '8422174': 'computer science', '8422087': 'socx&amp;l work', '8324680': 'mathematics', '8324681': 'electrical engineering', '8410036': 'accountancy', '8422182': 'nuclear engineering', '8422180': 'food science', '8422181': 'electrical engineering', '8310006': 'chemistry', '8310005': 'accountancy', '8310003': 'psychology', '8310002': 'biochemistry', '8310001': 'mechanical engineering', '8310000': 'psychology', '8410047': 'computer science', '8410044': 'economics', '8410045': 'accountancy', '8410042': 'education', '8410043': 'psychology', '8310009': 'civil engineering', '8410041': 'physics', '8422136': 'geography', '8409769': 'philosophy', '8409765': 'education', '8409764': 'veterinary medical science', '8409767': 'no match', '8409766': 'metallurgical engineering', '8409761': 'no match', '8409760': 'botany', '8409763': 'chemistry', '8409762': 'chemistry', '8409945': 'accountancy', '8409944': 'civil engineering', '8409947': 'education', '8409946': 'botany', '8409941': 'physics', '8409940': 'plant pathology', '8409943': 'no match', '8409942': 'no match', '8409949': 'no match', '8409787': 'finance', '8409786': 'plant biology', '8409785': 'no match', '8409784': 'education', '8409782': 'physics', '8409781': 'chemistry', '8409780': 'civil engineering', '8409866': 'library', '8409867': 'eleotrical engineering', '8409864': 'veterinary medical science', '8409865': 'physics', '8409863': 'plant pathology', '8409789': 'computer science', '8409788': 'eleotrical engineering', '8502058': 'human resources', '8502053': 'education', '8502052': 'physiology', '8502055': 'finance', '8502054': 'education', '8502057': 'education', '8502056': 'animal science', '8324548': 'dairy science', '8409898': 'education', '8422784': 'education', '8422785': 'psychology', '8422786': 'sociology', '8422787': 'metallurgical engineering', '8422788': 'chemistry', '8324538': 'accountancy', '8324539': 'spanish', '8324530': 'leisure studies', '8324531': 'computer science', '8324533': 'labor', '8324534': 'speech communication', '8324535': 'electrical engineering', '8324537': 'communications', '8409919': 'philosophy', '8324624': 'philosophy', '8324625': 'speech', '8324626': 'leisure studies', '8324627': 'education', '8324620': 'chemistry', '8324621': 'civil engineering', '8324622': 'education', '8324628': 'chemistry', '8324629': 'chemical engineering', '8410002': 'theatre', '8410003': 'psychology', '8410000': 'chemistry', '8410001': 'psychology', '8410006': 'agronomy', '8410007': 'accountancy', '8410004': 'german', '8410005': 'no match', '8422043': 'civil engineering', '8422042': 'electrical engineering', '8410008': 'mechanical engineering', '8410009': 'agronomy', '8422047': 'economics', '8422046': 'chemistry', '8422044': 'education', '8309993': 'plant pathology', '8309992': 'education', '8309991': 'speech', '8309990': 'chemistry', '8309997': 'business administration', '8309996': 'veterinary medical science', '8309995': 'spanish', '8309994': 'geology', '8309999': 'agricultural economics', '8422049': 'geology', '8410032': 'education', '8422121': 'education', '8409822': 'library', '8409823': 'computer science', '8409820': 'education', '8409821': 'electrical engineering', '8409826': 'animal science', '8409827': 'psychology', '8409824': 'education', '8409825': 'nutritional sciences', '8409453': 'chemistry', '8409980': 'mathematics', '8409828': 'physics', '8409982': 'no match', '8409985': 'veterinary medical science', '8324576': 'chemistry', '8409987': 'accountancy', '8409986': 'slavic languages', '8422071': 'dairy science', '8422076': 'english', '8422041': 'physics', '8410077': 'electrical engineering', '8410076': 'psychology', '8410075': 'mechanical engineering', '8410074': 'chemistry', '8410073': 'physics', '8410072': 'agricultural economici', '8410071': 'physics', '8422128': 'psychology', '8422075': 'nuclear engineering', '8410078': 'microbiology', '8410039': 'horticulture', '8409738': 'psychology', '8409739': 'library', '8422079': 'chemical engineering', '8324578': 'political science', '8422119': 'biology', '8324579': 'chemistry', '8409857': 'electrical engineering', '8409856': 'plant pathology', '8409855': 'eoonomios', '8409854': 'metallurgical engineering', '8409853': 'mechanical engineering', '8409852': 'sociology', '8409851': 'geology', '8409850': 'agronomy', '8409916': 'computer science', '8409917': 'microbiology', '8409914': 'biology', '8409915': 'economics', '8409912': 'electrical engineer', '8409913': 'psychology', '8409910': 'accountancy', '8409858': 'chemical engineering', '8422118': 'food science', '8409968': 'astronomy', '8422143': 'education', '8422140': 'biology', '8409966': 'spanish', '8422148': 'chemistry', '8324541': 'no match', '8324669': 'education', '8324543': 'educati', '8324542': 'physics', '8324545': 'no match', '8324544': 'electrical engineering', '8324547': 'geology', '8324546': 'french', '8324660': 'animal science', '8324661': 'education', '8422085': 'metallurgical engineering', '8324663': 'physics', '8324664': 'physics', '8324665': 'agronomy', '8324666': 'animal science', '8324667': 'computer science', '8422168': 'sociology', '8422169': 'education', '8422074': 'philosophy', '8422160': 'education', '8422161': 'anthropology', '8422162': 'chemistry', '8422163': 'animal science', '8422164': 'social work', '8422040': 'finance', '8422167': 'electrical engineering', '8422062': 'education', '8409819': 'education', '8409989': 'computer science', '8409988': 'psychology', '8422014': 'geography', '8422015': 'plant pathology', '8422017': 'mathematics', '8422010': 'ceramic engineering', '8422011': 'linguistics', '8422012': 'veterinary medical science', '8422013': 'physics', '8422018': 'no match', '8310014': 'biophysics', '8310015': 'atmospheric sciences', '8310016': 'communications', '8410038': 'physics', '8310010': 'musicology', '8310011': 'animal science', '8310012': 'education', '8310013': 'biophysics', '8410033': 'education', '8409798': 'education', '8410031': 'physical education', '8410030': 'physiology', '8310018': 'education', '8310019': 'electrical engineering', '8410035': 'animal science', '8410034': 'physics', '8409981': 'no match', '8409779': 'education', '8422070': 'english', '8409772': 'dairy science', '8409771': 'mathematics', '8409776': 'electrical engineering', '8409777': 'chemistry', '8409774': 'communications', '8409952': 'psychology', '8409953': 'education', '8409950': 'accountancy', '8409951': 'physics', '8409956': 'human resources', '8409954': 'computer science', '8409955': 'geology', '8409958': 'communications', '8409959': 'nuclear engineering', '8409984': 'microbiology', '8409794': 'business administration', '8409795': 'biochemistry', '8409796': 'education', '8409797': 'psychology', '8409790': 'education', '8409791': 'agronomy', '8409792': 'education', '8409793': 'physics', '8409813': 'chemistry', '8409812': 'plant pathology', '8409811': 'computer science', '8409810': 'labor', '8409817': 'nuclear engineering', '8409799': 'electrical engineering', '8409815': 'microbiology', '8409814': 'animal science', '8409927': 'biology', '8409926': 'chemistry', '8409925': 'aeronautical', '8409924': 'chemistry', '8409923': 'microbiology', '8409921': 'biology', '8409920': 'business administration', '8409929': 'computer science', '8409928': 'electrical engineering', '8409860': 'agronomy', '8422124': 'physical education', '8409971': 'education', '8422125': 'aeronautical', '8324611': 'animal science', '8324610': 'veterinary medical science', '8324613': 'physiology', '8324612': 'agricultural economics', '8324615': 'political science', '8324614': 'nuclear engineering', '8324617': 'education', '8324616': 'physics', '8422126': 'physics', '8324618': 'veterinary medical science', '8422058': 'business administration', '8422059': 'business administration', '8422113': 'chemistry', '8422115': 'aeronautical', '8422117': 'physics', '8422116': 'environmental science', '8422050': 'education', '8422051': 'biochemistry', '8422052': 'psychology', '8422053': 'geology', '8422056': 'french', '8422057': 'civil engineering', '8309986': 'plant pathology', '8309987': 'no match', '8309989': 'biochemistry', '8324504': 'speech', '8324507': 'physics', '8324506': 'chemistry', '8324501': 'chemistry', '8324500': 'education', '8324503': 'education', '8324509': 'geology', '8324508': 'no match', '8422123': 'labor', '8410064': 'psychology', '8410065': 'biochemistry', '8410066': 'biochemistry', '8410067': 'physios', '8410060': 'psychology', '8410048': 'veterinary medical science', '8410062': 'mechanical engineering', '8410063': 'business administration', '8410068': 'physics', '8410069': 'mathematics', '8409743': 'physics', '8409742': 'electrical engineering', '8409740': 'communications', '8409746': 'veterinary medical science', '8409745': 'camistry', '8409744': 'chemistry', '8422133': 'physics', '8409749': 'library', '8409748': 'biochemistry', '8422122': 'health', '8422038': 'microbiology', '8422064': 'english', '8422039': 'political science', '8422067': 'education', '8409844': 'chemistry', '8409845': 'german', '8409846': 'no match', '8409847': 'psychology', '8409840': 'economics', '8409841': 'history', '8409842': 'psychology', '8409843': 'mathematics', '8409962': 'slavic languages', '8409960': 'education', '8409967': 'agricultural economics', '8409849': 'nuclear engineering', '8409965': 'education', '8422060': 'agricultural engineering', '8422149': 'sociology', '8324608': 'agronomy', '8422032': 'physical education', '8324609': 'chemical engineering', '8422033': 'agronomy', '8409996': 'education', '8409997': 'acoountanoy', '8409994': 'physics', '8409995': 'labor', '8409992': 'nutritional sciences', '8409993': 'business administration', '8409990': 'physiology', '8409991': 'finance', '8409998': 'food science', '8409999': 'no match', '8422069': 'civil engineering', '8324601': 'agronomy', '8409970': 'history', '8422066': 'ceramic engineering', '8422805': 'agronomy', '8422804': 'computer science', '8422803': 'economics', '8422802': 'mathematics', '8422801': 'horticulture', '8422800': 'theoretical'}
    #testTrainingDataDict={'agricultural engineering': 3, 'botany': 2, 'eoonomios': 1, 'political science': 4, 'metallurgical engineering': 12, 'business administration': 9, 'physios': 2, 'human resources': 3, 'economxcs': 1, 'library': 5, 'animal science': 12, 'leisure studies': 2, 'spanish': 5, 'agronomy': 17, 'education': 74, 'veterinary medical science': 14, 'physical education': 7, 'horticulture': 5, 'linguistics': 2, 'agricultural economici': 1, 'sociology': 6, 'genetics': 3, 'psychology': 28, 'mechanical engineering': 9, 'communications': 7, 'biochemistry': 14, 'speech': 3, 'environmental science': 1, 'nuclear engineering': 13, 'microbiology': 8, 'educati': 1, 'labor': 7, 'german': 2, 'health': 4, 'computer science': 20, 'plant pathology': 12, 'mathematics': 12, 'speech communication': 2, 'geography': 3, 'theoretical': 4, 'accountancy': 14, 'agricultural economics': 6, 'biology': 11, 'philosophy': 6, 'camistry': 1, 'finance': 5, 'theatre': 2, 'geology': 9, 'nutritional': 1, 'entomology': 4, 'mathematios': 1, 'french': 3, 'biophysics': 5, 'anthropology': 2, 'chemical engineering': 9, 'comparative literature': 2, 'socx&amp;l work': 1, 'astronomy': 2, 'physiology': 8, 'acoountanoy': 1, 'musicology': 2, 'plant biology': 2, 'atmospheric sciences': 1, 'ceramic engineering': 2, 'english': 7, 'environmental engineering': 1, 'economics': 9, 'nutritional sciences': 6, 'slavic languages': 2, 'food science': 4, 'dairy science': 4, 'civil engineering': 16, 'aeronautical': 6, 'eleotrical engineering': 2, 'social work': 2, 'electrical engineering': 31, 'electrical engineer': 2, 'chemistry': 53, 'physics': 42, 'sla': 1, 'history': 6}
    #fileData=ProcessETDs(filePath)
    fileData=testProcessETDs(filePath, testFileDict, testTrainingDataDict)
    fileData.getTextBetweenTwoStrings('doctor of philosophy in', 'in', 'no match')
    print fileData.fileDict
    print fileData.trainingDataDict
    fileData.cleanTrainingData('no match')
    fileData.checkForAlternateString('doctor of education', 'education', 'no match')
    fileData.checkForAlternateString('doctor of musical arts', 'music', 'no match')
    print fileData.fileDict
    print fileData.trainingDataDict
    return fileData.fileDict
    


fileDict=runModuleForIdeals(r"\\libgrsurya\IDEALS_ETDS\ProQuestDigitization\Illinois_Retro1\Illinois_1_2")    
addToCSV(r"\\libgrsurya\IDEALS_ETDS\ETD_Metadata_Files\Retro1_Metadata\Illinois_Retro1_MARCDATA.csv", fileDict)
  
    
    

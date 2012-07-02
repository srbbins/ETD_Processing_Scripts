#!/usr/bin/env python2
class TrainingData(object):
    def __init__(self):
        self.trainingDataDict={}
        self.fileDict={}
       
    def detokenizeString(self, tokenList):
        detokenizedString=''
        for token in tokenList:
            detokenizedString+=token+' '
        return detokenizedString

    def getTextBetweenTwoStrings(self, tokenList, beginString, endString):#endstring needs to handle more than one token
        tokenCountForBeginString=len(beginString.split())
        writeToken=False
        for i, token in enumerate(tokenList):
            if i+tokenCountForBeginString<len(tokenList):
                testString=self.detokenizeString(tokenList[i:i+tokenCountForBeginString]).strip()
                if testString.lower()==beginString.lower():
                    markOne=i+tokenCountForBeginString
                    writeToken=True
            if writeToken==True and token.lower()==endString.lower() and i>markOne:
                markTwo=i
                return tokenList[markOne:markTwo]
        return ''

    def cleanTrainingData(self):pass
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

class metadataFinder(object):
    def __init__(self, someTrainingData, filePath):
        self.trainingData=someTrainingData
        self.filePath=filePath

    def edits1(self, word):#code adapted from Peter Norvig's code, found@ http://norvig.com/spell-correct.html 7/2/2012
        splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes    = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
        replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
        inserts    = [a + c + b     for a, b in splits for c in alphabet]
        return set(deletes + transposes + replaces + inserts)

    def testString
    #pregenerate edit1 list for all good entries in trainingData
    #determine based on some easy similarity metrics whether it's worth checking the edit1 data
    #determine based on further similarity metrics whether it's worth checking the edit1(edit1)data
    #use stoplist
    

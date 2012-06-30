#!/usr/bin/env python2
def processETDStrings(text):
    tokens=text.split()
    workingTokens=detokenizeString(getWorkingTokens(tokens))
    if workingTokens=='':
        workingTokens='no match'
    return workingTokens
    
def detokenizeString(tokenList):
    detokenizedString=''
    for token in tokenList:
        detokenizedString+=token+' '
    return detokenizedString

def getWorkingTokens(tokenList):
    writeToken=False
    workingTokens=[]
    for token in tokenList:
        if token.lower()=="submitted":
            writeToken=True
        if writeToken==True and token=="</page>":
            return workingTokens
        if writeToken==True:
            workingTokens.append(token)
    return workingTokens
            
            

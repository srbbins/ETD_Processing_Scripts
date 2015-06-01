def detokenizeString(tokenList):
    detokenizedString=''
    for i, token in enumerate(tokenList):
            if i==len(tokenList)-1:
                detokenizedString+=token.lower()
            else:
                detokenizedString+=token.lower()+' '
    return detokenizedString

def getEditDistance(word1, word2):
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
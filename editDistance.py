

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
    print distanceMatrix            
    return distanceMatrix[len(word1)][len(word2)]

def levenshtein(s1, s2):
    l1 = len(s1)
    l2 = len(s2)

    matrix = [range(l1 + 1)] * (l2 + 1)
    for zz in range(l2 + 1):
      matrix[zz] = range(zz,zz + l1 + 1)
    for zz in range(0,l2):
      for sz in range(0,l1):
        if s1[sz] == s2[zz]:
          matrix[zz+1][sz+1] = min(matrix[zz+1][sz] + 1, matrix[zz][sz+1] + 1, matrix[zz][sz])
        else:
          matrix[zz+1][sz+1] = min(matrix[zz+1][sz] + 1, matrix[zz][sz+1] + 1, matrix[zz][sz] + 1)
    print "That's the Levenshtein-Matrix for "+s1+" & "+s2+":"
    print matrix
    return matrix[l2][l1]

print getEditDistance("cat", "dog")
print levenshtein("cat", "dog")
print getEditDistance("sunday", "saturday")
print levenshtein("sunday", "saturday")
print getEditDistance("kitten", "sitting")
print levenshtein("kitten", "sitting")
print getEditDistance("sunday", "xxxxxx")
print levenshtein("sunday", "xxxxxx")
print getEditDistance("Democrats", "Republicans")
print levenshtein("Democrats", "Republicans")


import spacy 
# import quinductor
import nltk
from itertools import product
from nltk import word_tokenize, sent_tokenize
from spacy import displacy 
import re
import os
import json
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import math
WH_QUESTION = ['what', 'where', 'when', 'who', 'whom', 'whose', 'which', 'why', 'how']
CONV_QUESTION = ['is', 'are', 'was', 'were', 'do', 'does', 'did', 'has', 'have', 'had', 'can', 'could', 'shall', 'should', 'will', 'would', 'may', 'might', 'must']
nlp = spacy.load("en_core_web_sm")

def getNodesRelation(results, relations, node, dep = 'ROOT'):
    results[node] = dep
    if relations.get(node) is None:
        return
    for relation in relations[node]:
        getNodesRelation(results, relations, relation[0], dep+"."+str(relation[1])+"#"+str(relation[0]))

def getSentenceStructure(sentence):
    sentence = sentence.strip('.').lower()
    doc = nlp(sentence)
    root_idx = -1
    countRoot = 0
    relations = dict()
    for token in doc:
        if token.dep_ == 'ROOT':
            root_idx = token.i
            countRoot += 1
            continue
        relations[token.head.i] = relations.get(token.head.i, []) + [(token.i, token.dep_)]
    results = dict()
    if countRoot > 1 or root_idx == -1:
        return None, None
    getNodesRelation(results, relations, root_idx, 'ROOT' + '#' + str(root_idx) )
    return doc, results

def LLTE_Score(template):
    score = 0
    nums = []
    for item in template:
        if '#' in item and item.startswith('ROOT'):
            nums.append(int(item.strip(']').split('#')[-1]))
    for i in range(1, len(nums)):
        score += abs(nums[i] - nums[i-1]) 
    return score

def LLTE_Resolutions(templates):
    scores = [(template, LLTE_Score(template)) for template in templates]
    scores.sort(key = lambda x: x[1])
    # print(scores)
    # print("Best Template: ", scores[0][0], "Score: ", scores[0][1])
    return scores[0][0]

def getQuestionTemplate(results, doc, sentence, question):
    tamplate = []
    sentence = sentence.strip('.').lower()
    question = question.lower()
    # print(sentence)
    # print(question)
    question_doc = nlp(question)
    question_tokens = [token.lemma_ for token in question_doc]
    sentence_doc = nlp(sentence)
    sentence_tokens = [token.lemma_ for token in sentence_doc]
    for token in question_tokens:
        # print(token)
        if token in sentence_tokens:
            multi_nodes = []
            for idx, word in enumerate(sentence_tokens):
                if word == token:
                    # if results.get(idx) is None:
                        # print(idx, word, token, results)
                    multi_nodes.append(results.get(idx))
            if len(multi_nodes) > 1:
                # print(multi_nodes)
                multi_nodes = sorted(multi_nodes, key = lambda x: len(x.split('.')))
                tamplate.append(multi_nodes)
            else:
                tamplate.append(multi_nodes[0])
            # idx = sentence_tokens.index(token)
            # tamplate.append(results.get(idx))
        else:
            tamplate.append(token)
            
    # return tamplate
    elements = []
    total = 1
    for item in tamplate:
        if isinstance(item, list):
            elements.append(item)
            total *= len(item)
        else:
            elements.append([item])
        if total > 1000:
            return None
    tamplates = list(product(*elements))
    tamplates = [list(comb) for comb in tamplates]
    finalTamplate = LLTE_Resolutions(tamplates)
    return finalTamplate

def getAllSubNodes(results, node, generateQuestion = False):
    queue = [node]
    subnodes = []
    while queue:
        current = queue.pop(0)
        if current in subnodes:
            continue
        subnodes.append(current)
        node_idx = -1
        for idx, relation in results.items():
            if relation.startswith(current) and relation not in subnodes and relation not in queue:
                queue.append(relation)
    if not generateQuestion:
        subnodes = sorted(subnodes, key = lambda x: int(x.split('#')[-1]))
    return subnodes

def DCM(results):
    dcm = dict()
    for idx, relation in results.items():
        directChild = [relation+'*']
        for subnode in getAllSubNodes(results, relation):
            if relation.split('.') == subnode.split('.')[:-1] and len(relation.split('.')) == len(subnode.split('.')) - 1:
                if len(getAllSubNodes(results, subnode)) == 1:
                    directChild.append(subnode)
                else:
                    directChild.append(subnode + '*')
        dcm[relation] = directChild
    return dcm

def mergeNegatives(template, results):
    dcm = DCM(results)
    tokens = template.split()
    reducedTemplate = []
    for token in tokens:
        if token.count('-') > 1:
            token = token[1:-1]
            minus = token.split('-')[1:]
            for node, dc in dcm.items():
                if set(dc).issubset(set(minus)):
                    minus = [item for item in minus if item not in dc]
                    minus.append(node)
                    # newToken = '<' + token.split('-')[0] + '-' + '-'.join(newMinus) + '>'
                    # reducedTemplate.append(newToken)
                # else:
                #     reducedTemplate.append(token)
            newToken = '<' + token.split('-')[0] + '-' + '-'.join(minus) + '>'
            reducedTemplate.append(newToken)
        else:
            reducedTemplate.append(token)
            
    return ' '.join(reducedTemplate)

def ShiftReduce(results,template):
    stack = []
    queue = template.copy()
    while len(queue) > 0:
        head = queue.pop(0)
        # stack.append(head)
        if len(stack) >= 1:
            node1 = head
            node2 = stack[-1].split('-')[0]
            if node2.startswith('<'):
                node2 = node2[1:]
            r1 = node1.split('.')
            r2 = node2.split('.')
            idx = 0
            # if np.sum(np.array([1 for i in range(len(r1)) if r1[i].count('#') > 0])) != len(r1) or np.sum(np.array([1 for i in range(len(r2)) if r2[i].count('#') > 0])) != len(r2):
            #     stack.append(head)
            #     continue
            # if r1.count('#') == 0 or r2.count('#') == 0:
            #     stack.append(head)
            #     continue
            for i in range(min(len(r1), len(r2))):
                if '#' not in r1[i] or '#' not in r2[i]:
                    idx = 0
                    break
                if r1[i] != r2[i]:
                    break
                idx = i + 1
            if idx > 0 and abs(len(r1) - idx) <= 1 and abs(len(r2) - idx) <= 1:
                if stack[-1].count('-') > 0:
                    topStack = stack.pop()
                    if topStack.startswith('<'):
                        topStack = topStack[1:-1]
                    minus = topStack.split('-')[1:]
                    node = head if len(getAllSubNodes(results, head)) == 1 else head + '*' 
                    commonPrefix = '.'.join(r1[:idx])
                    newNode = '-'.join([m for m in minus if m != node])
                    if newNode == '':
                        stack.append('<' + commonPrefix + '>')
                    else:
                        stack.append('<' + commonPrefix + '-' +newNode + '>')
                else:
                    topStack1 = head
                    topStack2 = stack.pop()
                    if topStack2.startswith('<'):
                        topStack2 = topStack2[1:-1]
                    commonPrefix = '.'.join(r1[:idx])
                    subNodes = getAllSubNodes(results, commonPrefix)
                    for node in subNodes:
                        if node != topStack1 and node != topStack2:
                            if len(getAllSubNodes(results, node)) > 1:
                                node = node + '*'
                            commonPrefix += '-' + node
                    stack.append('<' + commonPrefix + '>') 
            else:
                stack.append(head)
        else:
            stack.append(head)
            
    questionTemplate = ''
    for item in stack:
        # if item.count('-') > 0:
        #     questionTemplate += f"<{item}>"
        if item.startswith('ROOT'):
            questionTemplate += f"[{item}]"
        else:
            questionTemplate += item
        questionTemplate += ' '
    return questionTemplate

def generalizeTemplate(template):
    pattern = re.compile('#[0-9]+')
    return pattern.sub('', template)

def generalizeResults(results):
    newResults = dict()
    pattern = re.compile('#[0-9]+')
    for key, value in results.items():
        newResults[key] = pattern.sub('', value)
    return newResults

def checkGaurds(sentence, gaurds):
    exists, isClause, hasClause = gaurds
    doc, results = getSentenceStructure(sentence)
    if results is None:
        return False
    results = generalizeResults(results)
    resultsInvers = {value: key for key, value in results.items()}
    for e in exists:
        if e not in results.values():
            return False
        
    if doc[resultsInvers.get('ROOT')].pos_ != isClause:
        return False
    
    if doc[resultsInvers.get('ROOT')].morph.to_dict() != hasClause:
        return False
    
    return True

def generateQuestion(sentence, template, gaurds, isAnswer = False):
    # if not isAnswer:
    if not checkGaurds(sentence, gaurds):
        return None
    doc, results = getSentenceStructure(sentence)
    template = generalizeTemplate(template)
    results = generalizeResults(results)
    resultsReverse = {v:k for k,v in results.items()}
    question = []
    for item in template.split():
        if item.startswith('<'):
            item = item[1:-1]
            if item.count('-') == 0:
                nodes = getAllSubNodes(results, item, True)
                # nodes = sorted(nodes, key = lambda x: int(x.split('#')[-1]))
                for node in nodes:
                    question.append(doc[resultsReverse[node]].text)
            else:
                nodes = item.split('-')
                allNodes = getAllSubNodes(results, nodes[0], True)
                for node in nodes[1:]:
                    if node.endswith('*'):
                        node = node[:-1]
                        allNodes = [n for n in allNodes if node != n]
                    else:
                        allSubNode = getAllSubNodes(results, node, True)
                        allNodes = [n for n in allNodes if n not in allSubNode]
                allNodes = sorted(allNodes, key = lambda x: resultsReverse[x])
                for node in allNodes:
                    question.append(doc[resultsReverse[node]].text)
        elif item.startswith('['):
            question.append(doc[resultsReverse[item[1:-1]]].text)
        else:
            question.append(item)
    return ' '.join(question)

def getGaurds(template, results, doc):
    results = generalizeResults(results)
    exists = set()
    hasClause = dict()
    resultsInverse = {v:k for k,v in results.items()}
    isClause = doc[resultsInverse['ROOT']].pos_
    hasClause = doc[resultsInverse['ROOT']].morph.to_dict()
    for item in template.split():
        if item.startswith('<'):
            item = item[1:-1]
            relation = item.split('-')[0]
            exists.add(relation)
        elif item.startswith('['):
            relation = item[1:-1]
            exists.add(relation)
    return exists, isClause, hasClause
        

def ngrams(context, unigram = dict(), bigram = dict(), trigram = dict(), wordCount = 0):
    sentences = sent_tokenize(context)
    for sentence in sentences:
        doc = nlp(sentence)
        tokens = [f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/') for token in doc]
        tokens.insert(0, '<s>')
        tokens.append('</s>')
        wordCount += len(tokens)
        gram1 = nltk.ngrams(tokens, 1)
        gram2 = nltk.ngrams(tokens, 2)
        gram3 = nltk.ngrams(tokens, 3)
        for k,v in nltk.FreqDist(gram1).items():
            unigram[k] = unigram.get(k, 0) + v
        for k,v in nltk.FreqDist(gram2).items():
            bigram[k] = bigram.get(k, 0) + v
        for k,v in nltk.FreqDist(gram3).items():
            trigram[k] = trigram.get(k, 0) + v
    return unigram, bigram, trigram, wordCount

def questionWord(question, answer, questionWordCount, questionCount):
    word = word_tokenize(question)[0].lower()
    if word in WH_QUESTION or word in CONV_QUESTION:
        doc = nlp(answer)
        rootToken = None
        for token in doc:
            if token.dep_ == 'ROOT':
                rootToken = f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/')
                
        questionCount[word] = questionCount.get(word, 0) + 1
        questionWordCount[(word, rootToken)] = questionWordCount.get((word, rootToken), 0) + 1
    return questionWordCount, questionCount

def calculateScore(question, unigram, bigram, trigram, wordCount, answer, questionWordCount, questionCount):
    lambda4 = 0.000001
    lambda3 = 0.01 - lambda4
    lambda2 = 0.1 - lambda3
    lambda1 = 0.9
    alpha = 0.8
    
    doc = nlp(question)
    tokens = [f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/') for token in doc]
    tokens.insert(0, '<s>')
    tokens.append('</s>')
    rNG = 0
    for i, token in enumerate(tokens):
        w1, w2, w3 = None, None, None
        w3 = token
        if i - 1 >= 0:
            w2 = tokens[i-1]
        if i - 2 >= 0:
            w1 = tokens[i-2]
            
        p3 = unigram.get((w3,), 0) / wordCount
        p2 = bigram.get((w2, w3), 0) / unigram.get((w2,), 1)
        p1 = trigram.get((w1, w2, w3), 0) / bigram.get((w1, w2), 1)
        
        rNG += lambda1 * p1 + lambda2 * p2 + lambda3 * p3 + lambda4
        
    rNG /= (len(tokens) - 2)
    
    doc = nlp(answer)
    rootToken = None
    for token in doc:
        if token.dep_ == 'ROOT':
            rootToken = f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/')
            
    word = word_tokenize(question)[0].lower()
    if questionWordCount.get((word, rootToken), 0) == 0:
        return 0
    rQW = questionWordCount.get((word, rootToken), 0) / (questionCount.get(word, 0) + 10e-10)
    score = alpha * rNG + (1 - alpha) * rQW
    return score

def checkTemplate(template, idf):
    template = ' '.join(template)
    template = template.replace('?', '')
    template = template.strip()
    words = template.split(' ')
    discardTemplate = False
    for word in words:
        if '#' not in word and word not in CONV_QUESTION and word not in WH_QUESTION:
            if word not in idf:
                discardTemplate = True
                break
            if idf[word] - 1 > math.log(4):
                discardTemplate = True
                break
    return discardTemplate

def generateTemplateGaurdsPair(sentence, question, idf, isAnswer = False):
    doc, results = getSentenceStructure(sentence)
    if results is None:
        return None, []
    template = getQuestionTemplate(results, doc, sentence, question)
    if template is None:
        return None, []
    if not isAnswer and checkTemplate(template, idf):
        return None, []
    template = ShiftReduce(results, template)
    template = mergeNegatives(template, results)
    template = generalizeTemplate(template)
    # if isAnswer:
    #     return template, []
    gaurds = getGaurds(template, results, doc)
    return template, gaurds

def getDataset(datasetPath):
    dataset = dict()
    with open(datasetPath) as jsonFile:
        dataset = json.load(jsonFile)
        jsonFile.close()
    return dataset

def get_sentence_containing_answer(context, answer_start):
    # Tokenize the context into sentences
    sentences = sent_tokenize(context)
    
    # Initialize start position for each sentence
    current_pos = 0
    
    # doc = nlp(context)
    
    for sentence in sentences:
        # sentence = sentence.text
        sentence_start = current_pos
        sentence_end = sentence_start + len(sentence)
        
        # Check if the answer_start falls within the sentence boundaries
        if sentence_start <= answer_start < sentence_end:
            return sentence
        
        # Update current position for the next sentence
        current_pos = sentence_end + 1  # +1 to account for the space or punctuation between sentences
    
    return None

def preProcessingTrainingSet(dataset):
    contexts = []
    questions = []
    answers = []
    sentences = []
    for d in dataset['data']:
        for paragraph in d['paragraphs']:
            contexts.append(paragraph['context'])
            q = []
            a = []
            s = []
            for qa in paragraph['qas']:
                if qa['is_impossible']:
                    continue
                sentence = get_sentence_containing_answer(paragraph['context'], qa['answers'][0]['answer_start'])
                if sentence is None:
                    continue
                s.append(sentence)
                a.append(qa['answers'][0]['text'])
                q.append(qa['question'])
                
            questions.append(q)
            answers.append(a)
            sentences.append(s)
    return contexts, questions, answers, sentences

def lemmatize(text):
    doc = nlp(text)
    lemmatized = [token.lemma_ for token in doc]
    return ' '.join(lemmatized)

def trainModel(contexts, questions, answers, sentences):
    unigram = dict()
    bigram = dict()
    trigram = dict()
    wordCount = 0
    questionWordCount = dict()
    questionCount = dict()
    questionTemplates = []
    answerTemplates = []
    questionGaurds = []
    answerGaurds = []
    
    vectorizer = TfidfVectorizer(preprocessor=lemmatize)
    vectorizer.fit_transform(contexts)
    feature_names = vectorizer.get_feature_names_out()
    idf_values = dict(zip(feature_names, vectorizer.idf_))
    
    for i in range(len(contexts)):
        if i % 100 == 0:
            print(f"Processing {i} out of {len(contexts)}")

        unigram, bigram, trigram, wordCount = ngrams(contexts[i], unigram, bigram, trigram, wordCount)

        for j in range(len(questions[i])):
            # print(sentences[i][j], questions[i][j], answers[i][j])
            questionTemplate, questionGaurd = generateTemplateGaurdsPair(sentences[i][j], questions[i][j], idf_values)
            if len(questionGaurd) == 0 or len(questionGaurd[0]) == 0:
                continue
            answerTemplate, answerGaurd = generateTemplateGaurdsPair(sentences[i][j], answers[i][j], None, True)
            if len(answerGaurd) == 0 or len(answerGaurd) == 0:
                continue
            questionWordCount, questionCount = questionWord(questions[i][j], answers[i][j], questionWordCount, questionCount)
            questionTemplates.append(questionTemplate)
            answerTemplates.append(answerTemplate)
            # templates.append(template)
            questionGaurds.append(questionGaurd)
            answerGaurds.append(answerGaurd)
        
    print("Training Completed")
    return unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGaurds, answerGaurds, questionWordCount, questionCount

def saveModel(res, modelFolderPath = 'Trained_Model'):
    unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGaurds, answerGaurds, questionWordCount, questionCount = res
    if not os.path.exists(modelFolderPath):
        os.makedirs(modelFolderPath)
    with open(modelFolderPath + '/' + 'unigram.json', 'wb') as jsonFile:
        pickle.dump(unigram, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'bigram.json', 'wb') as jsonFile:
        pickle.dump(bigram, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'trigram.json', 'wb') as jsonFile:
        pickle.dump(trigram, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionWordCount.json', 'wb') as jsonFile:
        pickle.dump(questionWordCount, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionCount.json', 'wb') as jsonFile:
        pickle.dump(questionCount, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionTemplates.json', 'wb') as jsonFile:
        pickle.dump(questionTemplates, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerTemplates.json', 'wb') as jsonFile:
        pickle.dump(answerTemplates, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionGaurds.json', 'wb') as jsonFile:
        pickle.dump(questionGaurds, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerGaurds.json', 'wb') as jsonFile:
        pickle.dump(answerGaurds, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'wordCount.json', 'wb') as jsonFile:
        pickle.dump(wordCount, jsonFile)
        jsonFile.close()
        
    print("Model Saved")

def loadModel(modelFolderPath = 'Trained_Model'):
    unigram = dict()
    bigram = dict()
    trigram = dict()
    wordCount = 0
    questionWordCount = dict()
    questionCount = dict()
    questionTemplates = []
    answerTemplates = []
    questionGaurds = []
    answerGaurds = []
    with open(modelFolderPath + '/' + 'unigram.json', 'rb') as jsonFile:
        unigram = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'bigram.json', 'rb') as jsonFile:
        bigram = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'trigram.json', 'rb') as jsonFile:
        trigram = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionWordCount.json', 'rb') as jsonFile:
        questionWordCount = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionCount.json', 'rb') as jsonFile:
        questionCount = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionTemplates.json', 'rb') as jsonFile:
        questionTemplates = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerTemplates.json', 'rb') as jsonFile:
        answerTemplates = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'questionGaurds.json', 'rb') as jsonFile:
        questionGaurds = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerGaurds.json', 'rb') as jsonFile:
        answerGaurds = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'wordCount.json', 'rb') as jsonFile:
        wordCount = pickle.load(jsonFile)
        jsonFile.close()
        
    print("Model Loaded")
    return unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGaurds, answerGaurds, questionWordCount, questionCount



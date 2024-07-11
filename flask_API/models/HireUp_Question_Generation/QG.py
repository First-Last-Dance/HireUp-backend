import spacy 
import nltk
from itertools import product
from nltk import word_tokenize, sent_tokenize
import re
import os
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import math
WH_QUESTION = ['what', 'where', 'when', 'who', 'whom', 'whose', 'which', 'why', 'how']
CONV_QUESTION = ['is', 'are', 'was', 'were', 'do', 'does', 'did', 'has', 'have', 'had', 'can', 'could', 'shall', 'should', 'will', 'would', 'may', 'might', 'must']
nlp = spacy.load("en_core_web_sm")

def getNodesRelation(setntence_structure, relations, node, dep='ROOT'):
    """
    Recursively traverses the dependency tree to extract the dependency relations of the nodes.

    Args:
        setntence_structure (dict): The dictionary to store the dependency relations of the nodes.
        relations (dict): The dictionary containing the relations between tokens.
        node (int): The index of the current node.
        dep (str): The dependency label of the current node.

    Returns:
        None
    """
    
    # Add the dependency relation of the current node to the dictionary
    setntence_structure[node] = dep
    # Recursively traverse the dependency tree to extract the dependency relations of the child nodes
    # Check if the current node has any child nodes
    if relations.get(node) is None:
        return
    # Iterate through the child nodes of the current node
    for relation in relations[node]:
        getNodesRelation(setntence_structure, relations, relation[0], dep + "." + str(relation[1]) + "#" + str(relation[0]))

def getSentenceStructure(sentence):
    """
    Analyzes the sentence structure using the spaCy library.

    Args:
        sentence (str): The input sentence.

    Returns:
        doc (spacy.tokens.doc.Doc): The spaCy document object representing the analyzed sentence.
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.
    """
    # Remove the trailing dot and convert the sentence to lowercase
    sentence = sentence.strip('.').lower()
    # Analyze the sentence using the spaCy library
    doc = nlp(sentence)
    # Initialize the index of the root node and the count of root nodes
    root_idx = -1
    countRoot = 0
    # Initialize the dictionary to store the dependency relations between tokens
    relations = dict()
    # Iterate through the tokens in the analyzed sentence
    for token in doc:
        # Check if the token is the root node
        if token.dep_ == 'ROOT':
            root_idx = token.i
            countRoot += 1
            continue
        # Add the dependency relation of the token to the dictionary
        relations[token.head.i] = relations.get(token.head.i, []) + [(token.i, token.dep_)]
        
    # Initialize the dictionary to store the dependency relations of the nodes
    setntence_structure = dict()
    # Check if the sentence has multiple root nodes or no root node
    if countRoot > 1 or root_idx == -1:
        return None, None
    # Extract the dependency relations of the nodes
    getNodesRelation(setntence_structure, relations, root_idx, 'ROOT' + '#' + str(root_idx) )
    # Return the spaCy document object and the dictionary representing the dependency relations of the tokens
    return doc, setntence_structure

def LLTE_Score(template):
    """
    Calculates the score of a template based on the absolute difference between the positions of the tokens in the template.

    Args:
        template (list): The template representing the dependency relations between tokens.

    Returns:
        score (int): The score of the template.
    """
    
    # Initialize the score and the list to store the positions of the tokens in the template
    score = 0
    nums = []
    # Iterate through the tokens in the template
    for item in template:
        # Check if the token is template expression not a constant word
        if '#' in item and item.startswith('ROOT'):
            # Append the ID of the token to the list
            nums.append(int(item.strip(']').split('#')[-1]))
    # Calculate the score based on the absolute difference between the positions of the tokens in the template
    for i in range(1, len(nums)):
        score += abs(nums[i] - nums[i-1]) 
    # Return the score
    return score

def LLTE_Resolutions(templates):
    """
    Calculates the LLTE score for each template and returns the template with the lowest score.

    Args:
        templates (list): A list of templates representing the dependency relations between tokens.

    Returns:
        str: The template with the lowest score.
    """
    # Calculate the LLTE score for each template
    scores = [(template, LLTE_Score(template)) for template in templates]
    # Sort the templates based on the LLTE score
    scores.sort(key = lambda x: x[1])
    # Return the template with the lowest score
    return scores[0][0]

def getQuestionTemplate(setntence_structure, doc, sentence, question):
    """
    Generates a question template based on the given sentence structure, document, sentence, and question.

    Args:
        setntence_structure (dict): A dictionary mapping each index in the sentence to its dependency relation.
        doc: The spaCy document object representing the analyzed sentence.
        sentence (str): The input sentence.
        question (str): The input question.

    Returns:
        finalTamplate: The generated question template.

    """

    tamplate = []
    # Remove the trailing dot and convert the sentence and question to lowercase
    sentence = sentence.strip('.').lower()
    question = question.lower()
    # Tokenize the sentence and question using the spaCy library and extract the lemmatized tokens
    question_doc = nlp(question)
    question_tokens = [token.lemma_ for token in question_doc]
    sentence_doc = nlp(sentence)
    sentence_tokens = [token.lemma_ for token in sentence_doc]

    # Iterate over each token in the question
    for token in question_tokens:
        # Check if the question token is present in the sentence
        if token in sentence_tokens:
            multi_nodes = []
            # Find all occurrences of the token in the sentence
            for idx, word in enumerate(sentence_tokens):
                if word == token:
                    multi_nodes.append(setntence_structure.get(idx))
            # Check if there are multiple occurrences of the token in the sentence
            if len(multi_nodes) > 1:
                # Sort the multi_nodes based on the number of levels in the sentence structure
                multi_nodes = sorted(multi_nodes, key=lambda x: len(x.split('.')))
                tamplate.append(multi_nodes)
            else:
                tamplate.append(multi_nodes[0])
        else:
            # Append the question token to the template as a constant word
            tamplate.append(token)
            
    elements = []
    total = 1
    # Generate all possible combinations of the template elements
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
    # Calculate the LLTE resolutions for each template
    finalTamplate = LLTE_Resolutions(tamplates)
    # Return the final template
    return finalTamplate

def getAllSubNodes(setntence_structure, node, generateQuestion=False):
    """
    Retrieves all the subnodes (All children nodes) of a given node in the sentence structure.

    Args:
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.
        node (str): The node for which to retrieve the subnodes.
        generateQuestion (bool): Flag indicating whether the function is used for generating a question template.

    Returns:
        list: A list of subnodes of the given node.
    """
    # Initialize the queue and the list to store the subnodes
    queue = [node]
    subnodes = []
    # Traverse the dependency tree to retrieve all the subnodes of the given node
    while queue:
        # Pop the current node from the queue
        current = queue.pop(0)
        # Check if the current node is already in the list of subnodes
        if current in subnodes:
            continue
        # Append the current node to the list of subnodes
        subnodes.append(current)
        node_idx = -1
        # Iterate through the nodes in the sentence structure
        for idx, relation in setntence_structure.items():
            # Check if the relation starts with the current node to find the child nodes of the current node
            if relation.startswith(current) and relation not in subnodes and relation not in queue:
                queue.append(relation)
    # Sort the subnodes based on the index of the nodes
    if not generateQuestion:
        subnodes = sorted(subnodes, key=lambda x: int(x.split('#')[-1]))
    # Return the subnodes
    return subnodes

def DCM(setntence_structure):
    """
    Creates a dictionary mapping each node in the sentence structure to its direct children.

    Args:
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.

    Returns:
        dict: A dictionary mapping each node to its direct children.
    """
    # Initialize the dictionary to store the direct children of each node
    dcm = dict()
    # Iterate through the nodes in the sentence structure
    for idx, relation in setntence_structure.items():
        # Initialize the list of direct children for the current node
        directChild = [relation+'*']
        # Iterate through the subnodes of the current node
        for subnode in getAllSubNodes(setntence_structure, relation):
            # Check if the subnode is a direct child of the current node
            if relation.split('.') == subnode.split('.')[:-1] and len(relation.split('.')) == len(subnode.split('.')) - 1:
                # Check if the subnode has no child
                if len(getAllSubNodes(setntence_structure, subnode)) == 1:
                    directChild.append(subnode)
                else:
                    directChild.append(subnode + '*')
        # Add the direct children of the current node to the dictionary
        dcm[relation] = directChild
    # Return the dictionary
    return dcm

def mergeNegatives(template, setntence_structure):
    """
    Merges negative tokens in the template based on the dependency relations in the sentence structure.

    Args:
        template (str): The template string.
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.

    Returns:
        str: The merged template string.
    """
    # Create a dictionary mapping each node to its direct children
    dcm = DCM(setntence_structure)
    # Split the template into tokens
    tokens = template.split()
    # Initialize the list to store the reduced template
    reducedTemplate = []
    # Iterate through each token in the template
    for token in tokens:
        # Check if the token contains multiple negative expressions
        if token.count('-') > 1:
            # Remove the '< >' markers from the token
            token = token[1:-1]
            # Split the token and extract the negative expressions
            minus = token.split('-')[1:]
            # Iterate through each node in the sentence structure
            for node, dc in dcm.items():
                # Check if the direct children of the node are a subset of the negative expressions
                if set(dc).issubset(set(minus)):
                    # Remove the direct children from the negative expressions and add the node
                    minus = [item for item in minus if item not in dc]
                    minus.append(node)
            # Create a new token with the merged negative expressions
            newToken = '<' + token.split('-')[0] + '-' + '-'.join(minus) + '>'
            # Append the new token to the reduced template
            reducedTemplate.append(newToken)
        else:
            # Append the token as it is to the reduced template
            reducedTemplate.append(token)
            
    # Join the reduced template tokens into a string and return it
    return ' '.join(reducedTemplate)

def ShiftReduce(setntence_structure, template):
    """
    Performs the shift-reduce algorithm to generalize a question template based on the given sentence structure and template.

    Args:
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.
        template (list): The list of template tokens.

    Returns:
        str: The generalized question template.
    """
    # Initialize the stack and the queue
    stack = []
    queue = template.copy()
    # Iterate through the tokens in the queue
    while len(queue) > 0:
        # Pop the first token from the queue
        head = queue.pop(0)
        # Check if the stack has one or more tokens for reduction
        if len(stack) >= 1:
            node1 = head
            node2 = stack[-1].split('-')[0]
            if node2.startswith('<'):
                node2 = node2[1:]
            r1 = node1.split('.')
            r2 = node2.split('.')
            idx = 0
            # Find the common prefix between the two nodes
            for i in range(min(len(r1), len(r2))):
                if '#' not in r1[i] or '#' not in r2[i]:
                    idx = 0
                    break
                if r1[i] != r2[i]:
                    break
                idx = i + 1
            # Check if the nodes can be merged if the common prefix is not empty and the difference in the dependences of the nodes is at most 1
            if idx > 0 and abs(len(r1) - idx) <= 1 and abs(len(r2) - idx) <= 1:
                if stack[-1].count('-') > 0:
                    topStack = stack.pop()
                    if topStack.startswith('<'):
                        topStack = topStack[1:-1]
                    # Split the negative expressions in the top of the stack
                    minus = topStack.split('-')[1:]
                    node = head if len(getAllSubNodes(setntence_structure, head)) == 1 else head + '*'
                    commonPrefix = '.'.join(r1[:idx])
                    newNode = '-'.join([m for m in minus if m != node])
                    if newNode == '':
                        stack.append('<' + commonPrefix + '>')
                    else:
                        stack.append('<' + commonPrefix + '-' + newNode + '>')
                else:
                    topStack1 = head
                    topStack2 = stack.pop()
                    if topStack2.startswith('<'):
                        topStack2 = topStack2[1:-1]
                    commonPrefix = '.'.join(r1[:idx])
                    subNodes = getAllSubNodes(setntence_structure, commonPrefix)
                    for node in subNodes:
                        if node != topStack1 and node != topStack2:
                            if len(getAllSubNodes(setntence_structure, node)) > 1:
                                node = node + '*'
                            commonPrefix += '-' + node
                    stack.append('<' + commonPrefix + '>')
            else:
                stack.append(head)
        else:
            stack.append(head)
            
    questionTemplate = ''
    for item in stack:
        if item.startswith('ROOT'):
            questionTemplate += f"[{item}]"
        else:
            questionTemplate += item
        questionTemplate += ' '
    return questionTemplate

def generalizeTemplate(template):
    """
    Generalizes a template by removing the index numbers from the template tokens.

    Args:
        template (str): The template string.

    Returns:
        str: The generalized template string.
    """
    pattern = re.compile('#[0-9]+')
    return pattern.sub('', template)

def generalize_setntence_structure(setntence_structure):
    """
    Generalizes the sentence structure dictionary by removing the index numbers from the values.

    Args:
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.

    Returns:
        dict: The generalized sentence structure dictionary.
    """
    new_setntence_structure = dict()
    pattern = re.compile('#[0-9]+')
    # Iterate through the items in the sentence structure dictionary
    for key, value in setntence_structure.items():
        # Remove the index number from the value
        new_setntence_structure[key] = pattern.sub('', value)
    return new_setntence_structure

def checkGuards(sentence, guards):
    """
    Checks if the given sentence satisfies the guards specified in the template.

    Args:
        sentence (str): The input sentence.
        guards (tuple): A tuple containing the guards: exists, isClause, and hasClause.

    Returns:
        bool: True if the sentence satisfies the guards, False otherwise.
    """
    exists, isClause, hasClause = guards
    
    # Get the sentence structure and document representation of the sentence
    doc, setntence_structure = getSentenceStructure(sentence)
    
    # Check if the sentence structure is None
    if setntence_structure is None:
        return False
    
    # Generalize the sentence structure
    setntence_structure = generalize_setntence_structure(setntence_structure)
    
    # Create a mapping of inverse sentence structure
    setntence_structure_invers = {value: key for key, value in setntence_structure.items()}
    
    # Check if all the exists guards exist in the sentence structure
    for e in exists:
        if e not in setntence_structure.values():
            return False
        
    # Check if the POS tag of the root node matches the isClause guard
    if doc[setntence_structure_invers.get('ROOT')].pos_ != isClause:
        return False
    
    # Check if the morphological features of the root node match the hasClause guard
    if doc[setntence_structure_invers.get('ROOT')].morph.to_dict() != hasClause:
        return False
    
    # All guards are satisfied
    return True

def generateQuestion(sentence, template, guards, isAnswer=False):
    """
    Generates a question based on the given sentence, template, and guards.

    Args:
        sentence (str): The input sentence.
        template (str): The template string.
        guards (tuple): A tuple containing the guards: exists, isClause, and hasClause.
        isAnswer (bool, optional): Specifies whether the generated sentence from template is for an answer. Defaults to False.

    Returns:
        str: The generated question.
    """
    # Check if the guards are satisfied for the given sentence
    if not checkGuards(sentence, guards):
        return None
    
    # Get the document and sentence structure
    doc, setntence_structure = getSentenceStructure(sentence)
    
    # Generalize the template and sentence structure
    template = generalizeTemplate(template)
    setntence_structure = generalize_setntence_structure(setntence_structure)
    
    # Create a mapping of inverse sentence structure
    setntence_structure_inverse = {v: k for k, v in setntence_structure.items()}
    
    # Initialize the list to store the question tokens
    question = []
    
    # Iterate through each token in the template
    for item in template.split():
        if item.startswith('<'):
            # Handle the case of a placeholder token
            item = item[1:-1]
            if item.count('-') == 0:
                # Get all subnodes of the specified node
                nodes = getAllSubNodes(setntence_structure, item, True)
                for node in nodes:
                    # Append the text of each subnode to the question
                    question.append(doc[setntence_structure_inverse[node]].text)
            else:
                # Handle the case of negative expressions
                nodes = item.split('-')
                allNodes = getAllSubNodes(setntence_structure, nodes[0], True)
                for node in nodes[1:]:
                    if node.endswith('*'):
                        # Exclude the specified subnode
                        node = node[:-1]
                        allNodes = [n for n in allNodes if node != n]
                    else:
                        # Exclude all subnodes of the specified node
                        allSubNode = getAllSubNodes(setntence_structure, node, True)
                        allNodes = [n for n in allNodes if n not in allSubNode]
                # Sort the remaining nodes based on their order in the sentence
                allNodes = sorted(allNodes, key=lambda x: setntence_structure_inverse[x])
                for node in allNodes:
                    # Append the text of each remaining node to the question
                    question.append(doc[setntence_structure_inverse[node]].text)
        elif item.startswith('['):
            # Handle the case of a node-level token
            question.append(doc[setntence_structure_inverse[item[1:-1]]].text)
        else:
            # Handle the case of a constant token
            question.append(item)
    
    # Join the question tokens into a string and return it
    return ' '.join(question)

def getGuards(template, setntence_structure, doc):
    """
    Retrieves the guards (exists, isClause, hasClause) based on the given template, sentence structure, and document.

    Args:
        template (str): The template string.
        setntence_structure (dict): The dictionary representing the dependency relations between tokens.
        doc (spacy.tokens.doc.Doc): The spaCy document object representing the analyzed sentence.

    Returns:
        tuple: A tuple containing the guards: exists (set), isClause (str), and hasClause (dict).
    """
    # Generalize the sentence structure
    setntence_structure = generalize_setntence_structure(setntence_structure)
    
    # Initialize the exists set and hasClause dictionary
    exists = set()
    hasClause = dict()
    
    # Create a mapping of inverse sentence structure
    setntence_structure_inverse = {v: k for k, v in setntence_structure.items()}
    
    # Get the POS tag and morphological features of the root node
    isClause = doc[setntence_structure_inverse['ROOT']].pos_
    hasClause = doc[setntence_structure_inverse['ROOT']].morph.to_dict()
    
    # Iterate through each token in the template
    for item in template.split():
        if item.startswith('<'):
            item = item[1:-1]
            relation = item.split('-')[0]
            # Append the first or main node of the negative expression to the exists set
            exists.add(relation)
        elif item.startswith('['):
            relation = item[1:-1]
            # Append the node-level token to the exists set
            exists.add(relation)
    
    return exists, isClause, hasClause
        

def ngrams(context, unigram=dict(), bigram=dict(), trigram=dict(), wordCount=0):
    """
    Generates n-grams from the given context and calculates their frequencies.

    Args:
        context (str): The input context.
        unigram (dict, optional): The dictionary to store the unigram frequencies. Defaults to an empty dictionary.
        bigram (dict, optional): The dictionary to store the bigram frequencies. Defaults to an empty dictionary.
        trigram (dict, optional): The dictionary to store the trigram frequencies. Defaults to an empty dictionary.
        wordCount (int, optional): The total count of words. Defaults to 0.

    Returns:
        dict: The updated unigram dictionary.
        dict: The updated bigram dictionary.
        dict: The updated trigram dictionary.
        int: The updated word count.
    """
    # Tokenize the context into sentences
    sentences = sent_tokenize(context)
    # Iterate through the sentences
    for sentence in sentences:
        # Analyze the sentence using the spaCy library
        doc = nlp(sentence)
        # Extract the POS tags and morphological features of the tokens
        tokens = [f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/') for token in doc]
        # Insert the start and end tokens to the list of tokens
        tokens.insert(0, '<s>')
        tokens.append('</s>')
        # Update the total word count
        wordCount += len(tokens)
        # Generate unigrams, bigrams, and trigrams from the tokens
        gram1 = nltk.ngrams(tokens, 1)
        gram2 = nltk.ngrams(tokens, 2)
        gram3 = nltk.ngrams(tokens, 3)
        # Update the unigram, bigram, and trigram dictionaries with the frequencies of the n-grams
        for k, v in nltk.FreqDist(gram1).items():
            unigram[k] = unigram.get(k, 0) + v
        for k, v in nltk.FreqDist(gram2).items():
            bigram[k] = bigram.get(k, 0) + v
        for k, v in nltk.FreqDist(gram3).items():
            trigram[k] = trigram.get(k, 0) + v
    # Return the updated unigram, bigram, trigram dictionaries, and the updated word count
    return unigram, bigram, trigram, wordCount

def questionWord(question, answer, questionWordCount, questionCount):
    """
    Updates the questionWordCount and questionCount dictionaries based on the given question and answer.

    Args:
        question (str): The input question.
        answer (str): The corresponding answer.
        questionWordCount (dict): A dictionary to store the count of question words and their corresponding root tokens of the answers.
        questionCount (dict): A dictionary to store the count of question words.

    Returns:
        dict: The updated questionWordCount dictionary.
        dict: The updated questionCount dictionary.
    """
    # Tokenize the question and get the first word
    word = word_tokenize(question)[0].lower()
    
    # Check if the first word is a WH-question word or a conventional question word
    if word in WH_QUESTION or word in CONV_QUESTION:
        # Analyze the answer using the spaCy library
        doc = nlp(answer)
        rootToken = None
        # Find the root token of the answer sentence
        for token in doc:
            if token.dep_ == 'ROOT':
                # Get the POS tag and morphological features of the root token
                rootToken = f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/')
        
        # Update the count of the question word and its corresponding root token of the answers
        questionCount[word] = questionCount.get(word, 0) + 1
        questionWordCount[(word, rootToken)] = questionWordCount.get((word, rootToken), 0) + 1
    
    # Return the updated questionWordCount and questionCount dictionaries
    return questionWordCount, questionCount

def calculateScore(question, unigram, bigram, trigram, wordCount, answer, questionWordCount, questionCount):
    """
    Calculates the score for a given question-answer pair based on n-gram probabilities and question word frequencies.

    Args:
        question (str): The input question.
        unigram (dict): The dictionary containing the unigram frequencies.
        bigram (dict): The dictionary containing the bigram frequencies.
        trigram (dict): The dictionary containing the trigram frequencies.
        wordCount (int): The total count of words.
        answer (str): The corresponding answer.
        questionWordCount (dict): The dictionary storing the count of question words and their corresponding root tokens of the answers.
        questionCount (dict): The dictionary storing the count of question words.

    Returns:
        float: The calculated score.
    """
    lambda4 = 0.000001
    lambda3 = 0.01 - lambda4
    lambda2 = 0.1 - lambda3
    lambda1 = 0.9
    alpha = 0.8
    
    # Tokenize the question and add start and end tokens
    doc = nlp(question)
    tokens = [f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/') for token in doc]
    tokens.insert(0, '<s>')
    tokens.append('</s>')
    
    # Initialize the score
    rNG = 0
    
    # Iterate through each token in the question
    for i, token in enumerate(tokens):
        w1, w2, w3 = None, None, None
        w3 = token
        
        # Get the previous two tokens if they exist
        if i - 1 >= 0:
            w2 = tokens[i-1]
        if i - 2 >= 0:
            w1 = tokens[i-2]
            
        # Calculate the probabilities of trigrams, bigrams, and unigrams
        p3 = unigram.get((w3,), 0) / wordCount
        p2 = bigram.get((w2, w3), 0) / unigram.get((w2,), 1)
        p1 = trigram.get((w1, w2, w3), 0) / bigram.get((w1, w2), 1)
        
        # Calculate the n-gram score
        rNG += lambda1 * p1 + lambda2 * p2 + lambda3 * p3 + lambda4
        
    # Normalize the n-gram score
    rNG /= (len(tokens) - 2)
    
    # Get the root token of the answer
    doc = nlp(answer)
    rootToken = None
    for token in doc:
        if token.dep_ == 'ROOT':
            rootToken = f"{token.pos_}/{'|'.join(sorted([k+'='+v for k,v in token.morph.to_dict().items()]))}".strip('/')
            
    # Get the first word of the question
    word = word_tokenize(question)[0].lower()
    
    # Calculate the question word score
    if questionWordCount.get((word, rootToken), 0) == 0:
        return 0
    rQW = questionWordCount.get((word, rootToken), 0) / (questionCount.get(word, 0) + 10e-10)
    
    # Calculate the final score
    score = alpha * rNG + (1 - alpha) * rQW
    return score

def checkTemplate(template, idf):
    """
    Checks if a template should be discarded based on the IDF (Inverse Document Frequency) of its words.

    Args:
        template (list): The list of tokens in the template.
        idf (dict): The IDF dictionary containing the IDF values of words.

    Returns:
        bool: True if the template should be discarded, False otherwise.
    """
    # Convert the template list to a string
    template = ' '.join(template)
    
    # Remove question mark and leading/trailing whitespaces
    template = template.replace('?', '')
    template = template.strip()
    
    # Split the template into individual words
    words = template.split(' ')
    
    # Initialize discardTemplate flag
    discardTemplate = False
    
    # Iterate through each word in the template
    for word in words:
        # Check if the word is not a special token and not a question word
        if '#' not in word and word not in CONV_QUESTION and word not in WH_QUESTION:
            # Check if the word is not in the IDF dictionary or the word is too rare
            if word not in idf or idf[word] - 1 > math.log(4):
                discardTemplate = True
                break
    
    return discardTemplate

def generateTemplateGuardsPair(sentence, question, idf, isAnswer=False):
    """
    Generates a template and its corresponding guards based on the given sentence and question.

    Args:
        sentence (str): The input sentence.
        question (str): The corresponding question.
        idf (dict): The IDF dictionary containing the IDF values of words.
        isAnswer (bool, optional): Indicates if the template is for an answer. Defaults to False.

    Returns:
        str: The generated template.
        list: The generated guards.
    """
    # Get the sentence structure and spaCy document object
    doc, setntence_structure = getSentenceStructure(sentence)
    
    # Check if the sentence structure is None
    if setntence_structure is None:
        return None, []
    
    # Get the question template based on the sentence structure, spaCy document object, sentence, and question
    template = getQuestionTemplate(setntence_structure, doc, sentence, question)
    
    # Check if the template is None
    if template is None:
        return None, []
    
    # Check if the template should be discarded based on IDF values
    if not isAnswer and checkTemplate(template, idf):
        return None, []
    
    # Perform template transformations or generalizations
    template = ShiftReduce(setntence_structure, template)
    template = mergeNegatives(template, setntence_structure)
    template = generalizeTemplate(template)
    
    # Get the guards for the template
    guards = getGuards(template, setntence_structure, doc)
    
    # Return the generated template and guards
    return template, guards

def getDataset(datasetPath):
    """
    Retrieves the dataset from the given JSON file.

    Args:
        datasetPath (str): The path to the JSON file.

    Returns:
        dict: The dataset loaded from the JSON file.
    """
    dataset = dict()
    # Open the JSON file and load the dataset
    with open(datasetPath) as jsonFile:
        dataset = json.load(jsonFile)
        jsonFile.close()
    return dataset

def get_sentence_containing_answer(context, answer_start):
    """
    Retrieves the sentence containing the answer based on the given context and answer start position.

    Args:
        context (str): The input context.
        answer_start (int): The start position of the answer.

    Returns:
        str: The sentence containing the answer.
    """
    # Tokenize the context into sentences
    sentences = sent_tokenize(context)
    
    # Initialize start position for each sentence
    current_pos = 0
    
    for sentence in sentences:
        # Calculate the start and end positions of the sentence
        sentence_start = current_pos
        sentence_end = sentence_start + len(sentence)
        
        # Check if the answer_start falls within the sentence boundaries
        if sentence_start <= answer_start < sentence_end:
            return sentence
        
        # Update current position for the next sentence
        current_pos = sentence_end + 1  # +1 to account for the space or punctuation between sentences
    
    return None

def preProcessingTrainingSet(dataset):
    """
    Preprocesses the training set by extracting contexts, questions, answers, and sentences.

    Args:
        dataset (dict): The dataset containing the paragraphs and questions.

    Returns:
        list: The list of contexts.
        list: The list of questions.
        list: The list of answers.
        list: The list of sentences.
    """
    contexts = []
    questions = []
    answers = []
    sentences = []
    
    # Iterate through each data entry in the dataset
    for d in dataset['data']:
        # Iterate through each paragraph in the data entry
        for paragraph in d['paragraphs']:
            # Extract the context
            contexts.append(paragraph['context'])
            
            q = []
            a = []
            s = []
            
            # Iterate through each question-answer pair in the paragraph
            for qa in paragraph['qas']:
                # Skip impossible questions
                if qa['is_impossible']:
                    continue
                
                # Get the sentence containing the answer
                sentence = get_sentence_containing_answer(paragraph['context'], qa['answers'][0]['answer_start'])
                
                # Skip questions without a corresponding sentence
                if sentence is None:
                    continue
                
                # Append the question, answer, and sentence to their respective lists
                s.append(sentence)
                a.append(qa['answers'][0]['text'])
                q.append(qa['question'])
                
            # Append the lists to the main lists
            questions.append(q)
            answers.append(a)
            sentences.append(s)
    
    return contexts, questions, answers, sentences

def lemmatize(text):
    """
    Lemmatizes the given text.

    Args:
        text (str): The input text.

    Returns:
        str: The lemmatized text.
    """
    doc = nlp(text)
    lemmatized = [token.lemma_ for token in doc]
    return ' '.join(lemmatized)

def trainModel(contexts, questions, answers, sentences):
    """
    Trains the question generation model using the given contexts, questions, answers, and sentences.

    Args:
        contexts (list): The list of contexts.
        questions (list): The list of questions.
        answers (list): The list of answers.
        sentences (list): The list of sentences.

    Returns:
        tuple: A tuple containing the trained model parameters.
    """
    # Initialize variables for model parameters
    unigram = dict()
    bigram = dict()
    trigram = dict()
    wordCount = 0
    questionWordCount = dict()
    questionCount = dict()
    questionTemplates = []
    answerTemplates = []
    questionGuards = []
    answerGuards = []
    
    # Create a TF-IDF vectorizer and fit it to the contexts
    vectorizer = TfidfVectorizer(preprocessor=lemmatize)
    vectorizer.fit_transform(contexts)
    feature_names = vectorizer.get_feature_names_out()
    idf_values = dict(zip(feature_names, vectorizer.idf_))
    
    # Iterate through each context
    for i in range(len(contexts)):
        if i % 100 == 0:
            print(f"Processing {i} out of {len(contexts)}")

        # Calculate n-grams for the context
        unigram, bigram, trigram, wordCount = ngrams(contexts[i], unigram, bigram, trigram, wordCount)

        # Iterate through each question in the context
        for j in range(len(questions[i])):
            # Generate question template and guard
            questionTemplate, questionGuard = generateTemplateGuardsPair(sentences[i][j], questions[i][j], idf_values)
            
            # Skip if question guard is empty
            if len(questionGuard) == 0 or len(questionGuard[0]) == 0:
                continue
            
            # Generate answer template and guard
            answerTemplate, answerGuard = generateTemplateGuardsPair(sentences[i][j], answers[i][j], None, True)
            
            # Skip if answer guard is empty
            if len(answerGuard) == 0 or len(answerGuard[0]) == 0:
                continue
            
            # Calculate question word count and question count
            questionWordCount, questionCount = questionWord(questions[i][j], answers[i][j], questionWordCount, questionCount)
            
            # Append templates and guards to respective lists
            questionTemplates.append(questionTemplate)
            answerTemplates.append(answerTemplate)
            questionGuards.append(questionGuard)
            answerGuards.append(answerGuard)
        
    print("Training Completed")
    
    # Return the trained model parameters as a tuple
    return unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGuards, answerGuards, questionWordCount, questionCount

def saveModel(modelParameters, modelFolderPath = 'Trained_Model'):
    """
    Saves the trained model parameters to the specified folder path.

    Args:
        modelParameters (tuple): A tuple containing the trained model parameters.
        modelFolderPath (str, optional): The folder path to save the model. Defaults to 'Trained_Model'.
    """
    unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGuards, answerGuards, questionWordCount, questionCount = modelParameters
    
    # Create the model folder if it doesn't exist
    if not os.path.exists(modelFolderPath):
        os.makedirs(modelFolderPath)
    
    # Save the model parameters as JSON files
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
    with open(modelFolderPath + '/' + 'questionGuards.json', 'wb') as jsonFile:
        pickle.dump(questionGuards, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerGuards.json', 'wb') as jsonFile:
        pickle.dump(answerGuards, jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'wordCount.json', 'wb') as jsonFile:
        pickle.dump(wordCount, jsonFile)
        jsonFile.close()
        
    print("Model Saved")

def loadModel(modelFolderPath = 'Trained_Model'):
    """
    Loads the trained model parameters from the specified folder path.

    Args:
        modelFolderPath (str, optional): The folder path to load the model from. Defaults to 'Trained_Model'.

    Returns:
        tuple: A tuple containing the loaded model parameters.
    """
    # Initialize variables for model parameters
    unigram = dict()
    bigram = dict()
    trigram = dict()
    wordCount = 0
    questionWordCount = dict()
    questionCount = dict()
    questionTemplates = []
    answerTemplates = []
    questionGuards = []
    answerGuards = []

    # Load the model parameters from JSON files
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
    with open(modelFolderPath + '/' + 'questionGuards.json', 'rb') as jsonFile:
        questionGuards = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'answerGuards.json', 'rb') as jsonFile:
        answerGuards = pickle.load(jsonFile)
        jsonFile.close()
    with open(modelFolderPath + '/' + 'wordCount.json', 'rb') as jsonFile:
        wordCount = pickle.load(jsonFile)
        jsonFile.close()

    print("Model Loaded")
    return unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGuards, answerGuards, questionWordCount, questionCount

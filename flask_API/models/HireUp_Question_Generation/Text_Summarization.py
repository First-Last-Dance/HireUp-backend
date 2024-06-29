import PyPDF2
import os
import math
import matplotlib.pyplot as plt
import re
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tag import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from nltk.tokenize import sent_tokenize
import language_tool_python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import fasttext
nltk.download('averaged_perceptron_tagger')
stop_words = set(stopwords.words('english')) 
tool = language_tool_python.LanguageTool('en-US')

def get_outliers_boundary(data):
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return q1, q3

def extract_text_from_pdf(pdf_path):
    page_lengthes = []
    pages = []
    text = ''
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            page_text = page_text.split('\n')
            page_text = page_text[1:]
            page_text = '\n'.join(page_text)
            pattern = re.compile(r'\n[0-9]+[A-Z]')
            match = pattern.search(page_text)
            if match:
                if match.start() > int(len(page_text) * 0.9):
                    page_text = page_text[:match.start()+1]
            page_lengthes.append(len(page_text))
            pages.append(page_text)
            # text += page_text
        lower_bound, upper_bound = get_outliers_boundary(page_lengthes)
        for page in pages:
            if len(page) > lower_bound and len(page) < upper_bound:
                text += page
        pattern = re.compile(r'-\s*\n')
        text = pattern.sub('', text)
        pattern = re.compile(r'[^\.:]\s*\n')
        text = pattern.sub(' ', text)
    
    return text

def preprocess_text(text, original_text = None, preprocessed_text = None, vocabulary = None, isText = False):
    if original_text is None:
        original_text = []
    if preprocessed_text is None:
        preprocessed_text = []
    if vocabulary is None:
        vocabulary = []
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    original_text.append(text)
    words = word_tokenize(text)
    text = text.lower()
    if not isText:
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    words = word_tokenize(text)
    # words = [stemmer.stem(lemmatizer.lemmatize(word)) for word in words if word not in stop_words]
    vocabulary.extend(words)
    document = ' '.join(words)
    preprocessed_text.append(document)
    vocabulary = list(set(vocabulary))
    return original_text, preprocessed_text, vocabulary

def getDocuments_from_pdf(filePath, original_documents = None, preprocessed_documents = None, vocabulary = None):
    if original_documents is None:
        original_documents = []
    if preprocessed_documents is None:
        preprocessed_documents = []
    if vocabulary is None:
        vocabulary = []
    text = extract_text_from_pdf(filePath)
    pattern = re.compile(r'[\.:]\s*\n')
    documents = pattern.split(text)
    document_lengths = [len(document) for document in documents]
    lower_bound, upper_bound = get_outliers_boundary(document_lengths)
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    for document in documents:
        if len(document) > lower_bound:
            matches = tool.check(document)
            document = language_tool_python.utils.correct(document, matches)
            ulrPattern = re.compile(r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
            emailPattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            if ulrPattern.search(document) or emailPattern.search(document):
                continue
            original_documents, preprocessed_documents, vocabulary = preprocess_text(document, original_documents, preprocessed_documents, vocabulary)
    return original_documents, preprocessed_documents, vocabulary

def getAllDocuments(folderPath):
    dir_list = os.listdir(folderPath)
    original_documents = []
    preprocessed_documents = []
    vocabulary = []
    for file_name in dir_list:
        file_path = folderPath+file_name
        original_documents, preprocessed_documents, vocabulary = getDocuments_from_pdf(file_path, original_documents, preprocessed_documents, vocabulary)
    return original_documents, preprocessed_documents, vocabulary

def TF_IDF(documents, vocabulary):
    tfidf_matrix = []
    
    # Calculate term frequency (TF) for each document
    for doc in documents:
        tf = {}
        words = word_tokenize(doc)
        total_words = len(words)
        
        for word in words:
            tf[word] = tf.get(word, 0) + (1 / total_words)
        
        tfidf_vector = []
        
        # Calculate inverse document frequency (IDF) for each word in the vocabulary
        for word in vocabulary:
            doc_count = sum([1 for doc in documents if word in doc])
            idf = math.log(len(documents) / (doc_count + 10e-10))
            
            # Calculate TF-IDF for each word in the document
            tfidf = tf.get(word, 0) * idf
            tfidf_vector.append(tfidf)
        
        tfidf_matrix.append(tfidf_vector)
    
    return np.array(tfidf_matrix)


def TF_IDF_Sklearn(documents, vocabulary):
    vectorizer = TfidfVectorizer(vocabulary=vocabulary)
    X = vectorizer.fit_transform(documents)
    return X, vectorizer

def SVD_Sklearn(tfidf_matrix):
    # Perform SVD on the tfidf_matrix
    svd_model = TruncatedSVD(n_components=5, algorithm='randomized', n_iter=1000)
    svd_matrix = svd_model.fit_transform(tfidf_matrix)
    
    return svd_matrix

def SVD_Np(tfidf_matrix):
    # Perform SVD on the tfidf_matrix
    U, s, V = np.linalg.svd(tfidf_matrix, full_matrices=True)
    return U, s, V

def get_top_N_documents_in_top_M_topics(U, original_documents, N, M):
    '''
    This function returns the top N documents in each the top M topics and sorts  the documents by their indices then merge them in one document.
    '''
    top_N_document_in_top_M_topic = []
    documents_set_indeces = set()
    documents_indeces = []
    for i in range(M):
        documents = ''
        j = 1
        top_document_indices = []
        skip = 0
        while j + skip <= N + skip and j + skip <= U.shape[0]:
            top_document_index = np.abs(U[:, i]).argsort()[-j-skip]
            if top_document_index not in documents_set_indeces:
                documents_set_indeces.add(top_document_index)
                top_document_indices.append(top_document_index)
                j += 1
            else:
                skip += 1
        # top_document_indices = np.abs(U[:, i]).argsort()[-N:][::-1]
        top_document_indices.sort()
        documents_indeces.append(top_document_indices)
        for index in top_document_indices:
            documents += original_documents[index] + '. '
        top_N_document_in_top_M_topic.append(documents)
    return top_N_document_in_top_M_topic, documents_indeces

def Summarize_Document(document, num_sentences):
    sentences = sent_tokenize(document)
    num_sentences = min(num_sentences, len(sentences))
    original_sentences = []
    preprocessed_sentences = []
    vocabulary = []
    for i in range(len(sentences)):
        original_sentences, preprocessed_sentences, vocabulary = preprocess_text(sentences[i], original_sentences, preprocessed_sentences, vocabulary)
    # tfidf_matrix = TF_IDF(preprocessed_sentences, vocabulary)
    sentenceEmbeddings = getDocumentsVector(preprocessed_sentences)
    U, s, V = SVD_Np(sentenceEmbeddings)
    summarization = []
    # for i in range(num_sentences):
    top_sentence_indices = np.abs(U[:, i]).argsort()[-num_sentences:][::-1]
    # top_sentence_indices.sort()
    for j in top_sentence_indices:
        sentence = original_sentences[j]
        sentence = sentence.strip()
        sentence += '.'
        sentence = re.sub(r'\.+', '.', sentence)
        sentence = re.sub(r'\s+', ' ', sentence)
        if re.search(r'[A-Z]', sentence) is None:
            continue
        sentence = sentence[re.search(r'[A-Z]', sentence).start():]
        summarization.append(sentence)
    return summarization

# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def getDocumentsVector(documents):
    # Load model from HuggingFace Hub
    tokenizer = AutoTokenizer.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    model = AutoModel.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    

    # Tokenize sentences
    encoded_input = tokenizer(documents, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    # sentence_embeddings to numpy array
    sentence_embeddings = sentence_embeddings.numpy()

    return sentence_embeddings

def getAllDocumentsFromGivenString(text):
    original_documents = []
    preprocessed_documents = []
    vocabulary = []
    documents = text.split('\n')
    for document in documents:
        if document == '':
            continue
        matches = tool.check(document)
        document = language_tool_python.utils.correct(document, matches)
        original_documents, preprocessed_documents, vocabulary = preprocess_text(document, original_documents, preprocessed_documents, vocabulary, isText=True)
    return original_documents, preprocessed_documents, vocabulary

def summarization(numberOfTopics, numberOfDocuments, numberOfSentences, folderPath = None, text = None, isText = False):
    sentences = []
    paragraphs = []
    if isText:
        original_documents, preprocessed_documents, vocabulary = getAllDocumentsFromGivenString(text)
    else:
        original_documents, preprocessed_documents, vocabulary = getAllDocuments(folderPath)
    # tfidf_matrix = TF_IDF(preprocessed_documents, vocabulary)
    documentsEmbeddings = getDocumentsVector(preprocessed_documents)
    U, s, V = SVD_Np(documentsEmbeddings)
    top_N_document_in_top_M_topic, documents_indeces = get_top_N_documents_in_top_M_topics(U, original_documents, numberOfDocuments, numberOfTopics)
    unique_sentences = set()
    for idx, document in enumerate(top_N_document_in_top_M_topic):
        # print(document)
        if document == '':
            continue
        summarization = Summarize_Document(document, numberOfSentences)
        for sentence in summarization:
            for index in documents_indeces[idx]:
                originalDoc = original_documents[index]
                if sentence in originalDoc and sentence not in unique_sentences:
                    paragraphs.append(original_documents[index])
                    sentences.append(sentence)
                    unique_sentences.add(sentence)
                    break
    return sentences, paragraphs

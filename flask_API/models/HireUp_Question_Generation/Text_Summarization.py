import PyPDF2
import os
import math
import re
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from nltk.tokenize import sent_tokenize
import language_tool_python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
stop_words = set(stopwords.words('english')) 
tool = language_tool_python.LanguageTool('en-US')

def get_outliers_boundary(data):
    """
    This function calculates the lower and upper boundaries for identifying outliers in a dataset.

    Parameters:
    - data: A list or array of numerical data.

    Returns:
    - q1: The lower boundary (first quartile) for identifying outliers.
    - q3: The upper boundary (third quartile) for identifying outliers.
    """
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return lower_bound, upper_bound

def extract_text_from_pdf(pdf_path):
    """
    This function extracts text from a PDF file.

    Parameters:
    - pdf_path: The path to the PDF file.

    Returns:
    - text: The extracted text from the PDF.
    """
    page_lengths = []
    pages = []
    text = ''
    # Open the PDF file in read-binary mode
    with open(pdf_path, 'rb') as file:
        # Create a PDF file reader
        reader = PyPDF2.PdfReader(file)
        # Iterate over all the pages of the PDF file
        for page in reader.pages:
            # Extract text from the page and append it to the text string
            page_text = page.extract_text()
            # split the text by new line
            page_text = page_text.split('\n')
            # remove the first element of the list
            page_text = page_text[1:]
            # join the list elements to form a string
            page_text = '\n'.join(page_text)
            # remove the references section from the page
            pattern = re.compile(r'\n[0-9]+[A-Z]')
            match = pattern.search(page_text)
            if match:
                # if the references section is found at the end of the page, remove it
                if match.start() > int(len(page_text) * 0.9):
                    page_text = page_text[:match.start()+1]
            # append the length of the page to the page_lengths list
            page_lengths.append(len(page_text))
            # append the page text to the pages list
            pages.append(page_text)
        # Calculate the lower and upper boundaries for identifying outliers in the page lengths
        lower_bound, upper_bound = get_outliers_boundary(page_lengths)
        # Concatenate the text of the pages that are within the lower and upper boundaries
        for page in pages:
            if len(page) > lower_bound and len(page) < upper_bound:
                text += page
        # Fix hyphenated words at the end of the lines and remove line breaks
        pattern = re.compile(r'-\s*\n')
        text = pattern.sub('', text)
        # Remove line breaks that are not followed by a period or colon
        # pattern = re.compile(r'[^\.:]\s*\n')
        # text = pattern.sub(' ', text)
        text = re.sub(r'\s+(?=\n)', '', text)
        text = re.sub(r'(?<![.:])\n', ' ', text)
    # Return the extracted text
    return text

from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import re

def preprocess_text(text, original_text=None, preprocessed_text=None, vocabulary=None, isText=False):
    """
    Preprocesses the given text by performing tokenization, lemmatization, and stemming.

    Args:
        text (str): The input text to be preprocessed.
        original_text (list, optional): A list to store the original text. Defaults to None.
        preprocessed_text (list, optional): A list to store the preprocessed text. Defaults to None.
        vocabulary (list, optional): A list to store the unique words in the text. Defaults to None.
        isText (bool, optional): Indicates whether the input is a text or PDF file. Defaults to False.

    Returns:
        tuple: A tuple containing the original text, preprocessed text, and vocabulary.
    """
    # Initialize the lists if they are not provided
    if original_text is None:
        original_text = []
    if preprocessed_text is None:
        preprocessed_text = []
    if vocabulary is None:
        vocabulary = []

    # Store the original text
    original_text.append(text)
    
    # Tokenize the text
    words = word_tokenize(text)
    
    # Convert the words to lowercase
    text = text.lower()

    if not isText:
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)

    text = text.strip()
    
    # Tokenize the text
    words = word_tokenize(text)
    
    # Add the words to the vocabulary
    vocabulary.extend(words)
    document = ' '.join(words)
    preprocessed_text.append(document)
    vocabulary = list(set(vocabulary))

    return original_text, preprocessed_text, vocabulary

def getDocuments_from_pdf(filePath, original_documents=None, preprocessed_documents=None, vocabulary=None):
    """
    Extracts text from a PDF file and preprocesses it.

    Args:
        filePath (str): The path to the PDF file.
        original_documents (list, optional): List to store the original documents. Defaults to None.
        preprocessed_documents (list, optional): List to store the preprocessed documents. Defaults to None.
        vocabulary (list, optional): List to store the vocabulary. Defaults to None.

    Returns:
        tuple: A tuple containing the original documents, preprocessed documents, and vocabulary.
    """
    if original_documents is None:
        original_documents = []
    if preprocessed_documents is None:
        preprocessed_documents = []
    if vocabulary is None:
        vocabulary = []

    # Extract text from the PDF file
    text = extract_text_from_pdf(filePath)

    # Split the text into individual documents based on certain patterns
    pattern = re.compile(r'[\.:]\s*\n')
    documents = pattern.split(text)

    # Calculate the lengths of each document
    document_lengths = [len(document) for document in documents]

    # Get the lower and upper bounds for outlier document lengths
    lower_bound, upper_bound = get_outliers_boundary(document_lengths)
    
    # Process each document
    for document in documents:
        if len(document) > lower_bound:
            
            # Check for grammar and spelling errors in the document
            matches = tool.check(document)
            document = language_tool_python.utils.correct(document, matches)

            # Check for URLs and email addresses in the document
            urlPattern = re.compile(r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
            emailPattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            
            # Skip the document if it contains a URL or email address
            if urlPattern.search(document) or emailPattern.search(document):
                continue

            # Preprocess the document and update the lists
            original_documents, preprocessed_documents, vocabulary = preprocess_text(document, original_documents, preprocessed_documents, vocabulary)

    return original_documents, preprocessed_documents, vocabulary

def getAllDocuments(folderPath):
    """
    Retrieves all documents from a given folder path and returns the original documents, preprocessed documents, and vocabulary.

    Args:
        folderPath (str): The path to the folder containing the documents.

    Returns:
        tuple: A tuple containing the original documents, preprocessed documents, and vocabulary.

    """
    # Get the list of files in the folder
    dir_list = os.listdir(folderPath)

    # Initialize empty lists for original documents, preprocessed documents, and vocabulary
    original_documents = []
    preprocessed_documents = []
    vocabulary = []

    # Iterate through each file in the folder
    for file_name in dir_list:
        # Create the file path by concatenating the folder path and file name
        file_path = folderPath + file_name

        # Call the getDocuments_from_pdf function to extract documents from the PDF file
        original_documents, preprocessed_documents, vocabulary = getDocuments_from_pdf(file_path, original_documents, preprocessed_documents, vocabulary)

    # Return the original documents, preprocessed documents, and vocabulary
    return original_documents, preprocessed_documents, vocabulary

def TF_IDF(documents, vocabulary):
    """
    Calculate the TF-IDF matrix for a list of documents.

    Args:
        documents (list): A list of documents.
        vocabulary (list): A list of words in the vocabulary.

    Returns:
        numpy.ndarray: The TF-IDF matrix.

    """
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
    """
    Compute the TF-IDF representation of a list of documents using the sklearn library.

    Parameters:
    - documents (list): A list of strings representing the documents.
    - vocabulary (list): A list of strings representing the vocabulary.

    Returns:
    - X (sparse matrix): The TF-IDF matrix representation of the documents.
    - vectorizer (TfidfVectorizer): The fitted TfidfVectorizer object.

    """
    # Create a TfidfVectorizer object with the given vocabulary
    vectorizer = TfidfVectorizer(vocabulary=vocabulary)

    # Transform the documents into a TF-IDF matrix
    X = vectorizer.fit_transform(documents)

    # Return the TF-IDF matrix and the fitted vectorizer
    return X, vectorizer

from sklearn.decomposition import TruncatedSVD

def SVD_Sklearn(matrix_representation):
    """
    Perform Singular Value Decomposition (SVD) on the given matrix.

    Parameters:
    matrix_representation (array-like): Matrix representation of the data.

    Returns:
    svd_matrix (array-like): The transformed matrix after applying SVD.
    """

    # Perform SVD on the given matrix
    svd_model = TruncatedSVD(n_components=5, algorithm='randomized', n_iter=1000)
    svd_matrix = svd_model.fit_transform(matrix_representation)
    
    return svd_matrix

def SVD_Np(matrix_representation):
    """
    Perform Singular Value Decomposition (SVD) on the given matrix.

    Parameters:
    matrix_representation (array-like): Matrix representation of the data.

    Returns:
    U (array-like): Left singular vectors.
    s (array-like): Singular values.
    V (array-like): Right singular vectors.
    """
    # Perform SVD on the given matrix
    U, s, V = np.linalg.svd(matrix_representation, full_matrices=True)
    return U, s, V

def get_top_N_documents_in_top_M_topics(U, original_documents, N, M):
    '''
    This function returns the top N documents in each of the top M topics and sorts the documents by their indices, then merges them into one document.

    Args:
        U (array-like): The matrix containing the topic-document distribution.
        original_documents (list): The list of original documents.
        N (int): The number of top documents to retrieve in each topic.
        M (int): The number of top topics to consider.

    Returns:
        list: A list of top N documents in each of the top M topics.
        list: A list of lists containing the indices of the top documents in each topic.
    '''
    # Initialize the lists to store the top N documents in each of the top M topics
    top_N_document_in_top_M_topic = []
    documents_set_indeces = set()
    documents_indeces = []
    
    # Get the minimum of the number of topics and the number of columns in U
    M = min(M, U.shape[1])
    
    # Iterate over the top M topics
    for i in range(M):
        # Initialize the string to store the top N documents in the topic
        documents = ''
        j = 1
        top_document_indices = []
        skip = 0
        
        # Get the top N documents in the topic
        while j + skip <= N + skip and j + skip <= U.shape[0]:
            top_document_index = np.abs(U[:, i]).argsort()[-j-skip]
            
            # Check if the document index is already in the set
            if top_document_index not in documents_set_indeces:
                documents_set_indeces.add(top_document_index)
                top_document_indices.append(top_document_index)
                j += 1
            else:
                skip += 1
        
        # Sort the document indices
        top_document_indices.sort()
        
        # Append the document indices to the list
        documents_indeces.append(top_document_indices)
        
        # Merge the top N documents into one document
        for index in top_document_indices:
            documents += original_documents[index] + '. '
        
        # Append the merged document to the list
        top_N_document_in_top_M_topic.append(documents)
    
    # Return the list of top N documents in each of the top M topics
    return top_N_document_in_top_M_topic, documents_indeces

def Summarize_Document(document, num_sentences):
    """
    Summarizes a given document by extracting the most important sentences.

    Args:
        document (str): The document to be summarized.
        num_sentences (int): The number of sentences to include in the summary.

    Returns:
        list: A list of the most important sentences in the document.

    """
    # Tokenize the document into sentences
    sentences = sent_tokenize(document)
    
    # Limit the number of sentences to summarize
    num_sentences = min(num_sentences, len(sentences))
    
    # Initialize lists for original sentences, preprocessed sentences, and vocabulary
    original_sentences = []
    preprocessed_sentences = []
    vocabulary = []
    
    # Preprocess each sentence in the document
    for i in range(len(sentences)):
        original_sentences, preprocessed_sentences, vocabulary = preprocess_text(sentences[i], original_sentences, preprocessed_sentences, vocabulary)
    
    # Get the sentence embeddings using the getDocumentsVector function
    sentenceEmbeddings = getDocumentsVector(preprocessed_sentences)
    
    # Perform Singular Value Decomposition (SVD) on the sentence embeddings
    U, s, V = SVD_Np(sentenceEmbeddings)
    
    # Initialize a list to store the summarized sentences
    summarization = []
    
    # Get the top sentences based on the SVD matrix
    top_sentence_indices = np.abs(U[:, 0]).argsort()[-num_sentences:][::-1]
    
    # Sort the sentence indices
    top_sentence_indices.sort()
    
    # Iterate over the top sentence indices
    for j in top_sentence_indices:
        # Get the original sentence
        sentence = original_sentences[j]
        
        # Clean up the sentence
        sentence = sentence.strip()
        sentence += '.'
        sentence = re.sub(r'\.+', '.', sentence)
        sentence = re.sub(r'\s+', ' ', sentence)
        
        # Check if the sentence starts with a capital letter
        if re.search(r'[A-Z]', sentence) is None:
            continue
        
        # Remove leading non-alphabetic characters
        sentence = sentence[re.search(r'[A-Z]', sentence).start():]
        
        # Add the sentence to the summarization list
        summarization.append(sentence)
    
    # Return the summarized sentences
    return summarization

# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    """
    Perform mean pooling on the token embeddings, taking the attention mask into account for correct averaging.

    Parameters:
    - model_output (tuple): The output of the model, containing the token embeddings.
    - attention_mask (tensor): The attention mask.

    Returns:
    - pooled_embeddings (tensor): The mean-pooled embeddings.

    """
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    pooled_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return pooled_embeddings

def getDocumentsVector(documents):
    """
    Compute sentence embeddings for a list of documents.

    Args:
        documents (list): A list of documents (strings).

    Returns:
        numpy.ndarray: A numpy array containing the sentence embeddings.

    """

    # Load model from HuggingFace Hub
    tokenizer = AutoTokenizer.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    model = AutoModel.from_pretrained('dmlls/all-mpnet-base-v2-negation')

    # Initialize an empty list to store the sentence embeddings
    sentence_embeddings = []

    # Iterate over each document
    for document in documents:
        # Tokenize the document
        encoded_input = tokenizer(document, padding=True, truncation=True, return_tensors='pt')

        # Compute token embeddings
        with torch.no_grad():
            model_output = model(**encoded_input)

        # Perform pooling
        document_embedding = mean_pooling(model_output, encoded_input['attention_mask'])

        # Normalize the document embedding
        document_embedding = F.normalize(document_embedding, p=2, dim=1)

        # Append the document embedding to the list
        sentence_embeddings.append(document_embedding)

    # Concatenate the document embeddings along the first dimension
    sentence_embeddings = torch.cat(sentence_embeddings, dim=0)

    # Convert sentence_embeddings to numpy array
    sentence_embeddings = sentence_embeddings.numpy()

    return sentence_embeddings

def getAllDocumentsFromGivenString(text):
    """
    Preprocesses a given text and returns the original documents, preprocessed documents, and vocabulary.

    Args:
        text (str): The input text.

    Returns:
        list: A list of original documents.
        list: A list of preprocessed documents.
        list: A list of vocabulary.

    """
    original_documents = []
    preprocessed_documents = []
    vocabulary = []
    
    # Split the text into individual documents
    documents = text.split('\n')
    
    # Iterate over each document
    for document in documents:
        # Skip empty documents
        if document == '':
            continue
        
        # Perform spell checking and correction using language_tool_python
        matches = tool.check(document)
        document = language_tool_python.utils.correct(document, matches)
        
        # Preprocess the document and update the original documents, preprocessed documents, and vocabulary lists
        original_documents, preprocessed_documents, vocabulary = preprocess_text(document, original_documents, preprocessed_documents, vocabulary, isText=True)
    
    # Return the original documents, preprocessed documents, and vocabulary
    return original_documents, preprocessed_documents, vocabulary

def summarization(numberOfTopics, numberOfDocuments, numberOfSentences, folderPath = None, text = None, isText = False):
    """
    Summarizes documents based on topic-document distribution using Singular Value Decomposition (SVD).

    Args:
        numberOfTopics (int): The number of topics to consider.
        numberOfDocuments (int): The number of top documents to retrieve in each topic.
        numberOfSentences (int): The number of sentences to include in the summary.
        folderPath (str, optional): The path to the folder containing the PDF files. Defaults to None.
        text (str, optional): The input text. Defaults to None.
        isText (bool, optional): Indicates whether the input is a text or a folder path. Defaults to False.

    Returns:
        list: A list of the most important sentences in the documents.
        list: A list of the original paragraphs containing the important sentences.
    """

    sentences = []
    paragraphs = []

    # Get the original documents, preprocessed documents, and vocabulary
    if isText:
        original_documents, preprocessed_documents, vocabulary = getAllDocumentsFromGivenString(text)
    else:
        original_documents, preprocessed_documents, vocabulary = getAllDocuments(folderPath)
        

    # Compute sentence embeddings or TF-IDF for the preprocessed documents
    documentsEmbeddings = getDocumentsVector(preprocessed_documents)
    # tfidf_matrix = TF_IDF(preprocessed_documents, vocabulary)

    # Perform Singular Value Decomposition (SVD) on the document embeddings
    U, s, V = SVD_Np(documentsEmbeddings)

    # Get the top N documents in each of the top M topics
    top_N_document_in_top_M_topic, documents_indeces = get_top_N_documents_in_top_M_topics(U, original_documents, numberOfDocuments, numberOfTopics)

    # Keep track of unique sentences to avoid duplicates
    unique_sentences = set()

    # Iterate over the top N documents in each of the top M topics
    for idx, document in enumerate(top_N_document_in_top_M_topic):
        if document == '':
            continue

        # Summarize the document and get the most important sentences
        summarization = Summarize_Document(document, numberOfSentences)

        # Iterate over the summarized sentences
        for sentence in summarization:
            # Iterate over the indices of the top documents in each topic
            for index in documents_indeces[idx]:
                originalDoc = original_documents[index]
                
                sentence = sentence.strip()
                sentence = sentence.strip('.')
                sentence = sentence.strip(':')

                # Check if the sentence is present in the original document and is not a duplicate
                if sentence in originalDoc and sentence not in unique_sentences:
                    paragraphs.append(original_documents[index])
                    sentences.append(sentence)
                    unique_sentences.add(sentence)
                    break

    # Return the most important sentences and the original paragraphs containing them
    return sentences, paragraphs

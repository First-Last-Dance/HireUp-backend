from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

#####################################

import fasttext
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import os

nltk.download('punkt')
nltk.download('stopwords')


model_en = fasttext.load_model("models\HireUp_interview\\cc.en.300.bin")
print("Current working directory:", os.getcwd())


negativeWords = {
    "bad": "not good",
    "ugly": "not beautiful",
    "poor": "not rich",
    "sad": "not happy",
    "weak": "not strong",
    "dirty": "not clean",
    "lazy": "not hardworking",
    "stupid": "not intelligent",
    "boring": "not interesting",
    "cruel": "not kind",
    "difficult": "not easy",
    "dishonest": "not honest",
    "impolite": "not polite",
    "incompetent": "not competent",
    "unfriendly": "not friendly",
    "unhealthy": "not healthy",
    "unlucky": "not lucky",
    "unpopular": "not popular",
    "unreliable": "not reliable",
    "unsuccessful": "not successful",
    "untrustworthy": "not trustworthy",
    "cowardly": "not brave",
    "careless": "not careful",
    "selfish": "not generous",
    "mean": "not nice",
    "pessimistic": "not optimistic",
    "insensitive": "not sensitive",
    "ignorant": "not knowledgeable",
    "arrogant": "not humble",
    "greedy": "not generous",
    "jealous": "not content",
    "annoying": "not pleasant",
    "apathetic": "not empathetic",
    "insecure": "not confident",
    "messy": "not organized",
    "negligent": "not attentive",
    "rebellious": "not obedient",
    "rude": "not polite",
    "skeptical": "not trusting",
    "tired": "not energetic",
    "ungrateful": "not thankful",
    "unhappy": "not joyful"
}


#####################################


# Mean Pooling - Take attention mask into account for correct averaging
# def mean_pooling(model_output, attention_mask):
#     """
#     Perform mean pooling on the token embeddings, taking the attention mask into account for correct averaging.

#     Parameters:
#     - model_output (tuple): The output of the model, containing the token embeddings.
#     - attention_mask (tensor): The attention mask.

#     Returns:
#     - pooled_embeddings (tensor): The mean-pooled embeddings.

#     """
#     token_embeddings = model_output[0] # First element of model_output contains all token embeddings
#     input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
#     pooled_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
#     return pooled_embeddings


###########################################################################


# def getSimilarity(applicantAnswers, correctAnswers):
#     """
#     Calculate the cosine similarity between the embeddings of two sets of answers.

#     Parameters:
#     - applicantAnswers (str): The answers provided by the applicant.
#     - correctAnswers (str): The correct answers.

#     Returns:
#     - similarity (float): The cosine similarity between the embeddings of the two sets of answers.
#     """

#     # Load model from HuggingFace Hub
#     tokenizer = AutoTokenizer.from_pretrained('dmlls/all-mpnet-base-v2-negation')
#     model = AutoModel.from_pretrained('dmlls/all-mpnet-base-v2-negation')

#     # Sentences we want sentence embeddings for
#     sentences = [
#         applicantAnswers,
#         correctAnswers
#     ]

#     # Tokenize sentences
#     encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

#     # Compute token embeddings
#     with torch.no_grad():
#         model_output = model(**encoded_input)

#     # Perform pooling
#     sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

#     # Normalize embeddings
#     sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

#     # Convert sentence_embeddings to numpy array
#     sentence_embeddings = sentence_embeddings.numpy()

#     # Calculate cosine similarity
#     similarity = cosine_similarity(sentence_embeddings[0].reshape(1,-1), sentence_embeddings[1].reshape(1,-1))[0][0]

#     return similarity


###########################################################################
################################## New #########################################



def replaceNegativeWords(sentence):
    temp = [negativeWords[word] if word in negativeWords else word for word in sentence.split()]
    return " ".join(temp)


def preprocessSentence(sentence):
    
    sentence = sentence.lower()
    
    tokens = word_tokenize(sentence)
    
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    tokens = [re.sub(r'[^a-zA-Z]', '', word) for word in tokens if word.isalnum()]
    
    preprocessed_sentence = ' '.join(tokens)
    
    return preprocessed_sentence



def countNegations(tokens):
    negation_words = {'not', 'no', 'never', 'none'}
    count = sum(1 for token in tokens if token in negation_words)
    return count


def getSimilarity(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    
    s1 = replaceNegativeWords(s1)
    s2 = replaceNegativeWords(s2)
    
    neg_count1 = countNegations(s1.split())
    neg_count2 = countNegations(s2.split())
    
    tokens1 = preprocessSentence(s1)
    tokens2 = preprocessSentence(s2)
    
    
    embedding1 = model_en.get_sentence_vector(tokens1)
    embedding2 = model_en.get_sentence_vector(tokens2)

    embedding1 *= (-1) ** neg_count1
    embedding2 *= (-1) ** neg_count2

    embedding1 = embedding1.reshape(1, -1)
    embedding2 = embedding2.reshape(1, -1)

    similarity_score = cosine_similarity(embedding1, embedding2)[0][0]

    return similarity_score

###########################################################################
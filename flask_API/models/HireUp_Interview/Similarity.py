from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

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

def getSimilarity(applicantAnswers, correctAnswers):
    """
    Calculate the cosine similarity between the embeddings of two sets of answers.

    Parameters:
    - applicantAnswers (str): The answers provided by the applicant.
    - correctAnswers (str): The correct answers.

    Returns:
    - similarity (float): The cosine similarity between the embeddings of the two sets of answers.
    """

    # Load model from HuggingFace Hub
    tokenizer = AutoTokenizer.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    model = AutoModel.from_pretrained('dmlls/all-mpnet-base-v2-negation')

    # Sentences we want sentence embeddings for
    sentences = [
        applicantAnswers,
        correctAnswers
    ]

    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    # Convert sentence_embeddings to numpy array
    sentence_embeddings = sentence_embeddings.numpy()

    # Calculate cosine similarity
    similarity = cosine_similarity(sentence_embeddings[0].reshape(1,-1), sentence_embeddings[1].reshape(1,-1))[0][0]

    return similarity
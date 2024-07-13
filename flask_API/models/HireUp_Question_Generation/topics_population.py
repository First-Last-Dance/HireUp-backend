import os
import time
from dotenv import load_dotenv
import requests
import QG
import Text_Summarization
from Text_Summarization import summarization

# Define the generate_questions function as provided
def myScore(template, question, answer):
    """
    Calculate the score for a generated question-answer pair based on the template, question, and answer.

    Parameters:
    template (str): The question template.
    question (str): The generated question.
    answer (str): The generated answer.

    Returns:
    float: The calculated score for the question-answer pair.
    """
    # Remove the question mark from the question and strip leading/trailing whitespaces
    question = question.strip('?').strip()
    
    # Split the template into words
    words = template.split()
    
    # Count the number of constant words in the template
    count = 0
    for word in words:
        if not ((word.startswith('[') and word.endswith(']')) or (word.startswith('<') and word.endswith('>'))):
            count += 1
    
    # Calculate the score by getting the ratio of the number of non-constant words in the question to the total number of words in the question
    score_1 = 1 - count/len(question.split())
    
    # Calculate the score by getting the ratio of the difference in length between the answer and question to the sum of their lengths
    question_length = len(question.split()) - count
    answer_length = len(answer.split())
    score_2 = (answer_length - question_length)/(answer_length + question_length)
    
    return 0.2 * score_1 + 0.2 * score_2

def generate_questions(folderPath='', numberOfTopics=10, numberOfDocuments=3, numberOfSentences=1, topQuestions=10, text='', isText=False):
    """
    Generate questions for a given folder path or text.

    Parameters:
    folderPath (str): The path to the folder containing the documents.
    numberOfTopics (int): The number of topics to generate questions for.
    numberOfDocuments (int): The number of documents to consider for each topic.
    numberOfSentences (int): The number of sentences to consider for each document.
    topQuestions (int): The number of top questions to select for each sentence.
    text (str): The text to generate questions for.
    isText (bool): A flag indicating whether the input is text or a folder path.

    Returns:
    dict: A dictionary containing the generated questions for each sentence.
    """
    try:
        # Perform text summarization to get most important sentences and paragraphs from which sentences are extracted
        sentences, paragraphs = summarization(numberOfTopics, numberOfDocuments, numberOfSentences, folderPath=folderPath, text=text, isText=isText)
        
        # Load the question generation model
        unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGuards, answerGuards, questionWordCount, questionCount = QG.loadModel('models\\HireUp_Question_Generation\\Trained_Model_Dev')
        
        # Get the folder name from the folder path
        normalized_path = os.path.normpath(folderPath)
        folder_name = os.path.basename(normalized_path)
        
        # Initialize the result dictionary
        result = {
            "name": folder_name,
            "questions": []
        }
        
        # Generate questions for each sentence
        for sentence_idx, sentence in enumerate(sentences):
            questionsWithScore = []
            uniqueQuestions = set()
            
            # Get the sentence structure
            doc, results = QG.getSentenceStructure(sentence)
            
            # Skip if the sentence structure is not available
            if results is None:
                continue
            
            # Generate questions for each question template
            for i in range(len(questionTemplates)):
                question = QG.generateQuestion(sentence, questionTemplates[i], questionGuards[i])
                
                # Skip if the question is already generated
                if question in uniqueQuestions:
                    continue
                
                answer = QG.generateQuestion(sentence, answerTemplates[i], answerGuards[i])
                
                # Add the question-answer pair to the list if both question and answer are generated
                if question is not None and answer is not None:
                    score = myScore(questionTemplates[i], question, answer) + 0.6 * QG.calculateScore(question, unigram, bigram, trigram, wordCount, answer, questionWordCount, questionCount)
                    questionsWithScore.append((question, answer, score))
                    uniqueQuestions.add(question)
            
            # Sort the questions based on score in descending order
            questionsWithScore.sort(key=lambda x: x[2], reverse=True)
            
            # Select the top questions
            length = min(topQuestions, len(questionsWithScore))
            question_list = []
            for i in range(length):
                print(questionsWithScore[i][0])   
                print("Answer: ", questionsWithScore[i][1])
                question_list.append(questionsWithScore[i][0])
            
            # Add the questions and answer to the result dictionary
            if question_list:
                result["questions"].append({
                    "question": question_list,
                    "answer": paragraphs[sentence_idx]
                })
        
        return result

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

        
def wait_for_express_server():
    print("Waiting for the Express server to start...")
    while True:
        try:
            # Get the address of the Express server from the environment variable
            express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
            # Send a GET request to the Express server
            response = requests.get(express_server_address)
            if response.status_code == 200:
                print("Express server started.")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        
def login():
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
    # Get the login credentials from the environment variables
    email = os.getenv('EXPRESS_SERVER_EMAIL', 'email@example.com')
    password = os.getenv('EXPRESS_SERVER_PASSWORD', 'password')
    # Send a POST request to the Express server to login
    response = requests.post(f"{express_server_address}/account/logIn", json={"email": email, "password": password})
    if response.status_code == 200:
        print("Login successful.")
        return response.json().get('token')
    else:
        print("Login failed.")
        
def send_topic(topic, token):
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
    # Send a POST request to the Express server to add the topic
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{express_server_address}/topic", json={"name": topic['name'], "questions": topic['questions']}, headers=headers)
    if response.status_code == 201:
        print(f"Topic '{topic['name']}' added successfully.")
    else:
        print(response)
        print(f"Failed to add topic '{topic['name']}'.")

# Main function to check directories and call generate_questions
def main(base_directory, processed_file):
    
    # Load environment variables from .env file
    load_dotenv()
    
    wait_for_express_server()
    
    token = login()
    
    print(f"Processing directories in {base_directory}...")
    # Read the list of processed directories from the file
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_directories = set(f.read().splitlines())
    else:
        processed_directories = set()

    # Get the list of subdirectories in the base directory
    subdirectories = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    print(f"Found {len(subdirectories)} subdirectories.")

    # Process each subdirectory
    for subdir in subdirectories:
        if subdir not in processed_directories:
            subdir_path = os.path.join(base_directory, subdir)
            if os.path.exists(subdir_path):
                print(f"Processing directory: {subdir_path}")
                topic = generate_questions(folderPath=subdir_path+"/")
                print(f"Generated questions for topic: {topic['name']}")
                send_topic(topic, token)
                processed_directories.add(subdir)
            else:
                print(f"Directory does not exist: {subdir_path}")

    # Write the updated list of processed directories to the file
    with open(processed_file, 'w') as f:
        for dir in processed_directories:
            f.write(f"{dir}\n")
            
    print("Processing complete.")

# Usage example
base_directory = 'topics_data'
processed_file = 'topics.txt'
if __name__ == "__main__":
    main(base_directory, processed_file)

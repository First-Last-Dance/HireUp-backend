import os
import time
from dotenv import load_dotenv
import requests
import QG
import Text_Summarization
from Text_Summarization import summarization

# Define the generate_questions function as provided
def myScore(template):
    words = template.split()
    count = 0
    for word in words:
        if not (word.startswith('[') and word.endswith(']')) or (word.startswith('<') and word.endswith('>')):
            count += 1
    return 1 - count/len(words)

def generate_questions(folderPath='', numberOfTopics=10, numberOfDocuments=3, numberOfSentences=1, topQuestions=1, text='', isText=False):
    try:
        sentences, paragraphs = summarization(numberOfTopics, numberOfDocuments, numberOfSentences, folderPath=folderPath, text=text, isText=isText)
        unigram, bigram, trigram, wordCount, questionTemplates, answerTemplates, questionGaurds, answerGaurds, questionWordCount, questionCount = QG.loadModel('models\HireUp_Question_Generation\Trained_Model_Dev')
        normalized_path = os.path.normpath(folderPath)
        folder_name = os.path.basename(normalized_path)
        result = {
            "name": folder_name,
            "questions": []
        }
        
        for sentence in sentences:
            questionsWithScore = []
            uniqueQuestions = set()
            doc, results = QG.getSentenceStructure(sentence)
            if results is None:
                continue
            for i in range(len(questionTemplates)):
                question = QG.generateQuestion(sentence, questionTemplates[i], questionGaurds[i])
                if question in uniqueQuestions:
                    continue
                answer = QG.generateQuestion(sentence, answerTemplates[i], answerGaurds[i])
                if question is not None and answer is not None:
                    questionsWithScore.append((question, answer, myScore(questionTemplates[i]), QG.calculateScore(question, unigram, bigram, trigram, wordCount, answer, questionWordCount, questionCount)))
                    uniqueQuestions.add(question)

            questionsWithScore.sort(key=lambda x: (x[2], x[3]), reverse=True)
            length = min(topQuestions, len(questionsWithScore))
            for i in range(length):
                print(questionsWithScore[i][0])   
                print("Answer: ", questionsWithScore[i][1])
                result["questions"].append({
                    "question": questionsWithScore[i][0],
                    "answer": sentence
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

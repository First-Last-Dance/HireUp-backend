import TopicModel, { ITopic, QuestionData } from './model';

/**
 * Retrieves all topics from the database.
 * @returns A list of all topics.
 */

export async function getAllTopics(): Promise<ITopic[]> {
  return TopicModel.find().catch((error) => {
    throw error;
  });
}

export async function getTopicsNames(): Promise<string[]> {
  const topics = await TopicModel.find({}, { name: 1 }).catch((err) => {
    throw err;
  });
  const topicsNames: string[] = [];
  topics.forEach((topic) => {
    topicsNames.push(topic.name);
  });
  return topicsNames;
}

/**
 * Adds a new topic to the database.
 * @param topicName The name of the topic to add.
 * @param questions The questions for the topic.
 * @returns The newly created topic document.
 */

export async function addTopic(
  topicName: string,
  questions: Array<QuestionData>,
): Promise<ITopic> {
  const newTopic = new TopicModel({ name: topicName, questions: questions });
  return newTopic.save().catch((error) => {
    throw error;
  });
}

/**
 * Deletes a topic from the database by its name.
 * @param topicName The name of the topic to delete.
 * @returns True if the topic is deleted successfully, otherwise false.
 */

export async function deleteTopicByName(topicName: string): Promise<boolean> {
  return TopicModel.deleteOne({ name: topicName })

    .then((result) => result.deletedCount !== 0)
    .catch((error) => {
      throw error;
    });
}

/**
 * Retrieves a topic from the database by its name.
 * @param topicName The name of the topic to retrieve.
 * @returns The topic document if found, otherwise null.
 */

export async function getTopicByName(
  topicName: string,
): Promise<ITopic | null> {
  return TopicModel.findOne({ name: topicName }).catch((error) => {
    throw error;
  });
}

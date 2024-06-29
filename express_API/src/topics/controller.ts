import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import { QuestionData, TopicData } from './model';
import * as Topic from './service';

// Get all topics' names
export async function getTopicsNames(): Promise<string[]> {
  return Topic.getTopicsNames().catch((error) => {
    throw error;
  });
}

// Get all given topics
export async function getTopics(topics: string[]): Promise<TopicData[]> {
  const topicsData: TopicData[] = [];
  for (const topicName of topics) {
    const topic = await Topic.getTopicByName(topicName).catch((error) => {
      throw error;
    });
    if (!topic) {
      throw new CodedError(ErrorMessage.TopicNotFound, ErrorCode.NotFound);
    }
    const topicData: TopicData = {
      name: topic.name,
      questions: topic.questions,
    };
    topicsData.push(topicData);
  }
  return topicsData;
}

// Add a new topic

export async function addTopic(
  topicName: string,
  questions: QuestionData[],
): Promise<TopicData> {
  const topic = await Topic.getTopicByName(topicName).catch((error) => {
    throw error;
  });
  if (topic) {
    throw new CodedError(
      ErrorMessage.TopicAlreadyExists,
      ErrorCode.InvalidParameter,
    );
  }
  const newTopic = await Topic.addTopic(topicName, questions).catch((error) => {
    throw error;
  });
  const topicData: TopicData = {
    name: newTopic.name,
    questions: newTopic.questions,
  };
  return topicData;
}

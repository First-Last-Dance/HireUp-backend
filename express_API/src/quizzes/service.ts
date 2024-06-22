import QuizModel, { IQuiz, QuizData } from './model';

// Function to add a new quiz
export const addQuiz = async (quizData: QuizData): Promise<IQuiz> => {
  const quiz = new QuizModel(quizData);
  return quiz.save();
};

// Function to get a quiz by its ID
export const getQuizById = async (quizId: string): Promise<IQuiz | null> => {
  return QuizModel.findById(quizId).exec();
};

// Function to get a quiz by its job ID
export const getQuizByJobID = async (jobId: string): Promise<IQuiz | null> => {
  return QuizModel.findOne({ jobID: jobId }).exec();
};

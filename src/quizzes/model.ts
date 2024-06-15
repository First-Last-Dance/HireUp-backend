import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for a question
export interface QuestionData {
  answers: string[];
  correctAnswer: string;
  score: number;
  text: string;
}

// Interface representing the structure of data for an quiz
export interface QuizData {
  jobID?: string;
  questions?: QuestionData[];
}

// Interface representing a mongoose document for an quiz
export interface IQuiz extends mongoose.Document {
  jobID?: mongoose.Types.ObjectId;
  questions?: QuestionData[];
}

// Define the schema for the quiz collection
const quizSchema = new Schema({
  jobID: { type: mongoose.Types.ObjectId, required: true },
  questions: { type: Array, required: true },
});

// Create a mongoose model based on the schema
const QuizModel = mongoose.model<IQuiz>('Quiz', quizSchema);

export default QuizModel;

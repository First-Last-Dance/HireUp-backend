import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for a question
export interface QuestionData {
  answers: string[];
  correctAnswer?: string;
  score?: number;
  text: string;
}

// Interface representing the structure of data for an quiz
export interface QuizData {
  jobID?: string;
  questions?: QuestionData[];
  applicationID?: string;
  quizDeadline?: Date;
  passRatio?: number;
  quizDurationInMinutes?: number;
}

// Interface representing a mongoose document for an quiz
export interface IQuiz extends mongoose.Document {
  jobID: mongoose.Types.ObjectId;
  questions: QuestionData[];
  passRatio: number;
  quizDurationInMinutes: number;
}

// Define the schema for the quiz collection
const quizSchema = new Schema({
  jobID: { type: mongoose.Types.ObjectId, required: true },
  questions: { type: Array, required: true },
  passRatio: { type: Number, required: true, default: 0.5 },
  quizDurationInMinutes: { type: Number, required: true, default: 10 },
});

// Create a mongoose model based on the schema
const QuizModel = mongoose.model<IQuiz>('Quiz', quizSchema);

export default QuizModel;

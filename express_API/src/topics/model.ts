import mongoose, { Schema, Document } from 'mongoose';

export interface QuestionData {
  question: string;
  answer: string;
}

export interface TopicData {
  name: string;
  questions: QuestionData[];
}

export interface ITopic extends Document {
  name: string;
  questions: QuestionData[];
}

const TopicSchema: Schema = new Schema({
  name: { type: String, required: true, unique: true },
  questions: { type: Array, required: true },
});

export default mongoose.model<ITopic>('Topic', TopicSchema);

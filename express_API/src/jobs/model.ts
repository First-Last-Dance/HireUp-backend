import mongoose, { Schema, Document } from 'mongoose';

export interface QuestionData {
  question: string;
  answer: string;
}

export interface JobData {
  title?: string;
  id?: string;
  description?: string;
  requiredSkills?: string[]; // Reference to Skills model
  salary?: string;
  companyName?: string;
  companyID?: string;
  applicationDeadline?: Date;
  quizDeadline?: Date;
  interviewDeadline?: Date;
  quizRequired?: boolean;
  published?: boolean;
  questions?: QuestionData[];
  numberOfInterviewQuestions?: number;
}
export interface IJob extends Document {
  title: string;
  description: string;
  requiredSkills: { type: mongoose.Types.ObjectId; ref: 'Skill' }[]; // Reference to Skills model
  salary: string;
  companyID: { type: mongoose.Types.ObjectId; ref: 'Company' }; // Reference to Companies model;
  applicationDeadline: Date;
  quizDeadline: Date;
  interviewDeadline: Date;
  quizRequired: boolean;
  published: boolean;
  createdAt: Date;
  questions?: QuestionData[];
  numberOfInterviewQuestions?: number;
}

const jobSchema: Schema = new Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  requiredSkills: {
    type: [{ type: mongoose.Types.ObjectId, ref: 'Skill' }],
    required: true,
  },
  salary: { type: String, required: true },
  companyID: { type: mongoose.Types.ObjectId, ref: 'Company', required: true },
  applicationDeadline: { type: Date, required: true },
  quizDeadline: { type: Date, required: true },
  interviewDeadline: { type: Date, required: true },
  quizRequired: { type: Boolean, required: true },
  published: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  questions: { type: Array },
  numberOfInterviewQuestions: { type: Number },
});

const Job = mongoose.model<IJob>('Job', jobSchema);

export default Job;

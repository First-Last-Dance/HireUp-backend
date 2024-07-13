import e from 'express';
import mongoose from 'mongoose';

const { Schema } = mongoose;

export interface EmotionData {
  emotion?: string;
  percentage?: number;
}

export interface InterviewQuestionData {
  questionEyeCheating?: number;
  questionFaceSpeechCheating?: number;
  questionSimilarity?: number;
  questionEmotions?: EmotionData[];
}

// Interface representing the structure of data for an application
export interface ApplicationData {
  applicantID?: string;
  applicantName?: string;
  jobID?: string;
  status?: string;
  applicationID?: string;
  companyName?: string;
  title?: string;
  steps?: string[];
  quizEyeCheating?: number;
  quizFaceSpeechCheating?: number;
  quizScore?: number;
  interviewQuestionsData?: InterviewQuestionData[];
  averageSimilarity?: number;
  totalSimilarity?: number;
  questionsCount?: number;
  quizEyeCheatingDurations?: Array<any>;
  quizSpeakingCheatingDurations?: Array<any>;
}

// Interface representing a mongoose document for an applicant
export interface IApplication extends mongoose.Document {
  applicantID: mongoose.Types.ObjectId;
  jobID: mongoose.Types.ObjectId;
  status: string;
  steps: string[];
  createdAt: Date;
  quizDeadline?: Date;
  interviewDeadline?: Date;
  quizEyeCheating?: number;
  quizFaceSpeechCheating?: number;
  interviewQuestionsData?: InterviewQuestionData[];
  quizScore?: number;
  averageSimilarity?: number;
  totalSimilarity?: number;
  questionsCount?: number;
  quizEyeCheatingDurations?: Array<any>;
  quizSpeakingCheatingDurations?: Array<any>;
}

// Define the schema for the application collection
const applicationSchema = new Schema({
  applicantID: {
    type: mongoose.Types.ObjectId,
    ref: 'Applicant',
    required: true,
  },
  jobID: { type: mongoose.Types.ObjectId, ref: 'Job', required: true },
  status: { type: String, required: true },
  steps: [{ type: String, required: true }],
  createdAt: { type: Date, default: Date.now },
  quizDeadline: { type: Date },
  interviewDeadline: { type: Date },
  quizEyeCheating: { type: Number },
  quizFaceSpeechCheating: { type: Number },
  interviewQuestionsData: [
    {
      questionEyeCheating: { type: Number },
      questionFaceSpeechCheating: { type: Number },
      questionSimilarity: { type: Number },
      questionEmotions: [
        {
          emotion: { type: String },
          percentage: { type: Number },
        },
      ],
    },
  ],
  quizScore: { type: Number },
  averageSimilarity: { type: Number },
  totalSimilarity: { type: Number },
  questionsCount: { type: Number },
  quizEyeCheatingDurations: [{ type: Array }],
  quizSpeakingCheatingDurations: [{ type: Array }],
});

// Create a mongoose model based on the schema
const ApplicationModel = mongoose.model<IApplication>(
  'Application',
  applicationSchema,
);

export default ApplicationModel;

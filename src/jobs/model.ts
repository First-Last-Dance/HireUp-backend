import mongoose, { Schema, Document } from 'mongoose';

export interface JobData {
  title?: string;
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
}
export interface IJob extends Document {
  title: string;
  description: string;
  requiredSkills: { type: mongoose.Types.ObjectId; ref: 'Skill' }[]; // Reference to Skills model
  salary: string;
  company: { type: mongoose.Types.ObjectId; ref: 'Company' }; // Reference to Companies model;
  applicationDeadline: Date;
  quizDeadline: Date;
  interviewDeadline: Date;
  quizRequired: boolean;
  published: boolean;
}

const jobSchema: Schema = new Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  requiredSkills: {
    type: [{ type: mongoose.Types.ObjectId, ref: 'Skill' }],
    required: true,
  },
  salary: { type: String, required: true },
  company: { type: mongoose.Types.ObjectId, ref: 'Company', required: true },
  applicationDeadline: { type: Date, required: true },
  quizDeadline: { type: Date, required: true },
  interviewDeadline: { type: Date, required: true },
  quizRequired: { type: Boolean, required: true },
  published: { type: Boolean, default: false },
});

const Job = mongoose.model<IJob>('Job', jobSchema);

export default Job;

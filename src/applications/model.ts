import e from 'express';
import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for an application
export interface ApplicationData {
  applicantID?: string;
  jobID?: string;
  status?: string;
  applicationID?: string;
  companyName?: string;
  title?: string;
  steps?: string[];
}

// Interface representing a mongoose document for an applicant
export interface IApplication extends mongoose.Document {
  applicantID: mongoose.Types.ObjectId;
  jobID: mongoose.Types.ObjectId;
  status: string;
  steps: string[];
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
});

// Create a mongoose model based on the schema
const ApplicationModel = mongoose.model<IApplication>(
  'Application',
  applicationSchema,
);

export default ApplicationModel;

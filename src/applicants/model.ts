import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for an applicant
export interface ApplicantData {
  email?: string;
  firstName?: string;
  middleName?: string;
  lastName?: string;
  phoneNumber?: string;
  nationalIDNumber?: string;
  profilePhoto?: string;
  nationalIDPhotoFace?: string;
  nationalIDPhotoBack?: string;
  skills?: string[]; // Reference to Skills model
}

// Interface representing a mongoose document for an applicant
export interface IApplicant extends mongoose.Document {
  email: string;
  firstName: string;
  middleName: string;
  lastName: string;
  phoneNumber: string;
  nationalIDNumber: string;
  profilePhoto: string;
  nationalIDPhotoFace: string;
  nationalIDPhotoBack: string;
  skills: { type: mongoose.Types.ObjectId; ref: 'Skill' }[]; // Reference to Skills model
}

// Define the schema for the applicant collection
const applicantSchema = new Schema({
  email: { type: String, required: true, unique: true }, // Email field is required and unique
  firstName: { type: String, required: true }, // First name field is required
  middleName: { type: String, required: true }, // Middle name field is required
  lastName: { type: String, required: true }, // Last name field is required
  phoneNumber: { type: String, required: true, unique: true }, // Phone number field is required and unique
  nationalIDNumber: { type: String, required: true, unique: true }, // National ID number field is required and unique
  profilePhoto: { type: String, default: '' }, // Default profile photo is an empty string
  nationalIDPhotoFace: { type: String, default: '' }, // Default national ID photo (face) is an empty string
  nationalIDPhotoBack: { type: String, default: '' }, // Default national ID photo (back) is an empty string
  skills: [{ type: mongoose.Types.ObjectId, ref: 'Skill' }], // Reference to Skills model
});

// Create a mongoose model based on the schema
const ApplicantModel = mongoose.model<IApplicant>('Applicant', applicantSchema);

export default ApplicantModel;

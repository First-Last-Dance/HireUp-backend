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
  email: { type: String, required: true, unique: true }, // Required and unique email
  firstName: { type: String, required: true }, // Required first name
  middleName: { type: String, required: true }, // Required middle name
  lastName: { type: String, required: true }, // Required last name
  phoneNumber: { type: String, required: true, unique: true }, // Required and unique phone number
  // Required and unique national ID number
  nationalIDNumber: { type: String, required: true, unique: true },
  profilePhoto: { type: String, default: '' }, // Default profile photo: empty string
  nationalIDPhotoFace: { type: String, default: '' }, // Default national ID photo (face): empty string
  nationalIDPhotoBack: { type: String, default: '' }, // Default national ID photo (back): empty string
  skills: [{ type: mongoose.Types.ObjectId, ref: 'Skill' }], // Reference to Skills model
});

// Create a mongoose model based on the schema
const ApplicantModel = mongoose.model<IApplicant>('Applicant', applicantSchema);

export default ApplicantModel;

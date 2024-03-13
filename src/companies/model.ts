import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for an company
export interface CompanyData {
  email?: string;
  name?: string;
  description?: string;
  address?: string;
  logo?: string;
}

// Interface representing a mongoose document for an company
export interface ICompany extends mongoose.Document {
  email?: string;
  name?: string;
  description?: string;
  address?: string;
  logo?: string;
}

// Define the schema for the company collection
const companySchema = new Schema({
  email: { type: String, required: true, unique: true }, // Email field is required and unique
  name: { type: String, required: true }, // Name field is required
  description: { type: String, required: true }, // Description field is required
  address: { type: String, required: true }, // Address field is required
  logo: { type: String, default: '' }, // Default logo is an empty string
});

// Create a mongoose model based on the schema
const CompanyModel = mongoose.model<ICompany>('Company', companySchema);

export default CompanyModel;

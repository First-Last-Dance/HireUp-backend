import mongoose from 'mongoose';

const { Schema } = mongoose;

// Interface representing the structure of data for an account
export interface AccountData {
  email?: string;
  password?: string;
  type?: string;
  verified?: boolean;
  admin?: boolean;
}

// Interface representing a mongoose document for an account
export interface IAccount extends mongoose.Document {
  email: string;
  password: string;
  type: string;
  verified: boolean;
  admin: boolean;
}

// Define the schema for the account collection
const accountSchema = new Schema({
  email: { type: String, required: true, unique: true }, // Email field is required and unique
  password: { type: String, required: true }, // Password field is required
  type: { type: String, default: '' }, // Default type is an empty string
  verified: { type: Boolean, default: false }, // Default verification status is false
  admin: { type: Boolean, default: false }, // Default admin status is false
});

// Create a mongoose model based on the schema
const AccountModel = mongoose.model<IAccount>('Account', accountSchema);

export default AccountModel;

import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import CompanyModel, { ICompany } from './model';

/**
 * Deletes a company by email.
 * @param email The email of the company to be deleted.
 */
export async function deleteCompanyByEmail(email: string): Promise<void> {
  await CompanyModel.findOneAndDelete({ email });
}

/**
 * Retrieves all companies.
 * @returns A list of all companies.
 */
export async function getAllCompanies(): Promise<ICompany[]> {
  return CompanyModel.find();
}

/**
 * Retrieves a company by email.
 * @param email The email of the company to be retrieved.
 * @returns The company with the specified email.
 * @throws CodedError if the company is not found.
 */
export async function getCompanyByEmail(email: string): Promise<ICompany> {
  const company = await CompanyModel.findOne({ email }).catch((err) => {
    throw err;
  });
  if (!company) {
    throw new CodedError(
      ErrorMessage.AccountNotFound,
      ErrorCode.AccountNotFound,
    );
  }
  return company;
}

/**
 * Checks if an email is available.
 * @param email The email to be checked.
 * @returns true if the email is available, false otherwise.
 */
export async function isEmailAvailable(email: string): Promise<boolean> {
  const existingAccount = await CompanyModel.findOne({ email });
  return !existingAccount;
}

/**
 * Adds a new company.
 * @param email The email of the new company.
 * @param name The name of the new company.
 * @param description The description of the new company.
 * @param address The address of the new company.
 * @returns The newly created company.
 * @throws CodedError if the email already exists.
 */
export async function addCompany(
  email: string,
  name: string,
  description: string,
  address: string,
): Promise<ICompany> {
  if (!(await isEmailAvailable(email))) {
    await deleteCompanyByEmail(email);
  }

  const newAccount = new CompanyModel({
    email,
    name,
    description,
    address,
  });
  return newAccount.save();
}

/**
 * Updates the logo of a company.
 * @param email The email of the company.
 * @param picture The base64 encoded string of the logo.
 * @throws CodedError if the company is not found.
 */
export async function updateLogo(
  email: string,
  picture: string,
): Promise<void> {
  if (await isEmailAvailable(email)) {
    throw new CodedError(
      ErrorMessage.AccountNotFound,
      ErrorCode.AccountNotFound,
    );
  }
  await CompanyModel.findOneAndUpdate({ email }, { logo: picture }).catch(
    (err) => {
      throw err;
    },
  );
}

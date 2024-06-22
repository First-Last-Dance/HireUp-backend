import * as Company from './service';
import { signUp, addTypeByEmail } from '../accounts/controller';
import { CompanyData } from './model';

/**
 * Registers a new company.
 *
 * @param email The email of the company.
 * @param password The password of the company.
 * @param type The type of the company.
 * @param name The name of the company.
 * @param description The description of the company.
 * @param address The address of the company.
 * @returns The JWT token for the registered company.
 */
export async function register(
  email: string,
  password: string,
  type: string,
  name: string,
  description: string,
  address: string,
): Promise<string> {
  let jwt = '';
  await signUp(email, password)
    .then(async (token) => {
      await Company.addCompany(email, name, description, address)
        .then(async () => {
          await addTypeByEmail(email, type)
            .then(() => {
              jwt = token;
            })
            .catch((err) => {
              throw err;
            });
        })
        .catch((err) => {
          throw err;
        });
    })
    .catch((err) => {
      throw err;
    });
  return jwt;
}

/**
 * Retrieves company data by email.
 *
 * @param email The email of the company.
 * @returns The data of the company.
 */
export async function getCompanyByEmail(email: string): Promise<CompanyData> {
  const data: CompanyData = {};
  await Company.getCompanyByEmail(email)
    .then(async (res) => {
      data.email = res.email;
      data.name = res.name;
      data.description = res.description;
      data.address = res.address;
      data.logo = res.logo;
    })
    .catch((err) => {
      throw err;
    });
  return data;
}

/**
 * Updates the logo of a company.
 *
 * @param email The email of the company.
 * @param picture The base64 encoded string of the logo.
 */
export async function updateLogo(email: string, picture: string) {
  await Company.updateLogo(email, picture).catch((err) => {
    throw err;
  });
}

/**
 * Retrieves the company ID by email.
 *
 * @param email The email of the company.
 * @returns The ID of the company.
 */
export async function getCompanyIDByEmail(email: string): Promise<string> {
  const res = await Company.getCompanyByEmail(email).catch((err) => {
    throw err;
  });
  return res._id;
}

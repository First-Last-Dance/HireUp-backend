import * as jwt from 'jsonwebtoken';
import * as dotenv from 'dotenv';
import * as EmailValidator from 'email-validator';
import bcrypt from 'bcryptjs';
import * as Account from './service';
import { CodedError, ErrorCode, ErrorMessage } from '../util/error';

/**
 * Generates a hash from a plain text password.
 * @param plainTextPassword The plain text password to be hashed.
 * @returns A promise that resolves to the hashed password.
 */
export async function generatePassword(
  plainTextPassword: string,
): Promise<string> {
  const saltRounds = 10;
  const salt = await bcrypt.genSalt(saltRounds);
  return bcrypt.hash(plainTextPassword, salt);
}

/**
 * Compares a plain text password with its hash.
 * @param plainTextPassword The plain text password.
 * @param hash The hash to compare against.
 * @returns A promise that resolves to true if the password matches the hash, false otherwise.
 */
async function comparePasswords(
  plainTextPassword: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(plainTextPassword, hash);
}

/**
 * Generates a JSON Web Token (JWT) with the given username.
 * @param userName The username to be encoded in the JWT.
 * @returns The generated JWT.
 */
function generateJWT(userName: string): string {
  dotenv.config();
  return jwt.sign(
    { userName },
    process.env.JWT_SECRET as unknown as jwt.Secret,
  );
}

/**
 * Checks if the given input string is in the format of a date (YYYY-MM-DD).
 * @param input The input string to be checked.
 * @returns True if the input string is a valid date, false otherwise.
 */
function isDateString(input: string): boolean {
  const dateFormatRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateFormatRegex.test(input)) {
    return false;
  }
  const parsedDate = new Date(input);
  return !Number.isNaN(parsedDate.getTime());
}

/**
 * Registers a new user with the given email and password.
 * @param email The email of the user to be registered.
 * @param password The password of the user to be registered.
 * @returns A promise that resolves to the JWT of the registered user.
 */
export async function signUp(email: string, password: string): Promise<string> {
  if (!email || !EmailValidator.validate(email)) {
    throw new CodedError(ErrorMessage.InvalidEmail, ErrorCode.InvalidParameter);
  }

  const generatedHash = await generatePassword(password);
  await Account.addAccount(email, generatedHash).catch((err) => {
    throw err;
  });

  return generateJWT(email);
}

/**
 * Authenticates a user with the given email and password.
 * @param email The email of the user to be authenticated.
 * @param password The password of the user to be authenticated.
 * @returns A promise that resolves to the JWT and type of the authenticated user.
 */
export async function signIn(email: string, password: string) {
  const pass = await Account.getPasswordByEmail(email).catch((err) => {
    throw err;
  });
  const account = await Account.getAccountByEmail(email).catch((err) => {
    throw err;
  });

  if (pass) {
    const authValid = await comparePasswords(password, pass);
    if (!authValid) {
      throw new CodedError(
        ErrorMessage.WrongPassword,
        ErrorCode.AuthenticationError,
      );
    }
    return { jwt: generateJWT(email), type: account?.type };
  }

  throw new CodedError(
    ErrorMessage.InternalServerError,
    ErrorCode.InternalServerError,
  );
}

/**
 * Adds a type to the user with the given email.
 * @param email The email of the user to add the type to.
 * @param type The type to be added to the user.
 * @returns A promise that resolves when the type is successfully added.
 */
export async function addTypeByEmail(
  email: string,
  type: string,
): Promise<void> {
  await Account.addTypeByEmail(email, type).catch((err) => {
    throw err;
  });
}

/**
 * Deletes the account of the user with the given email.
 * @param email The email of the user whose account is to be deleted.
 * @returns A promise that resolves when the account is successfully deleted.
 */
export async function deleteAccountByEmail(email: string): Promise<void> {
  await Account.deleteAccountByEmail(email).catch((err) => {
    throw err;
  });
}

/**
 * Retrieves all accounts.
 * @returns A promise that resolves to all accounts.
 */
export async function getAllAccounts(): Promise<any> {
  return Account.getAllAccounts().catch((err) => {
    throw err;
  });
}

/**
 * Retrieves the account of the user with the given email.
 * @param email The email of the user.
 * @returns A promise that resolves to the account of the user.
 */
export async function getAccountByEmail(email: string): Promise<any> {
  return Account.getAccountByEmail(email).catch((err) => {
    throw err;
  });
}

/**
 * Retrieves the password of the user with the given email.
 * @param email The email of the user.
 * @returns A promise that resolves to the password of the user.
 */
export async function getPasswordByEmail(
  email: string,
): Promise<string | null> {
  return Account.getPasswordByEmail(email).catch((err) => {
    throw err;
  });
}

/**
 * Checks if the given email is available.
 * @param email The email to be checked.
 * @returns A promise that resolves to true if the email is available, false otherwise.
 */
export async function isEmailAvailable(email: string): Promise<boolean> {
  return await Account.isEmailAvailable(email).catch((err) => {
    throw err;
  });
}

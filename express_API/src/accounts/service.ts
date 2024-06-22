import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import AccountModel, { IAccount } from './model';

/**
 * Deletes an account by email.
 * @param email The email of the account to be deleted.
 */
export async function deleteAccountByEmail(email: string): Promise<void> {
  await AccountModel.findOneAndDelete({ email }).catch((err) => {
    throw err;
  });
}

/**
 * Checks if an email is available for registration.
 * If the email is available and belongs to an account with an empty type, the account is deleted.
 * @param email The email to check availability.
 * @returns A boolean indicating whether the email is available.
 */
export async function isEmailAvailable(email: string): Promise<boolean> {
  const existingAccount = await AccountModel.findOne({ email });
  if (existingAccount?.type === '') {
    await deleteAccountByEmail(email);
    return true;
  }
  return !existingAccount;
}

/**
 * Adds a new account with the provided email and password.
 * Throws an error if the email is not available.
 * @param email The email for the new account.
 * @param password The password for the new account.
 * @returns The created account.
 */
export async function addAccount(
  email: string,
  password: string,
): Promise<IAccount> {
  if (!(await isEmailAvailable(email))) {
    throw new CodedError(ErrorMessage.EmailAlreadyExist, ErrorCode.Conflict);
  }
  const newAccount = new AccountModel({ email, password });
  return newAccount.save();
}

/**
 * Updates an account by email with the provided details.
 * @param email The email of the account to be updated.
 * @param password The new password.
 * @param type The new account type.
 * @param verified The new verification status.
 * @param admin The new admin status.
 * @returns The updated account.
 */
export async function updateAccountByEmail(
  email: string,
  password: string,
  type: string,
  verified: boolean,
  admin: boolean,
): Promise<IAccount | null> {
  return AccountModel.findOneAndUpdate(
    { email },
    {
      password,
      type,
      verified,
      admin,
    },
    { new: true },
  );
}

/**
 * Adds a type to an account by email.
 * @param email The email of the account to be updated.
 * @param type The new account type.
 * @returns The updated account.
 */
export async function addTypeByEmail(
  email: string,
  type: string,
): Promise<IAccount | null> {
  return AccountModel.findOneAndUpdate({ email }, { type }, { new: true });
}

/**
 * Retrieves all accounts.
 * @returns An array of all accounts.
 */
export async function getAllAccounts(): Promise<IAccount[]> {
  return AccountModel.find();
}

/**
 * Retrieves an account by email.
 * @param email The email of the account to retrieve.
 * @returns The account with the specified email.
 */
export async function getAccountByEmail(
  email: string,
): Promise<IAccount | null> {
  return AccountModel.findOne({ email });
}

/**
 * Retrieves the password of an account by email.
 * Throws an error if the account is not found.
 * @param email The email of the account.
 * @returns The password of the account.
 */
export async function getPasswordByEmail(email: string): Promise<string> {
  const account = await AccountModel.findOne({ email });
  if (!account) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  return account.password;
}

/**
 * Checks if an account with the specified email is verified.
 * @param email The email of the account.
 * @returns A boolean indicating whether the account is verified.
 */
export async function isAccountVerified(email: string): Promise<boolean> {
  const account = await AccountModel.findOne({ email });
  return !!account && account.verified;
}

/**
 * Checks if an account with the specified email is an admin.
 * @param email The email of the account.
 * @returns A boolean indicating whether the account is an admin.
 */
export async function isAccountAdmin(email: string): Promise<boolean> {
  const account = await AccountModel.findOne({ email });
  return !!account && account.admin;
}

export async function isAccountCompany(email: string): Promise<boolean> {
  const account = await AccountModel.findOne({ email });
  return !!account && account.type === 'Company';
}

export async function isAccountApplicant(email: string): Promise<boolean> {
  const account = await AccountModel.findOne({ email });
  return !!account && account.type === 'Applicant';
}

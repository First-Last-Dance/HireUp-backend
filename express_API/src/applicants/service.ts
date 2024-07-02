import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import ApplicantModel, { IApplicant } from './model';

/**
 * Deletes an applicant by email.
 * @param email The email of the applicant to be deleted.
 */
export async function deleteApplicantByEmail(email: string): Promise<void> {
  await ApplicantModel.findOneAndDelete({ email });
}

/**
 * Retrieves all applicants.
 * @returns A list of all applicants.
 */
export async function getAllApplicants(): Promise<IApplicant[]> {
  return ApplicantModel.find();
}

/**
 * Retrieves an applicant by email.
 * @param email The email of the applicant to be retrieved.
 * @returns The applicant with the specified email.
 * @throws CodedError if the applicant is not found.
 */
export async function getApplicantByEmail(email: string): Promise<IApplicant> {
  const applicant = await ApplicantModel.findOne({ email })
    .populate({
      path: 'skills',
      select: 'name -_id',
    })
    .catch((err) => {
      throw err;
    });
  if (!applicant) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  return applicant;
}

/**
 * Checks if an email is available.
 * @param email The email to be checked.
 * @returns true if the email is available, false otherwise.
 */
export async function isEmailAvailable(email: string): Promise<boolean> {
  const existingAccount = await ApplicantModel.findOne({ email });
  return !existingAccount;
}

/**
 * Checks if a phone number is available.
 * @param phoneNumber The phone number to be checked.
 * @returns true if the phone number is available, false otherwise.
 */
export async function isPhoneNumberAvailable(
  phoneNumber: string,
): Promise<boolean> {
  const existingAccount = await ApplicantModel.findOne({ phoneNumber });
  return !existingAccount;
}

/**
 * Checks if a national ID number is available.
 * @param nationalIDNumber The national ID number to be checked.
 * @returns true if the national ID number is available, false otherwise.
 */
export async function isNationalIDNumberAvailable(
  nationalIDNumber: string,
): Promise<boolean> {
  const existingAccount = await ApplicantModel.findOne({
    nationalIDNumber,
  });
  return !existingAccount;
}

/**
 * Adds a new applicant.
 * @param email The email of the new applicant.
 * @param firstName The first name of the new applicant.
 * @param middleName The middle name of the new applicant.
 * @param lastName The last name of the new applicant.
 * @param phoneNumber The phone number of the new applicant.
 * @param nationalIDNumber The national ID number of the new applicant.
 * @returns The newly created applicant.
 * @throws CodedError if the email, phone number, or national ID number already exist.
 */
export async function addApplicant(
  email: string,
  firstName: string,
  middleName: string,
  lastName: string,
  phoneNumber: string,
  nationalIDNumber: string,
): Promise<IApplicant> {
  if (!(await isEmailAvailable(email))) {
    await deleteApplicantByEmail(email);
  }
  if (!(await isPhoneNumberAvailable(phoneNumber))) {
    throw new CodedError(
      ErrorMessage.PhoneNumberAlreadyExist,
      ErrorCode.Conflict,
    );
  }
  if (!(await isNationalIDNumberAvailable(nationalIDNumber))) {
    throw new CodedError(
      ErrorMessage.NationalIDAlreadyExist,
      ErrorCode.Conflict,
    );
  }
  const newAccount = new ApplicantModel({
    email,
    firstName,
    middleName,
    lastName,
    phoneNumber,
    nationalIDNumber,
  });
  return newAccount.save();
}

/**
 * Updates the profile picture of an applicant.
 * @param email The email of the applicant.
 * @param picture The base64 encoded string of the profile picture.
 * @throws CodedError if the applicant is not found.
 */
export async function updateProfilePicture(
  email: string,
  picture: string,
): Promise<void> {
  if (await isEmailAvailable(email)) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  await ApplicantModel.findOneAndUpdate(
    { email },
    { profilePhoto: picture },
  ).catch((err) => {
    throw err;
  });
}

/**
 * Updates the national ID photo (front side) of an applicant.
 * @param email The email of the applicant.
 * @param picture The base64 encoded string of the national ID photo (front side).
 * @throws CodedError if the applicant is not found.
 */
export async function updateNationalIDPhotoFace(
  email: string,
  picture: string,
): Promise<void> {
  if (await isEmailAvailable(email)) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  await ApplicantModel.findOneAndUpdate(
    { email },
    { nationalIDPhotoFace: picture },
  ).catch((err) => {
    throw err;
  });
}

/**
 * Updates the national ID photo (back side) of an applicant.
 * @param email The email of the applicant.
 * @param picture The base64 encoded string of the national ID photo (back side).
 * @throws CodedError if the applicant is not found.
 */
export async function updateNationalIDPhotoBack(
  email: string,
  picture: string,
): Promise<void> {
  if (await isEmailAvailable(email)) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  await ApplicantModel.findOneAndUpdate(
    { email },
    { nationalIDPhotoBack: picture },
  ).catch((err) => {
    throw err;
  });
}

export async function updateApplicantSkills(
  email: string,
  skillsIDs: string[],
) {
  await ApplicantModel.findOneAndUpdate({ email }, { skills: skillsIDs }).catch(
    (err) => {
      throw err;
    },
  );
}

export async function getApplicantIDByEmail(email: string): Promise<string> {
  const applicant = await ApplicantModel.findOne({ email }).catch((err) => {
    throw err;
  });
  if (!applicant) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  return applicant._id;
}

export async function getApplicantByID(
  applicantID: string,
): Promise<IApplicant> {
  const applicant = await ApplicantModel.findById(applicantID)
    .populate({
      path: 'skills',
      select: 'name -_id',
    })
    .catch((err) => {
      throw err;
    });
  if (!applicant) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  return applicant;
}

import * as Applicant from './service';
import { signUp, addTypeByEmail } from '../accounts/controller';
import { ApplicantData } from './model';

/**
 * Registers a new applicant.
 * @param email The email of the applicant.
 * @param password The password of the applicant.
 * @param type The type of the applicant.
 * @param firstName The first name of the applicant.
 * @param middleName The middle name of the applicant.
 * @param lastName The last name of the applicant.
 * @param phoneNumber The phone number of the applicant.
 * @param nationalIDNumber The national ID number of the applicant.
 * @returns The JWT token for the registered applicant.
 */
export async function register(
  email: string,
  password: string,
  type: string,
  firstName: string,
  middleName: string,
  lastName: string,
  phoneNumber: string,
  nationalIDNumber: string,
): Promise<string> {
  let jwt = '';
  await signUp(email, password)
    .then(async (token) => {
      await Applicant.addApplicant(
        email,
        firstName,
        middleName,
        lastName,
        phoneNumber,
        nationalIDNumber,
      )
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
 * Retrieves applicant data by email.
 * @param email The email of the applicant.
 * @returns The data of the applicant.
 */
export async function getApplicantByEmail(
  email: string,
): Promise<ApplicantData> {
  const data: ApplicantData = {};
  await Applicant.getApplicantByEmail(email)
    .then(async (res) => {
      data.email = res.email;
      data.firstName = res.firstName;
      data.middleName = res.middleName;
      data.lastName = res.lastName;
      data.phoneNumber = res.phoneNumber;
      data.nationalIDNumber = res.nationalIDNumber;
      data.profilePhoto = res.profilePhoto;
      data.nationalIDPhotoFace = res.nationalIDPhotoFace;
      data.nationalIDPhotoBack = res.nationalIDPhotoBack;
    })
    .catch((err) => {
      throw err;
    });
  return data;
}

export async function updateProfilePicture(email: string, picture: string) {
  await Applicant.updateProfilePicture(email, picture).catch((err) => {
    throw err;
  });
}
export async function updateNationalIDPhotoFace(
  email: string,
  picture: string,
) {
  await Applicant.updateNationalIDPhotoFace(email, picture).catch((err) => {
    throw err;
  });
}
export async function updateNationalIDPhotoBack(
  email: string,
  picture: string,
) {
  await Applicant.updateNationalIDPhotoBack(email, picture).catch((err) => {
    throw err;
  });
}

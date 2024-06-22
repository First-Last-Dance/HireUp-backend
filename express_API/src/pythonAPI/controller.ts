import * as Applicant from '../applicants/service';
import * as Application from '../applications/service';
import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import axios from 'axios';
import * as dotenv from 'dotenv';

dotenv.config();

export async function startInterviewStream(
  applicantEmail: string,
  applicationID: string,
) {
  // Get applicant ID
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);
  if (!applicantID) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }

  // Get application
  const application = await Application.getApplicationByID(applicationID);

  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  // Check if the applicant is the owner of the application
  if (application.applicantID.toString() !== applicantID.toString()) {
    throw new CodedError(
      ErrorMessage.ApplicantIsNotTheOwnerOfTheApplication,
      ErrorCode.Forbidden,
    );
  }

  // Check if the application is in the right state
  if (application.status !== 'Online Interview') {
    throw new CodedError(ErrorMessage.IncorrectStep, ErrorCode.Conflict);
  }

  // invoke the python API

  const response = await axios.post(
    process.env.Python_Host + '/interview_stream',
    {
      ApplicationID: applicantID, // Assuming you expect 'title' in the request body
    },
  );
  return response.data;
}

import e from 'express';
import * as Applicant from '../applicants/service';
import * as Application from '../applications/service';
import * as Job from '../jobs/service';
``;
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

  // Get the job ID
  const jobID = application.jobID;

  // Check if the job exists
  const job = await Job.getJobByID(jobID.toString());
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }

  // Get the questions of the job

  const questions = job.questions;

  if (!questions || questions.length === 0) {
    throw new CodedError(ErrorMessage.NoQuestions, ErrorCode.NotFound);
  }

  console.log('questions', questions);

  // invoke the python API

  const response = await axios.post(
    process.env.Python_Host + '/interview_stream',
    {
      ApplicationID: applicationID,
      Questions: questions,
    },
  );
  if (!response.data) {
    throw new CodedError(ErrorMessage.InternalServerError, ErrorCode.NotFound);
  }

  await Application.updateApplicationStatus(
    applicationID,
    'Final Result',
  ).catch((err) => {
    throw err;
  });
  return response.data;
}

export async function startQuizStream(
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
  if (application.status !== 'Online Quiz') {
    throw new CodedError(ErrorMessage.IncorrectStep, ErrorCode.Conflict);
  }

  // Invoke the python API
  const response = await axios.post(process.env.Python_Host + '/quiz_stream', {
    ApplicationID: applicationID,
  });
  return response.data;
}

export async function quizCalibration(
  applicantEmail: string,
  applicationID: string,
  pictureUpRight: string,
  pictureUpLeft: string,
  pictureDownRight: string,
  pictureDownLeft: string,
) {
  // Get the details of the application
  const application = await Application.getApplicationByID(applicationID);

  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  // Get the applicant ID
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);

  // Check if the applicant is the owner of the application
  if (application.applicantID.toString() !== applicantID.toString()) {
    throw new CodedError(
      ErrorMessage.ApplicantIsNotTheOwnerOfTheApplication,
      ErrorCode.Forbidden,
    );
  }

  // Check if the application is in the right state

  if (application.status !== 'Online Quiz') {
    throw new CodedError(ErrorMessage.IncorrectStep, ErrorCode.Conflict);
  }

  // invoke the python API
  const response = await axios
    .post(process.env.Python_Host + '/quiz_calibration', {
      ApplicationID: applicationID,
      PictureUpRight: pictureUpRight,
      PictureUpLeft: pictureUpLeft,
      PictureDownRight: pictureDownRight,
      PictureDownLeft: pictureDownLeft,
    })
    .catch((err) => {
      throw err;
    });
  return response.data;
}

export async function interviewCalibration(
  applicantEmail: string,
  applicationID: string,
  pictureUpRight: string,
  pictureUpLeft: string,
  pictureDownRight: string,
  pictureDownLeft: string,
) {
  // Get the details of the application
  const application = await Application.getApplicationByID(applicationID);

  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  // Get the applicant ID
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);

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
  const response = await axios
    .post(process.env.Python_Host + '/interview_calibration', {
      ApplicationID: applicationID,
      PictureUpRight: pictureUpRight,
      PictureUpLeft: pictureUpLeft,
      PictureDownRight: pictureDownRight,
      PictureDownLeft: pictureDownLeft,
    })
    .catch((err) => {
      throw err;
    });
  return response.data;
}

export async function startQGSocket() {
  // invoke the python API
  const response = await axios.post(process.env.Python_Host + '/QG_socket');
  if (!response.data) {
    throw new CodedError(ErrorMessage.InternalServerError, ErrorCode.NotFound);
  }
  return response.data;
}

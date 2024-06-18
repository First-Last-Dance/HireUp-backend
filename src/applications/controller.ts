import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import { ApplicationData } from './model';
import * as Application from './service';
import * as Applicant from '../applicants/service';
import { getCompanyIDByEmail } from '../companies/controller';
import * as Job from '../jobs/service';
import { ICompany } from '../companies/model';

export async function updateApplicationStatus(
  applicationId: string,
  newStatus: string,
): Promise<ApplicationData> {
  const application = await Application.updateApplicationStatus(
    applicationId,
    newStatus,
  ).catch((err) => {
    throw err;
  });
  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }
  const updatedApplication: ApplicationData = {
    applicationID: application._id,
    status: application.status,
    applicantID: application.applicantID as unknown as string,
    jobID: application.jobID as unknown as string,
  };
  return updatedApplication;
}

export async function addApplication(
  jobID: string,
  applicantEmail: string,
): Promise<ApplicationData> {
  // Get the applicant ID from the applicant email
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);
  // Check if the applicant has already applied to the job
  const applicationExists = await Application.checkApplicationExists(
    applicantID,
    jobID,
  ).catch((err) => {
    throw err;
  });
  if (applicationExists) {
    throw new CodedError(
      ErrorMessage.ApplicationAlreadyExists,
      ErrorCode.Conflict,
    );
  }
  // Check if quiz is required
  const job = await Job.getJobByID(jobID);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  let steps = [
    'Application Form',
    'Online Quiz',
    'Online Interview',
    'Final Result',
  ];
  if (job.quizRequired) {
    steps = [
      'Application Form',
      'Online Quiz',
      'Online Interview',
      'Final Result',
    ];
  } else {
    steps = ['Application Form', 'Online Interview', 'Final Result'];
  }
  const data: ApplicationData = {
    status: 'Application Form',
    applicantID: applicantID,
    jobID,
    steps,
  };
  const application = await Application.addApplication(data).catch((err) => {
    throw err;
  });
  const newApplication: ApplicationData = {
    applicationID: application._id,
    status: application.status,
    applicantID: application.applicantID as unknown as string,
    jobID: application.jobID as unknown as string,
    steps: application.steps,
  };
  return newApplication;
}

export async function getApplicationById(
  applicationId: string,
): Promise<ApplicationData> {
  const application = await Application.getApplicationById(applicationId).catch(
    (err) => {
      throw err;
    },
  );
  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  const job = await Job.getJobByID(application.jobID as unknown as string);

  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }

  const companyName = (job.companyID as unknown as ICompany).name;
  const title = job.title;

  const retrievedApplication: ApplicationData = {
    applicationID: application._id,
    status: application.status,
    applicantID: application.applicantID as unknown as string,
    jobID: application.jobID as unknown as string,
    companyName: companyName,
    title: title,
    steps: application.steps,
  };
  return retrievedApplication;
}

export async function getApplicationsByApplicantEmail(
  applicantEmail: string,
  limit: number,
  page: number,
): Promise<ApplicationData[]> {
  const applicantId = await Applicant.getApplicantIDByEmail(applicantEmail);
  if (!applicantId) {
    throw new CodedError(ErrorMessage.AccountNotFound, ErrorCode.NotFound);
  }
  const applications = await Application.getApplicationsByApplicantId(
    applicantId,
    limit,
    page,
  ).catch((err) => {
    throw err;
  });
  const applicationsArr: ApplicationData[] = [];
  for (const application of applications) {
    const job = await Job.getJobByID(application.jobID as unknown as string);
    if (!job) {
      throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
    }
    const companyName = (job.companyID as unknown as ICompany).name;
    const title = job.title;
    applicationsArr.push({
      applicationID: application._id,
      status: application.status,
      applicantID: application.applicantID as unknown as string,
      jobID: application.jobID as unknown as string,
      companyName: companyName,
      title: title,
      steps: application.steps,
    });
  }
  return applicationsArr;
}

export async function getApplicationsByJobId(
  jobId: string,
  companyEmail: string,
  limit: number,
  page: number,
): Promise<ApplicationData[]> {
  // Check if the job belongs to the company
  const companyID = await getCompanyIDByEmail(companyEmail);
  const job = await Job.getJobByID(jobId);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  if ((job.companyID as unknown as ICompany)._id !== companyID) {
    throw new CodedError(
      ErrorMessage.JobIsNotOwnedByThisCompany,
      ErrorCode.Forbidden,
    );
  }
  const companyName = (job.companyID as unknown as ICompany).name;
  const title = job.title;
  const applications = await Application.getApplicationsByJobId(
    jobId,
    limit,
    page,
  ).catch((err) => {
    throw err;
  });
  const applicationsArr: ApplicationData[] = [];
  applications.forEach((application) => {
    applicationsArr.push({
      applicationID: application._id,
      status: application.status,
      applicantID: application.applicantID as unknown as string,
      jobID: application.jobID as unknown as string,
      companyName: companyName,
      title: title,
      steps: application.steps,
    });
  });
  return applicationsArr;
}

export async function getApplicationsCountByJobID(
  jobID: string,
): Promise<number> {
  return Application.getApplicationsCountByJobID(jobID);
}

export async function getApplicationsCountByApplicantEmail(
  applicantEmail: string,
): Promise<number> {
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);
  return Application.getApplicationsCountByApplicantID(applicantID);
}

export async function checkApplicationExists(
  applicantEmail: string,
  jobID: string,
): Promise<boolean> {
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);
  return Application.checkApplicationExists(applicantID, jobID);
}

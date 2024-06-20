import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import { ApplicationData } from './model';
import * as Application from './service';
import * as Applicant from '../applicants/service';
import { getCompanyIDByEmail } from '../companies/controller';
import * as Job from '../jobs/service';
import { ICompany } from '../companies/model';
import * as Quiz from '../quizzes/service';
import { QuizData } from '../quizzes/model';

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
  let steps;
  let status;
  if (job.quizRequired) {
    steps = [
      'Application Form',
      'Online Quiz',
      'Online Interview',
      'Final Result',
    ];
    status = 'Online Quiz';
  } else {
    steps = ['Application Form', 'Online Interview', 'Final Result'];
    status = 'Online Interview';
  }
  const data: ApplicationData = {
    status: status,
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
  const application = await Application.getApplicationByID(applicationId).catch(
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

export async function getApplicationsByJobID(
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
  const applications = await Application.getApplicationsByJobID(
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

export async function startQuiz(
  applicantEmail: string,
  applicationID: string,
): Promise<QuizData> {
  // Get the details of the application
  const application = await Application.getApplicationByID(applicationID);

  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  // Check if the quiz is already started

  if (application.quizDeadline) {
    throw new CodedError(ErrorMessage.QuizAlreadyStarted, ErrorCode.Conflict);
  }

  // Check if it's the correct status to start the quiz

  if (application.status !== 'Online Quiz') {
    throw new CodedError(ErrorMessage.IncorrectStep, ErrorCode.Conflict);
  }

  // Check if the applicant has already started the quiz
  if (application?.quizDeadline) {
    throw new CodedError(
      ErrorMessage.ApplicantAlreadyTookTheQuiz,
      ErrorCode.Conflict,
    );
  }

  // Get the quiz details
  const job = await Job.getJobByID(application.jobID as unknown as string);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }

  // Check if the quiz is required
  if (!job.quizRequired) {
    throw new CodedError(ErrorMessage.QuizNotRequired, ErrorCode.Conflict);
  }

  // Check if the quiz is expired
  if (job.applicationDeadline < new Date()) {
    throw new CodedError(ErrorMessage.QuizExpired, ErrorCode.Conflict);
  }

  const quiz = await Quiz.getQuizByJobID(
    application.jobID as unknown as string,
  );

  // Check if the quiz exists
  if (!quiz) {
    throw new CodedError(ErrorMessage.QuizNotFound, ErrorCode.NotFound);
  }

  const quizDuration = 1000 * 60 * quiz.quizDurationInMinutes;

  const quizDeadline = new Date(new Date().getTime() + quizDuration);

  const delayDuration = 1000 * 60 * 2; // 2 minutes

  // Update the quiz deadline
  await Application.updateQuizDeadline(
    applicationID,
    new Date(quizDeadline.getTime() + delayDuration),
  ).catch((err) => {
    throw err;
  });

  // Get the Applicant ID
  const applicantID = await Applicant.getApplicantIDByEmail(applicantEmail);

  // Check if the applicant is the owner of the application
  if (application.applicantID.toString() !== applicantID.toString()) {
    throw new CodedError(
      ErrorMessage.ApplicantIsNotTheOwnerOfTheApplication,
      ErrorCode.Forbidden,
    );
  }

  if (!quiz.questions) {
    throw new CodedError(ErrorMessage.NoQuestions, ErrorCode.NotFound);
  }

  // Remove the correct answers and the score from the quiz
  quiz.questions.forEach((question) => {
    delete question.correctAnswer;
    delete question.score;
  });

  return {
    questions: quiz.questions,
    applicationID: applicationID,
    quizDeadline: quizDeadline,
    quizDurationInMinutes: quiz.quizDurationInMinutes,
  };
}

export async function submitQuiz(
  applicantEmail: string,
  applicationID: string,
  answers: string[],
): Promise<boolean> {
  // Get the details of the application
  const application = await Application.getApplicationByID(applicationID);

  if (!application) {
    throw new CodedError(ErrorMessage.ApplicationNotFound, ErrorCode.NotFound);
  }

  // Get the quiz details
  const job = await Job.getJobByID(application.jobID as unknown as string);

  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }

  // Check if the quiz is required

  if (!job.quizRequired) {
    throw new CodedError(ErrorMessage.QuizNotRequired, ErrorCode.Conflict);
  }

  // Get the quiz details

  const quiz = await Quiz.getQuizByJobID(
    application.jobID as unknown as string,
  );

  // Check if the quiz exists

  if (!quiz) {
    throw new CodedError(ErrorMessage.QuizNotFound, ErrorCode.NotFound);
  }

  // Check if the quiz is expired

  if (application.quizDeadline === undefined) {
    throw new CodedError(ErrorMessage.QuizNotStarted, ErrorCode.Conflict);
  }

  if (new Date() > application.quizDeadline) {
    throw new CodedError(ErrorMessage.QuizExpired, ErrorCode.Conflict);
  }

  // Compare the answers with the correct answers

  let score = 0;

  for (let i = 0; i < quiz.questions.length; i++) {
    if (quiz.questions[i].correctAnswer === answers[i]) {
      score += quiz.questions[i].score || 1;
    }
  }

  // Get the Applicant ID

  const applicantID = await Applicant.getApplicantIDByEmail(
    applicantEmail,
  ).catch((err) => {
    throw err;
  });

  // Check if the applicant is the owner of the application
  if (application.applicantID.toString() !== applicantID.toString()) {
    throw new CodedError(
      ErrorMessage.ApplicantIsNotTheOwnerOfTheApplication,
      ErrorCode.Forbidden,
    );
  }

  // Calculate the pass ratio

  const passRatio = quiz.passRatio || 0.5;

  // Check if the applicant passed the quiz

  const totalScore = quiz.questions.reduce(
    (acc, question) => acc + (question.score || 1),
    0,
  );

  const result = score / totalScore;

  const status = result >= passRatio ? 'Online Interview' : 'Failed';

  // Update the application status

  await Application.updateApplicationStatus(applicationID, status).catch(
    (err) => {
      throw err;
    },
  );

  return result >= passRatio;
}

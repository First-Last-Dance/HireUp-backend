import { QuestionData, QuizData } from './model';
import * as Quiz from './service';
import * as Job from '../jobs/service';
import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import { getCompanyIDByEmail } from '../companies/controller';
import mongoose from 'mongoose';

// Function to add a quiz
export async function addQuiz(
  jobID: string,
  questions: QuestionData[],
  passRatio: number,
  quizDurationInMinutes: number,
  companyEmail: string,
): Promise<string> {
  // Get the job by its ID
  const job = await Job.getJobByID(jobID);

  // Check if the job exists
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }

  // Check if the job belongs to the company
  const companyID = await getCompanyIDByEmail(companyEmail);

  // Convert companyID to ObjectId if necessary
  const jobCompanyID =
    job.companyID instanceof mongoose.Types.ObjectId
      ? job.companyID
      : new mongoose.Types.ObjectId(job.companyID as unknown as string);

  if (!jobCompanyID.equals(new mongoose.Types.ObjectId(companyID))) {
    throw new CodedError(
      ErrorMessage.JobIsNotOwnedByThisCompany,
      ErrorCode.Forbidden,
    );
  }

  // Check if the job requires a quiz
  if (!job.quizRequired) {
    throw new CodedError(
      ErrorMessage.JobDoesNotRequireAQuiz,
      ErrorCode.Conflict,
    );
  }

  // Check if there are any questions
  if (questions.length === 0) {
    throw new CodedError(ErrorMessage.NoQuestions, ErrorCode.MissingParameter);
  }

  // Check if there is a quiz with the same job ID
  const existingQuiz = await Quiz.getQuizByJobID(jobID);
  if (existingQuiz) {
    throw new CodedError(ErrorMessage.QuizAlreadyExists, ErrorCode.Conflict);
  }

  // Create a new quiz
  const quizData: QuizData = {
    jobID,
    questions,
    passRatio,
    quizDurationInMinutes,
  };
  const quiz = await Quiz.addQuiz(quizData).catch((err) => {
    throw err;
  });

  return quiz._id;
}

// Function to get a quiz by its ID
export async function getQuizById(
  quizId: string,
  companyEmail: string,
): Promise<QuizData | null> {
  // Get the quiz by its ID
  const quiz = await Quiz.getQuizById(quizId);
  // Check if the quiz exists
  if (!quiz) {
    return null;
  }
  // Check if the company owns the quiz
  const job = await Job.getJobByID(quiz.jobID as unknown as string);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  // Check if the job belongs to the company
  const companyID = await getCompanyIDByEmail(companyEmail);

  // Convert companyID to ObjectId if necessary
  const jobCompanyID =
    job.companyID instanceof mongoose.Types.ObjectId
      ? job.companyID
      : new mongoose.Types.ObjectId(job.companyID as unknown as string);

  if (!jobCompanyID.equals(new mongoose.Types.ObjectId(companyID))) {
    throw new CodedError(
      ErrorMessage.JobIsNotOwnedByThisCompany,
      ErrorCode.Forbidden,
    );
  }

  return {
    jobID: quiz.jobID as unknown as string,
    questions: quiz.questions,
    passRatio: quiz.passRatio,
    quizDurationInMinutes: quiz.quizDurationInMinutes,
  };
}

// Function to get a quiz by its job ID
export async function getQuizByJobID(
  jobId: string,
  companyEmail: string,
): Promise<QuizData | null> {
  // Get the quiz by its job ID
  const quiz = await Quiz.getQuizByJobID(jobId);
  if (!quiz) {
    return null;
  }
  // Check if the quiz exists
  if (!quiz) {
    return null;
  }
  // Check if the company owns the quiz
  const job = await Job.getJobByID(quiz.jobID as unknown as string);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  // Check if the job belongs to the company
  const companyID = await getCompanyIDByEmail(companyEmail);

  // Convert companyID to ObjectId if necessary
  const jobCompanyID =
    job.companyID instanceof mongoose.Types.ObjectId
      ? job.companyID
      : new mongoose.Types.ObjectId(job.companyID as unknown as string);

  if (!jobCompanyID.equals(new mongoose.Types.ObjectId(companyID))) {
    throw new CodedError(
      ErrorMessage.JobIsNotOwnedByThisCompany,
      ErrorCode.Forbidden,
    );
  }

  return {
    jobID: quiz.jobID as unknown as string,
    questions: quiz.questions,
    passRatio: quiz.passRatio,
    quizDurationInMinutes: quiz.quizDurationInMinutes,
  };
}

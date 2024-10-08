// application.service.ts

import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import ApplicationModel, {
  IApplication,
  ApplicationData,
  InterviewQuestionData,
} from './model';

/**
 * Update status of an application by application ID
 * @param applicationId - The ID of the application to update
 * @param newStatus - The new status to update
 * @returns Updated application document
 */
export async function updateApplicationStatus(
  applicationId: string,
  newStatus: string,
): Promise<IApplication | null> {
  try {
    const updatedApplication = await ApplicationModel.findByIdAndUpdate(
      applicationId,
      { status: newStatus },
      { new: true },
    );
    return updatedApplication;
  } catch (error) {
    console.error('Error updating application status:', error);
    throw error;
  }
}

/**
 * Add a new application
 * @param data - Application data to be inserted
 * @returns Newly created application document
 */
export async function addApplication(
  data: ApplicationData,
): Promise<IApplication> {
  try {
    const newApplication = await ApplicationModel.create(data);
    return newApplication;
  } catch (error) {
    console.error('Error adding new application:', error);
    throw error;
  }
}

/**
 * Get an application by ID
 * @param applicationId - The ID of the application to retrieve
 * @returns Application document
 */
export async function getApplicationByID(
  applicationId: string,
): Promise<IApplication | null> {
  try {
    const application = await ApplicationModel.findById(applicationId);
    return application;
  } catch (error) {
    console.error('Error fetching application:', error);
    throw error;
  }
}

/**
 * Get all applications of a job by job ID
 * @param jobId - The ID of the job
 * @returns Array of application documents
 */
export async function getApplicationsByJobID(
  jobId: string,
  limit: number,
  page: number,
): Promise<IApplication[]> {
  try {
    const applications = await ApplicationModel.find({ jobID: jobId })
      .sort({
        createdAt: -1,
      })
      .limit(limit)
      .skip(limit * (page - 1));
    return applications;
  } catch (error) {
    console.error('Error fetching applications by job ID:', error);
    throw error;
  }
}

/**
 * Get all applications of an applicant by applicant ID
 * @param applicantId - The ID of the applicant
 * @returns Array of application documents
 */
export async function getApplicationsByApplicantId(
  applicantId: string,
  limit: number,
  page: number,
): Promise<IApplication[]> {
  try {
    const applications = await ApplicationModel.find({
      applicantID: applicantId,
    })
      .sort({
        createdAt: -1,
      })
      .limit(limit)
      .skip(limit * (page - 1));
    return applications;
  } catch (error) {
    console.error('Error fetching applications by applicant ID:', error);
    throw error;
  }
}

/**
 * Check if an application exists
 * @param applicationId - The ID of the application
 * @returns Boolean indicating if the application exists
 */

export async function checkApplicationExists(
  applicantID: string,
  jobID: string,
): Promise<boolean> {
  const application = await ApplicationModel.findOne({
    applicantID,
    jobID,
  }).catch((error) => {
    throw error;
  });
  return application !== null;
}

export async function getApplicationsCountByJobID(
  jobID: string,
): Promise<number> {
  return ApplicationModel.countDocuments({ jobID }).catch((error) => {
    throw error;
  });
}

export async function getApplicationsCountByApplicantID(
  applicantID: string,
): Promise<number> {
  return ApplicationModel.countDocuments({ applicantID }).catch((error) => {
    throw error;
  });
}

export async function updateQuizDeadline(
  applicationID: string,
  quizDeadline: Date,
): Promise<void> {
  await ApplicationModel.findByIdAndUpdate(applicationID, {
    quizDeadline,
  }).catch((error) => {
    throw error;
  });
}

export async function getApplicationsByJobIDAndStatus(
  jobID: string,
  status: string,
  limit: number,
  page: number,
): Promise<IApplication[]> {
  return ApplicationModel.find({ jobID, status })
    .sort({
      averageSimilarity: -1,
    })
    .limit(limit)
    .skip(limit * (page - 1))
    .catch((error) => {
      throw error;
    });
}

export async function getApplicationsCountByJobIDAndStatus(
  applicantID: string,
  status: string,
): Promise<number> {
  return ApplicationModel.countDocuments({ applicantID, status }).catch(
    (error) => {
      throw error;
    },
  );
}

export async function addQuizCheatingData(
  applicationID: string,
  quizEyeCheating: number,
  quizFaceSpeechCheating: number,
  quizEyeCheatingDurations: Array<any>,
  quizSpeakingCheatingDurations: Array<any>,
): Promise<void> {
  await ApplicationModel.findByIdAndUpdate(applicationID, {
    quizEyeCheating,
    quizFaceSpeechCheating,
    quizEyeCheatingDurations,
    quizSpeakingCheatingDurations,
  }).catch((error) => {
    throw error;
  });
}

export async function addInterviewQuestionData(
  applicationID: string,
  interviewQuestionData: InterviewQuestionData,
): Promise<void> {
  const application = await ApplicationModel.findById(applicationID).catch(
    (error) => {
      throw error;
    },
  );
  if (!application) {
    throw new Error('Application not found');
  }
  if (!application.totalSimilarity) {
    application.totalSimilarity = 0;
  }
  if (!application.questionsCount) {
    application.questionsCount = 0;
  }
  if (!application.interviewQuestionsData) {
    throw new CodedError(
      ErrorMessage.interviewQuestionDataIsNotAvailable,
      ErrorCode.NotFound,
    );
  }
  if (!interviewQuestionData.questionSimilarity) {
    interviewQuestionData.questionSimilarity = 0;
  }
  // Calculate the new total and count
  const newTotal =
    application.totalSimilarity + interviewQuestionData.questionSimilarity;
  const newCount = application.questionsCount + 1;
  const newAverage = newTotal / newCount;
  await ApplicationModel.findByIdAndUpdate(applicationID, {
    $push: { interviewQuestionsData: interviewQuestionData },
    totalSimilarity: newTotal,
    questionsCount: newCount,
    averageSimilarity: newAverage,
  }).catch((error) => {
    throw error;
  });
}

export async function updateQuizScore(
  applicationID: string,
  quizScore: number,
): Promise<void> {
  await ApplicationModel.findByIdAndUpdate(applicationID, {
    quizScore,
  }).catch((error) => {
    throw error;
  });
}

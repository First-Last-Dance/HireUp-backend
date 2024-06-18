// application.service.ts

import mongoose from 'mongoose';
import ApplicationModel, { IApplication, ApplicationData } from './model';

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
export async function getApplicationById(
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
export async function getApplicationsByJobId(
  jobId: string,
  limit: number,
  page: number,
): Promise<IApplication[]> {
  try {
    const applications = await ApplicationModel.find({ jobID: jobId })
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

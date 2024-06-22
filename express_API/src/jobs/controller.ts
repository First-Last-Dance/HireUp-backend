import { getCompanyIDByEmail } from '../companies/controller';
import { ICompany } from '../companies/model';
import { getSkillsIDs } from '../skills/controller';
import { ISkill } from '../skills/model';
import { CodedError, ErrorCode, ErrorMessage } from '../util/error';
import { JobData } from './model';
import * as Job from './service';

export async function addJob(
  title: string,
  description: string,
  requiredSkills: string[],
  salary: string,
  companyEmail: string,
  applicationDeadline: Date,
  quizDeadline: Date,
  interviewDeadline: Date,
  quizRequired: boolean,
): Promise<string> {
  const skillsIDs = await getSkillsIDs(requiredSkills);
  const companyID = await getCompanyIDByEmail(companyEmail);
  const jobData: JobData = {
    title,
    description,
    requiredSkills: skillsIDs,
    salary,
    companyID,
    applicationDeadline,
    quizDeadline,
    interviewDeadline,
    quizRequired,
  };
  const job = await Job.addJob(jobData).catch((err) => {
    throw err;
  });
  return job._id;
}

export async function getAllAvailableJobs(
  limit: number,
  page: number,
): Promise<JobData[]> {
  const jobs = await Job.getAllAvailableJobs(limit, page);
  const jobsArr: JobData[] = [];
  const skillsArr: string[] = [];
  jobs.forEach((job) => {
    job.requiredSkills.forEach((skill) => {
      skillsArr.push((skill as unknown as ISkill).name);
    });
    jobsArr.push({
      title: job.title,
      id: job._id,
      description: job.description,
      requiredSkills: skillsArr,
      salary: job.salary,
      companyID: (job.companyID as unknown as ICompany)._id,
      companyName: (job.companyID as unknown as ICompany).name,
      applicationDeadline: job.applicationDeadline,
      quizDeadline: job.quizDeadline,
      interviewDeadline: job.interviewDeadline,
      quizRequired: job.quizRequired,
    });
  });
  return jobsArr;
}

export async function deleteJobByID(
  jobID: string,
  companyEmail: string,
): Promise<void> {
  const job = await Job.getJobByID(jobID);
  if (!job) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  const companyID = await getCompanyIDByEmail(companyEmail);
  if ((job.companyID as unknown as ICompany)._id !== companyID) {
    throw new CodedError(ErrorMessage.JobNotFound, ErrorCode.NotFound);
  }
  await Job.deleteJobByID(jobID);
}

export async function getJobByID(jobID: string): Promise<JobData | null> {
  const job = await Job.getJobByID(jobID);
  if (!job) {
    return null;
  }
  const skillsArr: string[] = [];
  job.requiredSkills.forEach((skill) => {
    skillsArr.push((skill as unknown as ISkill).name);
  });
  return {
    title: job.title,
    description: job.description,
    requiredSkills: skillsArr,
    salary: job.salary,
    companyID: (job.companyID as unknown as ICompany)._id,
    companyName: (job.companyID as unknown as ICompany).name,
    applicationDeadline: job.applicationDeadline,
    quizDeadline: job.quizDeadline,
    interviewDeadline: job.interviewDeadline,
    quizRequired: job.quizRequired,
  };
}

export async function getAvailableJobsBySkills(
  skills: string[],
  limit: number,
  page: number,
): Promise<JobData[]> {
  const skillsIDs = await getSkillsIDs(skills);
  const jobs = await Job.getAvailableJobsBySkills(skillsIDs, limit, page);
  const jobsArr: JobData[] = [];
  const skillsArr: string[] = [];
  jobs.forEach((job) => {
    job.requiredSkills.forEach((skill) => {
      skillsArr.push((skill as unknown as ISkill).name);
    });
    jobsArr.push({
      title: job.title,
      description: job.description,
      requiredSkills: skillsArr,
      salary: job.salary,
      companyID: (job.companyID as unknown as ICompany)._id,
      companyName: (job.companyID as unknown as ICompany).name,
      applicationDeadline: job.applicationDeadline,
      quizDeadline: job.quizDeadline,
      interviewDeadline: job.interviewDeadline,
      quizRequired: job.quizRequired,
    });
  });
  return jobsArr;
}

export async function getNumberOfAvailableJobs(): Promise<number> {
  return Job.getNumberOfAvailableJobs();
}

export async function getNumberOfAvailableJobsBySkills(
  skills: string[],
): Promise<number> {
  const skillsIDs = await getSkillsIDs(skills);
  return Job.getNumberOfAvailableJobsBySkills(skillsIDs);
}

export async function getJobsByCompany(
  companyEmail: string,
  limit: number,
  page: number,
): Promise<JobData[]> {
  const companyID = await getCompanyIDByEmail(companyEmail);
  const jobs = await Job.getCompanyJobs(companyID, limit, page);
  const jobsArr: JobData[] = [];
  const skillsArr: string[] = [];
  jobs.forEach((job) => {
    job.requiredSkills.forEach((skill) => {
      skillsArr.push((skill as unknown as ISkill).name);
    });
    jobsArr.push({
      title: job.title,
      id: job._id,
      description: job.description,
      requiredSkills: skillsArr,
      salary: job.salary,
      companyID: (job.companyID as unknown as ICompany)._id,
      companyName: (job.companyID as unknown as ICompany).name,
      applicationDeadline: job.applicationDeadline,
      quizDeadline: job.quizDeadline,
      interviewDeadline: job.interviewDeadline,
      quizRequired: job.quizRequired,
    });
  });
  return jobsArr;
}

export async function getCompanyJobsCount(
  companyEmail: string,
): Promise<number> {
  const companyID = await getCompanyIDByEmail(companyEmail);
  return Job.getCompanyJobsCount(companyID);
}

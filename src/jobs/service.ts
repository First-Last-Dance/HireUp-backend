import JobModel, { IJob, JobData } from './model';

export async function getAllJobs(): Promise<IJob[]> {
  return JobModel.find().catch((error) => {
    throw error;
  });
}

export async function addJob(jobData: JobData): Promise<IJob> {
  console.log(jobData);
  const newJob = new JobModel(jobData);
  return newJob.save().catch((error) => {
    throw error;
  });
}

export async function deleteJobByID(jobID: string): Promise<void> {
  await JobModel.deleteOne({ _id: jobID }).catch((error) => {
    throw error;
  });
}

export async function getJobByID(jobID: string): Promise<IJob | null> {
  return JobModel.findById(jobID).catch((error) => {
    throw error;
  });
}

export async function updateJobByID(
  jobID: string,
  jobData: JobData,
): Promise<IJob | null> {
  return JobModel.findByIdAndUpdate(jobID, jobData, { new: true }).catch(
    (error) => {
      throw error;
    },
  );
}

export async function getAllAvailableJobs(
  limit: number,
  page: number,
): Promise<IJob[]> {
  return JobModel.find({
    published: true,
    applicationDeadline: { $gte: new Date() },
  })
    .populate({
      path: 'requiredSkills',
      select: 'name -_id',
    })
    .populate({
      path: 'companyID',
      select: 'name',
    })
    .limit(limit)
    .skip(limit * (page - 1))
    .catch((error) => {
      throw error;
    });
}

export async function getCompanyJobs(
  companyID: string,
  limit: number,
  page: number,
): Promise<IJob[]> {
  return JobModel.find({ companyID })
    .populate({
      path: 'requiredSkills',
      select: 'name -_id',
    })
    .populate({
      path: 'companyID',
      select: 'name',
    })
    .limit(limit)
    .skip(limit * (page - 1))
    .catch((error) => {
      throw error;
    });
}

export async function getCompanyJobsCount(companyID: string): Promise<number> {
  return JobModel.countDocuments({ companyID }).catch((error) => {
    throw error;
  });
}

export async function getAvailableJobsBySkills(
  skills: string[],
  limit: number,
  page: number,
): Promise<IJob[]> {
  return JobModel.find({
    published: true,
    applicationDeadline: { $gte: new Date() },
    requiredSkills: { $all: skills },
  })
    .populate({
      path: 'requiredSkills',
      select: 'name -_id',
    })
    .populate({
      path: 'companyID',
      select: 'name',
    })
    .limit(limit)
    .skip(limit * (page - 1))
    .catch((error) => {
      throw error;
    });
}

export async function getNumberOfAvailableJobs(): Promise<number> {
  return JobModel.countDocuments({
    published: true,
    applicationDeadline: { $gte: new Date() },
  }).catch((error) => {
    throw error;
  });
}

export async function getNumberOfAvailableJobsBySkills(
  skills: string[],
): Promise<number> {
  return JobModel.countDocuments({
    published: true,
    applicationDeadline: { $gte: new Date() },
    requiredSkills: { $all: skills },
  }).catch((error) => {
    throw error;
  });
}

// Check if the job exists
export async function checkJobExists(jobID: string): Promise<boolean> {
  const job = await JobModel.findById(jobID).catch((error) => {
    throw error;
  });
  return job !== null;
}

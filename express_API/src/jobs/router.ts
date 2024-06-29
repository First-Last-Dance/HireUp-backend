import express from 'express';
import * as Job from './controller';
import { requireAuth, requireCompany } from '../util/authentication';
import { CodedError } from '../util/error';
import { JobData } from './model';

const jobRoutes = express.Router();

/**
 * @swagger
 * tags:
 *   name: Job
 *   description: API endpoints for managing jobs
 */

/**
 * @swagger
 * /job/addJob:
 *   post:
 *     summary: Add a new job.
 *     tags: [Job]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               title:
 *                 type: string
 *               description:
 *                 type: string
 *               requiredSkills:
 *                 type: array
 *                 items:
 *                   type: string
 *               salary:
 *                 type: string
 *               applicationDeadline:
 *                 type: string
 *               quizDeadline:
 *                 type: string
 *               interviewDeadline:
 *                 type: string
 *               quizRequired:
 *                 type: boolean
 *     responses:
 *       '200':
 *         description: Job added successfully
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error
 */
jobRoutes.post('/addJob', requireAuth, requireCompany, async (req, res) => {
  const companyEmail = res.locals.email;
  const {
    title,
    description,
    requiredSkills,
    salary,
    applicationDeadline,
    quizDeadline,
    interviewDeadline,
    quizRequired,
  } = req.body;
  if (!title) {
    res.status(400).send('Title is required');
  } else if (!description) {
    res.status(400).send('Description is required');
  } else if (!requiredSkills) {
    res.status(400).send('Required skills are required');
  } else if (!salary) {
    res.status(400).send('Salary is required');
  } else if (!applicationDeadline) {
    res.status(400).send('Application deadline is required');
  } else if (!quizDeadline) {
    res.status(400).send('Quiz deadline is required');
  } else if (!interviewDeadline) {
    res.status(400).send('Interview deadline is required');
  } else if (quizRequired === undefined) {
    res.status(400).send('Quiz required is required');
  } else {
    await Job.addJob(
      title,
      description,
      requiredSkills,
      salary,
      companyEmail,
      applicationDeadline,
      quizDeadline,
      interviewDeadline,
      quizRequired,
    )
      .then((id) => {
        res.status(200).send({ id: id });
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

/**
 * @swagger
 * /job/availableJobs:
 *   get:
 *     summary: Get available jobs.
 *     tags: [Job]
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: string
 *         required: true
 *         description: Number of jobs per page
 *       - in: query
 *         name: page
 *         schema:
 *           type: string
 *         required: true
 *         description: Page number
 *     responses:
 *       '200':
 *         description: Jobs retrieved successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '500':
 *         description: Internal server error.
 */
jobRoutes.get('/availableJobs', async (req, res) => {
  const { limit, page } = req.query;
  if (!limit) {
    res.status(400).send('Limit is required');
  } else if (!page) {
    res.status(400).send('Page is required');
  } else {
    const startIndex =
      (parseInt(page as string) - 1) * parseInt(limit as string);
    const endIndex = parseInt(page as string) * parseInt(limit as string);
    const numberOfAvailableJobs = await Job.getNumberOfAvailableJobs();
    const pagesCount = Math.ceil(
      numberOfAvailableJobs / parseInt(limit as string),
    );
    await Job.getAllAvailableJobs(
      parseInt(limit as string),
      parseInt(page as string),
    )
      .then(async (jobs) => {
        const results: {
          previous?: { page: number; limit: number };
          next?: { page: number; limit: number };
          jobs: JobData[];
          pages: { count: number; limit: number };
        } = {
          jobs: jobs,
          pages: { count: pagesCount, limit: parseInt(limit as string) },
        };
        if (endIndex < numberOfAvailableJobs) {
          results.next = {
            page: parseInt(page as string) + 1,
            limit: parseInt(limit as string),
          };
        }
        if (startIndex > 0) {
          results.previous = {
            page: parseInt(page as string) - 1,
            limit: parseInt(limit as string),
          };
        }
        res.status(200).send(results);
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

/**
 * @swagger
 * /job/:
 *   delete:
 *     summary: Delete a job by ID.
 *     tags: [Job]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: jobID
 *         schema:
 *           type: string
 *         required: true
 *         description: Job ID
 *     responses:
 *       '200':
 *         description: Job deleted successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
jobRoutes.delete('/', requireAuth, requireCompany, async (req, res) => {
  const companyEmail = res.locals.email;
  const { jobID } = req.query;
  if (!jobID) {
    res.status(400).send('Job ID is required');
  } else {
    await Job.deleteJobByID(jobID as string, companyEmail)
      .then(() => {
        res.status(200).send('Job deleted successfully');
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

/**
 * @swagger
 * /job:
 *   get:
 *     summary: Get jobs by company.
 *     tags: [Job]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: string
 *         required: true
 *         description: Number of jobs per page
 *       - in: query
 *         name: page
 *         schema:
 *           type: string
 *         required: true
 *         description: Page number
 *     responses:
 *       '200':
 *         description: Jobs retrieved successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
jobRoutes.get('/', requireAuth, requireCompany, async (req, res) => {
  const companyEmail = res.locals.email;
  const { limit, page } = req.query;
  if (!limit) {
    res.status(400).send('Limit is required');
  } else if (!page) {
    res.status(400).send('Page is required');
  } else {
    const startIndex =
      (parseInt(page as string) - 1) * parseInt(limit as string);
    const endIndex = parseInt(page as string) * parseInt(limit as string);
    const numberOfAvailableJobs = await Job.getCompanyJobsCount(companyEmail);
    const pagesCount = Math.ceil(
      numberOfAvailableJobs / parseInt(limit as string),
    );
    await Job.getJobsByCompany(
      companyEmail,
      parseInt(limit as string),
      parseInt(page as string),
    )
      .then(async (jobs) => {
        const results: {
          previous?: { page: number; limit: number };
          next?: { page: number; limit: number };
          jobs: JobData[];
          pages: { count: number; limit: number };
        } = {
          jobs: jobs,
          pages: { count: pagesCount, limit: parseInt(limit as string) },
        };
        if (endIndex < numberOfAvailableJobs) {
          results.next = {
            page: parseInt(page as string) + 1,
            limit: parseInt(limit as string),
          };
        }
        if (startIndex > 0) {
          results.previous = {
            page: parseInt(page as string) - 1,
            limit: parseInt(limit as string),
          };
        }
        res.status(200).send(results);
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

/**
 * @swagger
 * /job/{jobID}:
 *   get:
 *     summary: Get a job by ID.
 *     tags: [Job]
 *     parameters:
 *       - in: path
 *         name: jobID
 *         schema:
 *           type: string
 *         required: true
 *         description: Job ID
 *     responses:
 *       '200':
 *         description: Job retrieved successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '500':
 *         description: Internal server error.
 */
jobRoutes.get('/:jobID', async (req, res) => {
  const jobID = req.params.jobID;
  if (!jobID) {
    res.status(400).send('Job ID is required');
  } else {
    await Job.getJobByID(jobID as string)
      .then((job) => {
        res.status(200).send(job);
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

/**
 * @swagger
 * /job/questions:
 *   post:
 *     summary: Add interview questions for a job.
 *     tags: [Job]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               jobID:
 *                 type: string
 *               questions:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     question:
 *                       type: string
 *                     answer:
 *                       type: string
 *               numberOfInterviewQuestions:
 *                 type: integer
 *     responses:
 *       '200':
 *         description: Questions added successfully
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error
 */
jobRoutes.post('/questions', requireAuth, requireCompany, async (req, res) => {
  const companyEmail = res.locals.email;
  const { jobID, questions, numberOfInterviewQuestions } = req.body;
  if (!jobID) {
    res.status(400).send('Job ID is required');
  } else if (!questions) {
    res.status(400).send('Questions are required');
  } else if (!numberOfInterviewQuestions) {
    res.status(400).send('Number of interview questions is required');
  } else if (questions.length < numberOfInterviewQuestions) {
    res
      .status(400)
      .send(
        'Number of interview questions is greater than the number of questions',
      );
  } else {
    interface Question {
      question: string;
      answer: string;
    }
    // Validate format of each question
    const isQuestionsFormatValid = questions.every(
      (q: Question) =>
        typeof q === 'object' &&
        typeof q.question === 'string' &&
        typeof q.answer === 'string',
    );

    if (!isQuestionsFormatValid) {
      return res.status(400).send('Invalid format for questions');
    }
    await Job.addJobQuestion(
      companyEmail,
      jobID,
      questions,
      numberOfInterviewQuestions,
    )
      .then(() => {
        res.status(200).send('Questions added successfully');
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  }
});

export default jobRoutes;

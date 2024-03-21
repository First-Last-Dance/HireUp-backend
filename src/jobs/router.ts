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
  if (
    !title ||
    !description ||
    !requiredSkills ||
    !salary ||
    !applicationDeadline ||
    !quizDeadline ||
    !interviewDeadline ||
    !quizRequired
  ) {
    res.status(400).send('Missing parameters');
  }
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
    .then(() => {
      res.status(200).send('Job added successfully');
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    });
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
  if (!limit || !page) {
    res.status(400).send('Missing parameters');
  }
  const startIndex = (parseInt(page as string) - 1) * parseInt(limit as string);
  const endIndex = parseInt(page as string) * parseInt(limit as string);
  await Job.getAllAvailableJobs(
    parseInt(limit as string),
    parseInt(page as string),
  )
    .then(async (jobs) => {
      const results: {
        previous?: { page: number; limit: number };
        next?: { page: number; limit: number };
        jobs: JobData[];
      } = {
        jobs: jobs,
      };
      if (endIndex < (await Job.getNumberOfAvailableJobs())) {
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
      res.status(500).send(err);
    });
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
    res.status(400).send('Missing parameters');
  }
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
});

/**
 * @swagger
 * /job:
 *   get:
 *     summary: Get a job by ID.
 *     tags: [Job]
 *     parameters:
 *       - in: query
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

jobRoutes.get('/', async (req, res) => {
  const { jobID } = req.query;
  if (!jobID) {
    res.status(400).send('Missing parameters');
  }
  await Job.getJobByID(jobID as string)
    .then((job) => {
      res.status(200).send(job);
    })
    .catch((err) => {
      res.status(500).send(err);
    });
});

export default jobRoutes;

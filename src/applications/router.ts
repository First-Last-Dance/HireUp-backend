import express from 'express';
import * as Application from './controller';
import {
  requireApplicant,
  requireAuth,
  requireCompany,
} from '../util/authentication';
import { CodedError } from '../util/error';
import { ApplicationData } from './model';

const applicationRoutes = express.Router();

/**
 * @swagger
 * tags:
 *   name: Application
 *   description: API endpoints for managing applications
 */

/**
 * @swagger
 * components:
 *   schemas:
 *     Application:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *         jobID:
 *           type: string
 *         applicantID:
 *           type: string
 *         status:
 *           type: string
 *           enum: [pending, accepted, rejected]
 *       required:
 *         - jobID
 *         - applicantID
 *         - status
 */

/**
 * @swagger
 * /application:
 *   post:
 *     summary: Add a new application
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - jobID
 *             properties:
 *               jobID:
 *                 type: string
 *                 description: The unique identifier of the job to apply for
 *     responses:
 *       200:
 *         description: A newly created application object
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Application'
 *       400:
 *         description: Bad request, jobID is missing
 *       500:
 *         description: Internal server error
 */
applicationRoutes.post('/', requireAuth, requireApplicant, (req, res) => {
  const { jobID } = req.body;
  if (!jobID) {
    return res.status(400).send('jobID is required');
  }
  const applicantEmail = res.locals.email;

  Application.addApplication(jobID, applicantEmail)
    .then((application) => {
      res.status(200).json(application);
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err.message);
      }
    });
});

/**
 * @swagger
 * /application:
 *   get:
 *     summary: Get all applications of the current applicant
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: limit
 *         required: true
 *         schema:
 *           type: integer
 *         description: The number of items to return
 *       - in: query
 *         name: page
 *         required: true
 *         schema:
 *           type: integer
 *         description: The page number to return
 *     responses:
 *       200:
 *         description: An array of application documents with pagination details
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 previous:
 *                   type: object
 *                   properties:
 *                     page:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *                 next:
 *                   type: object
 *                   properties:
 *                     page:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *                 applications:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Application'
 *                 pages:
 *                   type: object
 *                   properties:
 *                     count:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *       400:
 *         description: Bad request, limit or page query parameter missing
 *       500:
 *         description: Internal server error
 */
applicationRoutes.get('/', requireAuth, requireApplicant, async (req, res) => {
  const applicantEmail = res.locals.email;
  const { limit, page } = req.query;
  if (!limit) {
    res.status(400).send('Limit is required');
  } else if (!page) {
    res.status(400).send('Page is required');
  } else {
    const startIndex =
      (parseInt(page as string) - 1) * parseInt(limit as string);
    const endIndex = parseInt(page as string) * parseInt(limit as string);
    const numberOfApplications =
      await Application.getApplicationsCountByApplicantEmail(applicantEmail);
    const pagesCount = Math.ceil(
      numberOfApplications / parseInt(limit as string),
    );

    await Application.getApplicationsByApplicantEmail(
      applicantEmail,
      parseInt(limit as string),
      parseInt(page as string),
    )
      .then(async (applications) => {
        const results: {
          previous?: { page: number; limit: number };
          next?: { page: number; limit: number };
          applications: ApplicationData[];
          pages: { count: number; limit: number };
        } = {
          applications: applications,
          pages: { count: pagesCount, limit: parseInt(limit as string) },
        };
        if (endIndex < numberOfApplications) {
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
 * /application/getApplicationsByJobId/{jobID}:
 *   get:
 *     summary: Get all applications of a job by job ID with pagination
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: jobID
 *         schema:
 *           type: string
 *         required: true
 *         description: The ID of the job
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 10
 *         required: true
 *         description: The number of items to return per page
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           default: 1
 *         required: true
 *         description: The page number to return
 *     responses:
 *       200:
 *         description: An array of application documents with pagination details
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 previous:
 *                   type: object
 *                   properties:
 *                     page:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *                 next:
 *                   type: object
 *                   properties:
 *                     page:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *                 applications:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Application'
 *                 pages:
 *                   type: object
 *                   properties:
 *                     count:
 *                       type: integer
 *                     limit:
 *                       type: integer
 *       400:
 *         description: Bad request, required parameters are missing
 *       500:
 *         description: Internal server error
 */
applicationRoutes.get(
  '/getApplicationsByJobId',
  requireAuth,
  requireCompany,
  async (req, res) => {
    const jobID = req.params.jobID;
    const companyEmail = res.locals.email;
    if (!jobID) {
      return res.status(400).send('jobID is required');
    }
    const { limit, page } = req.query;
    if (!limit) {
      res.status(400).send('Limit is required');
    } else if (!page) {
      res.status(400).send('Page is required');
    } else {
      const startIndex =
        (parseInt(page as string) - 1) * parseInt(limit as string);
      const endIndex = parseInt(page as string) * parseInt(limit as string);
      const numberOfApplications =
        await Application.getApplicationsCountByJobID(
          jobID as unknown as string,
        );
      const pagesCount = Math.ceil(
        numberOfApplications / parseInt(limit as string),
      );

      await Application.getApplicationsByJobId(
        jobID as string,
        companyEmail,
        parseInt(limit as string),
        parseInt(page as string),
      )
        .then(async (applications) => {
          const results: {
            previous?: { page: number; limit: number };
            next?: { page: number; limit: number };
            applications: ApplicationData[];
            pages: { count: number; limit: number };
          } = {
            applications: applications,
            pages: { count: pagesCount, limit: parseInt(limit as string) },
          };
          if (endIndex < numberOfApplications) {
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
  },
);

/**
 * @swagger
 * /application/applied:
 *   get:
 *     summary: Check if an application exists for the current applicant and specified job
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: jobID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the job to check the application status for
 *     responses:
 *       200:
 *         description: Status of the application existence
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 exists:
 *                   type: boolean
 *       400:
 *         description: Bad request, jobID query parameter missing
 *       500:
 *         description: Internal server error
 */

applicationRoutes.get(
  '/applied',
  requireAuth,
  requireApplicant,
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const jobID = req.query.jobID as string;
    Application.checkApplicationExists(applicantEmail, jobID)
      .then((applicationExists) => {
        res.status(200).send({ exists: applicationExists });
      })
      .catch((err) => {
        if (err instanceof CodedError) {
          res.status(err.code).send(err.message);
        } else {
          res.status(500).send(err);
        }
      });
  },
);

/**
 * @swagger
 * /application/{applicationID}:
 *   get:
 *     summary: Get an application by ID
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         schema:
 *           type: string
 *         required: true
 *         description: The ID of the application
 *     responses:
 *       200:
 *         description: An application document
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Application'
 *       400:
 *         description: Bad request, applicationID is missing
 *       500:
 *         description: Internal server error
 */
applicationRoutes.get('/:applicationID', requireAuth, (req, res) => {
  const { applicationID } = req.params;
  if (!applicationID) {
    return res.status(400).send('applicationID is required');
  }

  Application.getApplicationById(applicationID as string)
    .then((application) => {
      if (!application) {
        return res.status(404).send('Application not found');
      }
      res.status(200).json(application);
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    });
});

export default applicationRoutes;

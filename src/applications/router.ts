import express from 'express';
import * as Application from './controller';
import {
  requireApplicant,
  requireAuth,
  requireCompany,
} from '../util/authentication';
import { CodedError } from '../util/error';

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
 *             $ref: '#/components/schemas/Application'
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
 *     responses:
 *       200:
 *         description: An array of application documents
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Application'
 *       500:
 *         description: Internal server error
 */
applicationRoutes.get('/', requireAuth, requireApplicant, (req, res) => {
  const applicantEmail = res.locals.email;

  Application.getApplicationsByApplicantId(applicantEmail)
    .then((applications) => {
      res.status(200).json(applications);
    })
    .catch((err) => {
      res.status(500).send(err.message);
    });
});

/**
 * @swagger
 * /application/getApplicationsByJobId:
 *   get:
 *     summary: Get all applications of a job by job ID
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: jobID
 *         schema:
 *           type: string
 *         required: true
 *         description: The ID of the job
 *     responses:
 *       200:
 *         description: An array of application documents
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Application'
 *       400:
 *         description: Bad request, jobID is missing
 *       500:
 *         description: Internal server error
 */
applicationRoutes.get(
  '/getApplicationsByJobId',
  requireAuth,
  requireCompany,
  (req, res) => {
    const { jobID } = req.query;
    const companyEmail = res.locals.email;
    if (!jobID) {
      return res.status(400).send('jobID is required');
    }

    Application.getApplicationsByJobId(jobID as string, companyEmail)
      .then((applications) => {
        res.status(200).json(applications);
      })
      .catch((err) => {
        res.status(500).send(err.message);
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
      res.status(500).send(err.message);
    });
});

export default applicationRoutes;

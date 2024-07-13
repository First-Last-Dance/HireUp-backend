import express, { application } from 'express';
import * as Application from './controller';
import fs from 'fs';
import {
  requireAdmin,
  requireApplicant,
  requireAuth,
  requireCompany,
} from '../util/authentication';
import { CodedError } from '../util/error';
import { ApplicationData } from './model';
import * as pythonAPI from '../pythonAPI/controller';
import multer from 'multer';
import * as dotenv from 'dotenv';

const applicationRoutes = express.Router();

// Multer file filter to handle wrong file names
const fileFilter = (req: any, file: any, cb: any) => {
  if (file.originalname.match(/\.(jpg|jpeg|png)$/)) {
    // Accept the file
    cb(null, true);
  } else {
    // Reject the file
    cb(
      new multer.MulterError('LIMIT_UNEXPECTED_FILE', 'Invalid file type'),
      false,
    );
  }
};
const upload = multer({
  storage: multer.memoryStorage(),
  fileFilter,
});

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
  '/getApplicationsByJobId/:jobID',
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

      await Application.getApplicationsByJobID(
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

/**
 * @swagger
 * /application/{applicationID}/startQuiz:
 *   get:
 *     summary: Starts a quiz for a given application
 *     description: This endpoint starts a quiz for the applicant associated with the given application ID.
 *     tags: [Application]
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application to start the quiz for
 *     responses:
 *       200:
 *         description: Quiz started successfully. Returns the quiz details.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 questions:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       text:
 *                         type: string
 *                         description: The text of the question.
 *                       answers:
 *                         type: array
 *                         items:
 *                           type: string
 *                         description: An array of possible answers.
 *                 applicationID:
 *                   type: string
 *                   description: The ID of the application the quiz is associated with.
 *                 quizDeadline:
 *                   type: string
 *                   format: date-time
 *                   description: The deadline by which the quiz must be completed.
 *                 quizDurationInMinutes:
 *                   type: integer
 *                   description: The duration of the quiz in minutes.
 *       400:
 *         description: Bad request. Possible reason could be invalid application ID.
 *       401:
 *         description: Unauthorized. User is not logged in or does not have permission to start the quiz.
 *       500:
 *         description: Internal server error.
 *     security:
 *       - bearerAuth: []
 */

applicationRoutes.get(
  '/:applicationID/startQuiz',
  requireAuth,
  requireApplicant,
  async (req, res) => {
    const applicationID = req.params.applicationID;
    const applicantEmail = res.locals.email;
    Application.startQuiz(applicantEmail, applicationID)
      .then((quiz) => {
        res.status(200).send(quiz);
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
 * /application/{applicationID}/submitQuiz:
 *   post:
 *     summary: Submit quiz answers for a given application
 *     description: This endpoint allows an applicant to submit quiz answers for the specified application ID.
 *     tags: [Application]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz answers are being submitted
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               applicationID:
 *                 type: string
 *                 description: The ID of the application
 *               answers:
 *                 type: array
 *                 items:
 *                   type: string
 *                   description: The answers provided by the applicant
 *     responses:
 *       200:
 *         description: Quiz answers submitted successfully. Indicates if the applicant passed or failed.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 result:
 *                   type: string
 *                   description: Result of the quiz, either 'Passed' or 'Failed'
 *       400:
 *         description: Bad request. Possible reasons could be invalid application ID or missing answers.
 *       401:
 *         description: Unauthorized. User is not logged in or does not have permission to submit the quiz.
 *       500:
 *         description: Internal server error.
 */

applicationRoutes.post(
  '/:applicationID/submitQuiz',
  requireAuth,
  requireApplicant,
  async (req, res) => {
    const applicationID = req.params.applicationID;
    const applicantEmail = res.locals.email;
    const { answers } = req.body;
    Application.submitQuiz(applicantEmail, applicationID, answers)
      .then((result) => {
        res.status(200).send({ result: result ? 'Passed' : 'Failed' });
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
 * /application/{applicationID}/startInterviewStream:
 *   get:
 *     summary: Starts an interview stream for a given application.
 *     description: Initiates the interview streaming process for the applicant associated with the given application ID.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application to start the interview stream for.
 *     responses:
 *       200:
 *         description: Interview stream started successfully.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 ip_address:
 *                   type: string
 *                   example: "192.168.44.1"
 *                 port:
 *                   type: integer
 *                   example: 5002
 *       400:
 *         description: Bad request. Possible reason could be missing or invalid application ID.
 *       401:
 *         description: Authorization information is missing or invalid.
 *       500:
 *         description: Internal server error.
 *     security:
 *       - bearerAuth: []
 *     tags: [Application]
 */
applicationRoutes.get(
  '/:applicationID/startInterviewStream',
  requireAuth,
  requireApplicant,
  (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    pythonAPI
      .startInterviewStream(applicantEmail, applicationID)
      .then((result) => {
        res.status(200).send(result);
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
 * /application/{applicationID}/startQuizStream:
 *   get:
 *     summary: Starts a quiz stream for a given application.
 *     description: Initiates the quiz streaming process for the applicant associated with the given application ID.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application to start the quiz stream for.
 *     responses:
 *       200:
 *         description: Quiz stream started successfully.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 ip_address:
 *                   type: string
 *                   example: "192.168.55.1"
 *                 port:
 *                   type: integer
 *                   example: 5003
 *       400:
 *         description: Bad request. Possible reason could be missing or invalid application ID.
 *       401:
 *         description: Authorization information is missing or invalid.
 *       500:
 *         description: Internal server error.
 *     security:
 *       - bearerAuth: []
 *     tags: [Application]
 */

applicationRoutes.get(
  '/:applicationID/startQuizStream',
  requireAuth,
  requireApplicant,
  (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    pythonAPI
      .startQuizStream(applicantEmail, applicationID)
      .then((result) => {
        res.status(200).send(result);
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
 * /application/{applicationID}/quizCalibration:
 *   post:
 *     summary: Submits calibration images for a quiz.
 *     description: Receives four calibration images from the applicant and processes them for quiz calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz calibration is being performed.
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               pictureUpRight:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing up-right, encoded in base64.
 *               pictureUpLeft:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing up-left, encoded in base64.
 *               pictureDownRight:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing down-right, encoded in base64.
 *               pictureDownLeft:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing down-left, encoded in base64.
 *             required:
 *               - pictureUpRight
 *               - pictureUpLeft
 *               - pictureDownRight
 *               - pictureDownLeft
 *     responses:
 *       200:
 *         description: Calibration process completed successfully. Returns result of the calibration.
 *       400:
 *         description: Bad request. Possible reasons include missing images or invalid application ID.
 *       401:
 *         description: Unauthorized. User authentication failed.
 *       500:
 *         description: Internal server error.
 *     security:
 *       - bearerAuth: []
 *     tags:
 *       - Application
 */

applicationRoutes.post(
  '/:applicationID/quizCalibration',
  requireAuth,
  requireApplicant,
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;

    const { pictureUpRight, pictureUpLeft, pictureDownRight, pictureDownLeft } =
      req.body;

    // Ensure all images are provided
    if (
      !pictureUpRight ||
      !pictureUpLeft ||
      !pictureDownRight ||
      !pictureDownLeft
    ) {
      return res.status(400).send('All images are required');
    }

    // Remove the data URL prefix
    // const base64Prefix = 'data:image/jpeg;base64,';
    // const pictureUpRightBase64 = pictureUpRight.replace(base64Prefix, '');
    // const pictureUpLeftBase64 = pictureUpLeft.replace(base64Prefix, '');
    // const pictureDownRightBase64 = pictureDownRight.replace(base64Prefix, '');
    // const pictureDownLeftBase64 = pictureDownLeft.replace(base64Prefix, '');

    try {
      // Convert images to Base64
      // const pictureUpRightBase64 = pictureUpRight[0].buffer.toString('base64');
      // const pictureUpLeftBase64 = pictureUpLeft[0].buffer.toString('base64');
      // const pictureDownRightBase64 =
      //   pictureDownRight[0].buffer.toString('base64');
      // const pictureDownLeftBase64 =
      //   pictureDownLeft[0].buffer.toString('base64');

      // Call the python API with the images
      const result = await pythonAPI.quizCalibration(
        applicantEmail,
        applicationID,
        pictureUpRight,
        pictureUpLeft,
        pictureDownRight,
        pictureDownLeft,
      );

      // Send the result back to the client
      res.status(200).send(result);
    } catch (err) {
      // Handle errors from the python API
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    }
  },
);

/**
 * @swagger
 * /application/{applicationID}/interviewCalibration:
 *   post:
 *     summary: Submits calibration images for a interview.
 *     description: Receives four calibration images from the applicant and processes them for interview calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the interview calibration is being performed.
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               pictureUpRight:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing up-right, encoded in base64.
 *               pictureUpLeft:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing up-left, encoded in base64.
 *               pictureDownRight:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing down-right, encoded in base64.
 *               pictureDownLeft:
 *                 type: string
 *                 format: base64
 *                 description: Calibration image captured with the camera facing down-left, encoded in base64.
 *             required:
 *               - pictureUpRight
 *               - pictureUpLeft
 *               - pictureDownRight
 *               - pictureDownLeft
 *     responses:
 *       200:
 *         description: Calibration process completed successfully. Returns result of the calibration.
 *       400:
 *         description: Bad request. Possible reasons include missing images or invalid application ID.
 *       401:
 *         description: Unauthorized. User authentication failed.
 *       500:
 *         description: Internal server error.
 *     security:
 *       - bearerAuth: []
 *     tags:
 *       - Application
 */

applicationRoutes.post(
  '/:applicationID/interviewCalibration',
  requireAuth,
  requireApplicant,
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;

    const { pictureUpRight, pictureUpLeft, pictureDownRight, pictureDownLeft } =
      req.body;

    // Ensure all images are provided
    if (
      !pictureUpRight ||
      !pictureUpLeft ||
      !pictureDownRight ||
      !pictureDownLeft
    ) {
      return res.status(400).send('All images are required');
    }

    // Remove the data URL prefix
    // const base64Prefix = 'data:image/jpeg;base64,';
    // const pictureUpRightBase64 = pictureUpRight.replace(base64Prefix, '');
    // const pictureUpLeftBase64 = pictureUpLeft.replace(base64Prefix, '');
    // const pictureDownRightBase64 = pictureDownRight.replace(base64Prefix, '');
    // const pictureDownLeftBase64 = pictureDownLeft.replace(base64Prefix, '');

    try {
      // Convert images to Base64
      // const pictureUpRightBase64 = pictureUpRight[0].buffer.toString('base64');
      // const pictureUpLeftBase64 = pictureUpLeft[0].buffer.toString('base64');
      // const pictureDownRightBase64 =
      //   pictureDownRight[0].buffer.toString('base64');
      // const pictureDownLeftBase64 =
      //   pictureDownLeft[0].buffer.toString('base64');

      // Call the python API with the images
      const result = await pythonAPI.interviewCalibration(
        applicantEmail,
        applicationID,
        pictureUpRight,
        pictureUpLeft,
        pictureDownRight,
        pictureDownLeft,
      );

      // Send the result back to the client
      res.status(200).send(result);
    } catch (err) {
      // Handle errors from the python API
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    }
  },
);

/**
 * @swagger
 * /application/getFinishedApplicationsByJobId/{jobID}:
 *   get:
 *     summary: Get all finished applications of a job by job ID with pagination
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
 *                     type: object
 *                     properties:
 *                       applicantID:
 *                         type: string
 *                       applicantName:
 *                         type: string
 *                       jobID:
 *                         type: string
 *                       status:
 *                         type: string
 *                       applicationID:
 *                         type: string
 *                       companyName:
 *                         type: string
 *                       title:
 *                         type: string
 *                       steps:
 *                         type: array
 *                         items:
 *                           type: string
 *                       quizEyeCheating:
 *                         type: number
 *                       quizFaceSpeechCheating:
 *                         type: number
 *                       interviewQuestionsData:
 *                         type: array
 *                         items:
 *                           type: object
 *                           properties:
 *                             questionCheating:
 *                               type: number
 *                             questionFaceSpeechCheating:
 *                               type: number
 *                             questionSimilarity:
 *                               type: number
 *                             questionEmotions:
 *                               type: array
 *                               items:
 *                                 type: object
 *                                 properties:
 *                                   emotion:
 *                                     type: string
 *                                   ratio:
 *                                     type: number
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
  '/getFinishedApplicationsByJobId/:jobID',
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
        await Application.getApplicationsCountByJobIDAndStatus(
          jobID as unknown as string,
          'Final Result',
        );
      const pagesCount = Math.ceil(
        numberOfApplications / parseInt(limit as string),
      );

      await Application.getApplicationsByJobIDAndStatus(
        jobID as string,
        'Final Result',
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
 * /application/{applicationID}/details:
 *   get:
 *     summary: Get details of a specific application by application ID
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
 *         description: The details of the application
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 applicant:
 *                   type: object
 *                   properties:
 *                     email:
 *                       type: string
 *                     firstName:
 *                       type: string
 *                     middleName:
 *                       type: string
 *                     lastName:
 *                       type: string
 *                     phoneNumber:
 *                       type: string
 *                     nationalIDNumber:
 *                       type: string
 *                     profilePhoto:
 *                       type: string
 *                     nationalIDPhotoFace:
 *                       type: string
 *                     nationalIDPhotoBack:
 *                       type: string
 *                     skills:
 *                       type: array
 *                       items:
 *                         type: string
 *                 application:
 *                   type: object
 *                   properties:
 *                     applicantID:
 *                       type: string
 *                     applicantName:
 *                       type: string
 *                     jobID:
 *                       type: string
 *                     status:
 *                       type: string
 *                     applicationID:
 *                       type: string
 *                     companyName:
 *                       type: string
 *                     title:
 *                       type: string
 *                     steps:
 *                       type: array
 *                       items:
 *                         type: string
 *                     quizEyeCheating:
 *                       type: number
 *                     quizFaceSpeechCheating:
 *                       type: number
 *                     interviewQuestionsData:
 *                       type: array
 *                       items:
 *                         type: object
 *                         properties:
 *                           questionCheating:
 *                             type: number
 *                           questionFaceSpeechCheating:
 *                             type: number
 *                           questionSimilarity:
 *                             type: number
 *                           questionEmotions:
 *                             type: array
 *                             items:
 *                               type: object
 *                               properties:
 *                                 emotion:
 *                                   type: string
 *                                 ratio:
 *                                   type: number
 *       400:
 *         description: Bad request, required parameters are missing
 *       500:
 *         description: Internal server error
 */

applicationRoutes.get(
  '/:applicationID/details',
  requireAuth,
  requireCompany,
  async (req, res) => {
    const applicationID = req.params.applicationID;
    const companyEmail = res.locals.email;
    if (!applicationID) {
      return res.status(400).send('applicationID is required');
    }

    await Application.getApplicationDetails(
      applicationID as string,
      companyEmail,
    )
      .then(async (result) => {
        res.status(200).send(result);
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
 *  /application/{applicationID}/quizCheatingData:
 *   post:
 *     summary: Add quiz cheating data for a specific application
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
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               quizEyeCheating:
 *                 type: number
 *               quizFaceSpeechCheating:
 *                 type: number
 *     responses:
 *       200:
 *         description: Quiz cheating data updated successfully
 *       400:
 *         description: Bad request, required parameters are missing
 *       500:
 *         description: Internal server error
 *
 */

applicationRoutes.post(
  '/:applicationID/quizCheatingData',
  requireAuth,
  requireAdmin,
  async (req, res) => {
    const applicationID = req.params.applicationID;
    const {
      quizEyeCheating,
      quizFaceSpeechCheating,
      eyeCheatingDurations,
      speakingCheatingDurations,
    } = req.body;

    if (
      quizEyeCheating === undefined ||
      quizEyeCheating === null ||
      quizFaceSpeechCheating === undefined ||
      quizFaceSpeechCheating === null ||
      eyeCheatingDurations === undefined ||
      eyeCheatingDurations === null ||
      speakingCheatingDurations === undefined ||
      speakingCheatingDurations === null
    ) {
      return res
        .status(400)
        .send(
          'Both quizEyeCheating and quizFaceSpeechCheating and eyeCheatingDurations and speakingCheatingDurations are required',
        );
    }
    try {
      await Application.addQuizCheatingData(
        applicationID,
        quizEyeCheating,
        quizFaceSpeechCheating,
        eyeCheatingDurations,
        speakingCheatingDurations,
      );
      res.status(200).send('Quiz cheating data updated successfully');
    } catch (err) {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    }
  },
);

/**
 * @swagger
 * /application/{applicationID}/interviewQuestionData:
 *   post:
 *     summary: Add interview question data for a specific application
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
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               questionEyeCheating:
 *                 type: number
 *               questionFaceSpeechCheating:
 *                 type: number
 *               questionSimilarity:
 *                 type: number
 *               questionEmotions:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     emotion:
 *                       type: string
 *                     ratio:
 *                       type: number
 *     responses:
 *       200:
 *         description: Interview question data updated successfully
 *       400:
 *         description: Bad request, required parameters are missing
 *       500:
 *         description: Internal server error
 */

applicationRoutes.post(
  '/:applicationID/interviewQuestionData',
  requireAuth,
  requireAdmin,
  async (req, res) => {
    const applicationID = req.params.applicationID;
    const {
      questionEyeCheating,
      questionFaceSpeechCheating,
      questionSimilarity,
      questionEmotions,
      questionEyeCheatingDurations,
      questionSpeakingCheatingDurations,
    } = req.body;
    if (
      typeof questionEyeCheating === 'undefined' ||
      questionEyeCheating === null ||
      typeof questionFaceSpeechCheating === 'undefined' ||
      questionFaceSpeechCheating === null ||
      typeof questionSimilarity === 'undefined' ||
      questionSimilarity === null ||
      typeof questionEmotions === 'undefined' ||
      questionEmotions === null ||
      typeof questionEyeCheatingDurations === 'undefined' ||
      questionEyeCheatingDurations === null ||
      typeof questionSpeakingCheatingDurations === 'undefined' ||
      questionSpeakingCheatingDurations === null
    ) {
      return res
        .status(400)
        .send(
          'All questionEyeCheating, questionFaceSpeechCheating, questionSimilarity, questionEyeCheatingDurations, questionSpeakingCheatingDurations , and questionEmotions are required',
        );
    }
    try {
      await Application.addInterviewQuestionData(
        applicationID,
        questionEyeCheating,
        questionFaceSpeechCheating,
        questionSimilarity,
        questionEmotions,
        questionEyeCheatingDurations,
        questionSpeakingCheatingDurations,
      );
      res.status(200).send('Interview question data updated successfully');
    } catch (err) {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    }
  },
);

// Config the .env file
dotenv.config();

/**
 * @swagger
 * /application/{applicationID}/quizVideo:
 *   get:
 *     summary: Get quiz video for a specific application
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
 *       - in: header
 *         name: range
 *         schema:
 *           type: string
 *         required: false
 *         description: Range of bytes to fetch from the video
 *     responses:
 *       200:
 *         description: Video fetched successfully
 *       206:
 *         description: Partial content
 *       400:
 *         description: Bad request
 *       416:
 *         description: Range not satisfiable
 *       500:
 *         description: Internal server error
 */

applicationRoutes.get(
  '/:applicationID/quizVideo',
  requireAuth,
  requireCompany,
  (req, res) => {
    const applicationID = req.params.applicationID;
    const videosPath = process.env.VIDEOS_PATH;
    const videoPath = `${videosPath}/quiz_video/${applicationID}.webm`; // Specify the exact path to the video file
    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;
    const range = req.headers.range;

    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;

      if (start >= fileSize) {
        res
          .status(416)
          .send(
            'Requested range not satisfiable\n' + start + ' >= ' + fileSize,
          );
        return;
      }

      const chunksize = end - start + 1;
      const file = fs.createReadStream(videoPath, { start, end });
      const head = {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mkv',
      };

      res.writeHead(206, head);
      file.pipe(res);
    } else {
      const head = {
        'Content-Length': fileSize,
        'Content-Type': 'video/mkv',
      };
      res.writeHead(200, head);
      fs.createReadStream(videoPath).pipe(res);
    }
  },
);

/**
 * @swagger
 * /application/{applicationID}/interviewVideo:
 *   get:
 *     summary: Get interview video for a specific application
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
 *       - in: query
 *         name: questionNumber
 *         schema:
 *           type: string
 *         required: true
 *         description: The question number of the interview
 *       - in: header
 *         name: range
 *         schema:
 *           type: string
 *         required: false
 *         description: Range of bytes to fetch from the video
 *     responses:
 *       200:
 *         description: Video fetched successfully
 *       206:
 *         description: Partial content
 *       400:
 *         description: Bad request
 *       416:
 *         description: Range not satisfiable
 *       500:
 *         description: Internal server error
 */

applicationRoutes.get(
  '/:applicationID/interviewVideo',
  requireAuth,
  requireCompany,
  (req, res) => {
    const applicationID = req.params.applicationID;
    const questionNumber = req.query.questionNumber as string;
    if (!questionNumber) {
      return res.status(400).send('questionNumber is required');
    }
    const videosPath = process.env.VIDEOS_PATH;
    const videoPath = `${videosPath}/interview_video/${applicationID}_${questionNumber}.webm`; // Specify the exact path to the video file
    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;
    const range = req.headers.range;

    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;

      if (start >= fileSize) {
        res
          .status(416)
          .send(
            'Requested range not satisfiable\n' + start + ' >= ' + fileSize,
          );
        return;
      }

      const chunksize = end - start + 1;
      const file = fs.createReadStream(videoPath, { start, end });
      const head = {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mkv',
      };

      res.writeHead(206, head);
      file.pipe(res);
    } else {
      const head = {
        'Content-Length': fileSize,
        'Content-Type': 'video/mkv',
      };
      res.writeHead(200, head);
      fs.createReadStream(videoPath).pipe(res);
    }
  },
);

// Error handling middleware
applicationRoutes.use(
  (
    err: Error,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction,
  ): void => {
    if (err instanceof multer.MulterError) {
      // Handle Multer errors
      res.status(400).send(`Multer error: ${err.message}`);
      next();
    } else {
      // Handle other errors
      res.status(500).send(`Server error: ${err.message}`);
      next();
    }
  },
);

export default applicationRoutes;

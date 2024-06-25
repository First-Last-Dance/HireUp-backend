import express, { application } from 'express';
import * as Application from './controller';
import {
  requireApplicant,
  requireAuth,
  requireCompany,
} from '../util/authentication';
import { CodedError } from '../util/error';
import { ApplicationData } from './model';
import * as pythonAPI from '../pythonAPI/controller';
import multer from 'multer';

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
 * /application/{applicationID}/quizCalibration/upRight:
 *   post:
 *     summary: Submits the up-right calibration image for a quiz.
 *     description: Receives the up-right calibration image from the applicant and processes it for quiz calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz calibration is being performed.
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               pictureUpRight:
 *                 type: string
 *                 format: binary
 *                 description: Calibration image captured with the camera facing up-right.
 *     responses:
 *       200:
 *         description: Up-right calibration image uploaded successfully.
 *       400:
 *         description: Bad request. Possible reasons include missing image or invalid application ID.
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
  '/:applicationID/quizCalibration/upRight',
  requireAuth,
  requireApplicant,
  upload.single('pictureUpRight'),
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    const pictureUpRight = req.file;

    // Ensure the image is provided
    if (!pictureUpRight) {
      return res.status(400).send('Up-right image is required');
    }

    try {
      // Convert image to Base64
      const pictureUpRightBase64 = pictureUpRight.buffer.toString('base64');

      // Call the python API with the image
      const result = await pythonAPI.quizCalibrationUpRight(
        applicantEmail,
        applicationID,
        pictureUpRightBase64,
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
 * /application/{applicationID}/quizCalibration/upLeft:
 *   post:
 *     summary: Submits the up-left calibration image for a quiz.
 *     description: Receives the up-left calibration image from the applicant and processes it for quiz calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz calibration is being performed.
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               pictureUpLeft:
 *                 type: string
 *                 format: binary
 *                 description: Calibration image captured with the camera facing up-left.
 *     responses:
 *       200:
 *         description: Up-left calibration image uploaded successfully.
 *       400:
 *         description: Bad request. Possible reasons include missing image or invalid application ID.
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
  '/:applicationID/quizCalibration/upLeft',
  requireAuth,
  requireApplicant,
  upload.single('pictureUpLeft'),
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    const pictureUpLeft = req.file;

    // Ensure the image is provided
    if (!pictureUpLeft) {
      return res.status(400).send('Up-left image is required');
    }

    try {
      // Convert image to Base64
      const pictureUpLeftBase64 = pictureUpLeft.buffer.toString('base64');

      // Call the python API with the image
      const result = await pythonAPI.quizCalibrationUpLeft(
        applicantEmail,
        applicationID,
        pictureUpLeftBase64,
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
 * /application/{applicationID}/quizCalibration/downRight:
 *   post:
 *     summary: Submits the down-right calibration image for a quiz.
 *     description: Receives the down-right calibration image from the applicant and processes it for quiz calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz calibration is being performed.
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               pictureDownRight:
 *                 type: string
 *                 format: binary
 *                 description: Calibration image captured with the camera facing down-right.
 *     responses:
 *       200:
 *         description: Down-right calibration image uploaded successfully.
 *       400:
 *         description: Bad request. Possible reasons include missing image or invalid application ID.
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
  '/:applicationID/quizCalibration/downRight',
  requireAuth,
  requireApplicant,
  upload.single('pictureDownRight'),
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    const pictureDownRight = req.file;

    // Ensure the image is provided
    if (!pictureDownRight) {
      return res.status(400).send('Down-right image is required');
    }

    try {
      // Convert image to Base64
      const pictureDownRightBase64 = pictureDownRight.buffer.toString('base64');

      // Call the python API with the image
      const result = await pythonAPI.quizCalibrationDownRight(
        applicantEmail,
        applicationID,
        pictureDownRightBase64,
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
 * /application/{applicationID}/quizCalibration/downLeft:
 *   post:
 *     summary: Submits the down-left calibration image for a quiz.
 *     description: Receives the down-left calibration image from the applicant and processes it for quiz calibration.
 *     parameters:
 *       - in: path
 *         name: applicationID
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the application for which the quiz calibration is being performed.
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               pictureDownLeft:
 *                 type: string
 *                 format: binary
 *                 description: Calibration image captured with the camera facing down-left.
 *     responses:
 *       200:
 *         description: Down-left calibration image uploaded successfully.
 *       400:
 *         description: Bad request. Possible reasons include missing image or invalid application ID.
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
  '/:applicationID/quizCalibration/downLeft',
  requireAuth,
  requireApplicant,
  upload.single('pictureDownLeft'),
  async (req, res) => {
    const applicantEmail = res.locals.email;
    const applicationID = req.params.applicationID;
    const pictureDownLeft = req.file;

    // Ensure the image is provided
    if (!pictureDownLeft) {
      return res.status(400).send('Down-left image is required');
    }

    try {
      // Convert image to Base64
      const pictureDownLeftBase64 = pictureDownLeft.buffer.toString('base64');

      // Call the python API with the image
      const result = await pythonAPI.quizCalibrationDownLeft(
        applicantEmail,
        applicationID,
        pictureDownLeftBase64,
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

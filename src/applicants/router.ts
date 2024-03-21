import express from 'express';
import multer from 'multer';
import * as Applicant from './controller';
import { CodedError } from '../util/error';
import { requireAuth } from '../util/authentication';

const applicantRoutes = express.Router();

// Multer file filter to handle wrong file names
const fileFilter = (req: any, file: any, cb: any) => {
  if (file.originalname.match(/\.(jpg|jpeg|png)$/)) {
    // Accept the file
    cb(null, true);
  } else {
    // Reject the file
    cb(new Error('Invalid file type'), false);
  }
};
const upload = multer({
  storage: multer.memoryStorage(),
  fileFilter,
});

/**
 * @swagger
 * tags:
 *   name: Applicant
 *   description: API endpoints for managing applicants
 */

/**
 * @swagger
 * /applicant/register:
 *   post:
 *     summary: Register a new applicant.
 *     tags: [Applicant]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *               password:
 *                 type: string
 *               firstName:
 *                 type: string
 *               middleName:
 *                 type: string
 *               lastName:
 *                 type: string
 *               phoneNumber:
 *                 type: string
 *               nationalIDNumber:
 *                 type: string
 *     responses:
 *       '200':
 *         description: Successfully registered the applicant.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.post('/register', async (req, res) => {
  const {
    email,
    password,
    firstName,
    middleName,
    lastName,
    phoneNumber,
    nationalIDNumber,
  } = req.body;
  const type = 'Applicant';
  if (!email) {
    res.status(400).send('Email is required');
  } else if (!password) {
    res.status(400).send('Password is required');
  } else if (!firstName) {
    res.status(400).send('First name is required');
  } else if (!middleName) {
    res.status(400).send('Middle name is required');
  } else if (!lastName) {
    res.status(400).send('Last name is required');
  } else if (!phoneNumber) {
    res.status(400).send('Phone number is required');
  } else if (!nationalIDNumber) {
    res.status(400).send('National ID number is required');
  } else {
    await Applicant.register(
      email,
      password,
      type,
      firstName,
      middleName,
      lastName,
      phoneNumber,
      nationalIDNumber,
    )
      .then((jwt) => {
        if (jwt !== '') {
          res.status(200).send({
            auth: true,
            token: jwt,
            type,
            email,
          });
        } else {
          res.status(500).send('Internal Server Error');
        }
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
 * /applicant:
 *   get:
 *     summary: Get applicant details.
 *     tags: [Applicant]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       '200':
 *         description: Applicant details retrieved successfully.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.get('/', requireAuth, async (req, res) => {
  const { email } = res.locals;
  await Applicant.getApplicantByEmail(email as string)
    .then((data) => {
      res.status(200).send(data);
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    });
});

// Route to handle uploading profile picture
/**
 * @swagger
 * /applicant/profilePicture:
 *   post:
 *     summary: Upload profile picture for authenticated applicant.
 *     tags: [Applicant]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               profilePicture:
 *                 type: string
 *                 format: binary
 *     responses:
 *       '200':
 *         description: Profile picture uploaded successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.post(
  '/profilePicture',
  requireAuth, // Middleware to require authentication
  upload.single('profilePicture'), // Middleware to handle file upload
  async (req, res) => {
    if (req.file) {
      const photo = req.file.buffer;
      const base64String = photo.toString('base64');
      // Call controller function to update profile picture
      await Applicant.updateProfilePicture(res.locals.email, base64String)
        .then(() => {
          res.status(200).send('Profile picture uploaded successfully.');
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

// Route to handle uploading national ID photo face
/**
 * @swagger
 * /applicant/nationalIDPhotoFace:
 *   post:
 *     summary: Upload national ID photo face for authenticated applicant.
 *     tags: [Applicant]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               nationalIDPhotoFace:
 *                 type: string
 *                 format: binary
 *     responses:
 *       '200':
 *         description: National ID photo face uploaded successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.post(
  '/nationalIDPhotoFace',
  requireAuth, // Middleware to require authentication
  upload.single('nationalIDPhotoFace'), // Middleware to handle file upload
  async (req, res) => {
    if (req.file) {
      const photo = req.file.buffer;
      const base64String = photo.toString('base64');
      // Call controller function to update national ID photo face
      await Applicant.updateNationalIDPhotoFace(res.locals.email, base64String)
        .then(() => {
          res.status(200).send('National ID photo face uploaded successfully.');
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

// Route to handle uploading national ID photo back
/**
 * @swagger
 * /applicant/nationalIDPhotoBack:
 *   post:
 *     summary: Upload national ID photo back for authenticated applicant.
 *     tags: [Applicant]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               nationalIDPhotoBack:
 *                 type: string
 *                 format: binary
 *     responses:
 *       '200':
 *         description: National ID photo back uploaded successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.post(
  '/nationalIDPhotoBack',
  requireAuth, // Middleware to require authentication
  upload.single('nationalIDPhotoBack'), // Middleware to handle file upload
  async (req, res) => {
    if (req.file) {
      const photo = req.file.buffer;
      const base64String = photo.toString('base64');
      // Call controller function to update national ID photo back
      await Applicant.updateNationalIDPhotoBack(res.locals.email, base64String)
        .then(() => {
          res.status(200).send('National ID photo back uploaded successfully.');
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
 * /applicant/updateSkills:
 *   post:
 *     summary: Update applicant skills
 *     description: This can only be done by the logged in applicant.
 *     tags: [Applicant]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               skills:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       '200':
 *         description: Skills updated successfully.
 *       '400':
 *         description: Bad request.
 *       '500':
 *         description: Server error.
 */
applicantRoutes.post('/updateSkills', requireAuth, async (req, res) => {
  const { email } = res.locals;
  const { skills } = req.body;
  await Applicant.updateApplicantSkills(email, skills)
    .then(() => {
      res.status(200).send('Skills updated successfully.');
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    });
});

// Error handling middleware
applicantRoutes.use(
  (
    err: Error,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction,
  ): void => {
    if (err instanceof multer.MulterError) {
      // Handle Multer errors
      res.status(400).send(`Multer error: ${err.message}`);
    } else {
      // Handle other errors
      res.status(500).send(`Server error: ${err.message}`);
    }
  },
);

export default applicantRoutes;

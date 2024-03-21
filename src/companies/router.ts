import express from 'express';
import multer from 'multer';
import * as Company from './controller';
import { CodedError } from '../util/error';
import { requireAuth } from '../util/authentication';

const companyRoutes = express.Router();

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
 *   name: Company
 *   description: API endpoints for managing companies
 */

/**
 * @swagger
 * /company/register:
 *   post:
 *     summary: Register a new company.
 *     tags: [Company]
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
 *               name:
 *                 type: string
 *               description:
 *                 type: string
 *               address:
 *                 type: string
 *     responses:
 *       '200':
 *         description: Successfully registered the company.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */

companyRoutes.post('/register', async (req, res) => {
  const {
    email, password, name, description, address,
  } = req.body;
  const type = 'Company';
  if (!email) {
    res.status(400).send('Email is required');
  } else if (!password) {
    res.status(400).send('Password is required');
  } else if (!name) {
    res.status(400).send('Name is required');
  } else if (!description) {
    res.status(400).send('Description is required');
  } else if (!address) {
    res.status(400).send('Address is required');
  } else {
    await Company.register(email, password, type, name, description, address)
      .then((jwt) => {
        if (jwt !== '') {
          res
            .status(200)
            .send({
              auth: true, token: jwt, type, email,
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
 * /company:
 *   get:
 *     summary: Get company details.
 *     tags: [Company]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       '200':
 *         description: Company details retrieved successfully.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */

companyRoutes.get('/', requireAuth, async (req, res) => {
  const { email } = res.locals;
  await Company.getCompanyByEmail(email as string)
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

// Route to handle uploading logo
/**
 * @swagger
 * /company/logo:
 *   post:
 *     summary: Upload logo for authenticated company.
 *     tags: [Company]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               logo:
 *                 type: string
 *                 format: binary
 *     responses:
 *       '200':
 *         description: Logo uploaded successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
companyRoutes.post(
  '/logo',
  requireAuth, // Middleware to require authentication
  upload.single('logo'), // Middleware to handle file upload
  async (req, res) => {
    if (req.file) {
      const photo = req.file.buffer;
      const base64String = photo.toString('base64');
      // Call controller function to update logo
      await Company.updateLogo(res.locals.email, base64String)
        .then(() => {
          res.status(200).send('Logo uploaded successfully.');
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

export default companyRoutes;

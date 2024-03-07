import express from 'express';
import * as Applicant from './controller';
import { CodedError } from '../util/error';

const applicantRoutes = express.Router();

/**
 * @swagger
 * /applicant/register:
 *   post:
 *     summary: Register a new applicant.
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
          res.status(200).send({ auth: true, token: jwt, type });
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
 *     summary: Get applicant details by email.
 *     parameters:
 *       - in: query
 *         name: email
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       '200':
 *         description: Applicant details retrieved successfully.
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error.
 */
applicantRoutes.get('/', async (req, res) => {
  const { email } = req.query;
  if (!email) {
    res.status(400).send('email is required');
  } else {
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
  }
});

export default applicantRoutes;

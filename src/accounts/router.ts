import express from 'express';
import * as Account from './controller';
import { CodedError } from '../util/error';

const accountRoutes = express.Router();

/**
 * @swagger
 *   components:
 *      securitySchemes:
 *          bearerAuth:
 *              type: http
 *              scheme: bearer
 *              bearerFormat: JWT
 */

/**
 * @swagger
 * /account/logIn:
 *   post:
 *     summary: Log in to the system
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
 *     responses:
 *       200:
 *         description: Logged in successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 auth:
 *                   type: boolean
 *                   example: true
 *                 token:
 *                   type: string
 *                   example: "JWT token"
 *                 type:
 *                   type: string
 *                   example: "user"
 *       400:
 *         description: Bad request, email or password is missing
 *       500:
 *         description: Internal server error
 */
accountRoutes.post('/logIn', async (req, res) => {
  const { email, password } = req.body;
  if (!email) {
    res.status(400).send('email is required');
  }
  if (!password) {
    res.status(400).send('Password is required');
  } else {
    await Account.signIn(email, password)
      .then((result) => {
        res.status(200).send({
          auth: true,
          token: result.jwt,
          type: result.type,
          email,
        });
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
 * /account/available:
 *   get:
 *     summary: Check if an email is available
 *     parameters:
 *       - in: query
 *         name: email
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success, returns availability status
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 available:
 *                   type: boolean
 *                   example: true
 *       400:
 *         description: Bad request, email parameter is missing
 *       500:
 *         description: Internal server error
 */
accountRoutes.get('/available', async (req, res) => {
  const { email } = req.query;
  if (!email) {
    res.status(400).send('email is required');
  } else {
    await Account.isEmailAvailable(email as string)
      .then((availability) => {
        res.status(200).send({ available: availability });
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

export default accountRoutes;

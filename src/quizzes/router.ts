import express from 'express';
import * as Job from './controller';
import { requireAuth, requireCompany } from '../util/authentication';
import { CodedError } from '../util/error';

const quizRoutes = express.Router();

/**
 * @swagger
 * tags:
 *   name: Quiz
 *   description: API endpoints for managing quizzes
 */

/**
 * @swagger
 * /quiz/addQuiz:
 *   post:
 *     summary: Add a new quiz.
 *     tags: [Quiz]
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
 *                     text:
 *                       type: string
 *                     answers:
 *                       type: array
 *                       items:
 *                         type: string
 *                     correctAnswer:
 *                       type: string
 *                     score:
 *                       type: number
 *     responses:
 *       '200':
 *         description: Quiz added successfully
 *       '400':
 *         description: Bad request. Missing or invalid parameters.
 *       '401':
 *         description: Unauthorized. Invalid credentials.
 *       '500':
 *         description: Internal server error
 */

// Route to add a new quiz
quizRoutes.post('/addQuiz', requireAuth, requireCompany, (req, res) => {
  const companyEmail = res.locals.email;
  const { jobID, questions } = req.body;

  // Validate jobID and questions in request body
  if (!jobID) {
    return res.status(400).send('jobID is required');
  }
  if (!questions) {
    return res.status(400).send('questions are required');
  }

  // Add the quiz
  Job.addQuiz(jobID, questions, companyEmail)
    .then((quizID) => res.status(200).send(quizID))
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        console.error(err); // Log the error for debugging purposes
        res.status(500).send('Internal server error');
      }
    });
});

/**
 * @swagger
 * /quiz/{quizId}:
 *   get:
 *     summary: Get a quiz by its ID.
 *     tags: [Quiz]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: quizId
 *         schema:
 *           type: string
 *         required: true
 *         description: The ID of the quiz to retrieve.
 *     responses:
 *       '200':
 *         description: Quiz retrieved successfully
 *       '404':
 *         description: Quiz not found
 *       '500':
 *         description: Internal server error
 */

// Route to get a quiz by its ID
quizRoutes.get('/:quizId', requireAuth, requireCompany, (req, res) => {
  const quizId = req.params.quizId;
  const companyEmail = res.locals.email;

  // Fetch the quiz by ID
  Job.getQuizById(quizId, companyEmail)
    .then((quiz) => {
      if (!quiz) {
        return res.status(404).send('Quiz not found');
      }
      res.status(200).send(quiz);
    })
    .catch((err) => {
      console.error(err); // Log the error for debugging purposes
      res.status(500).send('Internal server error');
    });
});

/**
 * @swagger
 * /quiz/getByJobID/{jobId}:
 *   get:
 *     summary: Get quizzes by job ID.
 *     tags: [Quiz]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: jobId
 *         schema:
 *           type: string
 *         required: true
 *         description: The ID of the job to retrieve quizzes for.
 *     responses:
 *       '200':
 *         description: Quizzes retrieved successfully
 *       '404':
 *         description: Quiz not found
 *       '500':
 *         description: Internal server error
 */

// Route to get quizzes by job ID
quizRoutes.get(
  '/getByJobID/:jobId',
  requireAuth,
  requireCompany,
  (req, res) => {
    const jobId = req.params.jobId;
    const companyEmail = res.locals.email;

    // Fetch the quizzes by job ID
    Job.getQuizByJobID(jobId, companyEmail)
      .then((quiz) => {
        if (!quiz) {
          return res.status(404).send('Quiz not found');
        }
        res.status(200).send(quiz);
      })
      .catch((err) => {
        console.error(err); // Log the error for debugging purposes
        res.status(500).send('Internal server error');
      });
  },
);

export default quizRoutes;

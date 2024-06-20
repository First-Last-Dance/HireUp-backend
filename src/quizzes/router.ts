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
 *                 description: The ID of the job associated with the quiz
 *               questions:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     text:
 *                       type: string
 *                       description: The text of the question
 *                     answers:
 *                       type: array
 *                       items:
 *                         type: string
 *                         description: A possible answer to the question
 *                     correctAnswer:
 *                       type: string
 *                       description: The correct answer to the question
 *                     score:
 *                       type: number
 *                       description: The score of the question
 *                 description: An array of questions for the quiz
 *               passRatio:
 *                 type: number
 *                 description: The passing ratio for the quiz
 *               quizDurationInMinutes:
 *                 type: number
 *                 description: The duration of the quiz in minutes
 *     responses:
 *       '200':
 *         description: Quiz added successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: string
 *               description: The ID of the added quiz
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
  const { jobID, questions, passRatio, quizDurationInMinutes } = req.body;

  // Validate jobID and questions in request body
  if (!jobID) {
    return res.status(400).send('jobID is required');
  }
  if (!questions) {
    return res.status(400).send('questions are required');
  }

  if (!passRatio) {
    return res.status(400).send('passRatio is required');
  }

  if (!quizDurationInMinutes) {
    return res.status(400).send('quizDurationInMinutes is required');
  }
  // Add the quiz
  Job.addQuiz(jobID, questions, passRatio, quizDurationInMinutes, companyEmail)
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
 * /quiz/getByJobID/{jobID}:
 *   get:
 *     summary: Get quizzes by job ID.
 *     tags: [Quiz]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: jobID
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
  '/getByJobID/:jobID',
  requireAuth,
  requireCompany,
  (req, res) => {
    const jobID = req.params.jobID;
    const companyEmail = res.locals.email;

    // Fetch the quizzes by job ID
    Job.getQuizByJobID(jobID, companyEmail)
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

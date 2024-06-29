import express from 'express';
import * as Topic from './controller';
import {
  requireAdmin,
  requireAuth,
  requireCompany,
} from '../util/authentication';
import { CodedError } from '../util/error';
import { TopicData } from './model';

const topicRoutes = express.Router();

/**
 * @swagger
 * /topic/names:
 *   get:
 *     summary: Get all topics' names
 *     tags: [Topic]
 *     responses:
 *       200:
 *         description: List of topic names
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: string
 *       500:
 *         description: Internal Server Error
 */
topicRoutes.get('/names', async (req, res) => {
  try {
    const topicsNames = await Topic.getTopicsNames();
    res.status(200).json(topicsNames);
  } catch (error) {
    if (error instanceof CodedError) {
      res.status(error.code).send(error.message);
    } else {
      res.status(500).send('Internal Server Error');
    }
  }
});

/**
 * @swagger
 * /topic:
 *   get:
 *     summary: Get all given topics
 *     tags: [Topic]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: body
 *         name: topics
 *         schema:
 *           type: array
 *           items:
 *             type: string
 *         required: true
 *         description: List of topic names
 *     responses:
 *       200:
 *         description: List of topics data
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/TopicData'
 *       400:
 *         description: topics parameter is required
 *       500:
 *         description: Internal Server Error
 */
topicRoutes.get('/', requireAuth, requireCompany, async (req, res) => {
  try {
    const topics = req.body.topics;
    if (!topics || topics.length === 0) {
      res.status(400).send('topics parameter is required');
    }
    const topicsData = await Topic.getTopics(topics);
    res.status(200).json(topicsData);
  } catch (error) {
    if (error instanceof CodedError) {
      res.status(error.code).send(error.message);
    } else {
      res.status(500).send('Internal Server Error');
    }
  }
});

/**
 * @swagger
 * /topic:
 *   post:
 *     summary: Add a new topic
 *     tags: [Topic]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - questions
 *             properties:
 *               name:
 *                 type: string
 *               questions:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       201:
 *         description: The created topic
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/TopicData'
 *       400:
 *         description: name and questions parameters are required
 *       500:
 *         description: Internal Server Error
 */
topicRoutes.post('/', requireAuth, requireAdmin, async (req, res) => {
  try {
    const topicName = req.body.name;
    const questions = req.body.questions;
    if (!topicName || !questions) {
      res.status(400).send('name and questions parameters are required');
    }
    const newTopic = await Topic.addTopic(topicName, questions);
    res.status(201).json(newTopic);
  } catch (error) {
    if (error instanceof CodedError) {
      res.status(error.code).send(error.message);
    } else {
      res.status(500).send('Internal Server Error');
    }
  }
});

export default topicRoutes;

import express from 'express';
import * as Skill from './controller';
import { CodedError } from '../util/error';
import { requireAdmin, requireAuth } from '../util/authentication';

const skillRoutes = express.Router();

/**
 * @swagger
 * tags:
 *   name: Skill
 *   description: Skill management
 */

/**
 * @swagger
 * /skill:
 *   get:
 *     summary: Get all skills
 *     tags: [Skill]
 *     responses:
 *       200:
 *         description: Success
 *       500:
 *         description: Internal server error
 */
skillRoutes.get('/', async (req, res) => {
  await Skill.getSkills()
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

/**
 * @swagger
 * /skill:
 *   post:
 *     summary: Add skills (Admin only)
 *     tags: [Skill]
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
 *       201:
 *         description: Skills added successfully
 *       400:
 *         description: Bad request
 *       401:
 *         description: Unauthorized
 *       500:
 *         description: Internal server error
 */
skillRoutes.post('/', requireAuth, requireAdmin, async (req, res) => {
  await Skill.addSkills(req.body.skills)
    .then(() => {
      res.status(201).send('Skills added successfully');
    })
    .catch((err) => {
      if (err instanceof CodedError) {
        res.status(err.code).send(err.message);
      } else {
        res.status(500).send(err);
      }
    });
});

export default skillRoutes;

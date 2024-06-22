import { Request, Response } from 'express';
import { NextFunction } from 'connect';
import * as jwt from 'jsonwebtoken';
import * as dotenv from 'dotenv';
import {
  isAccountAdmin,
  isAccountApplicant,
  isAccountCompany,
} from '../accounts/service';

interface JwtPayload {
  email: string;
  // admin: boolean;
  // verified: boolean;
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.headers || !req.headers.authorization) {
    return res.status(401).send('No authorization headers.');
  }

  const tokenBearer = req.headers.authorization.split(' ');
  if (tokenBearer.length !== 2) {
    return res.status(401).send('Malformed token.');
  }

  const token = tokenBearer[1];
  dotenv.config();
  return jwt.verify(
    token,
    process.env.JWT_SECRET as unknown as jwt.Secret,
    (err, decoded) => {
      if (err) {
        return res
          .status(500)
          .send({ auth: false, message: 'Failed to authenticate.' });
      }
      res.locals.email = (decoded as JwtPayload).email;
      return next();
    },
  );
}

export function requireCompany(
  req: Request,
  res: Response,
  next: NextFunction,
) {
  isAccountCompany(res.locals.email)
    .then((company) => {
      if (company) {
        return next();
      }
      return res.status(401).send('signed in user must be Company');
    })
    .catch((err) => res.status(500).send(err));
}

export function requireApplicant(
  req: Request,
  res: Response,
  next: NextFunction,
) {
  isAccountApplicant(res.locals.email)
    .then((applicant) => {
      if (applicant) {
        return next();
      }
      return res.status(401).send('signed in user must be Company');
    })
    .catch((err) => res.status(500).send(err));
}
export function requireAdmin(req: Request, res: Response, next: NextFunction) {
  isAccountAdmin(res.locals.email)
    .then((admin) => {
      if (admin) {
        return next();
      }
      return res.status(401).send('signed in user must be admin');
    })
    .catch((err) => res.status(500).send(err));
}

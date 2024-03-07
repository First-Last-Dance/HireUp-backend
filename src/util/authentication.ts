import { Request, Response } from 'express';
import { NextFunction } from 'connect';
import * as jwt from 'jsonwebtoken';
import * as dotenv from 'dotenv';
import { isAccountAdmin } from '../accounts/service';

interface JwtPayload {
  userName: string;
  admin: boolean;
  authorized: boolean;
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
      res.locals.userName = (decoded as JwtPayload).userName;
      return next();
    },
  );
}

// export function requireManager(
//   req: Request,
//   res: Response,
//   next: NextFunction,
// ) {
//   isManager(res.locals.userName)
//     .then((manager) => {
//       if (manager) {
//         return next();
//       }
//       return res.status(401).send('signed in user must be manager');
//     })
//     .catch((err) => res.status(500).send(err));
// }
export function requireAdmin(req: Request, res: Response, next: NextFunction) {
  isAccountAdmin(res.locals.userName)
    .then((admin) => {
      if (admin) {
        return next();
      }
      return res.status(401).send('signed in user must be admin');
    })
    .catch((err) => res.status(500).send(err));
}

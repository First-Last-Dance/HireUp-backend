import express from 'express';
import accountRoutes from './accounts/router';
import applicantRoutes from './applicants/router';

const routes = express.Router();

routes.get('/', (req, res) => {
  res.send('Hello World! from route');
});
routes.use('/account', accountRoutes);
routes.use('/applicant', applicantRoutes);

export default routes;

import express from 'express';
import accountRoutes from './accounts/router';
import applicantRoutes from './applicants/router';
import companyRoutes from './companies/router';

const routes = express.Router();

routes.get('/', (req, res) => {
  res.send('Hello World! from route');
});
routes.use('/account', accountRoutes);
routes.use('/applicant', applicantRoutes);
routes.use('/company', companyRoutes);

export default routes;

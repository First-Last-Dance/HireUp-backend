import express from 'express';
import accountRoutes from './accounts/router';
import applicantRoutes from './applicants/router';
import companyRoutes from './companies/router';
import skillRoutes from './skills/router';
import jobRoutes from './jobs/router';

const routes = express.Router();

routes.get('/', (req, res) => {
  res.send('Hello World! from route');
});
routes.use('/account', accountRoutes);
routes.use('/applicant', applicantRoutes);
routes.use('/company', companyRoutes);
routes.use('/skill', skillRoutes);
routes.use('/job', jobRoutes);

export default routes;

import express from 'express';
import accountRoutes from './accounts/router';
import applicantRoutes from './applicants/router';
import multer from 'multer';

const routes = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

routes.get('/', (req, res) => {
  res.send('Hello World! from route');
});
routes.post('/', upload.single('test'), (req, res) => {
  if (req.file) {
    const photo = req.file.buffer;
    const base64String = photo.toString('base64');
    console.log(photo);
    console.log(base64String);
    // Create an HTML img tag with src attribute set to the Base64 string
    const imgTag = `<img src="data:image/jpeg;base64,${base64String}" alt="Uploaded Photo">`;

    // Send the img tag as a response
    res.send(`File uploaded successfully. ${imgTag}`);
  }
});
routes.use('/account', accountRoutes);
routes.use('/applicant', applicantRoutes);

export default routes;

import * as dotenv from 'dotenv';
import express from 'express';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUI from 'swagger-ui-express';
import mongoose from 'mongoose';
import cors from 'cors';
import routes from './router';
import bodyParser from 'body-parser';

// Config the .env file
dotenv.config();

// Create the API
const app = express();
const port = process.env.PORT || 8080;

const corsOptions = {
  origin: '*',
  credentials: true, // access-control-allow-credentials:true
  optionSuccessStatus: 200,
};
app.use(cors(corsOptions));

// Swagger Docs.
const options = {
  failOnErrors: true, // Whether or not to throw when parsing errors. Defaults to false.
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Hello World',
      version: '1.0.0',
    },
  },
  apis: ['./src/**/router.ts'],
};

const openapiSpecification = swaggerJsdoc(options);

app.use('/docs', swaggerUI.serve, swaggerUI.setup(openapiSpecification));

// Add the json parser
app.use(express.json());

// Set the main router
app.use('/', routes);

// Increase the body size limit
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));

// Connect to DB

mongoose
  .connect(
    `${
      `mongodb://${process.env.DB_Host as string}` || 'mongodb://0.0.0.0:27017'
    }/HireUP`,
    { dbName: 'HireUP' },
  )
  .then(() => {
    console.log('DB connected');
    // Start the API
    app.listen(port, () => {
      console.log(`Backend server is listening on port ${port}....`);
      console.log('press CTRL+C to stop server');
    });
  })
  .catch((err) => console.log(err));

// app.listen(port, () => {
//   console.log(`Backend server is listening on port ${port}....`);
//   console.log('press CTRL+C to stop server');
// });

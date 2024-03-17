import mongoose from 'mongoose';
import * as dotenv from 'dotenv';
import Account from '../accounts/model';
import Applicant from '../applicants/model';
import Company from '../companies/model';
import Skill from '../skills/model';
import { generatePassword } from '../accounts/controller';

// Config the .env file
dotenv.config();

mongoose
  .connect(
    `${`mongodb://${process.env.DB_Host as string}` || '0.0.0.0:27017'}/HireUP`,
    { dbName: 'HireUP' },
  )
  .then(() => {})
  .catch((err) => console.log(err));

async function addAdmin() {
  const hashedPassword = await generatePassword('password');
  const adminData = {
    email: 'email@example.com',
    password: hashedPassword,
    type: 'applicant',
    verified: true,
    admin: true,
  };
  const applicantData = {
    email: 'email@example.com',
    firstName: 'Admin',
    middleName: 'Abu Admin',
    lastName: 'Abu Abu Admin',
    phoneNumber: '1234567890',
    nationalIDNumber: '1234567890',
    profilePhoto: 'unavailable',
    nationalIDPhotoFace: 'unavailable',
    nationalIDPhotoBack: 'unavailable',
  };
  Account.find({ admin: true })
    .exec()
    .then((result) => {
      if (result.length === 0) {
        const admin = new Account(adminData);
        admin.save().then(() => {
          const applicant = new Applicant(applicantData);
          applicant
            .save()
            .then(() => {
              mongoose.disconnect();
              console.log(
                'Admin created, email: email@example.com, password: password',
              );
            })
            .catch((err) => {
              throw err;
            });
        });
      } else {
        mongoose.disconnect();
        console.log(
          'Admin available, email: email@example.com, password: password',
        );
      }
    });
}
addAdmin();

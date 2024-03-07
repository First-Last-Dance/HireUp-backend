// import mongoose from 'mongoose';
// import * as dotenv from 'dotenv';
// import User from './users/model';
// import { generatePassword } from './users/controller';

// // Config the .env file
// dotenv.config();

// mongoose
//   .connect(
//     `${
//       `mongodb://${process.env.DB_Host as string}` || '0.0.0.0:27017'
//     }/Tazkarti`,
//     { dbName: 'Tazkarti' },
//   )
//   .then(() => {})
//   .catch((err) => console.log(err));

// async function addAdmin() {
//   const hashedPassword = await generatePassword('password');
//   const adminData = {
//     userName: 'Admin',
//     password: hashedPassword,
//     firstName: 'Admin',
//     lastName: 'Abu Admin',
//     birthDate: '2001-01-01',
//     gender: 'male',
//     city: 'Cairo',
//     email: 'email@example.com',
//     role: 'manager',
//     admin: true,
//     authorized: true,
//     address: 'unavailable',
//   };
//   User.find({ admin: true })
//     .exec()
//     .then((result) => {
//       if (result.length === 0) {
//         const admin = new User(adminData);
//         admin.save().then(() => {
//           mongoose.disconnect();
//           console.log('Admin created, userName: Admin, password: password');
//         });
//       } else {
//         mongoose.disconnect();
//         console.log('Admin available, userName: Admin, password: password');
//       }
//     });
// }
// addAdmin();

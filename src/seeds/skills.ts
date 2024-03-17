import mongoose from 'mongoose';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import Skill from '../skills/model';

// Config the .env file
dotenv.config();

mongoose
  .connect(
    `${`mongodb://${process.env.DB_Host as string}` || '0.0.0.0:27017'}/HireUP`,
    { dbName: 'HireUP' },
  )
  .then(() => {})
  .catch((err) => console.log(err));

async function addSkills() {
  try {
    // Read skill names from a text file
    const skillsFileContent = fs.readFileSync('skills.txt', 'utf-8');
    const skillsNames: string[] = skillsFileContent
      .split('\n')
      .map((skill) => skill.trim());

    const skills: { name: string }[] = [];

    for (const skillName of skillsNames) {
      const exist = await Skill.findOne({ name: skillName });
      if (!exist) {
        const skillData = {
          name: skillName,
        };
        const newSkill = new Skill(skillData);
        skills.push(newSkill);
      }
    }

    if (skills.length > 0) {
      await Skill.insertMany(skills);
      console.log('Skills added');
    } else {
      console.log('No new skills to add');
    }

    mongoose.connection.close();
  } catch (err) {
    console.error('Error adding skills:', err);
    mongoose.connection.close();
  }
}

addSkills();

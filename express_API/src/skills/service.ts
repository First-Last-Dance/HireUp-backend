import SkillModel, { ISkill } from './model';

/**
 * Retrieves all skills from the database.
 * @returns A list of all skills.
 */
export async function getAllSkills(): Promise<ISkill[]> {
  return SkillModel.find().catch((error) => {
    throw error;
  });
}

/**
 * Adds a new skill to the database.
 * @param skillName The name of the skill to add.
 * @returns The newly created skill document.
 */
export async function addSkill(skillName: string): Promise<ISkill> {
  const newSkill = new SkillModel({ name: skillName });
  return newSkill.save().catch((error) => {
    throw error;
  });
}

/**
 * Deletes a skill from the database by its name.
 * @param skillName The name of the skill to delete.
 * @returns True if the skill is deleted successfully, otherwise false.
 */
export async function deleteSkillByName(skillName: string): Promise<boolean> {
  return SkillModel.deleteOne({ name: skillName })
    .then((result) => result.deletedCount !== 0)
    .catch((error) => {
      throw error;
    });
}

/**
 * Retrieves a skill from the database by its name.
 * @param skillName The name of the skill to retrieve.
 * @returns The skill document if found, otherwise null.
 */
export async function getSkillByName(
  skillName: string,
): Promise<ISkill | null> {
  return SkillModel.findOne({ name: skillName }).catch((error) => {
    throw error;
  });
}

/**
 * Updates a skill's name in the database.
 * @param oldSkillName The current name of the skill to update.
 * @param newSkillName The new name for the skill.
 * @returns The updated skill document.
 */
export async function updateSkillName(
  oldSkillName: string,
  newSkillName: string,
): Promise<ISkill | null> {
  return SkillModel.findOneAndUpdate(
    { name: oldSkillName },
    { name: newSkillName },
    { new: true }, // Return the updated document
  ).catch((error) => {
    throw error;
  });
}

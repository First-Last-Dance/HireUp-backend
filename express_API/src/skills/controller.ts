import * as Skill from './service';

export async function addSkills(skills: string[]): Promise<void> {
  skills.forEach(async (skill) => {
    await Skill.getSkillByName(skill)
      .then(async (res) => {
        if (res === null) {
          await Skill.addSkill(skill).catch((err) => {
            throw err;
          });
        }
      })
      .catch(async (err) => {
        throw err;
      });
  });
}
export async function getSkills(): Promise<string[]> {
  const skills = await Skill.getAllSkills().catch((err) => {
    throw err;
  });
  const skillsArr: string[] = [];
  skills.forEach((skill) => {
    skillsArr.push(skill.name);
  });
  return skillsArr;
}

export async function getSkillsIDs(skillNames: string[]): Promise<string[]> {
  const skillsIDs: string[] = [];
  const skills = await Skill.getAllSkills().catch((err) => {
    throw err;
  });
  skills.forEach((skill) => {
    if (skillNames.includes(skill.name)) {
      skillsIDs.push(skill.id);
    }
  });
  return skillsIDs;
}

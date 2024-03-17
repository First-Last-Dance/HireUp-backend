import mongoose, { Schema, Document } from 'mongoose';

export interface ISkill extends Document {
  name: string;
}

const SkillSchema: Schema = new Schema({
  name: { type: String, required: true, unique: true },
});

export default mongoose.model<ISkill>('Skill', SkillSchema);

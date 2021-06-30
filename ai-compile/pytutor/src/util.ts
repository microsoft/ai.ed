export const BEGINNER = 1;
export const EXPERT = 2;
export const MODE_MEMENTO_NAME = "Python_Tutor_Mode";
export const EXTENSION_NAME = "Python Tutor";
export const BEGINNER_ICON = '👩‍🎓';
export const EXPERT_ICON = '🚀';

export enum Modes{
  Beginner = BEGINNER,
  Expert = EXPERT
}

export function getModeIcon(mode: number){
    if (mode === Modes.Beginner){
      return BEGINNER_ICON;
    }
    else{
      return EXPERT_ICON
    }
}
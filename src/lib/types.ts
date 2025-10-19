export type WorkoutLite = {
    id: string;
    name: string;
    description?: string | null;
  };
  
  export type ClimbInput = {
    name: string;
    grade: number;
    flagBoulder?: boolean;
    flagSport?: boolean;
    attempts?: number;
  };
  
  export type TrainingSessionInput = {
    name: string;
    scheduledDate: string; // ISO string
    description?: string;
    workoutId: string;
    climbs: ClimbInput[];
  };
  
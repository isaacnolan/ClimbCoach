export interface ClimbingPerformance {
  grade: string;
  style: 'boulder' | 'sport' | 'trad';
  completion: 'flash' | 'onsight' | 'redpoint' | 'failed';
  attempts: number;
  notes?: string;
}

export interface TrainingGoal {
  id: string;
  description: string;
  targetGrade: string;
  timeframe: string;
  priority: 'low' | 'medium' | 'high';
}

export interface TechniqueAnalysis {
  strength: string[];
  weakness: string[];
  recommendations: string[];
}

export interface WorkoutRecommendation {
  type: 'strength' | 'endurance' | 'technique' | 'power';
  exercises: {
    name: string;
    sets: number;
    reps?: number;
    duration?: number;
    rest?: number;
    notes?: string;
  }[];
  rationale: string;
}

export interface ChainOfThought {
  observations: string[];
  analysis: string[];
  conclusions: string[];
  recommendations: string[];
}

export interface ClimbingCoachState {
  userId: string;
  currentGoals: TrainingGoal[];
  performanceHistory: ClimbingPerformance[];
  techniqueAnalysis: TechniqueAnalysis;
  workoutHistory: WorkoutRecommendation[];
  chainOfThought: ChainOfThought;
} 
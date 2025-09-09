import type { 
  ClimbingPerformance, 
  TrainingGoal, 
  TechniqueAnalysis, 
  WorkoutRecommendation,
  ChainOfThought,
  ClimbingCoachState 
} from './types';

export class ClimbingCoach {
  private state: ClimbingCoachState;

  constructor(userId: string) {
    this.state = {
      userId,
      currentGoals: [],
      performanceHistory: [],
      techniqueAnalysis: {
        strength: [],
        weakness: [],
        recommendations: []
      },
      workoutHistory: [],
      chainOfThought: {
        observations: [],
        analysis: [],
        conclusions: [],
        recommendations: []
      }
    };
  }

  async analyzePerformance(performance: ClimbingPerformance): Promise<ChainOfThought> {
    // Reset chain of thought
    this.state.chainOfThought = {
      observations: [],
      analysis: [],
      conclusions: [],
      recommendations: []
    };

    // Add performance to history
    this.state.performanceHistory.push(performance);

    // Generate observations
    this.state.chainOfThought.observations = this.generateObservations(performance);

    // Analyze performance
    this.state.chainOfThought.analysis = this.analyzePerformancePatterns();

    // Draw conclusions
    this.state.chainOfThought.conclusions = this.generateConclusions();

    // Generate recommendations
    this.state.chainOfThought.recommendations = await this.generateRecommendations();

    return this.state.chainOfThought;
  }

  private generateObservations(performance: ClimbingPerformance): string[] {
    const observations: string[] = [];
    
    observations.push(`Completed ${performance.grade} ${performance.style} climb`);
    observations.push(`Completion type: ${performance.completion}`);
    observations.push(`Number of attempts: ${performance.attempts}`);
    
    if (performance.notes) {
      observations.push(`Additional notes: ${performance.notes}`);
    }

    return observations;
  }

  private analyzePerformancePatterns(): string[] {
    const analysis: string[] = [];
    const recentPerformances = this.state.performanceHistory.slice(-5);

    // Analyze grade progression
    const grades = recentPerformances.map(p => this.gradeToNumber(p.grade));
    if (grades.length > 1) {
      const progression = grades[grades.length - 1] - grades[0];
      analysis.push(`Grade progression: ${progression > 0 ? 'improving' : 'stable'}`);
    }

    // Analyze completion patterns
    const completionTypes = recentPerformances.map(p => p.completion);
    const flashCount = completionTypes.filter(c => c === 'flash').length;
    if (flashCount > 0) {
      analysis.push(`Strong performance on first attempts (${flashCount} flashes)`);
    }

    return analysis;
  }

  private generateConclusions(): string[] {
    const conclusions: string[] = [];
    const recentPerformances = this.state.performanceHistory.slice(-5);

    // Analyze strengths
    const successfulClimbs = recentPerformances.filter(p => p.completion !== 'failed');
    if (successfulClimbs.length > 0) {
      const strongestStyle = this.identifyStrongestStyle(successfulClimbs);
      conclusions.push(`Strongest in ${strongestStyle} climbing`);
    }

    // Identify areas for improvement
    const failedClimbs = recentPerformances.filter(p => p.completion === 'failed');
    if (failedClimbs.length > 0) {
      conclusions.push(`Need to focus on ${this.identifyWeakness(failedClimbs)}`);
    }

    return conclusions;
  }

  private async generateRecommendations(): Promise<string[]> {
    const recommendations: string[] = [];
    const recentPerformances = this.state.performanceHistory.slice(-5);

    // Generate training recommendations based on performance
    if (recentPerformances.length > 0) {
      const latestPerformance = recentPerformances[recentPerformances.length - 1];
      
      if (latestPerformance.completion === 'failed') {
        recommendations.push('Focus on technique drills for the next session');
        recommendations.push('Consider working on specific moves that caused difficulty');
      } else {
        recommendations.push('Continue with current training program');
        recommendations.push('Gradually increase difficulty in next session');
      }
    }

    // Add specific workout recommendations
    const workoutRecommendation = await this.generateWorkoutRecommendation();
    recommendations.push(`Recommended workout type: ${workoutRecommendation.type}`);
    recommendations.push(`Workout focus: ${workoutRecommendation.rationale}`);

    return recommendations;
  }

  private async generateWorkoutRecommendation(): Promise<WorkoutRecommendation> {
    // This would be expanded with more sophisticated logic
    return {
      type: 'strength',
      exercises: [
        {
          name: 'Hangboard Repeaters',
          sets: 4,
          reps: 6,
          duration: 7,
          rest: 3,
          notes: 'Focus on maintaining good form'
        }
      ],
      rationale: 'Building finger strength for better grip endurance'
    };
  }

  private gradeToNumber(grade: string): number {
    // Convert climbing grades to numbers for comparison
    // This is a simplified version and would need to be expanded
    const match = grade.match(/V(\d+)/);
    if (match) {
      return parseInt(match[1]);
    }
    return 0;
  }

  private identifyStrongestStyle(performances: ClimbingPerformance[]): string {
    const styleCounts = performances.reduce((acc, p) => {
      acc[p.style] = (acc[p.style] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(styleCounts)
      .sort((a, b) => b[1] - a[1])[0][0];
  }

  private identifyWeakness(performances: ClimbingPerformance[]): string {
    // This would be expanded with more sophisticated analysis
    return 'power endurance';
  }
} 
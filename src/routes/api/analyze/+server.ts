import { json } from '@sveltejs/kit';
import { ClimbingCoach } from '$lib/ai/reasoning';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  try {
    const data = await request.json();
    
    // Create a new climbing coach instance
    const coach = new ClimbingCoach(data.userId);
    
    // Analyze the performance
    const analysis = await coach.analyzePerformance(data.performance);
    
    return json({
      success: true,
      analysis
    });
  } catch (error) {
    console.error('Error analyzing performance:', error);
    return json({
      success: false,
      error: 'Failed to analyze performance'
    }, { status: 500 });
  }
}; 
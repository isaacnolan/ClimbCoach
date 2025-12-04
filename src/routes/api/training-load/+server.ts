import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { listTrainingSessions } from '$lib/server/training';
import { computeSessionLoads, computeACWR } from '$lib/load';

export const GET: RequestHandler = async () => {
  try {
    // Get sessions from the last 180 days
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 180);
    
    const sessions = await listTrainingSessions({ 
      from, 
      to 
    });

    if (!sessions || sessions.length === 0) {
      return json({
        success: true,
        trainingLoad: null,
        message: 'No training sessions found'
      });
    }

    // Compute training load metrics
    const { sessions: sessionLoads, gMax } = computeSessionLoads(sessions);
    const acwr = computeACWR(
      sessionLoads.map(s => ({ scheduledDate: s.scheduledDate, load: s.load }))
    );

    // Get recent sessions (last 7 days)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const recentSessions = sessionLoads.filter(
      s => new Date(s.scheduledDate) >= sevenDaysAgo
    );

    return json({
      success: true,
      trainingLoad: {
        currentACWR: acwr.acwr,
        acuteLoad: acwr.ewma7,
        chronicLoad: acwr.ewma42,
        maxGrade: gMax,
        recentSessionCount: recentSessions.length,
        totalLoad: sessionLoads.reduce((sum, s) => sum + s.load, 0),
        averageSessionLoad: sessionLoads.length > 0 
          ? sessionLoads.reduce((sum, s) => sum + s.load, 0) / sessionLoads.length 
          : 0,
        recentSessions: recentSessions.map(s => ({
          date: s.scheduledDate,
          name: s.name,
          load: s.load
        }))
      }
    });
    
  } catch (error) {
    console.error('Error fetching training load:', error);
    return json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch training load'
    }, { status: 500 });
  }
};

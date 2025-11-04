import { json } from '@sveltejs/kit';
import { ClimbingCoach } from '$lib/ai/reasoning';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  try {
    const data = await request.json();
    
    const pythonResponse = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    const responseText = await pythonResponse.text();

    if (!pythonResponse.ok) {
      throw new Error(`Python backend error: ${responseText}`);
    }

    const pythonData = JSON.parse(responseText);
    
    return json({
      success: true,
      reply: pythonData.reply
    });
    
  } catch (error) {
    console.error('Error in analyze endpoint:', error);
    return json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to process request'
    }, { status: 500 });
  }
}
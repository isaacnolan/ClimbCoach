import { json } from '@sveltejs/kit';
import { ClimbingCoach } from '$lib/ai/reasoning';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  try {
    const data = await request.json();
    
    console.log('Forwarding request to Python backend:', data);
    
    // Forward to Python backend
    const pythonResponse = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    // Get the response text first for error handling
    const responseText = await pythonResponse.text();
    console.log('Python backend response:', responseText);

    if (!pythonResponse.ok) {
      console.error('Python backend error:', responseText);
      throw new Error(`Python backend error: ${responseText}`);
    }

    // Try to parse the response
    let pythonData;
    try {
      pythonData = JSON.parse(responseText);
    } catch (e) {
      console.error('Failed to parse Python response:', e);
      throw new Error('Invalid response from Python backend');
    }

    if (!pythonData.reply) {
      console.error('No reply in response:', pythonData);
      throw new Error('No reply found in Python response');
    }

    console.log('Successfully processed response:', pythonData);
    
    // Return the Python backend response directly
    return json({
      success: true,
      reply: pythonData.reply
    });
  } catch (error) {
    console.error('Error analyzing performance:', error);
    return json({
      success: false,
      error: 'Failed to analyze performance'
    }, { status: 500 });
  }
}; 
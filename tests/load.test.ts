import assert from 'assert';
import { climbLoad, sessionLoad, computeSessionLoads, computeACWR } from '../src/lib/load';

// Simple unit smoke tests for load utilities
async function run() {
  const climbs = [
    { name: 'A', grade: 4, attempts: 2, flagBoulder: true },
    { name: 'B', grade: 3, attempts: 1, flagSport: true }
  ];

  const s = { name: 'S1', scheduledDate: new Date().toISOString(), climbs };
  const cl = climbLoad(climbs[0], 5);
  assert(typeof cl === 'number' && cl > 0, 'climbLoad should be number');

  const sl = sessionLoad(s as any, 5);
  assert(typeof sl === 'number' && sl > 0, 'sessionLoad should be number');

  const { sessions } = computeSessionLoads([s], 5);
  assert(Array.isArray(sessions) && sessions.length === 1, 'computeSessionLoads should return session array');

  // ACWR basic
  const acwr = computeACWR(sessions.map((ss: any) => ({ scheduledDate: ss.scheduledDate, load: ss.load })), { timeWeighted: true });
  assert(acwr && 'ewma7' in acwr, 'computeACWR should return values');

  console.log('load.test.ts: OK');
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});

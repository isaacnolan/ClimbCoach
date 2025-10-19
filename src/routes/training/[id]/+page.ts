import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
  const res = await fetch(`/api/training/${params.id}`);
  if (!res.ok) throw error(res.status, 'Not Found');
  const session = await res.json();
  return { session };
};

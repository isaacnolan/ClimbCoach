<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';

	let { children } = $props();
	let error: { message: string } | null = null;

	onMount(() => {
		// Initialize any global state here
	});
</script>

{#if error}
	<div class="error">
		<h1>Something went wrong</h1>
		<button onclick={() => window.location.reload()}>Reload Page</button>
	</div>
{:else}
	{@render children()}
{/if}

<style>
	.error {
		text-align: center;
		padding: 2rem;
		max-width: 600px;
		margin: 0 auto;
	}
</style>

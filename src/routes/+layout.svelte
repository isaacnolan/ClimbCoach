<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import ChatBot from '$lib/components/ChatBot.svelte';

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
	<div class="chat-container">
		<ChatBot />
	</div>
{/if}

<style>
	.error {
		text-align: center;
		padding: 2rem;
		max-width: 600px;
		margin: 0 auto;
	}
	
	.chat-container {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		z-index: 1000;
		max-width: 400px;
		width: 100%;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		border-radius: 12px;
		background: white;
	}
</style>

<script lang="ts">
  import { onMount } from 'svelte';

  let messages: { sender: 'user' | 'bot', text: string }[] = [];
  let input = '';
  let isLoading = false;

  async function sendMessage() {
    if (!input.trim()) return;
    const userMessage = input;
    messages = [...messages, { sender: 'user', text: userMessage }];
    input = '';
    isLoading = true;

    try {
      console.log('Sending message:', userMessage); // Debug log
      
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage,
          performance: {
            message: userMessage
          }
        })
      });
      
      console.log('Response status:', res.status); // Debug log
      
      const text = await res.text();
      console.log('Raw response:', text); // Debug log
      
      const data = text ? JSON.parse(text) : null;
      console.log('Parsed data:', data); // Debug log
      
      if (!res.ok || data?.error) {
        const errorMsg = data?.error || data?.detail || 'Server error';
        console.error('Error:', errorMsg);
        throw new Error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
      }
      
      if (!data?.reply) {
        console.error('No reply in response:', data);
        throw new Error('No response received from the server');
      }
      
      console.log('Adding message with text:', data.reply); // Debug log
      messages = [...messages, { 
        sender: 'bot', 
        text: data.reply 
      }];
    } catch (err) {
      console.error('Chat error:', err);
      messages = [...messages, { sender: 'bot', text: 'Sorry something went wrong!' }];
    } finally {
      isLoading = false;
    }
  }

  function handleKeyPress(e: KeyboardEvent) {
    if (e.key === 'Enter') sendMessage();
  }
</script>

<div class="chat-container">
  <div class="messages">
    {#each messages as msg}
      <div class="message {msg.sender}">
        <span>{msg.text}</span>
      </div>
    {/each}
    {#if isLoading}
      <div class="message bot"><span>...</span></div>
    {/if}
  </div>

  <div class="input-bar">
    <input
      type="text"
      placeholder="Ask ClimbBot anything..."
      bind:value={input}
      on:keypress={handleKeyPress}
    />
    <button on:click={sendMessage}>Send</button>
  </div>
</div>

<style>
  .chat-container {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    padding: 1rem;
    margin-top: 2rem;
    display: flex;
    flex-direction: column;
    height: 400px;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .message {
    max-width: 80%;
    padding: 0.8rem 1rem;
    border-radius: 12px;
    line-height: 1.4;
  }

  .message.user {
    align-self: flex-end;
    background: #3498db;
    color: white;
  }

  .message.bot {
    align-self: flex-start;
    background: #f5f5f5;
    color: #333;
  }

  .input-bar {
    display: flex;
    gap: 0.5rem;
  }

  input {
    flex: 1;
    padding: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 1rem;
  }

  button {
    background: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    cursor: pointer;
  }

  button:hover {
    background: #2980b9;
  }
</style>

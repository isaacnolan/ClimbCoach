import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ChatMessage = {
    sender: 'user' | 'bot';
    text: string;
    timestamp?: number;
};

// Load initial state from localStorage if available
const storedMessages = browser ? 
    JSON.parse(localStorage.getItem('chatMessages') || '[]') : 
    [];

// Create a writable store with stored messages as initial value
export const chatMessages = writable<ChatMessage[]>(storedMessages);

// Subscribe to changes and update localStorage
if (browser) {
    chatMessages.subscribe(messages => {
        localStorage.setItem('chatMessages', JSON.stringify(messages));
    });
}

// Helper functions to manipulate the chat store
export function addMessage(message: ChatMessage) {
    chatMessages.update(messages => [
        ...messages, 
        { ...message, timestamp: Date.now() }
    ]);
}

export function clearMessages() {
    chatMessages.set([]);
}

// Function to get the last N messages (useful for context)
export function getLastMessages(n: number = 10) {
    let messages: ChatMessage[] = [];
    chatMessages.subscribe(value => {
        messages = value.slice(-n);
    })();
    return messages;
}
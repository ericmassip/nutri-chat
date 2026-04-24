import 'vite/modulepreload-polyfill'
import '../scss/styles.scss'
import * as bootstrap from 'bootstrap'
import htmx from 'htmx.org'

window.htmx = htmx

// SSE extension must load after htmx is on window (it's an IIFE that reads the global)
import('htmx-ext-sse/sse.js').then(() => {
    htmx.process(document.body)
})

function scrollChatToBottom() {
    const container = document.getElementById('chat-messages')
    if (container) {
        container.scrollTop = container.scrollHeight
    }
}

document.addEventListener('DOMContentLoaded', scrollChatToBottom)

document.body.addEventListener('htmx:sseMessage', (event) => {
    const bubble = event.target.closest('.assistant-bubble')
    if (bubble) {
        const indicator = bubble.querySelector('.typing-indicator')
        if (indicator) indicator.remove()

        if (event.detail.type === 'done') {
            const streaming = bubble.querySelector('.streaming-content')
            if (streaming) streaming.style.display = 'none'
        }
    }

    scrollChatToBottom()
})

document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.detail.target && event.detail.target.id === 'chat-messages') {
        scrollChatToBottom()
    }
})

document.addEventListener('keydown', (e) => {
    if (e.target.matches('.chat-input') && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        const form = e.target.closest('form')
        if (form && e.target.value.trim()) {
            htmx.trigger(form, 'submit')
        }
    }
})

import 'vite/modulepreload-polyfill'
import '../scss/styles.scss'
import * as bootstrap from 'bootstrap'
import htmx from 'htmx.org'

window.htmx = htmx

// SSE extension must load after htmx is on window (it's an IIFE that reads the global)
import('htmx-ext-sse/sse.js').then(() => {
    htmx.process(document.body)
})

import { useEffect, useRef, useState } from 'react'
import ChatMessage from './ChatMessage'

function ChatWindow({ messages, isReplying, error, onSend }) {
  const [question, setQuestion] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isReplying])

  const submit = (event) => {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isReplying) return
    setQuestion('')
    onSend(trimmedQuestion)
  }

  return (
    <article className="panel chat-panel">
      <div className="panel-heading chat-heading">
        <span className="section-number">02</span>
        <div>
          <h2>Ask your knowledge</h2>
          <p>Answers grounded in your indexed documents.</p>
        </div>
      </div>

      <div className="messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="empty-chat">
            <span className="empty-mark" aria-hidden="true">✦</span>
            <h3>What would you like to know?</h3>
            <p>Upload a document, then ask a question about its contents.</p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} role={message.role} content={message.content} />
        ))}

        {isReplying && (
          <div className="message-row assistant" role="status" aria-label="Assistant is typing">
            <span className="avatar" aria-hidden="true">K</span>
            <div className="message typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="chat-error" role="alert">{error}</div>}

      <form className="chat-form" onSubmit={submit}>
        <label className="sr-only" htmlFor="question">Ask a question</label>
        <input
          id="question"
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={isReplying}
          autoComplete="off"
        />
        <button
          className="send-button"
          type="submit"
          disabled={!question.trim() || isReplying}
          aria-label="Send question"
        >
          <span className="send-label">Send</span>
          <span aria-hidden="true">↑</span>
        </button>
      </form>
      <p className="input-hint">Press Enter to send</p>
    </article>
  )
}

export default ChatWindow

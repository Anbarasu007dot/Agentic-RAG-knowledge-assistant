function ChatMessage({ role, content }) {
  const isAssistant = role === 'assistant'

  return (
    <div className={`message-row ${role}`}>
      {isAssistant && <span className="avatar" aria-hidden="true">K</span>}
      <div className="message">
        <span className="message-label">{isAssistant ? 'Assistant' : 'You'}</span>
        <p>{content}</p>
      </div>
    </div>
  )
}

export default ChatMessage

import { useRef, useState } from 'react'
import { uploadDocument } from '../api'

const ALLOWED_EXTENSIONS = ['txt', 'pdf', 'docx']

function DocumentUpload() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const chooseFile = (selectedFile) => {
    setResult(null)
    setError('')

    if (!selectedFile) {
      setFile(null)
      return
    }

    const extension = selectedFile.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setFile(null)
      setError('Please select a TXT, PDF, or DOCX file.')
      if (inputRef.current) inputRef.current.value = ''
      return
    }

    setFile(selectedFile)
  }

  const handleUpload = async () => {
    if (!file || isUploading) return

    setIsUploading(true)
    setError('')
    setResult(null)

    try {
      const data = await uploadDocument(file)
      setResult(data)
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Unable to upload the document.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <article className="panel upload-panel">
      <div className="panel-heading">
        <span className="section-number">01</span>
        <div>
          <h2>Add knowledge</h2>
          <p>Upload a source for the assistant to learn from.</p>
        </div>
      </div>

      <div
        className={`drop-zone ${file ? 'has-file' : ''}`}
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(event) => {
          if ((event.key === 'Enter' || event.key === ' ') && !isUploading) {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Choose a document to upload"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={(event) => chooseFile(event.target.files?.[0])}
          disabled={isUploading}
        />
        <span className="upload-icon" aria-hidden="true">↑</span>
        {file ? (
          <>
            <strong className="selected-name">{file.name}</strong>
            <span>{(file.size / 1024).toFixed(1)} KB · Click to replace</span>
          </>
        ) : (
          <>
            <strong>Choose a document</strong>
            <span>or drop it here</span>
          </>
        )}
        <div className="file-types">
          <span>TXT</span><span>PDF</span><span>DOCX</span>
        </div>
      </div>

      {isUploading && (
        <div className="upload-progress" role="status">
          <div className="progress-track"><span /></div>
          <p>Uploading and indexing your document…</p>
        </div>
      )}

      {result && (
        <div className="notice success" role="status">
          <span className="notice-icon" aria-hidden="true">✓</span>
          <div>
            <strong>Document indexed</strong>
            <p>{result.filename} · {result.indexed_chunks} chunks ready</p>
          </div>
        </div>
      )}

      {error && <div className="notice error" role="alert">{error}</div>}

      <button
        className="button secondary-button"
        type="button"
        onClick={handleUpload}
        disabled={!file || isUploading}
      >
        {isUploading ? 'Indexing…' : 'Upload & index'}
        {!isUploading && <span aria-hidden="true">→</span>}
      </button>
    </article>
  )
}

export default DocumentUpload

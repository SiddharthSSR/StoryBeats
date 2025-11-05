import { useState, useRef } from 'react'
import './PhotoUpload.css'

function PhotoUpload({ onUpload, error }) {
  const [preview, setPreview] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileChange = (file) => {
    if (!file) return

    // Check if it's an image by MIME type OR file extension
    const isImage = file.type.startsWith('image/')
    const fileName = file.name.toLowerCase()
    const hasImageExtension = /\.(jpg|jpeg|png|gif|webp|heic|heif)$/i.test(fileName)

    if (isImage || hasImageExtension) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(file)
      onUpload(file)
    } else {
      // Show error for unsupported file types
      console.warn('Unsupported file type:', file.type, file.name)
    }
  }

  const handleInputChange = (e) => {
    const file = e.target.files[0]
    handleFileChange(file)
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const file = e.dataTransfer.files[0]
    handleFileChange(file)
  }

  const handleClick = () => {
    fileInputRef.current.click()
  }

  return (
    <div className="photo-upload">
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        {preview ? (
          <div className="preview">
            <img src={preview} alt="Preview" />
            <p className="preview-text">Click or drop a new photo to change</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <p className="upload-text">Click to upload or drag and drop</p>
            <p className="upload-hint">PNG, JPG, GIF, HEIC up to 16MB</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}

export default PhotoUpload

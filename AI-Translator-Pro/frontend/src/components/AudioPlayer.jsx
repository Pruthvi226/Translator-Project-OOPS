import { useRef, useEffect } from 'react'
import { getTTSFileUrl } from '../services/api'

export default function AudioPlayer({ audioUrlOrFileId }) {
  const audioRef = useRef(null)

  const src = audioUrlOrFileId?.startsWith('/') || audioUrlOrFileId?.startsWith('http')
    ? audioUrlOrFileId
    : audioUrlOrFileId ? getTTSFileUrl(audioUrlOrFileId) : null

  useEffect(() => {
    if (src && audioRef.current) audioRef.current.load()
  }, [src])

  if (!src) return null

  return (
    <audio ref={audioRef} controls className="w-full max-w-md">
      <source src={src} type="audio/mpeg" />
      Your browser does not support the audio element.
    </audio>
  )
}

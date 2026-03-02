'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

interface UploadCardProps {
  onUploadComplete: () => void
}

export default function UploadCard({ onUploadComplete }: UploadCardProps) {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [bank, setBank] = useState<'monzo' | 'starling'>('monzo')
  const [dragOver, setDragOver] = useState(false)

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    setResult(null)
    try {
      const res = await api.upload(file, bank)
      setResult(res.message)
      onUploadComplete()
    } catch (err: any) {
      setResult(`Error: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }, [bank, onUploadComplete])

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file?.name.endsWith('.csv')) handleUpload(file)
  }

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Import Transactions</h2>

      <div className="flex gap-3 mb-4">
        {(['monzo', 'starling'] as const).map((b) => (
          <button
            key={b}
            onClick={() => setBank(b)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              bank === b
                ? 'bg-brand-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {b === 'monzo' ? '🟠 Monzo' : '💜 Starling'}
          </button>
        ))}
      </div>

      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
          dragOver ? 'border-brand-400 bg-brand-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          type="file"
          accept=".csv"
          onChange={onFileSelect}
          className="hidden"
          id="csv-upload"
          disabled={uploading}
        />
        <label htmlFor="csv-upload" className="cursor-pointer">
          {uploading ? (
            <p className="text-gray-500 animate-pulse">Importing...</p>
          ) : (
            <>
              <p className="text-gray-500 text-sm">
                Drag & drop your {bank === 'monzo' ? 'Monzo' : 'Starling'} CSV here,
                or <span className="text-brand-600 underline">browse</span>
              </p>
            </>
          )}
        </label>
      </div>

      {result && (
        <div className={`mt-3 text-sm p-3 rounded-lg ${
          result.startsWith('Error')
            ? 'bg-red-50 text-red-700'
            : 'bg-green-50 text-green-700'
        }`}>
          {result}
        </div>
      )}
    </div>
  )
}

"use client"
import React, { useEffect, useState } from 'react'

type BuildMeta = {
  commit: string
  date: string
  branch: string
}

export function BuildStamp({ inline = false }: { inline?: boolean }) {
  const [meta, setMeta] = useState<BuildMeta | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const url = typeof window !== 'undefined' ? new URL(window.location.href) : null
    const debug = url?.searchParams.get('debug') === '1'
    setVisible(debug)

    fetch('/version.json', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => setMeta(j))
      .catch(() => setMeta(null))
  }, [])

  if (!meta) return null

  const content = `v ${meta.commit} • ${new Date(meta.date).toLocaleString()} • ${meta.branch}`

  if (inline) {
    return <span data-build-stamp>{content}</span>
  }

  if (!visible) return null

  return (
    <div
      data-build-stamp
      style={{
        position: 'fixed',
        bottom: 8,
        right: 8,
        background: 'rgba(0,0,0,0.7)',
        color: '#fff',
        padding: '6px 10px',
        borderRadius: 6,
        fontSize: 12,
        zIndex: 9999,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
      }}
      title="Build version"
    >
      {content}
    </div>
  )
}

export default BuildStamp



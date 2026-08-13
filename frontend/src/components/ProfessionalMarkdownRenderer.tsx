'use client'

import { useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, FileCode } from 'lucide-react'
import type { Components } from 'react-markdown'
import { useTheme } from 'next-themes'

interface ProfessionalMarkdownRendererProps {
  content: string
  language?: string
}

export default function ProfessionalMarkdownRenderer({ content, language = 'en' }: ProfessionalMarkdownRendererProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  // Use a ref for the counter - NEVER call setState during render (causes hydration errors #418/#423)
  const codeIdCounterRef = useRef(0)
  const { theme = 'dark' } = useTheme()
  const isDark = theme === 'dark'
  const syntaxStyle = isDark ? oneDark : oneLight

  const textPrimary = isDark ? 'text-white' : 'text-gray-900'
  const textSecondary = isDark ? 'text-gray-300' : 'text-gray-700'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-500'
  const bgSecondary = isDark ? 'bg-gray-800' : 'bg-gray-100'
  const bgHeader = isDark ? 'bg-gray-800/80' : 'bg-gray-100'
  const borderColor = isDark ? 'border-gray-700' : 'border-gray-200'
  const borderColorLight = isDark ? 'border-gray-700/50' : 'border-gray-200/60'
  const codeBg = isDark ? 'bg-gray-800' : 'bg-gray-100'
  const codeText = isDark ? 'text-blue-400' : 'text-blue-600'
  const tableHeaderBg = isDark ? 'bg-gray-800/50' : 'bg-gray-100'
  const tableRowHover = isDark ? 'hover:bg-gray-800/30' : 'hover:bg-gray-50'

  const copyToClipboard = async (text: string, codeId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode(codeId)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const detectLanguage = (code: string, fallback?: string): string => {
    if (fallback) return fallback

    if (code.includes('import React') || code.includes('from react')) return 'jsx'
    if (code.includes('import {') && code.includes('from ') && code.includes('export')) return 'typescript'
    if (code.includes('def ') && code.includes(':')) return 'python'
    if (code.includes('function ') || code.includes('const ') && code.includes('=>')) return 'javascript'
    if (code.includes('public class') || code.includes('private ')) return 'java'
    if (code.includes('#include') || code.includes('int main')) return 'cpp'
    if (code.includes('SELECT') || code.includes('FROM') || code.includes('WHERE')) return 'sql'
    if (code.includes('<!DOCTYPE') || code.includes('<html')) return 'html'
    if (code.includes('body {') || code.includes('.class')) return 'css'
    if (code.includes('<?php') || code.includes('$')) return 'php'
    if (code.includes('package main') || code.includes('func ')) return 'go'
    if (code.includes('fn ') && code.includes('->')) return 'rust'
    if (code.includes('#!/bin/bash') || code.includes('echo ')) return 'bash'

    return 'text'
  }

  const extractFileName = (code: string, languageHint?: string): string => {
    const filePatterns = [
      /\/\/\s*file[:\s]+([^\n]+)/i,
      /#\s*file[:\s]+([^\n]+)/i,
      /<!--\s*file[:\s]+([^\n]+)-->/i,
      /\/\*\s*file[:\s]+([^\n]+)\s*\*\//i,
    ]

    for (const pattern of filePatterns) {
      const match = code.match(pattern)
      if (match) return match[1].trim()
    }

    const lang = detectLanguage(code, languageHint)
    const extensions: Record<string, string> = {
      python: 'script.py',
      javascript: 'app.js',
      typescript: 'app.ts',
      jsx: 'Component.jsx',
      tsx: 'Component.tsx',
      java: 'Main.java',
      cpp: 'main.cpp',
      sql: 'query.sql',
      html: 'index.html',
      css: 'styles.css',
      php: 'index.php',
      go: 'main.go',
      rust: 'main.rs',
      bash: 'script.sh',
      text: 'file.txt',
    }

    return extensions[lang] || 'file.txt'
  }

  const components: Components = {
    h1: ({ children }) => (
      <h1 className={`text-3xl font-bold ${textPrimary} mt-6 mb-4 pb-2 border-b ${borderColor}`} dir="auto">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className={`text-2xl font-bold ${textPrimary} mt-5 mb-3 pb-2 border-b ${borderColorLight}`} dir="auto">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className={`text-xl font-semibold ${isDark ? 'text-gray-200' : 'text-gray-800'} mt-4 mb-2`} dir="auto">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className={`text-lg font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mt-3 mb-2`} dir="auto">
        {children}
      </h4>
    ),

    p: ({ children }) => (
      <p className={`${textSecondary} mb-3 leading-relaxed`} dir="auto">
        {children}
      </p>
    ),

    ul: ({ children }) => (
      <ul className={`list-disc list-inside ${textSecondary} mb-3 space-y-1 ml-2`} dir="auto">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className={`list-decimal list-inside ${textSecondary} mb-3 space-y-1 ml-2`} dir="auto">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="ml-2" dir="auto">
        {children}
      </li>
    ),

    strong: ({ children }) => (
      <strong className={`font-bold ${textPrimary}`}>{children}</strong>
    ),
    em: ({ children }) => (
      <em className={`italic ${textSecondary}`}>{children}</em>
    ),

    code: ({ className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || '')
      const isInline = !match && !className

      if (isInline) {
        return (
          <code
            className={`${codeBg} ${codeText} px-1.5 py-0.5 rounded text-sm font-mono`}
            dir="auto"
            {...props}
          >
            {children}
          </code>
        )
      }

      const codeString = String(children).replace(/\n$/, '')
      const language = match ? match[1] : detectLanguage(codeString)
      const fileName = extractFileName(codeString, language)
      // Use ref counter - deterministic across server/client renders
      const codeId = `code-${codeIdCounterRef.current++}`

      return (
        <div className={`relative group my-4 rounded-lg overflow-hidden border ${borderColorLight}`}>
          <div className={`flex items-center justify-between ${bgHeader} px-4 py-2 border-b ${borderColorLight}`}>
            <div className="flex items-center gap-2">
              <FileCode className={`w-4 h-4 ${textMuted}`} />
              <span className={`text-sm ${textSecondary} font-mono`}>
                {(fileName.includes('/') || fileName.includes('\\')) ? `Paste this in ${fileName}` : fileName}
              </span>
            </div>
            <button
              onClick={() => copyToClipboard(codeString, codeId)}
              className={`flex items-center gap-1.5 px-2.5 py-1 ${isDark ? 'bg-gray-700/50 hover:bg-gray-700' : 'bg-gray-200/50 hover:bg-gray-200'} rounded ${textSecondary} hover:text-white transition-all text-xs`}
              title="Copy code"
            >
              {copiedCode === codeId ? (
                <>
                  <Check className={`w-3.5 h-3.5 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                  <span className={isDark ? 'text-green-400' : 'text-green-600'}>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          <SyntaxHighlighter
            style={syntaxStyle}
            language={language}
            PreTag="div"
            className={`!m-0 !p-4 text-sm ${isDark ? '!bg-gray-900' : '!bg-gray-50'}`}
            showLineNumbers
            lineNumberStyle={{
              color: isDark ? '#6b7280' : '#9ca3af',
              paddingRight: '1rem',
              userSelect: 'none',
              fontSize: '0.875rem'
            }}
          >
            {codeString}
          </SyntaxHighlighter>
        </div>
      )
    },

    blockquote: ({ children }) => (
      <blockquote
        className={`border-l-4 ${isDark ? 'border-blue-500' : 'border-blue-600'} pl-4 py-2 my-3 ${isDark ? 'bg-gray-800/30' : 'bg-blue-50'} italic ${textSecondary}`}
        dir="auto"
      >
        {children}
      </blockquote>
    ),

    a: ({ href, children }) => (
      <a
        href={href}
        className={`${isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'} underline`}
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),

    table: ({ children }) => (
      <div className="overflow-x-auto my-4">
        <table className={`min-w-full border-collapse border ${borderColor}`}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className={tableHeaderBg}>
        {children}
      </thead>
    ),
    tbody: ({ children }) => (
      <tbody className={`divide-y ${isDark ? 'divide-gray-700/50' : 'divide-gray-200'}`}>
        {children}
      </tbody>
    ),
    tr: ({ children }) => (
      <tr className={tableRowHover}>
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th className={`border ${borderColor} px-4 py-2 text-left ${textPrimary} font-semibold ${tableHeaderBg}`}>
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className={`border ${borderColor} px-4 py-2 ${textSecondary}`}>
        {children}
      </td>
    ),

    hr: () => (
      <hr className={`${borderColor} my-6`} />
    ),

    img: ({ src, alt }) => (
      <img
        src={src}
        alt={alt}
        className="max-w-full h-auto rounded-lg my-4 mx-auto"
      />
    ),
  }

  return (
    <div
      className="prose max-w-none"
      dir="auto"
      style={{
        textAlign: language === 'ur' || language === 'ar' || language === 'fa' || language === 'ps' ? 'right' : 'left',
      }}
    >
      <ReactMarkdown
        components={components}
        remarkPlugins={[]}
        rehypePlugins={[]}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
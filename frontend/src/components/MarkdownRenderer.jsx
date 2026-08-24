import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * High-performance, beautifully styled Markdown and Table renderer
 * tailored for ESCA HSE AI Assistant responses.
 */
export default function MarkdownRenderer({ content, className = '' }) {
  if (!content) return null

  return (
    <div className={`prose-hse leading-relaxed text-start ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-3 rounded-xl border border-line/90 shadow-md bg-steel-3/50 backdrop-blur-sm">
              <table className="w-full text-xs text-start border-collapse divide-y divide-line/60" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-steel-3 text-txt font-semibold border-b border-line" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th
              className="px-3.5 py-2.5 text-start font-bold text-txt text-[11.5px] sm:text-xs tracking-wider border-e border-line/40 last:border-e-0 whitespace-nowrap bg-steel-3/90"
              {...props}
            />
          ),
          tbody: ({ node, ...props }) => (
            <tbody className="divide-y divide-line/40 text-txt-1" {...props} />
          ),
          tr: ({ node, ...props }) => (
            <tr
              className="hover:bg-hi/10 transition-colors duration-100 odd:bg-steel-2/40 even:bg-steel-3/30"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="px-3.5 py-2 text-start text-[11.5px] sm:text-xs text-txt-1 border-e border-line/30 last:border-e-0 align-middle font-sans num"
              {...props}
            />
          ),
          p: ({ node, ...props }) => (
            <p className="mb-2 last:mb-0 leading-6 text-txt-1 text-xs sm:text-[13px]" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-bold text-white num" {...props} />
          ),
          b: ({ node, ...props }) => (
            <b className="font-bold text-white num" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside my-2 space-y-1 text-txt-1 ps-1 text-xs sm:text-[13px]" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside my-2 space-y-1 text-txt-1 ps-1 text-xs sm:text-[13px]" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-6" {...props} />
          ),
          code: ({ node, inline, className: codeClassName, children, ...props }) => {
            if (inline) {
              return (
                <code
                  className="bg-steel-3/90 text-info font-mono text-[11px] px-1.5 py-0.5 rounded border border-line/60 num"
                  {...props}
                >
                  {children}
                </code>
              )
            }
            return (
              <pre className="bg-steel-3/90 p-3 rounded-xl border border-line overflow-x-auto text-[11px] font-mono my-2.5 text-txt-2">
                <code {...props}>{children}</code>
              </pre>
            )
          },
          h1: ({ node, ...props }) => (
            <h1 className="text-sm sm:text-base font-bold text-white mb-2 mt-3.5 border-b border-line/50 pb-1" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-xs sm:text-sm font-bold text-white mb-1.5 mt-3" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xs sm:text-[12.5px] font-bold text-txt-1 mb-1 mt-2.5" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-s-4 border-hi bg-steel-3/40 px-3.5 py-2 my-2.5 rounded-e-lg text-txt-2 italic text-xs leading-5"
              {...props}
            />
          ),
          hr: ({ node, ...props }) => <hr className="border-line my-3" {...props} />,
          a: ({ node, ...props }) => (
            <a
              className="text-info hover:text-hi underline underline-offset-2 transition-colors font-medium"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

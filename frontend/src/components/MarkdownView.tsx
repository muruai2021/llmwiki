import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { WikilinkSpan } from "./WikilinkSpan";

/**
 * Render markdown, with [[wikilink]] syntax turned into clickable spans.
 */
export function MarkdownView({ content }: { content: string }) {
  // Pre-process: split out [[target|alias]] / [[target]] tokens
  // We pass them through to a custom component map via a customRemark-like trick:
  // simplest — replace [[x]] with [x](wikilink:x) before rendering.
  const preprocessed = preprocessWikilinks(content);
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href, children, ...rest }) {
            if (typeof href === "string" && href.startsWith("wikilink:")) {
              const target = href.slice("wikilink:".length);
              return <WikilinkSpan target={target} />;
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" {...rest}>
                {children}
              </a>
            );
          },
        }}
      >
        {preprocessed}
      </ReactMarkdown>
    </div>
  );
}

function preprocessWikilinks(src: string): string {
  // Match [[target]] or [[target|alias]]
  return src.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (_full, target: string, alias: string | undefined) => {
      const text = alias || target;
      // Encode target for the URL
      return `[${text}](wikilink:${encodeURIComponent(target)})`;
    },
  );
}

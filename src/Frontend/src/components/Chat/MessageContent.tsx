import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { solarizedlight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import { MessageContentProps } from '../../types/chat';

const MessageContent: React.FC<MessageContentProps> = ({ content }) => {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  const elements = [];

  content.replace(codeBlockRegex, (match, lang, code, index) => {
    if (index > lastIndex) {
      const textBefore = content.slice(lastIndex, index);
      elements.push(
        <div key={`${lastIndex}-text`} className="leading-relaxed">
          <ReactMarkdown
            components={{
              ul: ({ node, ...props }) => <ul className="list-disc pl-5" {...props} />,
              li: ({ node, ...props }) => <li className="mb-1" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
            }}
          >
            {textBefore}
          </ReactMarkdown>
        </div>
      );
    }

    elements.push(
      <SyntaxHighlighter
        key={index}
        language={lang || 'text'}
        style={solarizedlight}
        customStyle={{ margin: '0.5rem 0' }}
      >
        {code.trim()}
      </SyntaxHighlighter>
    );

    lastIndex = index + match.length;
    return match;
  });

  if (lastIndex < content.length) {
    const remainingText = content.slice(lastIndex);
    elements.push(
      <div key={`${lastIndex}-text`} className="leading-relaxed">
        <ReactMarkdown
          components={{
            ul: ({ node, ...props }) => <ul className="list-disc pl-5" {...props} />,
            li: ({ node, ...props }) => <li className="mb-1" {...props} />,
            strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
          }}
        >
          {remainingText}
        </ReactMarkdown>
      </div>
    );
  }

  return elements.length > 0 ? <>{elements}</> : (
    <div className="leading-relaxed">
      <ReactMarkdown
        components={{
          ul: ({ node, ...props }) => <ul className="list-disc pl-5" {...props} />,
          li: ({ node, ...props }) => <li className="mb-1" {...props} />,
          strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MessageContent;
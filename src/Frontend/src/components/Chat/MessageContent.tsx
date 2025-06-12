import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { solarizedlight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import { MessageContentProps } from '../../types/chat';
import { FileText } from 'lucide-react';

const MessageContent: React.FC<MessageContentProps> = ({ content, sender, attachments }) => {
  const renderAttachments = () => {
    if (!attachments || attachments.length === 0) {
      return null;
    }

    return (
      <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
        {attachments.map((file, index) => (
          <div key={index} className="bg-blue-100 rounded-lg p-2 flex items-center space-x-2 text-xs">
             <FileText className="h-5 w-5 text-blue-500" />
            <div className="flex-1 truncate">
              <p className="font-medium text-blue-800 truncate">{file.name}</p>
              <p className="text-blue-600">{ (file.size / 1024).toFixed(1) } KB</p>
            </div>
             {/* Note: Download functionality can be added here */}
          </div>
        ))}
      </div>
    );
  };

  // Nếu là user message, render text và attachments
  if (sender === 'user') {
    return (
      <div>
        {content && <div className="leading-relaxed whitespace-pre-wrap">{content}</div>}
        {renderAttachments()}
      </div>
    );
  }

  // Với bot messages, sử dụng markdown parsing và clean up whitespace
  const processedContent = content.replace(/\n\s*\n\s*\n/g, '\n\n').trim();
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  const elements = [];

  processedContent.replace(codeBlockRegex, (match, lang, code, index) => {
          if (index > lastIndex) {
        const textBefore = processedContent.slice(lastIndex, index);
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

  if (lastIndex < processedContent.length) {
    const remainingText = processedContent.slice(lastIndex);
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
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};

export default MessageContent;
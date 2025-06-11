// MessageList.tsx
import React, { useEffect } from 'react';
import { MessageListProps } from '../../types/chat';
import MessageContent from './MessageContent';

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  currentBotMessage,
  displayedContent,
  stoppedContent,
  isTyping,
  setDisplayedContent,
  setIsTyping,
}) => {
  useEffect(() => {
    if (isTyping && currentBotMessage && displayedContent !== currentBotMessage.content) {
      const timer = setTimeout(() => {
        setDisplayedContent(currentBotMessage.content.slice(0, displayedContent.length + 1));
      }, 0.1);
      return () => clearTimeout(timer);
    } else if (isTyping && currentBotMessage && displayedContent === currentBotMessage.content) {
      setIsTyping(false);
    }
  }, [currentBotMessage, displayedContent, isTyping, setDisplayedContent, setIsTyping]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg p-3 ${
              message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
            }`}
          >
            <MessageContent
              content={
                message === currentBotMessage && isTyping
                  ? displayedContent
                  : stoppedContent || message.content
              }
              attachments={message.attachments} // Truyền attachments vào MessageContent
            />
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold">Attachments:</p>
                {message.attachments.map((file, index) => (
                  <div key={index} className="text-xs text-gray-600">
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="flex justify-start">
          <div className="max-w-[70%] rounded-lg p-3 bg-gray-100 flex items-center justify-center">
            <div className="loader" />
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
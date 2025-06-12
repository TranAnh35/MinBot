// MessageList.tsx
import React, { useEffect, useRef } from 'react';
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
  onLoadMoreHistory,
  hasMoreHistory,
  isLoadingMoreHistory,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

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
    <div className="flex-1 overflow-y-auto space-y-6">
      <div className="container mx-auto px-4 py-4">
        {/* Load More History Button */}
        {hasMoreHistory && (
          <div className="flex justify-center mb-4">
            <button
              onClick={onLoadMoreHistory}
              disabled={isLoadingMoreHistory}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoadingMoreHistory ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Đang tải...</span>
                </div>
              ) : (
                'Tải thêm tin nhắn cũ'
              )}
            </button>
          </div>
        )}
        
        {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === 'user'
                  ? 'justify-end'
                  : 'justify-start'
              } mb-6`}
            >
              <div
                className={`max-w-3xl px-4 py-2 rounded-lg ${
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                    <span>Đang nhập...</span>
                  </div>
                ) : (
                  <MessageContent 
                    content={
                      message === currentBotMessage && isTyping
                        ? displayedContent
                        : stoppedContent || message.content
                    }
                    attachments={message.attachments}
                    sender={message.sender}
                  />
                )}
              </div>
            </div>
          ))}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList;
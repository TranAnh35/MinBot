// ChatInput.tsx
import React from 'react';
import { Send, Square, Paperclip, Globe } from 'lucide-react';
import { Button } from '../ui/button';
import { ChatInputProps } from '../../types/chat';

interface ExtendedChatInputProps extends ChatInputProps {
  open?: () => void; // Thêm prop open
}

const ChatInput: React.FC<ExtendedChatInputProps> = ({
  input,
  setInput,
  isLoading,
  isTyping,
  isWebSearchEnabled,
  chatFiles,
  onSend,
  onStopTyping,
  toggleWebSearch,
  open, // Nhận hàm open từ FileDropzone
}) => {
  return (
    <>
      <div className="flex space-x-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={(e) => {
            e.stopPropagation();
            if (open) open(); // Gọi open để mở dialog chọn file
          }}
          className="shrink-0 hover:bg-gray-200"
        >
          <Paperclip className="h-5 w-5 text-gray-600" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleWebSearch}
          className={`shrink-0 transition-colors duration-200 ${
            isWebSearchEnabled ? 'bg-blue-100 text-blue-600 hover:bg-blue-200' : 'hover:bg-gray-200'
          }`}
        >
          <Globe className="h-5 w-5" />
        </Button>
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && (isTyping ? onStopTyping() : onSend())}
        placeholder={isWebSearchEnabled ? 'Search the web...' : 'Message Gemini'}
        className="flex-1 bg-transparent border-0 focus:ring-0 text-gray-900 placeholder-gray-500 text-sm outline-none"
        onClick={(e) => e.stopPropagation()}
        disabled={isLoading}
      />
      {isTyping ? (
        <Button
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation();
            onStopTyping();
          }}
          className="shrink-0 text-white rounded-lg bg-blue-600 hover:bg-blue-700"
          size="icon"
        >
          <Square className="h-4 w-4" />
        </Button>
      ) : (
        <Button
          onClick={(e) => {
            e.stopPropagation();
            onSend();
          }}
          className="shrink-0 text-white rounded-lg bg-blue-600 hover:bg-blue-700"
          size="icon"
        >
          <Send className="h-4 w-4" />
        </Button>
      )}
    </>
  );
};

export default ChatInput;
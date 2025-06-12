// ChatInput.tsx
import React, { useRef, useEffect } from 'react';
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120); // Max height 120px (khoảng 5 dòng)
      textarea.style.height = `${newHeight}px`;
      
      // Nếu content vượt quá max height, hiện scrollbar
      if (textarea.scrollHeight > 120) {
        textarea.style.overflowY = 'auto';
      } else {
        textarea.style.overflowY = 'hidden';
      }
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (e.shiftKey || e.ctrlKey) {
        return; // Cho phép default behavior (xuống dòng)
      } else {
        // Enter: gửi tin nhắn
        e.preventDefault();
        if (isTyping) {
          onStopTyping();
        } else {
          onSend();
        }
      }
    }
  };
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
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={isWebSearchEnabled ? 'Search the web...' : 'Message Gemini'}
        className="flex-1 bg-transparent border-0 focus:ring-0 text-gray-900 placeholder-gray-500 text-sm outline-none resize-none min-h-[24px]"
        onClick={(e) => e.stopPropagation()}
        disabled={isLoading}
        rows={1}
        style={{ height: '24px' }} // Chiều cao ban đầu
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
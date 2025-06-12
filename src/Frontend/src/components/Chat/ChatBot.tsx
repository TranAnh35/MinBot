import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ChatBotProps, Message, Conversation } from '../../types/chat';
import { generateContent, createConversation, getConversationHistory, listUserConversations, deleteConversation, renameConversation, addMessage } from '../../services/api';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import FileSelector from './FileSelector';
import FileDropzone from './FileDropzone';
import { GenerateContentRequest } from '../../types/chat';
import { UploadedFile } from '../../types/interface';
import { ConversationSidebar } from './ConversationSidebar';
import { useSnackbar } from 'notistack';

const DEFAULT_USER_ID = "default_user";

export const ChatBot: React.FC<ChatBotProps> = ({ 
  uploadedFiles, 
  selectedFiles, 
  onFileSelect,
  showConversations,
  onCloseConversations
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [displayedContent, setDisplayedContent] = useState<string>('');
  const [stoppedContent, setStoppedContent] = useState<string | null>(null);
  const [currentBotMessage, setCurrentBotMessage] = useState<Message | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [showFileSelector, setShowFileSelector] = useState(false);
  const [isWebSearchEnabled, setIsWebSearchEnabled] = useState(false);
  const [chatFiles, setChatFiles] = useState<File[]>([]);
  
  // Conversation state
  const [userId] = useState<string>(DEFAULT_USER_ID);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(undefined);
  const [isConversationsLoading, setIsConversationsLoading] = useState(false);
  const [isConversationsLoaded, setIsConversationsLoaded] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [isLoadingMoreHistory, setIsLoadingMoreHistory] = useState(false);
  
  // State quản lý pagination, logic hoàn toàn dựa vào backend
  const [hasMoreHistory, setHasMoreHistory] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);

  // Ref để tránh cập nhật state trên component đã unmounted
  const isMounted = useRef(true);
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const { enqueueSnackbar } = useSnackbar();

  const loadConversations = useCallback(async () => {
    setIsConversationsLoading(true);
    try {
      const userConversations = await listUserConversations(userId);
      setConversations(userConversations);
    } catch (error) {
      enqueueSnackbar('Lỗi khi tải danh sách cuộc trò chuyện', { 
        variant: 'error',
      });
    } finally {
      setIsConversationsLoading(false);
      setIsConversationsLoaded(true); // Đánh dấu là đã tải xong conversations
    }
  }, [userId, enqueueSnackbar]);

  const loadConversationHistory = useCallback(async (conversationId: string, offset = 0) => {
    const isLoadingMore = offset > 0;
    if (isLoadingMore) {
      setIsLoadingMoreHistory(true);
    } else {
      setIsLoading(true);
      setMessages([]); // Xóa tin nhắn cũ khi chuyển conversation
    }

    try {
      const data = await getConversationHistory(conversationId, 50, offset);
      if (data && data.messages) {
        setMessages(prev => isLoadingMore ? [...data.messages, ...prev] : data.messages);
        setHasMoreHistory(data.has_more);
        setCurrentOffset(offset + data.messages.length);
      }
    } catch (error) {
      enqueueSnackbar('Lỗi khi tải lịch sử cuộc trò chuyện', { variant: 'error' });
    } finally {
      setIsLoading(false);
      setIsLoadingMoreHistory(false);
    }
  }, [enqueueSnackbar]);

  const loadMoreHistory = useCallback(() => {
    if (currentConversationId && hasMoreHistory && !isLoadingMoreHistory) {
      loadConversationHistory(currentConversationId, currentOffset);
    }
  }, [currentConversationId, hasMoreHistory, isLoadingMoreHistory, loadConversationHistory, currentOffset]);
  
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (currentConversationId && !isSendingMessage) {
      loadConversationHistory(currentConversationId, 0);
    } else if (!currentConversationId) {
      setMessages([]);
      setHasMoreHistory(false);
      setCurrentOffset(0);
    }
  }, [currentConversationId, isSendingMessage, loadConversationHistory]);

  const handleCreateNewConversation = useCallback(async () => {
    setIsLoading(true);
    try {
      const newConversationId = await createConversation(userId);
      setCurrentConversationId(newConversationId);
      setMessages([]);
      loadConversations();
      if (onCloseConversations) {
        onCloseConversations();
      }
      enqueueSnackbar('Đã tạo cuộc trò chuyện mới', { 
        variant: 'success',
      });
    } catch (error) {
      enqueueSnackbar('Lỗi khi tạo cuộc trò chuyện mới', { 
        variant: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, loadConversations, enqueueSnackbar, onCloseConversations]);

  const handleConversationSelect = useCallback((conversationId: string) => {
    setCurrentConversationId(conversationId);
    if (onCloseConversations) {
      onCloseConversations();
    }
  }, [onCloseConversations]);

  const handleRenameConversation = useCallback(async (conversationId: string, title: string) => {
    try {
      const success = await renameConversation(conversationId, title);
      if (success) {
        loadConversations();
        enqueueSnackbar('Đã đổi tên cuộc trò chuyện', { 
          variant: 'success',
        });
      } else {
        enqueueSnackbar('Không thể đổi tên cuộc trò chuyện', { 
          variant: 'error',
        });
      }
    } catch (error) {
      enqueueSnackbar('Lỗi khi đổi tên cuộc trò chuyện', { 
        variant: 'error',
      });
    }
  }, [loadConversations, enqueueSnackbar]);

  const handleDeleteConversation = useCallback(async (conversationId: string) => {
    try {
      await deleteConversation(conversationId);
      
      if (conversationId === currentConversationId) {
        setCurrentConversationId(undefined);
        setMessages([]);
      }
      
      // Tải lại danh sách cuộc trò chuyện
      loadConversations();
      enqueueSnackbar('Đã xóa cuộc trò chuyện', { 
        variant: 'success',
      });
    } catch (error) {
      enqueueSnackbar('Lỗi khi xóa cuộc trò chuyện', { 
        variant: 'error',
      });
    }
  }, [currentConversationId, loadConversations, enqueueSnackbar]);

  const convertFilesToUploadedFiles = (files: File[]): UploadedFile[] => {
    return files.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      name: file.name,
      size: file.size,
      type: file.type,
    }));
  };

  // Đọc file thành base64
  const filesToBase64 = async (files: File[]) => {
    const promises = files.map(
      (file) =>
        new Promise<{ name: string; size: number; content: string }>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1];
            resolve({ name: file.name, size: file.size, content: base64 });
          };
          reader.onerror = reject;
          reader.readAsDataURL(file);
        })
    );
    return Promise.all(promises);
  };

  const handleSend = async () => {
    if (!input.trim() && chatFiles.length === 0) return;
    if (isSending) return;

    setIsSending(true);
    const userInput = input.trim();
    const filesToSend = [...chatFiles];
    let attachments: { name: string; size: number; content: string }[] = [];
    if (filesToSend.length > 0) {
      attachments = await filesToBase64(filesToSend);
    }
    setInput('');
    setChatFiles([]);

    let conversationId = currentConversationId;
    let isNewConversation = false;

    if (!conversationId) {
        try {
            const newConversationId = await createConversation(userId);
            if (!isMounted.current) return;
            setCurrentConversationId(newConversationId);
            conversationId = newConversationId;
            isNewConversation = true;
        } catch (error) {
            if (!isMounted.current) return;
            enqueueSnackbar('Lỗi khi tạo cuộc trò chuyện, thử lại sau', { variant: 'error' });
            setIsSending(false);
            setInput(userInput);
            // Re-add files if creation failed
            return;
        }
    }

    const tempUserMessage: Message = {
      id: `temp_user_${Date.now()}`,
      content: userInput,
      sender: 'user',
      timestamp: new Date(),
      attachments: filesToSend.map((file, idx) => ({
        id: `${Date.now()}-${idx}`,
        name: file.name,
        size: file.size,
        type: file.type,
      })),
    };

    const tempBotMessage: Message = {
        id: `temp_bot_${Date.now()}`,
        sender: 'assistant',
        content: '',
        timestamp: new Date(),
        loading: true,
    };
    
    setMessages((prevMessages) => [...prevMessages, tempUserMessage, tempBotMessage]);

    try {
        // Gửi tin nhắn người dùng và không đợi
        addMessage(conversationId, 'user', userInput, attachments.length > 0 ? attachments : undefined)
            .then(response => {
                if (isMounted.current && response.success && response.message) {
                    setMessages(prev => prev.map(m => m.id === tempUserMessage.id ? { ...m, ...response.message } : m));
                }
            });

        const requestData: GenerateContentRequest = {
            input: userInput,
            files: filesToSend.length > 0 ? filesToSend : undefined,
            isWebSearchEnabled: isWebSearchEnabled,
            conversationId: conversationId
        };
        
        // This is where we call the backend
        const llmResponse = await generateContent(requestData);

        if (isMounted.current && llmResponse.content) {
            const finalBotMessage: Message = {
                ...tempBotMessage,
                content: llmResponse.content,
                loading: false,
                id: `bot_${Date.now()}`,
            };

            setMessages(prev => prev.map(m => m.id === tempBotMessage.id ? finalBotMessage : m));
            
            // Persist bot message
            addMessage(conversationId, 'assistant', llmResponse.content)
              .then(response => {
                  if (isMounted.current && response.success && response.message) {
                      setMessages(prev => prev.map(m => m.id === finalBotMessage.id ? { ...m, ...response.message } : m));
                  }
              });

            if (isNewConversation) {
                loadConversations();
            }
        } else {
             // Handle case where content is empty or error
             setMessages(prev => prev.filter(m => m.id !== tempBotMessage.id));
        }

    } catch (error) {
        if (isMounted.current) {
            enqueueSnackbar('Lỗi khi gửi tin nhắn hoặc tạo phản hồi', { variant: 'error' });
            // Remove user and bot temp messages on error
            setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id && m.id !== tempBotMessage.id));
            setInput(userInput);
        }
    } finally {
        if (isMounted.current) {
            setIsSending(false);
        }
    }
  };

  const handleStopTyping = () => {
    if (!isTyping) return;
    setIsTyping(false);
    setStoppedContent(displayedContent);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] pt-16">
      <MessageList
        messages={messages}
        isLoading={isSending}
        currentBotMessage={currentBotMessage}
        displayedContent={displayedContent}
        stoppedContent={stoppedContent}
        isTyping={isTyping}
        setDisplayedContent={setDisplayedContent}
        setIsTyping={setIsTyping}
        onLoadMoreHistory={loadMoreHistory}
        hasMoreHistory={hasMoreHistory}
        isLoadingMoreHistory={isLoadingMoreHistory}
      />
      {showFileSelector && (
        <FileSelector
          uploadedFiles={uploadedFiles}
          selectedFiles={selectedFiles}
          onFileSelect={onFileSelect}
          onClose={() => setShowFileSelector(false)}
        />
      )}
      <FileDropzone
        chatFiles={chatFiles}
        setChatFiles={setChatFiles}
      >
        <ChatInput
          input={input}
          setInput={setInput}
          isLoading={isSending}
          isTyping={isTyping}
          isWebSearchEnabled={isWebSearchEnabled}
          chatFiles={chatFiles}
          onSend={handleSend}
          onStopTyping={handleStopTyping}
          toggleWebSearch={() => setIsWebSearchEnabled(!isWebSearchEnabled)}
        />
      </FileDropzone>

      {/* Conversation Sidebar */}
      <ConversationSidebar
        userId={userId}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onCreateNewConversation={handleCreateNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        isLoading={isConversationsLoading}
        isOpen={showConversations || false}
        onClose={onCloseConversations || (() => {})}
      />
    </div>
  );
};
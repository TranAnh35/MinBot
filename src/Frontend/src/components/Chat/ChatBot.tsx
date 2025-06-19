import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ChatBotProps, Message, Conversation } from '../../types/chat';
import { generateContent, createConversation, getConversationHistory, listUserConversations, deleteConversation, renameConversation, addMessage } from '../../services/api';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import FileSelector from './FileSelector';
import FileDropzone from './FileDropzone';
import { GenerateContentRequest } from '../../types/chat';
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
    /*
     * Khi thay đổi conversation, chỉ tải lại lịch sử nếu hiện không ở trạng thái gửi tin nhắn
     * (tránh xoá message tạm thời vừa thêm). Không cần theo dõi isSending trong dependency –
     * nếu đang gửi thì lần thay đổi tiếp theo (khi gửi xong) cũng không đổi conversationId,
     * nên việc nạp lại lịch sử sẽ được thực hiện thủ công ở lần khác (ví dụ khi người dùng
     * rời và quay lại cuộc trò chuyện).
     */
    if (currentConversationId && !isSending) {
      loadConversationHistory(currentConversationId, 0);
    } else if (!currentConversationId) {
      // Reset state khi không còn conversation
      setMessages([]);
      setHasMoreHistory(false);
      setCurrentOffset(0);
      setIsTyping(false);
      setIsSending(false);
      setCurrentBotMessage(null);
    }
  }, [currentConversationId, loadConversationHistory]);
  
  // Kiểm tra xem có cần tạo conversation mới sau khi load danh sách
  useEffect(() => {
    const checkAndCreateConversation = async () => {
      // Chỉ thực hiện khi đã tải xong danh sách conversations
      if (isConversationsLoaded && conversations.length === 0 && !isConversationsLoading) {
        console.log("Không có conversation nào, đã sẵn sàng cho cuộc trò chuyện mới");
        // Không tạo trực tiếp ở đây, chỉ hiển thị thông báo
        enqueueSnackbar('Không có cuộc trò chuyện nào. Gõ tin nhắn để bắt đầu cuộc trò chuyện mới.', {
          variant: 'info',
          autoHideDuration: 5000
        });
      }
    };
    
    checkAndCreateConversation();
  }, [isConversationsLoaded, conversations.length, isConversationsLoading, enqueueSnackbar]);

  const handleCreateNewConversation = useCallback(async () => {
    setIsLoading(true);
    try {
      const newConversationId = await createConversation(userId);
      if (!newConversationId) {
        throw new Error("Conversation ID không hợp lệ");
      }
      
      setCurrentConversationId(newConversationId);
      setMessages([]);
      setHasMoreHistory(false);
      setCurrentOffset(0);
      
      // Đảm bảo conversation mới được thêm vào danh sách
      await loadConversations();
      
      if (onCloseConversations) {
        onCloseConversations();
      }
      enqueueSnackbar('Đã tạo cuộc trò chuyện mới', { 
        variant: 'success',
      });
    } catch (error) {
      console.error("Lỗi tạo conversation mới:", error);
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
    // Optimistic update first
    let prevTitle: string | undefined;
    setConversations(prev => prev.map(c => {
      if (c.conversation_id === conversationId) {
        prevTitle = c.title;
        return { ...c, title };
      }
      return c;
    }));
    try {
      const success = await renameConversation(conversationId, title);
      if (success) {
        // Ensure backend state synced
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
      // Revert optimistic update on error if we had previous title
      if (prevTitle !== undefined) {
        setConversations(prev => prev.map(c => c.conversation_id === conversationId ? { ...c, title: prevTitle! } : c));
      }
      enqueueSnackbar('Lỗi khi đổi tên cuộc trò chuyện', { 
        variant: 'error',
      });
    }
  }, [loadConversations, enqueueSnackbar]);

  const handleDeleteConversation = useCallback(async (conversationId: string) => {
    // Optimistically remove from local list for immediate feedback
    const prevConvs = conversations;
    setConversations(prev => prev.filter(c => c.conversation_id !== conversationId));
    try {
      await deleteConversation(conversationId);
      // If the deleted conversation is currently open, reset UI state
      if (conversationId === currentConversationId) {
        setCurrentConversationId(undefined);
        setMessages([]);
        setHasMoreHistory(false);
        setCurrentOffset(0);
        setIsLoading(false);
        setIsTyping(false);
        setIsSending(false);
        setDisplayedContent('');
        setStoppedContent(null);
        setCurrentBotMessage(null);
      }

      // Refresh list from backend to stay in sync
      await loadConversations();

      // Provide feedback – note: will be overwritten if no conversations later
      enqueueSnackbar('Đã xóa cuộc trò chuyện', {
        variant: 'success',
      });

      // Check if there are still conversations after deletion
      const updatedConversations = await listUserConversations(userId);
      if (updatedConversations.length === 0) {
        enqueueSnackbar('Đã xóa cuộc trò chuyện cuối cùng. Gõ tin nhắn để bắt đầu cuộc trò chuyện mới.', {
          variant: 'info',
          autoHideDuration: 5000,
        });
      }
    } catch (error) {
      // Revert optimistic removal on error
      setConversations(prevConvs);
      console.error('Lỗi khi xóa conversation:', error);
      enqueueSnackbar('Lỗi khi xóa cuộc trò chuyện', {
        variant: 'error',
      });
    }
  }, [currentConversationId, loadConversations, enqueueSnackbar, userId, conversations]);

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

  // Hàm chuẩn hóa message từ backend về đúng shape Message
  function normalizeMessageFromBackend(msg: any, tempId: string): Message {
    return {
      id: msg.id || tempId,
      content: msg.content,
      sender: msg.sender || (msg.role === 'user' ? 'user' : (msg.role === 'assistant' ? 'assistant' : 'bot')),
      timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
      attachments: Array.isArray(msg.attachments) ? msg.attachments.map((f: any, idx: number) => ({
        id: f.id || `${tempId}-file-${idx}`,
        name: f.name,
        size: f.size,
        type: f.type || '',
        path: f.path,
        error: f.error
      })) : undefined,
      loading: false,
    };
  }

  const handleSend = async () => {
    if (!input.trim() && chatFiles.length === 0) return;
    if (isSending) return;

    setIsSending(true);
    const userInput = input.trim();
    const filesToSend = [...chatFiles];
    setInput('');
    setChatFiles([]);

    let conversationId = currentConversationId;
    let isNewConversation = false;

    // Luôn tạo conversation mới nếu không có, trước khi xử lý file
    if (!conversationId) {
        try {
            // Log để debug
            console.log("Không có conversation ID, tạo conversation mới...");
            
            // Tạo conversation mới khi chưa có
            const newConversationId = await createConversation(userId);
            if (!isMounted.current) return;
            
            // Log để debug
            console.log("Đã tạo conversation mới với ID:", newConversationId);
            
            // Cập nhật conversation ID ngay lập tức để tránh race condition
            conversationId = newConversationId;
            isNewConversation = true;
            
            // Đảm bảo rằng có conversation hợp lệ trước khi tiếp tục
            if (!newConversationId) {
                if (!isMounted.current) return;
                throw new Error("Lỗi tạo conversation: ID không hợp lệ");
            }
            
            // Cập nhật state ngay lập tức
            setCurrentConversationId(newConversationId);
            
            // Reload danh sách conversation ngay lập tức để đồng bộ với backend
            await loadConversations();
        } catch (error) {
            if (!isMounted.current) return;
            console.error("Lỗi khi tạo conversation mới:", error);
            enqueueSnackbar('Lỗi khi tạo cuộc trò chuyện, thử lại sau', { variant: 'error' });
            setIsSending(false);
            setInput(userInput); // Khôi phục nội dung input
            setChatFiles([...filesToSend]); // Khôi phục files đã chọn
            return;
        }
    }
    
    // Xử lý file đính kèm sau khi đã có conversationId
    let attachments: { name: string; size: number; content: string }[] = [];
    if (filesToSend.length > 0) {
      try {
        console.log("Xử lý file đính kèm cho conversation:", conversationId);
        attachments = await filesToBase64(filesToSend);
      } catch (fileError) {
        console.error("Lỗi khi xử lý file đính kèm:", fileError);
        // Vẫn tiếp tục gửi message mà không có file đính kèm
        enqueueSnackbar('Có lỗi khi xử lý file đính kèm, tin nhắn sẽ được gửi mà không kèm file', { 
          variant: 'warning',
          autoHideDuration: 3000 
        });
      }
    }

    // Tạo ID với thêm chuỗi ngẫu nhiên để tránh trùng lặp
    const uniqueUserMsgId = `temp_user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const uniqueBotMsgId = `temp_bot_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    
    const tempUserMessage: Message = {
      id: uniqueUserMsgId,
      content: userInput,
      sender: 'user',
      timestamp: new Date(),
      attachments: filesToSend.map((file, idx) => ({
        id: `${uniqueUserMsgId}-file-${idx}`,
        name: file.name,
        size: file.size,
        type: file.type,
      })),
    };

    const tempBotMessage: Message = {
        id: uniqueBotMsgId,
        sender: 'assistant',
        content: '',
        timestamp: new Date(),
        loading: true,
    };
    
    // Cập nhật UI ngay lập tức
    setMessages((prevMessages) => [...prevMessages, tempUserMessage, tempBotMessage]);

    // Sử dụng một khối try-catch chính để bao quanh toàn bộ logic
    try {
        // Kiểm tra lại conversationId một lần nữa để đảm bảo an toàn
        if (!conversationId) {
            throw new Error("Không có conversation ID hợp lệ để gửi tin nhắn");
        }
        
        console.log("Bắt đầu gửi tin nhắn đến conversation:", conversationId);
        console.log("File đính kèm:", attachments.length);
        
        // Gửi tin nhắn người dùng 
        try {
            const userMessageResponse = await addMessage(
                conversationId, 
                'user', 
                userInput, 
                attachments.length > 0 ? attachments : undefined
            );
            
            if (isMounted.current) {
                if (userMessageResponse.success && userMessageResponse.message) {
                    console.log("Tin nhắn người dùng đã lưu thành công:", userMessageResponse.message.id);
                    const normMsg = normalizeMessageFromBackend(userMessageResponse.message, tempUserMessage.id);
                    setMessages(prev => prev.map(m => m.id === tempUserMessage.id ? normMsg : m));
                } else if (userMessageResponse.note === 'Duplicate message detected' && userMessageResponse.message) {
                    console.log("Phát hiện tin nhắn trùng lặp:", userMessageResponse.message.id);
                    const normMsg = normalizeMessageFromBackend(userMessageResponse.message, tempUserMessage.id);
                    setMessages(prev => prev.map(m => m.id === tempUserMessage.id ? normMsg : m));
                } else {
                    console.warn("Phản hồi khi lưu tin nhắn không như mong đợi:", userMessageResponse);
                }
            }
        } catch (userMsgError) {
            console.error("Lỗi khi lưu tin nhắn người dùng:", userMsgError);
            enqueueSnackbar('Lỗi: Không thể lưu tin nhắn', { variant: 'error', autoHideDuration: 5000 });
            // Stop further processing to avoid cascading errors
            if (isMounted.current) {
              setIsTyping(false);
              setCurrentBotMessage(null);
              setIsSending(false);
            }
            return;
        }

        // Bật trạng thái "đang nhập" 
        setCurrentBotMessage(tempBotMessage);
        setIsTyping(true);

        // Kiểm tra lại conversationId trước khi gửi yêu cầu tới LLM
        if (!conversationId) {
            console.error("Không có conversation ID hợp lệ để gửi đến LLM");
            throw new Error("Không có conversation ID hợp lệ để gửi đến LLM");
        }
        
        console.log("Gửi yêu cầu tới LLM với conversation ID:", conversationId);
        
        const requestData: GenerateContentRequest = {
            input: userInput,
            files: filesToSend.length > 0 ? filesToSend : undefined,
            isWebSearchEnabled: isWebSearchEnabled,
            conversationId: conversationId
        };
        
        // Gọi API để lấy phản hồi từ LLM
        const llmResponse = await generateContent(requestData);

        if (isMounted.current) {
            if (llmResponse?.content) {
                const finalBotMessage: Message = {
                    ...tempBotMessage,
                    content: llmResponse.content,
                    loading: false,
                    id: `bot_${Date.now()}`,
                };

                setMessages(prev => prev.map(m => m.id === tempBotMessage.id ? finalBotMessage : m));
                
                // Tắt trạng thái đang nhập
                setIsTyping(false);
                setCurrentBotMessage(null);
                
                // Lưu phản hồi bot vào conversation history
                try {
                    // Kiểm tra lại conversationId
                    if (!conversationId) {
                        throw new Error("Không có conversation ID hợp lệ để lưu phản hồi bot");
                    }
                    
                    console.log("Lưu phản hồi bot cho conversation ID:", conversationId);
                    
                    const botMsgResponse = await addMessage(conversationId, 'assistant', llmResponse.content);
                    
                    if (isMounted.current) {
                        if (botMsgResponse.success && botMsgResponse.message) {
                            console.log("Đã lưu tin nhắn bot thành công:", botMsgResponse.message.id);
                            const normMsg = normalizeMessageFromBackend(botMsgResponse.message, finalBotMessage.id);
                            setMessages(prev => prev.map(m => m.id === finalBotMessage.id ? normMsg : m));
                        } else {
                            console.warn("Lưu tin nhắn bot không thành công hoặc không có phản hồi:", botMsgResponse);
                        }
                    }
                } catch (botMsgError) {
                    console.error('Lỗi khi lưu phản hồi bot:', botMsgError);
                    // Tin nhắn bot vẫn hiển thị nhưng có thể không được lưu vào DB
                }

                // Nếu tạo conversation mới, cập nhật lại danh sách
                if (isNewConversation) {
                    loadConversations();
                }
            } else {
                // Trường hợp phản hồi rỗng
                setIsTyping(false);
                setCurrentBotMessage(null);
                setMessages(prev => prev.filter(m => m.id !== tempBotMessage.id));
                enqueueSnackbar('Không thể tạo phản hồi từ AI', { variant: 'warning' });
            }
        }
    } catch (error) {
        if (isMounted.current) {
            // Dừng trạng thái typing và xóa tin nhắn tạm khi có lỗi
            setIsTyping(false);
            setCurrentBotMessage(null);
            
            console.error('Lỗi trong quy trình chat:', error);
            
            // Hiển thị thông báo lỗi cụ thể hơn
            const errorMessage = error instanceof Error ? error.message : 'Lỗi không xác định';
            enqueueSnackbar(`Lỗi: ${errorMessage}`, { 
                variant: 'error',
                autoHideDuration: 5000
            });
            
            // Nếu không có conversation ID hợp lệ, tạo mới
            if (!currentConversationId && !conversationId) {
                console.log("Không còn conversation nào, sẽ tạo mới khi gửi tin nhắn tiếp theo");
                enqueueSnackbar('Không có cuộc trò chuyện nào. Gõ tin nhắn để bắt đầu cuộc trò chuyện mới', {
                    variant: 'info',
                    autoHideDuration: 5000
                });
            }
            
            // Lưu message gốc khi có lỗi
            setMessages(prev => prev.filter(m => m.id !== tempBotMessage.id));
            setInput(userInput);
            setChatFiles([...filesToSend]);
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
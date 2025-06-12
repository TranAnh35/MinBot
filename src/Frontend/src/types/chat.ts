import { UploadedFile } from "./interface";

export interface Message {
    id: string;
    content: string;
    sender: 'user' | 'bot' | 'assistant';
    timestamp: Date;
    sequence?: number; // Thêm sequence number để đảm bảo thứ tự
    file?: {
        name: string;
        type: string;
        size: number;
    };
    attachments?: UploadedFile[];
    loading?: boolean;
}

export interface MessageListProps {
    messages: Message[];
    isLoading: boolean;
    currentBotMessage: Message | null;
    displayedContent: string;
    stoppedContent: string | null;
    isTyping: boolean;
    setDisplayedContent: (content: string) => void;
    setIsTyping: (isTyping: boolean) => void;
    onLoadMoreHistory?: () => void;
    hasMoreHistory?: boolean;
    isLoadingMoreHistory?: boolean;
}

export interface MessageContentProps {
    content: string;
    attachments?: UploadedFile[];
    sender?: 'user' | 'bot' | 'assistant'; // Thêm sender để phân biệt cách render
}

export interface FileSelectorProps {
    uploadedFiles: ChatBotProps['uploadedFiles'];
    selectedFiles: ChatBotProps['selectedFiles'];
    onFileSelect: ChatBotProps['onFileSelect'];
    onClose: () => void;
}

export interface ChatBotProps {
    uploadedFiles: UploadedFile[];
    selectedFiles: UploadedFile[];
    onFileSelect: (file: UploadedFile) => void;
    onUploadClick: () => void;
    userId?: string;
    currentConversationId?: string;
    onConversationSelect?: (conversationId: string) => void;
    showConversations?: boolean;
    onCloseConversations?: () => void;
}

export interface FileDropzoneProps {
    chatFiles: File[];
    setChatFiles: (files: File[] | ((prev: File[]) => File[])) => void; // Cập nhật kiểu của setChatFiles
    children: React.ReactNode;
}

export interface ChatInputProps {
    input: string;
    setInput: (input: string) => void;
    isLoading: boolean;
    isTyping: boolean;
    isWebSearchEnabled: boolean;
    chatFiles: File[];
    onSend: () => void;
    onStopTyping: () => void;
    toggleWebSearch: () => void;
    open?: () => void; // Thêm open vào interface
}

export interface GenerateContentRequest {
    input: string; // Nội dung tin nhắn
    files?: File[]; // Danh sách file đính kèm (tùy chọn)
    isWebSearchEnabled?: boolean;
    conversationId?: string; // ID cuộc trò chuyện (nếu có)
}

export interface GenerateContentResponse {
    content: string; // Nội dung phản hồi từ API
    // Thêm các trường khác nếu API trả về thêm dữ liệu
}

export interface Conversation {
    conversation_id: string;
    user_id: string;
    title?: string; // Tiêu đề cuộc trò chuyện
    created_at: string;
    updated_at: string;
    preview?: string;
    messages: Message[];
}

export interface ConversationSidebarProps {
    userId: string;
    conversations: Conversation[];
    currentConversationId?: string;
    onConversationSelect: (conversationId: string) => void;
    onCreateNewConversation: () => void;
    onDeleteConversation: (conversationId: string) => void;
    onRenameConversation?: (conversationId: string, title: string) => void;
    isLoading: boolean;
}
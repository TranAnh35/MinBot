import api from '../libs/axios';
import { GenerateContentResponse } from '../types/api';
import { UploadedFile } from '../types/interface';
import { GenerateContentRequest, Conversation } from '../types/chat';

// Gọi API tạo nội dung từ LLM và RAG
export const generateContent = async (data: GenerateContentRequest): Promise<GenerateContentResponse> => {
  // Lấy thông tin từ RAG (nếu cần)
  const ragResponse = await api.get<{ response: string }>('/rag/query', {
    params: { question: data.input }
  }).catch(() => ({ data: { response: '' } })); // Xử lý lỗi RAG nếu cần

  let fileContents = '';
  if (data.files && data.files.length > 0) {
    // Gửi từng file tới endpoint /read để backend đọc nội dung
    const filePromises = data.files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<{ file_name: string; content: string }>('/files/read', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return `${response.data.file_name}: ${response.data.content}`;
    });
    const fileContentsArray = await Promise.all(filePromises);
    fileContents = fileContentsArray.join('\n');
  }

  let webResponse;
  if (data.isWebSearchEnabled) {
    const webSearchResult = await api.get<{ response: string }>('/web/search', {
      params: { query: data.input }
    }).catch(() => ({ data: { response: '' } }));
    console.log(webSearchResult.data);

    webResponse = await api.post<{ content: string }>('/generate/merge_context', {
      results: webSearchResult.data
    }).catch(() => ({ data: { content: '' } }));

    console.log(webResponse.data);
  }

  // console.log(webResponse.data);

  try {
    // Kiểm tra conversation_id trước khi gửi request
    if (data.conversationId && typeof data.conversationId !== 'string') {
      console.error("Lỗi: conversation_id không hợp lệ:", data.conversationId);
      throw new Error("ID cuộc trò chuyện không hợp lệ");
    }
    
    // Thêm logs để debug
    console.log("Gửi yêu cầu tới LLM API với:", {
      prompt: data.input,
      hasFileContent: !!fileContents,
      hasWebResponse: !!webResponse?.data?.content,
      conversationId: data.conversationId
    });
    
    // Gọi API LLM với prompt bao gồm nội dung file
    const llmResponse = await api.get('/generate/gen_content', {
      params: {
        prompt: data.input,
        rag_response: ragResponse.data.response,
        file_response: fileContents,
        web_response: webResponse?.data.content,
        conversation_id: data.conversationId
      },
    });

    if (!llmResponse?.data?.content) {
      console.warn("Cảnh báo: Phản hồi từ API không có nội dung");
      return { content: "Xin lỗi, tôi không thể tạo phản hồi lúc này. Vui lòng thử lại sau." };
    }

    return { content: llmResponse.data.content };
  } catch (error) {
    console.error("Lỗi khi gọi API generateContent:", error);
    throw error; // Ném lỗi để xử lý ở component
  }
};

// Gọi API lấy danh sách file đã upload
export const fetchFiles = async (): Promise<UploadedFile[]> => {
  const response = await api.get<{ files: UploadedFile[] }>("/files/files");
  return response.data.files;
};

// Upload file lên server
export const uploadFile = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append("file", file);

  await api.post("/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  // Sau khi upload, đồng bộ vào vector database
  await api.post("/rag/sync-files");
};

// Xóa file khỏi server
export const deleteFile = async (filename: string): Promise<void> => {
  const encodedFilename = encodeURIComponent(filename);
  await api.delete(`/files/delete/${encodedFilename}`);
  await api.post("/rag/sync-files");
};

export const setApiKey = async (apiKey: string): Promise<string> => {
  const response = await api.post<{ message: string }>("/api/set_api_key", apiKey, {
    headers: { "Content-Type": "text/plain" }
  });
  return response.data.message;
};

export const validateApiKey = async (apiKey: string): Promise<boolean> => {
  try {
    // Giả sử bạn thêm một endpoint mới để kiểm tra
    const response = await api.post<{ valid: boolean }>("/api/validate_api_key", apiKey, {
      headers: { "Content-Type": "text/plain" }
    });
    return response.data.valid;
  } catch (error) {
    console.error("API key validation failed:", error);
    return false;
  }
};

// Conversation API methods
export const createConversation = async (userId: string): Promise<string> => {
  const response = await api.post<{ conversation_id: string }>('/conversations/create', {
    user_id: userId
  });
  return response.data.conversation_id;
};

export const getConversationHistory = async (conversationId: string, limit: number = 50, offset: number = 0): Promise<any> => {
  const response = await api.get(`/conversations/${conversationId}/history`, {
    params: { limit, offset },
  });
  return response.data;
};

export const listUserConversations = async (userId: string): Promise<Conversation[]> => {
  const response = await api.get<{ conversations: Conversation[] }>(`/conversations/user/${userId}`);
  return response.data.conversations;
};

export const deleteConversation = async (conversationId: string): Promise<boolean> => {
  const response = await api.delete<{ success: boolean }>(`/conversations/${conversationId}`);
  return response.data.success;
};

export const renameConversation = async (conversationId: string, title: string): Promise<boolean> => {
  const response = await api.post<{ success: boolean }>('/conversations/rename', {
    conversation_id: conversationId,
    title: title
  });
  return response.data.success;
};

// Thêm message vào conversation với validation ở backend
export const addMessage = async (conversationId: string, role: string, content: string, attachments?: any[]): Promise<any> => {
  // Kiểm tra conversationId
  if (!conversationId) {
    console.error("Lỗi: Không có conversation_id khi gọi addMessage");
    throw new Error("Không có conversation_id hợp lệ");
  }
  
  try {
    const response = await api.post('/conversations/message', {
      conversation_id: conversationId,
      role: role,
      content: content,
      attachments: attachments,
    });
    return response.data;
  } catch (error: any) {
    console.error(`Lỗi khi thêm message ${role} vào conversation ${conversationId}:`, error);
    
    // Xử lý lỗi chi tiết và throw lỗi có thông tin rõ ràng hơn
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || 'Lỗi không xác định';
      throw new Error(`Lỗi ${status}: ${detail}`);
    }
    
    throw error; // Throw error ban đầu nếu không có response
  }
};

// Lấy tóm tắt conversation
export const getConversationSummary = async (conversationId: string): Promise<any> => {
  const response = await api.get(`/conversations/${conversationId}/summary`);
  return response.data;
};

// Refresh conversation data (để sync với database)
export const refreshConversation = async (conversationId: string): Promise<any> => {
  const response = await api.get(`/conversations/${conversationId}`);
  return response.data;
};
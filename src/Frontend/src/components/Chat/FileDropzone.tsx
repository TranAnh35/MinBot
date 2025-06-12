// FileDropzone.tsx
import React, { useCallback, ReactElement } from 'react';
import { useDropzone } from 'react-dropzone';
import { X } from 'lucide-react';
import { FileDropzoneProps, ChatInputProps } from '../../types/chat';

const FileDropzone: React.FC<FileDropzoneProps> = ({ chatFiles, setChatFiles, children }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setChatFiles((prev: File[]) => {
      const newFiles = acceptedFiles.filter((newFile) =>
        !prev.some((existingFile) => existingFile.name === newFile.name && existingFile.size === newFile.size)
      );
      return [...prev, ...newFiles];
    });
  }, [setChatFiles]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    noClick: true,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt', '.md'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'application/x-yaml': ['.yaml'],
    },
  });

  const removeFile = (index: number) => {
    setChatFiles((prev: File[]) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4" {...getRootProps()}>
      <input {...getInputProps()} />
      <div className="flex flex-col space-y-2 max-w-4xl mx-auto">
        {chatFiles.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {chatFiles.map((file, index) => (
              <div
                key={index}
                className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm flex items-center space-x-1"
              >
                <span className="truncate max-w-xs">{file.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="hover:text-blue-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div
          className={`flex items-center space-x-2 rounded-xl p-2 border transition-colors duration-200 ${
            isDragActive ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 border-gray-200'
          }`}
        >
          {React.Children.map(children, (child) =>
            React.isValidElement(child)
              ? React.cloneElement(child as ReactElement<ChatInputProps>, { open }) // Ép kiểu child
              : child
          )}
        </div>
      </div>
    </div>
  );
};

export default FileDropzone;
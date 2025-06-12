import React from 'react';
import { Button } from '../ui/button';
import { FileSelectorProps } from '../../types/chat';
import { X } from 'lucide-react';

const FileSelector: React.FC<FileSelectorProps> = ({ uploadedFiles, selectedFiles, onFileSelect, onClose }) => {
  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold">Select Files</h3>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
        {uploadedFiles.map((file) => (
          <div
            key={file.id}
            className={`p-2 rounded cursor-pointer ${
              selectedFiles.some((f) => f.id === file.id)
                ? 'bg-blue-100'
                : 'bg-gray-50 hover:bg-gray-100'
            }`}
            onClick={() => onFileSelect(file)}
          >
            <p className="text-sm truncate">{file.name}</p>
            <p className="text-xs text-gray-500">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileSelector;
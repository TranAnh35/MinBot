import React, { useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Trash2, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { fetchFiles, uploadFile, deleteFile } from '../services/api';
import { UploadedFile, DocumentUploaderProps } from '../types/interface';

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ onClose }) => {
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

    useEffect(() => {
        loadFiles();
    }, []);

    const loadFiles = async () => {
        const files = await fetchFiles();
        setUploadedFiles(files);
    };

    const handleUpload = async (files: File[]) => {
        await uploadFile(files[0]);
        loadFiles();
    };

    const handleDelete = async (filename: string) => {
        await deleteFile(filename);
        loadFiles();
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: handleUpload,
        accept: {
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/x-yaml': ['.yaml']
        },
    });

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white rounded-xl w-full max-w-4xl mx-4 overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-800">Upload Documents</h2>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                <div className="flex h-[600px]">
                    {/* Main upload area */}
                    <div className="flex-1 p-6">
                        <div
                            {...getRootProps()}
                            className={`
                h-full
                border-2 
                border-dashed 
                border-gray-200
                rounded-xl 
                flex 
                flex-col 
                items-center 
                justify-center 
                transition-colors
                ${isDragActive
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                                }
              `}
                        >
                            <input {...getInputProps()} />
                            <div className="p-8 text-center">
                                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                                    <Upload className="h-8 w-8 text-gray-400" />
                                </div>
                                <h3 className="text-lg font-semibold mb-2">
                                    {isDragActive ? 'Drop files here' : 'Upload your files'}
                                </h3>
                                <p className="text-sm text-gray-500 mb-4">
                                    Drag and drop your files here, or click to select files
                                </p>
                                <Button variant="outline" className="mx-auto">
                                    <FileText className="mr-2 h-4 w-4" />
                                    Browse Files
                                </Button>
                                <p className="mt-4 text-xs text-gray-400">
                                    Supported formats: PDF, TXT, DOC, DOCX
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="w-80 border-l border-gray-200 bg-gray-50">
                        <div className="p-4">
                            <h3 className="font-semibold text-gray-700 mb-3">Uploaded Files</h3>
                            <div className="space-y-2">
                                {uploadedFiles.length === 0 ? (
                                    <p className="text-sm text-gray-500 text-center py-4">
                                        No files uploaded yet
                                    </p>
                                ) : (
                                    uploadedFiles.map((file) => (
                                        <div
                                            key={file.name}
                                            className="bg-white rounded-lg p-3 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow"
                                        >
                                            <div className="flex items-center space-x-3">
                                                <FileText className="h-5 w-5 text-blue-500" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-gray-700 truncate">
                                                        {file.name}
                                                    </p>
                                                    <p className="text-xs text-gray-500">
                                                        {(file.size / 1024).toFixed(1)} KB
                                                    </p>
                                                </div>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleDelete(file.name)}
                                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <Trash2 className="h-4 w-4 text-red-500" />
                                            </Button>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
export interface UploadedFile {
    id: string;
    name: string;
    size: number;
}

export interface DocumentUploaderProps {
    onClose: () => void;
}
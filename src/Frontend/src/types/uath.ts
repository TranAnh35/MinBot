export interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    apiKey: string;
    onSaveApiKey: (apiKey: string) => void;
}
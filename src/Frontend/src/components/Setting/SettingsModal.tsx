import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Check } from 'lucide-react';
import { Button } from '../ui/button';
import { setApiKey, validateApiKey } from '../../services/api';
import { SettingsModalProps } from '../../types/uath';
import { useSnackbar } from 'notistack';

export const SettingsModal: React.FC<SettingsModalProps> = ({
    isOpen,
    onClose,
    apiKey,
}) => {
    const [newApiKey, setNewApiKey] = useState(apiKey);
    const [error, setError] = useState<string | null>(null);
    const [isValidating, setIsValidating] = useState(false);
    const [isValid, setIsValid] = useState<boolean | null>(null);
    const { enqueueSnackbar } = useSnackbar();

    const handleCheck = async () => {
        if (!newApiKey.trim()) {
            enqueueSnackbar("API key cannot be empty", { variant: "error", autoHideDuration: 3000 });
            return;
        }

        setIsValidating(true);
        setIsValid(null);

        try {
            const valid = await validateApiKey(newApiKey);
            setIsValid(valid);

            if (valid) {
                enqueueSnackbar("API key is valid", { variant: "success", autoHideDuration: 3000 });
            } else {
                enqueueSnackbar("API key is invalid. Please check and try again.", { variant: "error", autoHideDuration: 3000 });
            }
        } catch (err) {
            enqueueSnackbar("Failed to validate API key", { variant: "error", autoHideDuration: 3000 });
            setIsValid(false);
        } finally {
            setIsValidating(false);
        }
    };

    const handleSave = async () => {
        setError(null); // Reset lỗi trước khi kiểm tra
        const isValid = await validateApiKey(newApiKey);
        if (isValid) {
            try {
                const message = await setApiKey(newApiKey);
                enqueueSnackbar(`API key saved successfully, ${message}`, { variant: "success", autoHideDuration: 3000 });
                onClose(); // Đóng modal nếu lưu thành công
            } catch (err) {
                enqueueSnackbar("Không lưu được khóa API", { variant: "error", autoHideDuration: 3000 });
            }
        } else {
            enqueueSnackbar("Khóa API không hợp lệ. Vui lòng kiểm tra và thử lại.", { variant: "error", autoHideDuration: 3000 });
        }
    };

    const handleOpenChange = (open: boolean) => {
        if (open === false) {
            return;
        }
        onClose();
    };

    return (
        <Dialog.Root open={isOpen} onOpenChange={handleOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
                <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
                    <div className="flex justify-between items-center mb-4">
                        <Dialog.Title className="text-xl font-semibold">Settings</Dialog.Title>
                        <Dialog.Close asChild>
                            <Button variant="ghost" size="icon">
                                <X className="h-4 w-4" onClick={onClose} />
                            </Button>
                        </Dialog.Close>
                    </div>

                    {/* Thêm Description */}
                    <Dialog.Description className="text-sm text-gray-500 mb-4">
                        {/* Update your API key settings below. */}
                    </Dialog.Description>

                    <div className="space-y-4">
                        <div>
                            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">
                                API Key
                            </label>
                            <div className="flex space-x-2">
                                <input
                                    id="apiKey"
                                    type="password"
                                    value={newApiKey}
                                    onChange={(e) => {
                                        setNewApiKey(e.target.value);
                                        setIsValid(null); // Reset validation state when input changes
                                    }}
                                    className={`flex-1 px-3 py-2 border ${isValid === true ? 'border-green-500' :
                                            isValid === false ? 'border-red-500' :
                                                'border-gray-300'
                                        } rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                                    placeholder="Enter your API key"
                                />
                                <Button
                                    onClick={handleCheck}
                                    disabled={isValidating}
                                    className="whitespace-nowrap"
                                    variant="outline"
                                >
                                    {isValidating ? 'Checking...' : 'Check'}
                                </Button>
                            </div>
                            <p className="mt-1 text-sm text-gray-500">
                                Your API key is stored securely in local storage
                            </p>
                            {isValid === true && (
                                <p className="mt-1 text-sm text-green-500 flex items-center">
                                    <Check className="h-4 w-4 mr-1" /> API key is valid
                                </p>
                            )}
                            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
                        </div>

                        <div className="flex justify-end space-x-2 mt-6">
                            <Button variant="outline" onClick={onClose}>
                                Cancel
                            </Button>
                            <Button onClick={handleSave}>
                                Save Changes
                            </Button>
                        </div>
                    </div>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
};
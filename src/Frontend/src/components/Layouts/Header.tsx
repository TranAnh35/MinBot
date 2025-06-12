// components/Header.tsx
import React from 'react';
import { Menu, Upload, Settings } from 'lucide-react';
import { Button } from '../ui/button';

interface HeaderProps {
    onUploadClick: () => void;
    onSettingsClick: () => void;
    onConversationsClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onUploadClick, onSettingsClick, onConversationsClick }) => {
    return (
        <header className="bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <Button variant="ghost" size="icon" onClick={onConversationsClick}>
                        <Menu className="h-6 w-6" />
                    </Button>
                    <h1 className="text-xl font-semibold">MinBot</h1>
                </div>

                <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="icon" onClick={onUploadClick}>
                        <Upload className="h-5 w-5" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={onSettingsClick}>
                        <Settings className="h-5 w-5" />
                    </Button>
                </div>
            </div>
        </header>
    );
}
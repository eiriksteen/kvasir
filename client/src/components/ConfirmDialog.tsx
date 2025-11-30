'use client';

import React, { useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({
    isOpen,
    title,
    message,
    confirmText = 'Delete',
    cancelText = 'Cancel',
    onConfirm,
    onCancel
}: ConfirmDialogProps) {
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onCancel();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onCancel]);

    if (!isOpen) return null;

    return (
        <div 
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={onCancel}
        >
            <div 
                className="bg-white border border-gray-300 rounded-lg shadow-lg max-w-md w-full mx-4"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="p-6">
                    <div className="flex items-start gap-4 mb-4">
                        <div className="flex-shrink-0">
                            <AlertTriangle size={20} className="text-red-600" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-sm font-mono text-gray-900 mb-1">{title}</h3>
                            <p className="text-xs text-gray-600 font-mono">{message}</p>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
                        <button
                            onClick={onCancel}
                            className="px-3 py-1.5 text-xs font-mono text-gray-700 hover:bg-gray-100 rounded transition-colors"
                        >
                            {cancelText}
                        </button>
                        <button
                            onClick={onConfirm}
                            className="px-3 py-1.5 text-xs font-mono text-white bg-red-600 hover:bg-red-700 rounded transition-colors"
                        >
                            {confirmText}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

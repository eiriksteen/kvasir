'use client';

import { useState, useEffect } from 'react';
import { useTables } from '@/hooks/useTables';
import { UUID } from 'crypto';
import { BaseTable, TableConfig, TableColumn } from '@/types/tables';
import ConfirmationPopup from '@/components/ConfirmationPopup';

interface TableConfigurationPopupProps {
    isOpen: boolean;
    onClose: () => void;
    availableColumns: string[];
    analysisResultId: UUID;
    table?: BaseTable;
}

export default function TableConfigurationPopup({ isOpen, onClose, availableColumns, analysisResultId, table }: TableConfigurationPopupProps) {
    const [activeTab, setActiveTab] = useState<'data' | 'metadata' | 'display'>('data');
    const [title, setTitle] = useState('');
    const [subtitle, setSubtitle] = useState('');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [columnUnits, setColumnUnits] = useState<Record<string, string | null>>({});
    const [columnSignificantDigits, setColumnSignificantDigits] = useState<Record<string, number | null>>({});
    const [showRowNumbers, setShowRowNumbers] = useState(true);
    const [maxRows, setMaxRows] = useState<number | null>(null);
    const [sortBy, setSortBy] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(null);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    
    const { createTable, updateTable, deleteTable } = useTables(analysisResultId);

    useEffect(() => {
        if (availableColumns.length > 0 && selectedColumns.length === 0) {
            // Initialize with all columns selected by default
            setSelectedColumns(availableColumns);
            // Initialize column units and significant digits
            const initialUnits: Record<string, string | null> = {};
            const initialSignificantDigits: Record<string, number | null> = {};
            availableColumns.forEach(column => {
                initialUnits[column] = null;
                initialSignificantDigits[column] = null;
            });
            setColumnUnits(initialUnits);
            setColumnSignificantDigits(initialSignificantDigits);
        }
    }, [availableColumns]);

    // Populate form fields when editing an existing table
    useEffect(() => {
        if (table && table.tableConfig) {
            const config = table.tableConfig;
            setTitle(config.title || '');
            setSubtitle(config.subtitle || '');
            
            // Set selected columns and their units from the table config
            const columns = config.columns || [];
            setSelectedColumns(columns.map(col => col.name));
            
            const units: Record<string, string | null> = {};
            const significantDigits: Record<string, number | null> = {};
            columns.forEach(col => {
                units[col.name] = col.unit || null;
                significantDigits[col.name] = col.numberOfSignificantDigits || null;
            });
            setColumnUnits(units);
            setColumnSignificantDigits(significantDigits);
            
            setShowRowNumbers(config.showRowNumbers !== undefined ? config.showRowNumbers : true);
            setMaxRows(config.maxRows);
            setSortBy(config.sortBy);
            setSortOrder(config.sortOrder);
        }
    }, [table]);

    const handleConfirm = () => {
        const tableColumns = selectedColumns.map(columnName => ({
            name: columnName,
            unit: columnUnits[columnName] || null,
            numberOfSignificantDigits: columnSignificantDigits[columnName] || null
        }));
        
        const tableConfig: TableConfig = {
            title: title,
            subtitle: subtitle,
            columns: tableColumns,
            showRowNumbers: showRowNumbers,
            maxRows: maxRows,
            sortBy: sortBy,
            sortOrder: sortOrder,
        };
        
        if (table) {
            updateTable({
                tableId: table.id,
                tableUpdate: {
                    id: table.id,
                    tableConfig: tableConfig
                }
            });
        } else {
            createTable({
                tableCreate: {
                    analysisResultId: analysisResultId,
                    tableConfig: tableConfig
                }
            });
        }
        onClose();
    };

    const toggleColumnSelection = (columnName: string) => {
        setSelectedColumns(prev => 
            prev.includes(columnName) 
                ? prev.filter(col => col !== columnName)
                : [...prev, columnName]
        );
    };

    const updateColumnUnit = (columnName: string, unit: string | null) => {
        setColumnUnits(prev => ({
            ...prev,
            [columnName]: unit
        }));
    };

    const updateColumnSignificantDigits = (columnName: string, significantDigits: number | null) => {
        setColumnSignificantDigits(prev => ({
            ...prev,
            [columnName]: significantDigits
        }));
    };

    const handleDeleteTable = () => {
        setShowDeleteConfirmation(true);
    };

    const confirmDeleteTable = () => {
        if (table) {
            deleteTable({
                tableId: table.id
            });
            setShowDeleteConfirmation(false);
            onClose();
        }
    };

    const cancelDeleteTable = () => {
        setShowDeleteConfirmation(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 w-[600px] max-w-[95vw] max-h-[90vh] overflow-y-auto border border-gray-300">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Configure Table</h3>
                
                {/* Tab Navigation */}
                <div className="flex border-b border-gray-300 mb-6">
                    <button
                        onClick={() => setActiveTab('data')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'data'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Data
                    </button>
                    <button
                        onClick={() => setActiveTab('metadata')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'metadata'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Metadata
                    </button>
                    <button
                        onClick={() => setActiveTab('display')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'display'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Display
                    </button>
                </div>

                <div className="space-y-6">
                    {activeTab === 'metadata' && (
                        <div className="space-y-6">
                            {/* Title and Subtitle */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Table Title
                                </label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                    placeholder="Enter table title"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Subtitle
                                </label>
                                <input
                                    type="text"
                                    value={subtitle}
                                    onChange={(e) => setSubtitle(e.target.value)}
                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                    placeholder="Enter subtitle (optional)"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'data' && (
                        <div className="space-y-6">
                            {/* Table Columns */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-3">
                                    Select Columns to Include
                                </label>
                                
                                <div className="space-y-3 max-h-48 overflow-y-auto">
                                    {availableColumns.map((columnName: string) => (
                                        <div key={columnName} className="flex items-center gap-3 p-3 bg-gray-100 rounded border border-gray-300">
                                            <input
                                                type="checkbox"
                                                checked={selectedColumns.includes(columnName)}
                                                onChange={() => toggleColumnSelection(columnName)}
                                                className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                            />
                                            
                                            <span className="flex-1 text-gray-900 font-medium">
                                                {columnName}
                                            </span>
                                            
                                            <input
                                                type="text"
                                                value={columnUnits[columnName] || ''}
                                                onChange={(e) => updateColumnUnit(columnName, e.target.value || null)}
                                                className="w-20 bg-white border border-gray-300 rounded px-2 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#0E4F70]"
                                                placeholder="Unit"
                                                disabled={!selectedColumns.includes(columnName)}
                                            />
                                            
                                            <input
                                                type="number"
                                                value={columnSignificantDigits[columnName] || ''}
                                                onChange={(e) => updateColumnSignificantDigits(columnName, e.target.value ? parseInt(e.target.value) : null)}
                                                className="w-16 bg-white border border-gray-300 rounded px-2 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#0E4F70]"
                                                placeholder="Sig"
                                                min="1"
                                                max="15"
                                                disabled={!selectedColumns.includes(columnName)}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'display' && (
                        <div className="space-y-6">
                            {/* Display Options */}
                            <div>
                                <div className="flex items-center gap-3 mb-4">
                                    <input
                                        type="checkbox"
                                        checked={showRowNumbers}
                                        onChange={(e) => setShowRowNumbers(e.target.checked)}
                                        className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Show Row Numbers</span>
                                </div>
                                
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Maximum Rows (leave empty for all)
                                    </label>
                                    <input
                                        type="number"
                                        value={maxRows || ''}
                                        onChange={(e) => setMaxRows(e.target.value ? parseInt(e.target.value) : null)}
                                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                        placeholder="Maximum number of rows to display"
                                        min="1"
                                    />
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Sort By Column
                                        </label>
                                        <select
                                            value={sortBy || ''}
                                            onChange={(e) => setSortBy(e.target.value || null)}
                                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                        >
                                            <option value="">No sorting</option>
                                            {selectedColumns.map((columnName) => (
                                                <option key={columnName} value={columnName}>
                                                    {columnName}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Sort Order
                                        </label>
                                        <select
                                            value={sortOrder || ''}
                                            onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc' | null || null)}
                                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                            disabled={!sortBy}
                                        >
                                            <option value="">Select order</option>
                                            <option value="asc">Ascending</option>
                                            <option value="desc">Descending</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-gray-300">
                    {table && (
                        <button
                            onClick={handleDeleteTable}
                            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            Delete Table
                        </button>
                    )}
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={!title || selectedColumns.length === 0}
                        className="px-4 py-2 bg-[#0E4F70] text-white rounded hover:bg-[#0E4F70]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {table ? 'Update Table' : 'Create Table'}
                    </button>
                </div>
            </div>
            
            <ConfirmationPopup
                message="Are you sure you want to delete this table? This action cannot be undone."
                onConfirm={confirmDeleteTable}
                onCancel={cancelDeleteTable}
                isOpen={showDeleteConfirmation}
            />
        </div>
    );
}
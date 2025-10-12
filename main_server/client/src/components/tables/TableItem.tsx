'use client';

import React, { useState, useMemo } from 'react';
import { BaseTable, TableConfig } from '@/types/tables';
import { AggregationObjectWithRawData } from '@/types/data-objects';
import TableConfigurationPopup from '@/components/info-modals/analysis/TableConfigurationPopup';
import { Settings, Trash2, Download } from 'lucide-react';
import { UUID } from 'crypto';
import { downloadAggregationDataAsExcel } from '@/lib/utils';

interface TablesItemProps {
  table: BaseTable;
  aggregationData: AggregationObjectWithRawData;
  analysisResultId: UUID;
  onDelete: (tableId: string) => void;
  onUpdate: (tableId: string, tableUpdate: any) => void;
}

// Helper function to format numbers with significant digits
const formatNumberWithSignificantDigits = (value: any, significantDigits: number | null): string => {
  if (value === null || value === undefined || value === '') {
    return '-';
  }
  
  // If it's not a number, return as string
  if (typeof value !== 'number') {
    return String(value);
  }
  
  // If no significant digits specified, return as is
  if (!significantDigits) {
    return String(value);
  }
  
  // Format with significant digits
  return value.toPrecision(significantDigits);
};


const TableItem = ({ table, aggregationData, analysisResultId, onDelete, onUpdate }: TablesItemProps) => {
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  
  // Get table configuration from the table object
  const tableConfig: TableConfig = table.tableConfig;

  // Handle data availability check
  const hasData = aggregationData && aggregationData.data.outputData.data && Object.keys(aggregationData.data.outputData.data).length > 0;
  
  if (!hasData) {
    return (
      <div className="w-full h-32 flex items-center justify-center text-zinc-500 bg-[#1a1625] rounded border border-[#271a30]">
        No data available for table
      </div>
    );
  }

  const data = aggregationData.data.outputData.data as Record<`${string},${string}`, Array<number | string | boolean | Date | null>>;

  // Get available columns from AggregationObjectWithRawData
  const availableColumns = Object.keys(data).map(key => key.split(',')[0]);

  // Prepare table data
  if (!tableConfig.columns || tableConfig.columns.length === 0) return [];

  // Get data for each column
  const rows: any[] = [];
  const firstColumnKey = Object.keys(data).find(key => key.startsWith(tableConfig.columns[0].name + ','));
  const firstColumnData = firstColumnKey ? data[firstColumnKey as keyof typeof data] || [] : [];
  
  // Create rows based on the first column's data length
  for (let i = 0; i < firstColumnData.length; i++) {
    const row: any = {};
    
    tableConfig.columns.forEach(column => {
      const columnKey = Object.keys(data).find(key => key.startsWith(column.name + ','));
      const columnData = columnKey ? data[columnKey as keyof typeof data] || [] : [];
      row[column.name] = columnData[i] || '';
    });
    
    rows.push(row);
  }

  // Apply sorting if configured
  if (tableConfig.sortBy && tableConfig.sortOrder) {
    rows.sort((a, b) => {
      const aVal = a[tableConfig.sortBy!];
      const bVal = b[tableConfig.sortBy!];
      
      if (tableConfig.sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  }

  // Apply max rows limit
  if (tableConfig.maxRows) {
    rows.splice(tableConfig.maxRows);
  }

  const tableData = rows;

  const handleDelete = () => {
    setShowDeleteConfirmation(true);
  };

  const confirmDelete = () => {
    onDelete(table.id);
    setShowDeleteConfirmation(false);
  };

  const cancelDelete = () => {
    setShowDeleteConfirmation(false);
  };

  const handleDownloadExcel = () => {
    const filename = tableConfig.title || aggregationData.name || 'table_data';
    downloadAggregationDataAsExcel(aggregationData, filename);
  };

  return (
    <div className="w-full">
      {/* Table Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-medium text-white">{tableConfig.title}</h4>
          {tableConfig.subtitle && (
            <p className="text-xs text-zinc-400 mt-1">{tableConfig.subtitle}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadExcel}
            className="p-1 rounded transition-colors text-gray-400 hover:text-gray-200"
            title="Download as Excel"
          >
            <Download size={14} />
          </button>
          <button
            onClick={() => setIsConfigOpen(true)}
            className="p-1 rounded transition-colors text-gray-400 hover:text-gray-200"
            title="Configure table"
          >
            <Settings size={14} />
          </button>
          <button
            onClick={handleDelete}
            className="p-1 rounded transition-colors text-red-300 hover:text-white"
            title="Delete table"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1625] rounded border border-[#271a30] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-[#271a30]">
                {tableConfig.showRowNumbers && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-zinc-300 border-r border-[#3a2a4a]">
                    #
                  </th>
                )}
                {tableConfig.columns.map((column, index) => (
                  <th key={index} className="px-3 py-2 text-left text-xs font-medium text-zinc-300 border-r border-[#3a2a4a] last:border-r-0">
                    <div className="flex flex-col">
                      <span>{column.name}</span>
                      {column.unit && (
                        <span className="text-xs text-zinc-500">({column.unit})</span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b border-[#3a2a4a] last:border-b-0 hover:bg-[#2a1a3a] transition-colors">
                  {tableConfig.showRowNumbers && (
                    <td className="px-3 py-2 text-xs text-zinc-400 border-r border-[#3a2a4a]">
                      {rowIndex + 1}
                    </td>
                  )}
                  {tableConfig.columns.map((column, index) => (
                    <td key={index} className="px-3 py-2 text-xs text-white border-r border-[#3a2a4a] last:border-r-0">
                      {formatNumberWithSignificantDigits(row[column.name], column.numberOfSignificantDigits || null)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Table Footer */}
        <div className="px-3 py-2 bg-[#271a30] text-xs text-zinc-400 border-t border-[#3a2a4a]">
          Showing {tableData.length} rows
          {tableConfig.maxRows && ` (limited to ${tableConfig.maxRows})`}
          {tableConfig.sortBy && tableConfig.sortOrder && ` • Sorted by ${tableConfig.sortBy} (${tableConfig.sortOrder})`}
        </div>
      </div>

      {/* Table Configuration Popup */}
      <TableConfigurationPopup
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        availableColumns={availableColumns}
        analysisResultId={analysisResultId}
        table={table}
      />

      {/* Delete Confirmation Popup */}
      {showDeleteConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[#0a101c] rounded-lg p-6 w-96 max-w-[95vw] border border-[#271a30]">
            <h3 className="text-lg font-semibold text-white mb-4">Delete Table</h3>
            <p className="text-sm text-zinc-300 mb-6">
              Are you sure you want to delete this table? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={cancelDelete}
                className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableItem;
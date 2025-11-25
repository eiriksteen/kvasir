'use client';

import { useState, useEffect } from 'react';
import { X, FileText, Code, Download } from 'lucide-react';
import { Analysis } from '@/types/ontology/analysis';
import { UUID } from 'crypto';

interface GenerateReportPopupProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: Analysis;
  projectId: UUID;
}

export default function GenerateReportPopup({
  isOpen,
  onClose,
  analysis,
}: GenerateReportPopupProps) {
  const [filename, setFilename] = useState(analysis.name);
  const [includeCode, setIncludeCode] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // TODO: Implement generateReport function
  const generateReport = async (args: unknown) => {
    console.log('Generate report:', args);
  };

  // Reset form when popup opens
  useEffect(() => {
    if (isOpen) {
      setFilename(analysis.name);
      setIncludeCode(true);
      setIsGeneratingReport(false);
    }
  }, [isOpen, analysis.name]);

  // Handle escape key to close popup
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!filename.trim()) return;
    
    setIsGeneratingReport(true);
    try {
      await generateReport({
        analysisObjectId: analysis.id,
        generateReportRequest: {
          filename: filename.trim(),
          includeCode: includeCode
        }
      });
      onClose();
    } catch (error) {
      console.error('Error generating report:', error);
      // TODO: Add error handling UI
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white border border-gray-300 rounded-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#0E4F70]/20 rounded-lg">
              <FileText size={20} className="text-[#0E4F70]" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">Generate Report</h3>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900 transition-colors p-1 rounded-lg hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Filename Input */}
          <div className="space-y-2">
            <label htmlFor="filename" className="block text-sm font-medium text-gray-700">
              Report Filename
            </label>
            <input
              type="text"
              id="filename"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="Enter report filename..."
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70] focus:border-[#0E4F70] transition-colors"
              required
              disabled={isGeneratingReport}
            />
            <p className="text-xs text-gray-500">
              The report will be saved with this filename
            </p>
          </div>

          {/* Include Code Toggle */}
          <div className="flex items-center justify-between p-3 bg-gray-100 border border-gray-300 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-1.5 bg-blue-500/20 rounded-lg">
                <Code size={16} className="text-blue-600" />
              </div>
              <div>
                <label htmlFor="includeCode" className="block text-sm font-medium text-gray-700">
                  Include Python Code
                </label>
                <p className="text-xs text-gray-500">
                  Include the generated Python code in the report
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="includeCode"
                checked={includeCode}
                onChange={(e) => setIncludeCode(e.target.checked)}
                className="sr-only peer"
                disabled={isGeneratingReport}
              />
              <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0E4F70] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0E4F70] disabled:opacity-50"></div>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isGeneratingReport}
              className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!filename.trim() || isGeneratingReport}
              className="px-4 py-2 rounded-lg bg-[#0E4F70] text-white hover:bg-[#0E4F70]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isGeneratingReport ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Download size={16} />
                  Generate Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
import { NotebookSection, AnalysisResult } from '@/types/analysis';
import { UUID } from 'crypto';
import { AggregationObjectWithRawData } from '@/types/data-objects';
import * as XLSX from 'xlsx';

export const getStatusColor = (status: string) => {
	switch(status) {
		case 'running': return 'text-yellow-400';
		case 'failed': return 'text-red-400';
		case 'completed': return 'text-green-400';
		case 'paused': return 'text-blue-400';
		case 'awaiting_approval': return 'text-green-200';
		default: return 'text-gray-400';
	}
};


export const formatDate = (dateString: string) => {
	return new Date(dateString).toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit',
	});
};

// Convert snake_case to camelCase
const snakeToCamel = (str: string): string => {
	return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

// Convert camelCase to snake_case
const camelToSnake = (str: string): string => {
	return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
};

// Recursively convert object keys from snake_case to camelCase
export const snakeToCamelKeys = <T>(obj: T): T => {
	if (obj === null || obj === undefined) {
		return obj;
	}

	if (Array.isArray(obj)) {
		return obj.map(snakeToCamelKeys) as T;
	}

	if (typeof obj === 'object' && obj.constructor === Object) {
		const result: Record<string, unknown> = {};
		for (const [key, value] of Object.entries(obj)) {
			const camelKey = snakeToCamel(key);
			result[camelKey] = snakeToCamelKeys(value);
		}
		return result as T;
	}

	return obj;
};

// Recursively convert object keys from camelCase to snake_case
export const camelToSnakeKeys = <T>(obj: T): T => {
	if (obj === null || obj === undefined) {
		return obj;
	}

	if (Array.isArray(obj)) {
		return obj.map(camelToSnakeKeys) as T;
	}

	if (typeof obj === 'object' && obj.constructor === Object) {
		const result: Record<string, unknown> = {};
		for (const [key, value] of Object.entries(obj)) {
			const snakeKey = camelToSnake(key);
			result[snakeKey] = camelToSnakeKeys(value);
		}
		return result as T;
	}

	return obj;
};


// Utility function to build ordered list from nextType/nextId chain
export const buildOrderedList = (
	sections: NotebookSection[],
	results: AnalysisResult[],
	firstId: UUID | null,
	firstType: 'analysis_result' | 'notebook_section' | null
  ): (NotebookSection | AnalysisResult)[] => {
	const orderedList: (NotebookSection | AnalysisResult)[] = [];
	const sectionsMap = new Map(sections.map(s => [s.id, s]));
	const resultsMap = new Map(results.map(r => [r.id, r]));
	
	let currentId = firstId;
	let currentType = firstType;
	
	while (currentId && currentType) {
	  if (currentType === 'notebook_section') {
		const section = sectionsMap.get(currentId);
		if (section) {
		  orderedList.push(section);
		  currentId = section.nextId;
		  currentType = section.nextType;
		} else {
		  break;
		}
	  } else if (currentType === 'analysis_result') {
		const result = resultsMap.get(currentId);
		if (result) {
		  orderedList.push(result);
		  currentId = result.nextId;
		  currentType = result.nextType;
		} else {
		  break;
		}
	  } else {
		break;
	  }
	}
	
	return orderedList;
  };
  
  // Overloaded version for sections only (used by TableOfContents)
  export const buildOrderedSectionsList = (
	sections: NotebookSection[],
	results: AnalysisResult[],
	firstId: UUID | null,
	firstType: 'notebook_section' | 'analysis_result' 
  ): NotebookSection[] => {
	const orderedList = buildOrderedList(sections, results, firstId, firstType) as (NotebookSection | AnalysisResult)[];
	const filteredList = orderedList.filter(item => 'sectionName' in item) as NotebookSection[];
	return filteredList;
  };
  
  // Function to find all parent sections of a given section
  export const findParentSections = (targetSectionId: string, sections: NotebookSection[]): string[] => {
	const parentIds: string[] = [];
	
	const findParent = (sections: NotebookSection[], targetId: string, currentPath: string[] = []): boolean => {
	  for (const section of sections) {
		const newPath = [...currentPath, section.id];
		
		if (section.id === targetId) {
		  parentIds.push(...currentPath);
		  return true;
		}
		
		if (section.notebookSections && findParent(section.notebookSections, targetId, newPath)) {
		  return true;
		}
	  }
	  return false;
	};
	
	findParent(sections, targetSectionId);
	return parentIds;
  };
  
  // Function to convert AggregationObjectWithRawData to Excel file
  export const downloadAggregationDataAsExcel = (
	aggregationData: AggregationObjectWithRawData,
	filename: string
  ) => {
	const rawData = aggregationData.data.outputData.data;
	
	// Get all unique column names (first part before comma)
	const columnNames = [...new Set(Object.keys(rawData).map(key => key.split(',')[0]))];
	
	// Find the maximum number of rows across all columns
	const maxRows = Math.max(...Object.values(rawData).map(column => column.length));
	
	// Create worksheet data
	const worksheetData = [];
	
	for (let rowIndex = 0; rowIndex < maxRows; rowIndex++) {
	  const excelRow: any = {};
	  
	  columnNames.forEach(columnName => {
		// Find the first key that starts with this column name
		const columnKey = Object.keys(rawData).find(key => key.startsWith(columnName + ','));
		if (columnKey) {
		  const columnData = rawData[columnKey as keyof typeof rawData];
		  const value = columnData[rowIndex];
		  excelRow[columnName] = value !== null && value !== undefined ? value : '';
		} else {
		  excelRow[columnName] = '';
		}
	  });
	  
	  worksheetData.push(excelRow);
	}
	
	// Create workbook and worksheet
	const workbook = XLSX.utils.book_new();
	const worksheet = XLSX.utils.json_to_sheet(worksheetData);
	
	// Add worksheet to workbook
	XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
	
	// Generate and download file
	XLSX.writeFile(workbook, `${filename}.xlsx`);
  };

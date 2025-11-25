import { UUID } from 'crypto';

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


  // Smooth text streaming utility
  // Streams text character by character or word by word for a smoother UX
  export const createSmoothTextStream = (
	targetText: string,
	onUpdate: (currentText: string) => void,
	options: {
	  chunkSize?: number; // Number of characters to add per interval
	  intervalMs?: number; // Milliseconds between updates
	  mode?: 'character' | 'word'; // Stream by character or by word
	} = {}
  ): { cancel: () => void } => {
	const { chunkSize = 3, intervalMs = 20, mode = 'character' } = options;
	
	let currentIndex = 0;
	let cancelled = false;
	
	const streamNext = () => {
	  if (cancelled || currentIndex >= targetText.length) {
		// Ensure final text is set
		if (!cancelled) {
		  onUpdate(targetText);
		}
		return;
	  }
	  
	  if (mode === 'word') {
		// Stream by words for a more natural reading experience
		const remainingText = targetText.slice(currentIndex);
		const wordMatch = remainingText.match(/^(\s*\S+\s*)/);
		
		if (wordMatch) {
		  currentIndex += wordMatch[0].length;
		} else {
		  currentIndex = targetText.length;
		}
	  } else {
		// Stream by characters
		currentIndex = Math.min(currentIndex + chunkSize, targetText.length);
	  }
	  
	  onUpdate(targetText.slice(0, currentIndex));
	  setTimeout(streamNext, intervalMs);
	};
	
	// Start streaming
	setTimeout(streamNext, 0);
	
	return {
	  cancel: () => {
		cancelled = true;
		onUpdate(targetText); // Show full text immediately on cancel
	  }
	};
  };

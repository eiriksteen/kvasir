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


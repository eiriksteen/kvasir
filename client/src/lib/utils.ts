

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
export const getStatusColor = (status: string) => {
	switch(status) {
		case 'running': return 'text-yellow-400';
		case 'failed': return 'text-red-500';
		case 'completed': return 'text-green-500';
		default: return 'text-gray-400';
	}
};


export function convertTimeStamps(bigint64Array: BigInt64Array) {
    const convertedTimeData: Date[] = Array.from(bigint64Array).map((timestamp: bigint) => {
        return new Date(Number(timestamp) / 1000000);
    });
    return convertedTimeData;
}

export function formatTimeStamps(value: unknown, data: Array<unknown>) {
    if (data.every(item => item instanceof Date)) {
        value = new Date(value as string);
        const firstDate = new Date(data[0]);
        const lastDate = new Date(data[data.length - 1]);
        
        const timeDiff = lastDate.getTime() - firstDate.getTime();
        const daysDiff = timeDiff / (1000 * 60 * 60 * 24);

        if (daysDiff > 365) {
            // For ranges > 1 year, show just month and year
            return (value as Date).toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
        } else if (daysDiff > 7) {
            // For ranges > 1 week, show date without time
            return (value as Date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        } else {
            // For shorter ranges, show date and time
            return (value as Date).toLocaleString(undefined, { 
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit'
            });
        }
    }
}

export function getMinMax(series: Array<{ data: Array<number> }>) {
    const rawMin = Math.min(...series.map((s) => Math.min(...s.data)));
    const rawMax = Math.max(...series.map((s) => Math.max(...s.data)));
    const range = rawMax - rawMin;
    
    // Determine significant digits based on range
    let sigDigits;
    if (range > 3) {
        sigDigits = 0;  // For large ranges, use whole numbers
    } else if (range > 1) {
        sigDigits = 1;  // For medium ranges, use 1 decimal point
    } else if (range > 0.1) {
        sigDigits = 2;  // For smaller ranges, use 2 decimal points
    } else {
        sigDigits = 3;  // For very small ranges, use 3 decimal points
    }

    const min = Number((rawMin * 0.99).toFixed(sigDigits));
    const max = Number((rawMax * 1.01).toFixed(sigDigits));
    return {
        min: min,
        max: max
    }
}
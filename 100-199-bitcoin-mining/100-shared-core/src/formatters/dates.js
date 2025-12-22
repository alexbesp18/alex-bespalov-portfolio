/**
 * Date Formatting Utilities
 * 
 * Functions for formatting dates and time-related values.
 * 
 * @module formatters/dates
 */

/**
 * Format a date as YYYY-MM-DD
 * 
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 * @example
 * formatDate(new Date('2025-01-15')) // "2025-01-15"
 */
export const formatDate = (date) => {
  if (!date) return '';
  
  const d = date instanceof Date ? date : new Date(date);
  
  if (isNaN(d.getTime())) return '';
  
  return d.toISOString().split('T')[0];
};

/**
 * Format a date as human-readable string
 * 
 * @param {Date|string} date - Date to format
 * @param {Object} [options={}] - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 * @example
 * formatDateHuman(new Date('2025-01-15')) // "January 15, 2025"
 */
export const formatDateHuman = (date, options = {}) => {
  if (!date) return '';
  
  const d = date instanceof Date ? date : new Date(date);
  
  if (isNaN(d.getTime())) return '';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  };
  
  return d.toLocaleDateString(undefined, defaultOptions);
};

/**
 * Format a date as short string
 * 
 * @param {Date|string} date - Date to format
 * @returns {string} Short formatted date
 * @example
 * formatDateShort(new Date('2025-01-15')) // "Jan 15, 2025"
 */
export const formatDateShort = (date) => {
  return formatDateHuman(date, { month: 'short' });
};

/**
 * Format date and time
 * 
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date and time
 * @example
 * formatDateTime(new Date()) // "January 15, 2025, 2:30 PM"
 */
export const formatDateTime = (date) => {
  if (!date) return '';
  
  const d = date instanceof Date ? date : new Date(date);
  
  if (isNaN(d.getTime())) return '';
  
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

/**
 * Format time only
 * 
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted time
 * @example
 * formatTime(new Date()) // "2:30 PM"
 */
export const formatTime = (date) => {
  if (!date) return '';
  
  const d = date instanceof Date ? date : new Date(date);
  
  if (isNaN(d.getTime())) return '';
  
  return d.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  });
};

/**
 * Format relative time (e.g., "2 days ago")
 * 
 * @param {Date|string} date - Date to format
 * @returns {string} Relative time string
 * @example
 * formatRelativeTime(new Date(Date.now() - 86400000)) // "1 day ago"
 */
export const formatRelativeTime = (date) => {
  if (!date) return '';
  
  const d = date instanceof Date ? date : new Date(date);
  
  if (isNaN(d.getTime())) return '';
  
  const now = new Date();
  const diffMs = now - d;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffMonth = Math.floor(diffDay / 30);
  const diffYear = Math.floor(diffDay / 365);
  
  if (diffYear > 0) {
    return `${diffYear} year${diffYear > 1 ? 's' : ''} ago`;
  }
  if (diffMonth > 0) {
    return `${diffMonth} month${diffMonth > 1 ? 's' : ''} ago`;
  }
  if (diffDay > 0) {
    return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  }
  if (diffHour > 0) {
    return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  }
  if (diffMin > 0) {
    return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
  }
  
  return 'just now';
};

/**
 * Get months between two dates
 * 
 * @param {Date|string} startDate - Start date
 * @param {Date|string} endDate - End date
 * @returns {number} Number of months between dates
 */
export const getMonthsBetween = (startDate, endDate) => {
  const start = startDate instanceof Date ? startDate : new Date(startDate);
  const end = endDate instanceof Date ? endDate : new Date(endDate);
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0;
  
  const diffMs = end - start;
  return diffMs / (1000 * 60 * 60 * 24 * 30.42);
};

/**
 * Get months until a future date
 * 
 * @param {Date|string} futureDate - Future date
 * @returns {number} Number of months until date (0 if in past)
 */
export const getMonthsUntil = (futureDate) => {
  const months = getMonthsBetween(new Date(), futureDate);
  return Math.max(0, months);
};

/**
 * Format duration in months
 * 
 * @param {number} months - Number of months
 * @returns {string} Formatted duration
 * @example
 * formatDuration(18) // "1 year, 6 months"
 */
export const formatDuration = (months) => {
  if (months < 1) return 'Less than a month';
  
  const years = Math.floor(months / 12);
  const remainingMonths = Math.round(months % 12);
  
  const parts = [];
  
  if (years > 0) {
    parts.push(`${years} year${years > 1 ? 's' : ''}`);
  }
  
  if (remainingMonths > 0) {
    parts.push(`${remainingMonths} month${remainingMonths > 1 ? 's' : ''}`);
  }
  
  return parts.join(', ');
};


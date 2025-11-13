/**
 * Validation utilities
 */

/**
 * Validate phone number (only digits)
 */
export const validatePhone = (phone: string): boolean => {
  if (!phone) return true; // Optional field
  return /^[0-9]+$/.test(phone);
};

/**
 * Validate email format
 */
export const validateEmail = (email: string): boolean => {
  if (!email) return true; // Optional field
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Format phone number input (only allow digits)
 */
export const formatPhoneInput = (value: string): string => {
  return value.replace(/[^0-9]/g, '');
};

/**
 * Validate username (alphanumeric and underscore)
 */
export const validateUsername = (username: string): boolean => {
  if (!username) return false;
  return /^[a-zA-Z0-9_]+$/.test(username);
};


/**
 * Tests for logger utility
 * Tests the logger interface and basic functionality
 */

import logger from '../logger';

describe('Logger Utility', () => {
  // Store original console methods
  const originalConsole = {
    log: console.log,
    info: console.info,
    warn: console.warn,
    error: console.error,
  };

  // Store original NODE_ENV
  const originalNodeEnv = process.env.NODE_ENV;

  // Mock console methods
  const mockLog = jest.fn();
  const mockInfo = jest.fn();
  const mockWarn = jest.fn();
  const mockError = jest.fn();

  beforeAll(() => {
    console.log = mockLog;
    console.info = mockInfo;
    console.warn = mockWarn;
    console.error = mockError;
  });

  afterAll(() => {
    console.log = originalConsole.log;
    console.info = originalConsole.info;
    console.warn = originalConsole.warn;
    console.error = originalConsole.error;
    process.env.NODE_ENV = originalNodeEnv;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('logger has all required methods', () => {
    expect(logger).toHaveProperty('debug');
    expect(logger).toHaveProperty('info');
    expect(logger).toHaveProperty('warn');
    expect(logger).toHaveProperty('error');
    expect(typeof logger.debug).toBe('function');
    expect(typeof logger.info).toBe('function');
    expect(typeof logger.warn).toBe('function');
    expect(typeof logger.error).toBe('function');
  });

  // Note: logger respects log levels - in test env, only WARN and ERROR are logged
  // Testing that warn/error work (which always log regardless of env)
  
  test('logs warning messages', () => {
    logger.warn('Test warning message');
    
    expect(mockWarn).toHaveBeenCalled();
    const callArgs = mockWarn.mock.calls[0];
    expect(callArgs[0]).toContain('Test warning message');
  });

  test('logs error messages', () => {
    logger.error('Test error message');
    
    expect(mockError).toHaveBeenCalled();
    const callArgs = mockError.mock.calls[0];
    expect(callArgs[0]).toContain('Test error message');
  });

  test('logs error objects correctly', () => {
    const error = new Error('Test error');
    logger.error('Error occurred', error);
    
    expect(mockError).toHaveBeenCalled();
    const callArgs = mockError.mock.calls[0];
    expect(callArgs[0]).toContain('Error occurred');
    expect(callArgs[1]).toBe(error);
  });

  test('includes data in warning messages', () => {
    const data = { key: 'value' };
    logger.warn('Message', data);
    
    expect(mockWarn).toHaveBeenCalled();
    const callArgs = mockWarn.mock.calls[0];
    expect(callArgs[0]).toContain('Message');
    expect(callArgs[1]).toBe(data);
  });

  test('formats messages with timestamps', () => {
    logger.warn('Timestamp test');
    
    expect(mockWarn).toHaveBeenCalled();
    const callArgs = mockWarn.mock.calls[0][0];
    expect(callArgs).toMatch(/\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/); // ISO timestamp format
    expect(callArgs).toContain('[WARN]');
    expect(callArgs).toContain('Timestamp test');
  });
});

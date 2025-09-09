// Environment configuration test
import { getApiBaseUrl, getAppName, getAppVersion, isDevelopment, isProduction, isDebugMode } from './constants';
import { logger } from './logger';

export const testEnvironmentConfig = () => {
  logger.info('=== Environment Configuration Test ===');
  logger.info('API Base URL:', getApiBaseUrl());
  logger.info('App Name:', getAppName());
  logger.info('App Version:', getAppVersion());
  logger.info('Is Development:', isDevelopment());
  logger.info('Is Production:', isProduction());
  logger.info('Is Debug Mode:', isDebugMode());
  logger.info('=====================================');
  
  return {
    apiBaseUrl: getApiBaseUrl(),
    appName: getAppName(),
    appVersion: getAppVersion(),
    isDevelopment: isDevelopment(),
    isProduction: isProduction(),
    isDebugMode: isDebugMode()
  };
};

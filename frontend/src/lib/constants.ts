// Application constants and configuration
export const APP_CONFIG = {
  // Default values
  DEFAULT_API_KEY_PLACEHOLDER: "agent_key_abc123_is_prefilled_here",
  
  // Timeout values (in milliseconds)
  TIMEOUTS: {
    EMAIL_VERIFICATION: 2000,
    PASSWORD_RESET: 3000,
    API_REQUEST: 10000,
  },
  
  // Database port defaults
  DB_PORTS: {
    MYSQL: 3306,
    POSTGRES: 5432,
    MONGODB: 27017,
  },
  
  // UI constants
  UI: {
    SIDEBAR_WIDTH: "16rem",
    SIDEBAR_WIDTH_MOBILE: "18rem",
    SIDEBAR_WIDTH_ICON: "4rem",
    SIDEBAR_KEYBOARD_SHORTCUT: "b",
    SIDEBAR_COOKIE_NAME: "sidebar:state",
    SKELETON_WIDTH_MIN: 50,
    SKELETON_WIDTH_MAX: 90,
    // Icon sizes
    ICON_SM: "w-4 h-4",
    ICON_MD: "w-5 h-5", 
    ICON_LG: "w-6 h-6",
    ICON_XL: "w-8 h-8",
    // Container sizes
    CONTAINER_SM: "w-10 h-10",
    CONTAINER_MD: "w-16 h-16",
    CONTAINER_LG: "w-20 h-20",
  },
  
  // Query cache times (in milliseconds)
  CACHE_TIMES: {
    CONNECTIONS: 5 * 60 * 1000, // 5 minutes
    CONNECTION_DETAILS: 2 * 60 * 1000, // 2 minutes
    CONNECTION_STATUS: 30 * 1000, // 30 seconds
  },
  
  // External documentation links
  DOCUMENTATION: {
    SUPABASE: "https://supabase.com/docs/guides/database/connecting-to-postgres",
    SNOWFLAKE: "https://docs.snowflake.com/en/user-guide/admin-user-management.html",
    MONGODB: "https://docs.atlas.mongodb.com/security-add-mongodb-users/",
    MYSQL: "https://dev.mysql.com/doc/refman/8.0/en/creating-accounts.html",
  },
  
  // Docker configuration
  DOCKER: {
    IMAGE_NAME: "custardagent/agent-postgresql:latest",
    BACKEND_URL: "wss://clean-custard-backend-production.up.railway.app",
  },
} as const;

// Environment configuration
export const getApiBaseUrl = (): string => {
  // In development, use the proxy path
  if (import.meta.env.DEV) {
    return '/api/v1';
  }
  // In production, use the full URL
  return import.meta.env.VITE_API_BASE_URL || '/api/v1';
};

export const getAppName = (): string => {
  return import.meta.env.VITE_APP_NAME || 'Custard';
};

export const getAppVersion = (): string => {
  return import.meta.env.VITE_APP_VERSION || '1.0.0';
};

export const isDevelopment = (): boolean => {
  return import.meta.env.VITE_APP_ENV === 'development' || import.meta.env.DEV;
};

export const isProduction = (): boolean => {
  return import.meta.env.VITE_APP_ENV === 'production' || import.meta.env.PROD;
};

export const isDebugMode = (): boolean => {
  return import.meta.env.VITE_DEBUG === 'true' || isDevelopment();
};

export const shouldLogToConsole = (): boolean => {
  return isDebugMode();
};

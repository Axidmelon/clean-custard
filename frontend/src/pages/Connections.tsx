import { Database, Layers, GitBranch, CheckCircle, Snowflake, Loader2, AlertCircle, X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { CreateConnectionRequest, Connection } from "@/types/api";
import { useConnectionsWithDetails, useCreateConnection, useDeleteConnection, useConnectionStatus } from "@/hooks/useConnections";
import { useWebSocketConnectionStatus } from "@/hooks/useWebSocketStatus";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { APP_CONFIG } from "@/lib/constants";
import { logApiResponse, logUserAction, logError, logDebug } from "@/lib/logger";

interface DatabaseTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  db_type: string;
}


const databaseTemplates: DatabaseTemplate[] = [
  {
    id: 'supabase',
    name: 'Supabase',
    description: 'PostgreSQL database with real-time subscriptions and authentication',
    icon: Database,
    color: 'green',
    db_type: 'SUPABASE'
  },
  {
    id: 'snowflake',
    name: 'Snowflake',
    description: 'Cloud data platform with elastic compute and storage',
    icon: Snowflake,
    color: 'blue',
    db_type: 'SNOWFLAKE'
  },
  {
    id: 'mongodb',
    name: 'MongoDB',
    description: 'NoSQL document database for flexible data storage',
    icon: Layers,
    color: 'green',
    db_type: 'MONGODB'
  },
  {
    id: 'mysql',
    name: 'MySQL',
    description: 'Popular open-source relational database management system',
    icon: Database,
    color: 'blue',
    db_type: 'MYSQL'
  }
];



// Helper function to get database user creation commands
const getDatabaseUserCommands = (dbType: string): string => {
  switch (dbType) {
    case 'SUPABASE':
      return `-- PostgreSQL (Supabase)
CREATE USER custard_agent WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_database TO custard_agent;
GRANT USAGE ON SCHEMA public TO custard_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO custard_agent;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO custard_agent;`;
    case 'MYSQL':
      return `-- MySQL
CREATE USER 'custard_agent'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT ON your_database.* TO 'custard_agent'@'%';
FLUSH PRIVILEGES;`;
    case 'MONGODB':
      return `// MongoDB
use admin
db.createUser({
  user: "custard_agent",
  pwd: "secure_password",
  roles: [{ role: "read", db: "your_database" }]
})`;
    case 'SNOWFLAKE':
      return `-- Snowflake
CREATE USER custard_agent PASSWORD='secure_password';
GRANT ROLE PUBLIC TO USER custard_agent;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE PUBLIC;`;
    default:
      return `-- Create read-only user for ${dbType}
-- Replace with your database-specific commands`;
  }
};


// Connection Form Component with Step 1: Name Your Connection
function ConnectionForm({ databaseTemplate, onStepChange }: { 
  databaseTemplate: DatabaseTemplate;
  onStepChange?: (step: number) => void;
}) {
  const createConnectionMutation = useCreateConnection();
  const [currentStep, setCurrentStep] = useState(1);
  const [connectionName, setConnectionName] = useState('');
  const [generatedApiKey, setGeneratedApiKey] = useState<string>('');
  const [generatedAgentId, setGeneratedAgentId] = useState<string>('');
  const [generatedConnectionId, setGeneratedConnectionId] = useState<string>('');
  const [generatedWebsocketUrl, setGeneratedWebsocketUrl] = useState<string>('');
  

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!connectionName.trim()) return;
    
    try {
      const requestData: CreateConnectionRequest = {
        name: connectionName.trim(),
        db_type: databaseTemplate.db_type
      };
      
      const response = await createConnectionMutation.mutateAsync(requestData);
      
      // Log the response for debugging
      logApiResponse('Create Connection', response);
      
      // Store the generated API key, agent ID, and connection ID for Step 2
      if (response.api_key) {
        setGeneratedApiKey(response.api_key);
        logDebug('Set generated API key:', response.api_key);
      } else {
        logDebug('No API key in response');
      }
      
      if (response.agent_id) {
        setGeneratedAgentId(response.agent_id);
        logDebug('Set generated agent ID:', response.agent_id);
      } else {
        logDebug('No agent ID in response');
      }
      
      if (response.id) {
        setGeneratedConnectionId(response.id);
        logDebug('Set generated connection ID:', response.id);
      } else {
        logDebug('No connection ID in response');
      }
      
      if (response.websocket_url) {
        setGeneratedWebsocketUrl(response.websocket_url);
        logDebug('Set generated WebSocket URL:', response.websocket_url);
      } else {
        logDebug('No WebSocket URL in response');
      }
      
      setCurrentStep(2);
      onStepChange?.(2);
    } catch (error) {
      logError('Connection creation failed', error);
      // Even if the API call fails, we can still show Step 2
      // since the main purpose is to show the Docker command
      setCurrentStep(2);
      onStepChange?.(2);
    }
  };


  // Step 1: Name Your Connection
  if (currentStep === 1) {
    return (
      <div className="space-y-6">
        
        <form onSubmit={handleStep1Submit} className="space-y-4">
          {createConnectionMutation.error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {createConnectionMutation.error.message || 'Failed to create connection'}
              </AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <label htmlFor="connectionName" className="text-sm font-medium text-gray-700">
              Connection Name
            </label>
            <Input
              id="connectionName"
              type="text"
              placeholder="e.g., Production Analytics DB"
              value={connectionName}
              onChange={(e) => setConnectionName(e.target.value)}
              required
            />
            <p className="text-xs text-gray-500">
              This is a friendly name for your own reference.
            </p>
          </div>
          
          <div className="flex justify-end gap-3">
            <Button 
              type="submit" 
              disabled={createConnectionMutation.isPending || !connectionName.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {createConnectionMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                'Generate Connection Command'
              )}
            </Button>
          </div>
        </form>
      </div>
    );
  }

  // Step 2: Run the Secure Connector Agent
  const handleCopyCommand = async () => {
    const apiKey = generatedApiKey || APP_CONFIG.DEFAULT_API_KEY_PLACEHOLDER;
    const agentId = generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`;
    const connectionId = generatedConnectionId || 'YOUR_CONNECTION_UUID_HERE'; // Use the actual database UUID
    const websocketUrl = generatedWebsocketUrl || `${APP_CONFIG.DOCKER.BACKEND_URL}/api/v1/connections/ws/${agentId}`;
    
    // Log the values being used for debugging
    logDebug('Generated API key state:', generatedApiKey);
    logDebug('Generated agent ID state:', generatedAgentId);
    logDebug('Generated connection ID state:', generatedConnectionId);
    logDebug('Generated WebSocket URL state:', generatedWebsocketUrl);
    logDebug('API key being used:', apiKey);
    logDebug('Agent ID being used:', agentId);
    logDebug('Connection ID being used:', connectionId);
    logDebug('WebSocket URL being used:', websocketUrl);
    
    const command = `docker run -d \\
  --name custard-agent-${connectionName.toLowerCase().replace(/\s+/g, '-')} \\
  --network host \\
  -e CONNECTION_ID="${connectionId}" \\
  -e AGENT_ID="${agentId}" \\
  -e BACKEND_WEBSOCKET_URI="${websocketUrl}" \\
  -e DB_HOST="YOUR_${databaseTemplate.name.toUpperCase()}_HOST" \\
  -e DB_PORT="YOUR_DB_PORT" \\
  -e DB_USER="YOUR_READONLY_USER" \\
  -e DB_PASSWORD="YOUR_DB_PASSWORD" \\
  -e DB_NAME="YOUR_DATABASE_NAME" \\
  -e DB_SSLMODE="require" \\
  ${APP_CONFIG.DOCKER.IMAGE_NAME}`;
    
    try {
      await navigator.clipboard.writeText(command);
      logUserAction('Docker command copied to clipboard');
      // You could add a toast notification here
    } catch (err) {
      logError('Failed to copy command to clipboard', err);
    }
  };

  const getDatabaseSpecificHelp = (dbType: string) => {
    switch (dbType) {
      case 'SUPABASE':
        return {
          title: "Where to find these values in Supabase:",
          content: "Log in to your Supabase dashboard, go to **Project Settings > Database**. Use the 'Connection Info' details. We strongly recommend creating a dedicated, **read-only** user for Custard. **Note**: SSL is required for Supabase connections (already configured in the Docker command).",
          link: APP_CONFIG.DOCUMENTATION.SUPABASE
        };
      case 'SNOWFLAKE':
        return {
          title: "Where to find these values in Snowflake:",
          content: "Log in to your Snowflake account, go to **Admin > Warehouses** for warehouse details and **Data > Databases** for database info. Create a dedicated **read-only** role for Custard.",
          link: APP_CONFIG.DOCUMENTATION.SNOWFLAKE
        };
      case 'MONGODB':
        return {
          title: "Where to find these values in MongoDB:",
          content: "Log in to your MongoDB Atlas dashboard, go to **Database > Connect** for connection string details. Create a dedicated **read-only** user for Custard.",
          link: APP_CONFIG.DOCUMENTATION.MONGODB
        };
      case 'MYSQL':
        return {
          title: "Where to find these values in MySQL:",
          content: "Access your MySQL server directly or through your hosting provider's control panel. Create a dedicated **read-only** user for Custard with appropriate database permissions.",
          link: APP_CONFIG.DOCUMENTATION.MYSQL
        };
      default:
        return {
          title: `Where to find these values in ${databaseTemplate.name}:`,
          content: "Log in to your database dashboard and locate the connection details. We strongly recommend creating a dedicated, **read-only** user for Custard.",
          link: "#"
        };
    }
  };

  const helpInfo = getDatabaseSpecificHelp(databaseTemplate.db_type);

  // Log the current state for debugging
  logDebug('Step 2 - Generated API key:', generatedApiKey);
  logDebug('Step 2 - Connection name:', connectionName);

  return (
    <div className="max-h-[80vh] overflow-y-auto">
      {/* Scrollable Content */}
      <div className="space-y-6">
        {/* Security Info */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start space-x-4">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-green-900 mb-2">Secure by Design</h4>
              <p className="text-sm text-green-800">
                Your database credentials never leave your network. The agent runs locally and only sends encrypted metadata to Custard.
              </p>
            </div>
          </div>
        </div>

        {/* Generated Command Section */}
        <div className="bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-900">Docker Command</h4>
              <p className="text-xs text-gray-500 mt-1">
                ⚠️ Replace placeholder values with your actual database credentials
              </p>
            </div>
            <div className="flex space-x-2">
              <Button 
                size="sm" 
                variant="outline" 
                className="text-blue-600 border-blue-300 hover:bg-blue-50 shadow-sm"
                onClick={() => window.open('/docs/agent-deployment', '_blank')}
              >
                Setup Guide
              </Button>
              <Button 
                size="sm" 
                variant="outline" 
                className="text-gray-600 border-gray-300 hover:bg-gray-50 shadow-sm"
                onClick={handleCopyCommand}
              >
                Copy
              </Button>
            </div>
          </div>
          
          <div className="bg-gray-900 text-gray-100 rounded-lg border overflow-hidden shadow-lg">
            <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-xs text-gray-400 ml-2 font-medium">Terminal</span>
              </div>
            </div>
            <div className="p-4">
              <pre className="whitespace-pre-wrap text-xs leading-relaxed font-mono overflow-x-auto">
{`docker run -d \\
  --name custard-agent-${connectionName.toLowerCase().replace(/\s+/g, '-')} \\
  --network host \\
  -e CONNECTION_ID="${generatedConnectionId || 'YOUR_CONNECTION_UUID_HERE'}" \\
  -e AGENT_ID="${generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`}" \\
  -e BACKEND_WEBSOCKET_URI="${generatedWebsocketUrl || `${APP_CONFIG.DOCKER.BACKEND_URL}/api/v1/connections/ws/${generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`}`}" \\
  -e DB_HOST="YOUR_${databaseTemplate.name.toUpperCase()}_HOST" \\
  -e DB_PORT="YOUR_DB_PORT" \\
  -e DB_USER="YOUR_READONLY_USER" \\
  -e DB_PASSWORD="YOUR_DB_PASSWORD" \\
  -e DB_NAME="postgres" \\
  -e DB_SSLMODE="require" \\
  ${APP_CONFIG.DOCKER.IMAGE_NAME}`}
              </pre>
            </div>
          </div>
          
          <div className="mt-4 text-xs text-gray-500 space-y-1">
            <p>• Run this command in your server environment</p>
            <p>• Ensure Docker is installed and running</p>
            <p>• Replace placeholder values with your actual credentials</p>
            <p>• <code className="bg-gray-100 px-1 rounded">DB_SSLMODE="require"</code> is set for secure database connections (required for Supabase)</p>
          </div>
        </div>

        {/* Setup Requirements */}
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start space-x-4">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-yellow-900 mb-2">⚠️ Setup Requirements</h4>
              <p className="text-sm text-yellow-800 font-medium mb-3">Docker Command Alone is NOT Sufficient</p>
              <div className="text-sm text-yellow-700 space-y-2">
                <p>Before running the command above, you must:</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Configure your firewall to allow outbound HTTPS (port 443)</li>
                  <li>Create a read-only database user</li>
                  <li>Ensure database accessibility from Docker</li>
                  <li>Test network connectivity</li>
                </ul>
                <a 
                  href="/docs/agent-deployment" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-yellow-600 hover:text-yellow-800 underline font-medium text-sm"
                >
                  View complete setup guide →
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Database User Setup */}
        <div className="bg-gradient-to-r from-red-50 to-rose-50 border border-red-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start space-x-4">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900 mb-2">Create Read-Only Database User</h4>
              <p className="text-sm text-red-800 font-medium mb-3">CRITICAL: Create Read-Only User</p>
              <div className="text-sm text-red-700 space-y-3">
                <p>Never use admin/root database users. Create a dedicated read-only user:</p>
                <details className="group">
                  <summary className="cursor-pointer font-medium group-open:text-red-900 text-sm">
                    Show {databaseTemplate.name} commands
                  </summary>
                  <div className="mt-3 bg-red-100 p-3 rounded-lg">
                    <pre className="text-xs whitespace-pre-wrap font-mono">
{getDatabaseUserCommands(databaseTemplate.db_type)}
                    </pre>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Tests */}
        <div className="bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-xl p-5 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Quick Tests</h4>
          <details className="group">
            <summary className="cursor-pointer text-sm text-gray-700 font-medium group-open:text-gray-900">
              Test connectivity before deployment
            </summary>
            <div className="mt-4 space-y-3">
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Test internet access:</p>
                <code className="bg-gray-100 px-3 py-2 rounded text-xs font-mono block">docker run --rm alpine ping -c 3 8.8.8.8</code>
              </div>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Test backend connectivity:</p>
                <code className="bg-gray-100 px-3 py-2 rounded text-xs font-mono block">curl -I https://your-backend.railway.app/health</code>
              </div>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Test database connectivity:</p>
                <code className="bg-gray-100 px-3 py-2 rounded text-xs font-mono block">docker run --rm postgres:15-alpine pg_isready -h YOUR_DB_HOST -p 5432</code>
              </div>
            </div>
          </details>
        </div>

        {/* Help Section */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-sm">
          <h4 className="text-sm font-semibold text-blue-900 mb-3">{helpInfo.title}</h4>
          <p className="text-sm text-blue-800 mb-3">
            {helpInfo.content}
          </p>
          <a 
            href={helpInfo.link} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 underline font-medium"
          >
            View documentation →
          </a>
        </div>
        

        {/* Post-Deployment Verification */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-5 shadow-sm">
          <h4 className="text-sm font-semibold text-green-900 mb-3">After Running the Command</h4>
          <div className="text-sm text-green-700 space-y-2">
            <p className="font-medium">Check these logs for success:</p>
            <div className="space-y-2">
              <code className="bg-green-100 px-3 py-2 rounded text-xs font-mono block">
                ✅ Successfully connected to Custard backend
              </code>
              <code className="bg-green-100 px-3 py-2 rounded text-xs font-mono block">
                Database schema discovery completed
              </code>
            </div>
            <p className="mt-3">Then verify connection status in your dashboard.</p>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <Button 
          variant="outline" 
          onClick={() => setCurrentStep(1)}
          disabled={createConnectionMutation.isPending}
          className="shadow-sm"
        >
          Back
        </Button>
        <Button 
          className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
          disabled={createConnectionMutation.isPending}
        >
          Done - View Connection
        </Button>
      </div>
    </div>
  );
}

// Simple Database Card Component (no status, just name and connect icon)
function DatabaseCard({ databaseTemplate, onConnect }: { 
  databaseTemplate: DatabaseTemplate;
  onConnect: (template: DatabaseTemplate) => void;
}) {
  const IconComponent = databaseTemplate.icon;
  
  const getIconBgColor = (color: string) => {
    const colorMap: Record<string, string> = {
      'blue': 'bg-blue-50 border-blue-200',
      'green': 'bg-green-50 border-green-200',
    };
    return colorMap[color] || 'bg-gray-50 border-gray-200';
  };

  const getIconColor = (color: string) => {
    const colorMap: Record<string, string> = {
      'blue': 'text-blue-600',
      'green': 'text-green-600',
    };
    return colorMap[color] || 'text-gray-600';
  };
  
  return (
    <Card className="hover:shadow-lg transition-all duration-200 border-0 shadow-sm bg-white cursor-pointer">
      <CardContent className="p-6">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${getIconBgColor(databaseTemplate.color)}`}>
            <IconComponent className={`w-8 h-8 ${getIconColor(databaseTemplate.color)}`} />
          </div>
          
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900 text-lg">{databaseTemplate.name}</h3>
            <Button 
              size="sm" 
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => onConnect(databaseTemplate)}
            >
              <GitBranch className="w-4 h-4 mr-2" />
              Connect
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// WebSocket Status Indicator Component
function WebSocketStatusIndicator() {
  const [isReconnecting, setIsReconnecting] = useState(false);

  // Use the dedicated WebSocket connection status hook
  const { isWebSocketConnected, reconnect } = useWebSocketConnectionStatus();

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await reconnect();
    } finally {
      setIsReconnecting(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1">
        <div className={`w-2 h-2 rounded-full ${isWebSocketConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-xs text-muted-foreground">
          {isWebSocketConnected ? 'Real-time' : 'Polling'}
        </span>
      </div>
      {!isWebSocketConnected && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReconnect}
          disabled={isReconnecting}
          className="h-6 px-2 text-xs"
        >
          {isReconnecting ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            'Reconnect'
          )}
        </Button>
      )}
    </div>
  );
}

// Simple Connection Card Component (shows name, db_type, status)
function SimpleConnectionCard({ connection, onDelete }: { 
  connection: Connection; 
  onDelete: (id: string) => void;
}) {
  const getDbIcon = (dbType: string) => {
    const template = databaseTemplates.find(t => t.db_type === dbType);
    return template?.icon || Database;
  };
  

  // Use real-time status check with WebSocket and polling fallback
  const { 
    data: statusData, 
    isLoading: statusLoading, 
    isWebSocketConnected
  } = useConnectionStatus(connection.id);

  const getStatusInfo = (isConnected: boolean | null | undefined, isLoading: boolean, wsConnected: boolean) => {
    if (isLoading) {
      return {
        badge: (
          <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-100">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Checking...
          </Badge>
        ),
        iconBg: 'bg-gray-50 border-gray-200',
        iconColor: 'text-gray-600'
      };
    }
    
    if (isConnected) {
      return {
        badge: (
          <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
            <CheckCircle className="w-3 h-3 mr-1" />
            {wsConnected ? 'Connected' : 'Connected (Polling)'}
          </Badge>
        ),
        iconBg: 'bg-green-50 border-green-200',
        iconColor: 'text-green-600'
      };
    } else {
      return {
        badge: (
          <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            {wsConnected ? 'Pending' : 'Pending (Polling)'}
          </Badge>
        ),
        iconBg: 'bg-yellow-50 border-yellow-200',
        iconColor: 'text-yellow-600'
      };
    }
  };

  const IconComponent = getDbIcon(connection.db_type);
  const statusInfo = getStatusInfo(statusData?.agent_connected, statusLoading, isWebSocketConnected);
  
  return (
    <Card className="border-0 shadow-sm bg-white">
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${statusInfo.iconBg}`}>
            <IconComponent className={`w-5 h-5 ${statusInfo.iconColor}`} />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h3 className="font-semibold text-gray-900 truncate">{connection.name}</h3>
              <span className="text-sm text-gray-500">•</span>
              <span className="text-sm text-gray-600">{connection.db_type}</span>
              <span className="text-sm text-gray-500">•</span>
              {statusInfo.badge}
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={() => onDelete(connection.id)}
            >
              Delete
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Bottom Bar Component for Connection Form
function ConnectionBottomBar({ 
  databaseTemplate, 
  isOpen, 
  onClose,
  currentStep,
  onStepChange
}: { 
  databaseTemplate: DatabaseTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  currentStep: number;
  onStepChange: (step: number) => void;
}) {
  if (!isOpen || !databaseTemplate) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed bg-black bg-opacity-50 z-40"
        onClick={onClose}
        style={{ 
          top: '-100px',
          left: 0, 
          right: 0, 
          bottom: 0,
          width: '100vw',
          height: 'calc(100vh + 100px)',
          position: 'fixed'
        }}
      />
      
      {/* Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50 rounded-t-2xl">
        <div className="max-w-7xl mx-auto p-6">
          {currentStep === 1 && (
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <databaseTemplate.icon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Connect to {databaseTemplate.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Enter your {databaseTemplate.name} credentials to establish a connection
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          )}
          
          {currentStep === 2 && (
            <div className="relative flex items-center justify-center mb-4">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Run the Secure Connector Agent
                </h3>
                <p className="text-sm text-gray-600">
                  Set up a secure connection to your database using our lightweight agent.
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="absolute right-0 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          )}
          
          <ConnectionForm 
            databaseTemplate={databaseTemplate} 
            onStepChange={onStepChange}
          />
        </div>
      </div>
    </>
  );
}

export default function Connections() {
  const { 
    data: connections, 
    isLoading: loadingConnections, 
    error: connectionsError
  } = useConnectionsWithDetails();
  
  const deleteConnectionMutation = useDeleteConnection();
  const [selectedDatabaseTemplate, setSelectedDatabaseTemplate] = useState<DatabaseTemplate | null>(null);
  const [isBottomBarOpen, setIsBottomBarOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const handleConnect = (template: DatabaseTemplate) => {
    setSelectedDatabaseTemplate(template);
    setIsBottomBarOpen(true);
    setCurrentStep(1);
  };

  const handleCloseBottomBar = () => {
    setIsBottomBarOpen(false);
    setSelectedDatabaseTemplate(null);
    setCurrentStep(1);
  };

  const handleStepChange = (step: number) => {
    setCurrentStep(step);
  };

  const handleDeleteConnection = async (connectionId: string) => {
    if (window.confirm('Are you sure you want to delete this connection?')) {
      try {
        await deleteConnectionMutation.mutateAsync(connectionId);
        logUserAction('Connection deleted', { connectionId });
      } catch (error) {
        logError('Failed to delete connection', error);
      }
    }
  };

  return (
    <div className="space-y-8">
      {/* Header with Request Integration Button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Connections</h1>
          <p className="text-muted-foreground mt-1">
            Manage your data source integrations and connections
          </p>
        </div>
        <Button variant="outline" className="bg-white border-blue-300 text-blue-700 hover:bg-blue-50">
          <GitBranch className="w-4 h-4 mr-2" />
          Request Integration
        </Button>
      </div>

      {/* Databases Section */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Databases</h2>
          <p className="text-sm text-muted-foreground">
            Connect to your database sources
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {databaseTemplates.map((template) => (
            <DatabaseCard 
              key={template.id} 
              databaseTemplate={template} 
              onConnect={handleConnect}
            />
          ))}
        </div>
      </div>

      {/* Your Connections Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-2">Your Connections</h2>
            <p className="text-sm text-muted-foreground">
              Manage your active database connections
            </p>
          </div>
          <div className="flex items-center gap-2">
            <WebSocketStatusIndicator />
          </div>
        </div>
        
        {loadingConnections ? (
          <Card className="border-dashed border-gray-300">
            <CardContent className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">Loading your connections...</p>
            </CardContent>
          </Card>
        ) : connectionsError ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load connections: {connectionsError.message}
            </AlertDescription>
          </Alert>
        ) : connections && connections.length > 0 ? (
          <div className="space-y-4">
            {connections.map((connection) => (
              <SimpleConnectionCard 
                key={connection.id} 
                connection={connection}
                onDelete={handleDeleteConnection}
              />
            ))}
          </div>
        ) : (
          <Card className="border-dashed border-gray-300">
            <CardContent className="p-8 text-center">
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                <Database className="w-6 h-6 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No connections yet</h3>
              <p className="text-gray-500 mb-4">Connect to your first database to get started</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Bottom Bar for Connection Form */}
      <ConnectionBottomBar
        databaseTemplate={selectedDatabaseTemplate}
        isOpen={isBottomBarOpen}
        onClose={handleCloseBottomBar}
        currentStep={currentStep}
        onStepChange={handleStepChange}
      />
    </div>
  );
}
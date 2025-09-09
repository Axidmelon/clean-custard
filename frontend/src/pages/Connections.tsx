import { Database, Layers, GitBranch, CheckCircle, Snowflake, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { CreateConnectionRequest, Connection as ApiConnection, Connection } from "@/types/api";
import { useConnectionsWithDetails, useCreateConnection, useDeleteConnection, useRefreshConnections } from "@/hooks/useConnections";
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

interface DatabaseCredentials {
  host?: string;
  port?: string;
  username?: string;
  password?: string;
  database?: string;
  projectId?: string;
  keyFile?: string;
  accountId?: string;
  warehouseName?: string;
  catalog?: string;
  schema?: string;
  clusterId?: string;
  httpPath?: string;
  apiKey?: string;
  region?: string;
  connectionName?: string;
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



// Database credential form fields configuration
const getCredentialFields = (dbType: string): { field: keyof DatabaseCredentials; label: string; type: string; placeholder: string; required: boolean }[] => {
  switch (dbType) {
    case 'mysql':
      return [
        { field: 'host', label: 'Host', type: 'text', placeholder: 'localhost', required: true },
        { field: 'port', label: 'Port', type: 'text', placeholder: APP_CONFIG.DB_PORTS.MYSQL.toString(), required: true },
        { field: 'database', label: 'Database', type: 'text', placeholder: 'my_database', required: true },
        { field: 'username', label: 'Username', type: 'text', placeholder: 'username', required: true },
        { field: 'password', label: 'Password', type: 'password', placeholder: '••••••••', required: true }
      ];
    case 'supabase':
      return [
        { field: 'host', label: 'Database URL', type: 'text', placeholder: 'db.xyz.supabase.co', required: true },
        { field: 'database', label: 'Database Name', type: 'text', placeholder: 'postgres', required: true },
        { field: 'username', label: 'Username', type: 'text', placeholder: 'postgres', required: true },
        { field: 'password', label: 'Password', type: 'password', placeholder: '••••••••', required: true },
        { field: 'port', label: 'Port', type: 'text', placeholder: APP_CONFIG.DB_PORTS.POSTGRES.toString(), required: true }
      ];
    case 'snowflake':
      return [
        { field: 'accountId', label: 'Account Identifier', type: 'text', placeholder: 'xy12345.us-east-1', required: true },
        { field: 'username', label: 'Username', type: 'text', placeholder: 'username', required: true },
        { field: 'password', label: 'Password', type: 'password', placeholder: '••••••••', required: true },
        { field: 'warehouseName', label: 'Warehouse', type: 'text', placeholder: 'COMPUTE_WH', required: true },
        { field: 'database', label: 'Database', type: 'text', placeholder: 'MY_DATABASE', required: false },
        { field: 'schema', label: 'Schema', type: 'text', placeholder: 'PUBLIC', required: false }
      ];
    case 'mongodb':
      return [
        { field: 'host', label: 'Connection String', type: 'text', placeholder: `mongodb://localhost:${APP_CONFIG.DB_PORTS.MONGODB}`, required: true },
        { field: 'database', label: 'Database Name', type: 'text', placeholder: 'my_database', required: true },
        { field: 'username', label: 'Username', type: 'text', placeholder: 'username', required: false },
        { field: 'password', label: 'Password', type: 'password', placeholder: '••••••••', required: false }
      ];
    default:
      return [
        { field: 'connectionName', label: 'Connection Name', type: 'text', placeholder: 'My Connection', required: true },
        { field: 'apiKey', label: 'API Key', type: 'password', placeholder: 'Enter API key...', required: true }
      ];
  }
};

// Connection Form Component with Step 1: Name Your Connection
function ConnectionForm({ databaseTemplate }: { databaseTemplate: DatabaseTemplate }) {
  const createConnectionMutation = useCreateConnection();
  const [currentStep, setCurrentStep] = useState(1);
  const [connectionName, setConnectionName] = useState('');
  const [generatedApiKey, setGeneratedApiKey] = useState<string>('');
  const [generatedAgentId, setGeneratedAgentId] = useState<string>('');
  const [generatedWebsocketUrl, setGeneratedWebsocketUrl] = useState<string>('');
  
  const form = useForm<DatabaseCredentials>({
    defaultValues: {}
  });

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
      
      // Store the generated API key and agent ID for Step 2
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
      
      if (response.websocket_url) {
        setGeneratedWebsocketUrl(response.websocket_url);
        logDebug('Set generated WebSocket URL:', response.websocket_url);
      } else {
        logDebug('No WebSocket URL in response');
      }
      
      setCurrentStep(2);
    } catch (error) {
      logError('Connection creation failed', error);
      // Even if the API call fails, we can still show Step 2
      // since the main purpose is to show the Docker command
      setCurrentStep(2);
    }
  };

  const handleStep2Submit = async (data: DatabaseCredentials) => {
    try {
      // This would be the actual connection logic for Step 2
      // For now, we'll just show the generated command
      logUserAction('Step 2 credentials submitted', data);
    } catch (error) {
      logError('Step 2 connection error', error);
    }
  };

  const fields = getCredentialFields(databaseTemplate.id);

  // Step 1: Name Your Connection
  if (currentStep === 1) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Connect to Your {databaseTemplate.name} Database
          </h3>
        </div>
        
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
          
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={createConnectionMutation.isPending}>
                Cancel
              </Button>
            </DialogClose>
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
          </DialogFooter>
        </form>
      </div>
    );
  }

  // Step 2: Run the Secure Connector Agent
  const handleCopyCommand = async () => {
    const apiKey = generatedApiKey || APP_CONFIG.DEFAULT_API_KEY_PLACEHOLDER;
    const agentId = generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`;
    const websocketUrl = generatedWebsocketUrl || `ws://localhost:8000/api/v1/connections/ws/${agentId}`;
    
    // Log the values being used for debugging
    logDebug('Generated API key state:', generatedApiKey);
    logDebug('Generated agent ID state:', generatedAgentId);
    logDebug('Generated WebSocket URL state:', generatedWebsocketUrl);
    logDebug('API key being used:', apiKey);
    logDebug('Agent ID being used:', agentId);
    logDebug('WebSocket URL being used:', websocketUrl);
    
    const command = `docker run -d \\
  --name custard-agent-${connectionName.toLowerCase().replace(/\s+/g, '-')} \\
  -e CONNECTION_ID="${agentId}" \\
  -e BACKEND_WEBSOCKET_URI="${websocketUrl}" \\
  -e DB_HOST="YOUR_${databaseTemplate.name.toUpperCase()}_HOST" \\
  -e DB_PORT="YOUR_DB_PORT" \\
  -e DB_USER="YOUR_READONLY_USER" \\
  -e DB_PASSWORD="YOUR_DB_PASSWORD" \\
  -e DB_NAME="postgres" \\
  custard/agent:latest`;
    
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
          content: "Log in to your Supabase dashboard, go to **Project Settings > Database**. Use the 'Connection Info' details. We strongly recommend creating a dedicated, **read-only** user for Custard.",
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
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Run the Secure Connector Agent
        </h3>
        <p className="text-sm text-gray-600">
          Set up a secure connection to your database using our lightweight agent.
        </p>
      </div>
      
      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel - Information */}
        <div className="space-y-6">
          {/* Security Info */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-900">Security & Setup</h4>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle className="w-3 h-3 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-green-800 font-medium mb-1">Secure by Design</p>
                  <p className="text-xs text-green-700">
                    Your database credentials never leave your network. The agent runs locally and only sends encrypted metadata to Custard.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Help Section */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-900">{helpInfo.title}</h4>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800 mb-3">
                {helpInfo.content}
              </p>
              <a 
                href={helpInfo.link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 underline font-medium"
              >
                View documentation →
              </a>
            </div>
          </div>
          
          {/* Connection Status */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-900">Connection Status</h4>
            <div className="flex items-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-yellow-800">Waiting for connection...</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Command Snippet */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-900">Generated Command</h4>
            <Button 
              size="sm" 
              variant="outline" 
              className="text-gray-600 border-gray-300 hover:bg-gray-50"
              onClick={handleCopyCommand}
            >
              Copy
            </Button>
          </div>
          
          <div className="bg-gray-900 text-gray-100 rounded-lg border overflow-hidden">
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-xs text-gray-400 ml-2">Terminal</span>
              </div>
            </div>
            <div className="p-4">
              <pre className="whitespace-pre-wrap text-xs leading-relaxed font-mono overflow-x-auto">
{`docker run -d \\
  --name custard-agent-${connectionName.toLowerCase().replace(/\s+/g, '-')} \\
  -e CONNECTION_ID="${generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`}" \\
  -e BACKEND_WEBSOCKET_URI="${generatedWebsocketUrl || `ws://localhost:8000/api/v1/connections/ws/${generatedAgentId || `agent-${connectionName.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`}`}" \\
  -e DB_HOST="YOUR_${databaseTemplate.name.toUpperCase()}_HOST" \\
  -e DB_PORT="YOUR_DB_PORT" \\
  -e DB_USER="YOUR_READONLY_USER" \\
  -e DB_PASSWORD="YOUR_DB_PASSWORD" \\
  -e DB_NAME="postgres" \\
  custard/agent:latest`}
              </pre>
            </div>
          </div>
          
          <div className="text-xs text-gray-500 space-y-1">
            <p>• Run this command in your server environment</p>
            <p>• Ensure Docker is installed and running</p>
            <p>• Replace placeholder values with your actual credentials</p>
          </div>
        </div>
      </div>
      
      <DialogFooter>
        <Button 
          variant="outline" 
          onClick={() => setCurrentStep(1)}
          disabled={createConnectionMutation.isPending}
        >
          Back
        </Button>
        <DialogClose asChild>
          <Button 
            className="bg-blue-600 hover:bg-blue-700 text-white"
            disabled={createConnectionMutation.isPending}
          >
            Done - View Connection
          </Button>
        </DialogClose>
      </DialogFooter>
    </div>
  );
}

// Simple Database Card Component (no status, just name and connect icon)
function DatabaseCard({ databaseTemplate }: { databaseTemplate: DatabaseTemplate }) {
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
            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
                  <GitBranch className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[800px]">
                <DialogHeader>
                  <DialogTitle>Connect to {databaseTemplate.name}</DialogTitle>
                  <DialogDescription>
                    Enter your {databaseTemplate.name} credentials to establish a connection.
                  </DialogDescription>
                </DialogHeader>
                
                <ConnectionForm databaseTemplate={databaseTemplate} />
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardContent>
    </Card>
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
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusInfo = (status: string) => {
    const statusLower = status.toLowerCase();
    
    if (statusLower === 'connected' || statusLower === 'active') {
      return {
        badge: (
          <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
            <CheckCircle className="w-3 h-3 mr-1" />
            Connected
          </Badge>
        ),
        iconBg: 'bg-green-50 border-green-200',
        iconColor: 'text-green-600'
      };
    } else if (statusLower === 'pending' || statusLower === 'created') {
      return {
        badge: (
          <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Pending
          </Badge>
        ),
        iconBg: 'bg-yellow-50 border-yellow-200',
        iconColor: 'text-yellow-600'
      };
    } else if (statusLower === 'disconnected' || statusLower === 'error') {
      return {
        badge: (
          <Badge className="bg-red-100 text-red-700 hover:bg-red-100">
            <AlertCircle className="w-3 h-3 mr-1" />
            Disconnected
          </Badge>
        ),
        iconBg: 'bg-red-50 border-red-200',
        iconColor: 'text-red-600'
      };
    } else {
      return {
        badge: (
          <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-100">
            {status}
          </Badge>
        ),
        iconBg: 'bg-gray-50 border-gray-200',
        iconColor: 'text-gray-600'
      };
    }
  };

  const IconComponent = getDbIcon(connection.db_type);
  const statusInfo = getStatusInfo(connection.status);
  
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

export default function Connections() {
  const { 
    data: connections, 
    isLoading: loadingConnections, 
    error: connectionsError,
    refetch: refetchConnections 
  } = useConnectionsWithDetails();
  
  const deleteConnectionMutation = useDeleteConnection();

  // Handle new connection creation
  const handleConnectionCreated = (newConnection: ApiConnection) => {
    // The connection will automatically appear in the list due to React Query's cache invalidation
    // in the useCreateConnection hook, but we can also trigger a refetch to ensure it's visible
    refetchConnections();
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

      {/* Your Connections Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-2">Your Connections</h2>
            <p className="text-sm text-muted-foreground">
              Manage your active database connections
            </p>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => refetchConnections()}
            disabled={loadingConnections}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loadingConnections ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
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
            <DatabaseCard key={template.id} databaseTemplate={template} />
          ))}
        </div>
      </div>
    </div>
  );
}
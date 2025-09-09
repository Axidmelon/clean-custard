export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Welcome to Custard Analytics</p>
      </div>
      
      <div className="flex items-center justify-center min-h-[400px] bg-card rounded-lg border border-border">
        <div className="text-center space-y-3">
          <div className="w-16 h-16 bg-primary-light rounded-full flex items-center justify-center mx-auto">
            <div className="w-8 h-8 rounded bg-primary"></div>
          </div>
          <h2 className="text-xl font-semibold text-muted-foreground">Dashboard Coming Soon</h2>
          <p className="text-muted-foreground max-w-md">
            This is where your analytics dashboard will live. Stay tuned for beautiful charts and insights.
          </p>
        </div>
      </div>
    </div>
  );
}
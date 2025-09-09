import { NavLink, useLocation } from "react-router-dom";
import { BarChart3, MessageSquare, Plug, Settings, ChevronLeft, ChevronRight, User } from "lucide-react";
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarHeader, SidebarFooter, useSidebar } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-hooks";
import { User as UserType } from "@/contexts/auth-constants";
const navigationItems = [{
  title: "Dashboard",
  url: "/",
  icon: BarChart3
}, {
  title: "Talk Data",
  url: "/talk-data",
  icon: MessageSquare
}, {
  title: "Connections",
  url: "/connections",
  icon: Plug
}];
export function AppSidebar() {
  const sidebarContext = useSidebar();
  const location = useLocation();
  const authContext = useAuth();
  
  // Safety check to prevent useSidebar error
  if (!sidebarContext || !authContext) {
    return null;
  }
  
  const {
    open,
    setOpen
  } = sidebarContext as { open: boolean; setOpen: (open: boolean) => void };
  const { user } = authContext as { user: UserType | null };
  const currentPath = location.pathname;
  const isActive = (path: string) => {
    if (path === "/") return currentPath === "/";
    return currentPath.startsWith(path);
  };
  const getNavClassName = (path: string) => {
    const baseClasses = open 
      ? "w-full justify-start h-10 px-3 transition-all duration-200" 
      : "w-full justify-center h-10 px-2 transition-all duration-200";
    if (isActive(path)) {
      return `${baseClasses} bg-primary text-primary-foreground hover:bg-primary-hover`;
    }
    return `${baseClasses} hover:bg-sidebar-hover`;
  };

  const getUserDisplayName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    } else if (user?.first_name) {
      return user.first_name;
    } else if (user?.email) {
      return user.email.split('@')[0];
    }
    return 'User';
  };
  return <Sidebar className="border-r border-border bg-sidebar-bg" collapsible="icon">
      <SidebarHeader className="p-6 border-b border-border">
        {open ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-lg font-semibold text-foreground">Custard</h1>
                <p className="text-sm text-muted-foreground">Analytics</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOpen(!open)}
              className="h-8 w-8 p-0 hover:bg-sidebar-hover"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary-foreground" />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOpen(!open)}
              className="h-6 w-6 p-0 hover:bg-sidebar-hover"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        )}
      </SidebarHeader>

      <SidebarContent className={`flex-1 py-6 ${open ? 'px-4' : 'px-2'}`}>
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel className="px-3 mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {open ? "Navigation" : ""}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-2">
              {navigationItems.map(item => <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <NavLink to={item.url} className={getNavClassName(item.url)}>
                      <item.icon className="w-4 h-4" />
                      {open && <span className="ml-3">{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>)}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className={`border-t border-border ${open ? 'p-4' : 'p-2'}`}>
        <SidebarMenu className="space-y-2">
          {/* User Info */}
          {open && user && (
            <div className="px-3 py-2 bg-muted/30 rounded-md">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                  <User className="w-3 h-3 text-primary-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {getUserDisplayName()}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {user.email}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Settings">
              <NavLink to="/settings" className={getNavClassName("/settings")}>
                <Settings className="w-4 h-4" />
                {open && <span className="ml-3">Settings</span>}
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>;
}
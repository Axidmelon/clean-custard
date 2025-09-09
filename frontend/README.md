# Custard Frontend

A modern React application built with TypeScript, providing a beautiful and intuitive interface for the Custard AI Data Agent Platform. This frontend enables users to manage database connections, ask natural language questions, and interact with their data through an AI-powered interface.

## 🚀 Features

- **User Authentication**: Complete signup, login, and email verification system
- **Database Connection Management**: Real-time UI for creating, viewing, and managing database connections
- **Natural Language Queries**: Interactive interface for asking questions about your data
- **Real-time Updates**: Live connection status and data synchronization
- **Modern UI**: Beautiful, accessible components built with shadcn/ui
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Type Safety**: Full TypeScript implementation for better development experience

## 🛠️ Technology Stack

- **React 18**: Modern UI library with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript for better development experience
- **Vite**: Lightning-fast build tool and development server
- **shadcn/ui**: Beautiful, accessible UI components built on Radix UI
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **React Router**: Client-side routing for single-page application
- **React Query**: Powerful data fetching and caching library
- **React Hook Form**: Performant forms with easy validation
- **Lucide React**: Beautiful, customizable SVG icons
- **Sonner**: Toast notifications for user feedback

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── layout/          # Layout components (AppLayout, AppSidebar)
│   │   └── ui/              # shadcn/ui components
│   ├── contexts/            # React contexts (AuthContext)
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility functions and configurations
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── Connections.tsx  # Database connections management
│   │   ├── TalkData.tsx     # Natural language query interface
│   │   ├── Settings.tsx     # User settings
│   │   ├── Login.tsx        # User login
│   │   ├── Signup.tsx       # User registration
│   │   └── ...              # Other pages
│   ├── services/            # API service layer
│   ├── types/               # TypeScript type definitions
│   └── App.tsx              # Main application component
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
└── vite.config.ts          # Vite configuration
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://127.0.0.1:8000`

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env` file in the frontend directory:
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run build:dev` - Build for development
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality

## 🎨 UI Components

This project uses [shadcn/ui](https://ui.shadcn.com/) for beautiful, accessible components. Key components include:

- **Forms**: Input, Button, Card, Dialog, Select, etc.
- **Layout**: Sidebar, Navigation, Tabs, etc.
- **Feedback**: Toast, Alert, Progress, etc.
- **Data Display**: Table, Badge, Avatar, etc.

## 🔐 Authentication Flow

The application implements a complete authentication system:

1. **Registration**: Users can create accounts with email verification
2. **Login**: Secure JWT-based authentication
3. **Email Verification**: Required for account activation
4. **Password Reset**: Secure password recovery via email
5. **Protected Routes**: Automatic redirection for unauthenticated users

## 📊 Database Connections

The connections page provides:

- **Connection List**: View all database connections with real-time status
- **Create Connection**: Add new database connections (PostgreSQL, MySQL, MongoDB, Snowflake)
- **Connection Details**: View connection information, schema status, and record counts
- **Real-time Updates**: Live status updates and automatic refresh
- **Delete Connections**: Remove connections with confirmation

## 🔍 Natural Language Queries

The TalkData page enables:

- **Question Input**: Natural language question interface
- **Connection Selection**: Choose which database to query
- **Real-time Results**: Live query execution and results display
- **Query History**: View previous questions and answers
- **Error Handling**: User-friendly error messages and retry options

## 🎯 Key Features

### Real-time Data Synchronization
- WebSocket connections for live updates
- Automatic refresh of connection status
- Real-time query results

### Type Safety
- Full TypeScript implementation
- Strict type checking
- IntelliSense support for better development

### Responsive Design
- Mobile-first approach
- Adaptive layouts for all screen sizes
- Touch-friendly interactions

### Accessibility
- WCAG compliant components
- Keyboard navigation support
- Screen reader compatibility

## 🔧 Development

### Code Structure
- **Components**: Reusable UI components in `/src/components`
- **Pages**: Route components in `/src/pages`
- **Hooks**: Custom React hooks in `/src/hooks`
- **Services**: API integration in `/src/services`
- **Types**: TypeScript definitions in `/src/types`

### State Management
- **React Query**: Server state management and caching
- **React Context**: Global state (authentication)
- **Local State**: Component-level state with useState/useReducer

### Styling
- **Tailwind CSS**: Utility-first CSS framework
- **CSS Variables**: Consistent theming system
- **Responsive Design**: Mobile-first approach

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Environment Variables
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_APP_NAME`: Application name
- `VITE_APP_VERSION`: Application version

### Deployment Platforms
- **Vercel**: Recommended for easy deployment
- **Netlify**: Alternative deployment option
- **Docker**: Containerized deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the main [README](../../README.md) for complete setup
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

---

**Version**: 1.0.0  
**Last Updated**: January 2025
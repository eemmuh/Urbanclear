# Urbanclear Dashboard

A modern React dashboard for the Urbanclear Traffic Management System featuring real-time traffic visualization, WebSocket integration, and interactive maps.

## 🚀 Features

- **Real-time Data**: Live traffic updates via WebSocket connection
- **Interactive Maps**: Traffic visualization with Leaflet integration
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Charts & Analytics**: Real-time traffic flow charts and metrics
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **TypeScript**: Full type safety and better developer experience

## 🛠️ Technology Stack

- **React 18** - Modern React with hooks and context
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Leaflet** - Interactive maps
- **Chart.js** - Beautiful charts and graphs
- **Socket.io** - Real-time WebSocket communication
- **Zustand** - Lightweight state management
- **Framer Motion** - Smooth animations
- **React Router** - Client-side routing

## 📋 Prerequisites

Before running the dashboard, ensure you have:

1. **Node.js** (v16 or higher)
2. **npm** or **yarn**
3. **Urbanclear API** running on `http://localhost:8000`

### Installing Node.js

If Node.js is not installed:

**macOS (using Homebrew):**
```bash
brew install node
```

**macOS (using Node Version Manager):**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal or source profile
source ~/.zshrc

# Install latest Node.js
nvm install node
nvm use node
```

**Alternative (Download):**
Visit [nodejs.org](https://nodejs.org/) and download the installer.

## 🚀 Getting Started

1. **Install Dependencies:**
   ```bash
   cd dashboard
   npm install
   ```

2. **Start Development Server:**
   ```bash
   npm run dev
   ```

3. **Access Dashboard:**
   Open [http://localhost:3000](http://localhost:3000) in your browser

## 📁 Project Structure

```
dashboard/
├── public/                 # Static files
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── charts/       # Chart components
│   │   └── maps/         # Map components
│   ├── pages/            # Page components
│   ├── stores/           # Zustand state stores
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── styles/           # CSS files
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
├── package.json          # Dependencies and scripts
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── tsconfig.json         # TypeScript configuration
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

## 🎯 Key Components

### Dashboard Page
- **Overview metrics** - Key traffic statistics
- **Real-time map** - Live traffic visualization
- **Traffic charts** - Flow trends and analytics
- **Incident list** - Recent traffic incidents

### Traffic Page
- **Interactive map** - Detailed traffic visualization
- **Traffic trends** - Historical data charts
- **Metric selection** - Speed, flow rate, congestion

### Incidents Page
- **Active incidents** - Current traffic issues
- **Incident management** - Resolve and track incidents
- **Historical data** - Recently resolved incidents

## 🌐 API Integration

The dashboard connects to the Urbanclear API at `http://localhost:8000`:

### HTTP Endpoints
- `GET /api/v1/traffic/current` - Current traffic data
- `GET /api/v1/incidents/active` - Active incidents
- `GET /api/v1/dashboard/stats` - Dashboard statistics

### WebSocket Connection
- Real-time traffic updates
- Incident alerts
- System status updates

## 🎨 Styling

The dashboard uses **Tailwind CSS** for styling:

- **Utility-first** approach
- **Responsive design** with mobile-first breakpoints
- **Custom color palette** for traffic system
- **Dark mode ready** (can be enabled)

### Custom CSS Classes

```css
.card                    /* Standard card component */
.card-header            /* Card header section */
.card-content           /* Card content area */
.btn                    /* Base button styles */
.status-online          /* Online status indicator */
.loading-spinner        /* Loading animation */
```

## 🔌 WebSocket Integration

Real-time features powered by Socket.io:

```typescript
// WebSocket events
socket.on('traffic_update', (data) => {
  // Handle traffic data updates
})

socket.on('incident_alert', (data) => {
  // Handle new incident alerts
})
```

## 📊 State Management

Using **Zustand** for simple, effective state management:

```typescript
// Traffic Store
const useTrafficStore = create((set) => ({
  trafficData: [],
  incidents: [],
  setTrafficData: (data) => set({ trafficData: data }),
  addIncident: (incident) => set((state) => ({
    incidents: [incident, ...state.incidents]
  }))
}))
```

## 🗺️ Maps Integration

Interactive maps using **React Leaflet**:

- **Traffic flow visualization** - Colored circles based on congestion
- **Incident markers** - Custom icons for different incident types
- **Popups** - Detailed information on click
- **Auto-fitting bounds** - Automatically centers on data

## 📱 Responsive Design

Mobile-optimized with:

- **Collapsible sidebar** on mobile devices
- **Touch-friendly** controls and buttons
- **Responsive grid** layouts
- **Optimized map** interactions

## 🚀 Deployment

### Production Build

```bash
npm run build
```

### Deploy with Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dashboard/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Environment Variables

Create `.env` file for configuration:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Ensure API server is running
   - Check firewall settings
   - Verify WebSocket endpoint

2. **Map not loading**
   - Check internet connection for tile loading
   - Verify Leaflet CSS is loaded

3. **Charts not displaying**
   - Ensure Chart.js dependencies are installed
   - Check data format matches expected structure

### Development Issues

```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🤝 Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test responsive design on multiple devices
4. Update documentation for new components

## 📄 License

This project is part of the Urbanclear Traffic Management System.

---

For more information about the complete system, see the main [README](../README.md). 
# Frontend Design Document - Surveillance System

## 1. Executive Summary

The frontend is a modern web application built with React.js and TypeScript that provides an intuitive interface for managing surveillance cameras, defining regions of interest (ROIs), configuring event detection, and monitoring alerts. The design emphasizes real-time updates, responsive layouts, and user-friendly interactions for security personnel.

## 2. Technology Stack

### 2.1 Core Technologies
- **Framework**: React 18 with TypeScript
- **State Management**: Redux Toolkit with RTK Query
- **UI Library**: Material-UI (MUI) v5
- **Routing**: React Router v6
- **Styling**: Styled Components + MUI Theme
- **Real-time Communication**: Socket.io-client
- **Video Processing**: WebRTC + HLS.js
- **Canvas Drawing**: Fabric.js for polygon drawing
- **HTTP Client**: Axios
- **Build Tool**: Vite

### 2.2 Development Tools
- **Linting**: ESLint + Prettier
- **Testing**: Jest + React Testing Library
- **Type Checking**: TypeScript strict mode
- **Bundle Analysis**: Bundle Analyzer
- **Development Server**: Vite Dev Server

## 3. Application Architecture

### 3.1 Component Hierarchy
```
App
├── AuthProvider
├── SocketProvider
├── ThemeProvider
├── Router
│   ├── Public Routes
│   │   ├── LoginPage
│   │   └── ForgotPasswordPage
│   └── Protected Routes
│       ├── Layout
│       │   ├── Header
│       │   ├── Sidebar
│       │   └── MainContent
│       ├── Dashboard
│       ├── CameraManagement
│       │   ├── CameraList
│       │   ├── CameraForm
│       │   └── CameraDetail
│       ├── ROIManagement
│       │   ├── ROICanvas
│       │   ├── ROIList
│       │   └── ROIForm
│       ├── EventManagement
│       │   ├── EventTypeList
│       │   ├── EventTypeForm
│       │   └── EventScheduler
│       ├── EventLogs
│       │   ├── LogTable
│       │   ├── LogFilters
│       │   └── LogDetail
│       ├── LiveMonitoring
│       │   ├── VideoGrid
│       │   ├── VideoPlayer
│       │   └── AlertPanel
│       ├── Settings
│       │   ├── UserProfile
│       │   ├── SystemSettings
│       │   └── AlertSettings
│       └── Reports
│           ├── EventReport
│           ├── SystemReport
│           └── ExportTools
```

### 3.2 State Management Structure
```typescript
// Redux Store Structure
interface RootState {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
  };
  cameras: {
    list: Camera[];
    current: Camera | null;
    loading: boolean;
    error: string | null;
  };
  rois: {
    list: ROI[];
    current: ROI | null;
    drawingMode: boolean;
    selectedROI: number | null;
  };
  events: {
    logs: EventLog[];
    types: EventType[];
    filters: EventFilters;
    pagination: PaginationState;
  };
  alerts: {
    queue: Alert[];
    active: boolean;
    settings: AlertSettings;
  };
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    notifications: Notification[];
  };
}
```

## 4. Page-by-Page Design

### 4.1 Login Page

**Purpose**: User authentication and system access

**Components**:
- **LoginForm**: Username, password fields with validation
- **RememberMe**: Checkbox for session persistence
- **ForgotPassword**: Link to password recovery
- **SystemInfo**: Display system status and version

**Design Features**:
- Clean, centered layout with company branding
- Form validation with real-time feedback
- Loading states during authentication
- Error handling for invalid credentials
- Responsive design for mobile devices

**User Flow**:
1. User enters credentials
2. Client-side validation
3. API call to authentication endpoint
4. JWT token storage
5. Redirect to dashboard
6. WebSocket connection establishment

### 4.2 Dashboard

**Purpose**: Overview of system status and recent activity

**Layout**: Grid-based responsive layout

**Components**:
- **SystemStatusCards**: Active cameras, alerts today, system health
- **RecentEventsTable**: Last 10 events with quick actions
- **CameraHealthGrid**: Visual status of all cameras
- **AlertSummaryChart**: Event types distribution
- **QuickActions**: Common tasks shortcuts

**Real-time Updates**:
- Live camera status updates
- New event notifications
- System health monitoring
- Alert queue status

**Interactions**:
- Click events to view details
- Click cameras to view live feed
- Filter events by type or time
- Export dashboard data

### 4.3 Camera Management

**Purpose**: Add, edit, and manage camera profiles

**Layout**: Split view with list and detail panel

**Components**:
- **CameraList**: Searchable, filterable list of cameras
- **CameraCard**: Visual representation with status indicator
- **CameraForm**: Add/edit camera configuration
- **ConnectionTest**: Test DVR connectivity
- **BulkActions**: Multiple camera operations

**Camera Form Fields**:
- Basic Information: Name, description, location
- Connection Details: DVR string, RTSP URL, credentials
- Technical Settings: Resolution, FPS, timezone
- Status Management: Active/inactive toggle

**Features**:
- Real-time connection status
- Thumbnail preview from camera
- Duplicate detection for camera IDs
- Import/export camera configurations

### 4.4 ROI Management

**Purpose**: Define and manage regions of interest for each camera

**Layout**: Main video canvas with sidebar controls

**Components**:
- **VideoCanvas**: Live video feed with overlay capabilities
- **DrawingTools**: Polygon drawing, editing, deletion tools
- **ROIList**: List of ROIs for current camera
- **ROIProperties**: Edit ROI name, color, sensitivity
- **PreviewMode**: Test ROI with sample detections

**Drawing Interface**:
- Click to add polygon vertices
- Right-click to complete polygon
- Drag vertices to edit shape
- Delete button to remove ROI
- Color picker for ROI visualization
- Sensitivity slider for detection threshold

**Features**:
- Snap-to-grid for precise drawing
- Undo/redo functionality
- Copy/paste ROIs between cameras
- Import ROI coordinates from file
- Export ROI configurations

### 4.5 Event Management

**Purpose**: Configure event types and scheduling for ROIs

**Layout**: Tabbed interface for different event configurations

**Components**:
- **EventTypeManager**: Create/edit event types
- **EventScheduler**: Time-based scheduling interface
- **DaySelector**: Visual day-of-week selector
- **TimeRangePicker**: Start/end time selection
- **AlertConfiguration**: Voice alert settings

**Event Type Configuration**:
- Name and description
- Category (security, safety, operational)
- Severity level (low, medium, high, critical)
- Default voice alert
- Detection algorithm parameters

**Scheduling Interface**:
- Visual calendar for day selection
- Time range sliders with validation
- Multiple time slots per day
- Holiday/exception handling
- Bulk schedule updates

**Features**:
- Template system for common schedules
- Conflict detection for overlapping events
- Preview schedule in timeline view
- Copy schedules between ROIs

### 4.6 Live Monitoring

**Purpose**: Real-time video monitoring and alert management

**Layout**: Grid layout with control panel

**Components**:
- **VideoGrid**: Configurable grid of camera feeds
- **VideoPlayer**: Individual camera view with controls
- **AlertPanel**: Real-time alert notifications
- **ControlBar**: Playback, recording, snapshot controls
- **FullscreenMode**: Immersive monitoring experience

**Video Grid Features**:
- Configurable grid sizes (1x1, 2x2, 3x3, 4x4)
- Drag-and-drop to rearrange cameras
- Double-click for fullscreen view
- Camera status indicators
- FPS and bandwidth display

**Alert Panel**:
- Real-time alert notifications
- Alert priority indicators
- Acknowledge/dismiss actions
- Alert history for current session
- Sound toggle for voice alerts

**Controls**:
- Start/stop recording
- Take snapshots
- Digital zoom controls
- Pan/tilt controls (if supported)
- Audio mute/unmute

### 4.7 Event Logs

**Purpose**: View and manage historical event data

**Layout**: Table view with advanced filtering

**Components**:
- **EventTable**: Sortable, filterable event list
- **FilterPanel**: Comprehensive filtering options
- **EventDetail**: Detailed event information modal
- **VideoPlayer**: Event clip playback
- **ExportTools**: Data export functionality

**Filtering Options**:
- Date/time range picker
- Camera selection
- Event type filtering
- Confidence score range
- Alert status filtering
- Text search in notes

**Table Features**:
- Sortable columns
- Pagination with configurable page size
- Row selection for bulk actions
- Inline preview thumbnails
- Real-time updates for new events

**Event Details**:
- Full video clip playback
- Detection bounding boxes
- Event metadata
- User acknowledgment history
- Related events timeline

### 4.8 Settings

**Purpose**: System configuration and user preferences

**Layout**: Multi-section settings panel

**Components**:
- **UserProfile**: User account management
- **SystemSettings**: Global system configuration
- **AlertSettings**: Alert preferences
- **SecuritySettings**: Authentication and permissions
- **BackupSettings**: Data backup configuration

**User Profile**:
- Personal information
- Password change
- Notification preferences
- Theme selection
- Language selection

**System Settings**:
- Database configuration
- Storage management
- Performance tuning
- Logging configuration
- Update management

## 5. Component Design Details

### 5.1 VideoCanvas Component

**Purpose**: Display video feeds with interactive overlays

**Props**:
```typescript
interface VideoCanvasProps {
  streamUrl: string;
  rois: ROI[];
  mode: 'view' | 'draw' | 'edit';
  onROICreate: (coordinates: Point[]) => void;
  onROIUpdate: (roiId: number, coordinates: Point[]) => void;
  onROIDelete: (roiId: number) => void;
  onDetection: (detection: Detection) => void;
}
```

**Features**:
- WebRTC/HLS video streaming
- Canvas overlay for ROIs
- Real-time detection visualization
- Zoom and pan controls
- Fullscreen support
- Screenshot capability

**Drawing Modes**:
- **View Mode**: Only display existing ROIs
- **Draw Mode**: Create new ROIs with polygon drawing
- **Edit Mode**: Modify existing ROI vertices

### 5.2 AlertNotification Component

**Purpose**: Display real-time alerts to users

**Props**:
```typescript
interface AlertNotificationProps {
  alert: Alert;
  onAcknowledge: (alertId: number) => void;
  onDismiss: (alertId: number) => void;
  onPlaySound: (alertPath: string) => void;
}
```

**Visual Design**:
- Color-coded priority indicators
- Slide-in animation from right
- Auto-dismiss after configurable time
- Stacking for multiple alerts
- Mobile-responsive design

**Interactions**:
- Click to acknowledge alert
- Dismiss button to hide
- Play voice alert sound
- View event details
- Go to live camera feed

### 5.3 EventScheduler Component

**Purpose**: Visual time-based event scheduling

**Props**:
```typescript
interface EventSchedulerProps {
  roiId: number;
  events: ROIEvent[];
  eventTypes: EventType[];
  onEventCreate: (event: CreateROIEventRequest) => void;
  onEventUpdate: (eventId: number, event: Partial<ROIEvent>) => void;
  onEventDelete: (eventId: number) => void;
}
```

**Visual Design**:
- Weekly calendar view
- Color-coded event types
- Drag-and-drop event creation
- Resize events to adjust duration
- Conflict highlighting

**Features**:
- Multiple event types per ROI
- Overlap detection
- Template application
- Bulk editing capabilities
- Schedule preview

## 6. Real-time Features

### 6.1 WebSocket Integration

**Connection Management**:
- Automatic reconnection with exponential backoff
- Connection status indicators
- Heartbeat/ping-pong for connection health
- Authentication token management

**Event Types**:
- **camera_status**: Camera connection changes
- **event_detected**: New event notifications
- **alert_triggered**: Alert generation
- **system_status**: System health updates
- **user_activity**: Other user actions

**Message Handling**:
```typescript
interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  userId?: string;
}
```

### 6.2 Real-time Updates

**Dashboard Updates**:
- Live camera status changes
- New event count updates
- System health metrics
- Alert queue status

**Live Monitoring**:
- Real-time detection overlays
- Live alert notifications
- Camera feed status updates
- Bandwidth and performance metrics

**Event Logs**:
- New events appear immediately
- Real-time filtering updates
- Live acknowledgment status
- Current user activity indicators

## 7. User Experience Design

### 7.1 Responsive Design

**Breakpoints**:
- **Mobile**: < 600px (320px-599px)
- **Tablet**: 600px-959px
- **Desktop**: 960px-1279px
- **Large Desktop**: ≥ 1280px

**Mobile Adaptations**:
- Collapsible navigation
- Touch-friendly controls
- Simplified layouts
- Swipe gestures for navigation
- Optimized video grid (1x1, 2x2)

**Tablet Optimizations**:
- Split-view layouts
- Touch-optimized controls
- Adaptive grid sizes
- Gesture-based interactions

### 7.2 Accessibility Features

**WCAG 2.1 AA Compliance**:
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode
- Focus indicators
- ARIA labels and descriptions

**Visual Accessibility**:
- Adjustable font sizes
- Color blind friendly palettes
- Sufficient color contrast ratios
- Clear visual hierarchy
- Consistent iconography

**Motor Accessibility**:
- Large click targets
- Gesture alternatives
- Voice control support
- Reduced motion options
- Keyboard shortcuts

### 7.3 Performance Optimization

**Lazy Loading**:
- Route-based code splitting
- Component lazy loading
- Image lazy loading
- Video stream optimization

**Caching Strategy**:
- API response caching
- Static asset caching
- Video frame caching
- User preference caching

**Optimization Techniques**:
- Virtual scrolling for large lists
- Debounced search inputs
- Throttled resize events
- Optimized re-renders
- Memory leak prevention

## 8. Error Handling

### 8.1 Error Boundaries

**Component-level Error Boundaries**:
- Individual component isolation
- Graceful fallbacks
- Error reporting integration
- User-friendly error messages

**Global Error Handling**:
- Unhandled promise rejections
- Network error handling
- Authentication errors
- WebSocket connection errors

### 8.2 User Feedback

**Loading States**:
- Skeleton screens
- Progress indicators
- Spinners for async operations
- Loading bars for uploads

**Error Messages**:
- Clear, actionable error messages
- Error context and suggestions
- Retry mechanisms where appropriate
- Contact support options

**Success Feedback**:
- Toast notifications for actions
- Confirmation dialogs
- Progress indicators
- Completion messages

## 9. Security Considerations

### 9.1 Client-side Security

**Authentication Security**:
- Secure token storage (httpOnly cookies or secure localStorage)
- Token expiration handling
- Automatic logout on inactivity
- Multi-tab synchronization

**Input Validation**:
- Client-side validation with server verification
- XSS prevention
- CSRF protection
- Input sanitization

### 9.2 Data Protection

**Sensitive Data Handling**:
- No sensitive data in localStorage
- Encrypted communication
- Secure file uploads
- Data masking in logs

**Privacy Features**:
- User consent management
- Data anonymization options
- Right to deletion implementation
- Audit trail for data access

## 10. Testing Strategy

### 10.1 Unit Testing

**Component Testing**:
- Individual component behavior
- Props validation
- State changes
- Event handling

**Utility Testing**:
- Helper functions
- Custom hooks
- Utility modules
- Business logic

### 10.2 Integration Testing

**API Integration**:
- HTTP client interactions
- Error handling
- Data transformation
- Authentication flows

**WebSocket Testing**:
- Connection management
- Message handling
- Reconnection logic
- Event processing

### 10.3 End-to-End Testing

**User Workflows**:
- Complete user journeys
- Critical path testing
- Cross-browser compatibility
- Mobile device testing

**Performance Testing**:
- Load testing for multiple streams
- Memory usage monitoring
- Network performance
- Rendering performance

## 11. Deployment

### 11.1 Build Process

**Development Build**:
- Fast rebuild times
- Source maps for debugging
- Hot module replacement
- Development server

**Production Build**:
- Code minification
- Tree shaking
- Asset optimization
- Bundle analysis

### 11.2 Deployment Strategy

**Static Asset Hosting**:
- CDN integration
- Cache headers
- Compression
- Version management

**Environment Configuration**:
- Environment variables
- API endpoint configuration
- Feature flags
- Debug mode controls

## 12. Future Enhancements

### 12.1 Advanced Features

**AI-Powered Features**:
- Smart ROI suggestions
- Anomaly detection visualization
- Predictive analytics dashboard
- Automated threat assessment

**User Experience**:
- Voice control interface
- Mobile app integration
- AR/VR monitoring
- Gesture-based controls

### 12.2 Performance Improvements

**Advanced Optimization**:
- WebAssembly for video processing
- Service worker caching
- Progressive Web App features
- Edge computing integration

**Scalability Features**:
- Micro-frontend architecture
- Component lazy loading
- Dynamic imports
- Code splitting by feature

## 13. Conclusion

The frontend design provides a comprehensive, user-friendly interface for surveillance system management. The architecture emphasizes real-time updates, responsive design, and accessibility while maintaining high performance for video processing and alert management.

The modular component design allows for easy maintenance and future enhancements, while the robust testing strategy ensures reliability across different devices and browsers. The security-focused approach protects sensitive surveillance data while providing an intuitive user experience for security personnel.

The design balances powerful functionality with ease of use, making the system accessible to both technical and non-technical users while supporting the complex requirements of modern surveillance operations.

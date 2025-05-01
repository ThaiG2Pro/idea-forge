## UI Design Template (MVP Web Application)

### Core Pages
- **Authentication**:
  - Login: Email/Password fields, Submit button, Password recovery link
  - Registration (optional): Email, Password, Terms acceptance
- **Main Dashboard**:
  - Components:
    - Header (with user info/avatar)
    - Navigation (sidebar or top nav)
    - Content area (metrics/data visualization)

### Responsive Design Specifications
- **Mobile First Approach**:
  - Small screens: Full width cards, stacked layout, 90-95% width
  - Tablet: Semi-expanded layout, 80-90% width
  - Desktop: Optimized layout, fixed width containers (1000-1200px max)
- **Navigation**:
  - Mobile: Hamburger menu or bottom tabs
  - Desktop: Sidebar or horizontal top navigation

### Standard User Flow
1. User authentication (login/register)
2. Landing on dashboard/home view
3. Core feature navigation (3-5 main sections)
4. Settings/profile access
5. Logout functionality

### MVP Style Guide
- **Color System**:
  - Primary: #3B82F6 (blue) - main actions, key UI elements
  - Secondary: #10B981 (green) - success states, positive indicators
  - Accent: #F59E0B (amber) - attention, warnings
  - Neutral: #F9FAFB (light gray) - backgrounds
  - Text: #1F2937 (dark gray) - primary text
- **Typography**:
  - System fonts stack for performance: 
    - `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif`
  - Sizes: 14px (small), 16px (body), 18px (h3), 20px (h2), 24px (h1)
- **UI Components**:
  - Buttons: 8px radius, clear hover states, 40-44px height
  - Cards: White background, subtle shadows, 16px padding
  - Form inputs: 40px height, visible focus states
- **Spacing System**:
  - Base unit: 4px
  - Common spacing: 16px (compact), 24px (default), 32px (spacious)
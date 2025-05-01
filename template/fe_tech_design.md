# Frontend Technical Design Template for MVP Web Applications

## Framework Options
- **Modern SPA**: React + Vite + TailwindCSS
- **Alternative Options**: 
  - Next.js + TailwindCSS (for SSR/SEO needs)
  - Vue.js + Vite + Tailwind (if team prefers Vue)

## Recommended Folder Structure
- `/components`: Reusable UI components
  - `/common`: Buttons, inputs, cards, modals
  - `/layout`: Headers, footers, navigation, containers
  - `/features`: Feature-specific complex components
- `/pages`: Page-level components and routes
- `/services`: API calls and external integrations
- `/hooks`: Custom React hooks
- `/utils`: Helper functions and utilities
- `/context`: Context providers for state management
- `/assets`: Images, icons, and static resources
- `/styles`: Global styles and Tailwind customization

## State Management
- **Simple MVPs**: React Hooks + Context API
- **Complex State**: Consider Redux Toolkit or Zustand

## Authentication
- JWT token storage in localStorage/cookies
- Protected route wrappers
- Auth context provider

## Common Routes
- `/login`: User authentication
- `/register`: New user signup (if needed)
- `/dashboard`: Main user interface
- `/profile`: User settings and information
- `/[resource]`: Main resource views
- `/[resource]/:id`: Detail views for specific resources

## Responsive Design
- Mobile-first approach with Tailwind breakpoints
- Consistent component sizing and spacing system

## Performance Considerations
- Lazy loading for routes
- Image optimization
- Component memoization where beneficial
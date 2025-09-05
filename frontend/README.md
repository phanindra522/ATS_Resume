# ATS Scoring Assistant - Frontend

React frontend for the ATS Scoring Assistant built with Vite, TailwindCSS, and TypeScript.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Vite 7.1.4+ (latest stable)

### Installation

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

4. **Open in browser**
Navigate to http://localhost:5173

**Development server will be available at:** http://localhost:5173
**Network access:** http://192.168.0.102:5173 (for mobile testing)

## 🏗️ Build for Production

```bash
npm run build
npm run preview
```

## 🎨 Design System

### Swiss Design Principles
- **Clean & Minimal**: White backgrounds with strategic whitespace
- **Typography-First**: Clear hierarchy using Inter font
- **Functional Beauty**: Every element serves a purpose
- **Consistent Spacing**: Systematic use of spacing and proportions

### Color Palette
- **Primary**: Blue (#2563EB)
- **Surface**: Light gray (#FAFAFA)
- **Text**: Black (#111111), Secondary (#6B7280)
- **Success**: Green (#059669)
- **Warning**: Orange (#D97706)
- **Error**: Red (#DC2626)

### Components
- **Cards**: White background, rounded corners, subtle shadows
- **Buttons**: Primary (blue), Secondary (white with border)
- **Inputs**: Full-width, rounded, focus states
- **Navigation**: Clean, minimal with active states

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utilities and API client
│   ├── pages/         # Page components
│   ├── App.tsx        # Main application component
│   ├── main.tsx       # Application entry point
│   └── index.css      # Global styles and TailwindCSS
├── public/            # Static assets
├── package.json       # Dependencies and scripts
├── tailwind.config.js # TailwindCSS configuration
├── vite.config.ts     # Vite configuration
└── README.md          # This file
```

## 🛠️ Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api
```

### TailwindCSS
The project uses a custom TailwindCSS configuration with:
- Swiss design color palette
- Custom spacing and border radius
- Custom animations and keyframes
- Component-specific utility classes

## 📱 Responsive Design

The application is fully responsive with:
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Flexible grid layouts
- Touch-friendly interactions

## 🎯 Key Features

### Authentication
- Login/Signup forms with validation
- JWT token management
- Protected routes
- User profile management

### Resume Management
- Drag & drop file upload
- PDF/DOCX support
- File validation and error handling
- Upload progress indicators

### Job Descriptions
- Comprehensive job creation forms
- Skills and requirements input
- Experience level selection
- Form validation

### Scoring Results
- AI-powered candidate ranking
- Visual score representation
- Skills matching analysis
- Detailed candidate profiles

## 🚀 Performance Optimizations

- **Code Splitting**: Route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Optimized Images**: SVG icons and optimized assets
- **Bundle Analysis**: Built-in Vite bundle analyzer

## 🧪 Testing

```bash
# Install testing dependencies
npm install -D @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```

## 📦 Dependencies

### Core
- **React 18** - UI library
- **React Router** - Client-side routing
- **TypeScript** - Type safety

### Styling
- **TailwindCSS** - Utility-first CSS framework
- **Lucide React** - Icon library

### State Management
- **React Hooks** - Built-in state management
- **Context API** - Global state

### HTTP Client
- **Axios** - HTTP client with interceptors

### UI/UX
- **React Dropzone** - File upload handling
- **React Hot Toast** - Toast notifications

## 🔒 Security Features

- **JWT Authentication**: Secure token-based auth
- **Route Protection**: Protected routes for authenticated users
- **Input Validation**: Client-side form validation
- **XSS Protection**: Safe HTML rendering

## 🌐 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Change port in `vite.config.ts`
   - Kill existing processes on port 5173

2. **Build Errors**
   - Clear `node_modules` and reinstall
   - Check TypeScript errors
   - Verify all dependencies are installed

3. **API Connection Issues**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints

4. **Styling Issues**
   - Clear browser cache
   - Restart development server
   - Check TailwindCSS configuration

## 📞 Support

For issues and questions, please check the main project README or create an issue in the repository.

## 🎨 Customization

### Adding New Pages
1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Update navigation in `src/components/Navbar.tsx`

### Styling Changes
1. Modify `src/index.css` for global styles
2. Update `tailwind.config.js` for theme changes
3. Use component-specific classes for local styling

### Adding New Features
1. Create components in `src/components/`
2. Add API calls in `src/lib/api.ts`
3. Update types and interfaces as needed

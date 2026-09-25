const fs = require('fs');
let content = fs.readFileSync('src/main.jsx', 'utf8');

// Add import
if (!content.includes('import BookingPage')) {
  content = content.replace("import PermissionManager from './components/PermissionManager';", 
    "import PermissionManager from './components/PermissionManager';\nimport BookingPage from './components/BookingPage';");
}

// Add to PAGE_TITLES
if (!content.includes('booking: [')) {
  content = content.replace("overview: ['Overview'", "booking: ['Booking & Orders', 'Manage customer bookings and recoveries'],\n  overview: ['Overview'");
}

// Add to renderPage switch case
if (!content.includes('<BookingPage />')) {
  const switchStr = 'switch(activePage) {';
  content = content.replace(switchStr, switchStr + "\n      case 'booking':\n        return <BookingPage />;\n");
}

// Add to NAV Operations
if (!content.includes("key: 'booking'")) {
  const opStr = "{ group: 'Operations', items: [";
  const navItemStr = "{ group: 'Operations', items: [\n      { key: 'booking', label: 'Bookings', roles: ['Super_Admin', 'Manager'], icon: <svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" strokeWidth=\"1.8\"><path d=\"M4 19.5A2.5 2.5 0 016.5 17H20\"/><path d=\"M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z\"/></svg> },";
  content = content.replace(opStr, navItemStr);
}

fs.writeFileSync('src/main.jsx', content, 'utf8');
console.log('main.jsx updated with BookingPage');

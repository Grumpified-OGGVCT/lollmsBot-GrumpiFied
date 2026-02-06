# RCL-2 Cognitive Dashboard

## Overview

The **RCL-2 Cognitive Dashboard** is a comprehensive web-based GUI for monitoring and controlling the Reflective Consciousness Layer v2.0 of the LollmsBot AI system. It provides real-time visibility into the system's cognitive processes, constitutional restraints, council deliberations, and cognitive debt management.

## Features

### 🎛️ **Restraint Matrix Control Panel**
- **12 Constitutional Dimensions** organized into 4 categories:
  - **Cognitive Budgeting**: Recursion depth, cognitive budget, simulation fidelity
  - **Epistemic Virtues**: Hallucination resistance, uncertainty propagation, contradiction sensitivity
  - **Social Cognition**: User model fidelity, transparency level, explanation depth
  - **Autonomy & Growth**: Self-modification freedom, goal inference, memory consolidation
- Real-time slider controls (0.00-1.00)
- Hard-stop indicators with lock icons
- Cryptographic authorization for beyond-limit modifications
- Pending changes tracking
- Immutable audit trail integration

### 🧠 **Cognitive State Monitor**
- **System 1** (Fast Thinking) metrics:
  - Total calls
  - Total processing time
  - Average time per call
- **System 2** (Slow Thinking) metrics:
  - Total calls
  - Total processing time
  - Average time per call
- **Escalation tracking**: System 1 → System 2 transitions
- Real-time performance statistics

### 🏛️ **Reflective Council Viewer**
- **5 Council Members**:
  - **Guardian** (🛡️): Safety and ethics
  - **Epistemologist** (🔬): Truth and evidence
  - **Strategist** (♟️): Long-term consequences
  - **Empath** (💚): User wellbeing
  - **Historian** (📜): Learning from past
- Deliberation history with votes
- Conflict detection and highlighting
- Detailed perspective views
- Manual deliberation triggers

### 💳 **Cognitive Debt Dashboard**
- Outstanding debt queue (sortable table)
- Priority indicators (High/Medium/Low)
- Individual and bulk repayment
- Repayment history tracking
- Statistics and analytics
- Automated debt management

### 📋 **Audit Trail Browser**
- Chronological timeline of restraint changes
- Cryptographic hash chain verification
- Authorized vs. unauthorized attempts
- Tamper detection and alerts
- Compliance tracking

### 📊 **Decision Log Viewer**
- Complete decision history
- Confidence scores
- Decision types and context
- Filtering and sorting
- Detailed decision metadata

## Architecture

### File Structure

```
lollmsbot/ui/
├── templates/
│   └── index.html              # Main UI template (updated)
└── static/
    ├── css/
    │   ├── style.css           # Base styles
    │   └── rcl2.css            # RCL-2 dashboard styles
    └── js/
        ├── app.js              # Main app logic
        ├── rcl2-dashboard.js   # Dashboard controller
        ├── rcl2-restraints.js  # Restraint matrix
        ├── rcl2-council.js     # Council viewer
        └── rcl2-debt.js        # Debt manager
```

### Component Overview

#### **rcl2-dashboard.js** (Main Controller)
- Dashboard lifecycle management
- Tab switching and routing
- WebSocket connection for real-time updates
- API integration layer
- Toast notification system
- Keyboard shortcuts (Ctrl+K, Escape)

#### **rcl2-restraints.js** (Restraints)
- Slider control management
- Authorization modal
- Pending changes tracking
- Hard-limit enforcement
- API calls for updates

#### **rcl2-council.js** (Council)
- Member card rendering
- Deliberation history
- Vote visualization
- Conflict detection
- Test deliberation triggers

#### **rcl2-debt.js** (Debt)
- Debt queue management
- Priority sorting
- Repayment actions
- Statistics calculation
- History tracking

### API Integration

The dashboard integrates with the RCL-2 API routes at `/rcl2/*`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rcl2/restraints` | GET | Fetch current restraint values |
| `/rcl2/restraints` | POST | Update restraint dimension |
| `/rcl2/audit-trail` | GET | Get audit trail entries |
| `/rcl2/cognitive-state` | GET | Get System 1/2 metrics |
| `/rcl2/council/status` | GET | Get council composition |
| `/rcl2/council/deliberate` | POST | Trigger deliberation |
| `/rcl2/council/deliberations` | GET | Get deliberation history |
| `/rcl2/debt` | GET | Get outstanding debt |
| `/rcl2/debt/repay` | POST | Repay cognitive debt |
| `/rcl2/decisions` | GET | Get decision log |
| `/rcl2/ws` | WebSocket | Real-time updates |

## Usage

### Opening the Dashboard

1. **Click the Cognitive Button** (🧠) in the header
2. **Keyboard Shortcut**: Press `Ctrl+K` anywhere in the app
3. Dashboard opens as a full-screen overlay

### Closing the Dashboard

1. **Click the X button** in the top-right corner
2. **Press Escape** key
3. **Click outside** the dashboard (on the overlay)

### Navigation

Use the **6 tab buttons** at the top to switch between:
1. **Restraint Matrix** - Control constitutional parameters
2. **Cognitive State** - Monitor System 1/2 activity
3. **Council** - View deliberations and votes
4. **Cognitive Debt** - Manage obligations
5. **Audit Trail** - Browse change history
6. **Decision Log** - Review past decisions

### Modifying Restraints

1. Navigate to **Restraint Matrix** tab
2. Adjust sliders for desired dimensions
3. Click **Save Changes** (button enables when changes pending)
4. If beyond hard-limits, provide **authorization key** when prompted
5. Changes are logged in audit trail

### Repaying Cognitive Debt

1. Navigate to **Cognitive Debt** tab
2. View outstanding debt items sorted by priority
3. Click **Repay** on individual items, or
4. Click **Repay All Outstanding Debt** for bulk action
5. System performs deep reflection on deferred decisions

### Triggering Deliberations

1. Navigate to **Council** tab
2. Click **Trigger Test Deliberation**
3. View results modal showing:
   - Final decision
   - Individual perspectives
   - Vote breakdown
   - Detected conflicts

## Design Features

### Visual Design
- **Dark theme** with glassmorphism effects
- **Color coding**:
  - Green: Safe/Success
  - Yellow: Medium/Warning
  - Red: High/Error
  - Blue: Info/Accent
- **Smooth animations** and transitions
- **Modern card-based layout**
- **Responsive grid system**

### UX Features
- **Real-time updates** via WebSocket
- **Toast notifications** for user feedback
- **Loading states** for async operations
- **Empty states** with helpful hints
- **Keyboard shortcuts** for power users
- **Accessibility** features (ARIA labels)
- **Mobile-friendly** responsive design

### Security Features
- **Authorization modal** for sensitive operations
- **Cryptographic key verification**
- **Audit trail integrity checks**
- **Tamper detection alerts**
- **Read-only by default** (requires auth for modifications)

## Customization

### Styling

All styles are in `rcl2.css` and use CSS variables from `style.css`:

```css
--primary: #6366f1;      /* Primary accent */
--secondary: #8b5cf6;    /* Secondary accent */
--success: #10b981;      /* Success state */
--warning: #f59e0b;      /* Warning state */
--error: #ef4444;        /* Error state */
--bg-dark: #0f172a;      /* Dark background */
--bg-card: #1e293b;      /* Card background */
--text-primary: #f8fafc; /* Primary text */
```

### Configuration

Dashboard behavior can be configured in `rcl2-dashboard.js`:

```javascript
this.wsReconnectDelay = 3000;  // WebSocket reconnect delay (ms)
this.apiBase = '/rcl2';        // API base path
```

## Browser Support

- **Chrome/Edge** 90+ ✓
- **Firefox** 88+ ✓
- **Safari** 14+ ✓
- **Mobile browsers** ✓

## Performance

- **Lazy loading**: Tabs load content on-demand
- **Efficient rendering**: Virtual DOM techniques
- **Debounced updates**: Prevents excessive API calls
- **WebSocket pooling**: Shares connection across tabs
- **Optimized animations**: GPU-accelerated transforms

## Troubleshooting

### Dashboard Won't Open
- Check browser console for JavaScript errors
- Verify all script files are loaded
- Check network tab for 404 errors

### WebSocket Connection Failed
- Verify `/rcl2/ws` endpoint is available
- Check CORS settings if using different domain
- Check browser console for connection errors

### Authorization Key Not Working
- Verify key format (hexadecimal string)
- Check server logs for validation errors
- Ensure API route is properly configured

### Sliders Not Updating
- Check for pending changes indicator
- Verify API endpoint is responding
- Check browser console for errors
- Refresh page and try again

## Development

### Local Development

1. Start the LollmsBot server with UI enabled
2. Navigate to `http://localhost:57000` (or configured port)
3. Click cognitive button or press Ctrl+K
4. Make changes to JS/CSS files
5. Refresh browser to see changes

### Adding New Features

1. Add styles to `rcl2.css`
2. Add logic to appropriate component file
3. Update `rcl2-dashboard.js` if adding new tabs
4. Test in multiple browsers
5. Update this README

### Code Style

- **ES6+ JavaScript** (classes, async/await, etc.)
- **Vanilla JS** (no frameworks - maintains compatibility)
- **BEM-like CSS** naming (block__element--modifier)
- **JSDoc comments** for public methods
- **Console logging** for debugging

## Testing

### Manual Testing Checklist

- [ ] Dashboard opens and closes properly
- [ ] All 6 tabs switch correctly
- [ ] Restraint sliders move and update
- [ ] Authorization modal works
- [ ] Council deliberations display
- [ ] Debt repayment functions
- [ ] Audit trail renders correctly
- [ ] Decision log shows entries
- [ ] WebSocket connects
- [ ] Toast notifications appear
- [ ] Responsive on mobile
- [ ] Keyboard shortcuts work

### API Testing

Use the browser console to test API endpoints:

```javascript
// Test restraints endpoint
fetch('/rcl2/restraints').then(r => r.json()).then(console.log);

// Test cognitive state
fetch('/rcl2/cognitive-state').then(r => r.json()).then(console.log);

// Test deliberations
fetch('/rcl2/council/deliberations').then(r => r.json()).then(console.log);
```

## License

This GUI is part of the LollmsBot project and inherits its license (MIT).

## Credits

- **Design**: Modern dark theme inspired by current AI tool UIs
- **Icons**: Unicode emoji characters (universal compatibility)
- **Fonts**: Inter (sans-serif) + Fira Code (monospace)
- **Architecture**: Based on RCL-2 specification

## Version History

### v1.0.0 (2025-02-06)
- Initial release
- Complete 6-tab dashboard
- Restraint matrix control
- Council viewer
- Cognitive debt manager
- Audit trail browser
- Decision log viewer
- Real-time WebSocket updates
- Authorization system
- Mobile responsive design

---

**Built with ❤️ for transparent and accountable AI systems**

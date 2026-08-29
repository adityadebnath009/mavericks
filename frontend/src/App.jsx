import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import OperationsDashboard from './components/OperationsDashboard';

/**
 * LandingPageWrapper provides navigation bridge to LandingPage component.
 */
function LandingPageWrapper() {
  const navigate = useNavigate();

  const handleLaunchConsole = (mode = 'routing') => {
    const targetMode = mode === 'map' ? 'routing' : mode;
    navigate(`/console/${targetMode}`);
  };

  return <LandingPage onLaunchConsole={handleLaunchConsole} />;
}

/**
 * Main Application Root & Declarative URL Router for NAVIK Marine Decision-Support Platform.
 * Supports deep-linking, browser history navigation (Back/Forward), and URL synchronization.
 * Routes:
 *  - /                -> LandingPage
 *  - /console/:mode   -> OperationsDashboard (modes: routing, fisheries, weather, advisor)
 *  - /console         -> Redirects to /console/routing
 *  - *                -> Redirects to /
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPageWrapper />} />
        <Route path="/console/:mode" element={<OperationsDashboard />} />
        <Route path="/console" element={<Navigate to="/console/routing" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

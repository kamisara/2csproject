import { useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import Routes from "../routes/Routes";

export default function Layout() {
  const location = useLocation(); // Get current route/pathname

  // Determine if Navbar and Footer should be hidden
  // Hide them on login or signup pages
  const hideLayout =
    location.pathname === "/login" || location.pathname === "/signup";

  return (
    // Flex container to ensure footer sticks to bottom
    <div className="flex flex-col min-h-screen">
      
      {/* Render Navbar only if layout is not hidden */}
      {!hideLayout && <Navbar />}

      {/* Main content area */}
      <main className="flex-grow">
        {/* Routes component will render the matched page content */}
        <Routes />
      </main>

      {/* Render Footer only if layout is not hidden */}
      {!hideLayout && <Footer />}
    </div>
  );
}

import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
  useNavigate,
} from "react-router-dom";
import RightSlideModal from "./Components/RightSlideModal";
import AuthRedirect from "./Components/AuthRedirect";

const SuccessPage = ({ openModal }) => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const shouldShowForm = params.get("showForm") === "true";
    if (shouldShowForm) {
      openModal();
      navigate("/"); // clean URL
    }
  }, [location, openModal, navigate]);

  return <h2>Integration Successful</h2>;
};

const Home = ({ openModal }) => (
  <div>
    <button
      onClick={openModal}
      style={{ padding: "10px 20px", fontSize: "16px" }}
    >
      Open Integration Form
    </button>
  </div>
);

const App = () => {
  const [showForm, setShowForm] = useState(false);

  const openModal = () => setShowForm(true);
  const closeModal = () => setShowForm(false);

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <div>
              <button
                onClick={openModal}
                style={{ padding: "10px 20px", fontSize: "16px" }}
              >
                Open Integration Form
              </button>
            </div>
          }
        />
        {/* other routes... */}
      </Routes>

      {showForm && <RightSlideModal onClose={() => setShowForm(false)} />}
    </Router>
  );
};

export default App;

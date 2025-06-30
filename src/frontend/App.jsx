import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import RightSlideModal from "./Components/RightSlideModal";
import AuthRedirect from "./Components/AuthRedirect";

const SuccessPage = () => <h2>✅ Integration Successful!</h2>;
const ErrorPage = () => <h2>❌ Something went wrong.</h2>;

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
        <Route path="/" element={<Home openModal={openModal} />} />
        <Route path="/redirect/:appId" element={<AuthRedirect />} />
        <Route path="/success" element={<SuccessPage />} />
        <Route path="/error" element={<ErrorPage />} />
      </Routes>
      {showForm && <RightSlideModal onClose={closeModal} />}
    </Router>
  );
};

export default App;

import React, { useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";

const AuthRedirect = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { appId } = useParams(); // ✅ This is the actual path param being used

  useEffect(() => {
    console.log("AuthRedirect mounted");
    console.log("URL:", window.location.href);
    console.log("Path param appId:", appId);
    console.log("Raw query string:", location.search);

    const params = new URLSearchParams(location.search);
    const code = params.get("code");
    const email_id = params.get("state");

    console.log("Parsed query params:");
    console.log("code:", code);
    console.log("email_id (state):", email_id);

    if (code && email_id && appId) {
      console.log("All required params present. Starting token exchange...");

      fetch("http://localhost:8000/exchange-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          auth_code: code,
          email_id: email_id,
          app_id: appId,
        }),
      })
        .then((res) => {
          console.log("Exchange token response status:", res.status);
          if (!res.ok) throw new Error("Token exchange failed");
          return res.json();
        })
        .then((data) => {
          console.log("Token exchange successful, response data:", data);
          navigate("/success");
        })
        .catch((err) => {
          console.error("Token exchange error:", err);
          navigate("/error");
        });
    } else {
      console.warn("Missing required parameters:");
      if (!code) console.warn("- code is missing");
      if (!email_id) console.warn("- email_id (state) is missing");
      if (!appId) console.warn("- appId (path param) is missing");
    }
  }, [location, navigate, appId]); // ✅ replaced clientId with appId

  return <div>Exchanging token with Microsoft...</div>;
};

export default AuthRedirect;

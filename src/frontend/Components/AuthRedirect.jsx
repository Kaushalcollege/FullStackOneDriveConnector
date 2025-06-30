import { useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";

const AuthRedirect = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { appId } = useParams();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get("code");
    const stateParam = params.get("state");

    let clientId = localStorage.getItem("client_id");

    if (stateParam) {
      try {
        const parsed = JSON.parse(decodeURIComponent(stateParam));
        if (parsed.clientId) clientId = parsed.clientId;
      } catch (err) {
        console.error("Failed to parse state:", stateParam);
      }
    }

    console.log("\u{1F501} AuthRedirect Triggered:", { code, appId, clientId });

    if (code && clientId && appId) {
      fetch("http://localhost:8000/exchange-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          auth_code: code,
          client_id: clientId,
          app_id: appId,
        }),
      })
        .then((res) => {
          console.log("\u{1F512} Exchange token response:", res.status);
          if (!res.ok) throw new Error("Token exchange failed");
          return res.json();
        })
        .then((data) => {
          console.log("\u{2705} Token exchanged:", data);
          navigate("/success");
        })
        .catch((err) => {
          console.error("\u{274C} Token exchange error:", err);
          navigate("/error");
        });
    } else {
      console.warn("\u{26A0} Missing required parameters:", {
        code,
        appId,
        clientId,
      });
    }
  }, [location, navigate, appId]);

  return <div>Exchanging token with Microsoft...</div>;
};

export default AuthRedirect;

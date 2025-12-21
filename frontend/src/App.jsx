import { useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/pick-clip", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ youtube_url: url }),
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center", 
      justifyContent: "center", 
      width: "100%",
      maxWidth: 600,
      padding: 40,
      margin: "0 auto"
    }}>
      <h1 style={{ textAlign: "center", width: "100%" }}>Podcast Clip Picker</h1>

      <input
        type="text"
        placeholder="Paste YouTube link"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: "100%", padding: 8, marginTop: 20, textAlign: "center" }}
      />

      <button onClick={handleSubmit} disabled={loading} style={{ marginTop: 12, width: "100%" }}>
        {loading ? "Picking…" : "Pick Best Clip"}
      </button>

      {error && <p style={{ color: "red", textAlign: "center", width: "100%" }}>{error}</p>}

      {result && (
        <pre style={{ marginTop: 20, textAlign: "left", width: "100%" }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;

import { useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function extractVideoId(youtubeUrl) {
    try {
      const url = new URL(youtubeUrl);
      if (url.hostname.includes("youtube.com")) {
        return url.searchParams.get("v");
      }
      if (url.hostname.includes("youtu.be")) {
        return url.pathname.slice(1);
      }
    } catch (e) {
      return null;
    }
    return null;
  }

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
        <div style={{ marginTop: 20, width: "100%" }}>
          <div style={{ marginBottom: 16, textAlign: "center" }}>
            <p style={{ marginBottom: 8 }}><strong>Reason:</strong> {result.reason}</p>
            <p style={{ fontSize: "0.9em", color: "#888" }}>
              Clip: {Math.floor(result.start_seconds / 60)}:{(result.start_seconds % 60).toString().padStart(2, "0")} - {Math.floor(result.end_seconds / 60)}:{(result.end_seconds % 60).toString().padStart(2, "0")}
            </p>
          </div>
          
          {extractVideoId(url) && (
            <div style={{ position: "relative", paddingBottom: "56.25%", height: 0, overflow: "hidden", width: "100%" }}>
              <iframe
                style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
                src={`https://www.youtube.com/embed/${extractVideoId(url)}?start=${result.start_seconds}`}
                title="YouTube video player"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;

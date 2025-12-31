import { useState } from "react";

function App() {
  const [url, setUrl] = useState("https://www.youtube.com/watch?v=GeD8tpOCyIY");
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

  function formatReason(reason) {
    if (!reason) return null;
    
    // Helper function to convert markdown bold (**text**) to JSX
    // Also handles malformed markdown like **text* or *text**
    function parseBold(text) {
      const parts = [];
      // Match both proper **text** and malformed **text* or *text**
      const regex = /\*{1,2}(.+?)\*{1,2}/g;
      let lastIndex = 0;
      let match;
      
      while ((match = regex.exec(text)) !== null) {
        // Add text before the bold part
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index));
        }
        // Add the bold part
        parts.push(<strong key={match.index}>{match[1]}</strong>);
        lastIndex = regex.lastIndex;
      }
      
      // Add remaining text, removing any stray asterisks
      if (lastIndex < text.length) {
        const remaining = text.substring(lastIndex).replace(/\*+/g, '');
        if (remaining) {
          parts.push(remaining);
        }
      }
      
      return parts.length > 0 ? parts : text;
    }
    
    // Try splitting by newlines first
    let lines = reason.split(/[\n\r]+/).map(line => line.trim()).filter(line => line);
    
    // Check if it looks like bullet points (starts with *, -, or •)
    const bulletPattern = /^[\*\-\•]\s*/;
    const hasBullets = lines.some(line => bulletPattern.test(line));
    
    if (hasBullets) {
      // Has explicit bullets - extract and render them
      const bullets = lines
        .filter(line => bulletPattern.test(line))
        .map(line => line.replace(bulletPattern, '').trim())
        .filter(bullet => bullet);
      
      if (bullets.length > 0) {
        return (
          <ul style={{ textAlign: "left", margin: "8px 0", paddingLeft: "20px", listStyleType: "disc" }}>
            {bullets.map((bullet, index) => (
              <li key={index} style={{ marginBottom: "8px", lineHeight: "1.5" }}>{parseBold(bullet)}</li>
            ))}
          </ul>
        );
      }
    }
    
    // If no bullets detected, return as-is with bold parsing (join lines with space)
    return <div style={{ marginTop: "8px", lineHeight: "1.5" }}>{parseBold(lines.join(' '))}</div>;
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
        style={{ width: "100%", padding: 8, marginTop: 20, textAlign: "center", opacity: 0.6 }}
      />

      <button onClick={handleSubmit} disabled={loading} style={{ marginTop: 12, width: "100%" }}>
        {loading ? "Picking…" : "Pick Best Clip"}
      </button>

      {error && <p style={{ color: "red", textAlign: "center", width: "100%" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 20, width: "100%" }}>
          <div style={{ marginBottom: 16, textAlign: "center" }}>
            {result.title && (
              <div style={{ marginBottom: 12 }}>
                <h2 style={{ fontSize: "1.3em", fontWeight: "bold", marginBottom: 4 }}>
                  {result.title}
                </h2>
                {result.channel_name && (
                  <p style={{ fontSize: "1em", color: "#666", marginBottom: 8 }}>
                    {result.channel_name}
                  </p>
                )}
              </div>
            )}
            <h3 style={{ marginBottom: 16, fontSize: "1.5em", fontWeight: "bold" }}>
              The best clip of this podcast is: {Math.floor(result.start_seconds / 60)}:{(result.start_seconds % 60).toString().padStart(2, "0")} - {Math.floor(result.end_seconds / 60)}:{(result.end_seconds % 60).toString().padStart(2, "0")}
            </h3>
            <div style={{ marginBottom: 8, textAlign: "left" }}>
              <strong>Here's why this clip is great:</strong>
              {formatReason(result.reason)}
            </div>
          </div>
          
          {extractVideoId(url) && (
            <div style={{ marginTop: 24 }}>
              <p style={{ textAlign: "center", marginBottom: 16, fontSize: "1.1em", fontWeight: "500" }}>
                Watch the clip below:
              </p>
              <div style={{ position: "relative", paddingBottom: "56.25%", height: 0, overflow: "hidden", width: "100%" }}>
              <iframe
                style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
                src={`https://www.youtube.com/embed/${extractVideoId(url)}?start=${result.start_seconds}&end=${result.end_seconds}`}
                title="YouTube video player"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;

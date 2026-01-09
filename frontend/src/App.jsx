import { useState } from "react";

const CRITERIA_OPTIONS = [
  { id: "actionable", label: "Actionable advice" },
  { id: "surprising", label: "Surprising insight" },
  { id: "story", label: "Concrete story" },
  { id: "controversial", label: "Controversial/bold" },
  { id: "funny", label: "Funny/entertaining" },
  { id: "emotional", label: "Emotional/inspiring" },
];

function App() {
  const [url, setUrl] = useState("https://www.youtube.com/watch?v=GeD8tpOCyIY");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCriteria, setSelectedCriteria] = useState([]);
  const [topic, setTopic] = useState("");
  const [usedCriteria, setUsedCriteria] = useState([]);
  const [usedTopic, setUsedTopic] = useState("");

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

  function getResultHeading() {
    const time = `${Math.floor(result.start_seconds / 60)}:${(result.start_seconds % 60).toString().padStart(2, "0")} - ${Math.floor(result.end_seconds / 60)}:${(result.end_seconds % 60).toString().padStart(2, "0")}`;

    // Build description based on what was used for the search
    const parts = [];

    if (usedCriteria.length === 1) {
      const labels = {
        actionable: "most actionable",
        surprising: "most surprising",
        story: "best story",
        controversial: "most controversial",
        funny: "funniest",
        emotional: "most emotional",
      };
      parts.push(labels[usedCriteria[0]] || "best");
    } else {
      parts.push("best");
    }

    parts.push("clip");

    if (usedTopic) {
      parts.push(`about "${usedTopic}"`);
    }

    return `The ${parts.join(" ")}: ${time}`;
  }

  function toggleCriteria(criteriaId) {
    setSelectedCriteria((prev) =>
      prev.includes(criteriaId) ? [] : [criteriaId]
    );
  }

  async function handleSubmit() {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        youtube_url: url,
        criteria: selectedCriteria.length > 0 ? selectedCriteria : null,
        topic: topic.trim() || null,
      };

      const response = await fetch("http://127.0.0.1:8000/pick-clip", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = await response.json();
      setResult(data);
      setUsedCriteria([...selectedCriteria]);
      setUsedTopic(topic.trim());
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

      <p style={{ textAlign: "center", color: "#444", marginTop: 8, fontWeight: "500" }}>
        Paste a YouTube podcast link and we'll find the most shareable clip.
      </p>

      <input
        type="text"
        placeholder="Paste YouTube link"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onFocus={() => setUrl("")}
        style={{ width: "100%", padding: 8, marginTop: 20, textAlign: "center", opacity: 0.6 }}
      />

      <div style={{ marginTop: 20, width: "100%" }}>
        <label style={{ fontWeight: "500", display: "block", marginBottom: 8 }}>
          What kind of clip? <span style={{ fontWeight: "normal", color: "#666" }}>(optional)</span>
        </label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CRITERIA_OPTIONS.map((option) => (
            <label
              key={option.id}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "6px 12px",
                border: selectedCriteria.includes(option.id) ? "2px solid #007bff" : "1px solid #ccc",
                borderRadius: 20,
                cursor: "pointer",
                background: selectedCriteria.includes(option.id) ? "#e7f1ff" : "#fff",
                fontSize: "0.9em",
              }}
            >
              <input
                type="checkbox"
                checked={selectedCriteria.includes(option.id)}
                onChange={() => toggleCriteria(option.id)}
                style={{ display: "none" }}
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 16, width: "100%" }}>
        <label style={{ fontWeight: "500", display: "block", marginBottom: 8 }}>
          Find clips about... <span style={{ fontWeight: "normal", color: "#666" }}>(optional)</span>
        </label>
        <input
          type="text"
          placeholder="e.g. AI, productivity, hiring"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          style={{ width: "100%", padding: 8, textAlign: "left" }}
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          marginTop: 16,
          width: "100%",
          padding: "12px 16px",
          backgroundColor: loading ? "#999" : "#007bff",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          fontSize: "1em",
          fontWeight: "600",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Picking…" : "Pick Best Clip"}
      </button>

      {error && <p style={{ color: "red", textAlign: "center", width: "100%" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 20, width: "100%" }}>
          <div style={{ marginBottom: 16, textAlign: "center" }}>
            {result.title && (
              <div style={{
                marginBottom: 20,
                paddingBottom: 16,
                borderBottom: "1px solid #e5e5e5",
              }}>
                <p style={{ fontSize: "0.85em", color: "#888", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                  {result.channel_name || "Podcast"}
                </p>
                <h2 style={{ fontSize: "1.5em", fontWeight: "600", color: "#111", lineHeight: 1.3 }}>
                  {result.title}
                </h2>
              </div>
            )}
            <h3 style={{ marginBottom: 16, fontSize: "1.3em", fontWeight: "600" }}>
              {getResultHeading()}
            </h3>
            <div style={{ marginBottom: 8, textAlign: "left" }}>
              <strong>Here's why:</strong>
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

import React, { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

const LANGUAGES = [
  "English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam",
  "Spanish", "French", "German", "Italian", "Portuguese",
  "Russian", "Japanese", "Korean", "Chinese", "Arabic"
];

const API = "http://localhost:8000";

const HEADERS = {
  "ngrok-skip-browser-warning": "true",
  "Accept": "application/json"
};

function App() {
  const [video, setVideo] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [language, setLanguage] = useState("Hindi");
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState("");
  const [downloadUrl, setDownloadUrl] = useState(null);
  // eslint-disable-next-line
  const [jobId, setJobId] = useState(null);
  const fileInputRef = useRef();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setVideo(file);
    setVideoPreview(URL.createObjectURL(file));
    setStatus("idle");
    setDownloadUrl(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    setVideo(file);
    setVideoPreview(URL.createObjectURL(file));
    setStatus("idle");
    setDownloadUrl(null);
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/status/${id}`, { headers: HEADERS });
        const data = res.data;
        if (data.status === "processing") {
          setProgress(data.progress || "Processing...");
        } else if (data.status === "done") {
          clearInterval(interval);
          setStatus("done");
          setDownloadUrl(`${API}/download/${id}`);
        } else if (data.status === "error") {
          clearInterval(interval);
          setStatus("error");
          setProgress(data.message || "Something went wrong.");
        }
      } catch {
        clearInterval(interval);
        setStatus("error");
        setProgress("Could not reach server.");
      }
    }, 2000);
  };

  const handleSubmit = async () => {
    if (!video) return;
    setStatus("uploading");
    setProgress("Uploading video...");
    setDownloadUrl(null);

    const formData = new FormData();
    formData.append("video", video);
    formData.append("language", language);

    try {
      const res = await axios.post(`${API}/process`, formData, {
        headers: {
          ...HEADERS,
          "Content-Type": "multipart/form-data"
        }
      });
      const { job_id } = res.data;
      setJobId(job_id);
      setStatus("processing");
      setProgress("Pipeline started...");
      pollStatus(job_id);
    } catch (err) {
      setStatus("error");
      setProgress("Failed to start processing.");
    }
  };

  const handleDownload = async () => {
    try {
      const res = await axios.get(downloadUrl, {
        headers: HEADERS,
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "dubbed_output.mp4");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Download failed. Try again.");
    }
  };

  const reset = () => {
    setVideo(null);
    setVideoPreview(null);
    setStatus("idle");
    setProgress("");
    setDownloadUrl(null);
    setJobId(null);
  };

  const isProcessing = status === "uploading" || status === "processing";

  return (
    <div className="app">
      <div className="grain" />
      <header className="header">
        <div className="logo">
          <span className="logo-icon">⬡</span>
          <span className="logo-text">DubSync</span>
        </div>
        <p className="tagline">Multilingual Video Dubbing — Powered by AI</p>
      </header>

      <main className="main">
        <div
          className={`upload-zone ${videoPreview ? "has-video" : ""} ${isProcessing ? "locked" : ""}`}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isProcessing && fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            hidden
          />
          {videoPreview ? (
            <video src={videoPreview} className="video-preview" controls />
          ) : (
            <div className="upload-prompt">
              <div className="upload-icon">▶</div>
              <p className="upload-text">Drop your video here</p>
              <p className="upload-sub">or click to browse — MP4, MOV, AVI</p>
            </div>
          )}
        </div>

        <div className="controls">
          <div className="control-group">
            <label className="control-label">Target Language</label>
            <select
              className="select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={isProcessing}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <div className="button-row">
            {status !== "done" ? (
              <button
                className={`btn-primary ${isProcessing ? "loading" : ""}`}
                onClick={handleSubmit}
                disabled={!video || isProcessing}
              >
                {isProcessing ? (
                  <>
                    <span className="spinner" />
                    {status === "uploading" ? "Uploading..." : "Processing..."}
                  </>
                ) : "Dub Video"}
              </button>
            ) : (
              <>
                <button className="btn-download" onClick={handleDownload}>
                  ↓ Download Dubbed Video
                </button>
                <button className="btn-reset" onClick={reset}>Start Over</button>
              </>
            )}
          </div>
        </div>

        {(isProcessing || status === "error" || status === "done") && (
          <div className={`status-bar ${status}`}>
            {status === "done" && <span className="status-icon">✓</span>}
            {status === "error" && <span className="status-icon">✕</span>}
            {isProcessing && <span className="status-icon pulse">◉</span>}
            <span className="status-text">
              {status === "done" ? "Dubbing complete! Your video is ready." :
               status === "error" ? progress : progress}
            </span>
          </div>
        )}

        <div className="pipeline">
          {[
            { icon: "🎵", label: "Extract Audio" },
            { icon: "📝", label: "Transcribe" },
            { icon: "🌐", label: "Translate" },
            { icon: "🔊", label: "Generate TTS" },
            { icon: "🎬", label: "Merge Video" },
          ].map((step, i) => (
            <div className="pipeline-step" key={i}>
              <span className="step-icon">{step.icon}</span>
              <span className="step-label">{step.label}</span>
              {i < 4 && <span className="step-arrow">→</span>}
            </div>
          ))}
        </div>
      </main>

      <footer className="footer">
        Powered by Whisper + Wav2Lip + FastAPI · Running on GPU
      </footer>
    </div>
  );
}

export default App;

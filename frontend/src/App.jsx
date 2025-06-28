import { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';


function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800 text-white text-center">
      <h1 className="text-4xl font-bold mb-4">MockInterview.AI</h1>
      <p className="mb-8 text-lg w-3/4">AI-powered platform for personalized B.Tech placement interview practice. Upload your resume, get real-time interview questions, and receive feedback instantly.</p>
      <Link to="/upload" className="bg-blue-600 px-6 py-2 rounded-full text-white hover:bg-blue-500">Get Started</Link>
    </div>
  );
}

function ResumeUploadPage({ setSessionId }) {
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("");
  const navigate = useNavigate();

  const handleFileUpload = async () => {
    if (!file || !filename) return alert("Please select file and provide a filename.");
    const session_id = crypto.randomUUID();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("filename", filename);
    formData.append("file_type", "resume");
    formData.append("session_id", session_id);

    try {
      const response = await axios.post("http://localhost:8000/upload-doc", formData);
      if (response.data.file_id) {
        setSessionId(session_id);
        navigate("/interview");
      }
    } catch (error) {
      console.error("Upload error", error);
      alert("Failed to upload. Check backend.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-900 text-white">
      <h2 className="text-3xl font-semibold mb-4">Upload Your Resume</h2>
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} className="mb-2" />
      <input type="text" placeholder="Enter filename" onChange={(e) => setFilename(e.target.value)} className="mb-4 px-3 py-1 text-black rounded" />
      <button onClick={handleFileUpload} className="bg-green-600 px-4 py-2 rounded hover:bg-green-500">Upload and Start</button>
    </div>
  );
}

function InterviewPage({ sessionId }) {
  const [question, setQuestion] = useState("What is polymorphism in OOP?");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const synthRef = useRef(window.speechSynthesis);
  const recognitionRef = useRef(null);

  const startTTS = () => {
    const utterance = new SpeechSynthesisUtterance(question);
    utterance.lang = 'en-US';
    synthRef.current.speak(utterance);
  };

  const startSTT = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Your browser does not support Speech Recognition");

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      setAnswer(event.results[0][0].transcript);
    };

    recognition.onerror = (e) => console.error("Speech recognition error", e);

    recognition.start();
    recognitionRef.current = recognition;
  };

  const askNext = async () => {
    try {
      const payload = {
        session_id: sessionId,
        query: answer,
        model: "gemini-2.0-flash"
      };
      const res = await axios.post("http://localhost:8000/chat", payload);
      setFeedback(res.data.answer);
      setQuestion(res.data.answer); // Set new question to simulate conversation
    } catch (error) {
      console.error("Chat error", error);
      alert("Failed to get AI response.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <h2 className="text-2xl font-bold mb-4">Live Interview</h2>
      <div className="mb-6">
        <p className="text-lg font-medium">AI asks:</p>
        <div className="p-4 bg-slate-800 rounded my-2">{question}</div>
        <div className="flex gap-2 mt-2">
          <button onClick={startTTS} className="bg-blue-500 px-4 py-2 rounded hover:bg-blue-400">🔊 Speak</button>
          <button onClick={startSTT} className="bg-purple-500 px-4 py-2 rounded hover:bg-purple-400">🎤 Answer</button>
        </div>
      </div>
      <div className="mb-6">
        <p className="text-lg font-medium">Your Answer:</p>
        <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} className="w-full p-3 bg-slate-700 rounded resize-none" rows={4}></textarea>
      </div>
      <button onClick={askNext} className="bg-green-500 px-4 py-2 rounded hover:bg-green-400 mb-4">Submit Answer</button>
      {feedback && (
        <div className="bg-green-800 p-4 rounded mt-4">
          <strong>AI Feedback:</strong> {feedback}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [sessionId, setSessionId] = useState(null);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/upload" element={<ResumeUploadPage setSessionId={setSessionId} />} />
        <Route path="/interview" element={<InterviewPage sessionId={sessionId} />} />
      </Routes>
    </Router>
  );
} 
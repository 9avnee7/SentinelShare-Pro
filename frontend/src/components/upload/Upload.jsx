import React, { useState } from "react";
import axios from "axios";

const Upload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanPhase, setScanPhase] = useState("");
  const [progress, setProgress] = useState(0);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);

  const chunkSize = 300 * 1024; // 300KB

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setProgress(0);
    setCurrentChunk(0);
    setTotalChunks(0);
    setScanProgress(0);
    setScanPhase("");
  };

  const readFileAsArrayBuffer = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsArrayBuffer(file);
    });
  };

  const encryptChunk = async (chunk, key, iv) => {
    const encrypted = await crypto.subtle.encrypt(
      { name: "AES-GCM", iv },
      key,
      chunk
    );
    return new Uint8Array(encrypted);
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setScanning(true);
      setUploading(false);
      setProgress(0);
      setScanProgress(0);
      setScanPhase("Scanning with YARA...");

      const formData = new FormData();
      formData.append("file", file);

      await axios.post("http://localhost:8000/validate/yara", formData, {
        withCredentials: true,
      });
      setScanProgress(33);
      setScanPhase("Scanning with ClamAV...");

      await axios.post("http://localhost:8000/validate/clamav", formData, {
        withCredentials: true,
      });
      setScanProgress(66);
      setScanPhase("Scanning with VirusTotal...");

      const arrayBuffer = await readFileAsArrayBuffer(file);
      const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

      await axios.post("http://localhost:8000/validate/virustotal", {fileHash:hashHex});

      setScanProgress(100);
      setScanPhase("Scan completed");
      alert("File scanned successfully. Proceeding to upload...");

      setScanning(false);
      setUploading(true);

      const key = await crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt"]
      );

      const total = Math.ceil(file.size / chunkSize);
      setTotalChunks(total);

      for (let i = 0; i < total; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunkBlob = file.slice(start, end);
        const chunkArrayBuffer = await chunkBlob.arrayBuffer();

        const iv = crypto.getRandomValues(new Uint8Array(12));
        const encryptedChunk = await encryptChunk(chunkArrayBuffer, key, iv);

        const chunkFormData = new FormData();
        chunkFormData.append("chunk", new Blob([encryptedChunk]));
        chunkFormData.append("chunkIndex", i);
        chunkFormData.append("fileName", file.name);
        chunkFormData.append("iv", JSON.stringify(Array.from(iv)));
        chunkFormData.append("fileHash", hashHex);
        chunkFormData.append("totalChunks", total);
        chunkFormData.append(
          "key",
          btoa(
            String.fromCharCode(
              ...new Uint8Array(await crypto.subtle.exportKey("raw", key))
            )
          )
        );

        await axios.post("http://localhost:8000/upload", chunkFormData, {
     
          withCredentials: true,
        });

        setCurrentChunk(i + 1);
        setProgress(Math.round(((i + 1) / total) * 100));
      }

      alert("Upload completed successfully.");
    } catch (error) {
      console.error(error);
      alert("An error occurred during upload or scanning.");
    } finally {
      setScanning(false);
      setUploading(false);
      setProgress(0);
      setCurrentChunk(0);
      setTotalChunks(0);
      setScanProgress(0);
      setScanPhase("");
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto bg-white shadow rounded-lg mt-10">
      <h2 className="text-xl font-bold mb-4">Secure File Upload</h2>

      <input
        type="file"
        onChange={handleFileChange}
        className="mb-4"
        disabled={scanning || uploading}
      />

      {/* Scanning progress with phase */}
      {scanning && (
        <div className="mb-4">
          <p className="mb-2 font-semibold text-blue-600">{scanPhase}</p>
          <div className="w-full bg-gray-200 rounded h-4 overflow-hidden">
            <div
              className="bg-blue-600 h-4 transition-all duration-300"
              style={{ width: `${scanProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Upload progress */}
      {uploading && !scanning && (
        <div className="mb-4">
          <p className="mb-2 font-semibold text-green-600">
            Uploading... {progress}%
          </p>
          <p className="text-sm text-gray-500 mb-2">
            Chunk {currentChunk} of {totalChunks}
          </p>
          <div className="w-full bg-gray-200 rounded h-4 overflow-hidden">
            <div
              className="bg-green-600 h-4 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || scanning || !file}
        className={`${
          uploading || scanning || !file
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
        } text-white px-4 py-2 rounded`}
      >
        {scanning
          ? scanPhase
          : uploading
          ? `Uploading (${progress}%)`
          : "Upload File"}
      </button>
    </div>
  );
};

export default Upload;
